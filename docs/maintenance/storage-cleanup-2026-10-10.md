# 2026-10-10：闭场派生物与退役源码导出清理

本轮按 [storage-retention-policy v1.0.0](../storage-retention-policy.md) 和明确用户授权，提前回收两份已完成分析、可由原始 ETL 重建的派生文本。只清理下列两文件；没有删除目录、ETL、缓存、存档或其他原件，没有新增 trace、游戏或 SDK 操作。详细删除记录保留30天，摘要180天复核；本页记录已发生事实，不承诺外置原件永久可用。

以下 ETW 章节记录 05:08 UTC 的首次清理；后续退役源码导出见本页末节，原始回执及当时的用途判断保持原样。

机器 `BF-202609141645`，原生卷 serial `11439297576789895419`。执行窗口为 `2026-10-10T05:08:01.654263+00:00` 至 `2026-10-10T05:08:03.076522+00:00`；实际清理 exit 0、失败0、两项 absent 均真。相关 consumer 清点为空；最终占用保护为 DELETE | READ_ATTRIBUTES、share=0 的排他句柄。全部父目录无 reparse、叶文件为 regular single-link，size/mtime、原生 FileId 与已冻结 plan 一致后才记录 intent，执行 FileDispositionInfo、关闭句柄并核对路径不存在。

## 精确删除记录

- 路径：`C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0045/etw-cpu-001/dumper.txt`
  历史 SHA-256：`a3ce7977583cdcf0793aa4e2724d83842b91ad1162164b82020d7e2ee9ab58a7`；logical bytes 与 GetCompressedFileSizeW 均为 **10,098,403,170 B**。删除确认：`2026-10-10T05:08:02.907437+00:00`；FileId `52c42c00000001000000000000000000`，原 written FILETIME `134360782826197799`，links=1。历史 hash 复用首次完整分析/原导出 pin，本次未重新读取或哈希正文。

- 路径：`C:/workspace/ck3_lyd_runtime_20261004/r45-root-etw-synthetic-20261010-001/offline-stack-001/one-dumper/events.csv`
  历史 SHA-256：`3beff29c91464316402540b84d311bf99399cec2b5d510249993cb55840fccc0`；logical bytes 与 GetCompressedFileSizeW 均为 **1,092,354,095 B**。删除确认：`2026-10-10T05:08:03.071381+00:00`；FileId `3eb32c00000001000000000000000000`，原 written FILETIME `134360759056398749`，links=1。历史 hash 复用首次完整分析/原导出 pin，本次未重新读取或哈希正文。


## 保留证据与重建来源

清理时两份原 ETL 都实际打开 READ_DATA 句柄，size/mtime/native identity 已记录，未读取正文或重算 hash。可用性仅绑定本次检查；后续仍按期限管理。

- `C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0045/etw-cpu-001/cpu.etl`，1,103,101,952 B；既有 SHA-256 `378766bd00d2a39065619b7dd45c3f3723e8c6d79f176fb13eec20dbc29c432e`；实际 read_data_handle_opened=true、body_read=false。

- `C:/workspace/ck3_lyd_runtime_20261004/r45-root-etw-synthetic-20261010-001/cpu.etl`，254,803,968 B；既有 SHA-256 `35f0c01fc02f1f545e1116b5c25037ff5802aa82675dd808d768f02e14896822`；实际 read_data_handle_opened=true、body_read=false。


重建以保留 ETL 和原 xperf 导出命令回执为来源：只取回执中的实际 argv，并将输出改为新的外置路径；本次没有执行重建。文件重建属于重型写入，须重新满足当次容量及并发预留准入，不由本清理授权自动启动。

- 原导出命令：`C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0045/etw-cpu-001/009-dumper/RESULT.actual.json`，1,087 B，SHA-256 `9b6cdb73f33bc2c15128eb947d287728a7a8641e6e4e5fb884943171b83e60bf`。

- 原导出命令：`C:/workspace/ck3_lyd_runtime_20261004/r45-root-etw-synthetic-20261010-001/offline-stack-001/one-dumper/RESULT.actual.json`，2,008 B，SHA-256 `b53cd3d4cb6f2178a5de25fed0ec83f44d330687b87ca7eccafdfde0ce265b66`。


摘要与源码继续作为保留证据：

- `C:/workspace/ck3_lyd_runtime_20261004/r45-actual-etw-offline-analysis-20261010-001/ANALYSIS.actual.json`，329,674 B，SHA-256 `d96b2c8fa74b89f1848e07879edf9d43640993b0e871a7909e8baeb01ca05cf3`。

- `C:/workspace/ck3_lyd_runtime_20261004/r45-actual-etw-offline-analysis-20261010-001/COMPACT.actual.json`，59,864 B，SHA-256 `d9a81a943657dfe300a1eb71eae049e083e4b64700c5e51a9d204e96ed0353b4`。

