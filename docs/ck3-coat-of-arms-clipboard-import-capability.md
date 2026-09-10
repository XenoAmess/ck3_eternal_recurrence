# CK3 纹章设计器剪贴板导入能力报告

> 调研日期：2026-09-08 至 2026-09-11
>
> 页面：角色设计器 → 自定义纹章 → 设计你自己的纹章 → 从剪贴板粘贴
>
> 精确基线：CK3 `1.19.0.6 (Scribe)`，Steam build `23530548`
>
> 路线：MCP-first；截图或鼠标只用于把隔离测试实例导航到纹章页，不作为语法判定证据

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
| `legacy-ui` | 早期人工/UI 辅助观察；仅作补充，不作为 MCP-first 最终证据 |
| `unresolved` | 证据不足、含义歧义或资源与语法尚未拆开验证 |

“真正保存进角色/王朝/家族/头衔”还需要完成上层窗口的 Finish。`mcp-applied` 只证明当前纹章设计器 working state 已改变，
不冒充上层保存或跨存档持久化。

## 3. MCP-first 探测能力

### 3.1 补能力前后的事实

用实际安装的 Python MCP SDK `2.0.0` 连接现有 stdio server 时，补能力前共列出 62 个工具，
没有 coat-of-arms、clipboard 或 designer 工具。也就是说，旧 MCP 无法回答本报告的核心问题。

本轮先后新增两个原生工具和一个离线资源工具：

```text
ck3_probe_coat_of_arms_source_v1(
    source: string,
    expected_revision: integer,
    apply: boolean
)

ck3_export_coat_of_arms_source_v1(
    expected_revision: integer
)

ck3_query_coat_of_arms_resource_catalog_v1(
    game_directory: string,
    kind: "pattern" | "colored_emblem" | "color",
    query?: string,
    visible_only: boolean = true,
    offset: integer = 0,
    limit: integer = 50
)
```

对应原生 capability：

