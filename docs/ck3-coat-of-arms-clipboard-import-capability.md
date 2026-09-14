# CK3 纹章设计器剪贴板导入能力报告

> 调研日期：2026-09-08 至 2026-09-15
>
> 页面：角色设计器 → 自定义纹章 → 设计你自己的纹章 → 从剪贴板粘贴
>
> 精确基线：CK3 `1.19.0.6 (Scribe)`，Steam build `23530548`
>
> 路线：MCP-first；页面识别与导航也必须优先使用原生语义 MCP。历史 UI 导航证据只保留为过程记录，
> 不授权在 MCP 缺能力时继续回退到 OCR、鼠标或键盘链。

## 1. 结论

“从剪贴板粘贴”不是任意 CK3 脚本执行器。它把一段文本送入
`CoatOfArmsDesigner` 的专用纹章 reader，物化为
`SCoatOfArmsRenderDescription`，再生成粘贴预览；只有显式 paste 才把候选纹章写进当前
designer 的 working state。

可实际生效的是静态纹章数据：

- `pattern` 与根级 `color1`、`color2`、`color3`；
- 重复的 `colored_emblem`；
- emblem 的 `texture`、`color1..3`、`mask`；
- 重复的 `instance`；
- instance 的 `position`、`scale`、`rotation`、`depth`；
- 受限的 `textured_emblem` 数据。

它不会获得 scope，也不会进入 effect、trigger、event、decision、scripted GUI、控制台命令或本地化表达式解释器。
因此“某段文本被 reader 接受”最多意味着它能物化一份纹章描述，绝不等于其中长得像 CK3 脚本的字段会执行。

面向后续 Web 编辑器的稳定合同应是“一个确定的静态纹章对象”，不是“任意 CK3 代码”。

## 2. 证据分级

本文区分以下状态，避免把语法接受、资源有效和最终提交混为一谈：

| 状态 | 含义 |
|---|---|
| `engine-static` | 本机构建的 GUI、EXE 控制流、字段或原版语料已经确认 |
| `mcp-static-ready` | MCP/原生能力、闭合 schema 与自动测试已实现，但尚未在真实 CK3 进程中执行；不能作为语法结论 |
| `mcp-detected` | MCP 精确绑定到本次 CK3 进程，写入并回读相同源码，原生 `CanPaste` 为真且取得 preview handle |
| `mcp-applied` | 在 `mcp-detected` 基础上调用原生 paste，并验证 designer working state 已切到候选纹章 |
| `mcp-exported` | MCP 调用当前 designer 的原生 Copy，成功读取本次回调写入剪贴板的非空源码并绑定其字节数与 SHA-256 |
| `mcp-roundtrip` | 同一 CK3 进程和 exact binding 中完成 apply → export → 原样 reapply → export，且两次 canonical export 字节完全相同 |
| `mcp-committed` | MCP 只激活实时 GUI 树中的固定王朝 Finish，验证 route 从 `coat_of_arms_designer` 返回 `ruler_designer`，重开后原生 Copy 字节不变 |
| `browser-mcp-live` | 真实浏览器中的 Vue UI 经 Quarkus REST、Java MCP SDK、Python stdio MCP 和 native bridge 完成 apply/export，并把原生 Copy 结果写回编辑器 |
| `legacy-ui` | 早期人工/UI 辅助观察；仅作补充，不作为 MCP-first 最终证据 |
| `unresolved` | 证据不足、含义歧义或资源与语法尚未拆开验证 |

`mcp-applied` 只证明当前纹章设计器 working state 已改变。2026-09-14 新增的 `mcp-committed` 进一步证明王朝 Finish
已把该状态提交回仍在运行的角色设计器；它仍不冒充“完成整个角色创建”、进入战役后的王朝/家族/头衔状态或跨存档持久化。

## 3. MCP-first 探测能力

### 3.1 补能力前后的事实

用实际安装的 Python MCP SDK `2.0.0` 连接现有 stdio server 时，补能力前共列出 62 个工具，
没有 coat-of-arms、clipboard 或 designer 工具。也就是说，旧 MCP 无法回答本报告的核心问题。

本轮先后新增原生 CoA source、frontend route/action 工具和七个离线资源/渲染工具：

```text
ck3_probe_coat_of_arms_source_v1(
    source: string,
    expected_revision: integer,
    apply: boolean
)

ck3_export_coat_of_arms_source_v1(
    expected_revision: integer
)

ck3_query_frontend_gui_route_v1()

ck3_activate_frontend_new_game_v1()

ck3_activate_frontend_coat_of_arms_designer_v1()

ck3_commit_frontend_dynasty_coat_of_arms_v1()

ck3_inspect_frontend_coat_of_arms_tree_v1()

ck3_activate_frontend_coat_of_arms_custom_mode_v1()

ck3_query_coat_of_arms_resource_catalog_v1(
    game_directory: string,
    kind: "pattern" | "colored_emblem" | "color",
    query?: string,
    visible_only: boolean = true,
    offset: integer = 0,
    limit: integer = 50
)

ck3_read_coat_of_arms_resource_asset_v1(
    game_directory: string,
    kind: "pattern" | "colored_emblem",
    name: string
)

ck3_read_coat_of_arms_render_support_v1(
    game_directory: string
)

ck3_query_coat_of_arms_load_configuration_v1(
    user_directory: string
)

ck3_query_coat_of_arms_installed_dlc_sources_v1(
    game_directory: string
)

ck3_query_coat_of_arms_configured_resource_catalog_v1(
    user_directory: string,
    kind: "pattern" | "colored_emblem" | "color",
    query?: string,
    visible_only: boolean = true,
    offset: integer = 0,
    limit: integer = 50
)

ck3_read_coat_of_arms_configured_resource_asset_v1(
    user_directory: string,
    kind: "pattern" | "colored_emblem",
    candidate_id: 64-char uppercase SHA-256 identity
)
```

对应原生 capability：

```text
game.command.probe-coat-of-arms-source-v1
game.command.export-coat-of-arms-source-v1
game.command.query-frontend-gui-route-v1
game.command.activate-frontend-new-game-v1
game.command.activate-frontend-coat-of-arms-designer-v1
game.command.commit-frontend-dynasty-coat-of-arms-v1
```

probe 不属于自动游玩 planner 的无参数 action 集合，只能由调用方显式提供源码；export 则调用游戏自己的
`CoatOfArmsDesigner.OnCopyToClipboard` 路径，读取当前设计器写回系统剪贴板的源码。为了覆盖角色设计器所在的开局前流程，
MCP 合同明确区分三种绑定：

- `frontend`：尚无 semantic snapshot，必须使用 `expected_revision=0`；
- `frontend_snapshot`：世界地图已经生成并发布非零 snapshot/revision，但 `played_character=null` 且
  `episode_run_id=null`；绑定精确的 snapshot ID、public/native revision、date、PID 与 connection generation；
- `gameplay`：已有玩家角色和 episode，继续绑定非零 revision、date 与 episode identity。

三种模式共同要求：

- native bridge 已连接；
- 唯一 `bridge_pid` 与 `connection_generation` 在调用前后不变；
- hello 明确为 `ck3-1.19.0.6-msvc-x64`；
- EXE SHA-256 与版本完全匹配；
- `ck3_build_match=true` 且 capability 由同一 hello 广告。

Hybrid 后端中的 probe/export 与固定 frontend 动作都强制直达 native，
不会回退到 OCR、坐标或视觉驱动。`ck3_commit_frontend_dynasty_coat_of_arms_v1` 只解析实时
`ruler_designer` 树中的固定 `dynasty_finish_button`，并要求动作前为 `coat_of_arms_designer`、动作后为
`ruler_designer`；调用方不能传控件名、路径或指针。受管实机往返已经把该动作从 `mcp-static-ready` 提升为
`mcp-committed`，但证据范围止于角色设计器内的王朝家徽提交。

resource catalog 不启动 CK3，也不经过视觉路线。它先校验 `binaries/ck3.exe` 的 exact-build SHA-256，然后读取原版
`50_coa_designer_patterns.txt`、`50_coa_designer_emblems.txt` 与 `50_coa_designer_palettes.txt`，按原版设计器顺序分页返回
名称、颜色通道数、可见性、分类、相对路径以及当前页 DDS 的大小和 SHA-256。结果明确标记
`engine_registration_observed=false`、`dlc_and_mod_overrides_included=false`：它证明 exact 1.19.0.6 基础游戏磁盘资源，
不冒充运行时注册表或玩家当前 playset。

asset reader 只接受上述 manifest 中唯一存在的精确名称，再读取对应 DDS；返回 bounded base64、字节数、SHA-256、宽高、
mipmap 数与 FourCC，并复用同一 exact-build/provenance 边界。它不接受调用方提供相对路径，当前本机样本证明 pattern 为
DXT1、colored emblem 为 DXT5。这个工具用于后续浏览器像素预览，仍不声称与 CK3 shader 最终合成逐像素一致。

