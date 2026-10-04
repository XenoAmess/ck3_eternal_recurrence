# P0-SPLIT exact CK3 1.20.0.3 native source contract

2026-10-04. Research / exact static-confirmed for the new split chain. No new live sample, SDK, screen, native invocation, gameplay day, DLL, checkout mutation, test matrix, or Git ref. The installed EXE was read and matched Steam build25652598 SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`. Historical Z: merge evidence is absent on this machine; only its tracked conclusion is reused. Exact spans and disassembly remain here.

## Source and call chain

The existing typed action remains `ck3_execute_step(step="split-army-half-D", expected_revision=R)`, where D is the full public CUnit ID. Native bridge `ck3_12002_military.cpp:484–517` resolves fresh D, reads Unit+178 internal full CArmy ID and calls `296CF60(kind1, nativeArmyId, freshPlayedCharacterId, null)`. Packet layout and old ABI are reused, not revalidated by a new matrix. GUI `window_army.gui:1351–1362` uses `ArmyWindow.SplitHalfSelected`, current legality `CanSplitHalfSelected` and `BuildSplitHalfTooltip`. GUI native caller `13481A0` invokes the same validator at `13481BE` and enqueues the actual command.

Command secondary executor `296C310` resolves source CArmy using the complete ID from secondary-this+10, calls `296B6E0` at `296C384`, then partitions original regiment IDs between the retained source and newly returned sibling. `296B6E0` calls `2A96EA0` at `296B85B` to allocate a CArmy and corresponding CUnit at the original resolved province and owner context. The creator increments the allocation generation at `2A96FA2`, writes the CArmy full ID at `2A96FBD`, creates CUnit via `2AD67B0` at `2A970D8`, then stores CUnit ID at CArmy+124 (`2A970FA–FD`) and the CArmy ID at CUnit+178 (`2A97134–37`). This supports distinct same-session sibling identity, not a reusable global number after reload.

## Split supply and capacity

`296B956` reads source CArmy+180, and `296B95D` writes precisely the same signed64 raw value to new CArmy+180. Current source `ck3_12002_army.cpp:333` and the existing capacity topic identify this as current supply. The clone does not divide it by two and does not apply a capacity percentage. Original source is retained by execution. The same clone copies source+188 to new+188 (`296B948–94F`) and source+190 to new+190 (`296B964–96B`). Their timing meanings are the supply-clock owner's separate chain; this lane proves copying only. `2A96EA0` initially writes now at new+190 (`2A97062–72`), then this clone overwrites it with source+190: new allocation does not itself prove a fresh grace anchor.

Capacity is the existing `2C53C10(out,CArmy,null)` calculation from the current commander, not a copied "half capacity" field. The split executor after both composition refreshes calls existing commander selector `2C11A10(actor,false)` at `296CCC5`; valid returned Character is assigned to the sibling with `24DFA10` at `296CD34`. It is not necessarily the actor itself. Source commander remains separately observed; selector ranking is reused from commander topic and not closed anew here. Actual resulting commanders and capacities must be read after the action. Supply copied before commander selection is not proof of capacity equality or subsequent clamping time. No claim is made that final stored supply is always <= the new capacity before the normal update.

## Regiment assignment

`296B260` traverses the source `CArmy+38` array with count+44, resolves full ArmyRegiment IDs and constructs 16-byte sorting rows containing actual regiment pointer and signed weight. It has three groups:

1. A valid CMenAtArmsType at ArmyRegiment+18 (tag `4744624F` at definition+38) enters the MAA group. Weight is current soldiers ArmyRegiment+38, with a separate total per definition index+10.
2. A valid linked Character at ArmyRegiment+148 enters the character/knight group. Its sorting weight is Character+EC (prowess input); this is not the regiment's public soldier count.
3. Remaining records enter the other group with current soldiers ArmyRegiment+38. It includes the normal levy case, but the unqualified group must not be renamed "all and only levies" without record type evidence.

The MAA group is sorted by descending row weight (small-row insertion branch `296C730–7A4`, native sort for >32). It traverses descending records at `296C840`, uses same-type totals plus floor(1.5*current soldiers) in the transfer comparison, and otherwise balances total retained/sibling soldiers for a type not yet assigned to the sibling. Do not simplify this into every MAA type split exactly in half. The other group is ascending-sorted and traversed in reverse, moving a whole record when retained running soldier total is >= sibling total (`296CAD0–CB11`). These counters carry the earlier MAA totals. The character group is ascending-sorted then traversed in reverse, with independent prowess-weight balancing counters (`296CC60–CC9E`). This prevents "half" from implying exact equality of displayed soldiers or equal regiment counts.

Every actual transfer removes the same full ArmyRegiment ID from source through `24E0D30` and appends it to sibling through `24E0C70` (MAA `296C947/956`, other `296CAF2/CB05`, character `296CC7F/CC92`). The append helper writes CArmy ID back to ArmyRegiment+140 at `24E0D14` and appends the ID into the new army's vector. No new ArmyRegiment is constructed by these transfer blocks; individual records stay whole. Both compositions are refreshed using `24E8120` at `296CCA5/CCB4`. Formal proof of all current/max totals remaining unchanged still needs same-date live per-record rows: action completion alone cannot supply them.

## Existing merge formula reused

The tracked merge topic closes `296EEA0→2C54FD0→2C551A0`, keeps destination D and consumes source S. Supply is absolute supply-unit raw, not percentage. Destination weight is native `24E0160(D,out,0)+24E02A0(D,out)`; source weight is `2A95740(source_regiment_array,flags0)*100000`. It cannot be replaced with public current_soldiers for arbitrary records. Positive-weight result is the sum of per-army native fixed division then fixed multiplication of each original supply; clamp to the newly selected commander's native capacity, then write destination+180. Capacity and monthly supply changes are not summed. Two fixed truncation stages matter; even immediately recombining equal-supply split armies is not promised to restore identical raw supply.

## Available observation and remaining gap

Current strengths returns all `regiment_replenishment[]` ArmyRegiment full IDs when the optional collection is available (`ck3_12002_army.cpp:359–364`). Even unavailable first-record rows preserve their real `army_regiment_id`: use complete collections to prove source/sibling partition. Current/max per ArmyRegiment are already read at :289–290 but only aggregated to army totals; first-record chunks have partial coverage and cannot stand in for every full record. The current MCP exposes no native merge weight field. Numeric verification of all per-regiment values or a specific merge arithmetic example requires the smallest extension to the same strengths query or an independently bound save reader. Until then report actual aggregate changes, membership, supply, capacity and commanders separately.

## Exact evidence

| Logical span | Length | SHA-256 |
|---|---:|---|
| Executor 296C310..296CE13 | 2819 | 2e58b65cb25d14d7db2c466d8373f66bf84111660180f109eb699a50a3a1241d |
| Clone 296B6E0..296B9B0 | 720 | abcece0993c77c5e8eb0ae6c9c929ca50eb3103f00c8a8bcecd0992a118e6f13 |
| Classification 296B260..296B6E0 (includes trailing padding) | 1152 | 9633a7605a07a66521a24523f8ef94e4e717178d72e81a2feb0e11f0d041b212 |
| Army/Unit creation 2A96EA0..2A97194 | 756 | 1a597ddc81ef51fd181d30b2d3fad881a0091e4ccbfdd080c3a22d25b3204e12 |
| Remove 24E0D30..24E0EA9 | 377 | 42668b2c3d09878e1f4fad66e0e16e9084add1bb9d6debb8204ac3d506233be9 |
| Append 24E0C70..24E0D30 (complete fragmented function plus padding) | 192 | 2f9446d95b9e7b7a0fc87bc213fdfe2b32995cd22705841800915991737ee911 |
| New commander selector 2C11A10..2C11C0F | 511 | 88378335511265e6310f58513b033f742b7fab839eaf836d92f81f5280651a46 |

Single .pdata regions for classification, append and creator are only prefixes. Full contiguous spans were retained as additional evidence, without overwriting the prefixes. No prefix is claimed as the full function. All unknown selector/capacity-after-selection/live branches remain open.

2026-10-04 correction: the actual append backlink store is RVA `24E0D14` (full append disassembly), replacing the a01 mistyped `24E0CF7`. The mechanism and bytes are unchanged; a01 remains preserved.



### 2026-10-04 补记：E04 实际半拆的兵团守恒、继承及同省用量（候选追加）

本次为 Root 管理的原版 E04 重放 `R0161`，角色 `33388`，同一暂停日期 `date_raw=53147160`。准备输入记录的 EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`、DLL 为 `726d0f1970b4df4f7fc30bc641f31d0183b197efbebd1c1d9c240f2a6233b3f5`，独立源码冻结为 `f8530f4aeb64735dbeae4831f3bc6c315276bb88`。原始 query 的 `source.game_version/executable_sha256` 仍为 null；构建归属由另附 Root 准备记录绑定，不回填原响应。准备文件 `live_verified=false` 只是启动前记录；实际响应承担本次实机观察，不能单靠准备文件声称已实机。

