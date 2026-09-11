# R418 B1 零幸存者 liveness RED

## 判决

R418 attempt 06 已在同一 CK3 PID 和 connection generation 内解除全部已知原版事件阻断，并把固定的
`10190` 天产品观察窗跑到绝对截止点。Central 与 standalone PP 始终没有启动；直接原因是玩家的 B1 经理对象从窗口起点到终点
一直停在 active/state `7`，其冻结 roster 与 processing 域均为 `0`，也没有 pending、reopen 或隔级回调可以重新进入 closure。
继续延长窗口不会增加信息，故本轮判为 **production liveness RED**。

这与 R386 的“还剩 73 个 survivor、最后回调前需压缩并重封”不是同一状态。R418 已经没有 survivor，也没有回调。不能发布一个
空结果来伪造 B1 GREEN；正确恢复是无奖励、无发布地退役该旧周期，再由已经存在的玩家年度请求从当前 live vassal 域打开新周期。

## 不可变实机证据

- 轮次：R418 attempt 06，PID `204536`，connection generation `1`，玩家 `32904`。
- 固定观察范围：retained origin `53905680`，absolute deadline `54150240`；实际失败帧 `54150408`。
- B1 同一暂停帧：cycle/case `8/8`，state `7`，open year `1116`，runtime schema `2`，active `true`。
- roster：subject/before-prune/pruned `0/0/0`，amendment/audit `61/62`，reopen-required `false`。
- processing：count `0`，但旧 agenda/local-candidate/pre-calibration-valid 仍为 `132/132/132`。
- quota：book `2`，target `40/79/13`，recount `25/46/9`，pre-calibration expected `133`，mismatch `true`；
  `quota_rebuild_generation` 缺失。
- closure：state `0`，calibration-finalized/rewards-issued/publication-blocked 均为 `false`。
- pending：open/slot/expected/paid 均为 `0`，committed `false`，watchdog 字段不存在。
- 观察期间 20 次 timeline interrupt drain 均 GREEN；每次 product progress 仍为
  `b1_active=true / review_now=false / central=false / pp=false`。Stage 指针虽为 `9`，Central 因 B1 未发布而不可达。
- 汇总 artifact：
  `_runtime/p1-terminal-resume-r418-20260911/live-artifacts/terminal-stages-red-attempt-06.json`，
  `1,130,607` bytes，SHA-256
  `999828C356E88EB943A9E4CC22ACBF63BA294AFBAAFCA83FAE750C67D3342B76`。

同一 artifact 也闭合了 `tgp_movement_events.0070` 的第二次合法实例：authored `1` / native `0`，instance
`1108 -> null`，snapshot `native:2692 -> native:2693`，revision `2693 -> 2694`，
`postcondition_verified=true`。这项结果只把该原版事件合同升级为 production-live primitive；它不改变 B1 RED。

## 根因与生产唤醒缺口

现有恢复链各自覆盖了相邻状态，但没有覆盖 R418 的终态：

1. D+340 manager watchdog 只在 state `6` 重开 calibration；R418 已在 state `7`。
2. pending watchdog 只在 `pending_open_n >= 1` 时推进；R418 为 `0`。
3. final-survivor compaction 要求 closure `1`、reopen barrier 已消费且至少还有可重封的 processing 域；R418 为 closure `0`、
   processing `0`。
4. 年度京察请求与 common-superior sibling 请求都会因为 `zg361_b1_serial_dependents_active_trigger` 看到 active B1 而持续轮询，
   却没有在判 busy 之前修复这个 callback-free 状态。

因此根因不是观察时间不足，也不是新的原版事件合同，而是 B1 在最后一个 weak Character row 消失后缺少 manager-owned
零幸存者恢复入口。

## 最小修复合同

生成器新增 `zg361_b1_recover_empty_calibration_cycle_effect`。它只在现有玩家请求边界运行，并要求全部条件同时成立：

