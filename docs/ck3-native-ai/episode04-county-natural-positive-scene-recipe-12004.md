# R04 下一场：一次自然陆路 county positive 的最短模板

当前可具体执行的下一步是**只读侦察2645方向**，还不能直接提交一个已证县损耗
目标。来源为R0177最后的小快照048：Army18已在2635、正在围城、路线完整为空；
War4发布敌方默认征召点2645。没有2635→2645的实际preview，也没有该方向第一站
的双definition字节或native县条件。因此 `selected_target_province_id=null`，
不把2645称为相邻、陆路、敌方领有或跨县正例。

本机 `machine_id: desktop-3fevhd2-1c74096080`；准备基线
`b42afbbd85df3802b1fa6222f7aac403c2adf735`，观察时间2026-10-15 UTC。
下面都是Root在下一scene调用现有SDK工具的模板；本准备包没有联系SDK/桌面/
游戏，没有新读EXE、构建或写主仓，也没有实现selector或新API。

## 已有实测边界

048为 `048-r0177-terminal-snapshot.json`，131276B，SHA256
`d2485c2290c5b6ebf70ee40c7a6f70efce0223afbdc6ff4f9833ecfc8dc0f4b1`，
原envelope `at` 的精确时间和机器pin保存在本包交付回执。
body date53147472、paused=true、
snapshot native:117/public118/native117、actor31254，episode
`native-31254-00b796ef873c`。`/body/player_armies`的Army18位于2635、
controllable=true、非combat/retreat、route complete_empty。其soldiers=null，
不能用该快照推断fresh whole/B/S；war objective的besieging_strength也不是整军输入。

049为 `049-r0177-terminal-normal-checkpoint.json`，20316B，SHA256
`ba5cdec0ce9a1c04ba24f2a76007143e4ac2afe5555140c307703ceb3b3cee1b`。
这里只核保存receipt；没有读、hash或复制save。R0177的frame、Army完整ID和
checkpoint事实都不能直接充当当前R0178或以后scene的新鲜准入。

043已strict消费的旧边1032→2635为actual definition1B **0/1**，condition
available/false，Unit170原值及conditional post-entry值均0。旧Move的实际路线
是8645→[1032,2635]。这些解释landing县路径旁路；后续R03 siege positive不能
当county。下一场必须取得**两byte均非零且native condition=true**的实际第一边。
地图海陆标签、敌方目标名、领有猜测或B100本身均不能替代这两个原生条件。

## 只侦察一个有来源方向

1. Root完成当前R07pair并建立下一scene后，用现有
   `ck3_take_snapshot(include_native_command_history=false)`取fresh暂停frame。
   核运行身份/actor/public Army18→actual CArmy身份、owned/controllable、非
   combat/retreat；不能用本页旧R177 PID、revision或日期填入。若actual起点不是
   2635或fresh war不再发布2645，2645只是历史种子，先重读现有war目标，不提交它。
2. 若fresh仍是这组事实，核 `ck3://capabilities`现有action steps包含对应preview，
   然后**只调用一次只读preview**：

```python
R = fresh_snapshot["revision"]       # 本次实际int，禁止复用118
request = {
    "tool": "ck3_execute_step",
    "arguments": {
        "step": "preview-move-army-18-to-2645",
        "expected_revision": R,
    },
}
```

这复用已有 `preview_move_army_step`。b42的native_driver31834–31837会把实际war
enemy_default_raise加入既有目标集合；31963–31964发布preview。这里证明的是
已有scouting通道，**不是实际preview已成功**。若step没广告或返回unavailable/
空route，保存原诊断，目标继续unknown；不按省份数字邻近猜替代目标。

3. 验preview的available、army18、actual origin、target2645、queried snapshot/
   revision/native/generation/episode与fresh一致，`previewed_date_raw`等于fresh
   日期，route真正到2645。按已有driver14611–14625去掉可选起点前缀；得到
   `remaining_route`。其首项P才是**侦察得到的第一站**。多段时复用已有driver
   32160–32167对firsthop的广告，再只读preview18→P以证明这一边；不写新selector。
   现有小索引没有P，当前不得预填Province。

