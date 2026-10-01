# 1.20.0.2 当前玩家 Doctrine / Tenet 只读原生施工

施工开始记录：2026-10-01 16:17（Asia/Shanghai）。项目所有者已明确恢复宗教研究，同时停止战争相关研究。本专题只覆盖一般宗教与必要婚姻语义，不开展战争、圣战或 holy order。它是独立后续增量，不阻塞已冻结 nonwar candidate 的首轮实机。

冻结游戏为 CK3 **1.20.0.2 Crozier / Steam build 25588574**；`ck3.exe` 大小 `101039736` bytes，SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。施工输入是冻结安装文件，研究与夹具不访问运行中的 CK3。当前 baseline 为 [religion-stock](ck3-1.20.0.2-religion-stock.md) 与 [实际宗教 context](ck3-1.20.0.2-religion-context.md)，复用其已验证 getter，不重复旧验证。

`Character+0xB4` 是 full **RiteID**；Faith 由原生 `Character.GetFaith` 解析当前 Rite 后获得。角色采用的 Rite 与 Faith 的 main Rite 可以不同。因此“Faith intrinsic doctrine”“Rite 覆盖 doctrine”“有效 doctrine”必须分别保留来源与含义，不能将同一字段改标签当作完成。

## 五个并行工作包

| 工作包 | 当前交付目标 | 施工边界 |
| --- | --- | --- |
| Faith doctrine source | 原生 Faith 查询实际来源、authored definition 与 runtime 状态、stable key / group | 不将 main Rite 的当前集合误标为独立 intrinsic 列表 |
| Rite override | 实际 Rite doctrine collection、同 group 覆盖与 effective lookup | 不把 main Rite 当作玩家 Rite |
| Tenet / parameter | 原生 Tenet 分类与实际参数 getter、参数类型 / 来源 | 不以 stock 文本猜当前 runtime 状态 |
| 普通 hostility | 原生最终敌对分类 getter、方向与 enum 语义 | 仅一般宗教 / 婚姻，不研究军事使用 |
| Choices / legality | 实际 Doctrine / Tenet choices model、最终可见 / 合法输入 | 只读；不执行改宗、改革或创建信仰 |

每个工作包先记录 exact-build 原生树、ABI 与 Mermaid，再实现已闭合、能独立提供实际状态价值的最小只读 provider。复杂 choices model 未闭合时，记录具体构造器 / 最终 gate 的下一入口；不得用长期空字段或 schema 声称 choices 完成。共享 CMake、bridge 注册与 Python / MCP 接线由对应中央 owner 负责。本页及各域源不修改首轮冻结运行树。

```mermaid
flowchart TD
    A[实际 played Character] --> B[现有 religion context\nCharacter → actor Rite → Faith → Religion]
    B --> C[Faith+98 main Rite\nFaith HasDoctrine / GetDoctrines]
    B --> D[actor Rite\n当前礼仪 doctrine]
    C --> E1[Rite+7A0 / count+7AC\nmain Rite 当前集合]
    D --> E2[Rite+7A0 / count+7AC\nactor Rite 当前集合]
    E1 -. 初始化 / 同 group 语义施工中 .-> E[保留来源的 doctrine rows]
    E2 -. 初始化 / 同 group 语义施工中 .-> E
    E -. 独立 Tenet registry / 参数 getter 施工中 .-> F[Tenets 与两套当前 parameters]
    B -. 最终 getter 施工中 .-> G[普通 directional hostility]
    E -. 实际 choices model / 最终 gate 施工中 .-> H[只读候选与合法性]
    F -. 待 provider / fixture .-> I[私有只读 DTO]
    G -. 待 provider / fixture .-> I
    H -. 待 provider / fixture .-> I
    I -. 中央注册 + 真实 paused artifact .-> J[production-live primitive]
```

以上虚线保留尚未闭合的完整 choices 分支。施工开始时五包均为 **research**；当时预计第一批原生树 / ABI 在 20–40 分钟交付，已闭合 getter 的最小 provider / MSVC fixture 在 40–75 分钟交付，完整 choices model 在 60–120 分钟研究。以下以实际回执更新，估计不是验收承诺。

## 第一批静态发现