```text
game.command.probe-coat-of-arms-source-v1
game.command.export-coat-of-arms-source-v1
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

Hybrid 后端中的两个工具都强制直达 native，
不会回退到 OCR、坐标或视觉驱动。

resource catalog 不启动 CK3，也不经过视觉路线。它先校验 `binaries/ck3.exe` 的 exact-build SHA-256，然后读取原版
`50_coa_designer_patterns.txt`、`50_coa_designer_emblems.txt` 与 `50_coa_designer_palettes.txt`，按原版设计器顺序分页返回
名称、颜色通道数、可见性、分类、相对路径以及当前页 DDS 的大小和 SHA-256。结果明确标记
`engine_registration_observed=false`、`dlc_and_mod_overrides_included=false`：它证明 exact 1.19.0.6 基础游戏磁盘资源，
不冒充运行时注册表或玩家当前 playset。

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
当前实现限制输出为非空 ASCII、
无 NUL、最多 128 KiB。它已经达到 `mcp-static-ready`，尚未在真实 CK3 中执行，因此本报告仍不使用它改写任何语法结论。

### 3.3 验证状态

- Python contract、service、native driver、hybrid、离线资源索引和真实 MCP SDK tools/list/call：26 项聚焦测试 GREEN；
  不带 MCP SDK 的普通 Python 环境同组测试 26 项 GREEN，其中 3 项 SDK 集成测试按设计跳过；
- native bridge fresh build：成功；
- native protocol 与 adapter registry CTest：2/2 GREEN；
- Copy/export MCP primitive 已完成 closed-schema 注册、exact-build RVA/prologue 身份校验、UI-thread 调用、剪贴板读取、
  SHA-256 与 exact binding 投影，当前为 `mcp-static-ready`；遵守用户当前“不占用 CK3/主屏幕”的要求，live 结果明确待验；
- 离线 resource catalog 已对本机 exact 1.19.0.6 安装执行：基础游戏 manifest 共定义 42 个 pattern（38 个 designer 可见）、
  1,578 个 colored emblem（1,576 个可见）和 13 个背景色；该结果不含 DLC/mod override，也不是运行时注册证明；
- Web 编辑器的 Quarkus 伴随服务已完成真实后台贯通：`REST → MCP Java SDK 2.0.1 stdio client → Python MCP server →`
  `ck3_query_coat_of_arms_resource_catalog_v1` 返回 exact-build 两项 pattern 和完整 provenance；该贯通未启动或操作 CK3，
  也没有使用 OCR。Quarkus REST 映射 3/3、前端 API/parser 8/8、production build GREEN；
- CK3 frontend exact-build 握手：已真实取得，并广告新 capability；
- 隔离 attempt 5 补齐 `frontend_snapshot` 绑定；attempt 6 暴露剪贴板函数槽的瞬时初始化状态；attempt 8 又证明
  gameplay 生命周期门禁会让角色设计器永远无法安装 hook。现在 hook 在 exact adapter 选定后即于 frontend 启动，瞬时槽缺失仍在
  heartbeat 延迟重试；精确构建或入口身份失败保持永久拒绝。
- attempt 8 在完整纹章编辑器执行 27 条原生 probe 请求：25 条不同载荷加 2 条重复/应用复核，另有前后 capability 与 snapshot；
  hook 诊断最终为 `installed=true`、`failure=0`、`executed_requests=27`。会话绑定 CK3 PID `11348`、snapshot `native:3`、
  public revision `4`、connection generation `1`，结束时 `cleanup_proven=true` 且进程树为零。
- attempt 8 的 LF-only 多行载荷真实暴露 `CF_UNICODETEXT` 回读会转为 CRLF；同一载荷改用 CRLF 后为 `detected`。
  MCP 合同随后补成调用方换行规范化，避免把有效语法误报成 `clipboard_readback_mismatch`。

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

## 5. 哪些语法能导入并实际生效

### 5.1 稳定核心

| 层级 | 语法 | 实际含义 | 当前等级 |
|---|---|---|---|
| 外层 | `name = { ... }` | 定义候选纹章；普通标识符、`coa` 和数字 key 均被接受 | `mcp-detected` |
| 根 | `pattern = "pattern_*.dds"` | 选择底图；reader 接受名字不等于资源一定存在 | `mcp-applied` |
| 根 | `color1`、`color2`、`color3` | 底图通道颜色 | `mcp-applied` |
| 根 | 重复 `colored_emblem = { ... }` | 添加一个或多个彩色图案层 | `mcp-applied` |
| 根 | `textured_emblem = { ... }` | 受限的纹理图案层；当前仅验证 reader 接受 `_default.dds` | `mcp-detected` |
| emblem | `texture = "ce_*.dds"` | 选择 colored emblem 纹理；资源存在性需另验 | `mcp-applied` |
| emblem | `color1`、`color2`、`color3` | emblem 通道颜色 | `mcp-applied` |
| emblem | `mask = { ... }` | pattern 分区遮罩；`{ 1 }` 已应用，`{ 1 2 3 }` 已检测 | `mcp-applied` |
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

“注释在 copy-back 丢失”和“HSV 被 copy-back 规范化成 RGB”仍来自早期辅助观察；Copy/export MCP primitive 已静态就绪，
但尚未实机执行，所以仍需等待 live 复核。

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
| `textured_emblem` | `_default.dds` 载荷为 `mcp-detected`；早期设计器中呈占位/问号，编辑面板支持有限 | 可导入但标“有限支持”，不进 v1 默认生成面板 |
| 普通或数字 outer key | `custom_name={...}` 与 `79={...}` 均为 `mcp-detected` | 导出仍固定用 `coa`，减少无意义差异 |
| 多个顶层对象 | 整段为 `mcp-detected`；本轮没有 canonical copy-back 证明究竟采用哪一个 | 拒绝歧义输入 |
| 空块、无 pattern | `coa={}` 与 `coa={ color1=blue }` 均为 `mcp-detected` | 允许解析，产品层警告“不完整/可能依赖默认值” |
| 不存在的 pattern/emblem texture 名 | 两类载荷均为 `mcp-detected` | 将“reader 接受”和“资源存在”分开校验 |
| body-only，无 outer wrapper | 精确载荷为 `not_detected` | v1 必须要求 wrapper |
| 重复普通标量 | 两个 `color1` 为 `mcp-detected`，但优先级未通过 copy-back 证明 | 警告并拒绝默认导出 |
| `parent = c_england` | 与普通字段共存或单独存在均为 `mcp-detected`；继承是否解析、最终值为何尚未证明 | 只保留/警告，不进确定性 serializer |
| 静态 `@chosen = blue` + `color1=@chosen` | 为 `mcp-applied`；说明 reader 接受这类静态替换语法，不证明游戏 scope 变量能力 | 可导入并保留，默认导出展开成确定字面量 |
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
- `parent`、数据库 alias（reader 会接受，但继承解析和确定结果未证明）；
- `@变量` 声明与引用（简单静态替换会接受甚至应用，但产品应先展开为确定字面量）。

Web 端若要提供随机生成，应在自己的数据模型中完成选择，再导出确定的纹理、颜色与实例。

## 8. 目前 MCP 能力仍缺什么

本轮已实机闭合“输入源码 → 原生检测/预览 → 可选应用”，并补齐 frontend 生命周期与 Windows 换行规范化。
游戏自身 Copy/export 已通过 MCP/原生实现并完成静态验收，但尚未取得 live 证据；基础游戏 designer manifest 资源目录也已
通过离线 MCP 工具分页暴露。仍未通过 MCP 暴露的能力有：

- 读取 preview 的最终像素或直接导出 PNG；
- 完成角色设计器上层 Finish；
- 枚举游戏当前运行时实际注册且已合并 DLC/mod override 的 pattern/emblem/color 资源；
- 跨 CK3 build 自动适配 RVA 与字段。

按 MCP-first 原则，后续若需要 canonical round-trip、资源清单或截图无关的视觉验收，应继续补这些原生/MCP primitive，
而不是用 OCR 猜文字、按钮状态或 copy-back 内容。

## 9. `coat_of_arms_editer_of_ck3` 的实现约束与当前状态

应用已经按指定目录名 `coat_of_arms_editer_of_ck3` 建立，采用 Vue 3 + Element Plus + TypeScript；
当前纯前端即可完成解析、结构化编辑和源码生成，不需要后端。

建议模型：

```text
CoatOfArms
├─ pattern
├─ colors[1..3]
├─ coloredEmblems[]
│  ├─ texture / colors / mask
│  └─ instances[]: position / scale / rotation / depth
└─ texturedEmblems[]  (experimental)
```

当前首个可运行基线已经做到：

- parser 识别未知字段并给出带位置诊断，serializer 只输出稳定白名单；
- 语法合法、资源存在、引擎检测、designer 应用是四个不同状态；
- 多顶层、重复标量、body-only、模板 DSL 默认拒绝；
- 简单静态 `@变量` 在导入时展开，`parent` 保留为诊断而不混进确定性导出；
- 导出固定使用 `coa` wrapper、已实机验证的字段白名单和 CRLF；
- 提供图层/实例结构化表单与浏览器近似预览，且明确不冒充 CK3 renderer；
- 基础游戏 pattern/emblem 目录已经接入结构化选择器，并可按名字筛选首批 200 个 emblem；
- 必要的 Quarkus 伴随服务使用官方 Java MCP SDK 连接现有 Python stdio server，前端可刷新 session revision、执行原生
  detect/apply，以及载入原生 Copy/export 返回源码；伴随服务只允许四个相关 MCP 工具。

尚未完成的下一阶段能力：

- 继续补 DLC/mod playset 合并与运行时注册证据；
- 在重新获准占用 CK3 后，对编辑器的 detect/apply/Copy-export 做 live round-trip 验收；当前只是接口与静态实现 GREEN，
  不把 REST mock 或离线 catalog 贯通写成 designer live；
- PNG/像素验证 primitive；
- 基于真实 DDS 资源的预览，而不是当前的几何近似符号。

浏览器无法直接启动本机 stdio MCP，因此已引入 Maven + Java + Quarkus 伴随服务。后端只负责 REST/MCP 会话转接与
本机资源索引，不承担“执行 CK3 脚本”的虚构能力；当前也没有 DDS 转换或素材缓存。

首版有 Vitest parser/serializer 回归和 Vite production build 验收。后续扩展仍以本文的原生 MCP 证据为协议来源，
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
| `50_coa_designer_patterns.txt`（42 项/38 可见） | `3BAA46C11BD24E7D9F9F6D1DF3E51403D016AB4CAC7290A6541ED25561425B7B` |
| `50_coa_designer_emblems.txt`（1,578 项/1,576 可见） | `3D6529702F91FA352E07B0C64E4C33A88E5F86C2AAF0EF2D0CEB69CF6D600F3C` |
| `50_coa_designer_palettes.txt`（13 色） | `3AE2EA0F3B751D61C08A06408FA2EDA2ADC3FF6FBF204298D3D8CDC9613B87B4` |

当前实现与证据入口：

- `ck3_autonomous_player/src/xar_autoplayer/bridge/coat_of_arms_source_probe_contract.py`；
- `ck3_autonomous_player/src/xar_autoplayer/bridge/coat_of_arms_source_export_contract.py`；
- `ck3_autonomous_player/src/xar_autoplayer/coat_of_arms_resources.py`；
- `ck3_autonomous_player/native_bridge/src/coat_of_arms_designer_probe_v1.cpp`；
- `ck3_autonomous_player/tests/unit/test_coat_of_arms_source_probe_v1_bridge.py`；
- `artifacts/coa-clipboard-probe-2026-09-08/`（过程资产，不进 Git）。

`D:\workspace\open_kaishek` commit `33d690234d8217422978ee642055ab1b13e44c76` 的 CK3 profile
没有 CoA clipboard/render-description parser domain，因此本项离线预验记为 `not-applicable`；没有拿通用 effect parser 冒充专用 reader。
