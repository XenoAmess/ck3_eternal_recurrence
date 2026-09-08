# CK3 纹章设计器剪贴板导入能力报告

> 调研日期：2026-09-08
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

本轮新增显式工具：

```text
ck3_probe_coat_of_arms_source_v1(
    source: string,
    expected_revision: integer,
    apply: boolean
)
```

对应原生 capability：

```text
game.command.probe-coat-of-arms-source-v1
```

它不属于自动游玩 planner 的无参数 action 集合，只能由调用方显式提供源码。为了覆盖角色设计器所在的开局前流程，
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

Hybrid 后端中的本工具也强制直达 native，
不会回退到 OCR、坐标或视觉驱动。

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

输入先限制为非空 ASCII、无 NUL、最多 128 KiB，并以 base64 通过 named pipe；Python 绑定源字节 SHA-256，
原生侧写系统剪贴板后立刻 read-back 比较。该 ASCII 限制来自当前 CK3 reader 的真实行为：高位 UTF-8 字节会令外层函数提前退出，
而且可能留下旧的 `CanPaste` 状态；首版若允许任意 Unicode 会制造假阳性。

状态只有：

- `detected`：只检测，原生 reader 接受；
- `applied`：检测成功并验证 working state 应用成功；
- `not_detected`：本次精确源码未被 reader 识别；
- `apply_failed`：检测成功但原生 paste 后置条件失败；
- `unavailable`：没有在超时内观察到有效 designer，或原生入口不可用。

查询会覆盖 OS 剪贴板并改变游戏里的 paste preview，因此不是无副作用的纯读操作。

### 3.3 验证状态

- Python contract、service、native driver、hybrid 和真实 MCP SDK tools/list/call：14 项聚焦测试 GREEN；
- native bridge fresh build：成功；
- native protocol 与 adapter registry CTest：2/2 GREEN；
- CK3 frontend exact-build 握手：已真实取得，并广告新 capability；
- 隔离 attempt 5 实际暴露并补齐了 `frontend_snapshot` 绑定缺口；attempt 6 到达完整纹章编辑器后又证明，
  CK3 的剪贴板函数槽在早期注入时可能尚未初始化，旧实现会把这一瞬时状态永久记为 unavailable。原生桥已改为仅对此
  瞬时失败在 heartbeat 上延迟重试，并公开 installed/failure/observed/executed 诊断；精确构建或入口身份失败仍永久拒绝。
- 逐载荷 MCP 实机矩阵仍待新 DLL 的下一隔离 attempt；旧 DLL 返回的 `unavailable` 是桥接初始化 RED，不能算任何载荷的
  `not_detected`，也没有被写进第 5 节语法结论。

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
| 外层 | `name = { ... }` | 定义一个候选纹章；任意普通名字在辅助实机中可接受，复制时会规范化 | `engine-static + legacy-ui` |
| 根 | `pattern = "pattern_*.dds"` | 选择已注册底图 | `engine-static + legacy-ui` |
| 根 | `color1`、`color2`、`color3` | 底图通道颜色 | `engine-static + legacy-ui` |
| 根 | 重复 `colored_emblem = { ... }` | 添加一个或多个彩色图案层 | `engine-static + legacy-ui` |
| emblem | `texture = "ce_*.dds"` | 选择已注册 colored emblem 纹理 | `engine-static + legacy-ui` |
| emblem | `color1`、`color2`、`color3` | emblem 通道颜色 | `engine-static + legacy-ui` |
| emblem | `mask = { ... }` | 选择 pattern 分区遮罩；确切合法值域不应从单个样例外推 | `engine-static + legacy-ui` |
| emblem | 重复 `instance = { ... }` | 同一纹理的多个实例 | `engine-static + legacy-ui` |
| instance | `position = { x y }` | 归一化位置 | `engine-static + legacy-ui` |
| instance | `scale = { x y }` | X/Y 缩放；负值可镜像 | `engine-static + legacy-ui` |
| instance | `rotation = number` | 旋转；可为小数或负数 | `engine-static + legacy-ui` |
| instance | `depth = number` | 层叠顺序参数 | `engine-static + legacy-ui` |

原版直接语料可见于：

- `common/coat_of_arms/coat_of_arms/90_dynasties.txt`：多 emblem、多 instance、浮点值与 RGB；
- `common/coat_of_arms/coat_of_arms/01_landed_titles.txt`：mask 与负 scale；
- `common/coat_of_arms/coat_of_arms/01_holy_order_coas.txt`：rotation。

在 MCP 实机矩阵完成前，表中没有把这些辅助观察冒充 `mcp-detected`。

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

原版最终纹章语料使用引号/不引号字符串、整数、小数、负数、空白和紧凑 `key=value`。早期辅助实机还观察到：

- `#` 注释可接受，复制回去时注释丢失；
- `hsv { ... }` 可接受，复制时规范化成 `rgb { ... }`；
- 重复 `colored_emblem` 与重复 `instance` 均生效。

