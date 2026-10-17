# SDK38 出版等待与派系行动边界

机器：`xenoamess-full-tower-eb9d2c1186`。2026-10-17 公共第16批；来源与原字节 SHA 见[有限证据索引](research/sdk38-publication-and-gift/SOURCE-PINS.json)。本批只移植窄差分，保留公共 HolySite、M6、Clan 和前端接入，不用冻结 SDK 整叶覆盖主线。

正式 Crown／Construction 提交后，资源字段可能先于 Native revision 发布。普通 `GameplayBridgeService.plan_turn` 现在先识别持久 pending，最多等待5秒的新 owner 帧，再选择独立 receipt；资源值改变不会被当作 actor 改变。等待中的每个新帧都重新计算事件、通知、终态、战果窗口和战争优先级。新 UI／战争走完整普通规划器，未知或多份 pending 保留；既有安静地图单日观察资格不提供业务成功信用。

赠礼的 publication waiter 同样只比较角色稳定 ID 和 alive，而不因 gold／opinion 字典更新提前结束。新的普通自动赠礼必须有同帧、同派系及同收礼人的 Native stock danger 观测；单纯合法或有钱不授权花钱。旧 pending、receipt、cold reconciliation 和 checkpoint／submit 正向断言保留。真实旧 AUTO515 曾花100金，后续531有独立 receipt；这一事实不能证明派系已解散，也不能给新选择规则记省钱实测。

Native24 修复两个来源：既有 prewar V2 provider／mailbox／main-thread executor 已在源码表，正式 CMake 默认启用它；赠礼独立 receipt 成功序列化后才释放 pending 锁，并保存完整终态观测，允许丢回复时重读同一 receipt。失败不清锁，重读不重发旧动作，新赠礼重新建立 pending。公共共享 header 的实际构建必须重编 bridge、gift12004、gift12002、nonwar12002 四个消费者；没有新增测试 EXE 目标。

后续实机反例：Native24 虽发布 V2 capability，AUTO398 的 prewar 查询仍报 `mailbox_submit_unavailable`。Root／源码 owner 已定位外置增量链接误复用宏 OFF 的 `main_thread_query_mailbox` object，而 capability／provider 宏为 ON；因此 hello／默认开关不证明 executor whitelist 同步，更不证明首次主动战争成功。正式构建须逐项核所有宏消费者的实际 object、编译宏与链接输入，不能只检查改动 TU／capability。公共 CMake 同一 target 的 compile definition 会覆盖消费者；Native25 单 object 修复及真正 TrySubmit 夹具仍属后继，未给本批追记成功。

公共 Python 普通链32项、6子例和四类资格／账本绑定13项、56子例通过。Native24 原冻结生产闭包45 checks 通过；源码 owner 再核公共 header／router／test 与该 fixture 编译输入逐字节相同，实际调用既有 `RunGiftFixtureNative24()` 再得45 checks PASS，无 Game／pipe。没有重新执行公共 CMake target，也没有重链 DLL 或新 EXE；精确回执另存。不把这一离线结果当作实机业务通过。Root 已报告 Native24 冷恢复新 Game246608；本包不自行查询现场，不给 SDK38 业务链、稳定30年或性能目标预记成功。

四个公共纯资格函数分别保留 construction executor 前拒绝、first-heir 七个 PRE-read 拒绝、派系 receipt 前的 publication wait，以及业务 submit 的 Native admission 拒绝。最后一种原动作是业务尝试，不能因旧框架 `read_only_precondition` 标签改称只读查询；Python submission-started ledger 仍保留，恢复不重放、不授业务／日期信用。未知错误、during-read、timeout 和业务后验不借这些规则放行。

`campaign_continuity_binding` 先验证已存在的首 FULL，再核 campaign／runtime／queue 和注入的官方 Game 代绑定，只设置新加载 feeder 的账本路径。它不写账本、不打开窗口、不修改 frame／counter，也不代替完整接续资格。实际旧 launcher 的错误路径、修正事件和最小研究差分都保留；未来 watchdog renderer 的路径修正从未作为实际完整接续部署。

观众元数据另抽两个正常 import 的小模块，5项、4子例通过。audience binding 只修 `session=runtime_root` 与独立 recording SID，原字节快照／审计 create-only，替换要求调用者拥有唯一写入权；它不是系统级多写者 CAS，也不制造修复事件。前端 publisher 仅把尚未建立合法 gameplay baseline 的缺文件视为 unknown，不造0周期；已见真实 baseline、clean／cold verified marker、损坏 JSON 或权限错误仍保留真实错误。进度 resolver／reason／applied 的后继适配另批处理，不把这两个 API 当作完整 watcher 已部署。

新目标仍是1066罗贝尔干净局，旧成绩、Driver、goal 与天数不继承。先连续稳定30年，再低于1秒／日，再0.5秒／日；均未达。旧 R37 已闭33日片段约0.491秒／日只是一段无 SAVE 的样本，不是整局平均或扩大 peace horizon 的依据。录制从主菜单起，默认停顿头尾各2秒／中段4秒；最终 PTS、像素验收和通用电影引擎继续归独立 promo 工具链。本批不读媒体、不编码、不切换现场。
