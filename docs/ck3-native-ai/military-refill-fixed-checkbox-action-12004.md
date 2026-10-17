# R06：沿原版补员 checkbox 的最小动作接线（1.20.0.4）

下一步可以复用现有 `DispatchFixedGuiWidgetNativeV1`，点击原版补员**外层组**，让原 callback 自己构造变量和解析 receiver。无需先追 R194/R195 mode1 分支没有调用的动态 provider；也不能把静态候选指针直接传给 `12FF8D0`。本增量是默认关闭的候选实现，尚未编译或执行补员动作。

机器 `desktop-3fevhd2-1c74096080`；离线源码基线 `611bc985ae95f477dd7314df11f8602cd1e595f3`。[源与实际 slot13 证据](evidence/military-refill-fixed-checkbox-action-12004.json)记录观察时间和精确文件 pins。游戏身份沿用已闭 1.20.0.4 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；没有新 EXE 读取、SDK、游戏、桌面或 native 构建。这里没有 R196 新实机结论。

## 原版候选、调用、执行与后验

| 层 | 已闭来源与实际角色 | 本候选采用什么 |
| --- | --- | --- |
| GUI 候选 | `window_military.gui` 488/898：外层组 `OnMilitaryReinforcementClick`；内层 checkbox 只是 checked 展示 | fresh military census，只接受两个已证 profile 中唯一 visible/enabled 的外层组 |
| 分派 | 当前 `.4` `DispatchFixedGuiWidgetNativeV1` 检查实际 context、widget vtable、slot13=`3AA0D20`、callback group 与 modal，再调用 `3ABC4B0` | 沿已有 fixed widget adapter；路径由 native census 给出，再逐层重新解析并核 parent/context/vtable，不接受调用方指针或路径 |
| 原 callback | `3AA30E0 → 3A9F960 → 3AC38C0 → 3E4C090 → 1303D40` | 由原版当次 callback 建立临时变量，保留未知构造/选择细节，不自行模拟或调用 provider |
| 命令 | `1303D40` 非空 RCX 才调用 `12FF8D0`；后者用 receiver+218 的完整 Character → +1C0 military → +4A9 决定反向 desired，经 factory/`37F06D0` 提交 | 不直接调用此业务函数、不写 flag；wrapper 的 AL1 和 GUI handled 都只作 ACK |
| 独立后验 | R195 已实证同来源 owner31254 的 `static_direct_owner_switch_12004` available、raw4A9=1 | 新动作必须后读 fresh census、相同 owner/source/frame 且新 query ticket，目标 enabled 值真正可见才报告 verified |

当前 source 与 getter 事实见 [R195 实证](episode04-r195-static-owner-switch-12004.md)、[业务命令](military-refill-toggle-command-12ff8d0-12004.md)、[原版 final target](military-refill-finaltarget-1303d40-12004.md)。R194 没有此新 child，不能造出 R194→R195 的 toggle。

本轮仅解压已保全 R195 小归档到内存复核：两个 outer group 的 `button_base_slot13=true`、实际 vtable RVA=`76962064`，均为 **fallback group** 且恰1 callback；slot2=`3AA30E0`、entry=`3A9F960`、final=`1303D40`。可见组 enabled=true，另组 hidden。它给出复用 slot13 路径的实际可达依据；不是从 checkbox 名字猜的入口，也没有新 Driver 读取。

```mermaid
flowchart LR
  G[stock military outer group] --> D[fixed original GUI slot13 dispatch]
  D --> C[original expression callback builds variables]
  C -. native selected pointer not observed .-> R[1303D40 actual RCX]
  R --> T[12FF8D0 owner and inverse desired]
  T --> Q[37F06D0 command submission]
  Q -. setter/execution timing unknown .-> S[same owner military 4A9]
  S --> O[fresh independent source-owner read]
```

## 候选代码与最窄接口

新增 defaultOFF `XAR_ENABLE_FIXED_MILITARY_REINFORCEMENT_ACTION_12004`；依赖现有 military owner route 与 static owner switch reader。没有新 MCP、hook、ring、native-call slot 或 provider 执行入口。既有 `ck3_execute_step(step: str, expected_revision)` 原样承载两个固定 step：

```json
{"step":"disable-military-reinforcement-v1","expected_revision":"fresh public integer"}
```

