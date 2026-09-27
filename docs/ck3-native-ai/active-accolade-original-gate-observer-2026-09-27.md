# 现役称号来源门：原调用边界与受管观察合同（2026-09-27）

适用 CK3 `1.19.0.6`，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。只读 [`verify_active_accolade_original_call_boundary.py`](../../ck3_autonomous_player/native_bridge/research/verify_active_accolade_original_call_boundary.py) 复核既有 all-row gate 证据、四个函数入口的完整非相对指令、各自 `.pdata` owner、四条 `E8 rel32` 调用及精确返回地址；[冻结夹具](../../ck3_autonomous_player/native_bridge/research/fixtures/active_accolade_original_call_boundary_11906.json) SHA-256 `D8D680810CD8E9EB2F5875180011DE7CE73E121100928531CB45F6E6E6EE3B03`。本轮只做静态核验，未启动 CK3，也未在暂停帧调用原版 helper。

`0x2308D50` 在 `0x2308D66`、`0x2308D72` 依序调用两侧的 `0x23CBCE0`。后者按 `side+0x40/count+0x4C` 的 `0x60` stride MAA entry 遍历，只有通过骑士角色、称号链接和称号有效性门后，才在 `0x23CBEA3` 调 `0x251B8F0(accolade, side+0x110)`。`0x251B8F0` 在 `0x251B900` 调 `0x251C200(accolade)`；原函数逐个检查 `Accolade+0x58/count+0x64` 的 row `+0x10` 来源指针和来源对象 vtable `+0x00`，最终在 `AL` 返回**整组**通过与否。返回 false 时 `0x251B907` 跳过整组 modifier 追加。因此在原函数自然调用时，入口/出口 hook 可观察准确的 all-row 布尔结果，不需要暂停帧重调。

受管 typed trace 的最小安全合同：默认关闭，仅已哈希准入的显式 private trace 开启；在暂停且线程静止时装入预分配的 15/16 字节入口 detour，逐字节比对后才 patch，finish/RED 均恢复原字节。`cache` hook 确认 CombatID、日期与原调用 token，`refresh` hook 只接受上述两条 caller RVA、同一 Combat side 和原顺序；`gate` hook 只接受 `0x251B905` 返回地址及 refresh TLS，并先/后复核 Accolade full ID、`+0x58/+0x64` 行数组头，再调用**一次** trampoline。回执记录 materialization ordinal、side、Accolade full ID、原 gate bool、row count 和失败状态；固定容量溢出或任何 caller、线程、身份、数组头不一致时 fail closed，保留原游戏调用继续执行，绝不追加自造值。

**边界限制**：`0x251C200` 的返回值只有整组 bool，失效行索引和“空指针或虚函数 false”的具体分类没有返回；不得从调用后的 row 内存倒推失败时点。`0x251B8F0` 的 ABI 只收 Accolade 与 side aggregator，原 refresh 当前 `RSI` entry 指针并未作为参数传入；若同一 side 的多个 MAA entry 链到同一 Accolade，仅凭这个函数入口无法认定是哪一个槽位。可将现役全槽位 `knight_character_id_raw`/`accolade_id_raw` 与 trace 中同一 CombatID、日期、side、AccoladeID 作候选 join；唯一时标 `unique_candidate`，多个时标 `ambiguous_multiple_slots`，前后帧不同或无候选时保持 `unbound`。这一步不能把回读帧的空槽/链接当成原调用时的冻结输入，更不能把原 gate bool 充作下一日先验常数。

本页冻结的是可观察边界和拒绝语义；在 trace hook、wire 标准化、静态编译和受管实机对拍完成前，`accolade_source.source_gate_status` 继续为 `unknown_original_call_not_observed`。同日 fresh-load 优势/有效伤害差异见[独立对照](active-battle-fresh-load-frame-divergence-2026-09-27.md)，仍不能直接归因于称号。
