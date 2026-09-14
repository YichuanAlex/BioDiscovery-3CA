# R3 启动前工程验证

FULL_TEST_EXIT_CODE=0

- 工作流根目录：`C:\Users\User\Desktop\agentic\workflow_codex`；不存在的 `workflow\_codex` 未使用。
- Node 语法检查、PowerShell 5.1 启动器解析、R3 Probe、监督审计初始快照均通过。
- 项目 ThreeCA skill 经 `quick_validate.py` 检查通过。
- 恢复回归退出 0：自主持续 thinking、实际 reasoning 保存、恢复首条 session_meta、持久化重试、未知修改不重放、完成门槛、预算退出和 cookie challenge 拒绝通过。
- 3CA catalog 回归退出 0：超长搜索结果仍可 JSON.parse；第九个不同的 catalog 搜索被阻止，文件、PowerShell 和 complete_task 仍可继续完成探针。
- 完整 `test-Qwen3.5-4B.ps1` 退出 0：隔离、本地模型、tool-call 协议、3CA CLI/MCP、文件、附件、网络、PowerShell 和 JSONL 通过。
- 本次无交互终端，Computer Use 完成运行时加载、应用枚举和观察，输入动作明确 SKIP；相同且本轮未修改的 Computer Use 模块在 R2 启动前已经完成真实启动/选择/观察/动作/再观察闭环。两者不合并冒充本轮真实输入动作。

这些是工程门槛，不是 R3 科学质量或长程完成能力证明。
