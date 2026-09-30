# CK3 本体更新：MCP 迁移策略与执行计划

编制日期：2026-09-30（Asia/Shanghai）。状态：**更新前核心归档与废弃产物清理已执行；新版本适配、实机验收待更新后开始**。

执行结果见 [更新前冻结与清理记录](ck3-pre-update-baseline-and-cleanup-2026-09-30.md)：核心恢复包已归档、三个安装的数据指纹已冻结、过时构建/worktree 已清理，13 个权限失败目录已提供管理员脚本。

本计划针对即将发生的 CK3 二进制与原版数据更新。新版本号、Steam build ID、EXE SHA 和实际变化均待更新后冻结；不预设新版本的 ABI 或具体玩法变更。源码审阅基线为 `f82d0e2` 加当前工作树，未提交的实现不能当作已发布候选。

## 1. 推荐策略与交付目标

采用 **保存完整旧环境 → 冻结新 build → 新增 exact-build adapter → 按依赖恢复观测和动作 → 恢复有界 OODA → 对齐旧版已验能力** 的路线。

保持 MCP 工具名、公开游戏语义和 pipe 协议尽量稳定，把新 RVA、布局、主线程入口和命令生命周期放在新版本实现内。迁移期间保留旧 adapter 和旧证据；每恢复一个能产生游戏价值的能力包，就验收、提交并推进下一包。

三个交付里程碑分别是：

| 里程碑 | 可见结果 | 完成条件 |
|---|---|---|
| R1：基础 MCP 恢复 | 新版本可读取真实地图、玩家、日期与暂停状态，控制时间并保存/冷恢复。 | 新 build 的正式 bridge/MCP 实机后置状态与 cleanup；仅 hello/heartbeat 不算。 |
| R2：短程自治恢复 | 从新版本原生 seed 连续完成观察、决策、操作、验证，能处理遇到的事件/互动并恢复进度。 | 20-turn 有界 canary；分别统计查询、玩法回合、实际日期推进、中断处理与 checkpoint。 |
| R3：迁移完成 | 更新前已验能力在新 build 上恢复到相同场景与证据等级，关键循环重新通过。 | 更新前后 capability 对照表无未解释回退；旧版未完成域仍如实保留。 |

R2 不等于自然死亡的一代人自治；R3 不等于全游戏自治。若双方约定暂缓某能力，交付称“部分迁移并恢复生产”，单列剩余工作，不能改写成全部完成。

## 2. 当前基线与实际失效范围

现有唯一注册的游戏 adapter 为 CK3 `1.19.0.6`，绑定 EXE SHA-256：

```text
2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86
```

旧版 ABI 和实机结果继续以 [native research](../ck3_autonomous_player/native_bridge/research/README.md)、[原生 AI 专题](ck3-native-ai/README.md) 与各冻结 artifact 为准。迁移方法沿用 [版本适配契约](ck3-native-version-adapters.md)，但本次源码审阅发现：基础 adapter 边界已经存在，后续 typed query 路径仍有版本耦合。

| 层 | 已有依据 / 预期影响 | 迁移处理 |
|---|---|---|
| MCP / Python SDK / stdio、HTTP | CK3 更新本身不要求更换 MCP SDK；工具可被列出不代表 gameplay 可用。 | 保持 SDK 与工具名，先读 `ck3_get_capabilities` 和 diagnostics，再调用已恢复能力。 |
| profile / runtime 部署 | `prepare-profile` 密封 EXE、launcher、rules、DLC、Mod 和 runtime；升级后旧 manifest 会失配。 | 备份旧 state，再给新安装重新 prepare/verify；不手改 hash 绕过失配。 |
| 通用 DLL / named pipe | 注入、hello、heartbeat、ping/reconnect 主要独立于 CK3 游戏对象。 | 在新安装单独验证；通信成功不升级 gameplay readiness。 |
| registry / 基础 adapter | `game_adapter.cpp` 按完整 EXE SHA 选 adapter；未知 build 只有 bridge identity/heartbeat/ping。 | 新增版本 factory/registry entry，逐项公布实际恢复能力，保留旧 SHA 的 adapter。 |
| owning-thread query / journal | `bridge.cpp` 的 `WarEntryApplicationMainMailboxWorkerLifetime` 显式限制旧 adapter ID；mailbox executors、route helper 和部分 dispatch 直接调用 `ck3_11906`。 | 新增 adapter 还不够；迁移这些路径的版本入口、生命周期和查询分派。 |
| 对象与命令 ABI | storage、generation ID、对象大小、vtable、constructor/validator/clone/queue/destructor 都可能变化。 | 逐能力重定位并核对语义，随后做布局 fixture 与 paused live；不能只平移 RVA。 |
| 原版脚本与 AI 数据 | 即使 EXE 未变，事件、互动、CB、AI 权重、defines、rules、DLC、GUI 和 stable key 也可能变。 | 独立做数据差异表，更新受影响原生树，再校准策略；EXE 相同不等于语义兼容。 |
| seed / checkpoint / driver state | 存档版本兼容性待实测，旧 full ID、choice/token、pending intent、pipe 与恢复锚点属于旧会话。 | 新版本先建 fresh seed；旧档只在复制体中做兼容测试，不直接继续旧动作队列。 |
| 启动诊断 / UI fallback / Mod | 当前 `bridge.cpp` 的四项 startup containment 默认关闭，particle2 recorder 也默认关闭；视觉 baseline 仍绑定旧版本。 | 保持默认关闭，先做无 DLL 对照；UI 和 Mod 各自验证，不自动继承旧坐标或补丁。 |

