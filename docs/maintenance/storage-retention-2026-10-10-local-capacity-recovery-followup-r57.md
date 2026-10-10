# 2026-10-10 本机容量恢复追加记录：R57 与 merit 单场准入

记录时间：2026-10-10T07:07:55.558467+00:00。本记录只追加实际完成事实；[初期记录](storage-retention-2026-10-10-local-capacity-recovery.md) 对应的外置源稿为 6,175 B / SHA-256 `8363fabcc9073d1873395318872fe188016a3939c3ab9382e99df993b79f2f30`，原件保持原样，初期时点数据不覆盖。源稿位于 `C:/workspace/disk-cleanup-20261010/resume-05/docs/maintenance/`；这些 bytes/SHA 标识外置证据源稿，Git 入库副本可能归一换行，不宣称沿用源稿字节哈希。

## 范围与闭场

本机 `4号执行者` 仍只有 C 卷（511,776,722,944 B），沿用共同存储策略 1.0.0。全部动作由 disk lane 在原已授权项目范围串行完成；未扩根、未新全盘清点、未修改 MAIN、Steam、系统设置、游戏依赖或其他 owner 资产。

R57/a158 administrative_appointments 在原 POST 回执中于 2026-10-10T06:34:06.851220Z 完全 CLOSED：closure3、retained actual OS0、native0、原 allocator/keeper actual0、CAS8191 done/resources[]。原 public run2/verify2、business_pass=false 保留；host GREEN/正常退出不授业务 PASS。已以独占卷台账 HANDLE append 释放初始2GiB reservation，未把信用转给下一场。

- 原闭场：`C:\workspace\ck3-upgrade-20261010\qol-scene-resume-02\administrative_appointments--a158\POST-RUN-CLOSE-05.json` — 3,673 B / SHA-256 `7d7aba21f4c05c3bb7358836ddbe05462d838a59e8ed8f3b9f29f2a9568683ab`
- reservation 释放：`C:\workspace\disk-cleanup-20261010\resume-05\storage-coordinator\admin-a158-reservation-49-closed.json` — 3,940 B / SHA-256 `3294e70776a094c9912546b6888cb450d9dc0a16d1803feba72eb273d2f41b9b`

一次有界原生 metadata 读取仅该场 live/state/attempt 三个精确根：4,505 entries、0.391秒、321,861,480 B AllocationSize 路径上界；没有正文 hash。原已有 state/input 可重计，因此它是保守增量，不是独立净增长证明。live 109,640,904 B、state 164,925,176 B、attempt 47,295,400 B。该次只落盘 root 聚合，transport/report/PNG 各分类 actual allocation 仍为 null；不得从文本逻辑长度编造分类实际占用。后继闭场必要统计在同一 metadata pass 内增加类别聚合，不另导逐文件全集。

R57 生成 shadercache 已先核原 launch/profile、snapshot 排除、原进程身份消失及实际 CAS，再按每批≤1000精确文件、独占 HANDLE/native identity/size/mtime/journal/delete后缺失处理：3,816文件，实际释放161,276,720 B。原报告、业务结果、debug/error、存档、fixture、配置、源码、冻结输入未删除。

- R57 cache 实清：`C:\workspace\disk-cleanup-20261010\resume-05\C04-reclaim-a158-01-summary-23.json` — 2,423 B / SHA-256 `24726f76b9bb91cb96aec057b6f6d32efb6a9aec51b9b8d1a3f18ffb5ddbb5f0`
- 原闭场文本无损压缩：`C:\workspace\disk-cleanup-20261010\resume-05\a158-closed-text-compression-05.json` — 1,396 B / SHA-256 `4b86fba611097ee87ee17b49b915be3e26a6db356756ea3bbdf2f59d127573d6`

文本只对3份尚未 compressed 的闭场输出执行一次 NTFS 压缩，前后 bytes/SHA/mtime 相同；另6份已 compressed 原件跳过且未重 hash。actual AllocationSize 节省1,798,144 B，原件仍可读。去 cache/压缩后该三根保守上界158,786,616 B；这是前值减精确已回收分配，不是重新扫描值。

## 原审定队列的必要续清

R57 cache 回收后实际 free29,244,575,744 B，低于当时完整下一场门槛30,073,159,680 B，差828,583,936 B。Root 继而明确授权只消费原已持有、已审定的精确清单；不降低6GiB系统规划或20GiB安全余量。

