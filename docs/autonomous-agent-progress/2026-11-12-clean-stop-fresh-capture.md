# 正常停止后用真实 fresh READ 补齐捕获观察

实际57和60在周期已结算、pending为空后正常停止，却因 readiness 先看到 stop 而没有新 Known.observation，clean capture 退为 BATCH_DEFERRED；后继必须完整回放 saved history。本单元只在原 capture 抛出 MissingDriverObservation 时补一次真正 fresh 全状态 READ，再走原 capture。原第一次借用 writer 和 Controller CAS 已退出后才发 READ；negative dispatch／原包仍先归档，成功则核原 ACK、snapshot 时序与有限 deadline，用真实 frozen raw producer 形成 Complete，退出冻结与 writer 后再捕获。没有复用旧 SEM、假设 current snapshot、吞 UNKNOWN 或改停止／账本守卫。

实际单 TU／23类型首次编译0，原完整23类型和全部旧 public／protected API 保留；新增私方法使它不是 body-only。正式 Saved 变体只移同一方法与 import，另做必要单 TU／23类型首次0，ACTUAL1602B／`23ef3a9d618a0d229f4000da3afb23f6704282eb13405e90fff4fddf136d35d7`，CLOSE204B／`c1f1c056cf525a3ba01cb7cbe06b9312d2e7079b2bf9ab701cc416914f24b1b8`；不以 actual 编译替代 formal。

新增 qualification 测试是实际软件 fresh 协议与原 Controller／writer／Driver 的边界验证：真实 READ history 发布清空 observation 后，第一次捕获必须不写 WAL／不变 head，且退出 writer 与 CAS；真实 ACK／snapshot 经原 producer 形成 Complete 后，第二次原 capture 与 admission 回读完整 Driver、Controller 零 credit。另测 negative ACK、missing ACK 和真实 UNKNOWN 仍拒捕获。原首编 boxed assert 重载歧义保留，revision02仅显式解箱；完整四项首次4P／0F／0E／0skip、POST输入不变、CLOSE释放。ACTUAL1443B／`072069970132dcc4f2fb892f0b07cf02f48f668acda669b5a38b3d21062b1eaa`，CLOSE204B／`e3e76217279ab16ef71e7d85440e6a9a29e3d165f5a549b793f71941035ccfce`。

该测试位于 src/qualification，实际独立编译闭包使用冻结原 ActionWriterIntegrationFixture117170B／`7b271da6a8fca5f0d871a62f361792f1820891bafc6e3067d91813f1c5196899`，不是默认全树 CI；没有发行 Managed／RootSession 或调用私有 wrapper。正式单叶 typing、上述实际边界4P和未来正常 ownedStop 的完整组合分别记账；当前不授 RootSession 整体成功、捕获延迟收益或新增保存日，不为本单元停止正在执行的 Game 动作。

本地模型提供方法主体候选，owner修正 writer scope 退出边界、typed interrupt、一次原包归档及有限错误文本；独立 helper实现真实边界用例。原件位于 D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/clean-stop57-{compile01,test-compile01,test-compile02,junit01,formal-compile01}。机器 xenoamess-full-tower-eb9d2c1186，2026-11-12。
