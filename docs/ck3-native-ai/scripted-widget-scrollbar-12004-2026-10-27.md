# Scripted widget 原生滚动条静态研究（1.20.0.4）

状态：**exact-build 静态研究；未动态采样、未新增能力、未资格化调用、无新 live PASS**。

本页服务于 RRF 结果窗、Faith 窗及大型创建窗口的后继验收。研究只读原 EXE、原版 GUI、已有 C++ 和 R22 报告；没有访问游戏进程、调用原生函数、启动后端、创建分析库或修改生产代码。研究阶段禁止新输出，局部反汇编和摘要仅保留在当次工具 stdout；本页不是完整反汇编归档或执行资格回执。

## 身份与方法

- `machine_id: 4-8e1c2f1861`，由 `tools/ck3_live_run_id.py machine` 实际读回。
- 实际观察 UTC：`2026-10-26T18:31:06.899650Z` 至 `2026-10-26T18:39:50.900716Z`；本地日期为 2026-10-27。
- CK3 `1.20.0.4` / build `25734779`；输入：`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/binaries/ck3.exe`。
- 原 EXE：101,040,248 B，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，image base `0x140000000`。前后完整 SHA 相同，mtime_ns 均为 `1792040747148251100`。
- 当次 PATH、已配置 MCP 和卸载登记中未发现可用 REA/Ghidra/IDA/Rizin；这不是全盘软件不存在证明。使用本机工具 venv 已安装的 pefile/Capstone，以及现有 [find_rtti.py](../../ck3_autonomous_player/native_bridge/research/find_rtti.py)、[find_xrefs.py](../../ck3_autonomous_player/native_bridge/research/find_xrefs.py) 和 [disasm_ck3.py](../../ck3_autonomous_player/native_bridge/research/disasm_ck3.py) 的只读方法。
- 方法边界沿用 [研究流程](research-tooling-workflow.md)与 [REA 方法](../rea-ck3-research/methodology.md)：RTTI/xref 先作 locator，再核实际构造、调用、字段读写及消费者；函数 RF 表项不自动等于完整逻辑函数。下列地址全部为该 EXE 的 **RVA**。

## 已有实机事实与当前拒绝原因

来源为旧报告：`C:/workspace/rrf-development-20261024/review-fixes-a01/cold-R0020-finalization-a01/live/4-8e1c2f1861--religious-ritual-fusion--R0022/native-report.json`。

其 `r22-d1-refreshed-preview-controls` 对结果窗查询完整、未截断。可见的左列 `vertical_scrollbar` 及四个实际子按钮均为 `clickable=false`；`r22-07-faith-close-controls` 中可见 Faith 滚动条四个子按钮同样为 false。没有据此执行滚动。广告工具无 scroll/wheel/set-scroll；generic query 只有 root/revision，activate 只有 generation/widget ID/revision。

原版 `game/gui/shared/lists.gui:3236` 的 `scrollbox` 使用 `Scrollbar_Vertical`（3304），含 track、slider、空定义的 `dec_button/inc_button`（3358/3363）。GUI 声明为 button 不等于当前原生通道可点击，也不证明有可见箭头图形或非零尺寸。

现有 [InspectStandardClickBinding12004](../../ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp:1738) 读取 button 的 `+0x3F8`，空时改读 `+0x338`。而下述滚动按钮使用另一套按下/释放组；当前拒绝不能用放宽普通 onclick 判定解决。

## ScrollBar：布局、构造和一次性派发

RTTI `CPdxGuiScrollBar`：TypeDescriptor `0x55139D0`，COL `0x5070C58`，vtable **`0x496F150`**，与 R22 实际滚动条 vtable 数值相同。工厂 `0x3A5EDB0` 分配 `0x3C0` B 并初始化：

| 相对 ScrollBar 偏移 | 静态用途 | 构造默认值 |
| --- | --- | --- |
| `+0x358` | float 当前 value | 0 |
| `+0x35C / +0x360` | float 下界 / 上界 | 0 / 100 |
| `+0x364 / +0x368 / +0x36C` | float step / page / wheelstep | 1 / 10 / 10 |
| `+0x370` | direction；值 1 的布局分支使用 Y/高度 | 0 |
| `+0x378 / +0x380` | dec / inc 实际子按钮指针 | null |
| `+0x388 / +0x390` | slider / track 指针 | null |