render-support 工具继续沿用 exact EXE SHA 门禁，返回 `coa_mask_texture.dds` 与原版 `_default.dds` 的 bounded base64、15 个
`default_colors.txt` 命名颜色的原始模型/分量与 RGB 解算，以及五份 Clausewitz/Jomini/game shader 源文件的路径、大小和
SHA-256。它把 pattern/emblem 通道顺序、mask 通道隔离、surface detail、transform 顺序与 alpha blend 投影成结构化合同；
不返回或复制第三方实现。离线官方 MCP SDK 对 exact 安装读取 `_default.dds` 的结果为 96×96、7 mip、49,272 bytes、
无压缩 BGRA8；前端据此显示原始纹理，但尚未把 `textured_emblem` 合成进成品。当前唯一明确未从随附源码闭合的 shader 常量是
引擎如何绑定 `FallbackColor`，最终 GPU 采样与色彩空间也仍需以后用原生像素 primitive 对照。

load-configuration 工具只读当前 CK3 用户目录的 `dlc_load.json`，按其中的 `enabled_mods` 顺序解析 `.mod` 描述符，
为目录模组列出九类 `common/coat_of_arms` / `gfx/coat_of_arms` 直接候选文件、DDS 数量、`replace_path`、描述符与配置哈希。
archive 模组只报告路径与存在性，当前不解压枚举。结果固定标记 `launcher_database_used=false`、
`engine_mount_observed=false`、`resource_merge_applied=false`：它补齐“当前启动配置里有哪些候选资源”，尚未补齐
Clausewitz/Jomini VFS 的覆盖、合并和运行时注册语义。

exact EXE 的静态字符串把 `enabled_mods`、`disabled_dlcs`、`dlc_load.json` 与
`clausewitzlib/dlc.cpp` 绑定在同一诊断簇，并单独包含 `replace_path not implemented for MSGR_DLC`；这证明 store DLC 与普通
mod 至少存在不同处理分支，但字符串证据本身不能给出完整 mount 顺序。为避免把磁盘安装误当授权，新
installed-DLC-sources MCP 只在 exact-build 门后枚举 `game/dlc/*/*.dlc` 及其内容根九类 CoA 直接目录，并固定声明
`store_entitlement_observed=false`、`engine_mount_observed=false`。本机 29 份 `.dlc` 描述符的结果为
`dlc_with_coa_candidates=0`、CoA TXT/DDS 均为 0；因此本机 designer 清单中的 DLC 风格资源名不能据此解释为独立 DLC 树覆盖。

运行态来源使用已有 `ck3_query_loaded_feature_manifest_v1` 原生 MCP，而不是从上述磁盘描述符反推。它在同一 paused/map-ready
snapshot 内返回完整 44 项 effective gameplay feature flag 和 script `has_dlc` key 集合，并对前后 root、bitset、registry 与
snapshot 漂移 fail closed；entitlement 继续固定为 `unavailable/store_verdict_provenance_unclosed`。Web 伴随服务现已把该工具加入
有限白名单并提供独立“读取运行态”入口。这个结果能证明当前进程哪些 gameplay gate/脚本 DLC key 生效，但尚未把这些 gate 映射成
CoA VFS mount、同名资源 precedence 或 designer 最终 registry，因此不能据此自动选择冲突 DDS。

本机静态交叉检查解释了为什么不把启动器 SQLite 当作权威输入：当前 `dlc_load.json` 精确为 38 bytes、SHA-256
`B28A99338A45655C4A25CFEE44602A56451960142C9DD9E767B78C21A08C91BB`，配置启用模组为零；同一时刻启动器库中
“Initial playset”仍保存 82 个 enabled 条目，但该 playset 的 `isActive=0`，另两个 playset 也没有 active 标记。
这组数据证明数据库可保留非当前播放集，不能反向覆盖 `dlc_load.json` 的直接配置事实。

configured-resource catalog 继续解析目录模组及 ZIP archive 内的 designer manifest，分页返回配置顺序、
mod/descriptor/manifest provenance、
资源字段与同名候选计数；它只报告 potential conflict，不推导同名胜者。configured asset reader 不接受调用方路径或裸资源名，
只接受由当前 `dlc_load.json`、描述符 hash、manifest 路径/hash、条目序号、kind/name 共同派生的 opaque candidate ID；
配置顺序、描述符或 manifest 字节变化后
旧 ID 会失效。两者仍固定声明 `resource_merge_applied=false`、`load_order_precedence_applied=false`。因此现阶段 Web 编辑器可审计
“哪些目录/ZIP 模组声称提供哪些纹章资源”及其精确 DDS，但不会把这个集合冒充引擎最终 effective registry。
Vue 编辑器把这些来源放在独立候选表中：用户可显式选定某个 opaque candidate 做预览，序列化结果仍只写 CK3 资源名，
同名冲突不会被 UI 静默消解。

### 3.2 每条 MCP 结果提供什么证据

公开结果包含：

```text
status
detected
designer_observed
clipboard_written
clipboard_readback_matched
apply_requested
paste_invoked
applied
candidate_index
preview_coat_of_arms_handle
active_coat_of_arms_index
reason
source_sha256
source_bytes
binding
```

输入先限制为非空 ASCII、无 NUL、最多 128 KiB，并以 base64 通过 named pipe；API 在编码前把 LF、CRLF、旧式 CR
统一为 Windows 剪贴板实际回读的 CRLF，SHA-256 与字节数绑定这份规范文本。原生侧写系统剪贴板后立刻 read-back 比较。
该 ASCII 限制来自当前 CK3 reader 的真实行为：高位 UTF-8 字节会令外层函数提前退出，
而且可能留下旧的 `CanPaste` 状态；首版若允许任意 Unicode 会制造假阳性。

状态只有：

- `detected`：只检测，原生 reader 接受；
- `applied`：检测成功并验证 working state 应用成功；
- `not_detected`：本次精确源码未被 reader 识别；
- `apply_failed`：检测成功但原生 paste 后置条件失败；
- `unavailable`：没有在超时内观察到有效 designer，或原生入口不可用。

查询会覆盖 OS 剪贴板并改变游戏里的 paste preview，因此不是无副作用的纯读操作。

export 的公开结果为闭合 schema，包含 `status`、`designer_observed`、`copy_invoked`、`clipboard_read`、
`source`、`source_sha256`、`source_bytes`、`reason` 与同一 exact binding。成功状态只有 `exported`；已进入 designer callback
但未能调用 Copy 或未能读取剪贴板时返回 `unavailable`，不会泄露上一次成功结果；超时未观察到 designer 则整次命令失败。
当前实现限制输出为非空 ASCII、无 NUL、最多 128 KiB。2026-09-13 已在真实 CK3 进程中取得 `mcp-exported`，并与
`mcp-applied` 组成同会话 `mcp-roundtrip`；具体载荷与边界见 3.4。

### 3.3 验证状态

- Python contract、service、native driver、hybrid、离线资源索引/读取和真实 MCP SDK tools/list/call：30 项聚焦测试 GREEN；
  不带 MCP SDK 的普通 Python 环境同组测试 30 项 GREEN，其中 3 项 SDK 集成测试按设计跳过；
- native bridge fresh build：成功；
- native protocol、adapter registry 与 main-thread mailbox CTest：3/3 GREEN；
- 王朝 Finish 的 Python contract/driver/service/MCP/live-runner 聚焦测试 18/18 GREEN；Vue 40/40、Quarkus REST 15/15、
  Vite production build 与 Maven test GREEN；
- 2026-09-14 受管实机通过官方 MCP SDK 完成 apply → 原生 Copy → 固定 `dynasty_finish_button` → 返回
  `ruler_designer` → MCP 重开家徽页 → 原生 Copy。两次 Copy 均为 330 bytes、SHA-256
  `4769FD42836E68FA35DC07FBA23BEABCC589E5A33087314F1D6287E5C53C305A`，原文逐字节相等；route/action checks、
  cleanup、双锁释放与 Steam 离线均 GREEN，全程 OCR/keyboard/mouse 为 false；
- Copy/export MCP primitive 已完成 closed-schema 注册、exact-build RVA/prologue 身份校验、UI-thread 调用、剪贴板读取、
  SHA-256 与 exact binding 投影，并在 2026-09-13 的同进程 round-trip 中达到 `mcp-exported`；
- 离线 resource catalog 已对本机 exact 1.19.0.6 安装执行：基础游戏 manifest 共定义 42 个 pattern（38 个 designer 可见）、
  1,578 个 colored emblem（1,576 个可见）和 13 个背景色；该结果不含 DLC/mod override，也不是运行时注册证明；
- Web 编辑器的 Quarkus 伴随服务已完成真实后台贯通：`REST → MCP Java SDK 2.0.1 stdio client → Python MCP server →`
  `ck3_query_coat_of_arms_resource_catalog_v1` 返回 exact-build 两项 pattern 和完整 provenance；该贯通未启动或操作 CK3，
  也没有使用 OCR。Quarkus REST 映射 3/3、前端 API/parser 8/8、production build GREEN；