更新后的典型顺序是：旧 profile 拒绝启动 → 新 profile 可启动，但旧 DLL 报 `unsupported_build` → 新 adapter 逐步恢复。重新 prepare 只更新安装身份，不证明新 ABI 可用。

## 3. 更新前：现在应保存的材料

以下是执行清单；用户后续已授权执行，本轮**已完成核心 state/native 二进制归档与 build/data/source 冻结**，游戏本体直接复用已有目录，没有改动安装或运行玩法验收。具体文件、哈希、缺口和清理结果以 [执行记录](ck3-pre-update-baseline-and-cleanup-2026-09-30.md) 为准。

### 已有旧游戏目录，可直接复用

用户已提供保留的旧版安装：

```text
Z:\Crusader Kings III\Crusader Kings III_1.19.0.6_20260604
```

2026-09-30 20:16（Asia/Shanghai）只读检查确认：`binaries/ck3.exe` 大小为 `95,206,008` bytes，SHA-256 与第 2 节绑定值完全一致；`game/common`、`game/gui`、`game/events`、`launcher/launcher-settings.json` 存在，顶层同时保留 `clausewitz/`、`jomini/` 与 `launcher/`。这份目录可作为旧 build 的安装与逆向材料来源，**无需为了本计划再复制一份游戏本体**；保留原目录供新旧差异比较。

20:16 初次检查没有启动旧目录做运行回退验收，当时配套 DLL/userdir/state 尚未归档。后续执行已保存这些核心材料并核对现存 checkpoint/seed 的真实 hash；旧 production6b 临时 state 不存在的缺口已单列。运行回退尚未实测。游戏安装目录与玩家状态目录是两份材料；实际使用旧安装时，将 CLI 的 `--game-dir` 显式指向上述目录。

### A. 更新前必须保留

1. 停止现有自动游玩 owner/job，完成正常 checkpoint 和 cleanup，确认没有 CK3 进程，再让 Steam 更新。
2. 复用上述已保留旧目录；尚无旧目录时，在 Steam 更新目录之外保存旧安装的完整可运行副本，至少包含完整 `binaries/`、匹配的 `game/`、launcher 配置及运行所需文件。只存 `ck3.exe` 够做反汇编，不够承诺回退运行；副本能否在当前 Steam/DLC 条件下运行需单独确认。
3. 保存 launcher 原始/展示版本、平台、Steam appmanifest/build ID、EXE size/SHA、PE metadata，以及相关原版脚本/GUI/AI 数据的文件清单与指纹。游戏二进制和大体积数据留在仓库外，不提交 Git。
4. 保存当前可用的 production DLL/injector、各自 SHA、编译配置、源码 commit，以及对应 runtime/Mod projection/profile。当前工作树有大量既有变更，应另外保存本次相关 diff 与未跟踪源码；不要全仓提交、reset 或把杂项混进迁移提交。
5. 保存完整配套的 userdir/state：实际 checkpoint 文件、driver state、episode seed 文件和 metadata、environment manifest、tutorial 持久化、playset/rules/DLC 配置。记录它们的真实对应关系，不能只复制 JSON 指针。
6. 从现有 artifact 提取更新前能力基线：实际 `hello.capabilities`、关键 readiness、已验场景、代表性 GREEN/RED、cleanup 与恢复结果。逐项标出 `research / static-ready / fixture-live / production-live primitive / production-live loop`。

