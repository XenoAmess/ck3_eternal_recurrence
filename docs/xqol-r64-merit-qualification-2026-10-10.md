# QOL R64：贤能任命资格缺口与等级诊断修复

2026-10-10，Source16 R0064/a165原启动资格、两个初始业务步骤及campaign/government root实际PASS。这为bootstrap44提供本场root实际成功证据，不改写R62/R63。玩家31883为独立贤能制皇帝，日期53144328、PID14200/generation1。正式迁移仍7/10（70%）。

## 业务与闭场

原GUI及独立title-holder查询绑定的d_haeju16982/holder27139全池5人、自然下级c_gokju16974/holder35161全池40人均为AI，玩家31883均不在池，实际法律均为meritocratic_appointment_succession_law。原合同要求玩家自然合格入池，因此保留资格GAP；没有玩家分数或开关修改，百万分差OFF→ON→restored、实际GetHeirID及任命继任均NOT_RUN。等级、冷却与完整资格原因仍未观测。

原2步/0自然日、3000秒timeout/1800秒hold/90秒退出预留、300秒command/400秒readiness/poll0.05保持。最初误写序号1的mailbox请求没有被消费，328B原字节保全；确认序号0不存在后才首次发布0，随后独立县领请求使用合法序号1，没有重放已消费查询。

public run2/verify2、业务与产品PASS均false；normal_close_qualified=true、retained OS exit0、strict native0、三项closure true。原allocator7261由operator本人实际poll exit0，keeper0、CAS8348 done/resources[]；finished11:46:53.979646Z。正常退出不改变业务GAP。

- [最终薄field](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/meritocratic_appointments--a165/ROOT-FIELD-RETURN-R64-02.json)：12216B / SHA-256 d27c70420001bde9f4cb524cf8b2ba9c78a91722cef87fdd31383ea74e392ea5。
- [POST](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/meritocratic_appointments--a165/POST-RUN-CLOSE-05.json)：3680B / 300d1e0a39d628f6ce6f16126f2b1e0a15b0e29dea5758893a7e34cdfbb5cdc1。
- Source16 runtime：15232B / a3cd2dc5b00f2e3aee03ed3aec13eb15034533b3ed6447a9957fc5ddcf1084e3；已消费merit prepared：26078B / bf5cf9a5d7f88fc4c232c03fce74274b35c03a35e47c46a16d494de1482844ab，不改写为后继输入。

## 独立观测故障与修正

一次既有MCP等级诊断在11:37:22.159397Z成功返回transport，但available=false、exact4_current_rule_lease_required，等级/上限/累积值/门槛全null。这不能证明等级0或玩家不合格，没有第二次查询。

静态调用链证实：生产admission/binder传入ck3_12004::kExecutableSha256的规范大写SHA，新leaf却复制小写字面量并区分大小写比较，误拒合法来源。最小修正让生产leaf与既有focused测试共用该常量，保留module/read/rule/title、ordinal、完整角色身份及双采样守卫。[补丁原件](C:/workspace/ck3-upgrade-20261010/r64-qol-level-current-rule-lease-diagnosis-01/R64-CANONICAL-EXECUTABLE-IDENTITY-LEAF-01.patch)1577B / fbeb5f9b3aa156c037176c6d4433d8690394dfccd2885d14f658a888c36bf364。只重编1个生产对象与2个focused对象，其余572对象及库复用；编译、执行及后继live事实另行追加，静态定位不授PASS。

## 复用与范围

cbc789aeae0e23572f7627bd1a7db11b9c497f9d的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38048260010)实际66 success/20 skipped/0 failed/0 pending，static114202054673、shared acceptance步骤33成功并覆盖原followups9项。API终态实际回读11:34:26Z，不外推后继HEAD。

[QA07→QA08窄来源比较](C:/workspace/ck3-upgrade-20261010/qol-qa07-08-projection-equivalence-01/ROOT-QA07-QA08-NARROW-PROJECTION02.md)实际27文件中25个pin相同，另外2文件只变3个改信准入/派发顶层块。政府及领主赎金依赖文件、7个释放交互和8个结果回调块相同，可支持原合同已通过结果在未变生产块上的有限来源投影；不授整产品/runtime/fixture等价或新增业务PASS，3个改变的改信块不在投影内。QA07已使用send_interaction，不是execute→send差异。

后继只替换共同native，精确复用Source16 Python/host；未消费输入只更新manifest sibling，PAM+新只读fixture必须新public prepare。剩余QOL、重整河山及361既有版本维护按[用户职责纠正](handover/2026-10-10-non-phase2-mod-migration-scope.md)推进，不接手G2或天朝二期。


## 最小增量实际验证

实际生产leaf编译0、focused两个CPP编译/链接0、10项bounded mock执行0（0.367s）、完整DLL链接0（1.375s），总177.850s、children[]。首次vcvars引号入口exit1及focused旧obj被/TP误当源码的exit2原件保留；仅修环境入口/对象位置，未放宽生产flags或代码守卫。精确新focused EXE已取得Defender实际verified回读。Root另将Main两CPP逐字节pin与实际编译输入核对一致，不重跑该测试。

[实际构建final](C:/workspace/ck3-upgrade-20261010/r64-appointment-level-canonical-sha-build-02/NATIVE-CANONICAL-SHA-BUILD-FINAL-01.json)：3874B / SHA-256 86017d74c5517614e8565c534433199ee7376d5ec0da5b0d40acc86d477709f4。新DLL9078784B / 0394832898affec2c7d964ee16e1a0137c8db44d4a9e915f63941a489512419b；组合source index4129051B / 2ef1683163e02e0a8404191197f49d0637c3414752d268e0f8c2523419a83c8d，6915行沿用原author、2行指向新overlay，旧27db不变。BUILD/focused PASS不代表后继实机或业务PASS。


## Source17已实际选择，原生产包装失败保留

Root在7bb27aaea7f4f4e1662ce853b75f2c558ccf3259 clean状态下，对已生成的Source17执行原公共CLI plan，实际exit0/stdout4774B/空stderr/blockers=[]，随后唯一选择。[选择回执](C:/workspace/ck3-upgrade-20261010/root-resume-05/ROOT-SOURCE17-SELECTION-01.json)3768B / SHA-2567202d32f065cefa8e57e2826c246c2e957f4a42b1f655dd388e33562273af3ff。runtime14993B / 171dca156f6e0f7b318e8c319c209164067975f4f2bd8fcccccc9fa32335e31a；manifest44851B / f95886251b1746a85896232c41a0c850cfbab8b062854cf374d88723d1ab0f56，位于C:/workspace/ck3-upgrade-20261010/shared-native-canonical-hash-ready-01。

Source16 Python source index d97dc649…与host ed91b819…原路径及pin精确复用，native替换为实际03948328…DLL及组合index2ef16831…；没有复制Python树、重编572对象或重hash未变正文。现有公共入口只核原生索引文件pin，可绑定完整6917行组合author，partial overlay不冒称完整物理树。尚未给予新DLL实机或产品业务PASS，已消费R64不改写，未消费prepared须精确manifest sibling，新fixture须新prepare。

生产器原五件FAILED及后继诚实failure说明保留：额外-P造成同级模块导入失败，随后wrapper重复保存stdout/result超小输出cap、可信plan0未保全。六件80921B/children0，elapsed195.853034s超过原180s，不能称生产包装按时GREEN。Root没有重物化，直接既有CLI的独立实际plan0才是本次选择依据；plan只证明合同可绑定，不代表正文全验或游戏通过。
