# 天朝二期考核榜 named-widget state + ACL v1

状态：**read-only query 已在真实 paused CK3 到达 ACL 解码；provider-observed revision + exact semantic-activation dispatcher static-ready；production capability/open-close live artifact pending**。本文记录最小只读 provider、只返回 verification-pending ACK 的共享动作层，以及仍未取得的动作实机证据；不能据此声称考核榜完整 GUI gate、生产动作能力或 production-live 已完成。

## 目标与边界

这个切片让 runner 在同一个 paused revision 中回答两个有限问题：

1. 当前真实考核榜入口、外层窗口、modal 和 panel 的命名实例是否存在，以及其本地/递归缓存的有效可见性；
2. 当前玩家是否拥有 managed 考核面或 received 列表面；若当前玩家另有 self dossier，再验证其 #013 披露策略绑定。

公开 capability 为 `game.command.query-zhongguo-scoreboard-state-v1`，MCP 工具为 `ck3_query_zhongguo_scoreboard_state_v1(request_nonce, expected_revision)`。调用方不能提交 widget 名、变量名、坐标、角色 scope 或动作。native 响应固定使用 `zhongguo_scoreboard_state` result key。

只读 state 字段中的 `activate`、`close`、`reopen` 仍返回 typed `read_only_provider_action_not_exposed`。另有独立 transport capability `game.contract.zhongguo-scoreboard-action-v1-fail-closed` 和 MCP 工具 `ck3_activate_zhongguo_scoreboard_v1(...)`；它已连接 exact shortcut-manager semantic activation，但不广告 production capability `game.command.activate-zhongguo-scoreboard-v1`。动作只能返回 typed unavailable 或 `acknowledged_verification_pending`，绝不把 ACK 或 native raw bool 当作 GUI 成功。两者都不使用 OCR、坐标和 GUI definition presence 代替真实 runtime instance。

## Exact-build GUI 证据

冻结构建为 CK3 `1.19.0.6`，EXE SHA-256：