### B. 有时间再补

- 保留至少四类现成代表样本：paused map、事件/人物互动、战争/战斗、checkpoint 冷恢复；每类链接既有 ABI 与 artifact，不重复重跑。
- 保存公开 JSON 的代表 frame，作为旧/新 adapter 的语义回归输入；它验证协议兼容，不验证新引擎值正确。
- 如无可运行旧副本，明确记录“仅保留离线研究资料，运行回退未验证”。迁移照常开始，不把这项缺口扩展成额外审计。

建议归档：`artifacts/migrations/2026-09-30/pre-update/` 放索引、hash、能力表与小材料；完整旧安装使用仓库外目录。真正更新发生在其他日期时，按实际日期新建本轮目录。

## 4. 更新后迁移工作包

下面按单执行者的依赖顺序推进；不要求开启多代理。各包结束即保存结果、更新 docs/日报/周报并提交推送。

### M0：冻结新安装，区分二进制、数据与环境变化

**输入：** 新安装及更新前归档。

**施工：**

- 确认进程退出，冻结新版本号、EXE SHA/size/PE、Steam build ID、launcher/rules/DLC；列出新增、删除、内容变化的实际文件。
- 按已有能力关联变化：状态/命令、主线程泵、事件/互动、战争/战斗、政府/文化/法律、GUI/本地化、Mod 依赖。release notes 只作变化线索，安装内容和实际调用链决定结论。
- 新建独立 migration state/userdir，复制所需持久化材料并记录来源；用显式 `--game-dir` prepare/verify。不在唯一旧 state 上做原地试迁移。
- 做一次新版本无 DLL 的最小启动/地图对照，检查 Mod 加载与 parse/runtime 日志。随后通过受管入口验证未知 build 的 bridge-only hello、ping 与 cleanup。

**交付：** `build-identity.json`、`change-impact.md`、更新前后 capability ledger、对照 run。若 EXE 相同，优先处理实际数据/Mod/语义差异，免做无依据的全量 ABI 逆向。

### M1：补齐版本入口，建立新 adapter 的最小能力集合

**依赖：** M0 的 exact build。

- 新增 `ck3_<new_build>_adapter` 与该版本私有 bindings，接入 `game_adapter.cpp`、CMake 和独立测试；旧 `ck3_11906` 保留。实际文件名在拿到版本后确定。
- 检查 `bridge.cpp`、`game_adapter.cpp` 中本次要恢复的 typed query/step：将版本专属绑定和 owning-thread/journal 安装入口交给 adapter 或版本后端；可复用的 DTO、serializer、transport 保持稳定。
- 优先抽取已妨碍第二 adapter 的路径；不先搬全仓文件或重写所有历史能力。新 adapter 不能修改旧 adapter ID 来骗过 mailbox 的旧版判断。
- 新版本先只开放已验证的基础能力。研究候选走明确的验收配置；未实机通过的族不能进入生产 capability 集合。缺失能力沿用现有 unsupported/readiness 表达，不新增一套证明协议。

**交付：** 新 adapter 骨架、逐版本 lifecycle/query 接缝、旧版离线回归。仅该包完成时，新版本仍可是 `research/static-ready`。

### M2：恢复基础状态、主线程查询与最小时间循环

**依赖：** M1；具体 query 发布依赖新版本 owning-thread 入口闭合。

- 先定位 Jomini/game state、玩家/角色 storage、地图/日期/暂停/速度；核对 ID 宽度、generation、合法 absent 与读取失败的区别。
- 重定位 application-main/SDL pump、IAT/返回地址或新引擎等价调度点；核实 paused、地图切换与最小化条件下的实际执行线程和生命周期。
- 恢复 command queue 及 pause/speed 命令的构造、validator、clone/submit、析构。做一次“paused query → 推进一日 → 重新暂停 → 日期复查”的正式 MCP 闭环。
- 恢复 campaign root、selected rules、effective government 与 loaded feature manifest 的最小决策输入。runtime registry/DLC vocabulary 如有变化，重新从新 build 枚举；不能沿用旧版条目计数或用磁盘 descriptor 代替 runtime truth。

**交付：** 新版基础观测与时间 `production-live primitive/loop`、main-thread paused artifact。字段只有 schema 或长期 `null` 时，本包相关决策输入仍未完成。

### M3：恢复保存、冷恢复和中断处理，交付 R1/R2

