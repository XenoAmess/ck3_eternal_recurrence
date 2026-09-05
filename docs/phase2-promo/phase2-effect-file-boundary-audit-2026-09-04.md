# 天朝二期 effect 文件边界审计（2026-09-04）

## 2026-09-05 现行结论（取代下方旧白名单政策）

项目已把单文件过大强制视为文件边界缺陷，不再等待性能 RED，也不再讨论是否拆分。四个旧兼容 owner 已全部从 canonical source 退役：

- 361 mechanism：`1,449` 个 effect 拆为 `186` 个用途文件，每文件 `1–8`；
- B1 runtime：`78` 个 effect 拆为 `12` 个用途文件，每文件 `3–10`；
- Phase2 core：`26` 个 effect 拆为 `4` 个用途文件，分别为 `3 / 6 / 8 / 9`；
- 当前全树：`626 files / 3721 effects / maximum 10 / target misses 0 / >20 violations 0 / exceptions 0`。

生成器、读取方、production closure 与静态门均已切换到用途分片；旧 owner 不得与新分片并存。新 canonical 布局当前为 `static-ready / live-pending`，下一次 CK3 验收只能使用拆分版本。权威现行合同见
[`mod_zhongguo_style/docs/361-effect-file-boundary-contract.md`](../../mod_zhongguo_style/docs/361-effect-file-boundary-contract.md)。下文保留 2026-09-04 的历史快照和实机 artifact，不再授权任何 legacy 白名单。

### R79 产品投影门禁

`phase2-b3-production-closure-r79-f953503` 的 closure expander 会在计算固定点前强制退休候选中的 mechanism/B1 历史 owner，安装 canonical `186 + 12` 个用途 shard，并继续安装四个 core shard。runner 预检只读取 core shard，发现旧 `zg361_effects.txt` 或任一 shard 缺失即 RED。

对 `Z:\p2ag\p\common\scripted_effects` 的深度感知扫描结果为 `618 files / 3708 effects / maximum 10 / target misses 0 / >20 violations 0 / legacy owners 0`；closure `3708 effects / 988 events / 24 triggers / missing 0`。closure expansion / product manifest SHA-256 为 `1188760A606A3ECB1E9C8734B00C0E9BC150601158B072DF7DFACF093A6AC6F0` / `B667EB5BCC7FA2B677E529F42E597A5932ECFAF23A6316C23DF2B14C400A69E3`。静态门与 no-launch acceptance preflight 均 GREEN；实机状态仍待 R79。

状态：**GREEN / static-only / no CK3 launch**。审计基线为 canonical commit
`75c1432a46b5fc3f442de61711bbbff9973aa307`，范围是
`mod_zhongguo_style/common/scripted_effects/*.txt`。政策口径保持为：B2 起按用途分组，目标每文件 `1–10`
个顶层 effect，原则上不得超过 `20`；B2 以前的兼容 owner 只能由显式白名单继承，不能用改名或新增白名单消除 RED。

## 结论

运行：

```powershell
py mod_zhongguo_style/tools/effect_file_boundaries.py
```

得到：

```text
GREEN: 427 files / 3719 effects; target misses=0; >20 violations=0; max non-legacy=10
```

| 分类 | 文件 | 顶层 effect | `>10` | `>20` | 最大值 |
|---|---:|---:|---:|---:|---:|
| B2+ / 非遗留 | 423 | 2,167 | **0** | **0** | 10 |
| B1 及更早的显式兼容 owner | 4 | 1,552 | 4 | 4 | 1,449 |
| 合计 | 427 | 3,719 | 4 | 4 | 1,449 |

因此本轮需要枚举的 **B2+ `>10` 集合为空，B2+ `>20` 集合也为空**。没有新增例外、没有需要拆分的
B2+ 文件，也没有改动 canonical effect 正文或生成器。

按来源标记统计，425 个生成文件包含 3,688 个 effect，其中超过 10/20 的只有下表三个 pre-B2 owner；两个手写文件
包含 31 个 effect，其中只有下表的 `zg361_effects.txt` 超限。产品 effect 目录中没有 `test`、`selftest`、`fixture`
或 `acceptance` 文件；边界审计器及其临时测试夹具位于 `mod_zhongguo_style/tools/`，不计入产品定义数。

## 四个 grandfathered owner

