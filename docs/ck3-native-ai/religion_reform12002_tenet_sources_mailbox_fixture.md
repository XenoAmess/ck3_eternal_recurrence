# CK3 1.20.0.2 Tenet 来源查询的完整队列包

2026-10-01 的新验收为 **static-ready actual query wrapper**。一次 `/O2 /W4 /WX` 运行通过 7 个检查、1 个场景，生成 1 份实际 C++ `command_result`。尚未验证中央专用命名槽，也不把此夹具记为 paused live 或宗教操作能力。

版本锁定为 CK3 1.20.0.2 Crozier，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。原生调用树及提供器边界见 [Tenet 来源专题](religion_reform12002_tenet_sources.md)。本页只记录已冻结提供器之后新增的队列/返回包施工。

| 层 | 实际入口 |
| --- | --- |
| 私有 selector | `query-player-religion-draft-tenet-choices-v1` |
| domain | `player_religion_draft_tenet_choices_v1` |
| backend | `ck3-1.20.0.2-native-player-religion-draft-tenet-choices-v1` |
| DTO | `result.player_religion_draft_tenet_choices`，schema `ck3_12002_current_draft_tenet_sources_v1` |
| 构建 flag | `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1` |

## 实际输入与新增验证

新 `religion_reform12002_tenet_sources_mailbox_test.cpp` 复用冻结 `religion_reform12002_tenet_sources_test.cpp` 的真实内存布局 `Fixture`、`Bind` 及 native stub helpers；旧 8 场景 `main` 被重命名，运行计数为零。原提供器的 4 个已通过 O2 object 直接复用，没有重跑原场景。

唯一新场景保留原提供器的第一组输入：真实 DB `+EF0/+EFC` 有 8 个来源指针，真实草案 `+778` 有 2 个 `0x70` 字节槽，其原生槽 ID 为 7 和 11；现有 category 为窗口 `+888`，TopScope 为 `+D0`。source Faith 的 main Rite 与 actor Faith 使用不同对象，stub 逐次检查实际参数。提供器实际执行 source filter、raw status、knowledge、shown 和 selectable trigger，复制 Tenet 定义 key，形成完整 DTO。

新验证路径是 worker `TrySubmit` → fixture owning thread `ObserveMainThreadPumpAndDrainV1` → `EnterQueryMailbox` → 实际 `ReadCurrentDraftTenetSources12002` 与 key copier → `FinishQueryMailbox` → worker `Wait/Reclaim` → 实际 `SerializePlayerReligionDraftTenetChoicesResult12002`。队列终态回到 `idle`，published frame 前后均由 owner 读取，捕获 epoch 等于实际 pump epoch，线程 ID 等于 owner。

原生 helpers 在夹具中使用受检查的 stub；实际 native observer、队列、字符串复制器和序列化器使用生产源码。没有手填 DTO，没有给 JSON 添加 caller metadata，也没有构造 GUI item、类别窗口或宗教 command。通用 `permitted_executor` 只许可此实际 callback；它证明新库路径可用，专用 `permitted_executor_religion_draft_tenet_choices12002` 的中央安装仍需单独验证。

完整包经过 JSON 解码后，除由本次实际 owning pump 产生的 `capture_epoch`，其 DTO 所有字段与冻结提供器已有的第一份实际 JSON 一致。包保留原生的过滤结果与最终 gate：已选重复条目可以 `native_can_pick=true` 而 `final_selectable=false`；raw status 为零的来源分别呈现有知识与无知识结果；shown 或 selectable trigger 拒绝仍独立可见。

## 与当前实机观察的关系

协调者已经记录 R7 实机草案的 29 个 selected slots，以及只点击 Communion Tenet 后右侧实际列表为空的样本：

- `artifacts/g2-offline-2026-10-01/targeted-sdk-r7/r7-draft-groups-readonly-20261001T122903Z`
- `artifacts/g2-offline-2026-10-01/targeted-sdk-r7/r7-draft-groups-readonly-20261001T123302Z`：`current_category_slot=1`、`doctrine_marriage_type`、`doctrine_monogamy`，Doctrine cache 3，当前 Tenet cache 0、choices `[]`。

这些是已有 R7 现场背景，不是本查询的 live 证明；此页不推断空列表原因。新查询从实际全局 DB 来源集合与 `14F2030` filter 取得来源及其可实例化结果，不用当前 popup cache 的零行数替代全局来源计数。实际 DB 的合法零 count 已由原提供器夹具闭合，本次不重复该验证。

## 冻结证据与复现

新增证明：[attempt-001/result.json](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-reform/query-tenet-sources-mailbox/attempt-001/result.json)，SHA-256 `0ca9b6505d609d9265d852fb4c888f5c18d13613b9c895740e6f3222d5cd2a7a`。其中列出所有编译输入、复用 object、flag、编译日志、运行日志及包哈希。

唯一原包：[wire/actual-multiple-sources.json](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-reform/query-tenet-sources-mailbox/attempt-001/wire/actual-multiple-sources.json)，SHA-256 `9f0adadd05c0b94a5b32043efc6ba5bb7f9fca32fe1664899f3fc68b32ba0a86`。Python 层可直接复制这些字节并通过 production `NativeProtocolState` 消费，不能重新拼包。snapshot revision 为 701，原包 request ID 包含引号，以覆盖实际序列化转义。

冻结提供器已有结果为 `religion-reform/tenet-sources/fixture/result.json`，SHA-256 `d03f92110b50e27f014b07de86067a7082b37584f383a75a141c4d5899b94eed`；其第一份原生 DTO SHA-256 为 `22b05a73fec5e09b5659a46185fb4cd8a2fdf48d8740f9da13ced4334e759348`。

必要时复现新场景，输出必须使用新的 artifact 目录：

```powershell
& Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\religion_reform12002_tenet_sources_mailbox_tests.py --artifacts <new-attempt> --provider-objects Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\tenet-sources\fixture
```

日/周报告字段：2026-10-01 / 2026-W40；完成了 all-source Tenet observer 的实际只读队列及完整返回包，以解除“仅当前缓存可观测”的输入缺口。readiness 为 static-ready，无本轮 RED；旧提供器矩阵未重复、未操作 CK3、未操作 Git。下一项由中央集成专用 named slot、Python/官方 SDK 单例，再由协调者进行 paused 实机等价性验收。未交付选择、创建、编辑或宗教 OODA。commit/push 由 root 统一执行。