- `C:/workspace/ck3_lyd_runtime_20261004/r45-root-etw-synthetic-20261010-001/offline-stack-001/ADDRESS-PROOF.actual.json`，7,106 B，SHA-256 `73a83b3e8c6d6408ee1b3d8df9a52fb067f56804bc7abcd90f364453e6b1f6ca`。

- 清理 producer：`C:/workspace/ck3_lyd_runtime_20261004/storage-cleanup-20261010-001/cleanup_two_derived_texts.py`，16,241 B，SHA-256 `09ac7024f5abb2cfee8e7112fd337d46adb59a814672ac0e3c4208e3cd97424f`。


R45 首次完整分析、旧 RED 和工具验证的历史结果不改。派生正文现在为 deleted；历史 pin 用于身份和重建溯源，不能再被解释为当前路径存在。R45 startup RED、原始 stack 覆盖 UNKNOWN 和业务 NOT_GREEN 均不改变。


## 容量与记录期限

两删 logical bytes 合计 **11,190,757,265 B（10.4222 GiB）**，GetCompressedFileSizeW 合计同为 11,190,757,265 B。该 API 数值与逐文件逻辑量分别记录，不等同全项目物理占用。C: free 两次实读为 616,349,384,704 → 627,540,135,936 B，变化 11,190,751,232 B；并发系统活动及小回执也可能改变 free，不能把变化全部归因本清理。

详细 ledger 到期：`2026-11-09T05:08:03.076728+00:00`；摘要复核：`2027-04-08T05:08:03.076728+00:00`。期限为后续清理/整合候选，不表示已经实现自动 GC。现有未知 project usage/reservations 仍使重型写入 BLOCKED，本次只有精确删除和小回执。


## 精确回执

- `C:/workspace/ck3_lyd_runtime_20261004/storage-cleanup-20261010-001/INDEX.json`，5,157 B，SHA-256 `fffbf6f5ce5a041b60c2f762486dd59874f428ffa6164a719a5e928c2183ea2a`。

- `C:/workspace/ck3_lyd_runtime_20261004/storage-cleanup-20261010-001/RESULT.actual.json`，11,827 B，SHA-256 `62bf6ccffc126709033fa55c3e28cb52b6e97e2d860d78c448b022ebd99599a1`。

- `C:/workspace/ck3_lyd_runtime_20261004/storage-cleanup-20261010-001/TOMBSTONES.actual.json`，2,712 B，SHA-256 `0fff492fbc1120f80e573ff9c627b723cd793cc7c959067d1f7fbd4eaf86b3a3`。


[对应 R45 观测与可用性勘误](../ck3-native-ai/2026-10-10-r45-etw-startup-red.md)。

## 05:19 UTC：下一场重型写入准入

本机限定174个C根执行目录的元数据补漏已完成，9个归属未定目录全额保守计费；结合已有三份workspace根清点并扣除上述实际删除，滚动逻辑占用为118,069,504,191 B。另加1 GiB期间小写入额度，准入采用119,143,246,015 B保守值，不声称同时刻全盘物理清点。`C:/lem1`别名目标已计入workspace，容量计数不重复收费；来源判断的早期浅层访问经别名到过目标，边界澄清附在原报告旁。

ROOT在任务总线登记本卷协调者，并在实际独占byte lock临界区核验容量、登记唯一4 GiB峰值预留。fresh bus只见ROOT及协调者，没有其他重型进程或已申请重型写入；其余代理只做小源码/metadata工作。系统增长另预留10 GiB、安全余量20 GiB，required free为36,507,222,016 B，当次实读free为627,530,502,144 B。

已有占用超过默认102,389,285,273 B配额，因此登记**仅本机128 GiB**有限例外，owner为XenoAmess/ROOT，到2026-10-12T05:19:51.814083+00:00复核失效；后续继续缩减历史执行树，不自动续期。此例外只支持一轮Source06导出、三份缓存副本及R46 profile/存档/log峰值；不允许其他任务各自消费同一free或生成大型ETW全文。统一自动GC/预留器仍未实现，本次是实际串行人工协调。

实际准入：[ADMISSION.actual.json](C:/workspace/ck3_lyd_runtime_20261004/r46-root-storage-admission-20261010-001/ADMISSION.actual.json)，3,782 B，SHA-256 `4f56699cd0234f3fadfbdb319eb5c199c44cba08a059791c8cc922d580791d62`。原容量报告87,243 B，SHA-256 `30b4949c64c69c8c4afddd9352b0f215d794eec862e84402c5ac9c7a95157652`；链接边界附记1,676 B，SHA-256 `a0702dd2a8e162a68b1c83da79cb8c67046fdb75a22844f4cf86fd5053409c91`。本节不改变跨机器默认参数。

## 06:13 UTC：R46预留实际闭账