- Web 编辑器随后在真实浏览器和 CK3 进程间完成 `Vue → Quarkus REST → MCP Java SDK 2.0.1 → Python stdio MCP →`
  `native bridge → CoatOfArmsDesigner` 的 apply/export 闭环；浏览器实际发出 3 次 session GET、1 次 probe POST 和 1 次
  export POST，全部 HTTP 200。当前 Quarkus 测试 9/9、Vitest 24/24、前端 production build 与 Quarkus package 均 GREEN；
- 新增 manifest-owned asset reader 后，同一后台链路读取 `ce_martlet.dds` 的 87,536 bytes DXT5，base64 解码 SHA 与
  `25EFE25D83047430EF09C1E6490CA48BD2A79865CCCF668EED0844381B3F7BA3` 完全一致；Quarkus 4/4、前端 API/parser/DDS
  decoder 12/12 与 production build GREEN。`pattern__solid_designer.dds` 则为 128×128 DXT1；
- 新增 render-support MCP 后，后台 `REST → Java MCP SDK → Python stdio MCP → exact game/Jomini/Clausewitz files`
  返回 15 个命名颜色、五份 shader provenance 和 256×256 DXT1 surface mask；其 base64 解码后仍为 43,832 bytes，SHA-256
  `5FA2A49DC59AEEBA19709B6BB3F9D0B017ACDE7DC576793705EAF85C7F33691E`。官方 Python MCP SDK 9/9、Quarkus 5/5、
  前端 18/18 与 production build GREEN；全过程使用 `vision-report` 离线 driver，没有调用 session/probe/export；
- render-support MCP 随后补入唯一原版 textured-emblem 素材 `_default.dds`。真实安装的离线官方 MCP 调用返回
  96×96、7 mip、49,272 bytes、BGRA8，SHA-256
  `697430F86ABD26B5056A8779E4BF78C7CB526A57B5AD13F02898BA64B89526CC`；Python 资源组 14/14、前端 22/22 与 production
  build GREEN。该调用只读安装文件，没有启动、连接或操作 CK3；
- 新增 load-configuration MCP 后，普通 Python 聚焦测试 5 项通过、其中官方 SDK 用例按环境跳过；安装 MCP SDK 2.0.0 的
  专用环境 5/5 通过，并验证 tool schema 拒绝未知字段。对当前真实用户目录的官方 MCP 调用列出 76 个工具并返回
  `enabled_mod_count=0`、`disabled_dlcs=[]`、上述 38 bytes/SHA-256；Quarkus REST 映射 6/6、前端 19/19 和 production
  build GREEN。该次调用没有启动、连接或操作 CK3，也没有读取启动器 SQLite；
- 新增 configured catalog/asset MCP 后，load/configured 两组在官方 MCP SDK 环境合计 10/10，Quarkus REST 8/8、
  前端 20/20 和 production build GREEN。真实用户目录的官方 MCP 调用列出 78 个工具；因当前配置启用模组为零，pattern
  configured catalog 正确返回 `total=0`、`manifest_count=0`，同时保持 `resource_merge_applied=false`、
  `load_order_precedence_applied=false`。双模组夹具另外验证同名候选保留而不选胜者、配置顺序投影、opaque ID DDS 读取、
  配置变更令旧 ID 失效；随后同组又补齐 ZIP archive 中 manifest/DDS 的有界直读，archive 不再需要落盘解压；
- 新增 installed-DLC-sources MCP 后，真实安装的官方 MCP 调用列出 79 个工具并读取 29 份 `.dlc` 描述符，九类 CoA
  内容目录命中 0、TXT/DDS 均为 0；四组离线资源 MCP 21/21、Quarkus 9/9、前端 23/23 与 production build GREEN。
  全过程只读本地安装文件，不启动或连接 CK3；
- Web 编辑器随后复用已达 `production-live` 的 `ck3_query_loaded_feature_manifest_v1`：Quarkus 有界白名单、绑定
  `expected_revision` 的 REST 映射和 Vue typed client/UI 已接通。该增量只提升到 `mcp-static-ready`；既有 primitive 的原生 live
  证据不等于这次新增浏览器按钮已经完成 live 点击验收，也不补写 entitlement 或 CoA resource winner。聚焦验证为 Quarkus
  10/10、Vitest 25/25、前端 production build 与 Quarkus package GREEN；
- CK3 frontend exact-build 握手：已真实取得，并广告新 capability；
- 原生 frontend MCP 导航已在 2026-09-13 达到 `production-live primitive`：官方 MCP SDK 闭环为
  `query(main_menu) → activate-frontend-new-game-v1 → query(bookmarks)`，动作的十项检查全为 true，且明确为零 OCR、零键盘、零鼠标；
  artifact `mcp-frontend-route-live3.json` 为 408,936 bytes，SHA-256
  `1EBBFA6052967E02F2C929CDD11A76A312B75F85487E9B65DE0158CA7C14DDD5`，受管 CK3 清理与 Steam 离线状态均已验证；
- 隔离 attempt 5 补齐 `frontend_snapshot` 绑定；attempt 6 暴露剪贴板函数槽的瞬时初始化状态；attempt 8 又证明
  gameplay 生命周期门禁会让角色设计器永远无法安装 hook。现在 hook 在 exact adapter 选定后即于 frontend 启动，瞬时槽缺失仍在
  heartbeat 延迟重试；精确构建或入口身份失败保持永久拒绝。
- attempt 8 在完整纹章编辑器执行 27 条原生 probe 请求：25 条不同载荷加 2 条重复/应用复核，另有前后 capability 与 snapshot；
  hook 诊断最终为 `installed=true`、`failure=0`、`executed_requests=27`。会话绑定 CK3 PID `11348`、snapshot `native:3`、
  public revision `4`、connection generation `1`，结束时 `cleanup_proven=true` 且进程树为零。
- attempt 8 的 LF-only 多行载荷真实暴露 `CF_UNICODETEXT` 回读会转为 CRLF；同一载荷改用 CRLF 后为 `detected`。
  MCP 合同随后补成调用方换行规范化，避免把有效语法误报成 `clipboard_readback_mismatch`。

### 3.4 2026-09-13 同进程 canonical round-trip

隔离的 CK3 `1.19.0.6` 会话绑定 PID `23008`、snapshot `native:3`、public revision `4`、native revision `3`、
connection generation `1`。导航截图只用于进入完整纹章设计器；以下判断全部来自 MCP 的原生 reader/Copy 回调与结构化结果。

送入 `ck3_probe_coat_of_arms_source_v1(apply=true)` 的确定性载荷覆盖 pattern、根级三色、一个 colored emblem、
emblem 三色以及 position/scale/rotation/depth：

```text
coa = {
    pattern = "pattern_solid.dds"
    color1 = blue
    color2 = yellow
    color3 = white
    colored_emblem = {
        texture = "ce_fleur.dds"
        color1 = red
        color2 = black
        color3 = white
        instance = {
            position = { 0.250000 0.650000 }
            scale = { 0.420000 0.420000 }
            rotation = 17
            depth = 3
        }
    }
}
```

第一次 apply 返回 `status=applied`、`detected=true`、`designer_observed=true`、`applied=true`。紧接着原生 Copy
返回 327 bytes 的 canonical 源码，SHA-256 为
`9F84F667B413D2BA24FA101A28D6F455AD93B638F90D9C2A21A91EF264B93C93`。可观察到引擎把 outer key 改为
`coa_rd_dynasty_2974550562`，规范化空白和字段顺序，并把 `depth=3` 写成 `depth=3.000000`。

把这 327 bytes 原样 reapply 后再次 Copy，第二次仍返回完全相同的 327 bytes 与 SHA-256；两个 probe 均为 `applied`，
两个 export 均为 `exported`。因此上述字段组合在该 exact build 上已经形成同会话 canonical fixed point。该结果不证明
跨会话 outer key 恒定，不证明未包含字段的 copy-back 规则，也不等于点击上层 Finish 或保存进角色/王朝。

本轮 fresh bridge 为 2,636,800 bytes，SHA-256
`721337A077F71BEFCE42D6F157CDE4B01C16DA174D0D6E8DBEF5CD3F151DF601`。artifact 记录一次加载期 snapshot
`native game state is not available yet`，随后 snapshot、apply、export、reapply、export 全部成功；结束时
`exit_reason=stop`、`cleanup_proven=true`、`tree_gone=true`，没有遗留 CK3 进程。

### 3.5 2026-09-13 浏览器到 CK3 的 MCP live 闭环

在上一节原生 fixed point 之后，又以仓库 commit `8bbff3039248db03507bed43f73e963952b051ef` 启动独立 CK3
`1.19.0.6` 会话和正式构建的前后端。真实无头 Edge 打开 `http://localhost:5173/`，按可见按钮文字依次点击“连接”、
“应用到设计器”和“从 CK3 读取”。浏览器自身记录到 5 次实际 fetch：3 次
`GET /api/ck3/coat-of-arms/session`、1 次 `POST /api/ck3/coat-of-arms/probe`、1 次
`POST /api/ck3/coat-of-arms/export`，全部为 HTTP 200。链路为：

