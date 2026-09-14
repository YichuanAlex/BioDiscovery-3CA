# Q1 R3 自主工作流监督

## 边界

- 工作流：`C:\Users\User\Desktop\agentic\workflow_codex`。
- 研究目录：`C:\Users\User\Desktop\agentic\3CA\Q1_R3`。
- 监督目录：`C:\Users\User\Desktop\agentic\supervisor\Q1_R3`。
- `Q1_R1`、`Q1_R2` 和标准 Codex 产物只供监督者在任务结束后只读比较，不输入 Qwen3.5-4B。
- 只有项目内 Qwen3.5-4B 编写研究代码、下载数据、执行分析和撰写报告。监督者只优化启动前工作流工程、冻结版本、启动、读取日志和验收；不选择数据集、不提供统计方法/参考数字、不写或修改研究产物、不发送研究纠错提示。

## R2 证据驱动的启动前修复

- 自主模式所有请求保持 thinking；日志分别保存请求状态和接口实际 reasoning，恢复会话首条为 session_meta。
- 工具长输出限制为首尾 6000 字符；3CA catalog 的长返回进一步保持为可解析 JSON，并注明总数和返回条目数。
- 同一工作区版本下完全相同的调用只执行一次；3CA catalog 搜索有界，达到上限后要求使用已有 study id 进入 study/asset 阶段或记录具体阻塞。
- 项目 ThreeCA skill 只加入“有效结果后停止枚举、截断时收窄过滤、函数工具可用时不绕到 CLI”的通用路由，没有加入 Q1 研究答案。

完整工程测试、冻结哈希和正式启动时间在后续写入。本文件的启动前内容不代表研究完成。

## 启动前验证

2026-09-12 完成 Node/PowerShell 语法、ThreeCA skill 格式、恢复回归和完整集成测试，全部退出 0。第九次 3CA catalog 搜索阻断的独立回归确认其他工具仍可完成任务。当前无交互终端，Computer Use 输入动作按测试设计 SKIP；该模块未修改且此前真实动作闭环通过，不能把这次 SKIP 单独称为动作通过。详细记录见 `engineering-validation.md`。

## 正式启动

2026-09-12 17:45:21 +08:00 从空的 `C:\Users\User\Desktop\agentic\3CA\Q1_R3` 启动，运行器 PID 3812、Node 子进程 PID 9032。原始提示 SHA-256 为 `0baa8b29bfef9887295520a7b1582ec333496912d92a80cf0339000ae6276e24`；11 个关键工作流文件及哈希保存在 `run-manifest.json` 和 `frozen-workflow`。运维重启 0、研究干预 0、semantic acceptance pending。

只读 heartbeat `Qwen3.5-4B-q1-r3` 每 15 分钟观察重要变化；无变化保持安静，到失败或完成终态后暂停。首次快照为 3 轮、3 个工具返回、0 失败、3/3 thinking enabled、3/3 实际 reasoning、研究产物 0。模型自行调用 list_files 和两次 web_search；这只是运行开始，不是研究质量证明。

## 最终结果

R3 于 2026-09-12 17:47:17 +08:00 失败结束。最终为 20 轮、30 个工具返回、1 个失败、16 个重复或预算护栏返回；20/20 模型请求 thinking enabled，20/20 实际返回 reasoning，缺失 reasoning 为 0。原始用户输入 1、引擎续行 0、监督者研究输入 0、运维重启 0。

模型在有限 web/3CA 检索中获得主页和一份含可行 study id 的 `cancer` catalog 结果，但没有进入 `get_study`、`plan_asset`、`download_asset` 或工作区写入。它使用了系统明确不支持的 Unix `head -30`，该 PowerShell 调用失败；随后自行去掉 `head` 并成功读取 CLI help，说明具备一次局部纠错。此后它仍多次请求相同 CLI help 和已调用的 catalog/page 查询，护栏阻止执行，但没有促使模型换成下一阶段行动。

终态 checkpoint=`needs_attention`，phase=`start`，next_action 仍为 `inspect available tools and task sources`，错误为 `Autonomous recovery exhausted without verified progress`。研究目录文件 0，四项必需产物均不存在，semantic acceptance=`not_accepted`。`runner-result.json`、`audit.json`、`tool-timeline.csv`、`logs` 和 isolated rollout 保存完整失败证据。11 个冻结文件重新计算后哈希差异 0；heartbeat 已暂停，不重启、不补研究提示。

R3 相比 R2 的可确认改善仅是日志完整性和更早止损：R2 第三次 31 轮后失败且 15 次 thinking 被关闭；R3 20 轮失败但 20/20 thinking/reasoning 完整、无基础设施中断。任务完成率仍为 0，不能称长程能力变好或接近标准 Codex。