原生 `Faith.HasDoctrine` core `0x2439C20` 与 UI `GetDoctrines` `0xC59360` 解析 `Faith+0x98` 的 **main Rite**，继而访问 `Rite+0x7A0` doctrine pointer array、`+0x7AC` count。它们不是独立 Faith intrinsic 列表 getter；authored definition 的初始化来源与当前 runtime 集合需分别追查。当前角色的 Rite 及 Faith main Rite 要分别观测。

Faith 的 `has_doctrine_parameter` trigger `0x2B29170` 同样先解析 main Rite，再查 `Rite+0x7B8` 布尔 token 集；直接 Rite trigger `0x2AE9F70` 使用接收者 Rite 的该集合。两者均复用 membership `0xB9DE80`。布尔 token 与数值参数类型、key 来源正在闭合。新版 Tenet 有独立 `CTenetTypeDatabase`，不能按旧版 Doctrine group key 直接重命名为 Tenet。

一般 Faith hostility core `0x243E950` 通过双方 Faith main Rite 调用最终 `0x2591CE0`；其分类具有方向，offset 参数为 UI 变换。只读 provider 将固定 offset=false，并区分 actor Rite 及 Faith main Rite 的结果，分类标签与完整 ABI 由域专题冻结。

`window_rite_creation.gui` 的 choices 最终可选条件是 `DoctrineItem.CanPick(TopScope)` **并且** `pam_know_doctrine`，后者为真实玩家的 `knows_doctrine` 或 `prophet_perk`；还受 `ShouldDisplay(TopScope)` 控制。raw `CanPick` 不是完整最终合法性。choices model 的构造器、记录布局与 top-scope 输入仍有未闭合分支，不能将这个条件的名字或 schema 当作可执行候选 query。

后续 actual popup 研究已纠正同名 reflection 的类型归属：`0xEE47A0 → 0xEE0AD0` 是 **TenetItem.CanPick**，不是 DoctrineItem；DoctrineItem 单参数 wrapper 是 `0xEE4E60`，其 definition triggers 位于 `+0x1B8 / +0xE8`。知识 getter `0x28B0C00(Character*, DoctrineDefinition*)` 的生产读取与已完成 fixture 不受这个标签更正影响。choices ABI / 树已按新类型证据更新，旧标签不得用于最终合法性结论。

## 当前交付截点

2026-10-01 16:44（Asia/Shanghai）已完成 [当前 Doctrine query](religion_doctrine12002_query.md) 的真实 mailbox/完整 command-result：MSVC `/Od`、`/O2` 各 26 项新路径检查、各 4 份实际 full packet，并完成 3-reader 组合各 3 个 case。Python consumer 随后复用这四份 packet，3 个测试／7 个子场景通过；SDK 私有路由和中央 shared 登记由各 owner 接线。该包为 **static-ready**，没有 root paused artifact 时不称 live。

五个 library 首包及真实 Tenet rows 已各自通过必要 fixture，可复用下列原生专题：

- [Faith/main Rite Doctrine](religion_doctrine12002_intrinsic.md)：13 检查与 4 实际 JSON／模式。
- [actor Rite 有效 Doctrine](religion_doctrine12002_rite.md)：23 检查与 4 实际 JSON／模式。
- [布尔参数](religion_doctrine12002_tenet.md)：19 检查与 5 实际 JSON／模式；真实 core/personal Tenet rows 另有独立包。
- [一般 directional hostility](religion_doctrine12002_hostility.md)：20 检查与 7 实际 JSON／模式；其单独 target-Rite query/mailbox 正在交付。
- [Doctrine knowledge / choices 真实输入](religion_doctrine12002_choices.md)：19 检查与 8 实际 JSON／模式；完整可选列表/最终合法性未闭合，不以知识 getter 冒充它。

这些数字是各包原始验证范围，不汇总成新的验收矩阵或 live 计数。仅对新 selector/mailbox 路径增加相称的验证，不重跑已冻结 library 证明。第一批 ABI 和已闭合最小只读 primitive 在施工开始后约 27 分钟进入 static-ready；共享接线、真实 paused artifact 与实际游戏价值仍由下一增量记录。

交付记录应包含精确 tracked paths、SHA-256、原生 proof、一次与变更相称的实际 production-path fixture、失败 attempt、真实 readiness，以及日报 / 周报汇总字段。fixture 使用夹具进程的对象和原生回调替身，不等于运行游戏、fixture-live 或 production-live。后续真实 paused 验收由 root 串行执行。
