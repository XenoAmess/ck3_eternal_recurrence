# QOL R63：PAM正例启动资格失败，业务未执行

2026-10-10 19:01 CST，Source16 的 PAM 正例 a164/R0063 在原启动资格阶段失败。宋帝 D0 qualification 已 PASS，随后原 `actual_positive_doctrines_landed_recipient` 复合条件未成立，产生 forbidden FAIL marker。公共 run2/verify2，原35步完成0步、自然日0；没有取得业务 actor 或 campaign root，不能据此授予 bootstrap44、native角色等级诊断、PAM业务或产品发布通过。

## 原始观察与尚未确定的原因

原 debug.log 12597–12619 的薄片已保全：faith/Rite nestorian、stock SP10/3、SF>=0且<=0、legitimacy、Rite acts legitimacy/piety及piety>=4为TRUE；after_setup free_slots>=2及free_slots==0均FALSE，两项personal member及两项fulfillment均FALSE。原最终AND要求两项fulfillment，所以至少这两个必要条件未满足。cynical/zealous FALSE不属于该AND要求，不能称为缺陷。两个槽位比较只给出比较结果，不提供精确数值，也不能回推此前setup guard执行瞬间的值；完整规则与预置原因仍需静态定位，未据此盲加traits、延至D1或放宽断言。

该失败与R62 expected3/current4的root revision拒绝不同；R63未到root查询，既不能说旧race重现，也不能说修正44已实机通过。PAM负场暂不消费，待共享setup的影响明确；其他独立场继续准备。

## 输入与闭场

- 分配时MAIN：`b57d4ee9cf10306af0ea40b04bc49e514376f73c`，clean。
- Source16 runtime：15232 B / SHA-256 `a3cd2dc5b00f2e3aee03ed3aec13eb15034533b3ed6447a9957fc5ddcf1084e3`；共同manifest `47866bf34fa0a8919be138e95f4c83b84096dce76e8919dc2f1e7c329a9f7015`，native27db/queue04/helper03不变。
- 已消费PAM+ sibling：30372 B / `8580a387c3d96470d47515e1d2bf66ed477b3c1347f806ccb751db7bad5a5e37`，不重用该prepared。原35步/12日及4500/600/300/400秒、poll0.05不改。
- [原薄field](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_positive--a164/ROOT-FIELD-RETURN-R63-01.json)：13683 B / `7141f45e0f37c5117ed05bbc180e87d598fa66dfa22a5e011bb6b547a1b2248c`。
- [原POST](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_positive--a164/POST-RUN-CLOSE-05.json)：3690 B / `2213b832047fa20d0529805a4ed9bd0b37d036991ffc39b8c2e2ab84c47d5e26`。

实际CLOSED为11:01:02.385058Z。原run24820=2、原allocator15467由operator实际poll0确认、keeper0、三项closure和CAS8321 done/resources[]成立；failure lifecycle/retained OS0证明资源已收口。normal=false，失败闭场不改写为正常或业务PASS。闭场后才收回本场可再生cache及无损压缩文本，原失败/输入/证据保留并按统一存储策略到期复核。

## 后继

Source16四份未消费sibling和两份政府fresh public prepare已实际READY；R63已消费PAM+。下一独立merit使用publicprepare29中未消费的`meritocratic_appointments/prepare/prepared-case.json`，26078 B / `bf5cf9a5d7f88fc4c232c03fce74274b35c03a35e47c46a16d494de1482844ab`；0自然日及原预算/完整业务断言保持。其实际fresh容量检查未准入，缺317251584 B，未allocate。容量通过和新clean MAIN冻结均齐备后再启动；在最终GAP或失败之前，经既有共同queue42取得一次实际actor/title的独立native等级诊断，不强制角色入池、任命或继承。

正式迁移仍7/10（70%）。R60 ordinary及以前适用局部证据保留，不重复已完成业务。后续QOL、重整河山、361、两产品廷臣礼仪picker、G2顺序保持；发布缓存只核Steam真实下载文件与正式构建一致以及CK3实际加载缓存，不重复游戏内业务。

## 19:22 CST：只读观察采用，负场可独立继续

已采用[只读候选02](C:/workspace/ck3-upgrade-20261010/resume-pam-r63-final-and-fix-01/ROOT-R63-READONLY-OBSERVATION02.md)：只在原remove-all后、原piety分支后紧邻guard前、两个原setter后记录DLC/槽位比较/是否持有个人教义/piety4或5/两成员的布尔观察，没有变量、scope保存或业务写入。fixture18402 B / SHA-256 `ceb2de85b17f3db650dd4cfd5ac66361bb268a7885e4cf22961ae977780ba9a8`；contract4933 B / `86e2fece56e952df0508cb7fcfb20fbd4ad264ce68a90369bcf539061a11fa7b`仅变support pin。单次纯检查证明删除观察块逐字节还原原fixture与contract；不冒充引擎parser或实机通过。下一正场须新未消费prepare，原35步/12日/AND/dispatch/reply/SF奖励断言不变。

复核PAM−原setup29–38及guard69–72：负场只remove-all/SF0并要求对应Rite参数及personal flags均NOT，不依赖正场双槽准备，可解除暂缓按原合同独立推进。完整槽位公式为max(1,实际槽位modifier聚合值转整数+基础值)减实际持有数；基础1/piety4增加1是原版定义，尚不证明R63首次guard的实际聚合或持有值。

采用后Main现有followups文件9项实际通过(0.049s)，原预算、步骤及消费不重排断言保持。初次验证误指冻结源码树中不存在的client路径(FileNotFoundError)，第二次使用旧candidate client发现测试替身未接`read_report(allow_error=True)`与随后独立正常读回；两次ERROR原工具回执保留。仅将该预算测试的替身适配两次读回、隔离无关HANDLE取得依赖，四个原True/False/1/None预算断言不变；没有修改生产client。该9项接入既有统一官方CI的shared acceptance步骤并逐命令检查退出码，后继官方结果另记。
