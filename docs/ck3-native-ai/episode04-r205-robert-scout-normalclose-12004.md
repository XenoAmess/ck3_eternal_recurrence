# R205：Robert 的只读探路、补员目标筛查与正常闭场

`machine_id: desktop-3fevhd2-1c74096080`，run
`desktop-3fevhd2-1c74096080--vanilla--R0205`；实际观察为2026-10-18 UTC。
本场角色是 **Robert31254**，date53148192、Army18@2635。William 属于另场，不能反向
改写这里的角色身份。实际runtime/native source为
`19024b4d79d818a88709c9932ca4eb364d81ef33`，a35生产资格16,198B/SHA
`a80af8f9df7ca2a2ba56e474cb4092654e8f0782908b63f8278672534e6e2f67`。
绑定PID23676/create134367624036178149/gen1/episode `native-31254-7a037a02690d`。
归档所用后继Git HEAD不追认旧进程的部署版本。

这次完成了有界scout和正常闭场：**0 Move、0新日、0录像**。研究9/14、业务6/11、
合格动态0/11、ABC0/3及正式cue数均不增加。该结果提供下一步决策依据，没有取得R04
实际跨县正例、行军损失、R06兵员ADD或共同因果token。

## R04：可用preview的实际首边仍是同县

War4的原生holding集合完整27行，defender3、attacker24；玩家为attacker。Army18所在
2635本身不作新的探路目标，scout考虑2636和2644两个候选。实际source frame为
native_revision3/public_revision4，前后public revision均4、date53148192，same-frame fence成立。

| 请求目标 | 原生preview路线 | 实际首边 | county_objects_differ | native_condition_passes |
|---|---|---|---|---|
|2636|[2636]|2636|false|false|
|2644|[2645,2644]|2645|false|false|

两条preview都available/accepted，native condition实际调用并返回false，身份前后匹配。
source和first-edge county identity同为 `native:2212927206480`。2644的请求目的地不能替代
实际首边2645来算条件。[preview条件合同](episode04-county-entry-preview-condition-12004.md)
和[县入口机制](episode04-county-entry-condition-12004.md)仍要求实际输入与原生后验。
这两次查询没有执行Move，不能讲成军队已跨县、已损失兵员或已抵达。

历史2644路线提示只作旧来源；本场不把旧first hop变成全局排除规则。下一次局面变化后，
仍需用真实war holding和新preview取首边，再判断原生P。当前没有native-true候选时，
停止提交Move，保留这次有范围的否定结果。

## R06：两种q模式都没有可观察正例目标

`R205-Q-SCOUT.actual-a02.json`为832,816B的既有离线sidecar。它保存两个完整Driver
JSON的原始引用及共享projector投影；不是新造MCP packet，也不是原始pipe bytes。
本归档携带sidecar和小query receipts；11MB Driver本体只保留已有pin，未打开、未重hash。

| 模式 | physical slots | final_shared_q_i32=0 | position true | false | unknown |
|---|---:|---:|---:|---:|---:|
|fixed_chunk0_prepare|147|147|0|21|126|
|observed_prepared|147|147|0|21|126|

两个模式均无 `conditional_positive_target`。unknown126保持unknown，不能填成false，
也不能把所有physical slot都叫实际ArRg DATA。sidecar保留raw physical rows、ordered
occurrences与DATA aliases，模式的input_basis也原样保存。

Root因没有合格目标而未安装probe；本场没有natural/core/ADD共同token，也没有实际兵员
ADD。[R199位置与准备边界](episode04-r199-refill-position-preparation-12004.md)仍适用。
后续先在同一新鲜frame找到完整DATA identity、position=true且最终shared q>0的目标，
再按原实际scope准备观察。当前q0不能被改写为全局永远不能补员、特殊兵重新分类或人数cap结论。

## schema RED、真实OFF与正常闭场分开保留

原 `r205-off-natural-query-a01` 传入 `expected_revision:null`，在MCP参数schema层因需要
正整数而失败，body=null。这个RED没有进入原生predicate，不计作native condition失败，
也没有被a02覆盖。后续natural和regular query均用实际public revision5；返回绑定
native_revision4、date53148192、同episode与actor。不能用native revision4替代public5。

两族a02实际readback均installed/available、capture_enabled=false、busy=false、active=0、
retained=0、clear_completed=true、epoch0。这是**natural_phase与regular_core两族**的
实际OFF读回；没有由query触发一次disable，也不外推所有观察族。

正常Save metadata于02:46:19 UTC保存同一actor/date；文件3274B/SHA
`8ff12db862de5eb717773c4967f2f9571facbc2709e2dd6dd16d3872d2a65c09`。
它记录checkpoint73,689,226B/SHA
`a26b5eb55ec42b870533fe24714a2690bc1ae843e9bc5e1de09957100920b71c`，
本包引用该既有checkpoint pin，不复制或重新hash大存档。
natural OFF于02:52:14、regular OFF于02:53:04，均在Save后、最终Exit前。

bootstrap随后实际process_exit0，SDK thread退出、process tree cleanup_proven；recorder
为NOT_STARTED。02:58:33的SCREEN-RELEASE4817B/SHA
`4191692a60507b52dcca1bd46678a70dcbc8bb2b25b74252a845c82669eb13b6`
记录CAS6394 done/resources[]、exit_code0。BOOTSTRAP-OBSERVED中screen_released=false是
CAS之前的独立时刻，后续实际release原件保留。

close helper的 `observer_cleanup=NOT_CONFIGURED` 指没有配置pre_resume_hook；它不能
抹去Save后、Exit前的具名手工OFF证据，也不能被手工读回改写成自动hook已部署。
完整原件同时保存这两个职责层次，保存/关闭成功不授业务或视频资格。

## agent与视频可以复用的结论

- agent：preview可用时仍检查真实首边的原生条件；无true候选就保留范围、继续另场合法筛查。
- agent：q0或position unknown的slot不作为补员正例probe目标；未知身份、模式和DATA alias不补成0。
- 视频：可讲解“实际有界筛查没有找到目标”，可展示上述两条typed preview与表格；本场没有实拍片段、
  跨县损失或补员ADD镜头，不能填入动态合格格或正式cue。
- 工程：显式控制工具使用fresh public revision；schema RED、原生结果、独立OFF和闭场分别记录。

[小型来源索引](evidence/episode04-r205-robert-scout-normalclose-12004/source-index.json)、
[可读投影](evidence/episode04-r205-robert-scout-normalclose-12004/summary.actual.json)与
[便携原件ZIP](evidence/episode04-r205-robert-scout-normalclose-12004/originals.zip)随专题入库。
纯stdlib回放命令：

```text
py -B -X utf8 docs/ck3-native-ai/evidence/episode04-r205-robert-scout-normalclose-12004/verify_portable.py
```

回放只读ZIP内原件与literal投影，不打开来源机器的绝对路径、11MB Driver、存档、媒体或EXE。
可跨机器核历史内容，不授目标机器安装、运行时、Steam/SYSTEM、容量或实机资格。
