"""Project-local MLX service lifecycle and locked, resumable CLI runner."""

import fcntl
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime" / "macos"
STATE = RUNTIME / "server.json"
MAX_RETRIES_PER_CHECKPOINT_VERSION = 3
MAX_RETRIES_TOTAL = 5
RETRY_BASE_SECONDS = 3
METAL_OOM_MARKERS = (
    "metal out of memory",
    "metal command buffer",
    "insufficient memory",
    "resource limit exceeded",
)


def request(path, payload=None):
    url = (
        os.environ.get("WINGPT_API_URL", "http://127.0.0.1:8000/v1").removesuffix("/v1")
        + path
    )
    data = None if payload is None else json.dumps(payload).encode()
    headers = {} if data is None else {"Content-Type": "application/json"}
    with urllib.request.urlopen(
        urllib.request.Request(url, data=data, headers=headers), timeout=10
    ) as response:
        return json.load(response)


def identity():
    try:
        data = request("/v1/models")
        expected = os.environ["WINGPT_MODEL"]
        return next(
            (item for item in data.get("data", []) if item["id"] == expected), None
        )
    except (OSError, ValueError):
        return None


def chat_canary():
    try:
        data = request(
            "/v1/chat/completions",
            {
                "model": os.environ["WINGPT_MODEL"],
                "messages": [{"role": "user", "content": "Reply OK."}],
                "max_tokens": 1,
                "temperature": 0,
            },
        )
        return bool(data.get("choices"))
    except (OSError, ValueError):
        return False


def read_state():
    if not STATE.exists():
        return None
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return None


def write_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(STATE)


def recorded_process(state):
    if (
        not state
        or not isinstance(state.get("pid"), int)
        or not isinstance(state.get("model"), str)
        or not state["model"]
    ):
        return False
    result = subprocess.run(
        ["ps", "-p", str(state["pid"]), "-o", "command="],
        capture_output=True,
        text=True,
        check=False,
    )
    return (
        result.returncode == 0
        and "mlx_lm" in result.stdout
        and state.get("model", "") in result.stdout
    )


def recorded_metal_oom(state):
    if not recorded_process(state):
        return False
    log = Path(state.get("log", ""))
    if not log.is_file():
        return False
    tail = log.read_text(errors="replace")[-65536:].lower()
    return any(marker in tail for marker in METAL_OOM_MARKERS)


def terminate_recorded_server(state, reason):
    if not recorded_process(state):
        if state:
            state.update(
                {"status": "stale", "stopped_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            )
            write_state(state)
        return False
    pid = state["pid"]
    os.kill(pid, signal.SIGTERM)
    for _ in range(50):
        if not recorded_process(state):
            break
        time.sleep(0.1)
    else:
        os.kill(pid, signal.SIGKILL)
    state.update(
        {
            "status": "stopped",
            "stop_reason": reason,
            "stopped_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
    )
    write_state(state)
    return True


def start_server():
    model = identity()
    if model and chat_canary():
        print("MLX service ready; reusing the requested model.")
        return
    state = read_state()
    if recorded_metal_oom(state):
        pid = state["pid"]
        print(f"Metal OOM detected; restarting recorded MLX PID {pid}.", flush=True)
        terminate_recorded_server(state, "metal_oom")
    elif model and recorded_process(state):
        pid = state["pid"]
        print(f"MLX chat canary failed; restarting recorded MLX PID {pid}.", flush=True)
        terminate_recorded_server(state, "chat_canary_failed")
    elif model:
        raise RuntimeError(
            "An unmanaged MLX model endpoint is available, but the chat canary failed; no process was signaled."
        )
    from urllib.parse import urlparse

    url = urlparse(os.environ["WINGPT_API_URL"])
    if url.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Automatic startup is limited to a local model service.")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log = RUNTIME / "logs" / f"mlx-{stamp}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    args = [
        sys.executable,
        "-m",
        "mlx_lm",
        "server",
        "--model",
        os.environ["WINGPT_MODEL"],
        "--host",
        "127.0.0.1",
        "--port",
        str(url.port or 8000),
        "--decode-concurrency",
        "1",
        "--prompt-concurrency",
        "1",
        "--prefill-step-size",
        "512",
        "--prompt-cache-size",
        "1",
        "--prompt-cache-bytes",
        "2GB",
        "--max-tokens",
        os.environ.get("WINGPT_MAX_TOKENS", "4096"),
    ]
    with log.open("ab") as output:
        process = subprocess.Popen(
            args, stdout=output, stderr=subprocess.STDOUT, start_new_session=True
        )
    state = {
        "pid": process.pid,
        "model": os.environ["WINGPT_MODEL"],
        "log": str(log),
        "command": args,
        "status": "starting",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    write_state(state)
    print(f"Starting MLX PID {process.pid}; log: {log}", flush=True)
    for attempt in range(180):
        if process.poll() is not None:
            state.update({"status": "exited", "returncode": process.returncode})
            write_state(state)
            raise RuntimeError(
                f"MLX exited {process.returncode}: {log.read_text(errors='replace')[-5000:]}"
            )
        if identity() and chat_canary():
            state.update(
                {"status": "ready", "ready_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            )
            write_state(state)
            print("MLX service ready with the requested local model.", flush=True)
            return
        if attempt % 15 == 0:
            print("Waiting for MLX model initialization...", flush=True)
        time.sleep(2)
    terminate_recorded_server(state, "startup_timeout")
    raise RuntimeError(f"MLX startup did not become ready; inspect {log}")


def stop_server():
    state = read_state()
    if not state:
        print("No project-managed MLX service recorded.")
        return
    if terminate_recorded_server(state, "requested"):
        print(f"Stopped project-managed MLX PID {state['pid']}.")
    else:
        print("Recorded process no longer matches; no signal sent.")


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
    checkpoint = ROOT / ".runtime" / "codex-home" / "tasks" / f"{task_hash}.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    with checkpoint.with_suffix(".runner.lock").open("a") as lock:
        if "--autonomous" in arguments:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with (RUNTIME / "startup.lock").open("a") as startup_lock:
            fcntl.flock(startup_lock, fcntl.LOCK_EX)
            start_server()
        node = RUNTIME / "tools" / "bin" / "node"
        command = [
            str(node),
            str(ROOT / "codex-cli" / "bin" / "codex.js"),
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
            start_server()


def main():
    action, *arguments = sys.argv[1:]
    if action == "run":
        return run_agent(arguments)
    with (RUNTIME / "startup.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if action == "start":
            start_server()
        elif action == "stop":
            stop_server()
        elif action == "status":
            state = read_state()
            model_ready = bool(identity())
            canary_ready = model_ready and chat_canary()
            print(
                json.dumps(
                    {
                        "ready": canary_ready,
                        "model_endpoint_ready": model_ready,
                        "chat_canary_ready": canary_ready,
                        "metal_oom_detected": recorded_metal_oom(state),
                        "managed_process_running": recorded_process(state),
                        "service": state,
                    },
                    indent=2,
                )
            )
        else:
            raise ValueError(f"Unknown action: {action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
