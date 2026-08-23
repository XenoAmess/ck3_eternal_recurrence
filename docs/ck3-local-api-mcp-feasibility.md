# CK3 本地 API 与 MCP 桥接可行性预研

> 调研日期：2026-08-23
>
> 本机基线：CK3 `1.19.0.6`，Windows x64
>
> 状态：架构预研；未实施 DLL 注入，未启动游戏验证本方案

## 1. 结论

目标系统**可以构建**，但须区分两种含义：

1. 普通 CK3 Workshop 数据 Mod 不能自行监听 HTTP、实现 MCP Server 或访问任意操作系统资源。
2. “CK3 游戏桥 + 本地伴随进程”可以向 MCP 客户端提供实时或准实时的状态与受控操作。
3. DLL 注入或内存 hook 可以突破脚本层能力上限，技术上足以实现实时双向桥；但它不再属于受支持的 CK3 Mod API，而是按游戏版本维护的原生逆向工程。
4. 不建议永久修改 `ck3.exe`，也不建议把完整 HTTP/MCP 栈放进游戏进程。推荐使用“外部 MCP daemon + 薄注入 DLL + 可选数据 Mod”。
5. 无论使用哪条桥，均不能承诺“全部内部状态 + 全部合法玩家操作 + 跨版本稳定”。未暴露的硬编码规则、派生缓存、命令同步和 UI 上下文仍须逐项逆向或适配。

可行性判断：

| 路线 | 能力 | 可维护性 | 证据等级 | 结论 |
|---|---:|---:|---|---|
| 普通 Mod 内直接启动 HTTP/MCP | 无 | — | 官方/脚本能力证据 | 不可行 |
| 数据 Mod + 日志/`run` + 外部 MCP | 中高 | 高 | 公开组件链路实证；本项目闭环待实测 | 推荐 MVP |
| 存档解析 + MCP | 只读、中等宽度 | 中高 | 公开源码实证 | 已有先例，但不实时 |
| 外部进程读取 CK3 内存 | 只读、较宽 | 中低 | 通用 OS 能力；CK3 待实测 | 可作逆向探针，不宜直接成为稳定 API |
| DLL 注入 + 薄 IPC shim | 高 | 中低 | 通用注入/hook 能力；CK3 待实测 | 原生路线首选 |
| DLL 内直接承载 HTTP/MCP | 高 | 低 | 架构推论；CK3 待实测 | 技术可行，产品上不推荐 |
| 永久修改 `ck3.exe` | 高 | 极低 | 通用二进制工具能力；本机签名证据 | 最不推荐 |

## 2. 证据等级与边界

本文用以下标签区分事实强度：

- **本机实证**：在当前仓库或 CK3 1.19.0.6 本地安装中已有日志、源文件或验收结果。
- **公开源码实证**：第三方公开项目的代码已经实现对应链路。
- **源码证据**：原版脚本、GUI 或官方/社区维护的能力文档明确存在该入口，但本项目尚未做完整运行时复现。
- **待实测**：架构合理，但必须用当前 CK3 构建做隔离探针后才能升级为结论。
- **未查明**：当前资料不足，禁止按“已支持”设计产品契约。

本轮只做只读调研，没有注入 DLL、修改 EXE、启动 CK3 或执行多人/成就测试。公开资料和本地安装中均未找到可信、持续维护的 CK3 专用 native loader、Script Extender、原生插件 ABI 或官方 DLL Mod SDK。这个结果只能表述为“本轮未发现”，不能证明此类项目绝对不存在。

## 3. 普通 CK3 Mod 的能力边界

