# HolySite 原生只读口与后续原版采用入口

本轮先补到现有游玩智能体：`ck3_query_player_holy_site_v1(expected_revision, holy_site_id=null)`。省略 ID 时读取原生 HolySiteWindow 当前选中对象；显式 ID 按完整 uint32 reference 解析。当前 Faith 的全部站点、已加载 registry 类型索引也同时返回，智能体可先定位 `nadjaf` 等 source key，再用本轮实际 ID 查询。registry 不是原版采用候选列表。

当前资格为 **native fixture + 真实 MCP 协议通过，live pending**。没有在游戏里执行开窗、采用、供奉或移除；不能用本页推断某个存档的合法性或视频已拍成。

## 生产链与准入

`mcp_server.create_server` → `NativeHeadlessGameplayDriver.query_player_holy_site_private_v1` → 现有 G2 `execute_step/query-player-holy-site-v1` → 现有宗教 `ExecutePlayerReligionMailbox12002` → exact4 reader/serializer → 同一生产 MCP 返回。

复用原 owner mailbox 的 paused map、GetPlayer 角色、TLS/epoch、前后 snapshot 检查；此专口在基本宗教 context 后返回，不触发旧 context 的 13 个无关 addon。历史人物 ID 不作运行时完整 ID，正常战役守卫保持。

部署沿用 `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1`；独立 MCP CLI 显式加 `--private-player-holy-site-query`。公共 `tools/ck3_mod_acceptance.py` case 使用：

```json
{"required_mcp_tools":["ck3_query_player_holy_site_v1"],
 "opt_in_read_only_mcp_tools":["ck3_query_player_holy_site_v1"]}
```

公共 shared host 的 `--case-read-only-mcp-tool` choices、driver permission 与该 allowlist 均已接入，默认关闭。`ck3_inspect_gui_window_tree_v1(window_kind="holy_site")` 复用原生树观察，root 为 `holy_site_window`。

## 已闭合的 exact4 模型