```text
Vue 3 UI
  → Quarkus REST
  → MCP Java SDK 2.0.1 stdio client
  → Python MCP server
  → named pipe native bridge
  → CK3 CoatOfArmsDesigner
```

会话精确绑定 PID `17168`、snapshot `native:1`、public revision `2`、native revision `1`、connection generation `1`；
`map_ready=true`，designer hook 为 `installed=true`、`failure=0`。送入 UI 的 599-byte CRLF 文本 SHA-256 为
`C0B71A1D085ED4114CABF5ED1CC32EDF6C44D2AB847D37FA13013A0505EBE67E`，覆盖：

- `rgb { 32 64 160 }` typed color；
- 单值 `mask = { 1 }`；
- 两个重复 `instance`；
- 小数 position/scale/depth、正负 rotation，以及第二实例的负 X scale。

probe 返回 `status=applied`、`detected=true`、`designer_observed=true`、`applied=true`。随后 export 返回
`status=exported`、`designer_observed=true`、`copy_invoked=true`、`clipboard_read=true`。引擎写回 483-byte CRLF
canonical 源码，SHA-256 为 `6860C20BB90C74C017F12B7F3F6A275A49F4FE5A5F97C23E00AF9C7E1F55E1D5`；可观察到：

- outer key 改写为 `coa_rd_dynasty_1110059313`；
- `mask = { 1 }` 扩写为 `mask={ 1 0 0 }`；
- position、scale 和 depth 规范化为六位小数；
- 两个 instance、第二实例的负 X scale 与两种 rotation 均保留。

export 结果被同一个 Vue 页面重新解析并写回 textarea，诊断列表为空；浏览器 DOM 按 Web 规则把 CRLF 规范为 LF，因而页面内
文本为 455 bytes、SHA-256 `9F1E57C3075989E9A74BBF478116258C645DB262C328B0788957697283D1729C`。这不是引擎输出发生漂移，
而是 textarea 的换行表示不同；REST 响应中仍保留原始 483-byte CRLF 源码及其 hash。

浏览器链路 artifact 为
`artifacts/coa-clipboard-probe-2026-09-08/browser-quarkus-mcp-live-e2e1.json`，54,897 bytes，SHA-256
`DB491DA4E37D1DB26DAA9EEED8D577E73A9D6547FC382D2A85E8F5C0C407DAF6`。进程宿主 artifact 为同目录
`mcp-rest-live-host1.json`，2,581 bytes，SHA-256
`F1C933ADD15126A0AFE61A51CD47BA09D814EA6AE0D954C052884974F08A38F0`；它绑定本轮 fresh bridge 2,639,360 bytes、
SHA-256 `3B2B55F2B931D2FB8424B108F7954478B158C796005403F992F6A11A20D4917D`，并在退出时证明
`exit_reason=stop`、`cleanup_proven=true`、`tree_gone=true`。两份运行 artifact 按过程证据政策保留在本机、不提交 Git。

这把当前编辑器的实证状态提升为 `browser-mcp-live`。它仍只改变 designer working state；没有点击上层 Finish，不能声称
保存进角色/王朝或跨存档持久化。它也没有闭合运行时 DLC/mod effective registry、CK3 原生像素回读，或任意未列入矩阵的语法。

### 3.6 前端导航 MCP 补完与历史偏差

2026-09-13 的 `matrix3` 尝试在 MCP 尚不能识别/操作 CK3 开局前页面时，错误复用了鼠标/键盘导航链。这与本任务已经明确的
“MCP 欠缺时优先补 MCP”原则冲突。该 attempt 已停止且不得作为能力证据：

- artifact：`artifacts/coa-clipboard-probe-2026-09-08/mcp-live-matrix3.json`；
- 大小：2,686 bytes；SHA-256：
  `E529C7DFE24BE22830D2A3D5535C9AF7FF0F1F2145DF8A3FD3982D84F32C4914`；
- `commands=[]`，没有发出任何 CoA MCP 命令；
- `exit_reason=stop`、`cleanup_proven=true`、`tree_gone=true`，没有残留 CK3/host/watchdog 进程；
- 它只证明导航 harness 失败，不是任何语法的 RED/GREEN。

随后新增的 MCP v1 首片完全不使用屏幕解释或合成输入：

```text
ck3_query_frontend_gui_route_v1()
  -> unavailable | main_menu | bookmarks | lobby | ruler_designer | coat_of_arms_designer

ck3_activate_frontend_new_game_v1()
  -> 仅在 main_menu 解析固定 new_game_button
  -> 调用 CK3 原生 CPdxGuiShortcutManager 路径
  -> 再独立查询，只有观察到 bookmarks 才返回 verified
```

原生 DLL 在 exact SDL/CK3 application-main pump 中重新解析当前 GUI owner tree；传输层不能提供控件指针、控件名或回调地址。
`new_game_button` 也必须同时满足 runtime name、可见、可用、GUI context、button vtable、callback group 与 modal admission。
动作调用本身只产生 `acknowledged_verification_pending`，Python driver 必须独立看到路由从 `main_menu` 变为 `bookmarks`，
才投影 `postcondition_verified=true`。公开结果固定声明 `uses_ocr=false`、`uses_keyboard=false`、`uses_mouse=false`。

截至 2026-09-14，`main_menu → bookmarks → lobby 随机可玩角色 → ruler_designer → coat_of_arms_designer` 已由官方 MCP 和独立 route/tree 后置条件实机闭合为
`production-live primitive`；先前聚焦 inspector 还证明 lobby 默认角色设计器按钮在未选角时 disabled。最初尝试把书签人物选择与
`Pick Any` 串联是错误的状态模型：原版书签卡走 `GameSetup.SetSelectedCharacter`/`GameSetup.StartGame`，而 `Pick Any` 走
`GameSetup.OnCustomStart` 打开自由选择 lobby。三份失败 attempt 已保留，不能算语法或设计器能力证据。

修正后的 MCP 在 lobby 内使用已由 live tree 和原版源码共同识别的固定无名按钮 `4/0/1/0/1`，其回调为
`SetRandomPlayableObserverCharacter`；选角后必须独立观察默认角色设计器按钮 `3/0/2/3` 变为 enabled，才允许继续。
该替代动作与 `lobby → ruler_designer` 已实机 GREEN。新 tree 将 `dynasty_house` 固定在
`0/0/0/0/0/0/0/3`，原版 `window_ruler_designer.gui:514-548` 再把其 leaf
`0/0/0/0/0/0/0/3/1/0/1` 绑定为 `OpenDynastyCoatOfArmsDesigner`。对应零输入 MCP 只有独立观察
`coat_of_arms_designer` route 与可见 `coat_of_arms_page` 才会返回 verified；最终实机 artifact
`mcp-frontend-route-coa-page-live5.json`（1,185,843 bytes，SHA-256
`6BE30B3C356CCE22D279FD1906BAFE6474451D7FFCB5EF2229E5B538A0106103`）已取得 verified，并观察到可见、enabled 的
`coat_of_arms_page`、`dynasty_detail_input` 与 `dynasty_finish_button`，因此该段现为 `production-live primitive`。
`open_kaishek` 没有前端 GUI/CoA domain，预验证为 `not-applicable`；不得用鼠标、键盘或 OCR 绕过。

### 3.7 王朝 Finish 与提交后重开往返

原版 `window_ruler_designer.gui:3342-3348` 的 `dynasty_finish_button` 调用
`RulerDesignerWindow.FinishDynastyCoatOfArmsDesigner`，随后清除拥有独立家徽页的
`coat_of_arms_customization_open`。据此实现的 `ck3_commit_frontend_dynasty_coat_of_arms_v1()` 是零参数闭合工具：原生层只从
实时 `ruler_designer` owner tree 解析固定名字；Python 层还要求 child path `0/2/1/1`、可见、enabled、动作前 route 为
`coat_of_arms_designer`、动作后 route 为 `ruler_designer`。任何一项不符都 fail closed。

2026-09-14 的唯一受管实机 attempt 先应用一份确定纹章并原生 Copy，再调用该 Finish，随后用既有固定动作重开王朝家徽页并
再次原生 Copy。动作返回 `status=verified`、`action=commit_dynasty_coat_of_arms`、`postcondition_verified=true`；两次 Copy
均为 330 bytes、SHA-256 `4769FD42836E68FA35DC07FBA23BEABCC589E5A33087314F1D6287E5C53C305A`，原文逐字节相等。
artifact `mcp-frontend-dynasty-finish-roundtrip-live7.json` 为 1,594,848 bytes，SHA-256
`6569F652DB057520EB24A2DB3CC9FE2CD8F8C2A6BE8E76597F8F244BE6EFCEB8`，绑定仓库
`8231b2f1139970d4c3a8eb8191309255b61784c3` 和 exact CK3 `1.19.0.6`。MCP-only、OCR/keyboard/mouse=false、
Steam 离线、cleanup、进程树清零与双锁释放均为 GREEN。