启用对应 `enable-military-reinforcement-v1`。示例中的 revision 是占位说明，实际必须用 fresh snapshot 的整数，不能直接提交这段 JSON。NativeDriver 保留 public revision，底层 `_execute_primitive_step` 继续映射真实 native revision；夹具使用 public110/native109，不能把二者混用。

Native 专属 `military_reinforcement_action_12004` 走现有 frontend mailbox，复用 alive/paused snapshot、owner-thread、GUI owner 和 slot13/modal admission。只接受 stock source profile：

| outer child path | 固定有名祖先 |
| --- | --- |
| `0/0/0/2/3/0/0/0` | `tab_your_armies` / `footer` |
| `0/0/0/3/5/0/0/0` | `imperial_armies_ra_uses_this` / `footer` |

表达式仍须是 chain0/kind3/final1303D40/type635/receiver flag0，原 thunk/descriptor 和 source-reader pins 通过，独立 continuation 的 source owner 与实际 actor 相同。full depth8 的 `parent_depth_exhausted` **不阻断**已独立 available 的 continuation/getter，也不被改写成 full 成功。

Native 当次重读状态后，若 enabled 已等于 desired，不 dispatch；否则恰一次原版 GUI dispatch。`raw!=0` 是 enabled，不只接受 raw1；null military 保留原生 zero basis 与 raw null，不能与 read failure 混淆。Native 前后各作 fresh census，但回执始终 `postcondition_verified=false` / `verification_pending=true`。原 `native_handled=false` 不能否认副作用或允许重投。

DTO 的 `current_variable_table_observed=false`、`native_receiver_selected=false` 和 `provider_invoked=false` 延用 source-candidate 的观察范围：bridge 没有读取临时表、宣称已选择 native receiver 或直接调用 provider。它们不宣称原版 callback 当次内部没有解析变量或调用其他 helper；这些传递行为仍未观测。

Python 独立后读一次起，最多沿现有有限5秒只读确认模式；不会重发动作。只有同帧/同 owner/source 且 ticket 新于前读、实际 enabled 达到 desired，才返回 `verified_desired`；原来已是 desired 则是 `verified_already_desired`，没有切换信用。未达到或结果未知保留 once claim，连反向 step 也不能绕过重投。新 query 不要求 native revision 增长，因为 paused UI 命令可能同日期同 native frame完成。

## 本轮验证与后续资格

4 个新增 Python 行为案例已在外置 overlay 运行，消费生产 full census strict normalizer：非零 raw2、handled=false 后独立读回；未变 pending 并阻反向提交；null military false 的 no-action；owner/frame/隐藏/祖先/重复 source 与 ACK 矛盾拒收。没有重跑旧矩阵。

新增 native fixture 只提供源码、**NOTRUN**。它运行真实 source selector 和 action decision boundary，仅替换 native dispatch I/O，输出4行，其中2行来自实际 DTO serializer。未来 Root 同一 coherent build 需运行 target `xar_test_military_reinforcement_action_12004`，再用 `tests/verify_military_reinforcement_action_wire_12004.py --repo-root ... --native-jsonl ...` 让生产 strict consumer 消费真实 wire；这仍是离线合同，不是实机 toggle。

实机资格需要 Root 在未来独占窗口：固定军事面板已可见 → fresh paused frame/source owner getter → 单次固定 enable/disable → 保存独立后验。未知 selectedreceiver、临时变量表、内部 provider 是否执行与最终 ADD 保持未观测；常规补员 ADD 还须另取自然结算后的 physical writer / whole DATA 证据。不存在“点击 ACK 即 R06 完成”。

## Transport 接线更正（a45b）

原 a45 的四项行为案例替换了 primitive 边界，未覆盖真实 Driver 的结果投影。
`NativeHeadlessGameplayDriver._execute_primitive_step` 在611源码的12080行必将
`backend_id="native-headless"` 加入原生 result；旧 strict keyset 会在已提交动作后拒收它。
已封 a45 保留原样；a45b 独立 delta 仅允许这个可选 transport 字段，出现时必须精确为
`native-headless`。裸 native serializer wire 仍合法，原始 `.result.json` 不剥离该字段。

新增一项焦点案例实际经过生产 primitive、GUI census reader、capabilities、action 与 strict normalizer，
仅用 endpoint/state/snapshot 替换 Native I/O：public110 实际发出 native109，原 ACK
仍 verified=false/pending=true，独立 later byte1→0 才得到 verified。该案例实际通过；
原四项未重跑。它是离线协议证据，未产生任何实机 toggle、receiver/table/provider 或 ADD 信用。
