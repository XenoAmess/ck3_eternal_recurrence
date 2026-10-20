# 罗贝尔 v20261019：休假交接（2026-10-20）

机器：`machine_id: xenoamess-full-tower-eb9d2c1186`。本轮本机身份由 `tools/ck3_live_run_id.py machine` 实读；闭场观察截至 UTC `2026-10-20T01:57:55.947Z`。本文件按用户“收尾、写交接”指令停工，不继续开新场。精确机器回执见[闭场索引](../ck3-native-ai/evidence/robert-v20261019-vacation-closeout-2026-10-20.json)。

**存档仍是 1081-07-31，5429／10950 日（49.58%）、4753 个完整周期。受管现场已关闭，屏幕已释放。Source25／a03 尚未生成或部署；1 秒／游戏日、Native30 实际加载、连续热点与空闲全境画面都未验收。唯一一次 UAC 已成功完成九个 EXE 的永久精确路径登记。**

## 接手入口与路径

先读本文件、[日报](../autonomous-agent-progress/daily/2026-10-20.md)、[本场执行专题](../ck3-native-ai/robert30-v20261019-execution.md)、[长期性能记录](../ck3-native-ai/robert-v20261019-harness-performance.md)，然后核自己的机器 ID 与[统一存储策略](../storage-retention-policy.md)/[参数](../storage-retention-policy.json)。不同机器重新核实际 EXE/build、安装、权限、容量和 Steam 离线；本机证据不能外推。

以下缩写只绑定上述机器，不是跨机器配置：

```text
N = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep
P = N/p51-fresh1066-v20261019-prepare01
T = N/robert30-v20261019-campaign01/runtime
O = P/c23-source23-native30-cold100
B = D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01
R = D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01
A = D:/codex-ck3-demos/2026-10-20-project-exe-admin-once01
```

收尾前已推送主线为 `24a6e735078a8f6b2c48ebc5e7cee03c36474bf6`；本次新增源码与交接随本文件线性提交。业务来源仍是 Source24：
`campaign/robert-v20261019-source24-camera-cold-01`／`6b55531b1d3a44ee73ab13ea40132556030f682e`。不要把当前 master 自动当成已部署 SDK。

## 存档、时间与真实闭场

| 项目 | 保持值 |
| --- | --- |
| campaign／actor／episode | `native-31254-6271ac8cd441`／40526／`native-40526-1bec95182886` |
| 创始人／继承 | 31254／reconciled=1 |
| T0／30 年终点 | 53144328／53407128 |
| 当前 raw／日期 | 53274624／1081-07-31 |
| 累计信用 | 5429 日、4753 settled cycles；失败 4754 零信用 |
| 全墙钟起点 | `2026-10-19T03:26:49.420926Z`，维护与失败均不扣除 |
| 最后保存 | SAVE10480，count=74，pending=null，dirty=false |
| 下一序号 | NEXT10481；冷 SEM/CAP 可以依法消耗它，不要求首 FULL 也叫10481 |
| history 5268 | checkpoint 下界，未观察为真实 history 总长度 |

保存位置 `T/state/profile/save games/xar_checkpoint.ck3`，116203629 B，
SHA256 `f0edd690a08320c52fb61cafc21d8991aca8e7775e1f1c2692e7e09c865b0061`。
Driver 原件 38356800 B，SHA256 `b9f271f9b36885f008b6e05ab788ecbc47214178c64509646d44ea5e34872c29`。闭场没有重哈希大存档、Driver 或原片。

`O/HANDOFF-RUNTIME-CLOSED-20261020.json`（5941 B／`8c4deb07c365877ebd00d3ede09e8394752b353c22ba24c27d6fa489bf093cda`）核五个具名 Tasks absent、九个已知 owned 代次不存活、无 live CK3。两次冷启动创建的 suspended Game PID/birth 仍 unknown；Job0 与精确清理不能补出身份或正常退出0。

screen100 由唯一 owner 在 01:57:55Z 以 CAS 7490→7491 释放，resources=[]、屏幕任务 done；这不表示 campaign 完成。证据：
`O/SCREEN100-RELEASED-FOR-HANDOFF.json`（1756 B／`b452da0e62254afb0aee64aeac3ae7474dc116f3b7e34c5e727a7e0e89043eed`）。
个人 OBS114680、既有《黎之轨迹》和 Steam 未接管。最后离线原图是 01:26:42Z 的真实窗口位移图；下次启动须取得新独占和当次新鲜离线像素，不能复用此图。

最后正常 SDK 关闭仍是 C20 的 Queue/App/owner/bootstrap0、Job0。原2b录制正常闭段；79872 段 worker/stage1、无 capture_closed，不能因 OBS 退出0追认为正常素材。

