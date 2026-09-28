"""DeepSeek API health checks and locked, resumable workflow runner."""

import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime_api"
STATE = RUNTIME / "api.json"
MAX_RETRIES_PER_CHECKPOINT_VERSION = 3
MAX_RETRIES_TOTAL = 5
RETRY_BASE_SECONDS = 3


def request(path, payload=None, timeout=30):
    url = os.environ.get("WINGPT_API_URL", "https://api.deepseek.com").rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode()
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY is required")
    headers = {"Authorization": f"Bearer {key}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    with urllib.request.urlopen(
        urllib.request.Request(url, data=data, headers=headers), timeout=timeout
    ) as response:
        return json.load(response)


def identity():
    try:
        data = request("/models")
        expected = os.environ["WINGPT_MODEL"]
        return next(
            (item for item in data.get("data", []) if item["id"] == expected), None
        )
    except (OSError, ValueError):
        return None


def chat_canary():
    try:
        data = request(
            "/chat/completions",
            {
                "model": os.environ["WINGPT_MODEL"],
                "messages": [{"role": "user", "content": "Reply OK."}],
                "max_tokens": 1,
                "thinking": {"type": "disabled"},
                "user_id": os.environ.get("WINGPT_API_USER_ID", "biodiscovery_api"),
            },
            timeout=120,
        )
        return bool(data.get("choices"))
    except (OSError, ValueError):
        return False


def thinking_tool_canary():
    tool = {
        "type": "function",
        "function": {
            "name": "report_ok",
            "description": "Return the API preflight result.",
            "parameters": {"type": "object", "properties": {}},
        },
    }
    user_message = {"role": "user", "content": "Call report_ok."}
    common = {
        "model": os.environ["WINGPT_MODEL"],
        "tools": [tool],
        "max_tokens": 128,
        "thinking": {"type": "enabled"},
        "reasoning_effort": os.environ.get("WINGPT_REASONING_EFFORT", "max"),
        "user_id": os.environ.get("WINGPT_API_USER_ID", "biodiscovery_api"),
    }
    try:
        first = request(
            "/chat/completions",
            {**common, "messages": [user_message]},
            timeout=120,
        )
        assistant = first["choices"][0]["message"]
        calls = assistant.get("tool_calls") or []
        reasoning = assistant.get("reasoning_content")
        if (
            not calls
            or calls[0].get("function", {}).get("name") != "report_ok"
            or not isinstance(reasoning, str)
            or not reasoning
        ):
            return False
        follow_up = {
            "role": "assistant",
            "content": assistant.get("content") or "",
            "reasoning_content": reasoning,
            "tool_calls": calls,
        }
        second = request(
            "/chat/completions",
            {
                **common,
                "messages": [
                    user_message,
                    follow_up,
                    {
                        "role": "tool",
                        "tool_call_id": calls[0]["id"],
                        "content": '{"ok":true}',
                    },
                ],
            },
            timeout=120,
        )
        return bool(second.get("choices"))
    except (KeyError, OSError, TypeError, ValueError):
        return False


def write_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(STATE)


