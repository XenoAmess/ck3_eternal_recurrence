# QOL：R73 受控槽位夹具的 BOM 归因与后继修订

记录时间：2026-10-11 06:08 CST。范围仅“XenoAmess 的体验优化”1.1.1 的 CK3 1.20.0.4 迁移验收；不涉及 361，也没有发布产品。

## R73 实机结论

Source18 / Main `553a0848b2f77d78ad9dc4ad62ebbe8a7f260699` / `pam_positive` 的新公共 prepared42 在 R73/a174 实际启动。原 Song D0 资格通过，但新增 `common/modifiers/zqp_controlled_personal_slot_modifier.txt` 被 CK3 明确报告为缺少 UTF-8 BOM。紧邻原双 setter guard 的只读观察仍为 PAM DLC=true、free slot=1、free>=2=false、owned personal tenet=false、piety level=4；因此原 guard 未进入，35 个业务步骤全部 NOT_RUN，自然日0，run/verify均为2。

该场只证明夹具 modifier 未被合格加载；不能推断 `personal_tenet_slot_add` 引擎语义无效，也没有新增产品代码失败。原 R72 缺槽事实保持，R73 为新的代表失败原件。薄回执为 `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_positive--a174/ROOT-FIELD-RETURN-R73-01.json`，15898 B，SHA-256 `0f5a746ee7949b4bd8c8e25ac5067ebeb43afd1d5f4416a5de70fd7c39649206`；原 native report 23298188 B，SHA-256 `a095c8ace7c6702799c5de06d6de9265f1b224f5070c6109eb4776a597da8931`。

失败场已完整闭合：retained OS0、allocator实际0、keeper实际0、三项公共 closure 成立，CAS8507为done/resources=[]；normal close与业务通过均保持false。生成 shader cache 已按精确清单回收，原报告、日志、截图、配置和失败结论仍保留。

## 最小后继修订

唯一源码修订是在上述 modifier 首字节加入 UTF-8 BOM；内容仍只有一年期 fixture modifier 的 `personal_tenet_slot_add = 1`，原 PAM DLC/free==1 限制、原 free>=2 guard、双 setter、35步、12自然日及全部奖励断言不变。修订后文件为76 B，SHA-256 `effb9d83daebcb160bcc54c71b394aa7efe3a1844f76ee003f622d7f70dd822b`；`xqol_pam_positive.json` 的冻结字节合同同步更新。

`tools/.venv/Scripts/python.exe -B -X utf8 -m unittest tools.test_ck3_mod_acceptance_xqol_followups` 已实际通过9项。该离线结果不授引擎或产品业务信用。后继必须使用新的未消费公共 prepare/state，重新执行原35步/12日，并完成正常闭场；不得复用 R73 状态或把 BOM 修订写成已通过。

## 发布边界

QOL 1.1.1 仍为 DRAFT_NOT_PUBLISHED。正式 tag、27文件正式构建、Workshop 上传、匿名 Change Notes exact 回读、真实订阅缓存27/27与 CK3 实际加载、离线恢复及永久 changelog push 均待完成。
