import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).with_name("macos_runtime_api.py")
SPEC = importlib.util.spec_from_file_location("macos_runtime_api", MODULE_PATH)
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class ApiRuntimeTest(unittest.TestCase):
    def test_request_uses_bearer_without_persisting_secret(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = b'{"data":[]}'
        with (
            mock.patch.dict(
                runtime.os.environ,
                {
                    "DEEPSEEK_API_KEY": "sk-test-secret-value",
                    "WINGPT_API_URL": "https://api.deepseek.test",
                },
                clear=False,
            ),
            mock.patch.object(runtime.urllib.request, "urlopen", return_value=response) as urlopen,
        ):
            self.assertEqual(runtime.request("/models"), {"data": []})
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.deepseek.test/models")
        self.assertEqual(request.headers["Authorization"], "Bearer sk-test-secret-value")

    def test_ensure_api_records_only_credential_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "api.json"
            environment = {
                "DEEPSEEK_API_KEY": "sk-test-secret-value",
                "WINGPT_API_URL": "https://api.deepseek.test",
                "WINGPT_MODEL": "deepseek-v4-pro",
            }
            with (
                mock.patch.object(runtime, "STATE", state),
                mock.patch.dict(runtime.os.environ, environment, clear=False),
                mock.patch.object(runtime, "identity", return_value={"id": "deepseek-v4-pro"}),
                mock.patch.object(runtime, "chat_canary", return_value=True),
                mock.patch.object(runtime, "thinking_tool_canary", return_value=True),
            ):
                runtime.ensure_api()
            saved = state.read_text()
            self.assertNotIn(environment["DEEPSEEK_API_KEY"], saved)
            self.assertEqual(json.loads(saved)["credential_source"], "environment")

    def test_thinking_tool_canary_replays_reasoning(self):
        first = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "reasoning_content": "Use the preflight tool.",
                        "tool_calls": [
                            {
                                "id": "preflight-1",
                                "type": "function",
                                "function": {
                                    "name": "report_ok",
                                    "arguments": "{}",
                                },
                            }
                        ],
                    }
                }
            ]
        }
        second = {"choices": [{"message": {"role": "assistant", "content": "OK"}}]}
        environment = {
            "WINGPT_MODEL": "deepseek-v4-pro",
            "WINGPT_REASONING_EFFORT": "max",
            "WINGPT_API_USER_ID": "api_test",
        }
        with (
            mock.patch.dict(runtime.os.environ, environment, clear=False),
            mock.patch.object(
                runtime, "request", side_effect=[first, second]
            ) as request,
        ):
            self.assertTrue(runtime.thinking_tool_canary())
        follow_up = request.call_args_list[1].args[1]["messages"][1]
        self.assertEqual(follow_up["reasoning_content"], "Use the preflight tool.")
        self.assertNotIn("tool_choice", request.call_args_list[0].args[1])

    def test_run_agent_uses_api_entry_and_bounded_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime_dir = root / ".runtime_api"
            runtime_dir.mkdir()
            source_runtime = root.parent / "workflow_codex" / ".runtime" / "macos"
            (source_runtime / "tools" / "bin").mkdir(parents=True, exist_ok=True)
            workspace = root / "workspace"
            workspace.mkdir()
            codex_home = root / "isolated-codex-home"
            checkpoint = codex_home / "tasks"
            task_hash = runtime.hashlib.sha256(str(workspace.resolve()).lower().encode()).hexdigest()[:24]
            checkpoint.mkdir(parents=True)
            checkpoint_file = checkpoint / f"{task_hash}.json"
            checkpoint_file.write_text(json.dumps({"version": 1, "status": "interrupted"}))
            with (
                mock.patch.object(runtime, "ROOT", root),
                mock.patch.object(runtime, "RUNTIME", runtime_dir),
                mock.patch.dict(
                    runtime.os.environ,
                    {"CODEX_HOME": str(codex_home)},
                    clear=False,
                ),
                mock.patch.object(runtime, "ensure_api"),
                mock.patch.object(runtime.subprocess, "run", return_value=mock.Mock(returncode=75)) as run,
                mock.patch.object(runtime.time, "sleep"),
            ):
                self.assertEqual(
                    runtime.run_agent(["--autonomous", "--workspace", str(workspace)]),
                    75,
                )
            self.assertEqual(run.call_count, 4)
            command = run.call_args_list[0].args[0]
            self.assertTrue(command[1].endswith("codex_api.js"))


if __name__ == "__main__":
    unittest.main()