**依赖：** M2；R2 同时依赖所遇中断能被真实处理。

- 恢复原生保存命令与外部进程 restore，核对新格式；从新版本 fresh seed 保存、退出、冷恢复，重新取得 PID/generation、日期、玩家与 history anchor。
- 冷恢复后重新查询 choice/token、pending/event identity 和路线候选；旧 process-local 数值不要求跨进程相等，旧缓存不作为新动作依据。
- 迁移 current-event-window 的 manager/root/window/data 生命周期、stable definition key、实际 shown/enabled/cancel 和选择命令；迁移人物互动 component、五角色/routing/deadline、通知 ACK 与 reply validator。核对新数据里的定义/选项 key、费用和 effect 语义。
- 沿用旧版的诚实语义边界：空 indicator 不代表无效果，legality/ACK 不代表 semantic readiness。旧 degraded policy 只能在重新确认对应原生树、输入与定义后继续使用，并记录质量债。
- 先完成一个事件/互动“查询 → 合法选择/回复 → 实例或关系后置变化”，再跑 20-turn canary。若自然遇到未观测输入，下一施工入口就是该输入的只读 native query，而不是无限等待 unknown。

**交付：** R1 的保存/恢复证据；R2 的 canary、连续 OODA 日志与 checkpoint。没有遇到某类中断的 canary 不能替代该类独立验收。

### M4：恢复战争与其他已验能力，交付 R3

**依赖：** M2/M3 与对应的新版本原生树/数据差异记录。

按“该 capability 是否阻塞当前游玩”选取下一包，默认顺序如下：

| 顺序 | 恢复包 | 至少核对的生产语义 |
|---:|---|---|
| 1 | active-war/army/objective/score，strength，route preview | 玩家/盟友/敌人 identity、目标和军队真值；effective origin、mid-edge 首跳、完整路线次序。 |
| 2 | raise/move/halt/split/merge/disband、siege/assault | 军队出现、移动/路线变化、组成和围城后置状态；Halt 的立即清空/保留首跳语义重新闭合。 |
| 3 | contact、ongoing combat、hold、retreat、reinforcement、terminal journal | CombatID/双方 membership/phase、撤退合法性、真实 terminal；detour 与 owning-thread 入口逐版本重绑。 |
| 4 | declare / enforce / exit options、terms | 新增/结束真实战争，成本/接受/结果来源明确；旧版白和/投降未开放的语义门不因迁移而跳过。 |
| 5 | marriage、title-map navigation、Mod 死亡结算及其他基线能力 | 合法候选与婚姻关系结果、camera settled、结算 serial/ready 与持久化；按旧版实际等级恢复。 |

每族先补决策输入，再恢复动作，最后恢复 planner。AI 权重、阈值或新 mechanics 改变时，先更新 [对应原生决策树](ck3-native-ai/README.md) 与 Mermaid，把未闭合分支画成虚线；随后才改我方策略。

新 build 的 ID/数值不同并不自动判 RED，应对齐稳定语义与实际结果。新玩法不在迁移中顺手全面实现；只扩展解除现有循环 blocker 所需的最小能力。

### M5：切换生产、保留回退入口

- 发布 fresh-build DLL/injector、对应源码 commit/SHA 与 production projection；正式 profile、operator job 配置里的 DLL、checkpoint、state/pipe 路径同步指向同一候选。
- MCP daemon/客户端刷新实际 capability；可保留工具名和 endpoint。DLL 变更后的最终验收使用 fresh process，不把旧进程混合 injection generation 当作生产通过。
- 新生产从已验新版本 seed/checkpoint 出发。旧档能否续玩另列结果：fresh-new GREEN 与 old-save-import GREEN 是两个结论。
- 新版不稳定时，回退整个已保存的旧安装 + DLL/injector + Mod/profile + userdir/state 组合；再次 verify，按已有代表路径确认恢复。仅换回旧 DLL，或让旧 EXE 配新 `game/`，不算已知回退环境。
- 保留所有失败 attempt，区分 harness RED 与 capability RED。仅真实新故障才进入修复；不借升级派生理论安全审计。

## 5. 排期、优先级与调整规则

`T0` 是实际更新并冻结新安装的时间。以下是目标窗口，不是已知工期；单执行者按依赖顺序交付，逆向重构深度决定实际耗时。