`split-army-half-0` 在 `expected_revision=6` 返回 `split_submitted`，随后独立 roster 从 `native:5/public6/native5` 到 `native:6/public7/native6`，验证旧 public/native `0/0` 保留、仅新增 public `170` / native CArmy `161`，两者均仍在省 `1506`，原有其它玩家军队 ID 保留。兵员 query 则从 `native:4/public5/native4` 到 `native:6/public7/native6`；每份响应保留自己的 revision，不能把两份当作同一 frame。所有 paired 日期均为 `53147160` 且暂停。

| 分配 | 完整 ArmyRegiment IDs（按响应顺序） | 兵团数 | 当前/最大兵员 |
|---|---|---:|---:|
| 拆前 0/0 | 0,1,2,3,4,5,6,7,8,9,10,11,12 | 13 | 5660/5660 |
| 保留 0/0 | 4,5,6,8,9,10,12 | 7 | 2540/2540 |
| 新建 170/161 | 11,2,3,0,7,1 | 6 | 3120/3120 |

独立逐条核对表 `REGIMENT-PARTITION.csv` 证明：拆后两集合无交集、并集恰等于拆前集合，13 条完整 ID 每条当前/最大兵员均不变，总兵员仍为 5660。半拆没有把每条兵团一分为二，本例也没有得到两个 2830：两军相差 580，分别约占原兵员 44.88% / 55.12%。本例只核实实际分配结果；原版 exact .3 源树已确认按兵团类别处理，本次 MCP 没有 type/prowess 明细，不能再声称独立复算了每个分支的选择。

