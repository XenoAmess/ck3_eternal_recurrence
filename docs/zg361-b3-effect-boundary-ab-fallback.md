# B3 纯加载性能 RED 的 effect 文件边界 A/B 预案

## 状态与使用门槛

本节保留预案形成时 **no-launch、未物化** 的 fallback 基线；预案后来已在 r5 触发，四轮实机结果见文末：

- r3 artifact：`Z:\ck3_mod_rewrite_process_assets\zg361\b3e-27b66b3-20260904-063948Z`
- source：上述目录的 `product-source/`
- source commit 标签：`27b66b3`
- `projection.json` SHA-256：`b769ca3e36e42cb30ae667b91b7f7b54b7648b5ab3c0f28144b18a4c82d9c0ad`

只有 r4 已完成语义修正、静态与原生门禁均 GREEN，且余下 RED 被归因为纯加载性能时，才执行 B。语法错误、unknown effect、缺文件、错误 mod 顺序、native 注入失败、fixture 或 runner RED 都不属于这个门槛。

预案形成时没有生成 B 产品树、没有启动 CK3，也没有把“文件过大”写成既定根因；当时结论仅是文件边界值得用严格同条件 A/B 隔离。文末 ABBA 已完成，并否定把文件边界写成本次 terminal RED 根因。

## r3 effect 画像

r3 `product-source/common/scripted_effects` 共 **401 个文件、3581 个顶层 effect、14,305,819 bytes**。B2 以后文件已经满足 1–10 目标；超量全部来自旧边界豁免。

按 effect 数和字节最突出的文件如下：

| 文件 | effects | bytes | B 动作 |
|---|---:|---:|---|
| `zg361_generated_mechanism_effects.txt` | 1449 | 1,019,397 | 拆分 |
| `zg361_generated_scoreboard_snapshots.txt` | 6 | 480,700 | 保持；已经符合 1–10 |
| `zg361_workforce_endgame_003_m360_central_route_a_materialize_effects.txt` | 1 | 478,588 | 保持；单定义不可做纯边界拆分 |
| `zg361_workforce_endgame_004_m360_central_route_b_materialize_effects.txt` | 1 | 469,778 | 保持；单定义不可做纯边界拆分 |
| `zg361_workforce_endgame_058_al_m360_route_a_effects.txt` | 1 | 335,797 | 保持；单定义不可做纯边界拆分 |
| `zg361_workforce_endgame_059_al_m360_route_b_effects.txt` | 1 | 319,374 | 保持；单定义不可做纯边界拆分 |
| `zg361_b1_runtime_effects.txt` | 41 | 255,586 | 拆分 |
| `zg361_b1_runtime_effects_part2.txt` | 36 | 240,700 | 拆分 |
| `zg361_workforce_endgame_055_ad_m276_m277_effects.txt` | 8 | 130,221 | 保持；已经符合 1–10 |
| `zg361_workforce_endgame_005_m360_central_source_effects.txt` | 2 | 120,279 | 保持；已经符合 1–10 |

三个 B owner 的冻结身份为：

| owner | SHA-256 |
|---|---|
| `zg361_generated_mechanism_effects.txt` | `9e0479b33b322c3d51921180b5a4c34adc13bb9cea9f0f7a70d577a945edd052` |
| `zg361_b1_runtime_effects.txt` | `7e373996a4789f64df5bdb85448f01494a63902abc883df2731dc8318f966247` |
| `zg361_b1_runtime_effects_part2.txt` | `1f2d76436de74fb37698103f90adc029bac2ac16dd75b29e98d428e3e33f663c` |

`zg361_effects.txt` 虽在开发树的 pre-B2 豁免表中，但 **不在 r3 product-source**。因此本轮 B 不制造或加入它。若 r4 的 A source 包含该 26-effect owner，规划器会让整树 1–10/不超过 20 门禁 RED；必须先显式增加它的用途拆分契约，不能带着豁免开始 A/B。

