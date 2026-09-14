# Q1 R4 自主工作流监督

## 边界

- 工作流：`C:\Users\User\Desktop\agentic\workflow_codex`。
- 研究目录：`C:\Users\User\Desktop\agentic\3CA\Q1_R4`。
- 监督目录：`C:\Users\User\Desktop\agentic\supervisor\Q1_R4`。
- `Q1_R1`、`Q1_R2`、`Q1_R3` 和标准 Codex 产物只供监督者在任务结束后只读比较，不输入 Qwen3.5-4B。
- 只有项目内 Qwen3.5-4B 编写研究代码、下载数据、执行分析和撰写报告。监督者只优化启动前工作流工程、冻结版本、启动、读取日志和验收；不选择数据集、不提供统计方法或参考数字、不写或修改研究产物、不发送研究纠错提示。

## R3 证据驱动的启动前修复

- 工具参数在共享重复检测入口递归规范化，避免 JSON 键顺序绕过护栏。
- 同一规范化调用第二次被拒绝后，只在下一次模型响应临时隐藏该工具一轮，随后恢复；这不替模型选择下一工具。
- 实际完成八次 catalog 搜索后，直接 `search_studies` 从后续工具列表移除；study、asset、文件、PowerShell 和完成工具保持可用。
- 没有把 R1/R2/R3 或标准 Codex 的研究对象、方法、代码、数字或结论写进 R4 工作流或提示。

完整工程测试、冻结哈希和正式启动时间在启动后追加。本文件的启动前内容不代表研究完成。

## 启动前验证与正式启动

2026-09-12 完成 Node 语法、恢复/熔断永久回归和完整 `test-Qwen3.5-4B.ps1`，全部退出 0。完整测试本次实际完成 Computer Use 的应用枚举、启动、选择、观察、动作和动作后观察，没有 SKIP；详见 `engineering-validation.md`。这些检查只证明工程入口，不证明科学任务质量。

R4 于 2026-09-12 17:59:17 +08:00 从空的 `C:\Users\User\Desktop\agentic\3CA\Q1_R4` 启动。运行器 PID 22516、Node 子进程 PID 21400；原始提示 SHA-256 为 `41930e686f8c3be873c708ed3cf2e988425cab63f1e6acd417dbefdeb0a26a71`。11 个关键文件与哈希保存在 `run-manifest.json` 和 `frozen-workflow`；启动后复核哈希差异 0。运维重启 0、研究干预 0。

只读 heartbeat `Qwen3.5-4B-q1-r4` 每 15 分钟运行 `audit-r4.mjs`，只在实质变化、完成、失败、冻结差异或需要用户操作时通知；不得修改研究目录、工作流或向模型追加提示，终态后暂停。

## 首轮运行观察（非终态）

约 26 次模型响应时，26/26 thinking 开启且 26/26 实际返回 reasoning；51 个工具返回、8 个失败、24 个重复/预算护栏返回，研究文件仍为 0。模型曾自行从 catalog 转向 `get_study(3ca:20755)`，这是 R3 没有达到的阶段；但随后又以多个不同搜索词绕到 PowerShell，并把 Skill 名 `threeca-access` 当成不存在的函数工具调用 6 次。达到预算后的目录调用被护栏拒绝，但参数彼此不同，因此“相同调用第二次临时熔断”尚未触发。

这只是运行中快照。当前进程仍在运行、runner-result 尚不存在，不能判定成功或失败；监督者没有据此纠正研究路线、修改冻结引擎或重启任务。

## 最终结果

R4 于 2026-09-12 18:07:52 +08:00 自主失败结束，运行约 8 分 34 秒。最终 checkpoint=`needs_attention`、phase=`start`、rounds=48，错误为 `Autonomous recovery exhausted without verified progress`。49/49 次模型响应请求 thinking 且接口实际返回 reasoning，缺失 reasoning 为 0；84 个工具结果中 8 个失败、45 个为重复或预算护栏、触发 1 次单工具临时熔断。原始用户输入 1、监督者研究干预 0、运维重启 0。任务目录文件 0，四项必需产物 0/4，semantic acceptance=`not_accepted`。终态前 11 个冻结文件哈希差异 0。

R4 相比 R3 确实越过了工具阶段：调用 `get_study` 6 次、`plan_asset` 2 次、`download_asset` 4 次，实际下载了两个 study 的 data/metadata 到工作流本地缓存并记录字节数与 SHA-256。但模型没有把任何 provenance、代码、分析或报告写入任务目录。下载后它把压缩包绝对路径本身当作 PowerShell 命令；该无动作命令返回空输出和 exit 0，被旧进度判断误记为成功验证。之后又连续请求已封顶的 catalog CLI 搜索，最终由连续八轮无进展阈值结束。

新熔断只处理同一规范化调用的第二次重复。R4 大量使用不同搜索词，或在 catalog 已封顶后第一次发出新的 PowerShell 搜索字符串，因此绕过“相同调用”计数；预算分支也没有把被拒绝的工具放入下一响应冷却。这解释了 45 个护栏结果和仅 1 次熔断。R4 终态已固化；监督 heartbeat 的暂停操作由应用返回成功，随后其本地 automation 文件不再存在，不再声称仍有活跃 R4 监督。