| 实际回执 | 删除文件数 | actual AllocationSize 释放 B | 回执 SHA-256 |
| --- | ---: | ---: | --- |
| `C07-wire-retired-a159-b01-actual-31.json` | 10 | 112,615,424 | `4b702bcbe7fa42de525570402ee68ade6d7e0c4c40bcae2f78e23db49ae6b5c4` |
| `C05-nav-retired-a159-actual-59.json` | 40 | 118,882,304 | `18eb2bd15260568226f6de7470c18a1429a7adef47fb85846273e041c8774141` |
| `old-source07-a159-g0-summary-41.json` | 2,304 | 68,922,696 | `8dd860540467239a87e4f2082e97011f3ae6656e8d8e54114b7389d23a7b86bf` |
| `old-source15-a159-g0-1-summary-41.json` | 4,622 | 138,222,224 | `b3d7fba71b2b5c587ba37d33c942da5ed903d328372d931b88ef8a08dcac9656` |
| `old-source15-a159-g3-4-summary-41.json` | 13,775 | 282,866,864 | `5340cd292bd5df078f898265d1e6015a0b4af0171b4b82b8eb559f35d0409c6c` |
| `C05-reclaim-abandoned-prototype-a159-01-summary-23.json` | 3,780 | 157,999,920 | `55d7e4e6be31d4ca26baa5a4efc23e86ef6564bf82d87d572e401bceec5efb28` |
| 合计 | 24,531 | 879,509,432 | 逐项相加，未计未执行候选 |

其中 Source07 原2304匹配文件退休，334差异/old-only源码全保留；source15只执行原未消费g0/1/3/4，旧g2及source04已清8组没有重复计账。所有保留索引、不同/old-only文件和当前 Source14/qa12 源、fd1f DLL、injector/SDK及必要原始证据仍保留。

旧 reverse-composite-07 cache 按 Root 新的明确弃用决定处理，原 lease `waiting` 和历史 `preserved_unqualified` 原样保留，未伪造 done、正常退出或业务 PASS。执行前确认旧 harness PID/create_time消失、无CK3/实际writer/新鲜恢复claim、当前原R57 screen CAS已done/空资源；只删该精确 shadercache，未删 state/profile。

本次追加 actual 原始资产释放为 R57 cache161,276,720 +旧队列879,509,432 =1,040,786,152 B /28,347文件。加初期28,145,109,216 B /530,502文件后，累计实际资产释放29,185,895,368 B /558,849文件。原件无损压缩节省和审计自身压缩节省单列，不混入这项删除累计；失败均0。

## 审计预算与下一场

Root 将必要 plan/journal cap 一次调为72MiB物理/288MiB逻辑，仅新增8MiB写入份额在卷独占临界区准入。必要续清完成后已释放其未消费信用到0，剩余 retention cap 不算写入信用。

- 新增8MiB预留：`C:\workspace\disk-cleanup-20261010\resume-05\storage-coordinator\necessary-followup-cleanup-audit-57-reservation.json` — 1,277 B / SHA-256 `f185722490e7156fbefc251e628117ff1abaafdc26bbe37bea709c803d18aac6`
- audit实际：`C:\workspace\disk-cleanup-20261010\resume-05\post-R57-necessary-followup-05-own-audit-compression-27.json` — 1,165 B / SHA-256 `f84159fdb14f17fb34be16c09e88565800417b8d72e69350eb9788aacd611db1`
- audit预留释放：`C:\workspace\disk-cleanup-20261010\resume-05\storage-coordinator\necessary-followup-cleanup-audit-57-reservation-closed.json` — 1,189 B / SHA-256 `3a003d7ef3a9ff4764bd088ee727710c768c01e773458fce0b63274becbbdae5`

实际 audit allocation 68,473,296 B <75,497,472 B；logical 270,503,364 B <301,989,888 B。完成后仅压缩2个尚未 compressed 的自身小审计文件，节省12,288 B；1,203个已 compressed 文件跳过，未重复hash。详细plan/journal按30天到期处理/归纳，薄摘要与availability记录180天复核；不是“至少保留”或自动续期。

Root 已闭新admin小prepare/cause，实际logical1,185,217 B、remaining0；CCC17候选卡与readiness小卡也已花费。为保守计usage，追加2MiB上界（newadmin已授权peak1,524,382 +CCC384KiB +readiness128KiB ≤2MiB；可能与原thin cap重计）。Root 明确把未来未消费Root4MiB降为2MiB，其余helper2/CI1/disk1不变，other总未来6MiB，不把已占盘小prepare再次算未消费。

merit a159 的 fresh 原子准入如下；MAIN9f4420d5 clean/frozen、当前Source14/prepared/profile真实映射在临界区核过。