| 直接观察字段（均 Q100000） | 拆前 0/0 raw | 拆后 0/0 raw | 拆后 170/161 raw |
|---|---:|---:|---:|
| current_supply | 8299737 | 8299737 | 8299737 |
| current_supply_capacity | 10000000 | 10000000 | 10000000 |
| current_attrition_fraction | 1000 | 1000 | 1000 |
| current_supply_change_monthly | -1000000 | -1000000 | -877192 |

两军实际补给均为 `82.99737`，容量均为 `100`，没有按人数比例对半分 current supply。本次相同容量只能说明这两份当前查询结果相同，不能证明 capacity 是 clone 字段；已闭合原生容量树仍以当前统帅 modifier 求值。新军当前月变为 `-8.77192`，原军为 `-10`，必须逐军读当前 helper，不能把一个月变复制给另一支军队，也不能把月变预测当已实际扣除的补给。

`+188` 成功补给更新日期 storage64=`300333821678253472` / raw=`53147040`，`+190` grace anchor storage64=`300061168564366016` / raw=`53144256`：拆前、拆后 0/0、拆后 170/161 四个精确数值全部相同，符合 exact clone 的复制链。原军 bucket phase=0，新军 phase=11，当前 selected phase=5；新 ID 没有使这两个日期锚变成当前日期。本 paired case 未推进一天，未观察下一次 conditional supply check；未来 bucket 窗口应交给 clock 专题，并区分预测与实际执行。

同省用量也由两次 available 原生 preview 独立绑定：拆前 `preview-move-army-0-to-1527` 为 `native:2/public3/native2`，拆后 `preview-move-army-170-to-1527` 为 `native:6/public7/native6`，两份 episode run ID 均 `native-33388-76ee093d71da`、connection generation=1、日期 `53147160`。两次 current 省 `1506` 的 native usage 均 `5660`、limit 均 `3680`，仍超出 `1980`。即使新军自身只有 `3120<3680`，留在同省的另一军仍计入该原生 aggregate 用量。