## 本轮失败与已修范围

1. **C22 共享容量 schema 故障**：窄 prepare 卡覆盖仍由 GameSupervisor 消费的完整文档，触发 KeyError、publisher 停止及旧 Game30852 退出1。Root 与执行链均漏查活跃消费者。已补完整 schema 合成器、跨消费者检查与统一策略经验；[原失败](../ck3-native-ai/evidence/c22-warm-storage-schema-abort-actual-2026-10-20.json)保持失败。
2. **C23 首次 Run（00:50Z）**：完整44项清单传给最多8项的创建接口。已分离完整闭包与固定六入口，创建前调用原 verifier；max8／16KiB保持。[原失败束](../ck3-native-ai/evidence/c23-first-supervisor-launch-actual-failed-2026-10-20.json)1975 B／4351bc77…。
3. **a02 准备末尾 import 错误**：9源／7元数据已写并读回后，adopter 漏加 src19 导入路径。未重放写入；独立 completion 核精确输出、旧档 FileID 与原六入口，再 create-only 补 `O/A02-PREPARED.json`，10958 B／eae3503a…。原缺源 composer 曾从 HEAD 精确恢复，来源仍10985 B／ba9a0dd1…；没有近似重建。
4. **a02 唯一 Run（01:28:38Z）**：`XARG2ManagedOwner-dc9e5cdac3f1405288ac2428d5bf11d9` 在 pre-native callback 报 `EnumProcessModulesEx / WinError299`。完整源码与六入口已过；失败在 preload 前 DLL 缺席检查依赖 loader 模块名单。尚未到 injector/resume，actual-success Game receipt absent 不代表未创建进程。原 Task child1／bootstrap1／Job0、forced=false，已注销，不重 Run。外置：
   `T/ROOT-FRESH-SUPERVISOR-CLOSED-C23-A02.json` 1053 B／3e94fe69…；
   `O/SUPERVISOR-A02-CLOSED-UNREGISTERED.json` 2278 B／3e0cd654…；
   `O/POST-A02-FAILED-LAUNCH-CK3-KERNEL.json` 708 B／5d9f10fc…。

**M7 最小修复已进本轮源码、尚未进入实际 SDK**：[完整来源/资格](../ck3-native-ai/evidence/g2-m7-prenative-mem-image-source-2026-10-20.json)。只把 cold preabsence 换为系统 VA bounds 下两遍完整稳定 MEM_IMAGE 映射，核同 held process，任意错误不当空表；postloaded PSAPI／FileID／peer 原链保留，新 helper 进入 owner_source_epoch。13项／32 subtests通过。

唯一真实自有 suspended Python 例已跑原 Job→factory→Runtime hook：PID198888／FILETIME134369342403215399、2 images／38 regions，holder关闭后 borrowed 同身份仍活；随后受控 child1、Job0、owned0、parent0、无注入/恢复。原回执 `_runtime/m7-prenative-owned-attempt01/RECEIPT.json` 1635 B／397e94d4…。这是 Win32 机械资格，不是 CK3／NativeLoaded／H。相对解释器 Win2 发生在创建 probe 进程前，实际例仅一次。

## 一次 UAC 已完成；后继不再请求这批确认

用户只允许这一次确认。本机在 01:53:09—01:53:11Z 实际登记全部9路径；管理员 PID210048／FILETIME134369347886913739，实际退出0。Root独立核 UAC_calls=1、Path7→16、旧Path完整保留、Extension/Process数组不变。九次 nullable Add 均有实际新读回。

精确清单取 `R/attempt08-build/project-exe-manifest.json`，10169 B／
`f35cf135db1a564bcb55b3b5c932059deb4369d0e06fd4a5ff006b25d80e57a7`。
只登记该清单9个完整 EXE 路径；同路径重编不需逐次 UAC，新路径不能外推。
证据 `A/RESULT.json` 12670 B／`4e73071d49053e6cc65c1077d30a84a74cc82a2f917489e0e2c5fd99c9ba8e59`；
`A/LAUNCH-RESULT.json` 6116 B／`a5fda26b83a441b19c995e6fe04a550737f5ad73838e9ab683e7999cba43e3a7`。
原08取消1223／future:null保留，不追认成功。新单次脚本已执行完，不能再运行它。

未安装/恢复 SYSTEM broker：本机普通 SID `…2908730481-166481001-1318755029-1001` 与旧固定 installer OWNER `…4063940640-1897558599-686929869-1001` 不符，旧 policy/Taskfolder 也缺失。[只读诊断](../ck3-native-ai/evidence/native07-defender-canonical-broker-readonly-2026-10-20.json)只证明本机缺席，历史别机安装不能复用。九EXE登记不补 Native09 whole：09整体仍FAILED，11只补产物终检成功。