GUI 构造入口 `0x3B48B00` 消费 dec token `0x35D`、inc token `0x35E`，分别写入 `+0x378/+0x380`。失败分支原字符串明确为 `Could not create dec_button/inc_button for scrollbar`，并引用原生 `pdx_gui_scrollbar.cpp`。

一次性内核 **`0x3B487C0`** 以 RCX 为真实 ScrollBar、EDX 为方向枚举，减 1 后索引六项 RVA 表 `0x3B48878`：

| EDX | 分支目标 | 运算 |
| --- | --- | --- |
| 1 / 2 | `0x3B487E2 / 0x3B487F7` | value 加 / 减 step |
| 3 / 4 | `0x3B4880C / 0x3B4882E` | value 加 / 减 page，另受 `+0x3A8` 拖动锚比较约束 |
| 5 / 6 | `0x3B4884C / 0x3B48861` | value 加 / 减 wheelstep |

这些分支尾调 `0x3B47A30 → 0x3B47A70`。后者按原生边界和 `+0x398/+0x399` 标志分支 clamp，写 `+0x358`；值改变才更新 slider（`0x3B47FD0`）并通知回调。两个标志的完整生命周期未闭合，不将原生行为简化为我方公式。3/4 **不是**已证明可无条件调用的 page API；1/2 是最窄后继候选。

## 按钮生命周期与 ScrollArea 回调反链

dec 按下 `0x3B48890` 写 `+0x3A4=2`；inc 按下 `0x3B489A0` 写 1，均启动重复计时器；释放 `0x3B48AB0` 清状态并取消计时器。注册参数见 `0x12C`，重复字段 `+0x3AC=0x3C`；本页保留原数值，不独立授予时间单位。**只调用按下而不完成释放可能留下重复滚动。**

`0x3B48B00` 将按下 binder 装入子按钮 `+0x2F8`，释放 binder 装入 `+0x318`。binder vtable `0x496F350`，invoke `0x9CC100`；method 在 binder `+8`、有符号 adjust 在 `+0x10`、receiver 在 `+0x18`。构造时 method 分别为上述按下/释放函数、adjust 为 0、receiver 为实际 ScrollBar。它们不是现有 generic 读取的普通 onclick 组。

`CPdxGuiScrollArea`：TypeDescriptor `0x553BC20`，COL `0x50700A8`，vtable **`0x496DF18`**。静态链如下：

1. parser `0x3B3B130` 调用 `0x3B3A010`，将 vertical bar 存到 area `+0x338`、horizontal bar 存到 `+0x340`；替换时撤销旧关联。
2. `0x3B3A010` 向 bar `+0x2F8` 的 value-changed 数组注册 binder。其 vtable **`0x496E1F8`**、invoke **`0x3B3BF80`**、method **`0x3B3AFF0`**、adjust 0、receiver 为真实 area。这里 receiver 位于 binder `+0x20`，不能套用按钮 binder 的 `+0x18`。
3. setter `0x3B47A70` 按 `0x48` stride、条目 `+0x40` 取 callback object，再调用其 vtable `+0x10`；旧 value 作为通知参数传递。
4. `0x3B3AFF0` 核 source bar 等于 area `+0x338/+0x340`，读取 bar **新** value；对 content=area `+0x328` 的相应 Y/X 使用负 value，通过 `0x3B3B780 → 0x3A75460/0x3A75A80` 原生位置更新链保留另一轴。

这闭合了静态 value→通知→内容位置链，没有证明当前场次实例的数组、receiver 或滚动后态。

## 接入边界：复用 generic，不能放宽成任意调用

现有 [Identity/Capture/Dispatch](../../ck3_autonomous_player/native_bridge/src/scripted_widget_control12004_native.cpp:80) 已有 exact-build、暂停 owner mailbox、snapshot/GUI context、祖先和完整树绑定。[Activate](../../ck3_autonomous_player/native_bridge/src/scripted_widget_control12004.cpp:71) 重新捕获并逐项相等比较，在 dispatch 前消费 generation，UNKNOWN 不重放；当前 dispatch 使用原普通按钮路径。

