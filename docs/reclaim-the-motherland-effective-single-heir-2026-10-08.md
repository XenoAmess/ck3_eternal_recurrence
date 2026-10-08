# RMTM R12：有效单继承规则与空 own-law 表示（2026-10-08）

R12/a114 的[实际原生卡26](C:/workspace/ck3-upgrade-20261007/rmtm-r12-canonical-single-heir-contract-recommendation-26/ROOT-RMTM-R12-CANONICAL-SINGLE-HEIR-CONTRACT-26.md)纠正此前“own-law缺失即有效单继承规则缺失”的解释。D3 exact1.20.0.4、actor34422/current primary18371、date53144400/native revision16的[物理查询](C:/workspace/ck3-upgrade-20261006/resume-root-01/rmtm-r12-d3-physical-own-laws-once.result.json)实际available=true、native_law_count=0、完整laws=[]、single_heir_member=false、无unavailable原因。同一holder的realm single-heir TRUE、can_have/can_keep TRUE，owner/title/primary/durable refs一致且无ceremonial liege；完整空数组证明没有title override。这一后态可合法使用有效realm baseline，原own-law FALSE及law/heir ANDFAIL仍保留。

已有静态24/25证明引擎canonicalizer能删除与realm baseline比较投影相同的冗余own law，effective getter按realm baseline与保留的own laws合并。这里只复用已闭合语义；未取得R12 entry→store→clear的实际trace，不能声称本场add_title_law成功或本场确实走过该清除分支。无需继续强留冗余成员；初次add在realm不同法时仍有意义，不能因此全删生产add-law。

后继验收的待实施合同必须保留严格合取：完整物理own-law query available，当前同一进程/frame的owner/title/primary/durable完整身份不漂移，原current_heir与预读expected heir完整身份条件保持；然后只接受以下两种有效表示。`own_override`要求完整own keys含single-heir且原titleHasLaw独立Bool一致；`realm_baseline_no_override`要求物理count严格0、完整laws严格[]、当前相同holder的realm single-heir独立Bool为TRUE。非空缺single-heir、冲突或未知override、unavailable或身份漂移不能由realm Bool单独通过。死亡后的新owner必须重新取得同样证据，不能复用旧owner空数组；D3、死亡后law probe及死亡后总AND应使用同一标准。

原真实predecessor death→原次日恢复链仍必需：预读完整expected heir，证明死亡后相同完整TitleID的holder变为该heir、仍为后朝及正确primary；直属忠臣树、个人伯爵领、唯一官署entitlement与九席exact incumbents均按原条件实证。原36 families、14days及其余业务合同不变。该专题只修正解释和待施工准入合同，未把未来fixture写成已实施，也未授真实继承或整模组PASS；R8/R9/R10/R12原ANDFAIL不追认GREEN。

[closure37](C:/workspace/ck3-upgrade-20261007/rmtm-r0012-ownlaws-normal0-readonly-resource-01/ROOT-RMTM-R0012-A114-SMALL-CLOSURE-37.md): R12实际normal OS0/native0、线程cleanup已由Root闭场核定；host GREEN只授生命周期，keeper63376实际exit0→CAS6200 done（05:34:30 UTC）。本场只有当前规则表示/读接口和正常闭场信用，后续业务仍待完成，批次6/10（60%）。
