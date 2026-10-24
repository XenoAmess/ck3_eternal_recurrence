# 制作与发布状态

本次用户指令：依次完成需求文档、测试方案、编码、测试验收、发布。开始时间 2026-10-24；本机 `machine_id: desktop-3fevhd2-1c74096080`。

| 阶段 | 当前事实 | 依据 |
| --- | --- | --- |
| 需求 | 已制定版本 1 | [requirements.md](requirements.md) |
| 测试方案 | 已制定版本 1，尚未授予测试通过 | [test-plan.md](test-plan.md) |
| 编码 | 首版候选已实现，17文件正式清单、Java／Quarkus构建、独立验收夹具 | [既有可行性研究](feasibility-2026-10-24.md)与产品源码 |
| 测试验收 | 最终离线构建、原生测试、宿主注册与类型范围检查通过；扩展夹具已解析；首轮实机业务 RED，修复后待重新验收 | [最终干净提交构建回执](acceptance/offline-build-clean-checkout-2026-10-24.json)、[SDK回归](acceptance/rite-confirmation-sdk-2026-10-24.json)、[共享服务绑定](acceptance/rite-service-factory-2026-10-24.json)、[原生测试](evidence/native-religion-fixtures-2026-10-24.json) |
| 发布 | NOT_PUBLISHED，Workshop ID 未分配 | 待业务验收及正式发布闭环 |

工具链已在以上机器原位升级默认 Maven 3.9.16→3.10.0，PATH与原配置保留；实际来源和读回见[环境回执](evidence/environment-maven-2026-10-24.json)。本任务已取得共享策略下的有限容量准入，见[首次存储回执](evidence/environment-storage-2026-10-24.json)及[实际回收与重新准入](evidence/environment-storage-recovery-2026-10-24.json)：当前期限内预留为 C 4GiB、D 32MiB。这些资格不代表游戏业务已通过。

截至2026-10-24T09:02Z，首轮候选已完成最终离线准备：Java／Quarkus构建10项测试全部通过，17文件清单及既有清单消费者一致；启用14项所需能力的原生DLL已生成，三个原生测试在受管构建目录实际通过并取得SYSTEM精确路径登记回执。早先空EXE尾钩失败、外置来源登记拒绝及UAC取消仍保留为原始事实，没有将其标成成功。

SDK的19项礼仪回归及4项共享服务绑定回归通过；真实运行解释器离线注册220个工具，所需旧工具全部保留，与新接口使用同一个实际服务。冷加载完整CI命令组和严格检查的准确范围见[离线类型检查](acceptance/offline-types-2026-10-24.json)，旧大模块的遗留错误未被冒充为全绿。以上均为离线结果，实际游戏尚未启动，宗族迁移、犯罪理由、赦免、自然出生、存档恢复等业务继续等待原版界面与原生后态验收。正式发布状态仍为NOT_PUBLISHED。

2026-10-24T09:12Z 补记：首次固定提交56d5627的产品CI和SDK CI均已实际success，见[云端回执](acceptance/hosted-ci-2026-10-24.json)。固定提交换行与旧工作树打包资源不一致曾被生成器拒绝；已从该干净提交重建，10/10及15资源精确比对通过。公共plan与prepare已通过；第一次allocate在分配ID前因新产品不在共享canonical key表而退出1，未启动游戏，正在修复该登记项。原始失败保存在C盘任务证据根，不能从这些准备结果推导业务或发布完成。

2026-10-24T09:59Z 实机更新：R0001已真实启动，发现不可玩角色教学错误与共享推进scope缺失，尚未完成任何GUI业务phase，结果RED；原版GUI正常退出0、原始宿主退出1、公共run退出2、原生清理通过、keeper退出0、CAS8596释放。详见[R0001不可覆盖的失败记录](acceptance/R0001-2026-10-24.json)。源码修复正在准备，不能把静态或闭场通过改写成业务通过。

