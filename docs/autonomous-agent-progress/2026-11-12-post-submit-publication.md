# 普通后验观察保留真实派发时间界

普通事件在真实成功 ACK 后观察到的 publication 必须不早于原 submittedAt。原 held transport 可能先交付此前已接收、尚未投递的真实 snapshot；直接把第一帧当后态会被正确的时间守卫拒绝。

本单元仅让普通 after producer 在原 deadline 和最多4096次接收界内跳过真实 pre-submit publication，继续接收真实后帧。每帧仍通过原完整 Driver/native assembler；不添加 Native 出站查询或控制，不重写 snapshot 时间、request ID、parser、hash 或原259／298守卫。有实际私域 after 时仍使用该私域结果，私域失败不落入普通采样。

原完整9项测试与新增2项时序回归最终11P／0F／0E；新增用例覆盖排队旧帧→真实新帧→归档回放，以及旧帧后接收失败不得制造完成。原 pending 用例的两分钟真实等待保持。旧软件夹具的 diagnostics、CK3 rawDate、完整材料读取接口与 JSON state token 外部换行依次修正；原 Unknown-dispatch 用例已经断言 Settled Applied，却要求 visibleGameplay=false，与既有 ActionReceipt 合同矛盾，现仅纠正为 true，eligibleAdvance=false、原 Unknown 和无 invented accepted ACK 的断言保留。所有首轮失败、等待和修正输入均保留，没有裁剪最终完整类。

生产单 TU 的完整4类、最终测试3类与原 Helper3类均按真实首编/复用关系验收。正式两叶的 BASE 与已验证实际 BASE逐字相同，候选也逐字相同，直接复用原软件资格。Native 软件交付索引为 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/SOURCE20-SOFTWARE-READY-WHOLE11-AND-COST01.json`（5104B／`bd19d9e09d3e36e45a58ed1aa8c15fbeb654ff8df9c23df587792107418a2765`）。新增 private overload 是结构变化，不据此外推任意原地 redefine 能力。

Runtime44已在必要同局恢复边界采用该唯一实际叶；随后正常 Event13 的620原动作真实 APPLIED，submitted01:00:52.9564789Z，observed01:01:16.3577437Z。该事实证明本次实际后态时间守卫通过，不证明内部 skip 分支必然命中，也不追认原495的唯一坏 after packet 来源。620后续材料由独立 Source35完成622 RETAIN／623 SETTLE为 C25，未重发620、未新增推进或保存信用。

saved仍8日、年度普通保存政策不变；没有新增确认保存日，不报告有限秒／新增保存日。本单元不包含未来 Life physical-after-ACK协议或性能投影候选，它们的类型加载、真实 witness 与运行行为分别待各自回执。
