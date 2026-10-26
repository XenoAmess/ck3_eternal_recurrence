# resume63：REA、Java 全能力迁移与 G2 接续

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-26T14:50Z 实时记录；执行仍在进行。本页接续 [resume62 交接](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff.md)与[来源索引](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff-source-index.json)，不改变历史失败。

当前目标是研究并使用 REA，完成 G2 M0–M7 的原生研究和 Java 落地，完成 Python 能力迁移后使用 Java 继续普通自动游玩。[完整迁移与八 M 对照](2026-10-26-resume63-migration-and-g2-matrix.md)区分八个业务门槛与 Python 全功能范围；两者不能互相替代。

以下原表保留14:50Z及其后各次观察；最新状态以前向时间记录为准，不把新结果倒填到旧cut。2026-10-27 00:00（Asia/Shanghai）已跨日，午夜后事实另计27日。

## 已确认的基线

- 本轮实际执行 `py tools/ck3_live_run_id.py machine`，机器与交接相符；14:35:37Z 重新读取来源索引全部43份原件，大小及SHA全部MATCH。
- 复用交接的同一SRC、BUILD、m2与TMP。Host实测默认Maven3.10.0，原构建锁可取得并立即释放。没有每次修错重新复制源码或重建全部输出。
- 存储协调者读取实际 `Z:/.codex-task-bus`，新财务181与task-start回执在 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/capacity/`。采用完整旧hold保守上界；新增预算有明确子分配，不以空闲截图取代执行准入。当前复核期限16:40:26Z。
- 后台WMI观测存在多个CK3进程，但本轮尚未核实其完整身份和所有权；没有接管、终止或新启动。本轮新增游戏日与保存均0，Java完整G2业务仍0/8。

## 并行工作与下一门槛

| 工作包 | 本轮变化 | 下一门槛 |
|---|---|---|
| REA框架 | [真实源码与可执行方法](../rea-ck3-research/resume63-framework-workflow.md)已记录；复核23份旧来源。统一后端准备0x1D64290的有限查询 | 实际字节/CFG与独立解释；不重复全PE导入 |
| Host/SDK | MavenArgumentFile及其测试两叶已精确采用；v2 config仅属性，其余argv走CLI，保v1 | 实际增量编译、默认mvn离线POM回归、完整Tools VERIFY，随后LS与SDK完整step |
| M1 | 派系Known读取接共享语义槽的10叶已采用，加入真实source冷清槽/原件重放测试 | 编译及原APP/LS整类实际运行；自然继承重绑另验 |
| M2 | 首显示项处理三叶已采用，测试显式分开public/native revision | 原生产链整类；failed READ→journal→scan完整接续仍有未采用叶 |
| M4 | CASH刷新类型贯穿五叶已采用；同帧ROOT收入fallback正在补迁 | reducer/生产集成实际回归及原M4业务 |
| M6 | 活动对象消失后读取既有原生终态journal的五叶已采用 | 实际transport→归档→重放回归；四类业务分别实机 |
| M7 | cap四叶20操作已采用 | 实际cap回归；真实恢复后完整ordinary plan，不能只验replacement snapshot |
| M0/M3/M5 | 终战跨WarID归档、同Game自然继承Family闭包、婚配receipt日期接续各自正在独审/采用 | Host模块增量与真正consumer回归；M3用JFR定位已知过期而不放TTL |
| Runtime | 同Prepared FILE_REPLY及RootInvocation/v5分开施工，补原producer→全部consumer | 完整源码、测试及真实受管入口；不得伪造Session或独立issuer |
| Native | 四模块曾101/101；随后类型修正后的重跑实际100通过/1ERROR，暴露链接器删临时文件与容量枚举的竞争。已做窄修，最终回归待执行；strict仍有旧债 | 最终完整软件回归、实际修改范围类型、持续CI、Java UAC候选编测与实际设置读回 |
| Delivery | 只读恢复SRC/i61真实差异；保用户477B配置与原POM赢家 | 小型独立文档包先交付；最终图仅一次增量对齐，不提交未验源码 |

源码采用、软件测试、完整构建与实机信用分别记录。上述Java新采用项尚不能记为本轮测试通过。Tools旧完整失败、LS75不完整、M3五项失败、Cold17超时均保留。

14:54Z补记：原S26 Shared在子进程启动前拒绝新REA请求，原因是历史completed工具来源递归重验已被合法CAS更新的mutable容量head。没有新230B字节或REA后端结果。已安排共享历史读取最小修复；开发增量改走已有默认Maven、只读研究改走官方REA入口，分别记录实际命令和范围，不授旧Shared成功信用。

15:23Z前向结果：官方REA直接路径已实际完成230B/48指令及119B/35指令两题，局部CFG分别5块6边、4块4边；两题按各自新窗口闭场，第二题独审仍在进行。第一题返回被调结果低字节、第二题只规范AL，不能解释为兵力或胜率。原Shared失败保持。

Java原八整类实际两轮均未全过：第二轮68通过/1失败。随后查明默认Maven启动脚本额外运行一个未展开MAVEN_OPTS的版本探针；测试恢复与生产相同的双环境预算，保持384MiB，原失败方法真实通过、内层峰值238931968B。见[具体诊断](../maintenance/2026-10-26-default-maven-jvm-probe-memory.md)。完整Tools仍待后继，不拼接测试数。

首49份文档包已普通FF推送 `e735f2a0ed56e666e5f5d0977a7e532ff861f23c`；Linear history成功，Official Runner尚在运行。Native交付前发现旧工作树落后主线，改为fresh主线前向移植helper两叶；fresh四模块127/127软件通过，原CI另有三个消费者测试，完整step还在验收。既有主线configured实现和两项同义回归保持，不用旧源码覆盖。

## 执行约束

Host唯一写BUILD/m2及build-tools，各领域按精确源码文件分工，capture前协调短冻结。REA由单一后端执行岗采样，八M共享原件并独立解释；不按人数重复重分析。原Genesis已真实创建，禁止重新初始化。Steam确认只用后台原生回执，不抢焦点或自动联网。

本轮实际总线任务为 `ck3-java-g2-rea-resume63-20261026`。仓库原有489项dirty不清理、不整体stage；现有Git index约10.6MiB，超出小型预算，Delivery从新鲜origin/master保留未改子树，通过Git树对象交付明确文件，普通fast-forward push。源码和文档交付commit/CI终态随后追加。

## 2026-10-26T16:09Z 前向接续（本地27日00:09）

- Tools accounting修订的受影响11整类实际112/112通过，exit0、72.3101985s，重编2 main和1 test；独立核验保存在 [ACCOUNTING63-AFFECTED11-INDEPENDENT-RESULT01.json](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/controls/ACCOUNTING63-AFFECTED11-INDEPENDENT-RESULT01.json>)。不能将此前68通过与单例重跑拼成这一批。
- v5/R34先局编实际重编5 main、3 test，7.4593416s、exit0；随后13个整类实际121/121、零失败/错误/跳过，191.7773433s、exit0，这次没有重新编译。325个源码pins前后匹配，独核为 [V5-R34-AFFECTED13-INDEPENDENT-RESULT01.json](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/controls/V5-R34-AFFECTED13-INDEPENDENT-RESULT01.json>)。它与112是不同测试选择，不能相加冒完整Tools通过。普通Jar82也仍属于较早cut。
- M0六叶、M1十叶、M2二十三个唯一叶、M3自然继承十叶、M4五叶、M5日期接续八叶、M6六叶、M7七叶及FILE_REPLY六叶均已有源码接续；四个零JUnit helper同步改名为Assertions，LS标准test-jar POM已采用。各自精确范围见八M专题及[FILE_REPLY记录](2026-10-26-java-g2-resume63-file-reply.md)。领域编译和JUnit仍须实际执行；Host只清理adapters-storage/local-service两个模块，不-am clean，不清m2或其余缓存。
- R34旧计划把S26 receipt SHA/大小写死，Source/ENV/BUILD/inventory多处也正确要求同一实际producer。选用现有 `NativeCombinedSourceCut.sealExisting`：最终新Tools实际qualified后，对同一native源码树生成新来源控制原件，再用原ENV、缓存BUILD及inventory生产链接续，不热改Source15/ENV22/BUILD24。新的UAC v2候选仍待编测；Root独审已指出两处public CLI分派只认v1，修复必须同时到达这两个真实调用者。121软件通过不授新qualified carrier。
- Native在fresh主线前向移植后的四模块实际127/127通过；configured两完整叶strict通过，helper只对明确提取的修改范围strict通过。旧helper全模块201个错误是旧cohort事实，不能写成新全模块绿。原CI三个SDK消费者本包未执行，官方步骤保持。[原件及边界](../handover/2026-10-26-java-g2-resume63-native-helper-review.md)。两helper和持续CI hunk已FF推送 `7ecb8b1d10b88eeaed389ca76251eb5d679c652e`，configured生产叶保持fresh原样。
- REA两题230B/48指令与119B/35指令均已有独审，第二题另建独审记录，原close的PENDING不改写。[实验记录](../rea-ck3-research/experiments.md)维护具体引用、成本、opaque调用和未知。第三题只准备 `2B9D260` 的当前RF metadata及最多64B前缀，不预设包含关系，不自动追callee。旧 `28BFCD0` 完整103B与 `A11F60` 模型优先复用。
- [后台只读核对](../handover/2026-10-26-java-g2-resume63-runtime-readiness.md)已辨明三个旧CK3 generation的kernel handle均signaled，不能因WMI仍列PID或exit code259称它们仍在运行；其EXE路径查询失败仍为UNKNOWN。现存operator只绑定旧Python job，不是新Java路由。Genesis两份719B原件身份未变，仍seq0，未重建；SERVICE/新Java运行组装和实际权威尚未成立。
- 普通SAVE由真实Root普通动作后产生，不是可以预造的初始DATA。起步准备与M7恢复验收按真实顺序安排：完成必要迁移及运行资格→首场普通动作→canonical SAVE→public RESTORE→同高级意图的完整ordinary plan；不得将首场尚不能产生的SAVE设为循环前置。
- 官方CI `40345540217`（e735文档包）实际FAILURE：bootstrap与qualified Tools各636/636通过，但 `ControlCi.runQualified` 缺实际fixture-production request，在full parity前明确NOT EXECUTED、child exit1；并非编译失败。实际新SDK和完整cold/warm仍未执行，已沿原生产链修入口。`7ecb` 官方CI截至本记录仍未取得绿色终态。

Root已明确授权新的有限容量review至2026-10-26T17:40:26.824464Z，原quota和总hold保持；发新财务/执行卡前鲜读卷/RAM与实际基线，不追认或延长旧卡。任务总线15:59:17Z heartbeat为9027。午夜报告另按实际时间收口与建会。

本轮新增游戏日0、SAVE0、RESTORE0，Java完整G2仍0/8。下一门槛是实际领域编测、新Tools完整验收与SDK完整step、原生后继及设置读回、真实首场Java权威接通；当前继续执行，不以文档、普通Jar、构造器或ACK授业务完成。
