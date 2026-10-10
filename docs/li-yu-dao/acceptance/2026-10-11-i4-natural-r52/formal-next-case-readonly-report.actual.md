# B4/B5/C3 下一最小公共 case：只读依赖结论

本轮只读源码、小型输入和路径元数据。R52/a14 正在运行，不取其现场状态，不执行公共工具、测试、Git、PE、存档正文读取或 seed hash。以下不增加正式业务或 native 信用。

**现成最小正式 case 是 `li-yu-dao / i3b-formal-b4`，但现在尚不具备值得重新实机执行的生产修复/判别输入；O11 另缺它必需的 G2 公共注册。B5/C3 既没有合格前置 B4 seed，也没有已注册的公共产品 case。**

## B4：输入实际存在，守卫与执行已实现

[公共合同](C:/workspace/ck3_eternal_recurrence/docs/li-yu-dao/i3b-public-formal-b4.md)、[adapter](C:/workspace/ck3_eternal_recurrence/tools/ck3_mod_acceptance_cases/lyd_i3b_formal_adapter.py:73)、[case 数据](C:/workspace/ck3_eternal_recurrence/tools/ck3_mod_acceptance_cases/lyd_i3b_formal_b4.json:56)固定以下输入：

- 合法 R29 B3 已签署 seed：`C:/workspace/ck3_lyd_runtime_20261004/live-attempt-029/checkpoints/B3-signed-precommit-r3-signed/checkpoint.ck3`，91,709,349B，原 SHA `c8601e7ba08406a551dcddd2a19e454423db2be6b559fad9985c6d1121b537c9`。本次仅确认存在和大小，未读正文或重新核 SHA。
- 原正式71文件：`live-attempt-038/content/production`，以现存 `C:/workspace/ck3-common-runtime/cases/lyd-transaction-control-20261010-001/product-inventory.json` 固定 source06159。四项配置仍取既有显式输入；无诊断 overlay。
- 原签署资格30387B/`93ba24f0…3083`、保护基线426067B/`e08d6f60…4323`、reader request164563B/`899b3ee2…fcdb`；完整实际路径和原 pins 在 [现存输入](C:/workspace/ck3_lyd_runtime_20261004/r48-formal-i3b-public-case-sourceonly-20261010-001/prepare-inputs.candidate.json)。三文件及产品 inventory 本次均存在且大小与声明相符，未借此重新授予历史资格。
- 当场必须仍是 actor/root31254、Faith107/Rite169、日期53144712、暂停、`lyd.430` instance119、serial3/nonce6/phase2、选项 `[0,2,3]`。历史证书只证明来源；新冷载前置仍须自己观测。

[执行实现](C:/workspace/ck3_eternal_recurrence/tools/ck3_mod_acceptance_cases/lyd_i3b_formal_adapter.py:309)已完成：新 B3 SAVE→同帧 G2/G3→87保护/完整有序45 native-saved join；唯一 option1 提交→真实新431→后置 cache→新 B4 SAVE/G3/88保护。后置名单改变仍保全 B4 保存与保护结果。B3/B4 新正文各读一次，旧签署正文不重读；未知 ACK 不重放。结果明确只授 B4，B5/C3/product false。

公共现有命令形状是 `tools/ck3_mod_acceptance.py prepare --runtime ACTUAL --products tools/ck3_mod_acceptance_products.json --product li-yu-dao --case i3b-formal-b4 --case-inputs ACTUAL --prepare-output FRESH`，随后既有 plan/preflight/allocate/run/verify。下个 CASE、实际 runtime 和输入派生尚未建立；本包没有提供可误执行的预授 argv。

## 当前具体阻点