def ensure_api():
    model = identity()
    if not model:
        raise RuntimeError(
            f"DeepSeek API model is unavailable: {os.environ['WINGPT_MODEL']}"
        )
    if not chat_canary():
        raise RuntimeError("DeepSeek API chat canary failed")
    if not thinking_tool_canary():
        raise RuntimeError(
            "DeepSeek API thinking/tool/reasoning-continuity canary failed"
        )
    key_fingerprint = hashlib.sha256(
        os.environ["DEEPSEEK_API_KEY"].encode()
    ).hexdigest()[:12]
    write_state(
        {
            "provider": "deepseek-api",
            "base_url": os.environ["WINGPT_API_URL"],
            "model": os.environ["WINGPT_MODEL"],
            "credential_source": "environment",
            "credential_sha256_prefix": key_fingerprint,
            "status": "ready",
            "thinking_tool_canary": True,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
    )
    print(
        f"DeepSeek API ready with model {os.environ['WINGPT_MODEL']}.", flush=True
    )


def stop_api():
    state = {
        "provider": "deepseek-api",
        "model": os.environ["WINGPT_MODEL"],
        "status": "not_applicable",
        "note": "Remote API lifecycle is not managed by this workflow.",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    write_state(state)
    print("Remote DeepSeek API has no local server to stop.")


def checkpoint_version(checkpoint):
    data = json.loads(checkpoint.read_text())
    explicit = data.get("checkpoint_version", data.get("version"))
    if explicit is not None:
        return str(explicit)
    progress = {
        key: data.get(key) for key in ("phase", "next_action", "rounds", "session_file")
    }
    return hashlib.sha256(json.dumps(progress, sort_keys=True).encode()).hexdigest()[
        :16
    ]


def record_runner_status(checkpoint, status, **details):
    if not checkpoint.exists():
        return
    data = json.loads(checkpoint.read_text())
    data["runner"] = {
        "status": status,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        **details,
    }
    if status == "needs_attention":
        data["status"] = "needs_attention"
    temporary = checkpoint.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(checkpoint)


def normalized_returncode(returncode):
    return 128 - returncode if returncode < 0 else returncode


def run_agent(arguments):
    workspace = ROOT
    if "--workspace" in arguments:
        workspace = Path(arguments[arguments.index("--workspace") + 1]).resolve(
            strict=True
        )
    task_hash = hashlib.sha256(str(workspace).lower().encode()).hexdigest()[:24]
    codex_home = Path(
        os.environ.get("CODEX_HOME", ROOT / ".runtime_api" / "codex-home")
    ).resolve()
    checkpoint = codex_home / "tasks" / f"{task_hash}.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    with checkpoint.with_suffix(".runner.lock").open("a") as lock:
        if "--autonomous" in arguments:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with (RUNTIME / "startup.lock").open("a") as startup_lock:
            fcntl.flock(startup_lock, fcntl.LOCK_EX)
            ensure_api()
        source_runtime = ROOT.parent / "workflow_codex" / ".runtime" / "macos"
        node = source_runtime / "tools" / "bin" / "node"
        command = [
            str(node),
            str(ROOT / "codex-cli" / "bin" / "codex_api.js"),
            "--allow-network",
            *arguments,
        ]
        total_retries = 0
        retries_by_version = {}
        while True:
            result = subprocess.run(command, check=False)
            if (
                result.returncode != 75
                or "--autonomous" not in arguments
                or not checkpoint.exists()
            ):
                status = "completed" if result.returncode == 0 else "terminated"
                record_runner_status(
                    checkpoint,
                    status,
                    returncode=normalized_returncode(result.returncode),
                    total_retries=total_retries,
                )
                return normalized_returncode(result.returncode)
            version = checkpoint_version(checkpoint)
            version_retries = retries_by_version.get(version, 0)
            if (
                version_retries >= MAX_RETRIES_PER_CHECKPOINT_VERSION
                or total_retries >= MAX_RETRIES_TOTAL
            ):
                reason = (
                    "checkpoint_version_retry_limit"
                    if version_retries >= MAX_RETRIES_PER_CHECKPOINT_VERSION
                    else "total_retry_limit"
                )
                record_runner_status(
                    checkpoint,
                    "needs_attention",
                    reason=reason,
                    returncode=75,
                    checkpoint_version=version,
                    checkpoint_version_retries=version_retries,
                    total_retries=total_retries,
                )
                print(
                    f"Retry limit reached ({reason}); checkpoint needs attention.",
                    flush=True,
                )
                return 75
            retries_by_version[version] = version_retries + 1
            total_retries += 1
            delay = RETRY_BASE_SECONDS * (2 ** (total_retries - 1))
            record_runner_status(
                checkpoint,
                "retrying",
                returncode=75,
                checkpoint_version=version,
                checkpoint_version_retries=retries_by_version[version],
                total_retries=total_retries,
                retry_delay_seconds=delay,
            )
            print(
                f"Retryable interruption: resuming checkpoint {version} "
                f"after {delay}s ({total_retries}/{MAX_RETRIES_TOTAL}).",
                flush=True,
            )
            if "--resume" not in command:
                command.append("--resume")
            time.sleep(delay)
            ensure_api()


def main():
    action, *arguments = sys.argv[1:]
    if action == "run":
        return run_agent(arguments)
    with (RUNTIME / "startup.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if action == "start":
            ensure_api()
        elif action == "stop":
            stop_api()
        elif action == "status":
            model_ready = bool(identity())
            canary_ready = model_ready and chat_canary()
            tool_canary_ready = canary_ready and thinking_tool_canary()
            print(
                json.dumps(
                    {
                        "ready": tool_canary_ready,
                        "model_endpoint_ready": model_ready,
                        "chat_canary_ready": canary_ready,
                        "thinking_tool_canary_ready": tool_canary_ready,
                        "provider": "deepseek-api",
                        "model": os.environ["WINGPT_MODEL"],
                        "base_url": os.environ["WINGPT_API_URL"],
                        "credential_present": bool(os.environ.get("DEEPSEEK_API_KEY")),
                    },
                    indent=2,
                )
            )
        else:
            raise ValueError(f"Unknown action: {action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