R46现场CAS4378释放后，限定25组元数据计量无错误，已知留存逻辑量924,798,428 B。Source06/07复用既有index总量，不扫描native或重读缓存正文；后续小归档/记账增量另列，不冒充全盘同步清点或实际历史峰值。

ROOT于06:13:56 UTC持原卷锁追加[CLOSED-RESERVATION](C:/workspace/ck3_lyd_runtime_20261004/r46-root-storage-admission-20261010-001/CLOSED-RESERVATION.actual.json)，3,042 B / `2166ecf90af0736dacfde648de96000106ecb368d01918fbff0e0adc3dfcf322`。原4 GiB峰值预留已关闭，remaining_reserved_peak_bytes=0；该值是结束后续写入额度，不能解释为4 GiB减留存量。闭账当次free626,476,986,368 B，实际物理分配/历史峰值保持UNKNOWN。

缓存仍沿R44闭场起算到2026-10-17T03:03:44.013573Z，不因复制或prepare/allocate使用而续期；R46原始证据30天、未解问题有限保护7天，构建输入14天，到期按当前用途复核。没有新增删除或自动回收器。约0.94 MB的R46紧凑归档与导入副本单独计费；新的Source08或实机写入须重新登记预算，不能沿用已关闭预留。

## 08:19 UTC：Source06 / Source07 导出实际退役

旧导出已由 Source08 替代，ROOT 与相关执行者均确认后续不消费原路径；原恢复 ZIP、变更文件及来源索引实际保留。按可重建派生物的提前退役规则，ROOT 于 08:16:42 至 08:19:19 UTC 分 16 批删除索引内文件，每批至多 1,000 项。实际 exit 0，15,812 文件全部删除，失败 0；没有递归删除目录。原构建到期时间 Oct24 保持历史值，不把提前退役倒写成自然到期。

| 导出 | 删除文件 | 逻辑字节 | 逐文件 AllocationSize 合计 |
| --- | ---: | ---: | ---: |
| `C:/csr6` 索引内 payload | 7,906 | 141,027,785 | 156,741,592 |
| `C:/csr7` 索引内 payload | 7,906 | 141,030,443 | 156,752,560 |
| 合计 | 15,812 | **282,058,228** | **313,494,152** |

每文件删除前在排他句柄下核验原生身份与原 SHA，删除后确认路径不存在；来源恢复输入在操作期间持有只读句柄。根目录与空目录保留，旧引用的可用性明确改为“索引内 payload 已删除”，不声称目录本身消失。当前 `C:/csr8`、原始 trace、存档和着色器缓存不在此次删除范围。

操作前后卷空闲为 624,725,921,792 → 625,028,612,096 B，增加 302,690,304 B；系统并发活动和账本写入存在，不将此数等同逐文件回收量。两次 ETW 文本和本次源码 payload 累计删除 **11,472,815,493 B 逻辑量**，不重复计算旧删除，也不承诺相同物理净增。

08:24:26 UTC，原清理进程 exit 0 后，两份逐文件审计材料由 14,512,072 B 明文变为 1,752,185 B gzip；完整解压 size/SHA 核对成功后才删除明文。逻辑减少 12,759,887 B 单列，不再计入源码回收量。旧 PLAN/RESULT 不改写，新增可用性记录绑定 gzip 解压后的原始 pins；明文旧路径现为 deleted。两份压缩件分别在 Nov9 08:14:26 / 08:19:19 UTC 到期，摘要在 2027-04-08 08:19:19 UTC 复核，复制或压缩不续龄。

[精简实际回执、两根 tombstone 与账本可用性](receipts/2026-10-10-source06-source07-retirement.actual.json)随本页入库；完整逐文件账本只在外置压缩件中有限保存，不再次提交完整清单。本机这批实际清理不代表其他机器已执行，也没有安装自动 GC。

## 09:30 UTC：Source09 / R48 预算实际关闭

R48启动证明合同失败后，managed cleanup、原host1、keeper0及CAS4416已闭场。ROOT持原卷锁关闭独立4GiB预约，remaining为0；六个互斥已知根的logical subtotal为705,185,114B，未扫描source/native或读取cache正文。该subtotal不等于全项目实际占用或物理峰值，当次free624,020,348,928B单列。

源码与非cache profile14天、raw30天、小记录180天复核，必要保护最多7天；现有cache仍到Oct17 03:03:44UTC，不随复制、使用或失败续期。分类ledger和真实关闭记录已纳入[R48紧凑证据](../li-yu-dao/acceptance/2026-10-10-r0048-holder-startup-contract-red/REPORT.md)，压缩归档仅41,155B，没有新增删除量。后继接口更正位于MAIN case层，可复用Source09及v2seed，省去无必要的新runtime导出和cache快照；任何后继重型写入仍须重新准入。

## 10:01 UTC：R49复用运行时后的预算关闭