两次 preview 的统帅计算上下文分别为 null 与 `33388`；预览的 owner fallback / commander context 不是独立 `ck3_query_army_commander` 赋任认证，不能直接推出旧军由谁、新军确实由谁统领。两次 target London `1527` 当前 usage=0 / limit=7342 也只表示查询时该目标读数，不是两军未来抵达后的用量、补给、月变或可持续驻留保证。失败 `preview-split-a01`（目标1513）没有作为这些 available 数值的证据。

可供口播的有限主张：

- “平分会移动完整兵团，这次 5660 人变成了 2540 和 3120。”
- “拆出来的两支军队沿用了原军当前的补给值和补给日期锚。”
- “只在原地拆成两支，省里的总用量还是 5660，容量还是 3680；驻扎压力要按同地部队合计看。”

仍未观测：真正分省/离开后的 aggregate、按 bucket 执行的下一次补给更新、统帅独立赋任查询、非相同 current supplies 的实机合军、native 合军权重两操作数与 fixed 截断/容量 clamp 数字样本、合军后 source 消失/目标保留。此 case 的公开 2540/3120 兵员不能冒充 `24E0160+24E02A0` / `2A95740` 原生权重。录像及简中 UI 图像未由本复核 lane 阅读，不以 query 证据声称画面、清洁镜头或成片通过。

原始输入精确绑定：

| 输入 | SHA-256 | 路径 |
|---|---|---|
| health-before-halt-a01 | `394c7ff61f08c2f3f316a92b9fda6f4fe44add842dcad881bdda3bef35b67b10` | `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a01\responses\health-before-halt-a01.json` |
| after-halt-snapshot-a01 | `ad78fe62bc14dfcb08611858f1634fec15db2bcb4f09e0476a484ffc7a2e8bdb` | `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a01\responses\after-halt-snapshot-a01.json` |
| split-initial-a01 | `412cc7cc652fa33561f26dd34458a653b1701558bd91210eb1b488eb95bd6ec0` | `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a01\responses\split-initial-a01.json` |
| after-split-snapshot-a01 | `cf50330fd0965f7a12f5438a565300191e25075bc017013f26a76a96b8aba9f1` | `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a01\responses\after-split-snapshot-a01.json` |
| health-after-split-a01 | `405eeac3650652db55c617ee8bd3977b8a51f3c09a35fdf32dee60ab8cabd87f` | `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a01\responses\health-after-split-a01.json` |
| starting-health-a01 | `74a1ffd31f4c4718983f7844f3d90c08289bdc9463eb40154dfb81f4835dac24` | `C:\ck3-war-episode04-research-20261004-a01\operations-main-case-a01\starting-health-a01\002-000-health.response.json` |
| preview-before | `52b9fe2170822efe9ee15af967c4583ed7ac954b1427b66c99ad423a596a0ab7` | `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a01\responses\preview-london-a01.json` |
| preview-after | `efa1e2c44eef10ec4b4d5506f124b5efecac3565334b22bf96d8124f789964c4` | `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a01\responses\preview-split-london-a01.json` |
| prepared-runtime | `d891d04ac9a2dd981f7c3e741219106ce84ea5b9375767c268830c715bdda2d9` | `C:\ck3-war-episode04-research-20261004-a01\prepared-main-case-a01\prepared.json` |
| source-freeze | `00b7acd287c0af28c99d08329aca98039733570ddab3a8d8e06785b01571828f` | `C:\ck3-war-episode04-research-20261004-a01\capture-source-freeze-a02\manifest.json` |

逐条计算与边界：`C:\ck3-war-episode04-research-20261004-a01\split-live-review-a01\PAIRED-ANALYSIS.json`，SHA-256 `1a6767f36fcc64af99b4bc88e6d0f570896c22024d1ac7a774cb99e862ed41cf`。
完整原生静态语义：`D:\ck3-war-episode04-research-20261004-a01\split-merge\SOURCE-CONTRACT-a02.md`，SHA-256 `da0d738852e0f6fa35905912c5610b633ee9d0501fbf1cb15549006de052a2da`。
新 native research plan 的 check/render 均通过，仅证明声明结构和引用 bytes/hash 一致，不验证 CK3 语义、实机执行或拍摄质量。


