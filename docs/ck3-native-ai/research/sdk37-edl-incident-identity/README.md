# 停顿区间的 incident 与 AUTO 身份

机器：`xenoamess-full-tower-eb9d2c1186`。旧collector35452实际exit1，不能称持续健康。
前批`be658a4e`的[Official39009194515](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39009194515)
及Linear39009194700均已实际success，保存[终态小回执](OFFICIAL-THIRTEENTH-CI-FINAL.json)。
原6区间和失败原件保留。具体输入与差量见[来源索引](SOURCE-PINS.json)，没有复制视频、
Driver、SAVE或通用engine；独立promo v0.3.0不变。

## 缺序号不是一个 AUTO

真实SDK双进程退出观察没有`original_request`。旧collector先去掉其他SDK的AUTO序号，
之后SDK36当前非AUTO观察以None匹配多条旧区间，产生`Incident ambiguously matches multiple waits`。
新空seed也不能免疫：先关闭一个非AUTO区间后，下个非AUTO incident曾被当成同一None身份而静默丢失。

公共[CK3 adapter](../../../../tools/ck3_stall_edl.py)仅改两处：旧手工seed fallback必须是
正的精确int序号、相同已知SDK namespace及Game；新区间保留source namespace。
缺失、null、0、负数或bool都不是AUTO身份，按incident ID识别。
未知／不同SDK不能认领旧区间；真正相同正序号的多重匹配仍报错，不任挑一条。
撤回误报只留no-edit marker，不编造恢复；原真实closed区间不延长。

13项／11子例公共回放通过，其中8项新身份测试。正式生产adapter／collector读取临时小元数据，
实际1972B状态必要字段和原34783B EDL绑定原SHA；仅halt文件pin重新绑定到明确synthetic临时文件。
没有读取原D路径、媒体或当前loop。旧EDL内已撤回0c等错误标签按原字节保留，
fixture明确不追认为有效等待；本修复不自动修订那份历史EDL或授最终渲染资格。
公开测试不搬旧CK3/generic混合脚本作baseline，旧RED由原失败与owner回执证明。

owner新frontend02已file-only采用候选adapter`2465be62…`；新Game／新录像在该封包时仍pending。
公共发布不修改旧冻结collector或运行目录。默认头尾2秒／中段4秒、保overlay，最终真实PTS、
像素／素材绑定和编码验收仍归独立工具链另证，不因元数据测试通过便称成片完成。

## 普通继承运行端对齐补注

前批第13已公开binder和M7两个入口。现已收到[私有最小差量](private-natural-no-pact.patch)及
[review](PRIVATE-NATURAL-REVIEW.json)：原4d6b7864→新4c4da3f1，实际caller为私有
`automatic_handoff`，不导入公共M7。它取同一纯predicate，前面的SDK normalize／expected lifecycle
等值及Native／PID／actor／episode／分封／零重放守卫保留。
CLEAN03 ef5a2dac／runtime2f22不改，frontend及vanilla候选各3方法离线通过；
新Game日志、SEM、SAVE或自然继承实机事实仍需Root原件。本patch仅研究归档，不将私有路径作公共API。

## M6／M7 小型原版边界

[宴会host-death报告](feast-host-death-REPORT.md)只闭源码：stock回调延迟1日发两个单项tooltip通知，
不能由通知消失、actor改变、Activity行消失或prestige变化补出原actor／full Activity终态。
现已resolved Start的原actor守卫会先返回诊断，不虚构terminal；不扩到pending恢复，未跑实机。

[Tribal市场输入小结](tribal-market-PUBLIC-NOTE.md)区分公共已有Clan实现和冻结SDK37未纳入的边界。
stock著录基础75gold＋200prestige、0.40/月不是actual quote或收益；Native槽身份、同帧Tribal输入、
key目录及Python／Native多资源提交、独立双扣款和材料真值仍缺。
两包均无生产补丁或新gate，没有重跑旧矩阵；G2仍6/8，M6／M7未完成。

[Tribal authority补注](tribal-authority-REPORT.md)进一步确认现正式GROUPS与Python／Native
提交都只有Crown，不能换字符串就当支持Tribal。stock另有10年tribal_authority_cooldown及
innovation_all_things分支；历史十槽prestige index1仅作源码起点，不授当前.4现场资格。
它同样仅静态边界，无新API、Game调用或能力完成信用。

新局仍从1066罗贝尔主菜单起录、干净重开，旧成绩／状态不继承；稳定30年第一，再<1秒／日、
0.5秒／日，均未达。本包没有启动、停止或调用Game／SDK／OBS。
