# CK3 1.20.0.2 草案分组查询：实际 caller 夹具

状态：**static-ready query wrapper**。新增入口为 `query-player-religion-draft-groups-v1`，
domain key 为 `player_religion_draft_groups_v1`，结果位于 `result.player_religion_draft_groups`。
这里验证新 group model 的实际 worker / owning mailbox / complete protocol 通道，不执行宗教动作。

新 test 只读 include 冻结的 [原 caller 夹具](religion-reform12002-query-caller-fixture.md) 的 backing、
frame adapter 与 owning-pump helpers，将原 main 重命名后不调用。
新 backing 使用实际 selected slot array `window+0x790`、stride `0x48`，
每个 selected definition 的 group pointer 为 `+0xB08`，组的来源数组位于 `+0x140`、count `+0x14C`。
两组分别保留 `doctrine_a/b` 和 `doctrine_c/d` 的真实来源；
当前 category 的 owner、slot、doctrine cache、Tenet source cache 与 materialized Tenet status groups 也来自 backing 内存。
该来源集合不是已 materialized 的合法候选列表，不使用 registry 替代 choices。

实际调用流程为 worker `RunPlayerReligionDraftGroupsMailbox12002` → `TrySubmit` →
owner `ObserveMainThreadPumpAndDrainV1` → actual group reader → `Finish` →
`Wait/Reclaim` → native complete `command_result` → Python JSON 验证。
结果具备原生输出的 `protocol_version:1`、request ID 转义、accepted/private/read-only/advertised metadata 和 exact-build provenance；
夹具不补 metadata 或供给成功 DTO。`capture_epoch` 来自 pump，`snapshot_revision:701` 来自 published frame。

| 实际 wire | 结果 |
| --- | --- |
| `visible-multi-slots.json` | 两个 stride-48 selected slots，各自 group source 独立；当前 category slot 0 / group_a，三项 cache count 都为 1；实际 Tenet helper 返回 true |
| `absent-window.json` | 合法没有窗口，observed / available=true，draft=false，rows=[]，current Rite null |
| `hidden-window.json` | 缓存窗口不可见，draft=false，rows=[]，不调用 draft/Tenet helper |
| `known-empty.json` | 可见窗口真实 selected slots 与 cache 全为 0，draft=true，category slot=-1，current category未 materialized |

`all_group_materialized_choices_complete:false` 保持诚实边界。
`current_tenet_gate_complete` 只对应当前实际 materialized category，不表示全组候选已生成或可执行改革。
当前 sources/cache 查询具有独立观测价值；本通道不打开窗口、构造 popup、生成候选或提交动作。

MSVC `/O2 /W4 /WX` 首轮 **4 cases / 21 checks GREEN**；
artifact 为 `Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\query-group-mailbox\attempt-001`。
`result.json` SHA-256：`cd0b7dbe940b44d36f26104c81939bc1db4b747eb388a33ceed5dcee4eab8061`。
该目录 `wire/` 包含四条原始 complete command_result；Python/MCP 只可替换请求 nonce，不能补字段。
完整 source、dependency object 来源与 SHA、defines 记录在 receipt。

本夹具使用 existing `permitted_executor` 配置 exact typed group callback，证明实际 queue。
生产 dedicated named-slot 注册属于中央后续接线，本报告没有声称该注册已验收。
原 query 8 文件、named 3 文件与 stride / getter 矩阵均未修改或重新执行；复用冻结 `/O2` 库对象，
仅编译新 model/mailbox 与需要当前 layout 的 shared/core context 实现。
没有 CK3、pipe、Steam、UI、战争研究或 Git 操作，不声称 fixture-live 或 production-live。