### 2026-10-05 补记：R0162 重新识别半拆及后续实际兵员样本（候选追加）

本复核只读 Root `native-live-main-case-a02/responses` 的 R0162 响应；当前冻结输入为 `C:\ck3-war-episode04-research-20261004-a01\split-live-r0162-a01\scan-a08`。每份 raw 文件均独立绑定 SHA-256，每份 query 保留自己的 public/native revision 与 date。原始 query 的版本/hash null 保持原样，R0162 独立启动输入及 run allocator 收据另附 `RUNTIME-BINDING.json`；prepared.game EXE SHA匹配上述exactpin，DLL输入SHA为 `cb9af1f699589c94a478158543f8ff57ca29af6b63be5386de5af586f31f60e8`，allocator run为 `desktop-3fevhd2-1c74096080--vanilla--R0162`。prepared.live_verified=false只代表准备输入；不将其冒充live process attestation，也不借R0161绑定替代。EXE exact .3 静态树仍绑定 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

先从本 run 的 split literal、前后 roster 与 strengths 重新识别：保留 public/native `0/0`，新军 public/native `170/161`。虽然数值可能恰与旧 run 相同，本复核没有沿用旧 ID。拆前共 13 条完整 ArmyRegiment ID，拆后 7 / 6 条，无交集、并集精确等于拆前集合。每条 current/max 不变，兵团行的 current/max 汇总分别与三份军队顶层字段相等，军队总 current/max 守恒为 5660/5660；两军 current 为 2540 / 3120。

| 完整 reg ID | 拆前 current/max | 拆后 public army | 拆后 current/max |
|---:|---:|---:|---:|
| 0 | 1000/1000 | 170 | 1000/1000 |
| 1 | 800/800 | 170 | 800/800 |
| 2 | 100/100 | 170 | 100/100 |
| 3 | 20/20 | 170 | 20/20 |
| 4 | 800/800 | 0 | 800/800 |
| 5 | 400/400 | 0 | 400/400 |
| 6 | 20/20 | 0 | 20/20 |
| 7 | 800/800 | 170 | 800/800 |
| 8 | 100/100 | 0 | 100/100 |
| 9 | 20/20 | 0 | 20/20 |
| 10 | 800/800 | 0 | 800/800 |
| 11 | 400/400 | 170 | 400/400 |
| 12 | 400/400 | 0 | 400/400 |

| 观察（拆前一行、拆后两行）public/native | supply raw/scale | capacity raw/scale | monthly raw/scale |
|---|---:|---:|---:|
| 0/0 | 8299737/100000 | 10000000/100000 | -1000000/100000 |
| 0/0 | 8299737/100000 | 10000000/100000 | -1000000/100000 |
| 170/161 | 8299737/100000 | 10000000/100000 | -877192/100000 |

本例 supply 精确相同=`True`，日期锚四项 storage64/raw 精确继承=`True`，实际容量相同=`True`。相同 capacity 仅是当前查询事实，不能推导 capacity 为 clone 字段；原生容量树仍求当前统帅 modifier。月变是当前 helper 预测值，不能代替已扣除 supply，更不能作为已损失 soldiers。

冻结点已收到 57 份拆后 family strengths 样本，其中 2 个区间观察到 current/max 的改变：