R49实际公共run0/verify0、原CK3句柄OS0/native0、host/keeper/allocator0及CAS4427完成后，ROOT在原卷锁内核销独立4GiB预约，remaining0。新增case003/实际run/a11及明确小回执根的已知logical subtotal708,129,647B；现有Source09/O8/native/v2seed计0，不重复计算。物理分配和历史峰值UNKNOWN，free当次623,195,856,896B；本场未新增删除量。

## 10:33 UTC：回收 R48 重复输入副本

ROOT解除旧case002与R48 frozen profile三组重复输入的后续用途，在既有卷锁内复核实际进程、任务总线和恢复源后，实际删除7,374文件，9批、失败0、原进程exit0。逻辑量 **377,746,143 B**；逐文件 `FILE_STANDARD_INFO.AllocationSize` 合计394,349,744 B。卷free为623,175,266,304→623,581,229,056 B，差值不全部归因于回收。

三组分别为case002的3,686份原seed缓存142,910,437 B、原restored_campaign副本91,711,686 B、R48 frozen profile的3,687份原seed缓存143,124,020 B。删除只针对既有冻结清单中的精确叶文件；同一排他句柄核FileID/size/mtime和原SHA后，记录intent、Disposition、close及实际不存在。3687份immutable v2 seed与R34 D2a原存档在操作中实际持READ_DATA句柄，源正文不重复重哈希，身份与原内容pins保留。

全部84份业务/config/outer文件、1份freeze后被游戏改写的缓存、77份run新增缓存，以及case001、case003/R49均保留。R48 report/control/frozen argv/provenance/退出/keeper和紧凑归档仍可读；旧prepared/verify pins只能描述历史，不能再证明已回收profile副本现在完整可用。缓存Oct17、旧checkpoint/raw与保护的原期限不续。

10:35:34 UTC，原删除进程exit0后，两份audit逐字节压缩读回验证原size/SHA，再删除明文。7,944,793 B明文变为862,193 B gzip，减少7,082,600 B单列；到期仍为Nov9 10:30:08 / 10:33:04 UTC，摘要2027-04-08复核。完整逐文件账本只外置限期保存，[小型实际回执与可用性](receipts/2026-10-10-r48-profile-replicas-retirement.actual.json)入库。

## 10:40 UTC：回收三个旧 profile 存档副本

对R29、R26、R10各自`userdir/save games/xar_checkpoint.ck3`，ROOT解除当前用途后逐个验证对应独立checkpoint与目标实际size/SHA相同，保留源READ_DATA句柄并禁止写入/删除，目标share0句柄核原生身份后才删除。三个实际成功、失败0、原进程exit0，共 **275,024,775 B**；实际分配合计275,034,112 B。保留副本分别为B4-factory-result-r3-signed、r4-factory-protection-red-final和0240-detach-second-post-save；全部immutable checkpoint、R29正式B3基线、R34 D2a与代表证据保留。原copy回执不改写，[逐项删除与保留源实际SHA回执](receipts/2026-10-10-three-old-save-replicas-retirement.actual.json)标明旧mutable路径已删除。

原七attempt约21.2GB是历史清点；本次只释放其中三个副本，没有把整组认作垃圾或重新测算剩余量。Oct12原用途复核期限不续。卷free实际623,594,074,112→623,869,100,032 B，变化不全部归因于删除。

本日两份ETW派生文本、退役Source06/07、R48重复输入和三个旧save副本累计实际删除 **12,125,586,411 B逻辑量（约12.13GB）**。两轮审计压缩净减少19,842,487 B另列，既有删除不重复计数。本机结果不代表其他机器已经执行，也未安装自动GC。

缓存原Oct17 03:03:44UTC和配额原Oct12复核期限不续；其他新资产按checkpoint14天/raw30天/record180天复核，必要保护至多7天。约245KB紧凑归档及后续入库副本不在上述闭场计量时点内，作为有界小增量另列；没有保存第二份完整存档或wire。[实际预约、计量、分类与闭场压缩对象](../li-yu-dao/acceptance/2026-10-10-r0049-holder-diagnostic/INDEX.json)。统一自动GC/预约器仍未实现，不把本机人工闭账外推到其他机器。


## 12:53 UTC追加：旧v1缓存副本退役闭环

实际删除7,374项286,248,040B，失败0；当天payload删除累计12,411,834,451B。两份audit完整解压核对后无损压缩，另减8,412,562B，全天audit净减累计28,255,049B，不计入payload或排他磁盘free归因。当前v2与关键基线保留，期限不续。[实际摘要](receipts/2026-10-10-old-shader-cache-replicas-retirement/COMPACT-RECEIPT.actual.json)和[过程/原失败](storage-retention-2026-10-10.md)已入库；原19项小回执保留，不重复提交大jsonl/gzip。
