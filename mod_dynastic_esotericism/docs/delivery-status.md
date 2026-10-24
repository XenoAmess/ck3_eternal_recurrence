# 制作与发布状态

本次用户指令：依次完成需求文档、测试方案、编码、测试验收、发布。开始时间 2026-10-24；本机 `machine_id: desktop-3fevhd2-1c74096080`。

| 阶段 | 当前事实 | 依据 |
| --- | --- | --- |
| 需求 | 已制定版本 1 | [requirements.md](requirements.md) |
| 测试方案 | 已制定版本 1，尚未授予测试通过 | [test-plan.md](test-plan.md) |
| 编码 | R0007的House作用域修正、真实继承夹具与共享观察合同已形成干净候选1df185f；Java构建16项通过，九语正式24文件另行构建校验通过 | [House修复](2026-10-25-engine-house-dynasty-fix.md)与[后继软件回执](acceptance/r8-software-preparation-2026-10-25.json) |
| 测试验收 | R0007原生取消与实际创建分别有独立后态；创建后的夹具确认被真实产品脚本错误阻断，完整核心仍0/6，等待新候选实测 | [R0007失败与资源终态](acceptance/R0007-2026-10-25.json)、[测试方案](test-plan.md) |
| 发布 | NOT_PUBLISHED，Workshop ID 未分配 | 待业务验收及正式发布闭环 |

截至2026-10-24T18:46:46Z（北京时间10月25日02:46），总体约60%是规划估计；核心0/6、cold/seed/old未完成，Workshop未创建。R0007已原生退出，Game原Popen0、host1、public2、keeper0，SCREEN8743释放；资源终态不授业务通过。后继s08/common-runtime-a08已冻结，公共plan/prepare实际通过；尚未分配或启动R0008，保留a07原件。

2026-10-24T19:21:47Z更新：a08实际allocate在分配ID前退出2，真实Java运行包生产者漏出成员查询的构建证据，未启动Game或keeper。实际Java生产者补一行既有工具登记，原14项编译开关与来源守卫不变；完整Maven16项通过，新增到既有JUnit内的真实Java产物→公共预检正负链已执行。新S09以1df冻结SDK为基线，只接入同一主线Java修复，执行提交为25e7e5；a09真实Java运行包、plan/prepare和实际产物公共预检均通过，仍不授live或业务资格。新core state为a16、keeper为a27，旧a08/a12原件不改。详细[失败、修复与实际生成回执](acceptance/runtime-members-capability-2026-10-25.json)。核心0/6、总体约60%及未发布结论不变，04:00继续汇报实际阶段。

工具链已在以上机器原位升级默认 Maven 3.9.16→3.10.0，PATH与原配置保留；实际来源和读回见[环境回执](evidence/environment-maven-2026-10-24.json)。当前容量依据为机器绑定的 `C:/ck3-dynastic-esotericism-20261024/capacity/SEVEN-POOL6-D28-SCOPE-A16-ADMISSION-r1176.actual.json`（SHA-256 `275e150776a773ed50e5e2c78d829c9665891fd82848d56be54be4a305072ae7`）：七个实际Game profile共用6GiB执行池，另保留a11及a12未启动的旧准备材料；build/test512MiB，D剩余未来28MiB，硬期限2026-10-25T07:30Z。core/seed/cold/old新state分别为a16/a13/a14/a15；本次仅补正未Game旧a12与新a16/a27的scope，预算未增加。已实际checkout的旧incoming不再重复列为未来写入，仍保留两份临时index、objects和bus预算，来源32对象已计实际占用，没有冒充物理回收。C池、系统增长与安全预留均未减少。重型写入及启动前仍须实际新鲜检查；旧4GiB/32MiB记录只作历史。这些资格不代表游戏业务已通过。

当前软件增量：共享目的消费者从原合同顶层消费既有 `allow_actor_change`，真实producer→JSON→host loader→实际driver回归10/10，preserved3/3、offline-TTL6/6及7完整模块strict通过；同一原生成员查询已接通公共只读路由，完整产品CI step六条命令32项退出0。该许可只允许观察合同声明的actor变化，PID/generation/pipe、单调日期与原400日预算继续生效；实际继承和新礼仪领袖仍须原生与保存证据。完整共享91条命令退出0，其中一项HoF原生wire测试缺真实输入，明确NOT_EXECUTED。cold/warm完整30条命令已顺序全部退出0，包含独立Python进程SDK continuation；其中第23条的可选真实小WAL诊断缺输入，明确NOT_EXECUTED，不计全测试零跳过。已修正既有测试合同、两处局部类型推断及其两个来源指纹消费者，并恢复远端已发布的精确Source32历史标签。此前失败保留，不冒充一次无失败执行，也不授实机业务通过。

云端06d2358的产品和线性历史CI已success；Official实际Java两轮各633项通过后，完整parity因缺少真实fixture-production request拒绝，后续step未执行。已保留来源调查与原RED，没有伪造请求、放松guard或报告全仓绿色。以下按观察时间保留历史进展。

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

2026-10-24 R0004 实际增量（machine_id: `desktop-3fevhd2-1c74096080`）：a06 实机发现夹具整句宏日志被引擎拆成未知 effect，完整业务保持 RED。原生 UI 已观察默认“无”、两项教义可选及五名称字段读回；原最终 Can 仍因缺少原版教士傀儡前置而拒绝，未提交创建，已取消草案。原 SDK 同保留句柄退出0、host 原 Popen0、public run2、keeper 原 Popen0，SCREEN8661已释放；完整 normal-close 因共享消费者误将同一 Windows 路径的斜杠表示判为不同来源而失败。见[R0004原件摘要](acceptance/R0004-2026-10-24.json)。

后继已修路径比较合同，并用真实 inventory producer 到 SDK/消费者回归覆盖；正常关闭原四模块42项、原共享CI整组91条命令在一次顺序执行中全部退出0，7个完整修改定义 strict 通过。夹具改用静态日志、保留原完整正负谓词，准备真实原版教士关系前置并提供独立读回；这些软件结果不追认R0004。新干净Java构建、新runtime和后继实机仍待完成。旧867bcd4的Product CI成功，但Official CI另有scope测试导入路径RED，不能称全仓CI通过。实际出处见[后继软件与容量记录](acceptance/R0004-followup-2026-10-24.json)。