## A 与 B 的唯一区别

### A：语义修正后原边界

A 必须是 r4 实际待测的完整 source：包含已经确认的语义修正，但三个 owner 仍保持原文件边界。A 不是回退到 r3 内容。

### B：从 A 即时投影的纯边界候选

B 复制 A 全树，只删除上述三个 owner，并写入 198 个小文件：

- mechanism：186 个文件。
  - 1 个 ledger bootstrap；
  - 相邻两个 mechanism 为一组，每组完整保留 A/B/C choices 与 AI resolver，共 8 effects；最后 `361` 单独 4 effects，共 181 组；
  - player dispatch、AI batch、reference charter、organization climate 各 1 个文件。
- B1 第一段：5 个用途文件，effect 数依次为 `8, 9, 9, 8, 7`：case/bootstrap/policy/KPI、cycle/self-review、peer/facts/shadow、quota/bank/debt、huddle/agenda。
- B1 第二段：7 个用途文件，effect 数依次为 `6, 8, 4, 6, 5, 3, 4`：agenda/dissent/publication、pending/reopen、calibration finish/recusal、calibration controls/publish、appeal/peer submission、peer-slot consumption、appeal-credit/M360 source。

r3 内存规划结果：

- B effect 文件：`596`，相对 A 增加 `195`；
- effect 定义：仍为 `3581`；
- 三个 owner 的 1526 个 effect 定义逐 block 字节不变；
- B 全树最大 effect/file：`10`；1–10 miss：`0`；超过 20：`0`；
- 新 shards 总字节：`1,525,771`。相对原三个文件多出的 10,088 bytes 仅为各文件 BOM 和取证 header；
- definition-surface digest：`2b3c79d2503941ee1e75e5d111e91db5eae37323478c32e1f9dfe0970ba2fefd`；
- call-graph digest：`ce3e82408378ad70376f066ef12f94cc9d68847fcffe7269378718611e3f5387`。

这里的“等价”是严格的 effect 定义等价：名字、顺序、每个完整 block 的字节及从 block 提取的 effect 调用图都不变。文件头注释不是 CK3 语义的一部分。

## 规划与物化命令

只读复核 r3，不生成 B：

```powershell
py tools/plan_zg361_b3_effect_split_fallback.py `
  --source-root "Z:\ck3_mod_rewrite_process_assets\zg361\b3e-27b66b3-20260904-063948Z\product-source" `
  --require-r3-identity
```

r4 被确认为 pure performance RED 后，以 **语义修正后的 A** 为输入生成一次性 B。输出路径和 sidecar 必须不存在：

```powershell
py tools/plan_zg361_b3_effect_split_fallback.py `
  --source-root <r4-A-source> `
  --output-root <new-r4-B-source> `
  --manifest <new-r4-B-sidecar.json>
