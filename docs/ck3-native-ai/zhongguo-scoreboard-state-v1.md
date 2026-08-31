# 天朝二期考核榜 named-widget state + ACL v1

状态：**static exact-build ready，live-unverified**。本文记录的是最小只读 provider，不能据此声称考核榜完整 GUI gate 或 production-live 已完成。

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