后继候选是在既有 C++ 中加入内部强 enum `scrollbar_step_increment/decrement`：由实际 parent vtable、`+0x378/+0x380` 反绑匿名按钮，核 area 关联及上述 binder/receiver，再仅调一次 `0x3B487C0(1|2)`。不要调用 press-repeat，不接受外部函数指针，不放开普通 callback 白名单。须继续独立校验 modal、完整祖先、可用尺寸/裁剪、有限有效 range、repeat/timer 空闲及同帧身份。MCP 请求的 generation/widgetID 可以保留；这只是设计候选。

如需由消费者选择语义并确认滚动，现有 row/action DTO 还须显式给出 typed 控件种类/方向和真实 scroll before/after 状态，同步 serializer、既有 SDK parser/schema 与回归。当前 `verification_pending` ACK 不等于 viewport 已变化；到边界不变也须如实区分。不得为截图修改 Rite、family 或列表真值。

最小后继采样是在获准暂停 owner 查询中读取一个真实 bar 的 value/range/step/direction、子指针和尺寸/裁剪、repeat 状态，以及 bar↔area、按下/释放/value-changed binder 的真实 method/adjust/receiver；随后才可验证一次增减及独立内容位置后态。本页没有执行这些采样、回归、构建或动作。

## 大型窗口 census 的独立限制

[ResolveNamedGuiWidgetV1](../../ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp:1536) 先查 top-level，失败后确有 global-root BFS 的真实名称 fallback；不能表述为“绝对只支持 top-level”。但查找总队列 4096、深度 64，超限拒绝，不分页，重名取首个匹配；R17 named-subroot 实际 unavailable 保留，源码可能性不授可用。

[InspectNamedGuiSubtreeV1](../../ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp:1801) 另有输出 2048、遍历 4096、单节点 children4096、深64 的界；generic Capture 遇 truncated 拒绝。实际广告的 InspectGuiWindowTree 也不包含 rite_creation。滚动不减少隐藏子树，不能解决该 census 问题。

后继若采用 root 内显式容器 path 或 visible-subtree coverage，应保真实 root/祖先/帧及明确覆盖域，演进请求/输出合同并回归；不得伪造 root alias、默默滤掉节点后仍称完整全树，或仅提高 cap 猜测已修好。

## 小段字节与源码复核索引

下列 SHA 为当次从上述 exact EXE 读取的指定长度；不是新资格文件。`0x3B487C0` 段止于 ret，跳表数据另在 `0x3B48878`，不能把表当指令解码。

| RVA / bytes | SHA-256 |
| --- | --- |
| `0x3B487C0 / 183` | `527c220ba10634ebe568e39e4cef29b80a7f76f94a7733b4e55935d86a4a5d5c` |
| `0x3B47A30 / 319` | `4878ee47fdce0ab520dacf733f9ff792e8ca4ffa4529e635835f847caa28563d` |
| `0x3B3A010 / 153` | `52af42a006286351b68b8179ac1a370dba8069fc36265f59a9850c95ee764758` |
| `0x3B3AFF0 / 312` | `b75002101b54118fd59fe1027ef2aa20762892f702349358659e72a67e50861f` |
| `0x3B48B00 / 832` | `ea0a8db40e67bf7cca01fc77db4d6ccbf7b521cb45f0830d765654c9677c0ecc` |
| `0x3B48AB0 / 75` | `38ef1700ea2d54d8238d1cec2758b1844c5157e644dcbd295796257406d44418` |

研究时另实际比较 N7 来源 `5b834e4b21434c961fddfe8915ab5c28df3d9ce7`：`zhongguo_scoreboard_state_v1.cpp`、`scripted_widget_control12004_native.cpp`、`scripted_widget_control12004.cpp` 三份原字节均相等。相关普通派发来源为 [zhongguo_scoreboard_action_v1.cpp:415](../../ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_action_v1.cpp:415)。这些复核只绑定研究输入，不把 N7 旧资格扩展到本页候选分支。