| 窗口 | 优先级 | 交付 | 时间不足时保留的最小结果 |
|---|---|---|---|
| 更新前剩余时间 | P0 | 第 3 节 A 的旧环境与能力基线归档。 | 先保完整安装、production binaries、配套 state 和证据索引。 |
| T0 当天 | P0 | M0：新 build 身份、数据 diff、无 DLL 对照、profile 与 bridge-only 诊断。 | 明确第一个真实阻点和下一施工入口。 |
| 第 1–3 个工作日 | P0 | M1/M2：新 adapter、主线程入口、基础 paused query 与一日循环。 | 先交付可用观测，不宣称仅通信恢复就是 R1。 |
| 第 3–5 个工作日 | P0 | M3：save/cold restore、中断原语、R1 与首个 R2 canary。 | 单族闭环与 artifact，明确未恢复的中断。 |
| 第 2 周起 | P1 | M4/M5：战争等旧版已验族、关键循环、生产切换与 R3 对照。 | 恢复能继续当前局的族，逐项记录剩余项。 |

仅地址平移的小更新可能在数日内完成；对象、主线程模型、脚本和存档共同变化时应按数周量级预留。拿到 M0 差异表和 M2 首个闭环后再给基于实证的估时，不承诺未知新版本在固定日期全面恢复。

调整规则：

1. 新版无 DLL 对照也失败：先解决安装/驱动/Mod/真实环境故障；不要把它当 adapter ABI 失败。
2. 只有部分族变化：只复核受影响依赖；同一 exact build、同一候选已有可核验证据直接复用。
3. 某域输入不足阻塞 OODA：其只读 bridge/MCP 观测口升为 P0，再恢复动作/策略。
4. 新 hotfix 改 EXE：重新冻结独立 SHA；复用仍成立的研究与代码，但该 SHA 的实机证据重新建立，不追随热更反复重写全部架构。
5. 旧 seed 不兼容：使用新版 fresh seed 恢复 R1/R2；旧存档导入单列，避免把存档转换变成所有 MCP 的前置依赖。
6. 宗教域仍 owner-deferred；只保留圣战完整战争 OODA 与婚姻必要判定两项窄例外，faith/religion 保持 opaque 或最小输入，holy order 继续暂缓。

## 6. 验证方法与可执行入口

复用 [版本迁移契约](ck3-native-version-adapters.md) 与 [testing-workflow](testing-workflow.md)，一次与风险相称的检查后继续交付。仅文档规划不需要重跑整个游戏矩阵；真正迁移时按下表执行。

| 层级 | 验证 | 能支持的结论 |
|---|---|---|
| 离线锚点 | 新 build manifest 的 SHA、unique signature、RTTI/vtable、关键调用链和字段语义。 | 锚点/静态 ABI；签名相似不能直接证明语义。 |
| C++ fixture / fresh build | 新版 layout/command 与 mailbox lifecycle 的针对性 fixture；fresh helper 的 CTest、源/header 依赖核对；保留旧 adapter fixture。 | `static-ready`；不等于真实游戏通过。 |
| Python / MCP contract | adapter hello、partial/unsupported、snapshot/result normalization、实际改动相关 driver/service/MCP 测试。 | 上层兼容；不等于引擎数值正确。 |
| paused production query | 新 build、正式会话、同帧 identity/value 与合法零值/absent；正式 MCP 调用。 | 对应查询 `production-live primitive`，夹具则保持 `fixture-live`。 |
| 动作与有界 OODA | 前置状态 → 原生命令 → 下一 paused frame 的真实变化，含必要冷恢复/cleanup。 | 对应 primitive/loop；submitted/ACK 不能替代结果。 |
| 生产切换 | R2 canary + 受影响关键循环 + 更新前后能力对照。 | 经明确范围定义的 R3；不补写旧版未验场景。 |

下面是**迁移执行时的模板**，尖括号必须换成实际路径/版本；本次没有运行这些命令。profile prepare 前先完成备份并确认 CK3 退出：

```powershell
Get-FileHash -LiteralPath '<新安装>\binaries\ck3.exe' -Algorithm SHA256

& 'tools\.venv\Scripts\python.exe' 'ck3_autonomous_player\agent.py' `
  --game-dir '<新安装>' --state-dir '<新版独立state>' --bridge-mode disabled prepare-profile
& 'tools\.venv\Scripts\python.exe' 'ck3_autonomous_player\agent.py' `
  --game-dir '<新安装>' --state-dir '<新版独立state>' --bridge-mode disabled verify-profile

py ck3_autonomous_player/native_bridge/research/scan_anchors.py `
  --exe '<新安装>\binaries\ck3.exe' --manifest '<新版anchors.json>'

