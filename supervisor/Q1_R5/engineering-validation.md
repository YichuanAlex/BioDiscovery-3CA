# R5 启动前工程验证

FULL_TEST_EXIT_CODE=0

- 工作流根目录：`C:\Users\User\Desktop\agentic\workflow_codex`。
- Node 语法、PowerShell 5.1 解析、R5 启动器 Probe 和只读审计初始状态通过。
- until-complete 回归确认 `--max-rounds 0` 越过旧的连续无动作终止点，记录 loop recovery 后仍可写入、验证并完成。
- catalog CLI 预算拒绝回归确认 PowerShell 冷却一个响应、其他工具可继续，后一响应 PowerShell 自动恢复。
- path-only shell 回归确认非动作路径被拒绝且不能冒充成功验证。
- 完整 `test-Qwen3.5-4B.ps1` 退出 0：隔离、本地模型、reasoning、ThreeCA CLI/MCP、文件、附件、联网、写入、shell 和 JSONL 会话记录通过。
- 本次宿主无交互式终端，Computer Use 运行时、应用枚举和观察通过，输入动作按测试设计 SKIP；模块未修改，R4 启动前另有真实动作闭环通过证据。

这些是工程门槛，不是 R5 科学质量或长程完成能力证明。
