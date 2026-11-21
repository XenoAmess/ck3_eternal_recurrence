# Q44实际Native资格与R61重复SAVE副本退役

2026-11-22，machine_id: 4-8e1c2f1861。本记录只覆盖已完成的Native资格及闭场后私有重复副本清理；R61整案PARTIAL、四笔有限现货成交和426项软件验证保持各自范围。

## Q44实际构建与有限资格

源码 `7e19220153d6c6dcf25b8bf4cdcb96234a708e4a` 的原 `NATIVE-v21-Q44-01` 退出0／124.9841107秒，公共资格消费者为PASS。发布DLL为13,535,232字节，SHA-256 `307a3cb5336fa373a519a4a4d51a24bf999b98770ccf81643126601151558df4`；本文只引用原产物收据，没有重新读取DLL。

实际profile含235项开关，FileAPI为268／581／1个生产TU，总计850。原1873字节构建日志实际包含10条Building CXX和3条Linking；依赖决策里的112是元数据对象行，不是112次重新编译，更不是850个TU全部重编。原日志的vswhere找不到提示保留，随后vcvarsall完成x64初始化且构建实际成功；不能只取前一条提示改写原退出0。

22项旧有限fixture按真实依赖复用，本轮新执行0项；另一个新增letter-set OFF测试实际执行一次并退出0，原起止19:26:09.445121→19:26:09.564593 UTC。235／850／22已从上一批软件期望变为本次对应实际配置和有限资格，但不授Game业务、气泡显示、26785313异版本能力或全产品通过。631／411及426等历史软件数不与旧22复用重复相加。

## 4份私有副本真实退役，2项跳过

R61正常闭场并释放后，有限PLAN原进程退出0／10.5707027秒，APPLY退出0／8.5771957秒。以下路径均在已闭场的 `C:/workspace/ck3-market-live-20261121r/managed-states/financial-coin25/state/profile/` 内：

| 原私有路径 | 实际处理 | 对应保留档 |
| --- | --- | --- |
| `last_save.ck3` | 已删除，旧路径不可读 | R61 terminal |
| `save games/autosave.ck3` | 已删除，旧路径不可读 | R61 terminal |
| `save games/autosave_1.ck3` | 已删除，旧路径不可读 | R61 baseline |
| `save games/xar_checkpoint.ck3` | 已删除，旧路径不可读 | R61 terminal |
| `save games/autosave_2.ck3` | 缺失，SKIP，未退役 | 无 |
| `save games/restored_campaign.ck3` | 不匹配本场完整hash白名单，SKIP，未退役 | 未作删除判断 |

实际删除4份，共856649944逻辑字节，即3份terminal重复副本和1份baseline重复副本。两份唯一外部归档完整保留，原APPLY已逐项完成完整SHA和身份保持读回；本文不重读存档。原metadata、raw、审计、失败日志、源码及账本均未删除，也没有删除唯一外部SAVE。

卷空闲前后观察及差额保留，但差额不全部归因本次删除。旧spent不退、下一场容量不由此获批；不能把副本退役当新保存日或业务进展。所有删除／SKIP原件和外部来源见[有限证据索引](../../docs/maintenance/evidence/2026-11-22-financial-markets-native-q44-and-r61-retirements.json)。

## 资源与下一范围

Q44原512MiB峰值预算、owner上限307837684738字节及全部旧spent保持，没有退款或新场自动准入。本批没有新Game、SAVE、气泡送达或Workshop首发信用，完整产品未完成。

下一步从已保存R61的真实BUY372重新核实合约、资金和独立受益人后尝试真正新SHORT；当前没有SELL不能靠制造对手补齐，旧151减仓也不保证成交。登记通知仍受实际发行冷却资格约束，不清变量或按tick臆算日期。