| 文件 | 定义 / bytes | SHA-256 | 分类与保留理由 | 实机证据及边界 |
|---|---:|---|---|---|
| `zg361_b1_runtime_effects.txt` | 41 / 255,586 | `7E373996A4789F64DF5BDB85448F01494A63902ABC883DF2731DC8318F966247` | `gen_361_b1_runtime.py` 生成的 B1 兼容 owner；正式 B1 从旧 77-effect 单体做过语义保持的 41+36 拆分，B2+ 不再向它追加定义。 | 该精确文件随 B3 explicit-AND 产品实机加载并于 `125.965s` 到达 Frontend；见下方统一证据。整体验收后来因未进入 Load Save/In Game 为 RED，不能冒充 gameplay GREEN。 |
| `zg361_b1_runtime_effects_part2.txt` | 36 / 240,700 | `1F2D76436DE74FB37698103F90ADC029BAC2AC16DD75B29E98D428E3E33F663C` | 同一 B1 生成器的第二兼容 owner；41+36 分界保持旧正文顺序与 B1 ABI，且不对 B2+ 开放扩张。 | 与上一文件同一精确 Frontend 实机证据。 |
| `zg361_generated_mechanism_effects.txt` | 1,449 / 1,019,397 | `9E0479B33B322C3D51921180B5A4C34ADC13BB9CEA9F0F7A70D577A945EDD052` | B2 前即存在的机械化 361 机制 dispatcher，由 `zg361_mechanism_data.py` / `mechanism_choices/*.json` 生成；当前 B2/B3 投影只逐字节继承，不把新业务 effect 塞入该文件。 | 与上述 B1 文件同一精确 Frontend 实机证据。该结果也说明“文件很大”本身不是此轮 B3 Frontend 阻点的充分原因。 |
| `zg361_effects.txt` | 26 / 63,804 | `DEF1DB5FDCE8D310A2ABBA35BF9864BCFD5F2664474322356D30483C74ACF3E4` | 手写的 pre-B2 核心兼容源。它仍留在 canonical 开发/完整 release 树供旧入口兼容，但 Phase2 production projection 会移除该单体，按用途改挂 9/8/6/3 个定义的四个 `zg361_core_*_effects.txt`，所以 live Phase2 产品中不存在这个 `>20` 例外。 | 精确 monolith 在 2026-09-02 实机冻结清单中出现，并走到 `database_init` 后 timeout（0 fatal），只算 RED 暴露证据；当前 B3 Frontend 实机改载四个用途分片而没有该 monolith。不得把前者写成 monolith GREEN，也不得把后者写成正文语义重验。 |

四个文件都具备明确的 pre-B2 来源、当前哈希和实机边界记录；其中前三个是当前 live projection 的真实继承例外，第四个
只存在于 canonical source/release 树，Phase2 product 已通过用途分片消除超限。这个白名单不授权新的 B2+ 文件超过 20，
也不表示未来无需继续迁移 legacy owner。

## 实机证据绑定

当前三个 live `>20` owner 的精确副本位于：

`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\artifacts-live_native_state\profile\mod-content\zhongguo_361\common\scripted_effects`

对应冻结 artifact 根：

`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\artifacts-live`

- 303 callbacks `123.801s`，Frontend `125.965s`；zero-argument provider、unknown trigger、unknown effect、parser error 均为 0。
- outer report SHA-256：`F0ABC5F24505019061B986DB8992CA0DDD95C0D584C6C9F24B5D4BF6BB9B9B70`。
- evidence index SHA-256：`A6049D099759571921A5E81A0634517E25C91E5A0452AABA0D583041F6BFCE5F`。
- cell report SHA-256：`9A9AE5C6F52AAB6FC99F6D44D918C9556A8C43BCEF25C430583097D8846B9E17`。
- 整体结果仍是 `save_resume_red / frontend_without_load_save`；这里引用它仅证明精确文件已过 loader/Frontend，不提升业务状态。

同一 live product 为 420 个 effect 文件 / 3,698 个定义，三个继承文件是唯一 `>10` 和 `>20` 项；其余文件最大 10。
`zg361_effects.txt` 不在该 product 中，替代它的四片为：

| 用途片 | 定义 | SHA-256 |
|---|---:|---|
| `zg361_core_review_cycle_effects.txt` | 9 | `9C2EE4CBF01E712EA8CB124C54EB03F7C31DD6921D458A4B932697E7A89756D6` |
| `zg361_core_result_delivery_effects.txt` | 8 | `A1C287E080309ECD763C278620FBA95FFF1AA7AC31524E53B7382A94663E06C7` |
| `zg361_core_elimination_effects.txt` | 6 | `387C6290D83A9E4D921698AFE32192F0CDA9EFACF58B64B49075EDB4CA026D0B` |
| `zg361_core_appeal_scoreboard_effects.txt` | 3 | `181E722CD087877BE18155B7DD029E4A11EA644D43966D4CC0D0170578DAB45A` |

精确 canonical `zg361_effects.txt` 的历史 live 暴露由
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-shell-gate-20260902\artifacts4-live\source-tree-manifest.after.json`
绑定：manifest SHA-256 `BD5F8CEE6834FD29EB726526AE9CC3A2C52D80E2BEAE62DB81BC03F6A8C21323`；同轮
`runner-report.json` SHA-256 `3549502304DD58AB39AE553B546F6A5331CD1778F03027C71B03BA04C7D3A0C8`，终态为
`RED / loader_stage_timeout / database_init / 299.962s / fatal_error_count=0`。

## 后续规则

- 新增或重命名的 B2+ 文件默认进入 `<=20` 门禁；目标仍为 `1–10`，不因现有四个白名单降级。
- 加载性能 RED 只有在材料/闭包错误归零后才触发同条件文件边界 A/B；现有 ABBA 已否定“单文件体量是 B3 故障根因”的说法。
- 本审计没有发现真实代码或测试缺口，所以只补证据台账；没有签发候选，也没有启动 CK3。

静态复核：`test_effect_file_boundaries.py` 4/4 GREEN；普通与 `python -O` 边界审计均为上述 427/3,719 GREEN；
`validate_local.py` GREEN。
