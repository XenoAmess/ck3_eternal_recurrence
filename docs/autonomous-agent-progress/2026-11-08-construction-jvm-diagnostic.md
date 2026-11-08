# P119：一次冷 JVM 的线程 CPU 与 GC 诊断

本次只解释既有 P118 软件 DATA 对照中“主线程 CPU、whole 墙钟和进程 CPU 不同”的现象，没有实现或性能改进。唯一诊断 JVM 使用当前 B 的 SDK17、P117 共同依赖、原 Main03、同一个绝对 CAS／input／source／EXPECTED；六次调用（2 warm＋4 measured）全部 marker 和物理身份检查通过。诊断开销使它不能加入 P118 的 A/B 样本，更不能代表持续 worker、实际 Policy／Native READ 或游戏日速度。

## 实际执行与输出边界

原方案曾请求独立 128MiB 输出空间及 32MiB JFR。没有取得可用的现行分配入口，原 STORAGE-REQUEST01 仅 request_only／admission=false；随后明确撤回，未启动 JFR、repository、decoder 工具 JVM 或第二次业务运行。未借用过期卡或改 Guard／原 64MiB 软件 CAS 配置。旧 P118 文档中的 JFR／GC 是当时的下一步意图，本条记录其最终实际范围。

最终只用已有离线小元数据通道：GC＋safepoint 写入已捕获 stdout，stdout 上限 1MiB、该独立诊断根管理上限 4MiB。实际 stdout 为 23706B，stderr 为 0，分析后具名小根合计 787178B；大 JFR 请求目录另有 44783B 请求／准备元数据，没有 recording。现有源码编译、旧 Test RUN、Main 重编、新 PREP、HTTP、Game／GET／SAVE 均为零。

进程实际是 JDK21.0.10+7-LTS、Serial GC、1 available CPU、Xmx384MiB，没有改 collector 或 JIT 参数。通过已保留的精确子进程 HANDLE 采集线程快照及线程 HANDLE 终态 CPU；没有全系统线程枚举、suspend、线程上下文或 VA clone。17 个已保留线程按出生身份核对，不据 TID 相同认对象相同。

## 可以确认的 CPU 与暂停

| 实际观测 | 数值 |
| --- | ---: |
| 进程累计 kernel＋user CPU | 10.6875s |
| C2 CompilerThread0 CPU | 3.296875s |
| C1 CompilerThread0 CPU | 0.640625s |
| 两编译线程 CPU 合计 | 3.9375s |
| VM Thread CPU，未细分用途 | 1.5625s |
| 4 个未取得名称的线程 CPU 合计 | 5.1875s |
| 17 个 retained thread CPU 总和 | 10.6875s |
| 6 次 Main call 当前线程 CPU／wall | 2.125s／6.4936751s |
| Main setup／序列化前完整 main | 2.1108109s／8.7610659s |

线程 CPU 总和在实际计数精度下等于进程累计 CPU，残差为零；仍不能证明没有短命零 CPU 或被量化为零的线程。没有取得 Main 的 OS TID 名称，那个非零 unnamed 线程仍记 unknown，不能改名为 main。VM Thread 也不能全称 GC。Main 的逐 call CPU 不含 setup、类初始化和其它进程生命周期成本，wall 减它不是纯 I/O wait。

stdout 的顶层暂停事件有 45 次 Young、6 次 Full，共 51 个不同 GC ID；暂停合计 1.52485s，最大单次 86.129ms。48 次 safepoint 总时间 1.5295392s，包含这些 GC 暂停，不能相加；Young 后紧接 Full 可共用一个 safepoint。逐 GC CPU 日志仅 0.01s 精度，不取代线程累计 CPU。记录证明该冷、单 CPU 进程确有编译线程成本及 GC 停顿，尚不能把某个业务 phase 或全部差额归因于 GC／JIT／I/O。

线程采集共 156 次，名义间隔 50ms，实际间隔最小 49.9329ms、最大 241.0166ms、均值 70.6015529ms。50ms 在最初不超过 100ms 的范围内，已 BEGIN 后才收到后到 100ms 细化，未为此重采样或覆盖原件。observer capture wall 0.1612716s、控制端 CPU 0.046875s 单列，未假装零开销；没有绝对 phase 时间线，不能把这组累计线程 CPU 定位到某次 call 或具体方法。

## 完整窗口与解释限制

唯一 actor 实耗 11.7112399s，外层 collector 从 02:07:11.422065Z 到 02:07:24.337705Z，共 12.9156369s；MANAGED-CLOSE 在 02:07:24.246591Z 明确 terminal、reservation=false，无自动后继。进程出生到最后 observed thread exit 为 11.160288s，口径不同，分别保留。

从具名未启动 JFR 准备／请求 01:57:56.456543Z 到最终 collector close 为 567.881162s；到最终 qualification 02:10:47.069736Z 为 770.613193s，包含查明分配缺口、撤回方案、小诊断准备、等待及离线分析，不把未运行请求当作 JFR 实耗。这两个具名窗口不声称覆盖更早的调度准备。新诊断只有一个 workload JVM，没有为线程命名或更好数字追加运行。

另对同 SHA 的固定 Q1 做 Python 词法／结构只读计数：query 有 33993 个 object、14716 个 array、207949 个 key；whole 有 94632 个整数 token，float callback 为零。这只是这份 DATA 的形状，不是类型准入或方法热点证明，也不支持声称浮点正则是本次 CPU 根因。后继先做最窄源码所有权研究，不据本次诊断直接加缓存、删校验或授稳态墙钟改善。

原件根 D:/ck3-state/resume91-native-integration/p119-small-b-diagnostic01：
QUALIFIED-P119-SMALL-DIAGNOSTIC01.json 7166B／f18820bb3633e64115ae1397e37ea14df6add23fabb781a413137fceef398d39；
DIAGNOSTIC-ATTRIBUTION01.json 53260B／93b8e551363030b9a6e5e2e23545d0fc81d2ea99b072449ae3d44830f1b80c66；
stdout 23706B／e91bf36d6099c2fc03bb8ca37d309bf63942e5b4f88c6a4cf68b9cf47b8429e4。
Java 独立只读复核位于 construction-jvm-diagnostic119/read-only-analysis01/ANALYSIS.json，4326B／27497ac8520e535facaac839d292e1f872efc49ed5f6778812ddd3bebb14fca3。原始记录不覆盖。

本单仅完成软件诊断与文档；没有新增源码、编测或实际装载，不授新增 class Runtime 准入、保存日或 10 秒目标通过。