1. [registry2659/2691](C:/workspace/ck3_eternal_recurrence/tools/ck3_mod_acceptance_products.json:2659)要求 `ck3_query_confucian_assembly_predicates_v1`；O11 `manifest.json` 的13项能力没有它。更关键的是实际 `C:/csr11/ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py` 没有该函数注册；不能只补 metadata。MAIN [mcp_server1345–1352](C:/workspace/ck3_eternal_recurrence/ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py:1345)已在原 readonly opt-in 下实现，未来共同来源需要明确投影这项实际差异，保留 source/index/host/native 绑定。当前 O11 不改写，也没有证明需要新增 native 构建。
2. [R49 进度](C:/workspace/ck3_eternal_recurrence/docs/li-yu-dao/2026-10-10-progress.md)已实际观察 holder/resolve 后45→40且保存一致；[当前专题](C:/workspace/ck3_eternal_recurrence/docs/ck3-native-ai/li-yu-dao-resolve-cache-12004.md:9)明确 writer、resolve 与脚本 getter lazy refresh 因果仍 UNKNOWN，尚无采用的生产修复。五政治 Title full AST 与 actor succession 的保护保持原要求。B4 contract 自身也写明：没有新判别/修复不重复相同 factory。下一执行输入必须先指出实际改变了什么、要区分哪一尚未知原因，不能把 R47 空事务或 R49 诊断通过当作修复。

## B5：最小缺口是公共只读冷载 case 和真正 B4 PASS 输入

现存 [B5 输入合同](C:/workspace/ck3_lyd_runtime_20261004/r48-formal-i3b-public-case-sourceonly-20261010-001/B5-NEXT-INPUT-CONTRACT.unbound.json)明确 `executable_B5_case_implemented:false`；当前 LYD registry 无 B5 case。[B4结果](C:/workspace/ck3_eternal_recurrence/tools/ck3_mod_acceptance_cases/lyd_i3b_formal_adapter.py:365)也不冒授 B5。

后继最小工作可以是独立 saved-campaign/零 factory 操作的 B5 adapter，未来输入保持 NULL：实际 B4 PASS verify+精确后置 checkpoint+动态新 T+原正常关闭与释放。冷载重新核 Faith107/T holder31254、四属性/law95、45有序缓存、原88保护及新 SAVE 的 native-saved join。失败 B4 保存和 D2a/空事务保存均不能作为这个输入。是否冷载仍破坏状态目前没有合格 B4 前驱可测试，不预写根因。

## C3：底层全集合已实现，当前公共来源与产品场景仍缺

旧 [10月6日交接155](C:/workspace/ck3_eternal_recurrence/docs/handover/2026-10-06-li-yu-dao-vacation-handover.md:155)的“完整graph/profile24待实现”已被后续专题更正；[公共 G4 合同](C:/workspace/ck3_eternal_recurrence/docs/ck3-native-ai/2026-10-10-common-challenger-graph-readonly.md)和 MAIN [MCP1360](C:/workspace/ck3_eternal_recurrence/ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py:1360)已有完整 provider 的公共路由，参数仅实际 `expected_revision` 与1–8个 `faith_full_ids`。

O11 没有 `confucian_challenger_readonly` feature/G4 capability，实际 Csr11 MCP server 也没有 G4 注册。虽然所选 host 含对应 flag 字符串，这不足以使公共工具存在。未来按现有全局 opt-in 投影必要 Python/source 声明及精确 native 来源，产品不得自选 host policy。LYD registry 当前无 C3 case；现有 G4 源码不能替代正式挑战生命周期 adapter。

实际 nextinput 必须来自 B4+B5 同一个通过的新 T：把该真实 T 合法授给同 Faith NPC65865，证明其真实独立在任身份，再取完整非空 challenger/sponsor 集合和独立 saved owner-Faith join；保 HoR169、政治7 full AST 和人物身份，走真实挑战及拒绝/撤回/死亡清理/重载。NPC资格、动态 T、当前窗口/选项与图集合全部仍需实际输入，不预填18373或旧 event instance。旧失败 B4 世界不得成为通过 seed。

当前最小顺序仍是解决可判别的 factory 保护原因→现有公共 B4→独立 B5 冷载→C3。I4/R52 可以独立运行，不改变这些依赖。本包来源与小元数据按现有期限管理，不延续旧运行树或缓存 TTL；不依赖不存在的 `ck3-upgrade-20261008`。