这些项会继续由 MCP exact-source probe 复核。

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
| `textured_emblem` | reader 可接受；测试 `_default.dds` 在设计器中呈占位/问号，编辑面板支持有限 | 可导入但标“有限支持”，不进 v1 默认生成面板 |
| 任意普通 outer name | 辅助实机可接受，copy-back 会规范化 | 导出固定用 `coa` |
| 多个顶层对象 | 辅助实机只采用第一个，后续对象被忽略 | 拒绝歧义输入 |
| 无效 texture | 文法可能接受，但资源查找失败并显示占位，同时产生 graphics 诊断 | 将“语法合法”和“资源存在”分开校验 |
| body-only，无 outer wrapper | 旧观察相互冲突 | v1 必须要求 wrapper |
| 重复普通标量、未知键、`parent`、`@变量` | 没有足够稳定的提交语义 | 报错或 warning，不进入默认导出 |
| `color4` | 随机模板中偶见，但最终模型/UI 核心证据不足 | 不进 v1 |

## 6. 哪些 CK3 语法不能在这里执行

| 语法族 | 能否执行 | 结论依据 |
|---|---:|---|
| 本文第 5 节的 render-description 字段 | 是，只产生纹章数据语义 | 专用 CoA reader/renderer |
| `effect = { ... }`、scripted effect | 否 | 无 effect VM；辅助实机中整段不形成 preview |
| `trigger = { ... }` | 否 | 无 scope/trigger evaluator；辅助实机拒绝 |
| `event`、`decision`、`interaction` | 否 | 无对应数据库或队列调用 |
| `script_value`、scope link、变量操作 | 否 | render description 没有游戏 scope |
| GUI 表达式、`GetScriptedGui(...).Execute(...)` | 否 | 输入没有进入 GUI 表达式解释器 |
| console command、`run file.txt` | 否 | 无控制台 dispatcher |
| localization 表达式 | 否 | 无 loc 求值路径 |
| template 的 `list`、weighted list、trigger | 否 | 辅助实机 `list` 拒绝；这是随机生成阶段 DSL |
| include、任意磁盘读写、进程或网络调用 | 否 | 只解析内存文本并按名字查已注册 CoA 资源 |

反例：

```text
coa = {
    pattern = "pattern_solid.dds"
    color1 = blue
    effect = { add_gold = 1000 }
}
```

这不会给 `add_gold` 一个执行上下文。当前辅助实机中该输入没有有效 preview；即使将来发现 reader 会忽略某个未知字段，
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
- `parent`、数据库 alias；
- `@变量` 声明与引用。

Web 端若要提供随机生成，应在自己的数据模型中完成选择，再导出确定的纹理、颜色与实例。

## 8. 目前 MCP 能力仍缺什么

本轮优先补了“输入源码 → 原生检测/预览 → 可选应用”闭环。仍未通过 MCP 暴露的能力有：

- 调用游戏自己的 Copy/export，并返回规范化 source；
- 读取 preview 的最终像素或直接导出 PNG；
- 完成角色设计器上层 Finish；
- 枚举游戏当前实际注册的 pattern/emblem/color 资源；
- 跨 CK3 build 自动适配 RVA 与字段。

按 MCP-first 原则，后续若需要 canonical round-trip、资源清单或截图无关的视觉验收，应继续补这些原生/MCP primitive，
而不是用 OCR 猜文字、按钮状态或 copy-back 内容。

## 9. 对 `coat_of_arms_editer_of_ck3` 的约束

后续应用按用户指定目录名 `coat_of_arms_editer_of_ck3`，前端采用 Vue 3 + Element Plus + TypeScript。
仅解析、编辑和生成纹章源码不需要后端。

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

v1 应做到：

- parser 保留未知字段用于诊断，但默认 serializer 只输出稳定白名单；
- 语法合法、资源存在、引擎检测、designer 应用是四个不同状态；
- 多顶层、重复标量、body-only、模板 DSL 默认拒绝；
- 资源索引绑定 exact CK3 version/DLC/mod set；
- 可选“发送到游戏”通过 MCP 调新工具，不让前端模拟点击 paste。

浏览器若需要读取用户显式选择的本机 CK3 目录、转换 DDS 或建立素材缓存，才引入 Maven + Java + Quarkus 伴随服务。
后端只负责文件索引/转换/MCP 会话，不承担“执行 CK3 脚本”的虚构能力。

本轮不创建该应用目录；当前交付先冻结引擎事实与 MCP 能力边界，避免把旧 UI 推断固化成编辑器协议。

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
| 09 月 10 日衔接 `origin/master` 后的 `xar_ck3_bridge.dll`（2,507,776 bytes） | `EE1C2C6B5AD60ECD3442720F7D3F9CE98293FC8AF6333D79FD01705B1548B580` |

当前实现与证据入口：

- `ck3_autonomous_player/src/xar_autoplayer/bridge/coat_of_arms_source_probe_contract.py`；
- `ck3_autonomous_player/native_bridge/src/coat_of_arms_designer_probe_v1.cpp`；
- `ck3_autonomous_player/tests/unit/test_coat_of_arms_source_probe_v1_bridge.py`；
- `artifacts/coa-clipboard-probe-2026-09-08/`（过程资产，不进 Git）。

`D:\workspace\open_kaishek` commit `33d690234d8217422978ee642055ab1b13e44c76` 的 CK3 profile
没有 CoA clipboard/render-description parser domain，因此本项离线预验记为 `not-applicable`；没有拿通用 effect parser 冒充专用 reader。