| date_raw | public/native revision | 军队 current/max | 相对上一完整 family 样本的逐 reg 变化 |
|---:|---|---|---|
| 53147160 | 4/3 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147160 | 6/5 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147160 | 6/5 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147160 | 8/7 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147160 | 10/9 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147184 | 13/12 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147184 | 15/14 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147184 | 17/16 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147208 | 21/20 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147208 | 23/22 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147232 | 26/25 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147232 | 26/25 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147232 | 28/27 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147232 | 30/29 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147256 | 33/32 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147256 | 35/34 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147280 | 38/37 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147280 | 38/37 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147280 | 39/38 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147280 | 40/39 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147280 | 41/40 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147280 | 41/40 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147280 | 43/42 | 0/0=2540/2540; 170/161=3120/3120 | 无 current/max 变化 |
| 53147304 | 46/45 | 0/0=2540/2540; 170/161=3089/3120 | reg11:400→396 (max400→400); reg2:100→99 (max100→100); reg0:1000→990 (max1000→1000); reg7:800→792 (max800→800); reg1:800→792 (max800→800) |
| 53147304 | 46/45 | 0/0=2540/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147304 | 46/45 | 0/0=2540/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147304 | 48/47 | 0/0=2540/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147328 | 51/50 | 0/0=2540/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147328 | 53/52 | 0/0=2540/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147352 | 56/55 | 0/0=2540/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147352 | 58/57 | 0/0=2540/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147376 | 61/60 | 0/0=2413/2540; 170/161=3089/3120 | reg4:800→760 (max800→800); reg5:400→380 (max400→400); reg8:100→95 (max100→100); reg10:800→759 (max800→800); reg12:400→379 (max400→400) |
| 53147376 | 61/60 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147376 | 61/60 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147376 | 61/60 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147376 | 63/62 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147400 | 66/65 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147400 | 68/67 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147424 | 72/71 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147448 | 75/74 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147448 | 77/76 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147472 | 80/79 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147472 | 82/81 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147496 | 85/84 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147520 | 88/87 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147520 | 90/89 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147544 | 93/92 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147544 | 95/94 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147568 | 97/96 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147592 | 100/99 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147592 | 102/101 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147616 | 105/104 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147616 | 107/106 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147640 | 110/109 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147664 | 113/112 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147664 | 115/114 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |
| 53147688 | 118/117 | 0/0=2413/2540; 170/161=3089/3120 | 无 current/max 变化 |

分组详表位于 `C:\ck3-war-episode04-research-20261004-a01\split-live-r0162-a01\scan-a08\REGIMENT-TIMELINE.json`。逐条 delta 按当前军队 ID 分组，缺失/不可用 ID 不补零，额外或重复 ID 明示；若样本 family 不完整，不能冒充完整军队对照。此表只读实际兵员结果，尚未从 delta 单独认定 combat、attrition、replenishment 或脚本原因；完整 producer 因果归属继续由相应专题闭合。最后冻结日期为 `53147688`；没有收到的后续日程、抵达或检查执行仍未观测。

实机合军原生权重数值、fixed 截断与新统帅 capacity clamp 仍应单独观察；公开 2540/3120 人数不替代 `24E0160+24E02A0` / `2A95740` 两侧原生操作数。画面、简中控件和 clean spans 均由 Root 另验，本文件不作影片质量或人工签核声明。

原始响应绑定：