- `is_ai = no`、active flag、runtime schema `2`；
- state `7`、closure `0`、calibration 未 finalized；
- pending open `0`、oversight return `0`、publication 未 blocked；
- quota built serial 与当前 manager case 完全一致；
- Character-safe prune 后 subject 与 processing 均为 `0`。

命中后记录 recovery cycle/case/year，把遗留列表和计数清零，将旧周期置为 inactive/state `8`，保留 rewards 为 `0`，移除
open-year 与 review flags，并明确不调用 `zg361_b1_mark_published_effect` 或结算发奖。调用者随后在同一请求中重新检查 serial busy；
若 Central/PP 也未占用 serial，就调用既有 `zg361_b1_open_cycle_effect` 从当前 live vassal 域开启新周期。

唤醒点覆盖年度首次请求、既存 `.42` 两日轮询票据、common-superior `.90/.91` 请求以及 review-now bridge；
`open_cycle` 本身也在 eligibility 检查前调用恢复，避免其它合法玩家入口绕过。没有新增 on_action、console、fixture、AI 入口或公共 MCP/ABI。

## 当前验收边界

- B1 generator 生成 24 个文件并通过 `--check`。
- B1 runtime normal/`-O` 各 `76/76` GREEN。
- `validate_local.py` normal/`-O`、根 `validate_static.py` GREEN。
- ZhongGuo release tests `9/9` GREEN；1,031-file 可复现 release manifest / ZIP SHA-256 为
  `63443F986F873924B4B0AB4D17C32D052CE1E83A8A5A2836D4D83370F12B9B2B` /
  `647AB1A16941955536A5303E587516275B7A00319B1F2F1CABA107D8E9ECFE25`。
- 原版事件合同测试 `288 passed, 775 subtests passed`；portable evidence 为 `271` blobs / `1063` refs，
  manifest SHA-256 `EEF35766EF2E4C45EC834E3437C5D4769DD550309223472D7F49DC7D6BA48DA8`。

修复当前严格是 `static-ready`。游戏脚本无法热加载到 R418；必须先受控清理旧 PID，再以包含本修复的新 production projection 和
fresh CK3 进程恢复同一冻结 checkpoint。live 升级至少要证明旧 cycle/case `8/8` 被退役、新 serial 被打开，并最终获得无 anomaly 的
B1 state `8` / closure `4` / finalized，再恢复 Central 9–11 的正式 terminal 验收。T0 保持 `50% / stage 8/11 / P1 未签收`，
P2 视频继续锁定。

## R420 fresh 复验：调用点仍不可达

R420 用 commit `4cd6738b6fcdc2c62961971ddc951f5d5ca97b71` 的 detached code worktree 和 fresh 1,031-file
production projection，从 R418 attempt 06 前保存的零幸存者 checkpoint 启动新 CK3 PID `197452`。preflight
`18/18` GREEN；启动前 checkpoint SHA-256 为
`00E61D505A05C39F953C815AC6FB79F88DEEBA8B16CF246C87FAA94693F81E1F`，release manifest / ZIP SHA-256 为
`09E7962DFDAA63D9650BA74BEEBEE4C481850095C099315F11E3D35596A2DC6F` / `647AB1A16941955536A5303E587516275B7A00319B1F2F1CABA107D8E9ECFE25`。

fresh 进程从 date raw `54114528` 推进到 `54251808`，约 `15.7` 游戏年。B1 始终保持 cycle/case `8/8`、
active/state `true/7`、roster/processing `0/0`、closure `0`，恢复记录和状态迁移均未出现。这证明恢复 effect 的精确条件
并非唯一问题：现有 wake-up 调用点在这个演化存档中没有被触达。attempt 01 随后因同一窗口第二次合法出现
`culture_notification.1111` 而在选择前暂停；汇总 artifact SHA-256 为
`70B27E1064482C11FAE20CB730ED255755BDC5B70F1EAD1C048209EB31806866`。