这证明的是“家徽设计器 working state 经王朝 Finish 提交回当前角色设计器，且可重开得到相同 canonical CoA”。它没有点击
角色设计器最外层的创建/完成按钮，没有进入一局游戏，也没有重载存档，所以不得扩张为战役实体或跨存档持久化结论。

## 4. 原版实际调用链

### 4.1 GUI 只调用原生 designer

本机原版文件显示：

- `game/gui/window_ruler_designer.gui:3279-3315` 用
  `RulerDesignerWindow.GetCoatOfArmsDesigner` 实例化纹章设计器；
- `game/gui/shared/coa_designer.gui:482-493` 的复制按钮调用
  `CoatOfArmsDesigner.OnCopyToClipboard`；
- 同文件 `:504-523` 的粘贴按钮和预览绑定
  `CanPasteFromClipboard`、`OnPasteFromClipboard`、`GetPastePreviewCoA.GetCoA`；
- 同文件 `:589-595` 的 PNG 保存按钮单独调用
  `SaveCoatOfArmsImageToDisk(345, 345)`。

保存 PNG 是另一个原生按钮能力，不能由剪贴板载荷里的“代码”调用。

### 4.2 outer update 与内部 reader

当前构建的真实控制流是：

```text
B73500(designer)
  -> 读取 Windows clipboard
  -> D995A0(parser-result, UTF-8 view)  专用 CoA reader
  -> 物化 render description
  -> 保存 CanPaste / candidate / preview

B71F00(designer)
  -> 把当前 paste preview 写入 designer working state

B71E50(designer)
  -> 序列化当前设计并写回 clipboard
```

必须特别区分：RVA `0xD995A0` 的 RCX 是 outer caller 栈上的临时 parser-result，不是 designer，也不能在函数返回后缓存。
MCP 原生实现挂在 RVA `0xB73500` 的 19-byte 完整指令边界，在同一次自然 UI-thread callback 内完成
写入、回读、原生 update、字段读取和可选 paste；worker 从不保存 designer 指针。

当前 exact-build 字段：

| 偏移 | 含义 |
|---|---|
| `designer+0xE8` | 当前 active outer CoA index |
| `designer+0xEC` | working design changed |
| `designer+0xEF` | `CanPasteFromClipboard` |
| `designer+0xF0` | 当前解析候选 outer index |
| `designer+0xF4` | clipboard polling timer，约 0.16 秒 |
| `designer+0x100` | preview CoA handle |

apply 的后置条件是 `+0xEC == 1` 且 `+0xE8 == paste 前的 +0xF0`。

这条链中没有 effect VM、trigger evaluator、event queue、console dispatcher 或 GUI expression evaluator 的调用。

### 4.3 随游戏发布的渲染公式

渲染不是只能靠画面猜测。exact 1.19.0.6 安装同时发布了 Clausewitz `utility.fxh`、Jomini CoA `.fxh` 和 game CoA
`.shader` 源文件，可以直接证明：

- pattern 以 `FallbackColor` 起步，依次按纹理 R/G/B 向 `Color1/2/3` 做 `lerp`；
- colored emblem 以 `Color1` 起步，按纹理 G 混入 `Color2`，再按 R 混入 `Color3`；纹理 B 经 `GetOverlay(..., 1.0)`
  提供明暗，纹理 alpha 控制透明度；
- pattern mask 先变为 `r=clamp(r-g-b)`、`g=clamp(g-b)`、`b=b`，再与 `MaskColor` 相乘并求饱和和；
- 非 portrait 路径还用全局 `coa_mask_texture.dds` 的 B 通道做 0.2 强度 overlay，emblem alpha 再乘其 G 通道×2；
- instance 顶点变换顺序为负 scale 镜像、rotation、scale、position；最终使用 `src_alpha / inv_src_alpha` 混合；
- Clausewitz 的 `GetOverlay` 函数体也在安装目录中：为兼容旧行为，它调用 `Overlay(OverlayColor, Color)`，即特意交换通常理解的
  base/overlay 参数，不能用普通 CSS blend mode 直接替代。

这些是静态源码事实，不等于浏览器已经得到 CK3 GPU 的逐像素输出；特别是 `FallbackColor` 的 CPU 侧绑定、采样边界和 GPU
色彩空间仍需以后通过原生像素读取闭合。

### 4.4 王朝 Finish 是独立的上层提交路径

剪贴板 reader、paste 与 Copy 只操作 `CoatOfArmsDesigner` 的 working state；提交回角色设计器由
`RulerDesignerWindow.FinishDynastyCoatOfArmsDesigner` 单独负责。Web 编辑器因此把“应用到设计器”和“提交回角色设计器”做成
两个不同按钮与两个不同 MCP 合同：前者允许继续编辑/回读，后者关闭家徽页并验证回到 `ruler_designer`。纹章载荷本身不能调用
这个 Finish，也不能把任意 GUI expression 或 effect 塞进文本来取得同等能力。

## 5. 哪些语法能导入并实际生效

### 5.1 稳定核心

| 层级 | 语法 | 实际含义 | 当前等级 |
|---|---|---|---|
| 外层 | `name = { ... }` | 定义候选纹章；普通标识符、`coa` 和数字 key 均被接受 | `mcp-detected` |
| 根 | `pattern = "pattern_*.dds"` | 选择底图；reader 接受名字不等于资源一定存在 | `mcp-applied` |
| 根 | `color1`、`color2`、`color3` | 底图通道颜色 | `mcp-applied` |
| 根 | 重复 `colored_emblem = { ... }` | 添加一个或多个彩色图案层 | `mcp-applied` |
| 根 | `textured_emblem = { ... }` | 受限的纹理图案层；`_default.dds` 已应用并由原生 Copy 保留 | `mcp-applied` |
| emblem | `texture = "ce_*.dds"` | 选择 colored emblem 纹理；资源存在性需另验 | `mcp-applied` |
| emblem | `color1`、`color2`、`color3` | emblem 通道颜色 | `mcp-applied` |
| emblem | `mask = { ... }` | pattern 分区遮罩；`{ 1 }` 与 `{ 1 2 3 }` 均已应用 | `mcp-applied` |
| emblem | 重复 `instance = { ... }` | 同一纹理的多个实例 | `mcp-applied` |
| instance | `position = { x y }` | 归一化位置 | `mcp-applied` |
| instance | `scale = { x y }` | X/Y 缩放；负值可镜像 | `mcp-applied` |
| instance | `rotation = number` | 旋转；可为小数或负数 | `mcp-applied` |
| instance | `depth = number` | 层叠顺序参数 | `mcp-applied` |

原版直接语料可见于：

- `common/coat_of_arms/coat_of_arms/90_dynasties.txt`：多 emblem、多 instance、浮点值与 RGB；
- `common/coat_of_arms/coat_of_arms/01_landed_titles.txt`：mask 与负 scale；
- `common/coat_of_arms/coat_of_arms/01_holy_order_coas.txt`：rotation。

这些核心字段在一个完整载荷中共同取得 `status=applied`；这证明原版 paste 已把候选写进 designer working state，
但不单独证明每个字段的最终像素值，也不代替资源存在性检查。

exact 1.19.0.6 原版 `common/coat_of_arms` 语料中的 mask 载荷去重后只有 `{ 1 }`、`{ 2 }`、`{ 2 3 }`；随附
shader 将 pattern mask 明确拆为 R/G/B 三通道，而 MCP 另已应用 `{ 1 2 3 }`。该全通道形态在原生 Copy 中被省略，表明它是默认全选的规范化冗余值，而非拒绝。因此编辑器的确定性 mask 输入只接受整数分区
索引 1、2、3（允许组合）；小数、非数值、0 和大于 3 的值不在当前证据子集内，必须阻止导出，不能静默过滤。

### 5.2 字面量和排版

```text
color1 = "blue"              # quoted string
color2 = yellow              # identifier
color3 = rgb { 237 156 227 } # typed color block
position = { 0.5 0.25 }      # number list
scale = { -0.7 0.7 }         # negative and decimal
rotation = -150
depth = 1.01
```

原版最终纹章语料使用引号/不引号字符串、整数、小数、负数、空白和紧凑 `key=value`。MCP 实机已经确认：

- `#` 行尾注释和 `hsv { ... }` 可被 reader 接受；
- 引号/不引号颜色、`rgb { ... }`、整数、小数、负数与紧凑等号可被接受；
- 重复 `colored_emblem` 与重复 `instance` 可共同应用；
- 多行源码经 MCP 统一为 CRLF 后再写入 Windows 剪贴板。

2026-09-14 的扩展矩阵已将这两条从早期辅助观察升级为原生 MCP apply/Copy 证据：输入中的注释未出现在 Copy 源码中，
`hsv { 0.60 0.75 0.80 }` 被规范化为 `rgb { 51 112 204 }`。

### 5.3 推荐的最小输出

```text
coa = {
    pattern = "pattern_solid.dds"
    color1 = "blue"

    colored_emblem = {
        texture = "ce_martlet.dds"
        color1 = "yellow"

        instance = {
            position = { 0.5 0.5 }
            scale = { 0.7 0.7 }
            rotation = 0
            depth = 1
        }
    }
}
```

