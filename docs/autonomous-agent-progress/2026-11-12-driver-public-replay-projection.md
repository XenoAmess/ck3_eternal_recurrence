# 公共 Driver 原件回放也复用同调用投影

先前同调用投影复用仅覆盖 Loader.load。公共 Reader replay 与 captured replay 的 null-decoder 分支仍走普通 assemble，再由 Complete 重复投影。本单元让这两个严格解析出口交给既有私构造 nominal 值，再进入一个包内 replay 方法复用私有一次 token。第一投影仍放在原 public replay 的 catch 内，因此投影错误仍返回原 Incomplete；Loader.load 独立首投影在 catch 外的抛错语义不变。

原 raw framing／hash／manifest／完整 Driver 解码、callback 与 decoder getter 的顺序、packet 私副本、公开 assemble／projectFull／Complete 构造器及 token 消费／finally 均保留。正式两叶机械适配已有 NativePacketInput／parsedNode／completeValidatedIdentity，没有以实际运行变体整叶覆盖，也不把缓存扩到下一调用或下一轮。

实际变体必要两 TU／9类，加独立 Test 两类，完整四项首次4P。正式不同变体另做必要两 TU／12类，复用未改的同一 Test 两类对正式产物运行完整四项，实际4P／0F／0E／0skip；不以 actual 通过替代 formal。测试真实 public／captured 路由的 profile1／4 和 null／非null decoder，逐字段与原 public 组装对照；真实坏 nativeRef 保持 Incomplete，早期 raw／Driver hash 仍抛错，Loader 原首投影仍抛错；另测 callback 次序、null／错误同对象、caller packet 在 callback 后才 clone、nested replay 和之后公开伪 Full 仍拒。原 Loader 三项没有被算作这条新路径覆盖。

正式 ACTUAL1618B／`aaece6c53bb6bc7aa8270802832eb3e20cd919688157aa0c150814264885efaa`，whole4 ACTUAL1463B／`c35e7bbcb8f2606cc3d456267c8be4d71acd6542a3cab6784c1c82d062704719`、CLOSE204B／`b8a6f444ae473efeb8911ab26518c21031203fc6fb76a2fa1c4c912312d14609`。原件在 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/driver-public-formal52-{compile01,test12-junit01}/actual/prod`。机器 `xenoamess-full-tower-eb9d2c1186`，2026-11-12离线资格。正式 Test 使用现已同源的原 Helper；没有重编旧测试或整树。

实际核心三个生产 edit 来自本地模型完整候选，owner补显式 null 先序；正式版本由 owner按已有私有 packet 路径机械移入。独立测试由 owner12 实现。本次软件通过不授总墙钟／新增保存日提速。实际52与Snapshot54已由Runtime60在真实已停边界采用，正常入口恢复和后继实耗仍按真实回执记录；本次正式发表不要求再装载或重启。
