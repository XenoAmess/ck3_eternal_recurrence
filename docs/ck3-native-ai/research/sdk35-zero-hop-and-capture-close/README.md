# 原生零跳与录像关闭次序

`machine_id: xenoamess-full-tower-eb9d2c1186`。本批接续公共 `41846f49`，不修改冻结 SDK、运行中的游戏／OBS 或任何场次队列。稳定连续30年优先，之后低于1秒／日、再0.5秒／日，目标均未达；旧窗口30失败58日保留。

Native22 的最小修复只在已发布 `complete_empty` 路线、无移动目标、常规且未战斗／撤退、目标为当前位置时，直接通过现有 `BuildActiveRouteTimeline` 读真实 CUnit MovePath。它同时核验 Native 空路径与实际省份指针；Python 空数组不能制造零跳证明。完整敌军、接敌区间、两次独立采样与暂停时钟守卫继续执行。公共只加21行并扩既有 route fixture，保留主线后来加入的9行 movement cutoff 读回；没有整叶覆盖。实际编译来源为 routes `8486de95…`、bridge `55cc0bd6…` 的 typed_early 分派，11906旧 reader 不在本次生产路径。

公共两源已实际 MSVC `/W4 /WX` 编译并执行，覆盖 stationary self-target、snapshot／Native path不一致、战斗拒绝、同省敌军及一日边界接敌；没有在测试中调用游戏。新测试 EXE 的精确 Defender 登记已使用实际成功编译参数，实际结果仍为 `admin_required_for_verified_readback`，没有 Add 或 SYSTEM 生效信用。18MB DLL、334头全量 manifest 与测试二进制不入 Git，仅保留[小来源投影](NATIVE22-SOURCE-FREEZE-SUMMARY.json)和[公共编译结果](PUBLIC-NATIVE-ZERO-HOP-VALIDATED.json)。Root 已报告新 Game263980 冷载 Native22 `db399c0e…`、保留原日期53483040／12448周期；零跳业务实证另待 Root 健康链，不能以离线夹具替代。

旧录像约21.23GB。保留的 closed-probe 文件时间到 completed 内联 SHA 后时间约218.234秒，这段包含元数据开销，不能当作孤立 SHA CPU 时间。旧90秒关闭期限失败、Game6068强退exit1和后到的OBS正常exit0并列保存，不把迟到完成改写为原关闭流程成功。[有限计时与原件哈希](CAPTURE-FINALIZATION-OBSERVATION.json)不读取或复制原视频。

新的主仓 `tools/ck3_obs_capture.py` 只调整其受管 CK3 采集生命周期：解除 Game／overlay custody、独立确认 OBS 正常关闭后，原子发布 `capture_closed`，再由非 daemon 后台线程完成原有全片 SHA 和 `completed`。采集关闭与完整媒体完整性分开；哈希失败单独保留，不伪造完成。公开源码保留已有 `GetParent==0` 主窗口选择守卫；仅录游戏模式从已有 `started.json` 的真实 Game 出生绑定关闭证明，不使用该模式本来为空的 placement 字段。录制引擎及其 CK3 进程身份契约是现有主仓适配器，通用宣传视频渲染／审计仍归独立 `xar_promo_toolchain`，本包不 vendoring 其源码或第三方依赖。

R4 首 worker 因私有加载器覆盖 PYTHONPATH 而缺 `psutil`，属于环境失败，原件保留。依赖恢复后的[新OBS增长小回执](ROOT-NATIVE22-RECORDING-VERIFIED.json)只证明6秒增长5,222,400B，原回执还明确地图／overlay像素审阅待定；这不证明新版异步结束阶段已经实机通过，也不是30年稳定或成片人工验收。

公共只读 API `tools/ck3_capture_closed_receipt.py:validate_capture_closed_receipt` 及录制适配器的 `read_capture_closed_receipt` 显式接受已准入 session、Game出生、worker身份和输出根，只校验小回执／输出大小，不观察或关闭进程、不读视频正文。真实公共producer→wrapper→reader测试在completed尚不存在时通过，媒体SHA仍明确未验证。原R4关机场次harness的小研究patch保留，公共仓库没有整套替换它，也没有新增自动关Game／OBS的CLI。

两处 battle／committed-route modal 消费者沿用原 Native clock、cancel／idle、完整敌军、战斗和根绑定，只结算真实已推进日期，不给 UI 或战争业务信用。原非modal输出等价与4个生产链／48否例的正式队列复核保全。公共可复用消费函数明确依赖正式 SDK 验证器，不称为无SDK的自含队列；原场次整份262KB canonical不复制进产品源，runtime SHA-loader 小增量单列研究原件。

WAL 默认关闭且 SDK35 未采用；同一份真实基线报告已在[第八包](../sdk34-refuge-and-readback/DRIVER-PERSIST-FINDINGS.md)入库，不重复搬旧实现。37次life中23次可能替换小记录，0.0585秒／日只是该离线窗口写盘成本上限，未实机提速。另存[路线时钟报告](ROUTE-CLOCK-SPEED-REPORT.json)：56个实际路线日全部速度3，AUTO中位1.3848秒、54组H1中位0.3554秒、完整query→metrics中位2.2929秒，仅具名样本；速度5候选仍默认关、当前35不采用，旧5e7001分类增量将来必须重合到2748更新边界。它没有新Native API或实际收益信用。

- [精确小原件索引](SOURCE-PINS.json)
- [公共Native最小增量](PUBLIC-NATIVE-ZERO-HOP.patch)与[录制适配器小增量](PUBLIC-OBS-CAPTURE-CLOSE.patch)
- [旧游戏关闭边界](ROOT-NATIVE21-LATE-CLOSED-BOUNDARY.json)与[原期限失败](ROOT-RECORDING-SHUTDOWN.original.json)
- [modal独立复核](MODAL-INDEPENDENT-REVIEW.json)、[正式队列](MODAL-FORMAL-QUEUE-TESTS.json)、[非modal等价](MODAL-NONMODAL-EQUIVALENCE.json)及[公共／Native修订分离](MODAL-WIRE-REVISION.json)

原件中的绝对路径仅标识当时的外置来源，不是公共 API 的运行前提。当前候选／实机／仍未知分别保留；后续实际健康与连续窗口需追加新证明，不能从源码、录制增长或关闭 ACK 推导。

本批提交前的较新实际补记：Root已审地图／Native22＋P35 overlay并[准入首帧](ROOT-FIRST-FRAME-ADMITTED.json)，watchdog也[实际启动并观测6秒增长2,916,352B](ROOT-WATCHDOG-DEPENDENCIES02-VERIFIED.json)。AUTO22真实零跳horizon available、subject空路线、敌军ETA53483280、one_day_contact_free=true，Native clock generation1／tick1／overshoot0／paused把53483040推进到53483064。[精确完成包字段投影](ACTUAL-NATIVE22-ZERO-HOP-AND-CLOCK.json)仅保原件SHA与必要证明。旧55b分类器随后因只允许moving phase而拒绝stationary phase，FULL21失败；Root正做同SDK分类修复及原22重消费，不能重执行时钟。以上证明Native零跳及一天确已生效，**不证明外层连续推进已恢复，新窗口31尚未准入**；异步hash关闭阶段仍未实机验收。
