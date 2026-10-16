# CK3 1.20.0.4：真实 callback 的 type635 entry 候选读口

在现有 `ck3_inspect_gui_window_tree_v1(window_kind="military")` 上增加可选只读叶。只对已证finalkind3/chain0/type635/flag0/target1303D40的补员callback读取声明索引与定义entry。不会执行expression、provider或点击，也不发布任何receiver/provider/entry地址。

原生3AC38C0在调用时创建临时变量表，所以本读口固定 `current_variable_table_observed=false`、`native_receiver_selected=false`。callback+10 block的+98 declaration数组（8B每项、首DWORDkey）、+A4计数，以及+B0/+BC最后receiverindex决定候选key；只收key635。随后查真实callbackF0的context+E0定义表（+90/+9C、80Bentry、key+48），并沿definition+108优先/context+E8的父链收集匹配entry，不推断动态provider是否成功或哪项最终覆盖变量。

每项仅发布ancestor_depth、type+48、signed mode+40、flag+4C、direct+0/provider+38是否存在、合法image内provider vtable及slot2 RVA。mode1且direct非空才读owner+218，独立经实际.4 Character registry完整generation ID与Char magic校验。所有内部context/table/entry/direct/provider/vtable/Character指针及raw标量完整双捕获比较；公共输出没有堆地址。

数量/时间边界：每definition最多256entry、父链最多8context且拒绝循环；每leaf最多4096读、64KiB及20ms协作式deadline；每tree最多4个固定补员callback。超界、不可读或变化返回unavailable，不能解释为无补员/无provider。两个新增实际source body（3AC3EF0 879B与3AC1C00 449B）在owner线程以完整原字节校验，既有expression三body与thunk pins保留。

新leaf另需现mailbox owner/TLS/paused stamp、同ticket/epoch、读取前后完整snapshot与GUIowner/root一致。native frame token包含PID、connection_generation、native_revision、pump_epoch、ticket_sequence、thread/date/played FullID；driver再将它与前后public snapshot/episode绑定。旧tree无此资格时仍可返回原有census，新的entry leaf与token不发布。

Root一次采集可继续用既有MCP名/参数。另提供实际实现的 `ck3_autonomous_player/tools/capture_gui_refill_receiver_candidates_12004.py --enable-root-capture --repo-root <repo> --state-dir <fresh-state> --pipe-name <Root-admitted-pipe> --output <new-json> --expected-machine-id <machine> --expected-game-pid <pid> --expected-connection-generation <gen> --expected-native-revision <rev> --expected-played-full-id <id> --expected-date-raw <date>`。该脚本新建唯一native endpoint，只能由Root在原endpoint已释放且新build/current machine/scene已准入后运行；保存原response，不重试或开启窗口。

来源机器 `desktop-3fevhd2-1c74096080`，实际source15/16时间与完整字节见相邻来源专题；精确EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本候选未native build、未实机采集。Python反例只授consumer合同；native cold fixture保留为源码。下一实际dynamic slot2 RVA须来自新leaf，再独立准入唯一source entry；不授toggle、flag转移、actualADD或完整R06。

2026-10-16追加（同机）：Root已独立构建并运行该header-only冷fixture，Release构建显式`/UNDEBUG`使断言保留；目标EXE 33,280B、SHA-256 `d71f7e3cd788ae63c3dd634006a01db4fe3c4a760e44ac3465f271515dd363bc`，退出码0，SYSTEM对精确文件的Defender路径排除读回为verified。[小回执](acceptance/2026-10-16-r0181-first-edge/RECEIVER-FIXTURE.actual-a22.json)绑定构建与运行。上述“未native build”描述属于初始a18交付时点；现在仅冷fixture已验，完整Bridge DLL及真实military GUI leaf仍未构建/实机读取，不授receiver、toggle或ADD。
