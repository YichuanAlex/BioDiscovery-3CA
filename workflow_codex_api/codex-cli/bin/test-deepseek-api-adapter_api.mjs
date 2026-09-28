import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { isWindows, shellToolName } from "./wingpt-platform.js";

const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "wingpt-deepseek-api-"));
const workspace = path.join(fixture, "workspace");
const codexHome = path.join(fixture, "codex-home");
fs.mkdirSync(workspace);
process.env.DEEPSEEK_API_KEY = "sk-test-api-workflow-not-a-real-secret";
process.env.WINGPT_PROVIDER = "deepseek-api";
process.env.WINGPT_MODEL = "deepseek-v4-pro";
process.env.WINGPT_API_URL = "https://api.deepseek.invalid";
process.env.WINGPT_CONTEXT_TOKENS = "1000000";
process.env.WINGPT_MODEL_CONTEXT_TOKENS = "1000000";
process.env.WINGPT_MAX_TOKENS = "65536";
process.env.WINGPT_REASONING_EFFORT = "max";
process.env.WINGPT_API_USER_ID = "api_adapter_test";
process.env.CODEX_HOME = codexHome;
process.argv = [
  "node",
  "wingpt_api.js",
  "--autonomous",
  "--allow-write",
  "--allow-shell",
  "--workspace",
  workspace,
  "--max-rounds",
  "0",
  "--require-artifact",
  "result.txt",
  "create result.txt, verify it, and complete the task",
];

let requestNumber = 0;
globalThis.fetch = async (_url, options) => {
  requestNumber += 1;
  assert.equal(options.headers.Authorization, `Bearer ${process.env.DEEPSEEK_API_KEY}`);
  const body = JSON.parse(options.body);
  assert.equal(body.model, "deepseek-v4-pro");
  assert.deepEqual(body.thinking, { type: "enabled" });
  assert.equal(body.reasoning_effort, "max");
  assert.equal(body.user_id, "api_adapter_test");
  assert.equal("chat_template_kwargs" in body, false);
  assert.equal("temperature" in body, false);
  assert.equal("tool_choice" in body, false);
  for (const message of body.messages.filter((item) => item.role === "assistant" && item.tool_calls?.length)) {
    assert.equal(typeof message.reasoning_content, "string");
    assert(message.reasoning_content.length > 0);
  }
  if (requestNumber === 1) {
    return {
      ok: true,
      json: async () => ({
        choices: [{
          message: {
            role: "assistant",
            content: "",
            reasoning_content: "Create the required artifact.",
            tool_calls: [{
              id: "deepseek-call-1",
              type: "function",
              function: { name: "write_file", arguments: '{"path":"result.txt","content":"API_ADAPTER_OK\\n"}' },
            }],
          },
        }],
      }),
    };
  }
  if (requestNumber === 2) {
    const prior = body.messages.find((message) => message.tool_calls?.[0]?.id === "deepseek-call-1");
    assert.equal(prior.reasoning_content, "Create the required artifact.");
    const command = isWindows
      ? "if (-not (Test-Path -LiteralPath 'result.txt')) { exit 1 }; Write-Output API_ADAPTER_VERIFIED"
      : "test -s 'result.txt' && printf 'API_ADAPTER_VERIFIED\\n'";
    return {
      ok: true,
      json: async () => ({
        choices: [{
          message: {
            role: "assistant",
            content: "",
            reasoning_content: "Verify the artifact with an executable check.",
            tool_calls: [{
              id: "deepseek-call-2",
              type: "function",
              function: { name: shellToolName, arguments: JSON.stringify({ command }) },
            }],
          },
        }],
      }),
    };
  }
  assert.equal(requestNumber, 3);
  return {
    ok: true,
    json: async () => ({
      choices: [{
        message: {
          role: "assistant",
          content: "",
          reasoning_content: "Submit the verified completion candidate.",
          tool_calls: [{
            id: "deepseek-call-3",
            type: "function",
            function: {
              name: "complete_task",
              arguments: JSON.stringify({
                artifacts: ["result.txt"],
                verification_call_id: "deepseek-call-2",
                summary: "API_ADAPTER_OK",
              }),
            },
          }],
        },
      }],
    }),
  };
};

try {
  await import("./wingpt_api.js");
  assert.equal(requestNumber, 3);
  const taskHash = createHash("sha256").update(fs.realpathSync(workspace).toLowerCase()).digest("hex").slice(0, 24);
  const checkpoint = JSON.parse(fs.readFileSync(path.join(codexHome, "tasks", `${taskHash}.json`), "utf8"));
  assert.equal(checkpoint.status, "completed_candidate");
  const sessions = [];
  const collectSessions = (directory) => {
    if (!fs.existsSync(directory)) return;
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const target = path.join(directory, entry.name);
      if (entry.isDirectory()) collectSessions(target);
      else if (entry.name.endsWith(".jsonl")) sessions.push(target);
    }
  };
  collectSessions(path.join(codexHome, "sessions"));
  assert.equal(sessions.length, 1);
  console.log("PASS: one isolated API session completed write, verification, and complete_task with thinking continuity.");
} finally {
  fs.rmSync(fixture, { recursive: true, force: true });
}