### 5.4 多实例、镜像和 RGB

```text
coa = {
    pattern = "pattern_solid.dds"
    color1 = rgb { 32 64 160 }

    colored_emblem = {
        texture = "ce_martlet.dds"
        color1 = yellow
        mask = { 1 }

        instance = {
            position = { 0.30 0.50 }
            scale = { 0.35 0.35 }
            rotation = -20
            depth = 1.0
        }
        instance = {
            position = { 0.70 0.50 }
            scale = { -0.35 0.35 }
            rotation = 20
            depth = 2.0
        }
    }
}
```

### 5.5 扩展和边缘行为

| 输入 | 已知行为 | 产品建议 |
|---|---|---|
| `textured_emblem` | `_default.dds` 载荷为 `mcp-applied`，原生 Copy 保留 `texture` | 独立受限面板只保真 `texture` 的解析/编辑/导出；不生成未验证字段，也不把原始 DDS 冒充最终合成预览 |
| 普通或数字 outer key | `custom_name={...}` 与 `79={...}` 均为 `mcp-detected` | 导出仍固定用 `coa`，减少无意义差异 |
| 多个顶层对象 | `mcp-applied`；原生 Copy 证明采用第一个 | 仍拒绝默认导出，避免静默丢弃后续对象 |
| 空块、无 pattern | `coa={}` 为 `mcp-applied`，Copy 返回空 body | 允许解析，编辑器载入可编辑默认值并警告非字节保真 |
| 不存在的 pattern/emblem texture 名 | 两类载荷均为 `mcp-detected` | 将“reader 接受”和“资源存在”分开校验 |
| body-only，无 outer wrapper | 精确载荷为 `not_detected` | v1 必须要求 wrapper |
| 重复普通标量 | `mcp-applied`；两个 `color1` 的原生 Copy 只保留最后的 `red` | 与 CK3 一致取最后值，给出非阻断警告 |
| `parent = c_england` | 与普通字段共存或单独存在均为 `mcp-applied`；Copy 保留 `parent="c_england"` | 保真解析/编辑/导出引用；警告继承后的最终像素尚未回读 |
| 静态 `@chosen = blue` + `color1=@chosen` | 为 `mcp-applied`；原生 Copy 展开为 `color1=blue`，不证明游戏 scope 变量能力 | 可导入，默认导出展开成确定字面量 |
| 任意未知键 | 同一载荷连续两次均为 `not_detected` | 报错 |
| `color4` | 根级与 emblem 级组合载荷为 `not_detected` | 不进 v1 |

### 5.6 attempt 8 精确载荷矩阵

下表全部来自同一 exact-build、同一 snapshot/revision 的 MCP 会话；`detected` 只表示原版 reader 生成了有效 preview，
`applied` 才表示继续调用了原版 paste。

| 载荷/特征 | 结果 |
|---|---|
| `this is not coa syntax` | `not_detected` |
| `coa={ pattern="pattern_solid.dds" color1=blue }` | `detected` |
| 第 5.4 节的 RGB、三通道、多实例、负 scale、rotation、depth 组合 | `applied` |
| 在一个成功载荷后输入 `this is broken {` | `not_detected`，排除了残留 `CanPaste` 假阳性 |
| `custom_name={ # comment ... color1=hsv { ... } }`（CRLF） | `detected` |
| `pattern=... color1=blue`（无 outer wrapper） | `not_detected` |
| `coa={}`、无 pattern、数字 outer key | `detected` |
| 两个顶层对象 | `detected`，采用规则未解析 |
| `textured_emblem={ texture="_default.dds" }` | `detected` |
| 未知键、`color4` | `not_detected` |
| `effect={ add_gold=1000 }`、`trigger={ always=yes }`、`event={ id=test.1 }` | 均为 `not_detected` |
| `color1=list "normal_colors"` | `not_detected` |
| 不存在的 pattern texture、不存在的 emblem texture | 均为 `detected`，证明资源校验是另一层 |
| 重复 `color1` | `detected`，优先级未解析 |
| `@chosen=blue ... color1=@chosen` | `applied` |
| `parent=c_england`（与字段共存或单独存在） | `detected`，继承语义未解析 |
| `mask={ 1 2 3 }` + 完整 instance | `detected` |

### 5.7 2026-09-14 原生 apply/Copy 扩展矩阵

受管 runner 在同一个 CK3 `1.19.0.6` 进程、同一 Frontend snapshot revision `4` 上通过官方 MCP 完成了冻结的 15 例矩阵。
10 个正例全部 `detected=true` 且 `status=applied`；5 个负例全部 `not_detected`，每个负例前后的原生 Copy 源码 SHA-256 不变。

| 精确载荷 | detect/apply | 原生 Copy 结果 |
|---|---|---|
| 核心 pattern/color/emblem/两个 instance/`mask={1}` | `applied` | 字段保留；mask 规范化为 `{ 1 0 0 }`，浮点输出固定六位 |
| `@chosen=blue` + `color1=@chosen` | `applied` | 变量声明/引用不保留，输出 `color1=blue` |
| `color1=blue color1=red` | `applied` | 输出 `color1=red`；后值优先 |
| `first={color1=blue} second={color1=red}` | `applied` | 输出 `color1=blue`；第一个 outer 优先 |
| `parent=c_england color1=blue` | `applied` | 保留 `parent="c_england"` 与 `color1=blue` |
| `parent=c_england` | `applied` | 只保留 `parent="c_england"`，未展开继承内容 |
| 注释 + `hsv { 0.60 0.75 0.80 }` | `applied` | 注释丢弃，颜色输出 `rgb { 51 112 204 }` |
| `textured_emblem={texture="_default.dds"}` | `applied` | 保留 textured-emblem 与 texture |
| `coa={}` | `applied` | 输出空 body，不自动填充 pattern/color |
| `mask={1 2 3}` + instance 默认值 | `applied` | 省略全通道 mask，同时省略默认 position/rotation |
| 普通文本、body-only、`effect`、template `list`、未知键 | `not_detected` | 当前 designer working state 的 Copy SHA-256 全部不变 |

证据 artifact 为 `artifacts/coa-clipboard-probe-2026-09-08/mcp-frontend-route-coa-syntax-matrix-live6.json`，1,130,288 bytes，
SHA-256 `0C5F2F88765224219F7F824DD9F1215E4D2B9EBAB024F0677B5F7506D8F5F84A`。它记录 `mcp_only=true`、OCR/键盘/鼠标全为 false、
Steam 离线、共享锁释放、`cleanup_proven=true` 与 `tree_gone=true`。这些结论仍只绑定 exact build 与 designer working state，不等于上层 Finish/存档持久化或原生像素一致。

## 6. 哪些 CK3 语法不能在这里执行

| 语法族 | 能否执行 | 结论依据 |
|---|---:|---|
| 本文第 5 节的 render-description 字段 | 是，只产生纹章数据语义 | 专用 CoA reader/renderer |
| `effect = { ... }`、scripted effect | 否 | 无 effect VM；精确 MCP 载荷为 `not_detected` |
| `trigger = { ... }` | 否 | 无 scope/trigger evaluator；精确 MCP 载荷为 `not_detected` |
| `event`、`decision`、`interaction` | 否 | `event` 精确 MCP 载荷为 `not_detected`，且无对应数据库或队列调用 |
| `script_value`、scope link、变量操作 | 否 | render description 没有游戏 scope；静态 `@name=value` 文本替换虽可接受，但不是 scope 变量读写 |
| GUI 表达式、`GetScriptedGui(...).Execute(...)` | 否 | 输入没有进入 GUI 表达式解释器 |
| console command、`run file.txt` | 否 | 无控制台 dispatcher |
| localization 表达式 | 否 | 无 loc 求值路径 |
| template 的 `list`、weighted list、trigger | 否 | 精确 MCP `list "normal_colors"` 载荷为 `not_detected`；这是随机生成阶段 DSL |
| include、任意磁盘读写、进程或网络调用 | 否 | 只解析内存文本并按名字查已注册 CoA 资源 |

反例：

```text
coa = {
    pattern = "pattern_solid.dds"
    color1 = blue
    effect = { add_gold = 1000 }
}
```

这不会给 `add_gold` 一个执行上下文。当前 MCP 实机中该输入没有有效 preview；即使将来发现 reader 会忽略某个未知字段，
那也只证明 reader 容错，不能证明字段被执行。

## 7. 为什么模板 DSL 不属于剪贴板能力

`common/coat_of_arms/template_lists` 和 `99_coa_designer_templates.txt` 属于随机生成/模板阶段，例如：

```text
template = {
    coa_designer_blank_default = {
        pattern = "pattern_solid.dds"
        color1 = list "normal_colors"
        color2 = list "metal_colors"
    }
}
```

它不是已经物化的 `SCoatOfArmsRenderDescription`。下列语法不应由 Web 编辑器原样导出到剪贴板：

- `template = { ... }`；
- `list "normal_colors"` 与 weighted texture list；
- `special_selection`、template trigger；
- `@变量` 声明与引用（简单静态替换会接受甚至应用，但产品应先展开为确定字面量）。