EXE SHA-256：`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。

| 原生源 | 读取语义 |
|---|---|
| HolySite storage `0x5D1DE80`，对象 `+0x10` | 完整 ID；索引 `id & 0xFFFFFF` 后仍核对 generation |
| registered GetType `0x855A40` | site `+0x20` 类型，definition `+0x18` 原生字符串 key，`+0x38` magic |
| registered GetFaiths `0xD68090` 与 save/load 消费者 | site `+0x98` uint32 数组，保留顺序与重复 |
| Faith storage `0x5D1E300`，ID `+8` | 每个关联 Faith 单独解析 |
| IsHolySite / IsEminentHolySite | Faith `+0x890` / `+0x8A8` 两个独立 ID 集合；逐 Faith 返回 membership 和 eminent Boolean，不伪造等级枚举 |
| GetBarony `0x2658A30` | site `+0xB0` 完整 title ID |
| GetInventory `0xBB6C50` | site `+0x28` 内嵌对象，没有独立 inventory ID |
| Inventory.GetArtifacts `0x22E6B60` | inventory `+0x58` uint32 artifact ID 数组，保留 generation、顺序与重复 |
| 原生 inventory owner 分支 | `+0x3C` HolySite owner 优先，`+0x38` Character owner；分别读回，不把容器身份冒充 owner 字段赋值 |
| HolySiteWindow `handler+0x5D8` | primary vtable `0x4592338`、owner backlink、root `+0x60`、已选 HolySite fullID `+0xC8`；`+0xCC` 仅 raw item |

所有数组与完整 ID 在 callback 内重读；来源不可读分别报告 unavailable，不能当成 false 或空集合。window model 中保留旧选择不证明画面可见。`Active`、圣物认可、受益范围、artifact 对象详情以及采用合法性均明确 `observed=false`；未观察的值不能参与肯定决策。

## 后续原版 GUI 路线

原版 `gui/window_holy_site.gui` SHA `23542c54dd73b0c349e008649f201b1459ef833070fb6071e089dcd210642fb2` 的 L612、L617–618 在按钮回调里创建 `MakeDecisionTypeWithParam('adopt_holy_site_decision','selected_item',HolySite.MakeScope)`，再打开 `decision_detail` 并关闭站点窗。隐藏决议不能假定会出现在普通 keyed 决议列表。

原版 typed open 已静态闭合：Any 工厂 `0xD55AD0`，40-byte Any 的 inline DWORD 保存完整 ID，`OpenViewData 0xAF39E0(handler, 0xA8, &any)`；拷贝/析构生命周期已追到原生消费者。开窗前必须实际存在并验证 handler 中原版 window；随后另读 native root 可见性和选中 fullID。本页没有给这个尚未集成/实机验收的动作授予资格。

无名采用按钮不能猜 ordinal 或选第一按钮。现有 generic callback descriptor 观察器可按 `OpenGameViewData → HolySiteWindow.Close` 有序对、唯一可见启用控件与原版 Adopt/其他三个互斥可见谓词绑定。实际 descriptor、原版参数化 detail、合法性、最终单次提交及成本/Faith 集合变化仍须现场独立读回。

## 本机验证与证据

`machine_id: 4-8e1c2f1861`；观察时间为 2026-10-17 UTC，准确时间在下面机器可读原件。源码审查/构建/协议 fixture 均为此机事实，不能外推其他机器部署或游戏结果。

- Native increment03：真实编译 reader 与完整 `command_result` serializer，owned synthetic storage 14 checks PASS；EXE SHA `72b45bac7823da714482400d37d53047d2dfd60310a474fdf1cbbf0404981307`。输入包括多 Faith 的 eminent true/false、重复站点、同低位不同 generation 的 artifact ID、显式站点与旧 generation unavailable。
- SDK：实际 `create_server`/GameplayBridgeService、NativeDriver、normalizer、MCP ClientSession `list_tools/call_tool`，3 个测试 PASS；消费上述 4 个完整原包，另核严格输入与跨 build 拒绝。仅 hello/snapshot/endpoint 是明确标注的 Python transport fixture，无 Python 预制业务 DTO。
- 公共 optin：实际 parser/default-off permission 测试 1 PASS；公共 case/selector 测试 24 PASS。
- increment02 因保留旧 source mtime 使 Ninja 沿用旧对象，产出仍为内层 DTO；第一次 SDK 消费真实 RED 已保留。increment03 刷新实际更换文件 mtime 后真正重编，新 EXE/全包才通过，未用 Python 补包。

外置证据根：`C:/workspace/ck3-faith-and-power-20261017/episode01/`。

| 原件 | SHA-256 / 说明 |
|---|---|
| `native-candidate/native-mcp-qualification-a02.json` | `7e006e5d16fb5d62865191edccb2db21cc7eedf1688fab0062995dba06bdf4f4`，保留失败 |
| `native-candidate/native-mcp-qualification-a03.json` | `faa0c148cd254c93df51519b0837adf93660aedf7d01ba5d64bcb85b8a7c6b4b`，完整原包与真实 MCP 返回 |
| `runtime/increment-03/holy-site-12004-wire/` | 4 个新 native 完整包，逐文件 SHA 见 a03 |
| `runtime/increment-03/timestamp-correction.json` | 构建时间戳纠正，旧失败保留 |
| `native-candidate/research-plan-readonly-a02.json` / `...-check.json` | `native_research_plan check --for-observation` 结构/文件完整性 PASS；不授予 live 资格 |
| `native-candidate/model-source/HOLY-SITE-MODEL-SOURCE.md` / `holy-site-model-abi.json` | 完整 getter、constructor、save/load、member 消费者与 ABI 来源 |
| `native-candidate/inventory-source/inventory-source-contract.json` | 12 个完整函数体支持的库存合同 |
| `native-candidate/gui-source/GUI-SOURCE-DELIVERY.md` / `INTEGRATION-SOURCE-HOOKS.md` | owner、原版 typed open、Any 生命周期和 callback 分类来源 |

本轮共享 `.text/.rdata` immutable 缓存用于有限静态 source 审查，避免重复全 EXE 扫描；它是活跃开发输入，按通用存储策略在 episode 收口时复核。测试源码不写运行时证据；外置执行器保存上述带机器身份的资格原件。