# 在 x64 Visual Studio developer shell 中执行；BuildDir 必须尚不存在。
& 'ck3_autonomous_player\native_bridge\tools\build_fresh.ps1' `
  -BuildDir '<本轮新的build目录>'

& 'tools\.venv\Scripts\python.exe' -m unittest discover `
  -s ck3_autonomous_player/tests/unit -p test_native_adapter_protocol.py
```

现有 `research/run_*_live_acceptance.py` 以及 [canary handoff](autonomous-agent-progress/one-generation-canary-handoff.md) 可复用 runner 结构；先替换其中旧 SHA、checkpoint、固定 ID/预期数据和版本 ABI。原样跑旧 harness 报 RED，不能直接推断新版能力失败。native-headless 继续以最小化、零 OCR/键鼠 fallback 验收；视觉后端只有新版 UI contract 实测后才重新启用。

Mod 依赖另做最小修复与静态/本机验收：变动的生成器输入先更新再生成，禁止手改 `GENERATED FILE`；廷臣 trait 快照按实际新版提取、审阅，再生成；原生继承 GUI 重新投影；玩家限定闸门、BOM、production staging 规则继续遵守。日常只改简中与英文，正式发布翻译另走既有 workflow。

## 7. 迁移账本、验收记录与施工入口

每个能力包在本轮 `capability-ledger.md` 维护一行，**这是执行时待创建的记录格式，不代表现已迁回任何能力**：

| capability / MCP tool | 旧 build 等级 / artifact | 新 build 实际变化 | 当前等级 | ABI / 代码 / 测试 | 新 live artifact / 后置状态 | 依赖 / 下一动作 |
|---|---|---|---|---|---|---|
| 基础 snapshot / `ck3_take_snapshot` | 从旧 hello 与 artifact 填入 | 待 M0/M2 | `research` | 待填 | 未验收 | 新 state/storage/玩家链 |
| owning-thread typed query | 分别记录对应族 | 待 M0/M2 | `research` | 待填 | 未验收 | 新 application-main/mailbox |
| checkpoint / restore | 从旧实际恢复证据填入 | 待 M3 | `research` | 待填 | 未验收 | 保存 ABI、fresh seed |
| event / interaction / war 等 | 逐族记录，不能整域笼统写 complete | 待对应包 | `research` | 待填 | 未验收 | 按真实 blocker 排序 |

每份新 artifact 记录 build identity、源码 commit/工作树状态、DLL/injector SHA、profile/playset/rules/features、seed/checkpoint hash、PID/generation、前后观测、动作结果和 cleanup。复用现有 artifact 格式，不扩展无必要的 WAL/schema/证明系统。

具体施工入口：

- registry / ABI：[`game_adapter.cpp`](../ck3_autonomous_player/native_bridge/src/game_adapter.cpp)、[`ck3_11906_adapter.cpp`](../ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp)、[`ck3_11906.cpp`](../ck3_autonomous_player/native_bridge/src/ck3_11906.cpp)、[`CMakeLists.txt`](../ck3_autonomous_player/native_bridge/CMakeLists.txt)。
- query / lifecycle：[`bridge.cpp`](../ck3_autonomous_player/native_bridge/src/bridge.cpp)、[`main_thread_query_mailbox_v1_abi.json`](../ck3_autonomous_player/native_bridge/research/main_thread_query_mailbox_v1_abi.json) 及各族 ABI JSON。
- Python / MCP：[`native_driver.py`](../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py)、[`service.py`](../ck3_autonomous_player/src/xar_autoplayer/bridge/service.py)、[`mcp_server.py`](../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py)。
- 执行环境：[`operator-mcp.md`](operator-mcp.md)；CK3 job 必须在正确的操作者 token/desktop 上运行，通用 operator MCP 不随 CK3 ABI 重写。
- 原生树与能力债：[`ck3-native-ai/README.md`](ck3-native-ai/README.md)、[`one-generation-blocker-ledger.md`](autonomous-agent-progress/one-generation-blocker-ledger.md)。旧 build 结论保留版本标签，不能全局替换 SHA 就称新版 live。

更新前冻结现已执行；取得新版本后首先交付 M0 的差异表，随后依据实际变化确定 M1/M2 的最小改动。R1/R2/R3 的完成状态必须能回链新 build 的证据，旧版归档不代表新版兼容。