`parent=<database id>` 已被证明是直接 render-description 字段，可应用并被 Copy 保留，因此不再归入 template DSL。
但 Copy 不会展开它，引用的对象是否存在与继承后像素仍是独立验证层。Web 端若要提供随机生成，应在自己的数据模型中完成选择，再导出确定的纹理、颜色与实例。

## 8. 目前 MCP 能力仍缺什么

本轮已实机闭合“输入源码 → 原生检测/预览 → 应用 → 原生 Copy/export → 原样再应用 → 稳定再次导出”，并补齐 frontend
生命周期与 Windows 换行规范化。基础游戏 designer manifest 资源目录也已通过离线 MCP 工具分页暴露；运行中 CK3 的完整
effective feature 与 script `has_dlc` truth 已有 production-live 原生 primitive，并接入编辑器。前端路由的
`main_menu → bookmarks → lobby 随机可玩角色 → ruler_designer → coat_of_arms_designer` 已达到
`production-live primitive`；固定王朝 Finish 及提交后重开/Copy 一致性也已达到 `mcp-committed`。仍未通过 MCP 闭合的能力有：

- 读取 CK3 原生 preview 的最终像素或直接导出 PNG（浏览器已能按随附 shader 源码离线合成，但不替代 native pixel）；
- 完成整个角色创建，并验证进入战役后实际王朝/家族/头衔状态及跨存档持久化；
- 枚举游戏当前运行时实际注册且已合并 DLC/mod override 的 pattern/emblem/color 资源；现有 runtime feature truth 只证明
  gameplay gate，不提供 CoA VFS/registry winner；
- 跨 CK3 build 自动适配 RVA 与字段。

扩展矩阵已按第 5.7 节完成原生实机执行，因此重复标量、多 outer object、`parent`、静态变量、注释/HSV、
`textured_emblem`、空对象和三通道 mask 已从“只检测/待解析”升级为精确 apply/Copy 结论。body-only、effect、template list 与未知键
的拒绝则同时得到“未修改 designer working state”的前后 SHA 证据。

按 MCP-first 原则，后续若需要运行时合并资源清单或截图无关的视觉验收，应继续补这些原生/MCP primitive，
而不是用 OCR 猜文字、按钮状态或 copy-back 内容。

2026-09-15 已补出并实机验证两个 `production-live primitive`：专用树检查只允许从实时 `ruler_designer` 中解析可见、enabled 的
`coat_of_arms_page`，再以该对象为根做 512 项有界只读遍历；固定自定义模式动作只允许原版
`coa_designer.gui:351-437` 的两个互斥 `button_custom_mode` 叶节点，且 Python 后置条件要求同一路由中的
`coa_designer_tabs`、`background_panel`、`patterns` 与 `patterns_scrollbox` 全部可见、enabled。调用方不能传入控件名、child path
或指针。受管 official-MCP 实机证据为
`artifacts/coa-clipboard-probe-2026-09-08/mcp-frontend-coa-custom-mode-census-live8.json`：2,331,467 bytes，SHA-256
`72542CE89CE33A76A05D35722CCF301994533D409E4AD59D4F497D58760735FD`，绑定
`d9de68b1d41d15922852c1db398df1a8e92ab12a`，所有十项 custom-mode 检查与完整进程树清理均为 GREEN，Steam 保持离线，零 OCR、
零键盘、零鼠标。

这次 scoped census 取得了一个重要但仍有限的运行时边界：512 项遍历在 `coat_of_arms_page` 根上截断；
`patterns_scrollbox` 下可枚举 10 个后代、3 个直接子项，其中固定网格容器
`0/3/0/2/1/1/2/0/0/0/0` 报告 `child_count=38`，但其 38 个 pattern item 尚未进入本次返回集。

2026-09-15 已沿 MCP 路线补完零输入 `ck3_inspect_frontend_coat_of_arms_pattern_grid_v1()`。原生层只从固定
`ruler_designer` 根解析完整路径 `0/2/0/3/0/2/1/1/2/0/0/0/0`，并逐级核对
`coat_of_arms_page → background_panel → patterns → patterns_scrollbox` 的 runtime name、可见性和 enabled；调用方不能提供
root、child path、指针或遍历上限。网格本身必须保持空 runtime name、可见且 enabled。底层为有界广度优先遍历，Python 合同进一步
要求根的 `child_count` 与深度 1 的 `0..N-1` 路径完全相等，因此不会再把“只读到 child_count”误报为“直接子项已枚举”。该链已贯通
原生桥、native driver/service、官方 MCP、Quarkus REST 与 TypeScript 客户端，并通过原生 `127/127` CTest；当前状态仍是
`mcp-static-ready / live=false`。必须再跑一轮受管 CK3 才能把新工具返回的 38 个直接子项提升为 live 事实；即使届时完整返回，
也不得把 GUI item 外推为完整资源 registry 或同名 DDS 的 VFS 最终胜者。

## 9. `coat_of_arms_editer_of_ck3` 的实现约束与当前状态

应用已经按指定目录名 `coat_of_arms_editer_of_ck3` 建立，采用 Vue 3 + Element Plus + TypeScript；
当前纯前端即可完成解析、结构化编辑和源码生成，不需要后端。

建议模型：

```text
CoatOfArms
├─ parent (optional database reference)
├─ pattern
├─ colors[1..3]
├─ coloredEmblems[]
│  ├─ texture / colors / mask
│  └─ instances[]: position / scale / rotation / depth
└─ texturedEmblems[]  (experimental)
```

当前首个可运行基线已经做到：

- parser 识别未知字段并给出带位置诊断，serializer 只输出稳定白名单；
- parser 拒绝未声明、循环或重复的静态 `@变量`，以及 wrapper 外的顶层标量/游离值；
- 结构化表单持续复核命名颜色或 `rgb`/`hsv` 三分量字面量、可打印 ASCII 资源名、有限数值与 128 KiB 原生输入上限；
  因而导入后再手工填入伪 CK3 tagged block 或非法数值也会阻止复制和原生 MCP 请求；
- mask 表单保留输入中的非法 token 并给出 error，只允许原版语料/shader/MCP 共同支持的整数分区索引 1、2、3；
- `src/domain/capabilityMatrix.ts` 把本报告第 5–7 节的保守子集投影成前端可见表格：每行固定语法、最小例子、
  `mcp-applied`/`mcp-detected`/`mcp-not-detected` 证据和 accept/warn/sanitize/reject 策略；测试要求可接受例子无 error、
  reject 例子必有 error，且静态变量确实从确定性输出中展开；
- 语法合法、资源存在、引擎检测、designer 应用是四个不同状态；
- 多顶层、body-only 和模板 DSL 默认拒绝；重复标量按已证实的后值优先规则导入并警告；
- 简单静态 `@变量` 在导入时展开，`parent` 作为受限 ASCII 数据库引用保真解析、编辑和导出；
- 导出固定使用 `coa` wrapper、已实机验证的字段白名单和 CRLF；
- 提供图层/实例结构化表单与浏览器近似预览，且明确不冒充 CK3 renderer；
- 基础游戏 pattern/emblem 目录已经接入结构化选择器，并可按名字筛选首批 200 个 emblem；
- 必要的 Quarkus 伴随服务使用官方 Java MCP SDK 连接现有 Python stdio server，前端可刷新 session revision、读取同帧
  runtime feature/script-DLC truth、通过固定动作打开王朝家徽页、执行原生 detect/apply、载入原生 Copy/export 返回源码，
  并通过另一项固定动作把王朝家徽提交回角色设计器；
  另有一个只读、限定 `coat_of_arms_page` 的树检查、一个固定自定义模式动作和一个固定 pattern 网格根检查，为后续从原版数据模型枚举资源建立入口；
  新 binding 端点从 `ck3_get_capabilities` 验证 exact native 连接，有 snapshot 时返回正 revision，无 snapshot 时返回 probe/export
  合同允许的 frontend `revision=0`，从而不再把 gameplay snapshot 错当作前端设计器的必需条件；
  伴随服务只允许十七个相关工具（capabilities + snapshot + 十四项 CoA 专用 MCP + 一个 runtime-feature MCP）；
- manifest-owned 单素材与 render-support 已接入浏览器：除 DXT1/DXT5 顶层 mip 解码外，还能解码 `_default.dds` 使用的
  无压缩 BGRA8 并在受限 `textured_emblem` 行内显示原始纹理；主路径按随游戏发布的 shader 源码合成三通道调色、mask、
  实例变换、surface detail 和 blend，仍明确不冒充 native GPU 像素完全一致。

尚未完成的下一阶段能力：

- 继续补 DLC/mod playset 合并与运行时注册证据；
- CK3 原生 PNG/像素验证 primitive，用于闭合浏览器源码模型与 native GPU 的差异；
- 解析/验证 textured emblem 的完整字段与最终合成路径；当前只闭合已实机应用并 Copy 保留的 `texture="_default.dds"` 形态以及素材原始像素。