## 一次Move，先暂停核县准入

沿用Root既有身份、合法性和contact守卫。fresh同frame、非combat/retreat、
owned controllable、P不同于actual origin、现有step合法并已取得exact preview后，
只提交一次现有typed Move；这里的P只能来自刚才的firsthop，不是2645的默认别名。

```python
request = {
    "tool": "ck3_move_army",
    "arguments": {
        "army_id": 18,
        "target_province_id": P,
        "expected_revision": fresh_revision_immediately_before_move,
    },
}
```

现有typed Move已经要求paused ready map、owned noncombat Army及expected revision
（native_driver8882–8921）。ACK后核实际postcondition、stored route、exact origin/
first target仍符合preview；未知结果不重复Move。**此时先不推进日期**，用已有
`ck3_query_army_strengths(army_ids=[18],expected_revision=<actual post R>,
profile="ordinary_core_v1")`取县child，并保留response-local完整结果引用。

同query `/army_strengths/i`按army_id查i。推进一边前只需这些现有观测：

- `county_entry_inputs_v1` available，native B>0；condition available/true，
  exact actor/source/target/mode绑定实际stored first edge。false或缺值则这次还没有
  R04 positive候选，保持暂停，不为正例强行推进。
- `current_movement_progress`里actual old/first-target definition1B均非零，
  typed distinct Province、Unit kind0；既有movement prefix ready并给出conditional
  post-entry Unit170，使special flag0。Unit UI状态码不能代替170。
- 同帧loaded floor child原值或明确unavailable；不补0/100000，不用R177的floor
  代替fresh leaf。native B与getter取整结果原样保留。
- `loss_application_inputs_v1`的whole与县whole一致、S_pref可读。最短正例优先
  S_pref≥B：conditional P=B、R0，只等primary；不要求残差分支另出token。
- actual writer observer installed；保存latest_sequence和unattributed failures、
  完整当前regiment FullID，以及运行/查询frame，作为这一observer lifetime的pre fence。

现有公开县condition只针对stored first target。preview成功本身不提供该native
boolean；所以在不新增query/API的约束下，不能承诺Move提交前就知道condition=true。
这个“暂停提交路线→同帧读条件”是最小缺观测步骤；没有必要先试走多个县。
`敌方不领有`和`跨县界`仍是候选解释，本文没有它们的逐目标native证明，不作为guard。

## 自然到达和一笔物理debit的验收

通过上面fresh guard后，由Root既有自然day/first-arrival流程推进**这一条边**，
到实际P即暂停，不按预测日期直接宣称到达。随后一次同Army ordinary_core查询，
其现有actual writer family在history profile守卫外，足够消费retained writer。
不需要额外full-history query、新hook或按军队净少人归因。

复用 `classify_retained_loss_writer_window_v1`，输入完整writer family、当前FullArRg
ID、实际绑定EXE SHA、pre latest/failure fences。县primary raw return必须
`0x24E25EE`；native caller_kind=other不能将其滤掉。若S<B实际走residual，则还需
inner `0x2A958E8`、source-complete county_entry parent、outer `0x24E2630`、flags0
及actual CArmy/array/writer身份一致。flags0单独同样可能来自siege。

现有physical consumer须验same-instance、complete DATA alias/unique-slot覆盖，
原始物理current before−after的unique sum等于actual debit>0。request、预算、
Army/ArRg缓存净数都不能替代。若没有合格县事件，结论是尚未验得R04 positive，
不是全县损耗0；窗口覆盖和clock缺口保留unknown。R03 siege与periodic按各自
caller/context分开，不能用同日或相邻seq合并。

短口播：“我们已经从海上落地，但上一条边的旧字节是0，不能拿它演示县损耗。
下一步先用现有路线预览侦察2645方向，取它实际第一站；只有双字节非零、原生
条件为true才推进一边，再用writer物理槽确认真正扣了多少。当前还没有选定目标。”