CK3/Jomini 脚本只允许使用引擎注册的 scope、trigger、effect、on_action、GUI datatype 和 scripted GUI。CK3 Wiki 的脚本限制明确写有 `No access to the operating system`；`script_docs` 则用于枚举当前构建实际注册的脚本能力。参见 [CK3 Scripting](https://github.com/jesec/ck3-modding-wiki/blob/master/wiki_pages/Scripting.md) 与 Paradox [Dev Diary #87: Royal Modding](https://www.paradoxinteractive.com/games/crusader-kings-iii/news/dev-diary-87-royal-modding)。

因此普通 Mod 不能：

- 创建 TCP socket、监听 HTTP 或主动调用远程 API；
- 启动 exe、PowerShell、shell 或其他本地进程；
- 通过普通脚本 API 任意读取外部 JSON、命令文件或操作系统内存；
- 通过普通脚本 API 动态求值任意字符串为 CK3 scope、effect 或对象引用；
- 访问未由引擎注册为 trigger/effect/datatype 的硬编码状态。

普通 Mod 可以：

- 在现有 on_action、事件、决议、互动、scripted GUI 和周期 pulse 中观察脚本可见状态；
- 使用 `debug_log` / `error_log` 向引擎约定的日志输出动态信息；
- 由 GUI 的 `ExecuteConsoleCommand` 调用游戏内部控制台命令；
- 通过 GUI -> `ExecuteConsoleCommand('run ...')` 这一高权限特殊入口加载并解析 `run/<filename>.txt` 的 effect grammar；原版源码和 VOTC 证明入口存在，本机 1.19.0.6 的 non-debug 自动执行语义仍待实测；
- 通过 scripted GUI/effect 修改脚本层允许修改的状态。

本仓库已有的边界证据：

- [cross-save-persistence.md](cross-save-persistence.md) 记录了 CK3 缺少通用外部 I/O 与跨存档 API，且 `debug_log` 是只写出口。
- [gui-system.md](gui-system.md) 记录了普通窗口中的 `GetPlayer`、`GetScriptedGui` 和 `ExecuteConsoleCommand` 能力。
- [testing-workflow.md](testing-workflow.md) 已使用 `debug.log` 增量标记验证真实游戏链路，并记录 GUI 自动执行控制台命令尚未在本项目完整验证。
- 本机原版 `Crusader Kings III/game/gui/console.gui:191-196` 含 `ExecuteConsoleCommand('run run.txt')` 的 Run 按钮；游戏本体目录被 `.gitignore` 排除，此项属于可由合法本地安装复查的源码证据，不是仓库内发布链接。

## 4. 无需逆向的双向桥已有先例

### 4.1 实时/准实时 Mod 桥

Voices of the Court 已公开实现与本目标相近的双向链路：

```text
CK3 effect
  -> debug_log 输出结构化 VOTC:IN 记录
  -> 游戏 GUI 把 VOTC:IN 通知复制到剪贴板
  -> 外部 Electron 应用收到通知后读取并解析 debug.log
  -> 应用写入 CK3 用户目录 run/votc.txt
  -> talk_window_v2 存活期间，无可见内容的 counter widget
     约每 0.4 秒执行 ExecuteConsoleCommand('run votc.txt')
  -> effect 执行并通过日志/剪贴板返回结果或通知
```

直接源码证据：

- [游戏状态日志 effect](https://github.com/Voices-of-the-Court/votc_mod/blob/d99807aee66c48b98c10951c501e33134aefa474/common/scripted_effects/log_gamedata_v3s_effect.txt#L3)
- [外部应用解析 debug.log](https://github.com/Voices-of-the-Court/VOTC/blob/0968a13575cb336f8b1bd1f2bd1c37a3cf660d9d/src/main/gameData/parseLog.ts#L29)
- [外部应用轮询并分发剪贴板通知](https://github.com/Voices-of-the-Court/VOTC/blob/0968a13575cb336f8b1bd1f2bd1c37a3cf660d9d/src/main/ClipboardListener.ts#L23-L58)
- [外部应用管理 run/votc.txt](https://github.com/Voices-of-the-Court/VOTC/blob/0968a13575cb336f8b1bd1f2bd1c37a3cf660d9d/src/main/actions/RunFileManager.ts#L14)
- [对话窗口内的 counter widget 循环执行 run 文件](https://github.com/Voices-of-the-Court/votc_mod/blob/d99807aee66c48b98c10951c501e33134aefa474/gui/custom_gui/talk_window_v2.gui#L69-L83)
- [利用 GUI 复制到剪贴板发出低延迟通知](https://github.com/Voices-of-the-Court/votc_mod/blob/d99807aee66c48b98c10951c501e33134aefa474/gui/event_window_widgets/event_window_widget_talk_v2.gui#L16)

这证明“数据 Mod + 本地应用”的链路可行性不是概念猜想。它不证明全局常驻轮询、原子文件替换、无竞态或可靠传输，也不证明本项目当前 1.19.0.6、non-debug、暂停、读档和所有模态窗口下都具备相同运行时语义；这些仍须独立验收。

### 4.2 存档到 MCP

[ck3-strategy-advisor](https://github.com/thomandretti/ck3-strategy-advisor) 已将最新可读 CK3 存档包装成只读 MCP tools，证明 MCP 层本身没有技术障碍。其限制也具有代表性：

- 普通存档只有保存后才新鲜；
- 二进制 autosave/Ironman 不能按普通文本直接解析；
- 中后期存档可能达到数百 MB，解析存在秒级延迟和较高内存峰值；
- 很多意见、合法行动和派生值没有以最终计算结果存入存档。

因此存档适合作为诊断或宽状态补充，不适合作为实时操作闭环的唯一通道。

## 5. EXE 修改、外部内存访问与 DLL 注入

### 5.1 永久修改 EXE

可以通过修改导入表、插入 loader stub、代码洞或静态 detour 让 `ck3.exe` 加载自定义代码。Microsoft Detours 也提供二进制导入表编辑和 payload 能力，参见 [Detours 概览](https://github.com/microsoft/detours/wiki) 与 [payload/import editing](https://github.com/microsoft/Detours/wiki/OverviewPayloads)。

但这条路线没有必要，且维护成本最高：

- 本机 `ck3.exe` 当前 Authenticode 状态为 `Valid`，签名者为 Paradox Interactive；修改代码、导入表等 Authenticode 哈希覆盖的映像内容会使原签名验证失败。
- **经验性维护风险**：Steam 更新或“验证游戏文件”通常会替换补丁后的文件，须在目标渠道做实际更新/修复测试。
- 每个版本都要重新确认 patch offset、原指令和控制流。
- 除非另有明确许可，不应把 Paradox 原二进制或其修改副本作为项目产物分发；即使只分发 patcher，也须严格绑定合法原文件哈希并单独审阅许可边界。
- **经验性分发风险**：杀毒软件和终端安全产品通常会提高对 EXE patcher 的风险判定，须用最终签名产物实测。

本机只读指纹：

```text
文件：Crusader Kings III/binaries/ck3.exe
大小：95,206,008 bytes
SHA-256：2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86
Authenticode：Valid
```

该指纹只描述本机当前安装，不是所有 1.19.0.6 渠道构建的 canonical 哈希。

### 5.2 外部进程内存读取

外部程序可使用 Windows [`ReadProcessMemory`](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-readprocessmemory) 等进程 API 读取 CK3 地址空间，不必先注入 DLL。它适合：

- 寻找玩家角色、日期、暂停、资源等少量候选锚点；
- 观察对象布局和验证 signature scan；
- 在不改变游戏进程代码的情况下制作只读原型。

主要问题：

- ASLR、编译优化和游戏更新会改变地址与布局；
- 多层指针可能在读取期间失效；
- 跨线程读取无法自然获得一致的“同一 tick 快照”；
- 外部写内存更容易绕过引擎不变量，不应作为正式操作层。

### 5.3 DLL 注入

DLL 一旦进入 `ck3.exe`，即可使用正常的 Windows 网络、文件和 IPC API，也可以对满足指令 prologue、调用签名、线程和生命周期约束的已定位函数安装 hook。这里要区分两层：Detours 可在创建进程时装载 instrumentation DLL，并提供 detour；[MinHook](https://github.com/TsudaKageyu/minhook) 只是在代码已经进入进程后提供 x86/x64 detour，不是 CK3 injector。参见 [Microsoft Detours](https://github.com/microsoft/Detours) 与 [Using Detours](https://github.com/microsoft/detours/wiki/Using-Detours)。这些通用工具不证明 CK3 的 VM、command dispatcher 或对象布局已经被定位。

注入成功只解决“代码进入进程”，不解决 CK3 语义。仍需逆向：

- 主模拟线程或安全的 tick/update hook；
- 当前 game instance、玩家角色和对象生命周期；
- 脚本 VM、scope、trigger/effect registry 或控制台 dispatcher；
- interaction、decision、战争、军队等命令对象及其合法性检查；
- 读档、退回前端、退出和热重载时的失效边界；
- 多人命令序列化和主机权限。

下表只是尚无 CK3 native probe 支撑的架构估计，全部标为**待实测**：

| 接入方式 | 预期语义可靠性 | 预期逆向成本 | 预期风险 | 证据 |
|---|---:|---:|---:|---|
| 调用现有脚本/effect/console 分发入口 | 较高 | 中 | 中 | 待定位、待实测 |
| Hook GUI data model 或引擎 command | 高 | 高 | 中高 | 待定位、待实测 |
| 读取内部对象图并生成快照 | 中 | 高 | 高 | 待定位、待实测 |
| 直接修改 C++ 对象字段 | 低 | 高 | 极高 | 不建议实施 |

对状态，优先复用引擎 getter、脚本 scope 或只读序列化路径；对操作，优先调用玩家 UI 最终使用的 command/interaction 路径。直接修改金币、战争、头衔或军队字段可能绕过合法性、缓存、历史、通知、费用、AI 反应和同步，不能称为“执行了合法玩家操作”。

### 5.4 不建议在 DLL 内承载完整 MCP

技术上可以在注入 DLL 内启动 loopback HTTP Server 并直接实现 MCP JSON-RPC；不推荐这样设计：

- HTTP 线程、JSON 库、TLS/认证和依赖冲突会扩大 CK3 的崩溃面；
- 网络回调线程不能安全地直接读取正在变化的游戏对象；
- DLL 卸载、读档和游戏退出期间很难可靠停止全部后台线程；
- MCP 协议升级会迫使重新发布和注入游戏 DLL；
- 网络端点漏洞会与 CK3 进程权限合并。

Windows 明确要求 `DllMain` 只执行最小初始化，并警告 loader lock 下的进程创建、复杂同步、线程和动态加载可能死锁或崩溃；参见 [Dynamic-Link Library Best Practices](https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-best-practices)。DLL 应延迟初始化，并把网络/MCP 留在外部进程。

## 6. 推荐架构

```text
支持 MCP 的 AI 客户端
  |-- stdio --------------------------|
  `-- Streamable HTTP / 127.0.0.1 ----|
                                      v
                            ck3-mcp-daemon
                     MCP tools/resources/prompts
                 schema、认证、幂等、审计、确认、缓存
                                      |
                    当前用户 ACL 的 named pipe
                       或 shared-memory + event
                                      |
                              ck3_bridge.dll
                    薄 shim、版本门禁、主线程队列
                                      |
                        CK3 getter / command / VM
                                      |
                           可选 CK3 数据 Mod
               稳定 scripted effect、玩家闸门、游戏内确认 UI
```

建议 daemon 内定义可替换的 `BridgeDriver`：

- `LogRunDriver`：`debug.log` + `run/*.txt`，作为低风险 MVP；
- `SaveDriver`：存档只读补充；
- `UiDriver`：截图/OCR/经验证鼠标操作，处理只能由原生 UI 完成的动作；
- `InjectedDriver`：named pipe 连接薄 DLL，提供低延迟状态和原生命令。

这样可以先证明 MCP 产品语义，再按真实瓶颈替换游戏桥，不需要一开始就承担完整逆向成本。

### 6.1 DLL 线程模型

1. IPC 线程只做帧解析、长度检查和命令入队，不解引用 CK3 对象。
2. hook 一个已验证的主线程安全点，每 tick 最多处理有限数量请求，并断言线程 ID、游戏 phase 和递归深度。
3. 调用引擎前释放 IPC/队列锁；command 可能同步开事件、切换状态或使旧对象失效，hook 必须有 reentrancy guard，返回后重新取得对象而非继续使用旧指针。
4. 主线程重新验证 game instance、存档、玩家、暂停、revision 与动作前置条件。
5. 主线程调用引擎 getter/command，或把状态复制为不含游戏指针的普通快照。
6. 后台线程只序列化复制后的快照并回写 IPC。
7. 退出/读档时先使 generation 失效，未完成请求返回 `unknown`，不得自动重放。
8. 生产版不热卸载 DLL；停用时只停止接单、解除仍可安全解除的 hook，并让进程退出自然回收模块。

本文的 `revision` 是桥自建的单调观察代数：每次发布新快照或确认动作提交时递增，用来把 action handle 绑定到一次已观察状态。它不是 CK3 引擎提供的全局事务号，也不能发现两次观察之间所有未导出的状态变化；游戏侧执行前仍必须重新检查完整前置条件。

### 6.2 版本门禁

每次启动至少校验：

- EXE SHA-256 与已支持构建完全匹配；
- 所有 signature scan 恰好命中预期数量；
- 目标函数 prologue、调用约定和附近不变量匹配；
- RTTI/vtable/object generation 探针通过；
- 失败时不安装任何 hook，并让 MCP 只报告 `unsupported_build`。

禁止“在未知版本上试着跑”。模式扫描只能减少维护成本，不能把私有 ABI 变成稳定 ABI。

## 7. MCP 契约

MCP/HTTP 只是 AI 客户端与 daemon 之间的协议，不应兼任 daemon 与 CK3 的进程内桥。单一客户端优先提供 stdio；需要独立常驻服务或多个客户端时再提供 Streamable HTTP。两种传输的定位见官方 [MCP Architecture](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture)、[stdio](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio) 与 [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)。

建议资源：

- `ck3://session`
- `ck3://state/current`
- `ck3://ui/screenshot`
- `ck3://capabilities`

建议工具：

- `ck3.get_session`
- `ck3.take_snapshot`
- `ck3.get_player`
- `ck3.get_realm`
- `ck3.list_legal_actions(snapshot_id)`
- `ck3.prepare_action(action_handle, expected_revision)`
- `ck3.commit_action(confirmation_token, request_id)`
- `ck3.get_action_status(request_id)`
- `ck3.wait_for_change(after_revision, timeout_ms)`

不得对模型开放：

- 任意 `execute_console_command(text)`；
- 任意 `execute_effect(text)`；
- 任意文件路径；
- `read_memory(address)` / `write_memory(address, value)`；
- 未经游戏侧复验的“legal=true”客户端断言。

动作句柄应绑定 `game_instance_id + snapshot_id + revision + action_id + parameters_hash`。所有写操作还必须带独立 `request_id`；JSON-RPC `id` 只负责一次传输关联，不是幂等键。

建议状态及重试规则：

| 状态 | 含义 | 是否可重试 |
|---|---|---|
| `accepted` / `queued` | daemon 已受理，尚未获得游戏侧开始证明 | 只有证明未开始后才可取消或重新排队 |
| `started` | 游戏侧已开始处理 | 不可自动重试 |
| `committed` | 已获得提交 ACK | 不可重试，返回缓存结果 |
| `rejected` | 前置条件不满足，且确认没有副作用 | 修正输入并取新快照后可发新 request ID |
| `failed` | 已证明动作未提交 | 仅按明确错误策略处理 |
| `unknown` | 可能已生效，但 ACK 或持久记录丢失 | 绝不自动重放 |

daemon/DLL 的 ledger 无法与 CK3 动作形成跨进程原子事务：动作可能已经生效，而 ACK 或 ledger 尚未落盘。此时只能返回 `unknown`，通过重新取快照和检查后置条件缩小不确定性；后置条件也未必能唯一归因于该请求。把 request token 在同一个游戏 effect/command 中记录可以加强防重，但其跨崩溃持久性仍取决于存档时机，因此不得承诺跨崩溃 exactly-once。

## 8. 安全、一致性与游戏边界

### 8.1 本地接口安全

- 默认只读，操作能力显式启用。
- MCP Streamable HTTP 规范要求（MUST）校验 `Origin`；并建议（SHOULD）本地服务只绑定 loopback 且实施认证。[MCP Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- 本项目进一步硬性要求 HTTP 只绑定 `127.0.0.1`、校验 `Host`、使用随机 bearer token，不得绑定 `0.0.0.0`。`Host` 与 bearer 形式是项目加固策略，不是 MCP 规范指定的唯一实现。
- named pipe 每次启动使用随机 nonce 名称、`FILE_FLAG_FIRST_PIPE_INSTANCE` 和只允许当前 Windows 用户的显式 DACL，并校验 peer PID、映像路径及预期父子/会话关系；仅有同用户 DACL 不能阻止同一用户下的恶意进程或 pipe squatting。Windows named pipe 的 security attributes 可定义 DACL，参见 [CreateNamedPipe](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createnamedpipea) 与 [GetNamedPipeClientProcessId](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid)。shared memory/event 等命名对象采用同等防抢占策略。
- `read`、`operate`、`debug-admin` 分权；公开 MCP 永不包含 raw memory/console 权限。
- 高影响动作由本地托盘或游戏内窗口确认，不能只依赖 tool description。
- 对输入长度、请求频率、输出大小、字符集和路径做硬限制。
- CK3 人物名、事件文本、Mod 文案和存档内容均视为不可信数据，不得拼入系统提示、工具描述或代码。

### 8.2 游戏状态一致性

- MVP 采用“暂停 -> 在已验证主线程安全点生成逻辑一致快照 -> 决策 -> 单动作 -> 新快照”的回合制门闩。暂停只减少游戏时间推进，是产品门闩；它不保证其他线程、GUI 或派生缓存停止，也不是原子性的证明。
- 同一时刻只允许一个写请求在途。
- 请求必须带 `expected_revision`，过期即返回 `stale_snapshot`。
- game instance、读档 generation 或玩家角色改变时，使旧句柄全部失效。
- DLL 和 daemon 都保存幂等记录；同一 request ID、不同参数直接冲突。
- DLL 在执行前再次检查玩家、作用域、费用、冷却和合法性；外部判断只能用于展示。
- 状态快照必须注明来源、游戏日期、paused、revision、字段完整度和是否包含隐藏信息。

### 8.3 本项目硬边界

若将本方案接入本项目，所有数据 Mod 入口仍必须遵守：

- 只以 `GetPlayer` 或等价玩家根开始；
- 游戏内 effect 同时验证 `is_ai = no` 和项目玩家启用 flag；
- 新 on_action 即使对全场角色触发，也必须先包玩家 limit；
- 外部“AI 客户端”只代表替玩家决策的程序，不能给 CK3 内部 AI 留入口；
- 首版拒绝多人、Ironman、前端、读档中和未知模态状态。

多人模式中单客户端直接调用内部 effect 或修改对象很可能造成 OOS。找到并复用原版 host-authoritative command/serialization 路径只是重新评估的必要条件，还必须验证正确网络 phase、所有参与端兼容、确定性输入与时序、隐藏信息和公平性边界。首版禁多人既是 OOS 防线，也是作弊风险和支持责任边界；本文没有做任何多人验证。

## 9. 分发、维护与许可风险

- 普通 Workshop 适合数据 Mod，不适合承担 native DLL/注入器分发和更新。
- 原生桥应使用独立安装器/启动包装器，提供源码、签名、构建哈希、版本清单和明确卸载方式。
- 不覆盖原始 EXE；不使用模糊 DLL 搜索顺序劫持作为默认安装方式。
- 每个 CK3 补丁先降级为只读/不支持，重新逆向并通过门禁后才开放操作。
- 注入、hook 和代理 DLL 可能触发杀毒软件；不能要求用户关闭安全软件作为正常安装步骤。
- 不触碰 DRM、DLC 校验、成就绕过或账号/多人服务。

成就与 Ironman 是两个不同问题。官方 [CK3 1.9.0 “Lance” 更新说明](https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-128-ck3-1-9-0-lance-update.1583293/) 称单人非 Ironman 和使用普通 Mod 不再自动阻断成就，但切换玩家、打开多人大厅或使用 debug commands 会取消该局资格。`ExecuteConsoleCommand('run ...')` 是否被 1.19.0.6 计为 debug command、native injection 是否影响资格，本轮均未验证，因此产品不得承诺成就兼容；首版拒绝 Ironman 则出于存档、可恢复性和支持边界，不应把它写成成就的同义词。

Paradox 2026-01-21 版 [User Agreement](https://legal.paradoxplaza.com/eula) 把 scripts/programs/mods 列入 UGC，允许创作与公开，但默认要求 UGC 免费且严格非商业，并只列出特定捐赠/赞助例外；同时禁止损害服务以及开发、分发或出售 cheats。协议没有明确授予 EXE 注入的通行权。若 daemon、托管服务或安装器拟收费，必须先单独解决许可问题。任何公开分发都须按产品用途、发行平台和所在地法律审阅；本文不是法律意见，也不把技术可行性等同于官方许可。

## 10. 推荐实施顺序

### Phase 0：不注入的产品语义原型

1. Mod 按需输出带 `BEGIN/schema/session/revision/END` 的玩家状态帧。
2. daemon 提供 `/health`、`/v1/session`、`/v1/snapshots/latest` 和只读 MCP tools。
3. 验证日志截断、重启、读档、重复帧和实际日志可见延迟。本机 `Crusader Kings III/game/log_settings_live.json` 的全局 `flush_interval_seconds` 为 3，但特定 logger 的 `always_flush_level` 可覆盖缓冲行为，所以 3 秒既不是固定延迟，也不是 SLA。
4. 用 `run/ck3mcp_inbox.txt` 和一个无害的 Mod 自有 effect 验证 request/ACK 闭环。
5. 严格验证 non-debug、暂停、模态窗口、热重读、原子替换和重复执行语义。

退出标准：只读状态可靠；一个白名单动作在同一存活会话内对已知 request ID 防重。ACK 丢失或进程重启后若无法证明未开始，则进入 `unknown` 且绝不自动重放，不承诺跨崩溃 exactly-once。

### Phase 1：最小原生探针

1. 启动包装器向受支持 SHA-256 的 CK3 注入空 DLL，不改 EXE。
2. DLL 通过 named pipe 只返回 build、hash、PID、generation 和 heartbeat。
3. 找到一个主线程安全点；不修改状态，只读取是否载入、日期、玩家 ID 和暂停状态。
4. 制造未知版本、错误签名、退回菜单、读档和退出负例，要求 fail closed。
5. 保存崩溃 dump、hook 安装记录和完整版本指纹。

退出标准：连续多次启动/读档/退出无崩溃，未知构建不安装 hook，状态快照有明确 generation。

### Phase 2：受控原生命令

1. 优先逆向一个无害、可验证、由原版 command/effect 完成的动作。
2. 完成 `prepare -> confirm -> commit -> ACK -> new snapshot`。
3. 验证 stale revision、重复 request ID、超时 unknown、daemon/DLL 任一重启。
4. 再逐项适配决议、互动、事件选项、战争、军队；每个动作族独立认证。

退出标准：每个公开 tool 都有游戏内前置条件、执行后反证、同一会话幂等测试、`unknown` 不重放测试和版本回归夹具。

### Phase 3：混合驱动

对无法安全调用内部 command 的原生 UI 操作，保留截图/OCR/经验证鼠标驱动。内存桥负责提供观察与控件身份，UI 驱动负责保持真实玩家操作语义。不要为追求“全部走内存”而直接 set 状态。

## 11. 首轮必须回答的未决问题

以下问题在实机 probe 前保持“待实测/未查明”：

1. 当前 1.19.0.6 在 non-debug 模式下，自定义注册 GUI 是否能稳定自动执行 `run`。
2. `run/*.txt` 是否每次重新读取，原子替换时是否可能读到旧文件或半文件。
3. 暂停、原生 modal、读档和退回前端时，隐藏 GUI state 是否继续推进。
4. 最安全的模拟主线程 hook 是哪一个，是否跨大厅/游戏态共用。
5. 是否能定位并复用脚本 VM/effect dispatcher，而不直接操作对象字段。
6. 玩家可见 getter 与内部对象在同一 tick 的一致性如何定义。
7. 哪些原生动作存在可复用的 host-authoritative command，哪些只能走 GUI。
8. 当前平台/渠道构建之间是否共享同一二进制哈希和内部布局。
9. 注入器、DLL 与 daemon 在常见安全软件下的误报和签名要求。
10. 公开分发的许可、平台规则和支持边界。

在这些问题解决前，项目定位应保持为：

> 单机、暂停态、显式授权、有限语义动作的 CK3 AI 控制桥；不是完整 CK3 API，不支持多人或 Ironman，也不保证跨版本原生 ABI。

## 12. 2026-08-23 架构决策：一套策略，两种速度

本轮结合已经跑通的 one-life planner、持久 CK3 development session 与本机 1.19.0.6 二进制后，决定不把
“视觉智能体”和“MCP 智能体”做成两套产品。策略层只认识语义步骤与结果；感知/执行由可替换 backend 提供：

```text
one-life planner
       |
GameplayStepExecutor.execute_step(step) -> StepResult
       |
       +-- vision: OCR + CK3 快捷键 + 必要鼠标
       +-- mod:    debug.log snapshot + run/*.txt scripted effect
       +-- native: injected DLL + named pipe + CK3 command dispatcher
       `-- hybrid: 当前步骤 native/mod 支持就走快桥，否则回落 vision
```

这不是全局二选一开关，而是**按能力逐步迁移**。例如原生桥先支持日期、暂停/速度和事件选项时，婚姻候选仍可走
OCR；后来定位 `CSendCharacterInteractionCommand` 后，婚姻步骤再切过去。一个快桥已经声明支持的动作如果执行时报错，
不会再盲目通过视觉后端重放；只有“该 backend 尚未实现此步骤”才选择 fallback。

### 12.1 为什么现有 planner 可以直接复用

`strategy.choose_one_life_turn()` 不消费截图对象。它主要读取命令历史，以及少数稳定的语义结果：战争分数、订婚是否接受、
分割风险、胜利/解散状态、原生存档摘要、事件中断与本代死亡终点。因此无需先造一个覆盖 CK3 全部对象的巨型 API，
也不应把 MCP 状态硬塞进强绑定 PNG/OCR 的 `observation-v2`。

当前代码已抽出 backend-neutral `GameplayStepExecutor` 和共用的单回合/多回合 runner；视觉实现只是其中一个 callback。
另有独立的 `GameplayBridgeDriver`、semantic-first hybrid 路由和 MCP v2 server facade。MCP 目前公开：

- `ck3_get_capabilities`
- `ck3_take_snapshot`
- `ck3_plan_turn`
- `ck3_auto_turn`
- `ck3_execute_step`
- `ck3_save_checkpoint`
- `ck3_restore_checkpoint`
- `ck3_reply_pending_character_interaction`
- `ck3_select_event_option`
- `ck3_resolve_active_event`
- `ck3_wait_for_change`
- `ck3://capabilities`
- `ck3://state/current`

`vision-report` driver 只读现有持久 session 报告；`vision-session` 通过 run 目录内的原子 inbox/outbox，把 MCP semantic step
交回该常驻 session 的主线程执行。`mod` driver 会原子写 `run/xar_mcp_inbox.txt`、增量读取 `debug.log` 的完整 request frame；
`hybrid` 将数据 Mod 快照和视觉 session 的命令历史/未迁移动作合并。四者都复用同一个 planner 和同一组 MCP tools。

### 12.2 原生动作已有的本机逆向锚点

当前 `ck3.exe` 没有公开插件 ABI，但保留了足够多的 MSVC RTTI/断言字符串。本机只读枚举已经看到：

- `CSelectEventOptionCommand`、`CRemoveEventCommand`
- `CSendCharacterInteractionCommand`、`CReplyCharacterInteractionCommand`
- `CExecuteDecisionCommand`
- `CRaiseTroopsCommand`、`CMoveUnitCommand`、`CDisbandArmyCommand`
- `CPauseGameCommand`、`CSetGameSpeedCommand`、`CAutoSaveCommand`
- `CGameCommandHelper<T>`、`CJominiCommandHelper<T>`、`CEventManager`、`CWar`、`CArmy`

这使“复用原生玩家 command”成为有具体入口的逆向任务，而不是直接写内存字段。第一条 native 端到端动作应选择
`CSelectEventOptionCommand` 或 `CSetGameSpeedCommand`：它们能立即替换当前最频繁的全屏 OCR + 快捷键循环，验证价值也最直接。

### 12.3 重启边界

- Python planner、MCP daemon、driver 路由、schema 与 OCR 逻辑：可热更新，不需要重启 CK3。
- MCP 在 vision/mod/native/hybrid 间切换：DLL 已随本局加载且能力兼容时，不需要重启 CK3。
- 数据 Mod 脚本或 GUI 本身改变：通常需要重新加载内容或重启游戏。
- DLL、hook 地址或进程内协议改变：开发期可用 injector `--pipe` 给现有 CK3 附加一个新的 DLL generation，无需重启；
  正式/干净验收仍用 suspended pre-resume injection 启动新进程，避免旧 generation 继续驻留。

`runtime.py` 已用 `CREATE_SUSPENDED` 创建 CK3；原生加载器的自然接点是在 Job/进程身份建立后、`process.resume()` 前。
因此不需永久修改 `ck3.exe`，也不需要让每次 MCP/策略迭代承担一次游戏冷启动。

### 12.4 价值优先实施顺序

1. 已完成：抽离 backend-neutral turn runner，保留 OCR/键鼠 baseline。
2. 已完成：MCP v2 tools/resources 与 hybrid capability routing；用 official Python SDK 做 in-memory 协议测试。
3. 已完成离线原型：独立数据 Mod bridge 输出玩家 ID、日期与 total days，0.4 秒执行 typed `run` inbox，并以
   `BEGIN -> STATE -> ACK -> END` 回帧；Python `mod` driver 已闭合请求、增量日志解析和 MCP snapshot。游戏内链路仍待一次专用 profile 实测。
4. 已完成首个 live native slice：x64 薄 DLL、长度前缀 UTF-8 JSON、250ms heartbeat/ping/pong、suspended 注入与已运行进程
   `--pipe` attach；exact-build bridge 可读取日期 tick、公开 1–5 档速度、暂停状态和本地玩家 ID，并通过原生命令队列执行
   `pause-map`、`resume-map`、`set-speed-1..5`。
5. 2026-08-23 已用正式 MCP client/tools 在真实 CK3 1.19.0.6 的最小化窗口完成 headless loop：
   `ck3_take_snapshot -> resume-map -> ck3_wait_for_change (date_raw 53171400 -> 53171424) -> pause-map`；该过程未调用
   OCR、截图、窗口激活或键鼠。`native-session` 还会用 `-continuelastsave` 尝试直接载入最后存档。
6. 已完成：active event/选项、`CSelectEventOptionCommand`、`life-advance`、原生 checkpoint 落盘与进程级恢复；
   玩家角色 `CharacterID`/生死已进入 snapshot。Python native driver 在首次 `map_ready=true` 且存在玩家角色时锁定
   `episode_character_id`；此后观察到角色死亡或 played `CharacterID` 改变都会直接终止一代制本局。
7. 已完成离线实现、待真实样本：待处理角色互动 snapshot 与 `CReplyCharacterInteractionCommand` 接受/拒绝。
   下一步按实际收益接主动婚姻、战争状态、宣战、抬兵/移动/解散；缺少原生 capability 时，纯 native 明确返回
   unsupported，只有 `hybrid-fallback` 配置才允许回落。

本项目是本机单人游戏自动玩家。当前开发优先级由“能否更快、更稳定地完成实际玩法”决定；与实际崩溃、错误动作或
不可用版本无关的泛化安全证明，不进入这条功能路线的阻塞清单。

### 12.5 最小化运行与可配置回落

MCP 运行时必须把下面两种模式公开为不同配置，禁止用同一个名称隐式改变行为：

| 模式 | 原生能力缺失时 | 最小化 CK3 | 视觉/键鼠 |
|---|---|---|---|
| `native-headless` | 返回 `unsupported` | 继续使用 DLL 状态快照与原生命令 | 永不调用，也不自动恢复或激活窗口 |
| `hybrid-fallback` | 按公开的 backend 顺序尝试下一项 | native 与 data-Mod 能力可继续；vision fallback 不可用 | 只有窗口当前可见且该步骤尚无语义 backend 时才允许 |

`native-headless` 是纯原生产品模式，不包含“为了完成任务临时切回 OCR”的隐藏分支。其 capability 响应必须明确包含
`headless=true`、`minimized_operation=true`、`fallback_enabled=false` 和 `visual_fallback=false`。尚未完成逆向的步骤应保留为
可查询的 unsupported capability，而不是唤醒窗口。

`hybrid-fallback` 是另一个显式模式。它公开 `fallback_order`，初始顺序为 native → data Mod → vision session；快 backend
已经接收某项动作后发生错误时不向下重放，只有调用前就确定为 unsupported 或 unavailable 时才选择下一 backend。视觉
fallback 还必须先证明窗口处于可截图状态；最小化时直接返回该步骤当前不可执行，不得用 `ShowWindow`、前台激活或键鼠把
窗口偷偷拉回来。这样用户可以在“保证全程后台”与“可见时优先完成更多功能”之间明确选择。

最小化运行是否真正成立，以同一 PID 下的实机连续推进为准：窗口最小化后，MCP 仍能读取日期/暂停/速度/当前事件，调用
原生命令推进游戏并收到新 revision。named-pipe heartbeat 只能证明 DLL 线程仍活着，不能替代上述游戏语义验收。

### 12.6 一代制角色身份契约

`NativeHeadlessGameplayDriver` 的生命周期就是一局 rogue episode 的身份边界。第一份同时满足 `map_ready=true` 和
`played_character.character_id` 有效的 snapshot 锁定 `episode_character_id`；加载期没有玩家角色时保持未锁定，不猜测角色，
同一个 driver 经 `restore-checkpoint` 建立新的 DLL connection generation 时也不重置该 ID。

每份 native snapshot 和 capability 响应显式返回：

- `episode_character_id`：本局首次锁定的玩家角色，未进入可玩地图前为 `null`；
- `one_life_terminal` 与 `one_life_terminal_reason`：同 ID 且存活时为 `false/null`；原角色 `alive=false` 时 reason 为
  `played_character_dead`；当前 played ID 已变时为 `played_character_changed`；
- `continue_as_heir_after_death=false`：primary heir 只参与当前生命的继承风险评估，不是下一位可玩角色。

因此即使 CK3 在相邻两个采样间完成死亡与继承、没有留下 `alive=false` 帧，planner 仍会选择唯一的 `death-terminal`，其结果用
`native_played_character_changed` 区分该路径，绝不对新 ID 执行婚姻、战争或推进时间。恢复到死亡前 checkpoint 且 played ID 仍与
锁定 ID 相同则继续本局。`played_character` 规范同时允许成对携带可选的 `primary_heir_id`/`has_heir`；这两个字段只作为策略信息，
不会改变 episode identity 或授权继承人 gameplay。

Native driver 现在还为每次锁定的 episode 生成稳定的 `episode_run_id`。当 `death-terminal` 被执行且 MCP 配置了
`state_dir` 时，它会把本进程积累的原生命令历史、终局原因、检查点摘要和已有玩法成果直接写入
`strategy/one-life-history.json`，并在结果中返回 `cross_run_strategy`。同一 driver 重复读取终局会以同一 run ID
更新该 episode；下一局仍只读取这份智能体自己的历史来调整开局优先级，不继续扮演继承人。