```

不要对 r4 使用 `--require-r3-identity`：语义修正本来就会改变 block hash。规划器仍会要求 effect 名称和用途锚点与 r3 相同，并证明 B 完整继承 A 的新 block 字节和调用图；名称/顺序变化则 fail-closed，先更新用途计划。

物化器还会证明：

1. A source 在操作前后逐文件 hash 不变；
2. B 除三个旧 owner 和 198 个新 shards 外，其余相对路径逐字节等于 A；
3. 三个旧 owner 不再存在，所有声明的 shards 都存在且带 UTF-8 BOM；
4. effect 名、effect block hash、调用图与 A 完全相等；
5. 每个新 shard 为 1–10 effects；整树无 1–10 miss、无超过 20 的例外。

## 同条件实机 A/B 清单

CK3 启动必须继续串行。每个 attempt 使用全新隔离 userdir，禁止复用缓存现场。

固定项：

- CK3 `1.19.0.6` 与 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
- 同一 r4 semantic commit、同一 projection closure、同一 DLC/mod 顺序；
- 同一 native DLL/injector、runner 参数、seed/checkpoint、桌面会话和超时；
- 除三个 owner 被等价 shards 替代外，A/B 文件 hash 清单完全一致；
- 不把 ACK、fixture schema 或静态 GREEN 当作 loader GREEN。

建议顺序是 `A1 → B1 → B2 → A2`，每次独占 CK3 启动资源。每轮冻结：

- projection/materialization manifest 与 B sidecar；
- append-only loader-stage JSONL、loader gate、`error.log`、`game.log`、`debug.log`；
- PID、启动/退出时间、到 lobby/map-ready/native-ready 各阶段耗时；
- runner report、进程退出/回收结果和失败阶段；
- 是否出现 parser/unknown effect/duplicate definition 等产品错误。

判定：

- A 两次同阶段 performance RED，B 两次 GREEN：支持“文件边界导致启动问题”，再把 B 设计落回正式 generators；
- A/B 都 RED 且失败阶段相同：本次边界拆分未解决问题；
- B 出现 parser/缺定义/重复定义：B 是产品 RED，不能作为性能比较；
- 结果不复现或阶段不同：结论为 inconclusive，不声称文件边界是根因。

## 诚实边界与 B 后续

四个 319–478 KB 文件各自只有一个完整 effect。保持 effect body 和调用图完全不变时，它们不能继续按文件边界拆分。`zg361_generated_scoreboard_snapshots.txt` 虽有 480,700 bytes，也已经只有 6 个 definitions；按 1–10 政策它不是违规项。

所以，若本 B 仍是纯性能 RED，下一实验不能继续称为“仅边界拆分”：必须把超大单 effect 抽取为 helper definitions，届时 effect surface 和调用图都会改变，需要新的语义回归与实机证据。

B 若实机 GREEN，正式合并仍需修改 `gen_361_mechanisms.py` 与 `gen_361_b1_runtime.py` 让 shards 成为生成器权威输出，退役三个 monolith，更新 projection/release allowlist 与所有读取旧路径的测试，然后运行 generators `--check`、`validate_local.py`、release reproducibility 和完整 focused/live 验收。一次性 B source 不能直接当正式发布源。

## r5 同条件 A/B 实机证据（2026-09-04）

本节记录预案触发后的冻结结果。A/B 都使用 git `cb02d4c16f7ff86243e063fa97d519ec87553266`、CK3 `1.19.0.6`、EXE SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`、相同 fixture tree
`e2c092a464b53aa3b6161f4f3559ae74e817fe2ecf0327011979c41573eaf5de` 与同一 300 秒 loader-stage 门限。

### 运行树边界隔离

- A projection：565 files / 21,607,125 bytes；tree SHA-256
  `50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f`；projection manifest SHA-256
  `2052dada087a91273a3b15587a34b00c861cca543dbe14926026f3a2ba29b298`。
- B projection：760 files / 21,617,213 bytes；tree SHA-256
  `c071005918b151a41ef1b65cba538d93b2e23da9a7ba5783724d7f39cd485c32`；projection manifest SHA-256
  `7c492bcec9013ab8070935a8f5fe0fc4e0bd4e679f2b22c3cdde873358cdcab4`。
- 两棵投影的 562 个同路径文件逐文件 bytes/SHA 相同，0 个同路径文件发生变化。B 只删除三个冻结 owner，并增加 198 个
  `common/scripted_effects/zg361_ab_b3_*` shards（mechanism 186、B1 12）；文件净增 195，字节净增 10,088，等于 BOM/header 开销。
- B sidecar SHA-256 为 `1534d9b89fd42b2ef225908f924c74306987171d691119c2aa2d8fbd45c19af4`。
  sidecar 证明非目标文件逐字节相同、原 owner 全部缺席、shards 全部存在且有 BOM、每文件 1–10 effects、定义 block 字节与调用图相同。
  definition-surface/call-graph digest 分别为
  `2b3c79d2503941ee1e75e5d111e91db5eae37323478c32e1f9dfe0970ba2fefd` 与
  `ce3e82408378ad70376f066ef12f94cc9d68847fcffe7269378718611e3f5387`。
