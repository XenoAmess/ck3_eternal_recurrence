# 天朝二期考核榜 named-widget state + ACL v1

状态：**read-only query static exact-build ready；typed action paused-probe blocked；live-unverified**。本文记录的是最小只读 provider，以及尚未达到公开条件的动作 ABI 候选证据；不能据此声称考核榜完整 GUI gate、动作 provider 或 production-live 已完成。

## 目标与边界

这个切片让 runner 在同一个 paused revision 中回答两个有限问题：

1. 当前真实考核榜入口、外层窗口、modal 和 panel 的命名实例是否存在，以及其本地/祖先链有效可见性；
2. 当前玩家是否拥有 managed 考核面，或是否拥有 received-self 面及其 #013 披露策略绑定。

公开 capability 为 `game.command.query-zhongguo-scoreboard-state-v1`，MCP 工具为 `ck3_query_zhongguo_scoreboard_state_v1(request_nonce, expected_revision)`。调用方不能提交 widget 名、变量名、坐标、角色 scope 或动作。native 响应固定使用 `zhongguo_scoreboard_state` result key。

本切片明确不提供点击、activate、close、reopen 或任意写动作，也不使用 OCR、坐标和 GUI definition presence 代替真实 runtime instance。`activate`、`close`、`reopen` 均返回 typed `read_only_provider_action_not_exposed`。

## Exact-build GUI 证据

冻结构建为 CK3 `1.19.0.6`，EXE SHA-256：

