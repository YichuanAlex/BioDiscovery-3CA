# R8 工程验证（2026-09-13）

CORE_TEST_EXIT_CODE=0
FULL_TEST_EXIT_CODE=1
AUTONOMOUS_PROBE_EXIT_CODE=0
DESKTOP_ACTION_STATUS=failed
R8_DESKTOP_TOOLS=not_exposed

最终核心测试真实进程 PID 6080 已退出，2026-09-13 08:21:28 +08:00 回读 exit 0，stdout 含 core functional test completed; desktop action NOT certified。原始证据：logs/engineering-core-final.stdout.log、logs/engineering-core-final.stderr.log。覆盖项目路径/全局环境隔离、恢复及 resume、工具参数/预算/重复护栏、共享 CLI 目录/文件/归档安全、函数桥有效有界 JSON、MCP 十项工具、真实 Qwen 模型及原生工具协议、附件、文件/shell、实际联网与完整 rollout。联网冒烟按六轮内的一次真实搜索及来源答复检查，不验证新闻的编辑质量或事实真伪，不证明科研结果。

独立真实自主工程探针使用 Qwen3.5-4B，4 次响应均实际返回 reasoning、thinking 开启；写入 probe.txt 后 shell 回读并提交原真实验证 ID。实际 exit 0、completed_candidate；监督者独立核对内容恰为 ENGINE_R8_OK，12 字节，SHA-256 a352eadd74f120100609d4a3940f0b231b9389e89e148da1ef07aef191301a7c。证据：engineering-probe-checkpoint.json、logs/engineering-autonomous.stdout.log 和原始 rollout-2026-09-13T08-04-07-15842bb9-ca4.jsonl。工程探针及 mock 不进入 R8 研究区、不提供研究对象或答案。

完整测试首次 PID 9456 实际 exit 1，Computer Use 报 failed to activate captured window。只读桌面检查为可读的 Default，并非已确认锁屏；按恢复规则刷新唯一新测试窗口重试一次仍失败，停止桌面输入，不更改权限或登录界面。两次自建 Character Map 测试进程已核对身份后关闭。原始完整失败日志 logs/engineering-full.stdout.log / stderr 保留，不覆盖为成功。桌面动作未修复或认证，默认完整测试仍要求此路径通过。

首次 core-only PID 27008 的新闻自由对话未收束，且实际进程参数显示 PowerShell 5 把无 BOM 脚本中文字面量读成乱码。只停止工程新闻 Node 23448 后实际 exit 1；证据 logs/engineering-core-first.stdout.log / stderr。随后测试脚本实际转换为 UTF-8 BOM（EF BB BF），最终进程参数已确认正确中文；联网测试增加明确上限及实际最终答复/来源检查，超限或停滞不算通过。研究 prompt.txt 由 Node 显式 UTF-8 读取，与上述 shell 字面量路径不同。

R8 专用科研启动验收使用核心检查 0 + 原任务不暴露 computer_use 的条件，manifest 明确记录 core_passed_desktop_action_failed，不宣称完整测试通过。已按引擎原任务判定规则去除路径再检查 R8 提示，桌面工具检测结果为 false；正式首个模型请求另作只读核对。研究不依赖桌面动作，不能借此声明整个桌面能力正常。

实际本地 /v1/models 已核对：id=Qwen3.5-4B，root=/mnt/c/Users/User/Desktop/agentic/model/Qwen3.5-4B，max_model_len=65536。复用现有 vLLM 0.28.0 / transformers 5.17.0，原生工具 parser=qwen3_coder、reasoning parser=qwen3，文本任务 language-model-only；自主执行仍用实际服务约束的 JSON 行动。模型目录 C:\Users\User\Desktop\agentic\model\Qwen3.5-4B，权重未修改。model-start 日志和正式 manifest 保存实际路径/身份及配置、索引、聊天模板哈希，未复制大型权重。

R8 开始时研究区为空，不复制 R1–R7 或标准 Codex 的科研代码、计算结果或报告。允许可追溯的公开原始缓存复用，但新任务初始资产记忆为空，监督者不注入旧数据集 ID、资产路径、分析方法或研究答案。核心测试成功、原 reasoning 存在与模型身份正确都不证明长期无循环或科学成功；结构完成与科学验收分离。R8 同时修改工作流和模型，不单独归因后续差异。无 Rust 修改，未声称运行 Rust 格式化或测试。

## 正式启动后的只读核查

2026-09-13 08:22:16 +08:00 启动 R8，PowerShell 运行器 PID 22196、实际科研 Node PID 22360，命令行使用项目内 codex.js、--autonomous、--max-rounds 0、四项必需产物和 UTF-8 prompt.txt。20 个关键工作流文件（含共享 CLI 源码与实际安装模块）副本/哈希已冻结；正式启动后不修改引擎、科研代码或提示。模型 ID 与实际 /v1/models 根路径均为指定 Qwen。

原始首个 model_request 的 runtime_context 是 JSON 字符串，正确解析后 advertised_tools 为 20 项且明确不含 computer_use；catalog_references 与 asset_references 都为真正的空数组、预算为零、workspace_version=0。不是用不存在字段的 null 或 PowerShell @($null).Count 代替核验。首分钟快照为运行中、10 次真实 reasoning / thinking、7 个结构化行动、6 个已返回工具、0 个错误/护栏、0 个冻结差异和科研提示干预；3 次引擎续行仍表示任务未完成，不作为研究成果。研究区文件 0、必需产物 0/4，科学验收 pending。