## Source25 待组装的三个包

| 包 | 已完成与边界 |
| --- | --- |
| M7 preload 修复 | 四生产叶：custody/windows/新 `bridge/native_preload_mapped_images_v1.py`/epoch ledger。独立审与真实 owned 例通过，当前 src19 未改。 |
| 非主导战争保地 | [helper/transform/精确diff/资格](../ck3-native-ai/evidence/nonleading-player-realm-siege-priority-2026-10-20.json)，29627 B，19项通过。当前玩家领内敌围城可进入既有只读预测，保原事件/终战/移动约束。Strategy仅RAM变换，未部署、无战果信用。 |
| 时钟进展诊断B | [SOURCE-READY](../../tools/g2_saved_campaign/candidates/exact_clock_wait_progress_20261020/SOURCE-READY.json)，57560 B，5项通过/4.689s。从已有 heartbeat 接收与原 candidate 记录等待期变化，不加RPC/轮询/Native构建；wait/时限/暂停清理不改，仍未采用。 |

Strategy 前像与 Source24 完全相同：Git blob `000b0ec364dcf6bfef17db2d0d51fc426aa21b02`，1047320 B／SHA256 `45c164297b90b32203e7860b4a7735cfa65c5ca1db7141e898d15395d2e47e78`。不用移植或重跑19项。NativeB 首次因56KiB子帽RED，结果字典未保留；Root把未用scratch重分至同64KiB总帽，第二次5项才有PASS。其新错误DTO为 v2，后继需核 MCP／Queue typed 消费兼容；本轮未验证整条冷链。

**Source25 writer、Git branch/anchor、导出目录、a03 producer/plan/Task均未创建。** a03三张源码卡虽签但未投递，96+32+64KiB全保未用；不能把规划/RAM草稿称可执行实现。现有 Source24 两视图仍 `src19` 与 `reference-c23/src`，1457叶，每份59209522 B，实际[导出原闭件](../ck3-native-ai/evidence/source24-dual-export-actual-complete-2026-10-20.json)。

下轮拟定路径，不是实存事实：

```text
N/sdk-v20261019-candidate/src20
N/sdk-v20261019-candidate/reference-c23-a03/src
O/immutable-source-export-a03
O/ROOT-FINAL-SDK-SOURCE25-BASE.json
T/ROOT-FINAL-SDK-FREEZE-P37C23-A03.json
T/ROOT-C23-CANONICAL-PRELOAD-POLICY-A03.json
```

新 Source25 以6b55531b为父，仅叠三个包；不要顺带混入远端其他研究。新 helper 数量/全rows从真实产物派生。先写无policy的 compact BASE，后由 runtime 仅加实际 A03 policyref 一次创建最终RootFinal；保 A02 的84d59／f57c8原件。

a03 controls要实现：完整闭包核验＋六入口子集、原 max8/16KiB、全普通规划器、WAL313；新 attempt/五输出命名A03，绑定a01/a02真实失败闭件与独立随机Tasknonce；失败CLOSED只投影M7已读 phase/PID/birth，缺失unknown、不额外OS读。不得清旧stop/exit marker。
feeder薄适配仅A02→A03读源；其逆变换应精确还原旧main41718／6147cbc0…、ledger34988／6b0ece99…、launcher2451／e3105fec…。原timing函数AST `b9d3a1ca97b7d06d5bf4b0648df64f1b63061303ebe59fea96b14ff92890fceb`；新alias不是FuncDef，不能误用旧AST抽取器。未创建的新finite helper须归a03主图，不能拿历史cdc3冒新来源。

## 性能、镜头与 G2 的下一门槛

阶段目标1秒／日，远期0.5；现未达。可引用旧C18 90日文件创建端点109.5799153秒，即1.2175546秒／日，精确FULL mono unknown。没有本轮新FULL；全墙钟仍从原起点算。

已确认原wait把整个remaining交给 public-revision等待，而heartbeat只notify、不增加public_revision，30秒内可能仅末尾一个candidate。fresh heartbeat与累计owner+64不能证明全段pump。B候选保留观察空窗/身份变化unknown，用已有heartbeat区分变化何时被SDK看见；不把它称时钟已修。

Queue每RPC反复扫描累计四根是长期热点假设；只累计自有写入会漏多写者变化。等真实FULL的wall/RPC时间并集/混合残差再定收益；增量缓存缺完整外部变更凭据时仍走原扫描，不删容量/once守卫，不靠改变战争意愿提速。

