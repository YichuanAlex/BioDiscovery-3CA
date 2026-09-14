# R2 结束后的工作流验证

- R2 冻结运行终态：失败；checkpoint `needs_attention`；研究产物 0；不重启、不改研究目录。
- 定向恢复回归：退出 0；覆盖自主模式持续 thinking、实际 reasoning 保存、恢复首条 session_meta、未知修改不重放、持久化重试、产物格式门槛。
- 真实 Qwen3.5-4B 日志探针工作区：`C:\Users\User\Desktop\agentic\tmp\reasoning-probe-20260912-1729`。
- 探针会话：`C:\Users\User\Desktop\agentic\workflow_codex\.runtime\codex-home\sessions\2026\09\12\rollout-2026-09-12T17-31-01-1696bdf7-e75.jsonl`。
- 探针结果：3 个 assistant 响应；3 次 thinking requested/enabled；3 次实际 reasoning；3 个 reasoning 原文项；首条为 session_meta；`probe.txt` 精确内容为 `REASONING_LOG_OK`。
- 完整 `test-Qwen3.5-4B.ps1`：退出 0；包括真实本地模型、项目内 3CA MCP/CLI、Computer Use 动作闭环、文件、附件、网络、PowerShell、会话日志和隔离测试。

以上验证只适用于 R2 结束后的当前工作流，不属于 `frozen-workflow-attempt3`，不改变 R2 not_accepted 结论。
