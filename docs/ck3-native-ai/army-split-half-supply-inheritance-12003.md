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