`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

静态逆向冻结的最小读取链如下：

- GUI global slot RVA：`0x576CC68`；
- root/owner chain：`[slot] -> +0x1B8 -> +0x58 -> +0x3D0 -> +0x08`；
- exact top-level runtime widget lookup RVA：`0x36D0B20`；
- widget local hidden flags：`+0xD0`，mask `0x10`；
- parent：`+0xE8`；children pointer/count：`+0xF0/+0xFC`；
- MSVC widget name string：`+0x1B8`。

这里调用的是 runtime top-level instance lookup。GUI definition lookup、脚本变量存在、源文件中出现 `name = ...` 都不能替代它。当前尚未保存 paused CK3 response artifact，因此 root singleton 只属于 exact-build 静态逆向证据，不能标为 production-live。

固定 runtime allowlist 只有四项：

| stable identity | runtime name | v1 可观察字段 |
|---|---|---|
| `zg361_open_scoreboard` | `zg361_scoreboard_toggle` | exists、local/effective visible |
| `zg361_scoreboard_window` | 同名 | exists、local/effective visible |
| `zg361_scoreboard_modal` | 同名 | exists、local/effective visible |
| `zg361_scoreboard_panel` | 同名 | exists、local/effective visible |

`zg361_open_scoreboard` 是产品稳定入口身份；实际带名字的顶层容器是 `zg361_scoreboard_toggle`。该容器下目前有三个无名 clickable descendants，所以 v1 不能诚实证明具体入口的 enabled 状态。它不会把容器存在误写成“按钮可点击”。

有效可见性只在固定实例的 parent 链上读取 `local hidden` bit；循环、深度超过 64、遍历超过 4096、指针或名字漂移都会 fail closed。

以下 ABI 尚未冻结，统一 typed unavailable：

- enabled；
- focus；
- modal/blocking；
- screen rect；
- scroll min/max/value。

因此 `full_widget_gate_ready=false` 固定不变。root lookup 不能代替上述字段，更不能代替动作能力。

## Typed action 的 exact-build 静态账本

本轮只冻结了候选调用链，没有把它公开成能力。CK3 `1.19.0.6` 的静态证据如下：

- `CPdxGuiWidget` RTTI/type descriptor、COL、vftable 分别为 `0x518CFE0`、`0x4B93CB0`、`0x4504EA0`；
- `CPdxGuiButtonBase` 分别为 `0x56026B8`、`0x4B955B0`、`0x4505B98`；
- `CPdxGuiPushButton` 分别为 `0x50A9930`、`0x4B95560`、`0x4506020`；
- PushButton vtable slot 36 指向 `[0x36C6A90,0x36C6BD0)`。它在 `+0xD0` mask `0x02` 未置位且 `+0x7F8` callback 非空时取得 callback 对象、构造 `Position2D/Position2DX/Position2DY` 上下文并执行；`+0x7F8` 由 runtime property ID `0x11B` / definition `+0x3F8` 刷新，静态上只能命名为 primary/left-release callback dispatch candidate。GUI `onclick` 的 definition property ID `0x307` / `+0x338` 尚未与这条 runtime 链闭合；
- slot 37 指向 `[0x36C6BD0,0x36C6C92)`，只看到对应状态回落；
- `[0x36C6CA0,0x36C6EEB)` 根据 event `+0x24` 与 ButtonBase `+0x810/+0x814` 的 trigger mode 判定事件，不是可独立复用的 enabled getter；
- `[0x369E140,0x369E16F)` 是 `filter_mouse` mask setter：property key `filter_mouse` 在 `0x4294DE8`、ID 为 `0x3EE`；input bit 0 映射到 widget `+0xD1` bit 7，bits 1..3 映射到 `+0xD2` bits 0..2，bits 4+ 被丢弃。所以只能确认“若输入 `0x0F`，则 mask 为 `D1:80/D2:07`”；脚本 token `all` 的 exact numeric value 及 modal-stack/top-receiver 语义都尚未闭合，也没有真实 modal hidden/visible 对照样本，因此不能公开命名为 `modal_blocking=true`。

上述 span 的 SHA-256 已写入机器 ABI 账本。它们足以确定下一次 probe 应观察什么，不足以完成动作，原因有四项：

1. `zg361_scoreboard_toggle` 是容器；managed、received 与 system 三个真实入口按钮都无名。静态源码不能替代 paused runtime 中“恰有一个可见 PushButton”的实例证据；
2. modal 背景关闭按钮无名；header 关闭按钮会从原版 `buttons_window_control` 模板继承通用名 `button_close`，但它尚没有 scoreboard-specific identity，也没有 paused runtime 展开实例证据；当前不存在独立 reopen 控件；
3. `0x36C6A90` 的 callback 执行形状尚未由真实 scoreboard event trace 闭合到该按钮的完整 `onclick` 序列；直调还会绕过上游 hit-test、capture、modal、shortcut 与完整 enabled admission。`+0xD0` mask `0x02` 只能说已在 button-event/callback gate 中观测到，没有 enabled/disabled 对照前不能对外命名为 enabled；
4. 当前 public/native snapshot revision 不包含 GUI/VariableSystem 独立变化，`query_sequence` 又是每次查询都会变化的运输序号。它不能冒充“动作后状态发生变化”的新 revision。

因此当前 wire 必须继续返回 `read_only_provider_action_not_exposed`，`action_abi_ready=false`、`action_postcondition_revision_ready=false`、`production_live_ready=false`。禁止直接调用候选 RVA、ButtonBase 状态传播槽，禁止用源码 definition presence、OCR、屏幕坐标或一次 ACK 补齐证据。

下一次允许占用 CK3 的最小 paused probe 必须一次批量保存 managed 与 received-only 两种真实玩家现场，并完成：

1. 给三入口和背景关闭控件建立 scoreboard-specific runtime identity，将 header 的通用 `button_close` 名绑定到 scoreboard panel 相对路径；查询实际 pointer/vtable/祖先可见性，证明每种现场只有一个合法入口；
2. 先静态闭合 definition `onclick` ID `0x307` / `+0x338` 与 runtime ID `0x11B` / `+0x3F8` / `+0x7F8`，以及 slot 36 的上游 event admission；再对真实 scoreboard 按钮记录受控 native event trace，闭合 dispatcher → PushButton action slot → `onclick` callback 序列，并用 enabled/disabled 对照冻结 admission bit；
3. 在 modal hidden/open/closed 三态读取 `+0xD1/+0xD2`，把实际 hit-test/filter 状态与 blocking 语义闭合；
4. 引入只在 canonical scoreboard GUI/变量状态变化时更新的独立 `scoreboard_state_revision`，动作只先返回独立 `submitted/verification_pending` ACK；later pump 必须重新查询更大的 scoreboard revision 并验证后置条件；
5. `activate` 后验证 modal/panel 可见与正确 tab/list/facts，`close` 后验证 open 变量不存在与 modal/panel 隐藏；`reopen` 必须是 close 已经由新 revision 证明后再重新定位入口并 activate 的两阶段组合，不能用两次 toggle 或同泵读回冒充成功。

## 当前玩家 ACL

ACL 永远从同帧 `played_character_id` 的二十个固定产品 mirror 变量读取，不接受 caller 选择 scope，也不根据爵位等级猜测权限。读前/读后 frame、两份 raw row 和四个 widget pointer identity 必须一致。

固定变量 allowlist 为：

1. `zg361_sb_m_01_char`
2. `zg361_scoreboard_managed_owner`
3. `zg361_sb_r_01_char`
4. `zg361_sb_self_char`
5. `zg361_scoreboard_received_owner`
6. `zg361_scoreboard_received_cycle_serial`
7. `zg361_scoreboard_received_case_serial`
8. `zg361_sb_self_case_owner`
9. `zg361_sb_self_cycle_serial`
10. `zg361_sb_self_case_serial`
11. `zg361_sb_self_b1_case_owner`
12. `zg361_sb_self_b1_cycle_serial`
13. `zg361_sb_self_b1_case_serial`
14. `zg361_sb_self_disclosure_acl_mode`
15. `zg361_sb_self_disclosure_policy_available`
16. `zg361_sb_self_disclosure_policy_id`
17. `zg361_sb_self_disclosure_self_mode`
18. `zg361_sb_self_disclosure_team_mode`
19. `zg361_sb_self_disclosure_evaluator_identity_mode`
20. `zg361_sb_self_disclosure_blackbox_risk`

managed 面只有两种合法状态：

- `m_01` 与 managed owner 同时不存在：面不可用，`current_player_can_assess_others=false`；
- 两者均为合法 character target，且 owner 等于当前玩家：面可用，`current_player_can_assess_others=true`。

这条规则不推断 rank。公爵及以上玩家只有产品真实 materialize managed 面后才能考核别人；伯爵和男爵在 managed 面不存在时只能被考核，provider 不会因头衔猜出额外权限。

received-self 面要求首行与 self character 都是当前玩家；received header 的 owner/cycle/result case 必须与 self result tuple 一致。B1 owner/cycle 必须与 result tuple join，但 B1 case serial 是独立 policy case，不能与 result case serial 比较。合法例子仍是 B1 case `41`、result case `903`。#013 A/B 的 policy ID 绑定 B1 case；C/legacy 路径保持 policy unavailable。

任何 owner、subject、cycle、case、kind、披露模式或 policy join 不一致都返回 typed `acl_inconsistent`，不会退回爵位推断、第三方读取或宽松 `null`。

## Same-frame 和 readiness

查询通过 application-main fixed mailbox 的第十八槽 `permitted_executor_octodenary` 执行，步骤为 `query-zhongguo-scoreboard-state-v1`。响应绑定：

- exact build 与 adapter/consumer identity；
- connection generation 与 query sequence；
- request nonce；
- snapshot/public/native revision；
- paused/date/current player。

只有 player binding、GUI root、入口/窗口最小状态、ACL 和 same-frame 全部成立时，`state_acl_query_ready=true`。这只表示“固定四实例 + 当前玩家 ACL”的最小只读查询可用。

`production_live_ready=false` 在本版本固定不变。没有真实 paused artifact，不得把离线 fixture、源码契约、命令 ACK 或 capability registration 写成 live。

## 证据与下一步

机器可读冻结账本：

- `ck3_autonomous_player/native_bridge/research/zhongguo_scoreboard_state_v1_abi.json`
- `ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_scoreboard_state_v1_source_contract.json`
- `ck3_autonomous_player/schemas/zhongguo-scoreboard-state-v1.schema.json`

离线 native fixture 覆盖 received-only 玩家不能获得 manager ACL、A 策略 B1/result case 独立、祖先 hidden 传播、未冻结字段 typed unavailable、read-only 动作边界与 exact RVA binder。Python contract 覆盖固定 step、未知字段/任意 widget 输入拒绝、严格响应归一化、MCP facade 与 shared wiring。

允许启动 CK3 后的下一项施工必须是：在真实角色与真实考核榜实例上取得同一 paused revision 的 MCP response artifact，分别覆盖 managed 与 received-only 玩家，再按 artifact 单独把最小 slice 提升为 production-live primitive。focus、scroll、rect、blocking、enabled 和 activate/close/reopen 仍须各自冻结 exact-build ABI、实现 typed query/action、获得独立 ACK 后新 revision 的查询证据；在此之前正式完整 runner gate 继续保持 RED。
