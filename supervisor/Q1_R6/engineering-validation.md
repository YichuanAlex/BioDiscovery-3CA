# R6 启动前工程验证

2026-09-12 23:05 +08:00，Windows PowerShell 完整集成测试真实退出码：

FULL_TEST_EXIT_CODE=0

- 完整输出：logs/engineering-full.stdout.log、logs/engineering-full.stderr.log；stdout 包含最终 functional test completed 标记。
- 自主恢复回归、Windows 路径路由、无写入探索恢复、检索预算持久化、陈旧 running/码 75 恢复、排他锁释放全部通过。
- 3CA MCP 初始化、10 个工具枚举与实际调用通过。
- 本轮 Computer Use 实际完成枚举、启动、选择、观察、动作、再观察；不是 SKIP。
- 本地 Qwen3.5-4B 模型、工具协议、联网、文件、附件、受限写入、shell、原始会话事件及环境隔离通过。
- Node 语法、R6 PowerShell 脚本语法/Probe 通过；test-audit-r6.mjs 的原始日志镜像回读与去重检查通过。
- 测试进程退出后，测试启动的后台服务持有输出通道，已通过原项目停止入口关闭，使外层正常取得真实退出码。正式 R6 由其原启动入口重新加载服务；没有中断研究进程。

这些结果支持工程入口可运行，不代表科学研究已完成或正确。监督者未在研究目录放置代码、数据选择或答案。
