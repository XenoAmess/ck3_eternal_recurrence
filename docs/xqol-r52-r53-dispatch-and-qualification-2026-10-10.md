# XQOL R52/R53：派发语义与夹具资格失败（2026-10-10）

本记录保留两场原失败，不授修后业务或发布 PASS。共同输入是 CK3 1.20.0.4/build25734779、EXE `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`、Source13/runtime05/native fd1f，以及冻结 MAIN `fde5fb0a03d24ba00b8a09ce0a52462a50882671` 的旧正式27映射。唯一现场执行者为 `/root/qol_scene_operator`。

| 原场 | 实际结果 | 原闭场 |
| --- | --- | --- |
| R52 / a153 ordinary | D0低分目标的原生 AI 资格检查已 PASS；原计划前5步通过，第6步 day001-no-fail 要求0、实际2。原DIAG为 accepted2/refused0/pending移除，low已改为ROOT的faith/rite且无原拒绝opinion；原“1接受1拒绝”及low拒绝后果仍 FAIL。不是低分资格未构造，也不放宽原断言。 | run2/verify2，case/business/release false；normal_close_qualified=false，retained OS0、failure shutdown/lifecycle true，strict native-zero normal证明false；keeper0/allocator0，CAS8121 done/resources[]。 |
| R53 / a154 PAM positive | 启动资格中 personal acts 与 personal mendicant fulfillment 两项实际false，资格门禁拒绝；业务步骤0，不能归类为奖励、异步回复或修后派发通过。 | run2/verify2，case/business/release false；normal_close_qualified=false，retained OS0、failure shutdown/lifecycle true，strict native-zero normal证明false；keeper0/allocator0，CAS8130 done/resources[]。 |

两场均保留原4500s timeout、400s readiness、600s hold、300s command timeout；没有延长预算、重放原业务或用退出成功冲销 FAIL。GUI自动退出动作与实际 OS0 属失败收尾事实，不能把原 normal_close_qualified 改成true。

当前 .4 EXE内置文档/RTTI/vtable与实际description函数绑定研究已明确：`run_interaction execute_threshold=decline` 会立即执行达到该等级的互动，包含decline档，并不等待AI自然拒绝。这解释R52低分资格有效却实际2接受0拒绝；原生产 `xqol_conversion_effects.txt` 的courtier/vassal/tributary三处采用了该立即执行路径，旧validator还要求该token、禁止send_threshold，形成错误静态契约。拟最小修复是三处改 `send_threshold=decline` 并纠正validator；本记录时采用、最终新正式27文件pin、修后自然reply/业务PASS均为 **PENDING**。R53个人教义资格是另一独立缺口，不能仅靠阈值修复宣称完成。

最小影响范围为 ordinary、PAM正负和UI改信提交/自然回复/唯一汇总。R33仅既有defense23/final6局部、R36两guard、R38牵制索款、R46自付赎囚、R42/R43原validity/身份范围继续按未改依赖保留；R48精确冻结夹具直接accepted callback，pending1→0→finish，release走未改accept路径，同场补证及原verify2保留，不因全局27fingerprint变化重跑无关场。Roman−120tooltip仍是既有未观察限制，不新增发布gate。

fde5官方CI run[38020302422](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38020302422)实际 completed/success：84 steps、64 success、20 skipped。原步骤库存没有完整QOL generator/static/builder/repro/parser覆盖，不能把整体CI绿外推为本产品原L0齐全；缺项和原current.4 static fullpins在外置 `resume-qol-02/source-signoff-impact-05/ROOT-QOL-SOURCE-SIGNOFF-IMPACT-AND-MINIMAL-L0-05.md`。后继仅对实际修正源补必要L0和受影响业务，正式tag/build/发布事实仍pending。

原件入口（C10=`C:/workspace/ck3-upgrade-20261010`；均为旧回执已有pin，本记录未重hash原件）：

- R52：`C10/qol-scene-resume-02/ordinary_async--a153/POST-RUN-CLOSE-05.json`，3661B / `a99a9839960e2616da86ca1937f6e5d54f6d04a1ea6e30afaa0c176fe380e1b7`；其中包含精确prepared、原native-report、verify、OS句柄、keeper和CAS回执pins。
- R53：`C10/qol-scene-resume-02/pam_positive--a154/POST-RUN-CLOSE-05.json`，3658B / `f73823c2d252414745c6a11203f34ca4afafafc8b35ad2a24890729d6f2f808f`；同样保留全部原关闭来源。
- 原生语义：`C10/ordinary-run-interaction-current4-readonly-01/CURRENT4-RUN-INTERACTION-DOC-BINDING-03.json`，64333B / `36badd509cdeb06d8adadc611f42868780ba7177788b32b8b1dd490df38b5f74`。
- scoped源码/原R52薄DIAG/R48 exact调用链：同根 `XQOL-DISPATCH-SCOPED-SOURCE-EVIDENCE-04.json`，36249B / `4f80bdf04a2cd8e41e956fb3dbf38f2e9a3ae0a7840568dd100ccea11c5cc969`。研究只读，无修后实机信用。

