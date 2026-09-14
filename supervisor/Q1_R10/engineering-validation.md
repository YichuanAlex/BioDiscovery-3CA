# R10 启动前工程验证

2026-09-13 09:29 +08:00，Windows PowerShell 非桌面核心集成测试真实退出码：

CORE_TEST_EXIT_CODE=0
R10_DESKTOP_TOOLS=not_exposed

- 完整输出：`logs/engineering-core.stdout.log`、`logs/engineering-core.stderr.log`；stdout 包含 `workflow_codex core functional test completed; desktop action NOT certified`。
- 正式 Node 入口固定到项目内官方 Node 24.21.0（libuv 1.52.1）；下载包按 Node 官方 `SHASUMS256.txt` 校验，ZIP SHA-256 为 `158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541`。
- 恢复回归真实退出 0，覆盖目录边界、原结果复用、资产引用、检索预算、格式验收、持久化错误、单任务锁与码 75 恢复。
- 核心测试完成真实 Qwen 模型、工具协议、文件、附件、联网、shell、3CA CLI/MCP、JSONL 与环境隔离检查。
- 实际模型身份：Qwen3.5-4B，root=`/mnt/c/Users/User/Desktop/agentic/model/Qwen3.5-4B`，max_model_len=65536。
- Computer Use 桌面动作的既有激活失败没有被改写为通过；R10 自主科研任务不暴露 `computer_use`。核心通过不代表桌面能力正常，也不代表科学研究已完成或正确。
- R9 原始日志、冻结副本和失败终态保留；本轮不恢复 R9 的陈旧 `running` 检查点，不复制其研究选择或计算结果。