2026-10-24T10:22Z 修复准备：仅对原版可玩角色传授选项知识，全员归族与犯罪规则不缩减。修改的5个脚本增量语法解析通过，CK3 1.20.0.4语义profile仍不受离线工具支持，见[解析回执](acceptance/playable-knowledge-parser-2026-10-24.json)。九语发布构建合同14项测试通过，当前真实源仍是中英开发包，尚未写入七语正式译文，见[构建准备](acceptance/release-localization-builder-2026-10-24.json)。两者均不授予新实机或发布通过。

2026-10-24T10:57:55.767374+00:00 后继入口准备完成：原正常退出profile接线的完整7组测试33项及修改范围严格检查通过，见[实际回执](acceptance/managed-exit-wiring-2026-10-24.json)；最终干净候选480ea的Java构建14/14、17文件包和13文件夹具回读通过。新common-runtime-a04已生成，公共plan／prepare实际退出0；尚未启动R0002，业务与发布仍未通过。专项最初两次测试夹具报告写入竞态已修复，原RED保留，生产代码字节未改变。

2026-10-24T11:18:01.579044+00:00 启动前更新：R0002未启动宿主或CK3，实际public run因离线凭据超过冻结守卫的30秒窗口而退出2；keeper合作退出0，CAS8607已释放，见[R0002原件摘要](acceptance/R0002-2026-10-24.json)。业务为NOT_RUN，不存在Game退出码。原先60秒的口头说法已按pinned源码纠正。2afe的[产品CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40088035978)及[SDK CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40088035992)实际成功；[cold CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40088036030)在232套件中出现1失败和1错误，均为新profile必填检查误阻旧v1/v2只读验证。正在恢复历史读取与实际launch检查的正确边界，并补既有unrun消费者的真实pre-intent拒绝闭场路径。后继完整相关回归和新冻结场次尚未通过。

2026-10-24T12:38Z 恢复执行：机器身份重新核验为 `desktop-3fevhd2-1c74096080`，实际 EXE SHA 与 1.20.0.4/build25734779 基线一致，后台 Steam 新观察为 offline；无 CK3 进程。任务容量已从关闭状态重新原子准入到 r1158/storage46，期限2026-10-25T07:30Z。R0003 的公共 verify 实际退出2，case/gui/business/release均未通过；其真实原生同handle退出0与资源闭场消费者通过只授资源结束，原业务RED及normal-close=false保留。见[R0003摘要](acceptance/R0003-2026-10-24.json)。四个fixture修正与新等待规则已形成3592360干净候选，正在重新Maven构建；共享正常闭场typed路由和完整回归仍在施工。尚未分配下一场或发布Workshop。

2026-10-24T12:43Z 离线增量完成：新干净候选Java构建15项JUnit通过，15打包资源、17文件正式开发包/ZIP和13文件core fixture逐字节一致；已线性rebase并推送master b4a58ed38。R0001旧GUI和R0003真实typed原件均通过共享资源消费者，资源22项、同CI step余13+12及历史20项通过，strict仅覆盖8个完整实际定义与实际分派。详见[恢复构建与typed闭场](acceptance/resumed-fixture-and-typed-closure-2026-10-24.json)。不授业务或正常闭场通过，原R3 RED不变；下一场所需无错误typed正常闭场仍在完整共享CI验证中。

2026-10-24T13:19Z 共享正常关闭软件路径完成：新增独立typed路由，实际保留原handle精确FILETIME，校验原fact/close/once claim与冻结profile/source inventory；GUI review仍为null，autosave完整性资格仍false。正常关闭原组40项及7个完整新增顶层定义strict通过。原共享CI step全部91条命令均已真实执行并取得0，期间环境依赖和旧fixture/source兼容失败分次修复，原RED保留；不将它们写成一次无失败执行或实机通过。尚待全新runtime、R0004实际业务与正常退出验收。

完整命令及修复出处见[typed正常闭场与91条共享CI](acceptance/typed-normal-close-and-full-shared-ci-2026-10-24.json)。Windows短TEMP修复后的5c6cc产品CI已实际success，远端runner机器ID未采集；不外推为本机游戏通过。