镜头源码已在Source24接真实scope→pre-resume→Service→Mode4；Native30 DLL为19469312 B／`39350bd933549ff11e7a79e1b1e0340664bf87ee129a2aa8cdb7b0e9be269f56`，实际未加载。空闲门槛30游戏日，范围来自递归实际封臣县，coverage_verified=false。下一次必须取得自然 Mode4 跟踪/更新/目标/epoch/expiry与原图，及安静30日后的 Mode1 县集/bounds/zoom/原图，单ACK/settle不能授全境可见。

G2仍6/8：M6已找到同实例Start、自然具名gain25及后普通消费，真实终态仍unknown；M7 H未跑。入口：[M6](../ck3-native-ai/g2-m6-research-2026-10-19.md)、[M7](../ck3-native-ai/g2-m7-research-2026-10-19.md)。M4后继优先按融资缺口补合法借款实际本金、债务关系与到账链；只Confirm/ACK不授信用。M5另一采购liveness缺口仅研究，未修：等待旧雇佣首次raised inventory的早返回可能漏同帧合同结束证据；不要按超时重买原单。

## 接班执行顺序

1. 新machine/容量/任务总线读回，领新屏幕独占。旧运行准入期限是 `2026-10-20T03:48:56.993837Z`，不自动续；过期按届时实际占用和剩余工作人工重评。
2. 组合Source25三包并完成真实canonical锚、完整清单/父commit/差量检查；实现a03 controls与feeder，先处理接口/导入/真实Windows生命周期，避免用CK3反复试探已可离线验证的问题。
3. 独立报价 Git/export/runtime峰，生成同一完整容量schema。所有launch/keeper/profile/job绑定同一新full SHA；窄prepare卡不能替换共享full。本轮新增UAC净7929856 hold也须纳入，保留旧预算/失败束。
4. 核本机实际游戏EXE/build与Native30绑定、当次Steam离线原图，审新SPEC后唯一Run。先证新Game/birth、NativeLoaded及sameholder链，随后审display SPEC/新publisher/新record UUID/地图原帧，旧蓝窗退役。
5. 冷恢复SAVE10480，合法SEM/CAP核原campaign、actor/episode/T0/4753周期和5429日；不重10468/10476、不补4754信用。核实际App WALenv=1和自然append，Task配置1不够。
6. timed feeder自行发布首FULL、同producer mono围住发布至验证；五actualrefs/newTasknonce精确绑定。首批闭后0RPC HOLD，Root读request/response SHA、日期/周期/完整wall/并集后，才create-only `T/ROOT-C23-FIRST-FULL-CONTINUE100.json`，schema `xar.C23-first-FULL-root-continue/v1`、reviewer=/root、真实reviewed_at_utc与原样first_batch；不能手发首FULL。
7. 自然热点/空闲镜头、M6终态、战争保地效果与完整吞吐并行验收；未覆盖弹窗原生采集、按实际第一项续行，批后离线补共享registry。最后继续到原30年终点，评分用15秒入口。

## CI、存储与其他交付

24a6e735 官方CI `39352495841 / 118399667739`：47、51已PASS，63为历史注解测试误读当前政策而RED；Linear `39352496070` GREEN，后继skipped不算绿。仅换固定历史压缩fixture后原3项0.42s通过，[依据](../maintenance/evidence/2026-10-20-storage-policy-annotation-fixture-ci.json)；adapter和当前政策未改。本次提交的远端CI未验，接手按exactSHA观察，不冒整轮GREEN。

最终存储账 `B/SESSION-20261020-FINAL-ACCOUNT-STOP-HANDOVER01.json`，7259 B／`92a9054dd69be65ee0c6f4799367095cfa720fdd4f056cf3c45b4fe57797e8ff`。live/immutable A02 full仍27016 B／`62a24182df872934e4244f3a684427f3357c5580ecea5ca56fb5e4f48c91e971`；本轮后加hold以final账为准，旧62a2不是下一场当前容量证明。保必要Driver/SAVE/源码/原片及失败束，按统一期限复核，不无限续留、不删个人/其他任务资产。

首局复盘与改进已入[长期经验](../ck3-native-ai/robert-first30-lessons-2026-10-19.md)。首局10→2的全部因果尚未闭，不能因本局49.58%时间进度称已保地或优于首局。后续评分15秒、旧60秒不动，见[评分入口](../ck3-native-ai/campaign-score-presentation-v1.md)。

两张B站封面已入Git：`promo/robert_first30/bilibili/`下16:9 1920×1080与4:3 1440×1080 JPG、README、delivery.json。本轮发现四叶均skip-worktree、当前checkout未物化；从HEAD可读完整blob，不是被删交付，也未重新生图/上传。按需取回这四个确切blob即可，不需展开整个sparse checkout。旧成片/网盘事项沿[首轮交接](2026-10-19-robert-first30-scoring-vacation-handoff.md)，不把本轮源码收尾写成视频重交付。
