# B3 纯加载性能 RED 的 effect 文件边界 A/B 预案

## 状态与使用门槛

本预案是 **no-launch、未物化** 的 fallback。取证基线是：

- r3 artifact：`Z:\ck3_mod_rewrite_process_assets\zg361\b3e-27b66b3-20260904-063948Z`
- source：上述目录的 `product-source/`
- source commit 标签：`27b66b3`
- `projection.json` SHA-256：`b769ca3e36e42cb30ae667b91b7f7b54b7648b5ab3c0f28144b18a4c82d9c0ad`

只有 r4 已完成语义修正、静态与原生门禁均 GREEN，且余下 RED 被归因为纯加载性能时，才执行 B。语法错误、unknown effect、缺文件、错误 mod 顺序、native 注入失败、fixture 或 runner RED 都不属于这个门槛。

本次没有生成 B 产品树，没有启动 CK3，也没有把“文件过大”写成既定根因。当前结论只是：文件边界仍是一个值得用严格同条件 A/B 隔离的候选变量。

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
