import importlib.util
import json
import signal
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).with_name("macos_runtime.py")
SPEC = importlib.util.spec_from_file_location("macos_runtime", MODULE_PATH)
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class FakeProcess:
    pid = 4321
    returncode = None

    def poll(self):
        return None


class MacosRuntimeTest(unittest.TestCase):
    def test_chat_canary_uses_chat_completion(self):
        with (
            mock.patch.dict(
                runtime.os.environ, {"WINGPT_MODEL": "/models/qwen"}, clear=False
            ),
            mock.patch.object(
                runtime,
                "request",
                return_value={"choices": [{"message": {"content": "OK"}}]},
            ) as request,
        ):
            self.assertTrue(runtime.chat_canary())

        self.assertEqual(
            request.call_args,
            mock.call(
                "/v1/chat/completions",
                {
                    "model": "/models/qwen",
                    "messages": [{"role": "user", "content": "Reply OK."}],
                    "max_tokens": 1,
                    "temperature": 0,
                },
            ),
        )

    def test_start_restarts_only_recorded_pid_after_metal_oom(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime_dir = root / ".runtime" / "macos"
            (runtime_dir / "logs").mkdir(parents=True)
            state_path = runtime_dir / "server.json"
            old_state = {
                "pid": 1234,
                "model": "/models/qwen",
                "log": str(runtime_dir / "logs" / "old.log"),
            }
            environment = {
                "WINGPT_API_URL": "http://127.0.0.1:8000/v1",
                "WINGPT_MODEL": "/models/qwen",
                "WINGPT_MAX_TOKENS": "4096",
            }
            with (
                mock.patch.object(runtime, "ROOT", root),
                mock.patch.object(runtime, "RUNTIME", runtime_dir),
                mock.patch.object(runtime, "STATE", state_path),
                mock.patch.dict(runtime.os.environ, environment, clear=False),
                mock.patch.object(
                    runtime,
                    "identity",
                    side_effect=[{"id": "/models/qwen"}, {"id": "/models/qwen"}],
                ),
                mock.patch.object(runtime, "chat_canary", side_effect=[False, True]),
                mock.patch.object(runtime, "read_state", return_value=old_state),
                mock.patch.object(runtime, "recorded_metal_oom", return_value=True),
                mock.patch.object(
                    runtime, "terminate_recorded_server", return_value=True
                ) as terminate,
                mock.patch.object(
                    runtime.subprocess, "Popen", return_value=FakeProcess()
                ),
                mock.patch.object(runtime.time, "sleep"),
            ):
                runtime.start_server()

            terminate.assert_called_once_with(old_state, "metal_oom")
            state = json.loads(state_path.read_text())
            self.assertEqual(state["pid"], 4321)
            self.assertEqual(state["status"], "ready")

    def test_start_restarts_recorded_pid_after_chat_canary_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime_dir = root / ".runtime" / "macos"
            (runtime_dir / "logs").mkdir(parents=True)
            state_path = runtime_dir / "server.json"
            old_state = {
                "pid": 1234,
                "model": "/models/qwen",
                "log": str(runtime_dir / "logs" / "old.log"),
            }
            environment = {
                "WINGPT_API_URL": "http://127.0.0.1:8000/v1",
                "WINGPT_MODEL": "/models/qwen",
                "WINGPT_MAX_TOKENS": "4096",
            }
            with (
                mock.patch.object(runtime, "ROOT", root),
                mock.patch.object(runtime, "RUNTIME", runtime_dir),
                mock.patch.object(runtime, "STATE", state_path),
                mock.patch.dict(runtime.os.environ, environment, clear=False),
                mock.patch.object(
                    runtime,
                    "identity",
                    side_effect=[{"id": "/models/qwen"}, {"id": "/models/qwen"}],
                ),
                mock.patch.object(runtime, "chat_canary", side_effect=[False, True]),
                mock.patch.object(runtime, "read_state", return_value=old_state),
                mock.patch.object(runtime, "recorded_metal_oom", return_value=False),
                mock.patch.object(runtime, "recorded_process", return_value=True),
                mock.patch.object(
                    runtime, "terminate_recorded_server", return_value=True
                ) as terminate,
                mock.patch.object(
                    runtime.subprocess, "Popen", return_value=FakeProcess()
                ),
                mock.patch.object(runtime.time, "sleep"),
            ):
                runtime.start_server()

            terminate.assert_called_once_with(old_state, "chat_canary_failed")
            self.assertEqual(json.loads(state_path.read_text())["status"], "ready")

    def test_return_75_stops_after_three_retries_of_same_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime_dir = root / ".runtime" / "macos"
            runtime_dir.mkdir(parents=True)
            workspace = root / "workspace"
            workspace.mkdir()
            checkpoint = self._checkpoint(root, workspace, version=7)
            result_75 = mock.Mock(returncode=75)
            with (
                mock.patch.object(runtime, "ROOT", root),
                mock.patch.object(runtime, "RUNTIME", runtime_dir),
                mock.patch.object(runtime, "start_server"),
                mock.patch.object(
                    runtime.subprocess, "run", return_value=result_75
                ) as run,
                mock.patch.object(runtime.time, "sleep") as sleep,
            ):
                returncode = runtime.run_agent(
                    ["--autonomous", "--workspace", str(workspace)]
                )

            self.assertEqual(returncode, 75)
            self.assertEqual(run.call_count, 4)
            self.assertEqual(
                [call.args[0] for call in sleep.call_args_list], [3, 6, 12]
            )
            data = json.loads(checkpoint.read_text())
            self.assertEqual(data["status"], "needs_attention")
            self.assertEqual(
                data["runner"],
                {
                    "status": "needs_attention",
                    "updated_at": mock.ANY,
                    "reason": "checkpoint_version_retry_limit",
                    "returncode": 75,
                    "checkpoint_version": "7",
                    "checkpoint_version_retries": 3,
                    "total_retries": 3,
                },
            )

    def test_return_75_has_five_retry_total_limit_across_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime_dir = root / ".runtime" / "macos"
            runtime_dir.mkdir(parents=True)
            workspace = root / "workspace"
            workspace.mkdir()
            checkpoint = self._checkpoint(root, workspace, version=0)
            versions = iter([1, 1, 2, 2, 3, 3])

            def interrupt(_command, **_kwargs):
                data = json.loads(checkpoint.read_text())
                data["version"] = next(versions)
                checkpoint.write_text(json.dumps(data))
                return mock.Mock(returncode=75)

            with (
                mock.patch.object(runtime, "ROOT", root),
                mock.patch.object(runtime, "RUNTIME", runtime_dir),
                mock.patch.object(runtime, "start_server"),
                mock.patch.object(
                    runtime.subprocess, "run", side_effect=interrupt
                ) as run,
                mock.patch.object(runtime.time, "sleep") as sleep,
            ):
                returncode = runtime.run_agent(
                    ["--autonomous", "--workspace", str(workspace)]
                )

            self.assertEqual(returncode, 75)
            self.assertEqual(run.call_count, 6)
            self.assertEqual(
                [call.args[0] for call in sleep.call_args_list], [3, 6, 12, 24, 48]
            )
            data = json.loads(checkpoint.read_text())
            self.assertEqual(data["runner"]["reason"], "total_retry_limit")
            self.assertEqual(data["runner"]["total_retries"], 5)

    def test_termination_records_state_and_normalizes_signal_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "server.json"
            state = {"pid": 1234, "model": "/models/qwen", "status": "ready"}
            with (
                mock.patch.object(runtime, "STATE", state_path),
                mock.patch.object(
                    runtime, "recorded_process", side_effect=[True, False]
                ),
                mock.patch.object(runtime.os, "kill") as kill,
            ):
                self.assertTrue(runtime.terminate_recorded_server(state, "requested"))

            kill.assert_called_once_with(1234, signal.SIGTERM)
            recorded = json.loads(state_path.read_text())
            self.assertEqual(recorded["status"], "stopped")
            self.assertEqual(recorded["stop_reason"], "requested")
            self.assertEqual(runtime.normalized_returncode(-signal.SIGTERM), 143)

    @staticmethod
    def _checkpoint(root, workspace, version):
        resolved_workspace = workspace.resolve(strict=True)
        task_hash = runtime.hashlib.sha256(
            str(resolved_workspace).lower().encode()
        ).hexdigest()[:24]
        checkpoint = root / ".runtime" / "codex-home" / "tasks" / f"{task_hash}.json"
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_text(json.dumps({"version": version, "status": "interrupted"}))
        return checkpoint


if __name__ == "__main__":
    unittest.main()