| 文件 | SHA-256 |
|---|---|
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\split-initial-a02.json` | `702e60cd529b98d7207160a959ab2cacc2d300ddeb4653de7abed5ddd7cd6f2b` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\before-split-health-a02.json` | `c310dd37bc045f389783a6eb2c030052fd95e2f0ae2cf2c10a498022f7d72c82` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\before-split-snapshot-a02.json` | `eb32f751a101598b9c99f4a54e91e1177a569d478f3eb0d33b2dc62cb403ef27` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\after-split-snapshot-a02.json` | `60f120a80401204546726561f4ca965f0f924c80d1cdda89f49745cf8a2ff0f9` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\after-split-health-a02.json` | `c50795a38dcb1c360525c0fede84cb14e27165fe2b4c181fa481e8365248b54a` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\after-london-move-health-a02.json` | `5cf07623dad3c545526cd24c351fd21a56ceea9f8b330ad8f0b8c03736367554` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse01-006-000-health.json` | `8831dd004b0a7277226ff511203b580ee9f181be96f747b5bc0fb906189d490d` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse01-012-001-health.json` | `c09c6e3550c32bb3b98e3dbf09d54f1763265166e58b3431bd6c2bb7ba835d80` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse01-018-002-health.json` | `cb8cf1b97f7d1d74130cbda6cd1d920c135489738e8175fff19d1082b1640e96` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse01-024-003-health.json` | `0eeaecb9f4086651d2fb45dbe3ba6c3d76e8b911050d514b3f6f97966c7a81b1` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse01-030-004-health.json` | `f4b4e557232abeaab1f56c1c572b31e35146c8eb975092fcc727fad7e29807bf` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse01-036-005-health.json` | `acd6f7296836433595cf3b86da9b89f6febfdfcaef0fd15df240ebabcf6f6bf6` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse01-042-006-health.json` | `3f9f345dbc31b55387ce6b1d03f4d3b44d68b23600e9cedbebdda7ab2607b3d9` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse01-048-007-health.json` | `19b3d22589d5a45988ffe1757c8f88fd50a437451da0086778809797fdf5c50e` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse01-054-008-health.json` | `c3fab189554ace5de606806458f6f90060873fca04fa4bab36b6d6ad6bcebcfa` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse02-006-000-health.json` | `b51f5903729a64e7cd2f2e9017ccc67d90bbfd321aedd11385abe5f2e8addf62` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse02-012-001-health.json` | `9fc28d616bbd7ef509095705f831a7875e6fc7df6dd8709bf261b179579bdffd` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse02-018-002-health.json` | `c2f882ee028b69ad4b7e8981b460e0395f373b674251f686b1de2c6baf4b093f` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse02-024-003-health.json` | `5f84d8c298d6aab54818626e8852879aa79a445dd7b8e76f800a0080d5c67e97` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse02-030-004-health.json` | `3f1eb29fd1268baeea32d826c67ee7fe485ec2a4098e25da8f77b6ac4fbf0788` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse02-036-005-health.json` | `23dc7e4c08a4d83b85f54e8297e0e8d7fe7fc7a788b6ee00b778b72abc93b97a` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\locked-before-health-a02.json` | `2d453b9e2070fc10b8d32aabbc131a7c337e7e411e876cc87808e65ae22008a7` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\halt-locked-after-health-a02.json` | `93ed408eb3e2f441ef4cbd9d7d8beb6e97b5d8671b0aa78b30b59e05acaa268e` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\reroute-locked-after-health-a02.json` | `6c42342dd222f6dc7e7cef09cf84710a6aaeb6d4c9d5cbc6f105e439dc1fd40f` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\halt-locked-final-health-a02.json` | `ed7260e1e79c06868d67f83e3b9601dda35ec2f2499661b63bf1684d9a53905c` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse03-006-000-health.json` | `ade7b4b47e122ae36d5e1148fb0b572df0191e4089bef9d5d80efa1632250ff5` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse03-012-001-health.json` | `f0e7080d9fb450beb595e8ea46e29d74916ff4a0e2ef7bd424b951646c24ef96` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse03-018-002-health.json` | `55ee276152690b5517b19629f82c6b03650cafb50acadb1a8dc0c65a258b6108` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\after-update-health-a02.json` | `950a7798473cae566e4a0a4f923516f3def3b9b1357b7e626293bafff3394c4c` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse04-006-000-health.json` | `e2de3454b34cd5d50231f0ec77ee6ed63ce7aa1a2cb17d4a456a1d74bdd6132f` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse04-012-001-health.json` | `aa6794c08306128d7c5b89bebc2c9b71c91ed0d3ee34965154ab8246b49de72b` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse04-018-002-health.json` | `ed351bd5cd22411ec5f808447ffaec1a5c2e60651cacd7c0ddace6edfe9ea58f` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse04-024-003-health.json` | `afa30de6b4457604be710c2fa038bcfb9136af5f3e6ee5760c561a84b70f6ffc` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse04-030-004-health.json` | `c7c473f06db60bcfd6fa13399bd91ddcf2092cad64434331f75a2aacd848f7f9` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse04-036-005-health.json` | `c478e392bc8c7e596ccc8498f32a02e8854238d58e2f2d89880627a80a7def9e` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse04-042-006-health.json` | `306fb22d41962effe50510d141470784fa40ca36ee0f1b5ba1a7b685ed4e2536` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\arrival-health-a02.json` | `a96ef26435d125e733cad74ffd559d7de95d095356c2267473fd7bd537370951` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\recovery-before-health-a02.json` | `06339bfde8d3e8f6c6cd726e0b10a7b12891c8d83133296ab5f80b93875c537e` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-006-000-health.json` | `10253fa7c9f36169cbc6d7dbaf2db7d3125cf84743b8e458d336c2c4d4d4ae94` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-012-001-health.json` | `53627e802bf034a9fcf3b6fbb60ad787f6d87c08af46523b082f5c5612a91e4a` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-018-002-health.json` | `5dd6251521c7aef77a9cf01ffe8e8b3c45ba24bc8f5c781b96f6bbd258fb9db6` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-024-003-health.json` | `b1b6caf3bbde9a5f48371f44fec396d03b35a0b91b5510fc5a1c5fb7ab1b84a5` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-030-004-health.json` | `f79b6f2dcb74ace36deec8b552ea26287f9bc062a1bc136cb1ee852f11d309cb` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-036-005-health.json` | `7bfa0867bdb6a467352884ea6e26ac58fe9457d73f218f99ab1d4704e53d4e6e` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-042-006-health.json` | `af1738e048aea2807b26bb8f737638b212827e19bc9a97cd72a612fb8140f90a` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-048-007-health.json` | `550413554af01e19d8688a11f218831c84d24ed953f6bbd695bbddd82a4b39e4` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-054-008-health.json` | `f4022a1a1b0fae7a3838d439c67804380fed8886f726c4a5cd6cef81d47fafc3` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-060-009-health.json` | `7f9d23ea501e2c12ef07ac91c7449914c2bb5e5400069a5a76b2727e5087c79c` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-066-010-health.json` | `528ed0ddc99245636de6ee8572fd064969999b9c7843e95ed9f9c5d9d802acce` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-072-011-health.json` | `4998a029da2c87f9e4bdefcaf2b3e4571cb06a9bba4072efffc464539866487e` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-078-012-health.json` | `f1f20e28ad412d4401e8ad58a7e13150c966393badb4764493ef383e3dd46f88` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-084-013-health.json` | `7812fa3a7b556df0b943bd65dd15b9ab774379486d520cf5ff1be8fb948533ec` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-090-014-health.json` | `15a54c64ed416bc24a97ae8f1954fd8ddf3767a7653e6af3739f36ed3a7aa108` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-096-015-health.json` | `a911bf9ae50bddec7c9055b997fdd7f79ac9881d2b074937acd7654787f470f4` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-102-016-health.json` | `948c92da9f5e67dc57d12c344b593ebb8ae909b9d75e734e1e5d8cb77b364dc2` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-108-017-health.json` | `807a8f3bfce0b3a2cd6ab967bb10f242c9bc7a2aa21a66d619792ddd827e09c3` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-114-018-health.json` | `24e6a4f580f7586ec6553a0bc11f9c2fee493afb610b8f9415ddcfef22462c03` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-120-019-health.json` | `fe6e2a12de28bdc8c3f528185b330c35dab279a613b0709bd7f097056d9a8dcd` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-126-020-health.json` | `4c03f2bc2e53bf05216dfa65daf107a7114a064c44ebac3eca9205985b8589a9` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-132-021-health.json` | `b59679ac60fbee9383473856d9bad672a45c191b6a914b775926e62604184402` |
| `C:\ck3-war-episode04-research-20261004-a01\native-live-main-case-a02\responses\r0162-pulse05-138-022-health.json` | `f6827d7ca4e6e88c75c0220528639866d20bc78d613c3ab9a69f5e5701edfa21` |

失败/不可解析的 body 也保存在 `C:\ck3-war-episode04-research-20261004-a01\split-live-r0162-a01\scan-a08\INPUT-CACHE.json` 的 `unparsed_or_error_bodies` 中，不被当作 available 样本。分析 JSON SHA-256=`74e8269286b286595a70cf549e1cb717386deda5084925abdf9a752609c0267c`，timeline SHA-256=`05aa65b0e5fb603a31d91814661b3ba1007660f35b6918c7dbc3c5ff93c57e85`。Native plan check/render 只核声明结构与精确文件 bytes/hash，不验证原生语义或代替实机执行。

全部被查询军队的分组（含16777220，且不把166 unavailable当零）另在 `C:\ck3-war-episode04-research-20261004-a01\split-live-r0162-a01\scan-a08\ALL-ARMY-REGIMENT-TIMELINE.json`，SHA `b3b32484543d8006d960841a4bebdcf38a55433bc15831c19a50b42ac5ba533c`。完整timeline与新增changed rows摘要分开，ownership transfer不当作人数死亡。