`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

静态逆向冻结的最小读取链如下：

- GUI global slot RVA：`0x576CC68`；
- root/owner chain：`[slot] -> +0x1B8 -> +0x58 -> +0x3D0 -> +0x08`；
- GUI owner 的全局 widget root：`owner +0xD0`；这里的 owner 字段与下方 widget 自身 `+0xD0` flags 属于不同对象，不能混用；
- GUI context modal receiver vector：data `+0x290`、`int32 count +0x29C`，静态读取上限 256，top receiver 为最后一项；
- exact top-level runtime widget lookup RVA：`0x36D0B20`。其冻结 span 为 `0x36D0B20..0x36D0CA8`（`0x188` B，SHA-256 `AA460EB52819C0D02F64293EE7F3793DD8D3B0CB010A3347011CE04AECA4B83F`）；函数先读 `owner+0xD0`，然后只枚举该 root 的 `+0xF0/+0xFC` direct children 做 exact-name 比较，不递归；
- widget local hidden flags：`+0xD0`，mask `0x10`；effective-hidden 递归缓存位：同一字节 mask `0x08`；
- widget effective-disabled cache：`+0xD0`，mask `0x02`；local-disabled source bit 为 `0x04`；
- parent：`+0xE8`；children pointer/count：`+0xF0/+0xFC`；
- MSVC widget name string：`+0x1B8`。

这里调用的是 runtime direct-child instance lookup。GUI definition lookup、脚本变量存在、源文件中出现 `name = ...` 都不能替代它。R515 已保存一次真实 paused state 请求并越过 GUI root，但在 ACL 解码处因 received 列表与 self dossier 被错误捆绑而返回 unavailable；尚无 open/close/switch 的 GREEN artifact，因此 scoreboard provider 仍不能标为 production-live。

同一 owner/root ABI 已取得一条用途受限的旁证：B3 promotion R12 的 custom/native direct-child probes 全为 none；promotion-only candidate 随后在 direct lookup miss 时从 `owner+0xD0` 做固定名字、depth 64 的 descendant fallback，R13/R14 均越过最初 progress query。scoreboard 同样先 exact top-level 定位 window，再在 window 内按固定 allowlist 做 bounded descendant lookup。R517/R519 证明旧的逐名字 DFS 即使从 `4096` 调到 `8192`，仍小于 4,782 个源码 block 加 2,110 次 template expansion 的真实实例规模。最终实现改为一次遍历、一次读取每个 runtime name，并在同一趟中收集 15 个固定身份；总上限为 65,536、depth 仍为 64。它比十四次重复扫描更便宜，也不放宽名字或 root。该修复仍不构成 scoreboard live 或公开动作能力。

固定 runtime allowlist 有 15 项。下表概括四个外层对象；三个入口、三个 outer tab、三个 list-page witness 和 backdrop/header close 也以编译期固定名字读取：

| stable identity | runtime name | v1 可观察字段 |
|---|---|---|
| `zg361_open_scoreboard` | `zg361_scoreboard_toggle` | exists、local/effective visible、effective enabled |
| `zg361_scoreboard_window` | 同名 | exists、local/effective visible、effective enabled |
| `zg361_scoreboard_modal` | 同名 | exists、local/effective visible、effective enabled |
| `zg361_scoreboard_panel` | 同名 | exists、local/effective visible、effective enabled |

`zg361_open_scoreboard` 是产品稳定入口身份；实际带名字的顶层容器是 `zg361_scoreboard_toggle`。动作合同不会把容器当成任意点击目标，而是只从三个已命名入口中选择唯一有效可见项。

local visible 读取 `+0xD0 bit 0x10`；effective visible 直接读取 CK3 已递归维护的
`+0xD0 bit 0x08` 缓存，不再从 parent 链重算。离线对照专门覆盖“child local visible、
但 effective hidden”的组合，避免再次把祖先 local bit 当作引擎最终输入门禁。

effective-enabled 已闭合：definition property `0x305` 经 parser `0x36A1928` 进入 setter `0x369CA70`；`0x369CA90` 将 local/inherited disabled 递归缓存到 `+0xD0 bit 0x02`。ButtonBase slot 13（`0x36C69A0`，base `0x369E720`）按该 effective bit 拒绝输入。因此 provider 只读这个缓存位并返回 `enabled = !(flags & 0x02)`；它没有把 local bit `0x04` 误当成 effective 状态。

以下 ABI 尚未冻结，统一 typed unavailable：

- focus；
- modal/blocking；
- screen rect；
- scroll min/max/value。

因此 `full_widget_gate_ready=false` 固定不变。root lookup 不能代替上述字段，更不能代替动作能力。

## Provider-owned observation revision

available state 直接公开五个顶层字段：`tree_fingerprint_v1`、`semantic_fingerprint_v1`、`provider_session_id`、`observation_sequence`、`observed_state_revision`。`provider_session_id` 是 DLL/provider 生命周期初始化时用系统 CSPRNG 生成的 128 bit 值，固定编码为 32 个大写十六进制字符；生成失败时 revision provider typed unavailable，绝不拿 PID、时间或 module base 代替。两个 fingerprint 都是 64 个大写十六进制字符的 SHA-256，只用于诊断；provider 判定变化时比较的是内部 canonical bytes，不拿 hash 碰撞假设代替字节相等。

tree bytes 冻结为：带终止 NUL 的 domain `XAR/ZG361/SCOREBOARD/TREE/V1`、`u16 format=1`、EXE SHA raw 32 bytes、allowlist 长度与 UTF-8、GUI owner/root，以及固定 15 项的 `u8 index/exists + u64 instance/vtable + u8 parent depth + 从 window root 到 target 顺序的每层 u64 ancestor/u32 child ordinal`。它刻意不含 visible、enabled 或 modal top receiver，所以同一 GUI 树上的正常开关不会制造 tree drift。

semantic bytes 冻结为：带终止 NUL 的 `XAR/ZG361/SCOREBOARD/SEMANTIC/V1`、`u16 format=1`、EXE SHA raw 32 bytes、allowlist 长度与 UTF-8、`i32 played_character_id`、15 项 `index/exists/effective-visible/enabled`、modal open、modal top relation 与 receiver、active page、visible entry、20 项原始 ACL allowlist（固定顺序，不另写 row index；present 后为 `i32 kind + i64 payload`）及派生 ACL/case tuple。modal relation 的固定枚举为 none / exact modal / strict descendant / other，并作为 input-routing 诊断写进 fingerprint；`modal_blocking` ABI 尚未冻结，所以它不再作为 surface availability 或动作准入门。产品把 HUD 入口保留在 modal 下方：打开态必须恰有一个 active page 和一个同面的 visible entry；关闭态必须没有 active page 且恰有一个 visible entry。零项、多项或打开态 page/entry 不同面都会让整次 query unavailable。

只有 application-main 上两次完整 tree/semantic bytes 与前后 paused frame 都一致，才允许发布观测。同一 `{provider session, connection generation, player, date, build, allowlist}` 绑定内：每次成功发布让 `observation_sequence +1`；tree 或 semantic bytes 任一相比上一条成功发布发生变化，才让 `observed_state_revision +1`。首条成功观测为 `1/1`。unavailable 不更新；动作 ACK 的 validation read 也不更新，并且当前 bytes 不等于最后一次已发布观测时直接 fail closed。

这套 revision 不叫 engine revision，也不声称捕捉查询间发生后又恢复的瞬态。A→B→A 只有在 B 被一次成功 query 实际采到时，才能由单调 revision 证明两次变化。内部 STATE digest 使用带终止 NUL 的 `XAR/ZG361/SCOREBOARD/STATE/V1` 加 raw tree/semantic digest，仅供 provider 自身记录，不新增公开字段。

## Typed action 的 exact-build 静态账本

本轮把严格解析、同帧 admission、mailbox、exact dispatcher 和 verification-pending ACK 接到了共享层，但没有公开生产动作能力。CK3 `1.19.0.6` 的静态证据如下：

- `CPdxGuiWidget` RTTI/type descriptor、COL、vftable 分别为 `0x518CFE0`、`0x4B93CB0`、`0x4504EA0`；
- `CPdxGuiButtonBase` 分别为 `0x56026B8`、`0x4B955B0`、`0x4505B98`；
- `CPdxGuiPushButton` 分别为 `0x50A9930`、`0x4B95560`、`0x4506020`；
- 旧候选 PushButton vtable slot 36 / `0x36C6A90` 已证伪为 oversound/hover 路径，**严禁调用**；
- exact 安全入口为 shortcut-manager binder `0x36E1C40`。manager 从 GUI context `+0x3E0` 取得；bridge-owned `0x50` pimpl stub 只在 `+0x48` 放 target，CString 使用合法空 SSO。binder 构造 type `0x1D` 的 `CPdxGuiShortcutEvent`，经 `DeliverGuiEvent 0x36CB4A0`、两层 prehandler、ButtonBase slot13 `0x36C69A0`、callback group wrapper `0x36C56C0` 与 slot10；
- flags=0 时选择 `target+0x3F8` group0，为空才 fallback 到 `target+0x338` group0。dispatch admission 要求实际选择的 group 至少一个 callback，条目 stride `0x48`、callback `+0x40` 的 vslot2 可调用；
- modal vector 为 GUI context `+0x290/+0x29C`。若倒扫发现任一 effective-visible modal，exact binder 仍以绝对最后一项 `vector[count-1]` 作为 strict-descendant `0x369E620` 的 root；实现保持这个 exact-build 行为，不擅自替换成倒扫命中项；
- `[0x369E140,0x369E16F)` 是 `filter_mouse` mask setter：property key `filter_mouse` 在 `0x4294DE8`、ID 为 `0x3EE`；input bit 0 映射到 widget `+0xD1` bit 7，bits 1..3 映射到 `+0xD2` bits 0..2，bits 4+ 被丢弃。所以只能确认“若输入 `0x0F`，则 mask 为 `D1:80/D2:07`”；脚本 token `all` 的 exact numeric value以及从这些局部 flags 推导通用 `modal_blocking` 的规则尚未闭合。动作 admission 不依赖这项推导，而是直接读取已闭合的 global modal vector/top receiver；没有真实 modal hidden/visible 对照前，state 字段仍不能公开命名为 `modal_blocking=true`。

prehandler 可以短路 ButtonBase 或修改 event `+0x14`；ButtonBase 在空 callback 组时也可能返回 true。因此 binder raw bool 只公开为 `native_handled` 诊断值，无论真假都不构成动作结果。完整 dispatch 调用结束后只返回 `acknowledged_verification_pending`，独立 later query 才能证明变化。

provider-owned revision 与独立 action ABI 的 exact dispatcher 均已静态闭合，但真实 paused open/close/switch 对照尚不存在；`query_sequence` 仍只是运输序号。state payload 内的 `action_abi_ready=false` 继续表示“尚未完成 public/live promotion”，而不是否认独立 action ABI 已 static-ready；`production_live_ready=false` 同样固定保持，生产 capability 不得广告，runner 不得生成 verified PASS。禁止调用已证伪 slot 36，禁止用源码 definition presence、OCR、屏幕坐标、一次 ACK 或 `native_handled` 补齐证据。

完整双表面 scoreboard 验收仍须单独保存 managed 与 received-only 两种真实玩家现场，并完成：

1. 在 modal hidden/open/closed 三态互证 top receiver relation、active page、visible entry 与 provider fingerprint/revision；
2. 保存 source query、exact ACK 与独立 later query；later 必须具有同一 provider session/connection/player/date/build、相同 tree fingerprint、更大的 observation sequence 与 `observed_state_revision`、不同 semantic fingerprint；
3. `open` 后验证 modal/panel 与正确 list page，三个 switch 各验证唯一目标页，`close` 验证 modal 与三页隐藏；
4. `reopen` 必须拆成 close ACK → closed query → open ACK → open query，不能用两次 toggle 或同泵读回冒充成功。

## 当前玩家 ACL

ACL 永远从同帧 `played_character_id` 的二十个固定产品 mirror 变量读取，不接受 caller 选择 scope，也不根据爵位等级猜测权限。读前/读后 frame、两份 raw row、15 个 widget pointer identity 及完整 tree/semantic bytes 必须一致。

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

received 列表面与当前玩家 self dossier 是两个独立事实。产品 `zg361_scoreboard_received_available_gui` 只要求 `zg361_sb_r_01_char`；因此首行是合法 character 时，列表面可用。received owner/cycle/result case 若存在必须能按冻结类型解码，缺失则保持 typed `variable_absent`。

只有 self dossier 的十四个字段中至少一项存在时，才进入完整 received-self join；此时必须全量闭合，self character 必须等于当前玩家，received header 的 owner/cycle/result case 必须与 self result tuple 一致。B1 owner/cycle 必须与 result tuple join，但 B1 case serial 是独立 policy case，不能与 result case serial 比较。合法例子仍是 B1 case `41`、result case `903`。#013 A/B 的 policy ID 绑定 B1 case；C/legacy 路径保持 policy unavailable。若十四个 self 字段全部不存在，则 `surface_available=true`、`current_player_is_subject=false` 是合法列表态。

任何已存在字段的 kind 错误，或部分 self dossier、owner、subject、cycle、case、披露模式、policy join 不一致，都返回 typed `acl_inconsistent`，不会退回爵位推断或第三方读取。完整缺失的 self dossier 使用逐字段 typed `variable_absent`，不把合法缺失伪装成 `null` 成功值。

## Same-frame 和 readiness

查询通过 application-main fixed mailbox 的第十八槽 `permitted_executor_octodenary` 执行，步骤为 `query-zhongguo-scoreboard-state-v1`。动作 transport 使用独立第二十二槽 `permitted_executor_duovigintary`，不会覆盖只读查询槽。响应绑定：

2026-09-12 的 R511 实机首次调用证明该查询与所有 gameplay primitive
共享 `type="execute_step"` 外层消息。旧 state mailbox 解析器误写为
`type="command"`，导致已发布 capability 对真实 Python 请求恒定返回
malformed；同文件族的 action parser 已正确使用 `execute_step`。修复只校正
transport discriminator，不改变 capability、字段或 ABI，并由独立 mailbox
parser 回归覆盖。R511 在输入前终止，因此它是 bridge/harness RED，不是
记分板业务结果。

R513 随后实机跨过上述 transport，暴露第二个 native 错误。state resolver 把
`third+0x3D0` 的 owner-lookup host 同时当成 GUI dispatch context，导致 modal vector
从错误对象的 `+0x290/+0x29C` 读取并返回 `gui_root_unavailable`。同构建 action
dispatcher 的静态账本与实现已经证明 modal vector 属于第三 GUI 链对象，而 top-level
owner 才经 `third+0x3D0 -> +0x08` 解析。因此修复必须保留两个对象身份；不得用延时重试、
OCR 或“unavailable 等于 closed”绕过。R513 仍无业务输入，分类为 capability RED。

最小修复把第三 GUI 链对象保存在 dispatch context，并用独立局部变量解析
`third+0x3D0 -> +0x08` owner。focused native fixture 强制三者地址不同并已通过；
R515 的新 DLL 查询已经越过 GUI root，关闭了该错误；随后暴露的当前 RED 是 ACL
合同把合法 received list-only 状态误判为不一致。

R515 的 canonical seed（player `29037`）存在 `zg361_sb_r_01_char=26347`、
received owner `32904`、cycle `2`，但 `zg361_sb_self_char` 及全部 self dossier
字段不存在。产品 GUI 的 received 面只以首行为可见条件，self detail 另有独立
`zg361_sb_self_available_gui` 全量门禁。native/Python 合同现按这个产品边界拆开；
新 DLL 的真实 paused query 和 open 动作仍待下一轮验证。

R517 使用上述 DLL 后不再返回 `acl_inconsistent`，而是进入 widget 完整性门禁并返回
`widget_not_instantiated`。R519 将上限调到 8,192 后仍得到同一 RED，排除了简单二倍
上限足够的假设。当前 `zg361_scoreboard.gui` 有 7,604 行、4,782 个源码 block，另含
2,110 次 `using` template expansion；逐名字扫描既重复又无法用源码行数准确估计运行树。
最终修复在同一固定 window 子树做一次最多 65,536 节点的收集，并在 15 项全找到时
立即停止。名字 allowlist、depth 64、child count 4,096、动作目标和所有 ACL 规则不变。

R521 使用该单次遍历后仍返回 `widget_not_instantiated`。此前 top-level unavailable 分支
会丢弃已经完成的逐 widget `exists` 结果，15 项统一退回 `snapshot_unavailable`，导致
同一个 RED 无法指出缺失身份。响应现在保留首次固定 allowlist 解码得到的 widget 数组：
找到的项继续返回 typed `exists=true` 与只读 pointer/visibility，缺失项返回 typed
`exists=false`，其 pointer/visibility reason 为 `widget_not_instantiated`；top-level status、
reason 与全部 readiness 仍保持 unavailable/false，且不发布 provider observation。
这是一项诊断语义增强，不放宽 action 或 production-live 门禁。

- exact build 与 adapter/consumer identity；
- connection generation 与 query sequence；
- request nonce；
- snapshot/public/native revision；
- paused/date/current player。
- provider session、connection generation、tree/semantic fingerprint、observation sequence 与 observed state revision。

只有 player binding、GUI root、15 个固定实例最小状态、ACL 和 same-frame 全部成立时，`state_acl_query_ready=true`。这只表示“固定实例 + effective-enabled + 当前玩家 ACL”的只读查询可用。

`production_live_ready=false` 在本版本固定不变。没有真实 scoreboard state/open-close-switch paused artifact，不得把离线 fixture、promotion discovery 旁证、源码契约、命令 ACK 或 capability registration 写成 scoreboard live。

## 证据与下一步

机器可读冻结账本：

- `ck3_autonomous_player/native_bridge/research/zhongguo_scoreboard_state_v1_abi.json`
- `ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_scoreboard_state_v1_source_contract.json`
- `ck3_autonomous_player/schemas/zhongguo-scoreboard-state-v1.schema.json`

离线 native fixture 覆盖 received-only 玩家不能获得 manager ACL、received list-only 玩家没有 self dossier 时仍可读取列表、A 策略 B1/result case 独立、local/effective hidden 缓存对照、未冻结字段 typed unavailable、read-only 动作边界、exact RVA binder，以及 identical/A-B-A/ACK-validation/unavailable 的 provider tracker 对照。Python contract 覆盖 list surface 与 current-player dossier 的单向约束、固定 step、五个 provider 字段、未知字段/任意 widget 输入拒绝、严格响应归一化、MCP facade 与 shared wiring。

下一项 bounded live 工作先用 R515 的 received list-only 现场验证 state query 与宣传片所需的单次 open/visible/close。完整双表面验收继续作为独立工作包，随后在真实角色与真实考核榜实例上分别覆盖 managed 与 received-only 玩家，再按 artifact 单独把外层五个原子动作提升为 production-live primitive。focus、scroll、rect 与页面内动作仍是后续独立 ABI；provider revision 必须取得真实 open/close/switch 对照，reopen 必须取得 close/open 两阶段各自的 ACK 与 later query。在此之前正式完整 runner gate 继续保持 RED，但它不再作为宣传片只读展示首镜头的无关前置。

## R523 全局根定位结论

R523 使用保留逐控件诊断的 DLL 得到 15/15 `exists=false`，证明失败点在 window 子树遍历之前：CK3 的 direct top-level lookup 没有返回 scripted-widget registration，继续增加 DFS 上限没有作用。scoreboard 现复用 promotion R13/R14 已实机跨过首查的 owner `+0xD0` 全局 GUI 根 fallback，并从全局根执行同一个单次 65,536 节点 fixed-allowlist traversal。

direct lookup 仍为首选；fallback 不接受调用方名字，不改变 15 项 allowlist、depth、child count、ACL、schema 或动作 readiness。该路径在新 DLL 的 R525 前只标记为 `static-ready`，不得把 focused native executable 冒充 live scoreboard 证据。

## R525 动作后渲染稳定证据

R525 已在实机证明全局根 fallback 生效：15 个固定身份全部存在，received 关闭态发布 provider observation/revision `2/1`，exact native `open` 返回 accepted、verification-pending ACK。action cell 随后零等待执行独立查询，得到 `unavailable/state_projection_unavailable`。

`zg361_scoreboard_toggle` 与 `zg361_scoreboard_modal` 均使用 `Animation_ShowHide_Quick`；exact-build 的共享模板把淡入、淡出时长定义为 0.15 秒。过渡期间，effective visibility 可短暂不满足 canonical closed/open 两种互斥关系。provider 在这种帧继续 unavailable 是正确行为，不放宽 semantic invariant。

consumer 现只在动作 accepted 后等待 0.25 秒，再执行原有的一次独立 later query。它不轮询，也不把 unavailable 改写为成功。在 R527 取得符合预期 revision 与可见面的 available observation 前，该动作仍只记为 `static-ready + exact live ACK`，不能标成 verified production-live primitive。

R527 已执行上述有界检验，0.25 秒后仍返回 `state_projection_unavailable`，所以固定等待不是充分修复，后续不继续增加等待或原样复跑。最后可解码帧已经出现 scoreboard dimmer 与 panel 轮廓，证明 callback 改变了 GUI；当前缺口是 unavailable 响应没有保留 modal/page/closed-entry 的实际值。

新的诊断实现会在 tree/semantic projection RED 时保留已经解码的 first/second widget 与 ACL 状态，再调用 `SetTopUnavailable` 清空全部 readiness。它不发布 observation/revision，也不改变 success path。second read 的既有失败原因按 GUI lookup、widget decode、ACL、missing instance、tree/semantic 分支保留原有 reason vocabulary。下一轮只用于读取这些状态并确定唯一失败关系。

R529 的保留诊断给出了确定的产品形状：modal、panel、received entry、received tab、received page 和两个 close 控件均 effective-visible，另外两个 entry/page 不可见；received list ACL 同时有效。`zg361_scoreboard.gui` 也直接证明 HUD toggle/entry 的 visible 表达式不依赖 `zg361_scoreboard_open`，打开 modal 不会卸载或隐藏入口。因此旧 canonicalizer 的“open 必须零 visible entry”与产品实现不一致。最小修复要求 open 时恰有一个 active page、恰有一个 visible entry，且两者同面；closed 仍要求零 page/一个 entry。它不放宽多入口、多页或错面状态，也不改变 response schema、ACL、动作或 readiness。

R531 用该修复后的 fresh DLL 再次得到完全相同的稳定 received surface，却仍在 semantic builder 返回 unavailable。所有字段读取、ACL、唯一 entry、唯一同面 page 已满足，关闭态同一 tree 也能发布；唯一剩余条件是把 effective-visible modal 与 modal receiver vector 的绝对 top 强行绑定。该绑定超出了已冻结能力：ABI 文档一直把 modal relation 定义为 semantic observation，并明确 `modal_blocking` 未冻结、action admission 由独立 exact dispatcher 负责。最小修复保留 relation/receiver 读取和 fingerprint 编码，但不再让 none/other 与 modal visibility 的组合关闭整个只读 surface。parent-chain 无法安全读取仍返回 RED。
