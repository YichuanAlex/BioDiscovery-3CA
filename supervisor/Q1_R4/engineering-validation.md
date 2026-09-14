# R4 启动前工程验证

FULL_TEST_EXIT_CODE=0

- 工作流根目录：`C:\Users\User\Desktop\agentic\workflow_codex`。
- Node 语法和恢复回归退出 0。
- 参数规范化回归确认键顺序不能绕过重复调用检测。
- 单工具临时熔断回归确认第二次重复后只隐藏该工具一个模型响应，其他工具保持可用。
- 3CA catalog 回归确认第八次实际搜索后 `search_studies` 不再出现在工具列表，写文件、PowerShell 和完成工具仍可继续。
- 完整 `test-Qwen3.5-4B.ps1` 退出 0：路径隔离、本地模型、恢复、实际 reasoning 保存、3CA CLI/MCP、文件、附件、联网、写入、shell 和 JSONL 会话记录通过。
- 本次 Computer Use 实际完成应用枚举、启动、选择、观察、输入动作及动作后观察，没有被标记为 SKIP。

这些是工程门槛，不是 R4 科学质量或长程完成能力证明。
