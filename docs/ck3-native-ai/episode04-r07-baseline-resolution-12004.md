# R07 baseline：正规 Army row 与 retained query 恢复

machine_id: `desktop-3fevhd2-1c74096080`。观察2026-10-17，source `611bc985ae95f477dd7314df11f8602cd1e595f3`，R0195。此机器实证不外推其他机器。

R195 的 `r195-s1-baseline-a01` 在原Army query2已完整保全后失败：Root exec session10742，exit1；旧外置relay line232要求 `row.native_carmy_id_observable is True`，报 `actual wholeDATA source not qualified`。原front没有写入，不能将该attempt改标通过。正式 `war_contract` normalized Army row不输出这个旧bool；它输出status/native_carmy_id，并保留严格的native_army_resolution_v1。

共享 `army_split_merge_observation_12004.read_bound_native_army_resolution` 使用真实typed结果：public Army ID与所请求CUnit一致，row available，CArmy FullID有效，resolution available/ready/resolved，raw reference与entry FullID均匹配该CArmy，entry index在本次实际storage范围内。public CUnit与native CArmy是不同身份域，不能要求数值相等，也不能用旧bool或默认true修补。wholeDATA非空/ready/available、原query/frame/episode/generation/source、兵数和current commander等既有守卫继续保留。

发生这种结果已落盘但后置守卫失败的情况，先从该原response-local complete Driver result reference核size/SHA和scope/query/日期/public+native revision。R195已在离线读取原query2 retained结果恢复Army/DATA，没有重发Army query。首次失败发生在commander/cash之前，因此完整baseline仍需Root新唯一attempt只读补current commander及cash(query)和before snapshots；不能凭原三包制造未采字段。新completion必须确认原暂停日期/public/native revision和runtime lifetime未变，只提交这三类只读工具，不启采样、不推进日、不发Move/Halt、不录制。成功时另写标准baseline canonical并附恢复来源，原失败原样保留。

当前外置恢复输入：`C:/ck3-e04-resume-20261015-a01/r195-r07-live-small-audit-a01/RECOVERED-ARMY.actual-a01.json`，45249B SHA `1064847c65d41e9e5934f6435879700f1e72fdd308a4d98917dafb9f1e6f8f42`。其原baseline-before/army-before/army响应与完整Driver reference全部精确绑定。大CK3存档和原始native/wire dump未读取。外置执行卡及最终audit receipt记录后续是否真实完成；本文不预写完整baseline/control32日/pair通过。

R195 preview1032为同Army18/date53148192/origin2635的available单边[1032]，陆海definition1→0，原包13886B SHA `cef6474fa589c7b34f0b5e79ffd8e363958013a83f5fc9fba7b837e7542e713a`。其中24E2230 county-loss Pfalse和0内部stage调用是该分支bypass，不是Move/route不合法；不能借它绕过控制试验作为“首海失败未arm”。fresh preview只授路线门，实际入水/时钟/付款仍分别取证，0条callback不证明免费。

两条focused离线回归覆盖无legacy bool时public/native不同身份域仍可合法绑定，以及legacy true不能掩盖native generation/availability/storage错误。此修复不重跑旧完整研究矩阵，不授任何新实机或费用资格。
