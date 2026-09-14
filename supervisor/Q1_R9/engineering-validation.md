# R9 启动前工程验证

2026-09-13 08:57 +08:00，Windows PowerShell 非桌面核心集成测试真实退出码：

CORE_TEST_EXIT_CODE=0
R9_DESKTOP_TOOLS=not_exposed

- 完整输出：logs/engineering-core.stdout.log、logs/engineering-core.stderr.log；stdout 包含 `workflow_codex core functional test completed; desktop action NOT certified`。
- Node/PowerShell 语法检查通过；恢复回归真实退出 0，覆盖目录边界、原结果回用、资产引用、检索预算、格式验收、持久化错误、单任务锁与码 75 恢复。
- 项目 Node 入口实际带 `--no-maglev`；当前 Node 24.15.0 接受该参数。核心测试经此入口完成真实 Qwen 模型、工具协议、文件、附件、联网、shell、3CA CLI/MCP、JSONL 与环境隔离检查。
- 实际模型身份：Qwen3.5-4B，root=/mnt/c/Users/User/Desktop/agentic/model/Qwen3.5-4B，max_model_len=65536。
- Computer Use 桌面动作的既有激活失败没有被改写为通过；R9 自主科研任务不暴露 computer_use。核心通过不代表桌面能力正常，也不代表科学研究已完成或正确。
- R8 原始日志、冻结副本和失败终态保留；本轮不恢复 R8 陈旧 `running` 检查点，不复制其研究选择或计算结果。