浏览器无法直接启动本机 stdio MCP，因此已引入 Maven + Java + Quarkus 伴随服务。后端只负责 REST/MCP 会话转接与
本机资源索引，不承担“执行 CK3 脚本”的虚构能力；当前也没有 DDS 转换或素材缓存。

当前前端有 Vitest `43/43` parser/serializer/validator/capability-matrix/API/DDS/renderer 回归和 Vite production build 验收；
Quarkus REST 测试 `18/18` 且 Maven test GREEN。后续扩展仍以本文的原生 MCP 证据为协议来源，
不会把旧 UI 观察或第三方 parser 行为固化成 CK3 引擎事实。

## 10. 辅助参考边界

只读参考了 Nargodian 的
[CK3CoatOfArmsEditor 固定提交 `bace8d1`](https://github.com/Nargodian/CK3CoatOfArmsEditor/tree/bace8d1287bf98cb07da7be3ca7269f89a887be4)，
没有复制其代码、测试、资源、目录结构，也没有把 clone 放进本仓库。

- [parser](https://github.com/Nargodian/CK3CoatOfArmsEditor/blob/bace8d1287bf98cb07da7be3ca7269f89a887be4/editor/src/models/coa/_internal/coa_parser.py)
  只能说明第三方 AST 接受哪些 token；
- [model import](https://github.com/Nargodian/CK3CoatOfArmsEditor/blob/bace8d1287bf98cb07da7be3ca7269f89a887be4/editor/src/models/coa/serialization_mixin.py)
  是社区工具自己的字段消费逻辑；
- [instance import](https://github.com/Nargodian/CK3CoatOfArmsEditor/blob/bace8d1287bf98cb07da7be3ca7269f89a887be4/editor/src/models/coa/_internal/instance.py)
  只作 position/scale/rotation/depth 建模参考。

第三方 parser 接受文本，不证明 CK3 接受，更不证明 CK3 会执行 effect。该项目的 `##META##` 也是注释中的私有 round-trip 数据，
不是 CK3 纹章语法。

## 11. 可复核指纹

| 对象 | SHA-256 |
|---|---|
| `binaries/ck3.exe` | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| `game/gui/shared/coa_designer.gui` | `2F3B863A7FEA692D630825052426CCC674403D096C37DD470E63C923D2D356EC` |
| `game/gui/window_ruler_designer.gui` | `C5761FD395E0C3D7FDF320DDE41DA900928F0A2EB217524E25348CCCC07ABDC9` |
| 简中 CoA 本地化 | `448145B50EFE30E6C4712B1A41B66DD5A95BE15E63764707E4398ADD423B6EEB` |
| `90_dynasties.txt` | `633390574316C021734952A1F214F49C62BD27148D936FB9F3563E6602CD4` |
| `B73500..B7368B` outer clipboard update | `6E178A77E1992B09B17203373AC3DC3452644FEBB1CE270749056F41BA3DA9D5` |
| `B71E50..B71EF6` copy/export | `DD0EBE6E41946B21D2BBE301293BF60F88EB5489894535A950B5AD6F42200E4E` |
| `B71F00..B71FB3` paste | `1A8C4A85AFF86CB093FF7F203F7F5E4977F5683F805271AC55C45CD4B489DF99` |
| `D995A0..D99A0D` inner reader | `696BB6B97536366849ADA406F06610CF047752F31D1D9FED398B0364CF789FDD` |
| attempt 6 live artifact | `DF12B49B29227683DDB2637D587F5B1E8948395A1CAA85CC8A4B2BB3EE495786` |
| 09 月 09 日 `xar_ck3_bridge.dll`（2,462,208 bytes） | `297E8786C3D1834C640973755936679D60AF0C9DE2C8CECA8D2C66CE95F3C279` |
| attempt 7 live artifact（CK3 在菜单前以 `0xC0000374` 退出，无 probe 执行） | `81E73231272A64EB0AA9A4A0ABD15CDFD4B93BE73E34D000F5EE8047621E11AF` |
| attempt 8 MCP live artifact（27 条原生请求、cleanup GREEN） | `B40E16DD700EEB0FD0703B909955563F04D5810543D2E28D9D72E0DDE081CD2F` |
| attempt 8 `xar_ck3_bridge.dll`（2,507,776 bytes） | `EC534B8D4D3BFA16FCA9BCA8DA4DD2CF393019C86892AFAD0BCF372E541C59CD` |
| Copy/export static build `xar_ck3_bridge.dll`（2,551,808 bytes；rebase 后 exact master） | `F28BFFA0F82A6F9C51DC0E8491DE93578B443A00957F73E6B11BCB660C395FF8` |
| 09 月 13 日 MCP same-session round-trip artifact（26,521 bytes；cleanup GREEN） | `9EB7DC0AE1F7EBF2F7D5F8518DE948AACD929104AAFF7447B0B8375B19D0DE84` |
| 09 月 13 日 round-trip `xar_ck3_bridge.dll`（2,636,800 bytes） | `721337A077F71BEFCE42D6F157CDE4B01C16DA174D0D6E8DBEF5CD3F151DF601` |
| 09 月 14 日 15 例 MCP apply/Copy 矩阵（1,130,288 bytes；cleanup GREEN） | `0C5F2F88765224219F7F824DD9F1215E4D2B9EBAB024F0677B5F7506D8F5F84A` |
| 09 月 14 日矩阵 `xar_ck3_bridge.dll`（2,813,440 bytes；source `e2a05929`） | `412A9A869A1B4E43DFE6CCF521D43806FC10EDA24F9B934B76C242BA04B3582C` |
| 09 月 14 日矩阵 injector（39,936 bytes） | `4675729904ACC23A017998FC06583CF476FC073AD0790C43A6736FAA8437A237` |
| 09 月 14 日王朝 Finish 往返 artifact（1,594,848 bytes；cleanup GREEN；source `8231b2f1`） | `6569F652DB057520EB24A2DB3CC9FE2CD8F8C2A6BE8E76597F8F244BE6EFCEB8` |
| 09 月 14 日 Finish 往返 `xar_ck3_bridge.dll`（2,814,464 bytes） | `3B432B97F69392552BE3C6A2E5369FB228973FD73750CCD6EF9AB0316BD7664D` |
| 09 月 14 日 Finish 往返 injector（39,936 bytes） | `506F0A7E093AFEF2BDB39FF49C373964ED0950CD9582E66BAC6AE21713D833EE` |
| 09 月 15 日固定 pattern 网格 inspector 静态构建（2,818,560 bytes；`live=false`） | `2CEA58975B3ABF3B75453F4A85705B0BFC2DB999AD219E96F65E77B7BE47BB06` |
| `50_coa_designer_patterns.txt`（42 项/38 可见） | `3BAA46C11BD24E7D9F9F6D1DF3E51403D016AB4CAC7290A6541ED25561425B7B` |
| `50_coa_designer_emblems.txt`（1,578 项/1,576 可见） | `3D6529702F91FA352E07B0C64E4C33A88E5F86C2AAF0EF2D0CEB69CF6D600F3C` |
| `50_coa_designer_palettes.txt`（13 色） | `3AE2EA0F3B751D61C08A06408FA2EDA2ADC3FF6FBF204298D3D8CDC9613B87B4` |
| `coa_mask_texture.dds`（256×256 DXT1，43,832 bytes） | `5FA2A49DC59AEEBA19709B6BB3F9D0B017ACDE7DC576793705EAF85C7F33691E` |
| `textured_emblems/_default.dds`（96×96 BGRA8，7 mip，49,272 bytes） | `697430F86ABD26B5056A8779E4BF78C7CB526A57B5AD13F02898BA64B89526CC` |
| Clausewitz `utility.fxh`（含 `GetOverlay`） | `ABD382499457D6616597E41647983B982A44AEA7A0A3392927693827201CAB1B` |
| Jomini `coat_of_arms_pattern.fxh` | `46EBB391EF78CEC706EAABA809F3F90E0BF931793655E91EB56517A761006960` |
| Jomini `coat_of_arms_textured_emblem.fxh` | `432202D6A4FF73743B9445EF802C5B7EEC3346F0D0A51DDBF49C5940B884ABD6` |

当前实现与证据入口：

- `ck3_autonomous_player/src/xar_autoplayer/bridge/coat_of_arms_source_probe_contract.py`；
- `ck3_autonomous_player/src/xar_autoplayer/bridge/coat_of_arms_source_export_contract.py`；
- `ck3_autonomous_player/src/xar_autoplayer/coat_of_arms_resources.py`；
- `ck3_autonomous_player/native_bridge/src/coat_of_arms_designer_probe_v1.cpp`；
- `ck3_autonomous_player/tests/unit/test_coat_of_arms_source_probe_v1_bridge.py`；
- `artifacts/coa-clipboard-probe-2026-09-08/`（过程资产，不进 Git）。

`D:\workspace\open_kaishek` commit `33d690234d8217422978ee642055ab1b13e44c76` 的 CK3 profile
没有 CoA clipboard/render-description parser domain，因此本项离线预验记为 `not-applicable`；没有拿通用 effect parser 冒充专用 reader。