- 四轮报告都证明运行树 before/after hash 不变；但 loader 未到 runtime mount inventory，因此这里证明的是 runner 实际投影进隔离
  userdir 且参与本轮 database load 的稳定产品树，不把缺失的 post-frontend mount inventory 冒充已验证结果。

### 运行结果与时间线

| 轮次 | artifact | 总时长 | 303 callbacks 首次完成 | callbacks 完成后 quiet | 最后节点 | material pattern | 结果 | report SHA-256 |
|---|---|---:|---:|---:|---|---|---|---|
| A1 | `b3g-fecd2f2-20260904-073033Z/artifacts-live` | 320.080s | 297.264s | 2.675s | `CJominiInGameMusicDatabase` | 0；fatal/theme 0/0 | `loader_stage_timeout` | `65d2cb67b698892fc2ed17d0c8fcf6db3270cc5a3a8e21387e7dcefb3eafa711` |
| B1 | `b3g-fecd2f2-20260904-073033Z-boundary-B/artifacts-live-b1` | 318.838s | 133.034s | 166.813s | `CJominiInGameMusicDatabase` | 0；fatal/theme 0/0 | `loader_stage_timeout` | `33bf29986ebbeefabda16ee3653e0c871dde918be8cac0df6c38be28c87537ea` |
| B2 | `b3g-fecd2f2-20260904-073033Z-boundary-B/artifacts-live-b2` | 321.813s | 125.891s | 173.854s | `CJominiInGameMusicDatabase` | 0；fatal/theme 0/0 | `loader_stage_timeout` | `f5d11f9638a4567da06de1eed72adac85c630b9dc40bf9cc37aa3fd3dfd514f9` |
| A2 | `b3g-fecd2f2-20260904-073033Z/artifacts-live-a2` | 319.338s | 137.788s | 162.083s | `CJominiInGameMusicDatabase` | 0；fatal/theme 0/0 | `loader_stage_timeout` | `c5c971401356821e0c476c9f80ae45d1d1badb22aae9abc7b19fe69c47274bc7` |

辅助 artifact SHA-256：

| 轮次 | cell report | evidence index | loader progress JSONL | loader gate | final error log |
|---|---|---|---|---|---|
| A1 | `4330d75297eecf753ffd0f6d68f19d31d25da6bc3b3611b5f513f584f85c21c2` | `9a8fb5cc719ee2a2cafb325f4c66993d1c5c92ab1ee4faa3e7d3ab9f890affac` | `3b651fa40b1697a3f5b045c0b5181cdd3974843d3dc13ad904f205c975333a4f` | `7d6661769142d7ccff8dbc7da876810cf9db7bbf7de34d7313a3b9856e7d58fc` | `16437dd36e1c91c0fdd25d7c4ea444a1600333cfd35796c53aa75610d87fc458` |
| B1 | `68ce2014b3136855ab0b0efc9fcc8b38d83fd949b7c7459ff45ac5b1a9675fe2` | `fcc25a3ee3d9966a2d70f9e36b50b0f4abbfecf5dc55af7b616a2e03f3103e9c` | `be1ccf95450acd701e0fcd87590495522b9f28437f76088545e8391649cade13` | `a9e19ca954e1415e3a05d424a49d3501a122d97c39365cf0383d5eeedbda5c06` | `9c41e1ff734b19d99b9b4431408009a3d103d0e00a7068ec7e329bed431a4019` |
| B2 | `c9501fea4608214874ce92fdaf6cc8695e3f4e00d959183788ff0d1b183aa2f8` | `7d4dca66f88ea895a2118fd79feec69e8dd267d1f122cca3b30f4004412baebf` | `a7249b5a13d95d4b7f552599bf7f49b838c5b85d6542a324e3be09a009565c6d` | `abe497b094914a4c0fc5a46164d833a2ad61a8470cf490bcf3fc83bd84d97b51` | `c4201b74d284312b9f6971b1eecd7ae14411c4c37acf2eae09829e2ae1e4aded` |
| A2 | `7d094fe9e1435458deac48458c5a10f928c5b27ae60baf29431136fb67b5cc85` | `8504210b332ebf727f75211b6fb549fdf5b45088a2afea51a4956d8b0209878b` | `ee647bffa89f2e00f481b49dcefba1f008d723b143c51b1e4dcde3fcf346ac9c` | `66a89c73f1cf88f8ce578300b54268265c665379d71e59e69f8b91e40d48ed71` | `6ac100fc74fcc36618744a2c83d837c35fdde51d8cd1f3480c4727fe9ef25050` |