代码调用图给出与实机现象一致的最小解释：年度 dispatch 在进入 `zg361_issue_jingcha_mandate_effect` 前要求当前玩家仍是
celestial liege；`.90/.91` sibling ticket 也把恢复调用放在同一资格门内；`.42` 只有旧存档已经持有 pending ticket 才会执行。
该玩家仍拥有旧 B1 manager state，但长期演化后可能已失去当前天朝资格，因此所有已有恢复点均可合法不运行。

下一修复把同一个严格 recovery effect 前移到 `zg361_jingcha_annual_dispatch_effect` 顶部、当前 celestial eligibility
判断之前。年度 pulse 本身是已有 `yearly_playable_pulse` 玩家入口；effect 内仍要求 `is_ai=no`、active/schema/state、
serial 与零 survivor 全部精确匹配。失去资格的旧 owner 只会无奖励、无发布地退役残留周期；仍有资格者可在同一次年度 pulse
继续进入原有开新周期路径。当前结论仍为 `static-ready`，必须用新的 fresh production projection 再次恢复同一 checkpoint
验证；R420 证据不把这一根因解释冒充 live 修复完成。

## R422 复验：`yearly_playable_pulse` 本身不会覆盖失地玩家

R422 从 R420 attempt 01 冻结的零幸存者 checkpoint 冷启动 PID `22264` / connection generation `1`。输入
checkpoint 为 `197,968,111` bytes，SHA-256
`85AD59742D62D26740AC7786D890C94F080224E5F782EA1298B8CE46B0A5505C`；production tree SHA-256 为
`4D1D611BE25FE1C2D21F7716D8E785E269BA108C75FF7AE5D2EA3F7EFCF2AEEA`。该候选已经把 recovery 调用移到
`zg361_jingcha_annual_dispatch_effect` 的 celestial eligibility 前，但入口仍挂在 `yearly_playable_pulse`。

attempt 02 从 date raw `54251808` 推进到 `54481488`，共 `9570` 游戏日，离既定绝对截止只剩 `620` 日。
B1 在最终 paused frame 仍是同一 cycle/case `8/8`、active/state `true/7`、roster/processing `0/0`、closure
`0`；这说明不是 dispatch 内部资格判断阻止恢复，而是该角色根本没有再收到 playable pulse。原版 exact-build source
明确注释 `yearly_playable_pulse` 只对 count+ 角色触发；同一玩家在本存档已失去相应身份。

因此生产唤醒点改为 `yearly_global_pulse` 的扩展 on_action。原版定义明确它每年 1 月 1 日触发且没有 ROOT；扩展只执行
`every_player`，再调用同一个严格的 `zg361_b1_recover_empty_calibration_cycle_effect`。effect 内的 `is_ai=no`、schema、
state、serial、pending 与零 survivor 门保持不变，不会把恢复入口扩给 AI，也不改变正常周期。`yearly_playable_pulse`
的既有年度业务链继续保留。

本次 RED 还实见 `tgp_movement_events.0060` 在十年 cooldown 后第二次合法出现；旧事件合同的
`max_occurrences=1` 独立导致选择前停车，不改变上述 B1 判决。原版 caller 与重复边界见
[tgp-movement-rival.md](../ck3-native-ai/tgp-movement-rival.md)。

证据与清理：

- B1 after：`b1-after-attempt-02.json`，SHA-256
  `53809BDF64DA162A6C4E6A50775EFEC180FAD59DF494485998736F213FC82D43`。
- retained RED：`terminal-stages-red-attempt-02.json`，SHA-256
  `AD3F9517ADBEFACA1E59ADF6F01D73A1B950DFD631401D23241D2B0BA1BB754E`。
- partial checkpoint：`terminal-partial-attempt-02.ck3`，SHA-256
  `9B8CA99765BC1AD78ADE1B3EAB6417060C7FFC29C9C942D88C8F29EECCAF7B7F`。