- reservation：`C:\workspace\disk-cleanup-20261010\resume-05\storage-coordinator\merit-a159-after-a158-03-reservation-52.json` — 6,406 B / SHA-256 `87cd91b79a8a7b9f31c98172215c3c9a89a65c3566268d0e476ba8061105a93b`
- actual free **30,096,605,184 B ≥ 30,071,062,528 B**；余量25,542,656 B。
- 公式：2,147,483,648 单merit峰值 +6,291,456 其他未来预留 +6,442,450,944 系统规划 +21,474,836,480 安全 =30,071,062,528 B。
- current owned usage保守上界33,565,731,000 B（含两 MAIN linked worktrees、R57新增、实清抵扣及audit cap新增8MiB/薄产物2MiB）；quota51,177,672,294 B，满足usage+单场peak+other≤quota。
- 原合同hold1800/reserve90/timeout3000/naturalday0/cmd300/readiness400/.05不变。准入只供a159 merit；其 actual allocate06:51:59.993885Z /CAS8194/publicrun06:53:07.505655Z。活动merit profile禁止清理；尚无ransom/后序产品预算信用。

公式通过即停止旧资产清理。CCC17新1000个native中间物61,648,896 B仍仅候选，未执行、不计回收。最初2957objects聚合差额没有逐项落盘，不能冒作exact清单；CCC17由Root后来单次窄metadata授权实查封卡，与聚合差额分开。

原free与本次free之间的卷差不能等同本场分配：audit/其他小产物/未知并发变化分开，未知外部增长保持null。分页文件单路径只读metadata仍为5,736,935,424 B/mtime1791569723952797300，未解释差额，也未调整系统设置或6GiB规划。三个独立其他repo的owner/usage/cleanup仍null，未扫描或删除。下一原实际CLOSED后才释放当前峰值，并重新准入后序场。


### R59 领主代赎实际闭场追加（2026-10-10）

以下是后续独立时点的实际追加，前文的旧候选/准入状态和原始源稿均保持历史原样。R58 闭场 cache 实清3,824文件/161,198,896 B；其原件无损压缩另省2,494,464 B。R59 准入前 CCC17 旧中间物实际1,000文件/61,648,896 B已消费；不是前文仍候选时点的状态，也不得再次计回收。R59首次容量不足记录原样保留，后续07:42:46.035684Z实际free30,462,812,160 B通过完整30,071,062,528 B门槛，预留2GiB仅供a160。6GiB system_growth_reserve 是不受管系统/应用增长的共同规划，不是仅分页文件专用；外部应用剩余增长保持null，已知其他受管任务预留仍须另计。

R59业务失败与正常退出false不变，但实际 OS0、failure lifecycle、closure3、allocator0、keeper0和CAS8243done/空资源成立后已释放单场预留。释放原件 `storage-coordinator/ransom-a160-after-a159-02-reservation-52-closed.json`：7827 B / SHA-256 `fc45e24637bb9f7a8dda239fffe0544bb821612b1dadacdd243ebd56b5e0035b`。一次 metadata pass 的三精确根保守 AllocationSize 上界278,654,440 B（4,249 entries /0.448秒），包含已计输入的可能重计，没有正文hash，不当净增长。

只清该已闭场生成 cache：3,780文件/157,999,920 B，失败0。原件 `C04-reclaim-a160-01-summary-23.json`：2423 B / SHA-256 `94e09cd9d5005474bae23667fb507278a52fcf385aaf4211bf474a4c1c81b003`。另2份原闭场文本做NTFS无损压缩，bytes/SHA/mtime不变，省2,723,840 B；5个已compressed原件跳过不重hash，未删证据。原件 `a160-closed-text-compression-05.json`：1396 B / SHA-256 `ef5b6b39be79f80f469a5442268aa8901d508019f24b2b0664a1f3db15ddf10f`。路径均相对 `C:/workspace/disk-cleanup-20261010/resume-05/`。

计入另记的5个旧Git垃圾958,803,968 B后，当前累计实际删除分配 **30,525,547,048 B /567,458文件**；压缩节省单列，卷free变化不全部归因项目。R59处理后free30,630,338,560 B，项目保守usage32,951,724,672 B（未减压缩）。下一场仍须新的原子准入，不继承a160信用。CCC18的500项22,986,752 B、R58已owner审定的5张过时导航PNG均未删、不计回收；满足公式即停止清理。现行Source14/qa12/fd1f、原失败报告、debug/error、业务和有效图像证据均保留。
