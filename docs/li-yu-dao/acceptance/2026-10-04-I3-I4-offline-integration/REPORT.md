# I3/I4 离线内容与领导机制集成检查

结论：冻结输入通过 **10 项 L0 集成检查**；16 个对真实脚本或生成器的独立突变均被目标断言检出。实机、原生 scope 校验、领袖继承、冷却自然到期、存档重载与完整玩家同意流程均为 **NOT_RUN**。不能将此报告改记为 live GREEN。

候选源文件为 [test_content_leadership.py](test_content_leadership.py)，导入目标为 `mod_li_yu_dao/tools/test_content_leadership.py`；以 Python 标准库 unittest 加仓库已有 Clausewitz 结构解析器及玩家入口检查函数运行，没有复制或模拟游戏业务状态机。

输入绑定基准提交 `01b4dda39505929c1245de699e67862f4130a02e` 上的新 I3/I4 未提交工作树。完整 103 文件逐字节快照及 SHA 见 [INPUTS.json](INPUTS.json)。实际运行版本和最终逐文件复核见 [DELIVERY.json](DELIVERY.json)；结果只能适用于其中的精确字节，不能外推为已提交版本。

检查覆盖：36 学统从入口菜单可达并可返回；翻页、打开、关闭及取消不写状态；每项礼仪分派到自己有玩家与资金门禁的实践；旧 8 个事件 ID 与 24 个基础资源/经验结果保留；个人改派只用单角色 setter 与 365 天等待期；C3 工厂与钩子唯一正式 owner，默认 C2 生成器不能覆盖正式根；challenger 默认关闭，私人师承不伪造 HoR；迁移前清理只删除对应 owned claim office；退休/辞任只处分已捕获的专属头衔，宗主承认只授予原宗主头衔或新建专属头衔；玩家主动入口与目标同意回调分离，议礼回调重新验证提案序号和受影响玩家同意。

原始通过记录：[第二次基线 stderr](baseline-run-002/stderr.txt)、[命令/退出码/字节哈希](baseline-run-002/result.json)。基础 stress/XP 数值指脚本输入；引擎特质修正与舍入没有在这些检查中执行。

突变有效性证据：[完整 16 项汇总](mutation-run-001/SUMMARY.json)。覆盖旧事件错派、旧奖励变化、不足资金仍执行、孤立菜单页、取消/翻页写状态、个人改派迁移全项礼仪、共享生成器覆盖、开启未验原生 challenger、假 HoR setter、删除外来或合法宗主头衔、AI 主动发起、无关师长接受、绕过玩家拒绝及迁移漏清 claim office。每个目录保留精确 argv、返回码、stdout/stderr、原始与突变文件 SHA；完整突变源码仅保存在外置目录，从未装载。

首轮测试有 3 个断言不符现有授权边界：错误要求清理伴随钩子嵌入共享钩子，而实际由 C2 按顺序调用；错误排除新建专属头衔的授予；错误把 C2 自动递送议案视作 C3 主动 AI 门禁。修正后的检查分别验证实际调用顺序、被授予头衔的具体 scope、递送链不能提交归属变更。[原始首轮结果](baseline-run-001/stderr.txt) 与 hash 匹配的 [初版测试源码](test_content_leadership.initial-v1.py) 保留。这些失败属于测试假设，未发现需要修改产品源码的集成失败。

运行命令（导入后）：`python -B mod_li_yu_dao/tools/test_content_leadership.py`。外置候选使用 `LYD_CONTENT_TEST_SOURCE` / `LYD_CONTENT_TEST_REPO` 指向冻结输入；实际环境与命令已保存在 raw receipts。