- canonical / operator cleanup 均 GREEN，SHA-256 分别为
  `8EEDE1FAEE4E2934111727DFC3EB5C7D5557D38FF111DED57C10C1FAA8B637C2` /
  `B933751884608D645FFA1F7B7C6624007DA91BB0ED385507BA0AE70EE3508BF6`。

按项目所有者明确要求，下一次 B1 验收不再重复完整 `10190` 天产品窗口。它只从同一冻结卡死存档跨过最近一次
`yearly_global_pulse`，随即查询旧 cycle/case 是否退役或重建；该最小后置 GREEN 之前，修复状态仍为 `static-ready`。

## R424 / R426 短验收：排除 global `every_player` 路径

R424 首次执行严格 370 天短验收，在任何游戏日期推进前命中只读探针重绑定竞态：恢复时间的 ACK 已提交，但缓存帧仍短暂标为
paused，B1 query 因 revision 已前进而在提交前拒绝。该 attempt 保留为 harness RED，没有产品状态变化；汇总、canonical cleanup、
operator cleanup SHA-256 分别为
`40CE6F68E5ADA7A659B49308B9F873CAE6E103F1B299B59567DB07549677067C` /
`F6994C2A6D1A921E2ACDD97801C44EF41E40FCCB84C523BBC1259CE98248885A` /
`7E4C2161F06CDD8902B2AF48827304B94644A7F594280CC7117A6BBBBDF0C49B`。

R426 只让该只读探针在这组已知、零提交的 stale-binding 错误上等待下一帧，没有改产品、checkpoint 或时间窗。它从同一
date raw `54251808` 推进到 `54260712`，即在 370 天绝对截止后第一帧停止；整个窗口没有观察到 cycle/case `8/8` 从
active/state `true/7` 退役。汇总 artifact 为 `200,817` bytes，SHA-256
`EC0215A297935CA241ED0819486F2E46AC9CA0D9548D80D5D046EF7BABDC4A0E`；canonical / operator cleanup 均 GREEN，
SHA-256 分别为 `64BED75B4A7DE80C004AE3FF2F66DFA3CA9CC0CDB23A3E375FE4AE57602F8728` /
`990C0A58DE57DD42081F66C8BEF9A14D661F767B7A76BD5DC453315C80E0F09E`。

因此 `yearly_global_pulse -> every_player` 在该真实失地玩家上不可达；这次短验收已经否定 R422 的唤醒假设，不应再延长同一路径。
原版 1.19.0.6 `yearly_on_actions.txt` 明确 `random_yearly_everyone_pulse` 对所有角色逐个触发，且 root 就是该角色。
生产唤醒点改挂这个 pulse，自定义 on_action 用 `trigger = { is_ai = no }` 在入口拒绝 AI，再调用原有严格 recovery effect。
新的实机复验仍从冻结零幸存者存档开始，只推进到该角色下一次 everyone pulse，保守最多两个游戏年；命中 state `8` / inactive
后立即停止。当前依然是 `static-ready`，不把 R426 RED 写成已修复。

## R428：everyone pulse 到达窗口仍 RED，根因改为完成态门禁

R428 使用 commit `3438eb1373426cfe0034a99cb2f61779648c8ca7` 的 fresh production projection，从同一冻结
checkpoint 开始，严格限制为 `740` 游戏日。product tree SHA-256 为
`188C9D46FFAD61F2175CB5CDA2B97375614FB434B103C3AB3B47230F9C2C5089`；projection receipt SHA-256 为
`23CFC1F53F2985F8D55E340B6CC3845914A00DA569AB55F91A668F71F31384EB`。运行从 date raw `54251808`
推进到绝对截止 `54269568` 后按预设边界停止，B1 仍未退役。retained RED 为 `349,273` bytes，SHA-256
`3854846678DF402C55AF7E2D1434F89FE7492FF6EFE37FC0A486C5B51DAA059E`；canonical / operator cleanup 均
GREEN，SHA-256 分别为 `93079AC39831DF6030CB30EA71591C08D8927910464A7A5F3CC32FB405D2A560` /
`7DD7CFBA6D84E75174C1D632D869D498582A9D6E4B179AFB209DACDFA050342F`。