A1 到 303 callbacks 用时 `297.264s`，但同一原边界的 A2 只用 `137.788s`，快 `159.476s`（`53.65%`）。A2 与 B1/B2
仅差 `4.754s` / `11.897s`；B 相对 A2 的幅度只有 `3.45%` / `8.63%`，远小于 A 内部两轮差异。ABBA 顺序中只有首轮 A1
接近门限，后续 B1、B2、A2 都在 `125.891–137.788s` 完成 303 callbacks；这与冷启动或运行次序效应一致，不能归因给文件拆分。

A1/B1/B2/A2 的 native cleanup 均为 GREEN，CK3 tree gone、job empty、global process inventory empty 且 protected storage unchanged；
因此四轮时间线不受遗留 CK3 进程跨轮污染。日志中的 `zg361pp.9004.a` localization 诊断是四轮共享的既知 nonblocking 项；
没有 `Unknown effect`、`Unknown trigger`、not-found、direct recursion、parser 或 invalid-effect material pattern。

四轮都在约 300 秒门限结束，都是 303 callbacks、最后节点 `CJominiInGameMusicDatabase`、post-init 0、completion publish absent，
也都没有 Frontend、Load Save/In Game 或 native readiness。最终结论是：本次仅边界拆分既没有解除 terminal RED，也没有产生可从
ABBA 区分于轮次波动的稳定加载收益；实验不支持“文件边界/单文件体量是本次启动问题根因”。一次性 B 不应据此进入正式 generators。

### B2/A2 判定表与实际命中

| B2 | A2 | 判定 |
|---|---|---|
| 同 B1：callback 较早，但同阶段 frontend RED | callback 同样较早，且同阶段 frontend RED | **实际命中**：A1 是首轮离群值；无稳定拆分收益，拆分未解决 terminal，不支持文件边界根因 |
| 重复 B1 的 callback 提前，但仍同阶段 frontend RED | 重复 A1 的 callback 靠近门限 | 拆分的性能收益可复现，但不是当前 terminal RED 的充分修复；保留 B 作为性能候选，继续定位 post-callback/frontend 阻点 |
| 到达 frontend/Load Save/native readiness，且无 material error | 重复 A1 RED | 支持边界拆分是本次启动阻点的有效修复；再把 B 设计落回正式 generators 并做完整静态/live 回归 |
| RED 且出现仅 B 有的 parser、unknown effect、duplicate definition 或调用图错误 | 任意 | B 产品 RED；本组性能比较无效，先修 B 等价性 |
| 与 B1 相反或阶段/树/运行条件不一致 | 任意 | inconclusive；不得声称文件边界是根因 |
| 任意 | A2 到达 frontend/ready | A 本身不稳定；当前 A/B 不能归因，保留四轮 artifact 后另行设计实验 |

最终判定引用了四轮 exact report、projection/sidecar hash 与 callback milestone。总进程时长受固定 timeout 支配，不能单独用作加载性能指标；
下一项调查应针对共同的 post-callback/frontend terminal 缺失，而不是继续扩大 boundary-only 拆分。