## 闭场后采用（2026-10-10）

三处 authored 派发已改为 `send_threshold = decline`，生产 validator 同步纠正；原生产检查直接调用的四个必要向量一次通过，修后自然回复仍待实机。PAM正例在原双信条设置前，仅当实际 `piety_level < 4` 时使用原版 `set_piety_level = { value = 4 }`，取得原版第4级提供的额外容量；原双信条、SF exact0、奖励与预算断言保留，contract只更新该fixture pin。R53没有实际slots/piety读回，不能把基础容量定位写成当场已证原因。原文PENDING及两场失败是原截止事实，最终新正式27和本机完整L0另记实际回执。

本机既有工具随后实际并行完成一次必要L0：`gen_xqol_phase2.py --check`、完整 `validate_xenoamess_quality_of_life.py --release-localization`、builder单测9项、`build_xenoamess_quality_of_life_release.py --check`、产品全脚本parser和PAM正例夹具parser，六项exit0，总墙钟约4.24秒，输入前后完全不变。产品解析16文件/138025B、0错误、corpus SHA `3ff79b4b385fb384efcbdc20331371544d62ec348ea75ef885fb028a5a877595`；夹具解析4文件/20779B、0错误、corpus SHA `2474725215f5bce08727ce53e7026277418a5c06ae24b4be5d6269a5f9d4103f`。parser只授本次语法子集；既有current .4 semantic profile UNSUPPORTED不变，没有有限运行时或实机信用。

实际精确argv、耗时、stdout/stderr pins、源文件pins和解释器见 `C10/root-resume-04/qol-current4-l0-once-01/ROOT-QOL-CURRENT4-L0-ACTUAL-01.json`，9868B / `847f23c101e09fe0a2a2c0eba02ab9aa0134c13344039a18b8c62a3d60fa67ac`。同一JAR433166B/`6ac143ebf03f3e1a041dff01b2d808e60de8e289d18cebf9855682f0a80b6d82`沿用原open_kaishek `522ac2d`构建身份，未重编。新正式27、自然拒绝、PAM奖励和UI仍待后继公共prepare/实机。

## R54观察作用域与R33局部复用

R54/a155原前5步通过，day001另报running-owner-stamp不完整，保留独立失败；stock回调的after观察另明确报`zqlr_actor`未定义。原debug显示当前scope与actor均为实际Song34422，imprisoner34422、ROOT为空。付款人28755、囚犯65886、`ransom_saved_gold_value=51`是付款前钱包快照，不是直接报价或已支付金额证明。只在after原active guard内重新保存当前实际imprisoner scope，新增一行`save_scope_as = zqlr_actor`；stock body/inverse/BOM、原断言和30步/12日/原预算不变。采用后该四文件夹具parser一次exit0、0.301秒、0错误，corpus `e035178c79543b77fa046d0fe0ee620ff8c266798c0301e475eeb4f19fddaa79`。作用域修正不授实际付款或day001 PASS。

原闭场回执`C10/qol-scene-resume-02/liege_shared_ransom--a155/POST-RUN-CLOSE-05.json`，3687B/`d46bda3092ba17cb6382fb3eba04f31e5be087284785bbfd3da6afa491bdeb88`，run2/verify2、normal-qualified=false、retained OS0 failure proof、原keeper/allocator0、CAS8140 done/resources[]。修正及parser回执`C10/root-resume-04/ROOT-R54-OBSERVER-ADOPTION-AND-PARSER-ACTUAL-01.json`，2294B/`24133da3092d0c71e1b253a2a06acbcf4591ba686053a37b0bf8b31d7a550528`。

UI原prior_core整套27绑定会拒绝本次三行派发修正。现增加一次窄来源等价：原R33 prepared/receipt pins不变，其余26文件exact一致，唯一新conversion文件必须逐字节精确逆变换三处send回execute并还原原7458B/SHA。只继承R33 defense23/reverse/final6，不继承改信/PAM/UI/正常退出或整产品通过。原实际R33调用闭包不经过修改的dispatcher；来源静态收据`C10/pam-personal-fulfillment-r53-readonly-01/R33-CORE23-CONVERSION-DISPATCH-SCOPE-01.json`，46230B/`8a2fde9c28c572bacd6885e5cd35e8c2a8a1e83b50846f03f4daf03f60f74459`，不另重跑原业务。实际生产prior_core六向量一次PASS0.030秒，回执`C10/ui-prior-core-send-equivalence-06/UI-R33-ACTUAL-PRIOR-CORE-VALIDATION-07.json`5871B/`cf3b72e83e93600ff95c2ab9ffbd5aa0d18bf42eba703fd0b4f5701ed6cd82d6`；setup缺sibling合同的原失败保留，未改生产候选追认。