这次结果否定了“只要换到 everyone pulse，原恢复门就会通过”的解释。逐项对照 frozen query 与恢复 effect 后，唯一未由
B1 snapshot 暴露的前置字段是 `zg361_b1_oversight_return_status`。生成源的状态机给出确定语义：`0` 为未发起，`1` 为
一日延迟的跳级复核回调在途；`zg361b1.124` 只有在 `1 + state 6 + publication_blocked 1` 时消费 ticket，然后先把状态写成
`2`，再恢复 `state 7` 并清除 publication block。状态 `2` 因而是**回调已完成**，不是仍有回调。旧恢复门只接受 `0`，会把
合法完成态 `2` 永久拒绝。R418 的 `state 7 + publication_blocked 0 + pending 0 + zero survivors` 与该完成后形态完全吻合；
由于 snapshot 没有发布这个字段，这里明确记为“源码状态机 + R428 排除结果”的根因推断，最终由修复后同 checkpoint 的后置状态验证。

最小修复只把恢复门改为接受 `oversight_return_status` 的 `0/2`，继续拒绝唯一在途态 `1`；其余 schema、active、state、closure、
calibration、pending、publication、serial 与 prune 后双零门全部保持。`random_yearly_everyone_pulse` 入口保留：R422 已实证失地
玩家不再收到 `yearly_playable_pulse`，若没有这个玩家专属低频入口，完成态门修复仍不会自动执行。该结论当前为
`static-ready`；只再做一轮同 checkpoint、最多 `740` 游戏日的目标复验，观察退役后立即停止。

## R430：完成态门禁修复 production-live GREEN

commit `4553a429f69d1df15d31d59e14300067c7c33320` 只把恢复门的
`zg361_b1_oversight_return_status` 从“必须为 `0`”改为“允许 `0/2`、继续拒绝在途态 `1`”，没有改变奖励、发布、
quota、closure 或正常周期逻辑。fresh production staging 共 `1,031` 文件，tree SHA-256
`84443728419E390024936809778C98D4BF4B529747FF776DE0F2FD4DC97E58CE`；projection manifest SHA-256
`383EFCCC7BE736C226441C1F6D502D614E3608CE687A053EFF024CC297AEFE86`。

R430 从同一冻结 checkpoint 的 cycle/case `8/8`、`state=7`、active、roster/processing `0/0` 开始。runner 的硬上限仍为
`740` 游戏日，但实际只推进 **148 游戏日**便由目标 probe 观察到同一 `8/8` 变成 `state=8`、inactive；roster、processing、
agenda 均为 `0`，`rewards_issued=false`。十项后置检查全部 GREEN，命中后立即暂停，没有继续运行其它 mod 场景。

live artifact 为 `b1-minimal-wakeup-live.json`，`47,994` bytes，SHA-256
`4AB0EE070EB686DB8737AF5086516FF412E2C4E297B7F3BC17FF32774FEF782E`。canonical / operator cleanup 均 GREEN，
SHA-256 分别为 `9D3FCCBE60B3929694587180E31808F47C23ED2AD76A95F8C7819DAF3BF9C028` /
`5FF5F2BC4FE9A342FF047C08800A4F78F12C70FFC8C24E311B6CA757E79E311B`；CK3 与 operator 进程均已退出。

B1 零幸存者永久卡死 bug 至此关闭，能力等级从 `static-ready` 升为 `production-live primitive`。该 artifact 只证明遗留空周期
会无奖励、无发布地安全退役；它不单独证明新周期完整 publication，也不代替其余 P1 收据或最终 evidence assembly。除非以后
B1 状态机再次改动或出现新的可复现回归，不再重复运行这个 checkpoint。
