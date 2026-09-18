"""Project-local MLX service lifecycle and locked, resumable CLI runner."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime" / "macos"
STATE = RUNTIME / "server.json"


def request(path):
    url = os.environ.get("WINGPT_API_URL", "http://127.0.0.1:8000/v1").removesuffix("/v1") + path
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.load(response)


def identity():
    try:
        data = request("/v1/models")
        expected = os.environ["WINGPT_MODEL"]
        return next((item for item in data.get("data", []) if item["id"] == expected), None)
    except (OSError, ValueError):
        return None


def start_server():
    if identity():
        print("MLX service ready; reusing the requested model.")
        return
    from urllib.parse import urlparse
    url = urlparse(os.environ["WINGPT_API_URL"])
    if url.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Automatic startup is limited to a local model service.")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log = RUNTIME / "logs" / f"mlx-{stamp}.log"
    args = [
        sys.executable, "-m", "mlx_lm", "server", "--model", os.environ["WINGPT_MODEL"],
        "--host", "127.0.0.1", "--port", str(url.port or 8000),
        "--decode-concurrency", "1", "--prompt-concurrency", "1",
        "--prefill-step-size", "512", "--prompt-cache-size", "1",
        "--prompt-cache-bytes", "2GB", "--max-tokens", os.environ.get("WINGPT_MAX_TOKENS", "4096"),
    ]
    with log.open("ab") as output:
        process = subprocess.Popen(args, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    STATE.write_text(json.dumps({"pid": process.pid, "model": os.environ["WINGPT_MODEL"], "log": str(log), "command": args}, indent=2))
    print(f"Starting MLX PID {process.pid}; log: {log}", flush=True)
    for attempt in range(180):
        if process.poll() is not None:
            raise RuntimeError(f"MLX exited {process.returncode}: {log.read_text(errors='replace')[-5000:]}")
        if identity():
            print("MLX service ready with the requested local model.", flush=True)
            return
        if attempt % 15 == 0:
            print("Waiting for MLX model initialization...", flush=True)
        time.sleep(2)
    raise RuntimeError(f"MLX startup did not become ready; inspect {log}")


def stop_server():
    if not STATE.exists():
        print("No project-managed MLX service recorded.")
        return
    state = json.loads(STATE.read_text())
    pid = state["pid"]
    # Only signal a process whose command still identifies this project's server.
    result = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
    if result.returncode == 0 and "mlx_lm" in result.stdout and state["model"] in result.stdout:
        os.kill(pid, signal.SIGTERM)
        print(f"Stopped project-managed MLX PID {pid}.")
    else:
        print("Recorded process no longer matches; no signal sent.")
    STATE.unlink(missing_ok=True)


def run_agent(arguments):
    workspace = ROOT
    if "--workspace" in arguments:
        workspace = Path(arguments[arguments.index("--workspace") + 1]).resolve(strict=True)
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
        command = [str(node), str(ROOT / "codex-cli" / "bin" / "codex.js"), "--allow-network", *arguments]
        while True:
            result = subprocess.run(command)
            if result.returncode != 75 or "--autonomous" not in arguments or not checkpoint.exists():
                return result.returncode
            print("Retryable interruption: resuming the same checkpoint.", flush=True)
            if "--resume" not in command:
                command.append("--resume")
            time.sleep(3)
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
            print(json.dumps({"ready": bool(identity()), "service": json.loads(STATE.read_text()) if STATE.exists() else None}, indent=2))
        else:
            raise ValueError(f"Unknown action: {action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
