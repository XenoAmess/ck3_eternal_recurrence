# 主 MOD 1.21.0.3 Florin 离线适配（2026-11-20）

machine_id: `desktop-3fevhd2-1c74096080`。目标为本机 CK3 `1.21.0.3 / build26785313`，EXE SHA-256 `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`；当前原版来源为 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game`。本工作包只读取安装文件并在 D 盘外置候选编测，没有启动游戏、Steam、GUI、Native live、旧自动游玩或存档恢复。

## 发布基线与本次范围

正式公开基线是 **1.0.2 / v1.0.2 / 36aa60f5aac2ae53bc8fa56db36a7df5a38dd095 / Workshop3784706360**，见 [永久发布记录](../release-changelogs/eternal-recurrence/1.0.2.md) 与 [实际发布索引](../release-evidence/eternal-recurrence/1.0.2.json)。旧 README 中“1.0.1公开、1.0.2尚未发布”的概括已纠正。该索引引用的旧 R20 run_id 为 `4-8e1c2f1861--eternal-recurrence--R0020`；缺少明确机器身份的其他旧原件仍为 machine_id unknown，不追认本机效力。

源码 **1.0.3 / supported_version 1.21.*** 是新候选。此前已集成的主庭臣311条特质元数据、114项other目录与22测试只保留其独立单元资格；本轮不重复编造完成记录。主产品保持真人玩家限定、评分/池/契约、700档教程位与跨存档表示，以及现有九语言内容。

## 原版与源代码核对

- 当前 `gui/window_succession_event.gui` 的 UTF-8-sig/LF规范化 SHA 为 `80132a0b5bb2c3e8c8f7b676c964b2c2eafec731ca5e25b98092aa437564d438`，与现有投影可逆恢复出的旧原版逐字符一致。注入锚点仍唯一，教会继承、返回宗族及原生菜单路径保持。现有生成器标注其最初1.20.0.2来源，保留准确历史；没有只换SHA或虚造重生成。
- 逐个读取当前原版10个 on_action 入口及9个提供文件，核对开局玩家已知时点、死亡前root、战争 attacker/defender、hook使用者、county.holder、父母scope、建筑付款者/省份和生日root。继续只扩展 on_actions；原玩家双闸、先同步结算再写教程和延迟承载者的顺序保持。
- 原版仍使用 `rite_creation_piety_cost_mult`、教程 `trigger_transition` 与界面域 `is_tutorial_lesson_completed`。既有 faith/Rite 选择与交付链不改。上述为源码依赖审核，GUI引擎回调、实际菜单/观察者行为与教程物理写入仍需本轮实机。
- 共保存15个当前stock文件SHA。上轮266 selected ZIP只是292文件子集，本次15项中13项缺少旧源；缺失项明确不可比较，没有从旧哈希重建原版或宣称完整安装差分。
- 按 AGENTS 的文件边界约定，将手写 `xar_effects.txt` 的33个顶层effect按初始化/结算/六维购买/资源购买/特殊购买/后代统计拆为 **8/2/6/5/10/2**。33个定义块逐字符相等，调用名和作用域不变；没有复制或重复定义。现有validator改为聚合这6份文件，并检查每个scripted-effect文件不超过20个定义。其他生成器与评分生成13定义文件保持。

## 实际软件资格

同一稀疏开发目录完成 `validate_static.py` 的真实完整CLI：generated parity、BOM/九语言、机制/AI屏障、图片与正式allowlist全部通过。现有 no-heir 5项（含本机实际原版比较）及manifest 6项共 **11 tests P / 0 skip**。没有新Java模块或Maven编译需求，旧非一期Python构建器只按实际范围维护；未新增Python生产模块。

原生产 `build_release.build_release` 对实际候选完成两次 **91文件 / 6,179,193 B** staging，真实 `--verify` CLI两次退出0。manifest SHA均为 `f14aa897ffbf387bf240fe3177ab6ac0a16cf741bf0113a8cb056bb3262d9a11`，ZIP均为 `f2cc9a25ec482436488c622a19e6b68d3cdd6ca9cc35e9d018f2d1b011f757da`；逐stage与ZIP条目字节另行核对。manifest中的zero revision和v1.0.3标签字符串是明确的合成测试身份，不存在本工作包创建的Git tag，也不是正式发布构建。Root须按实际集成提交/tag重建。

现有主产品 `main-ui` emitter实际prepare以及未修改的公共generic `prepare_case`/profile materializer完成91产品文件、20fixture文件读回，且原source-courtier-ui合同不变。仅调用transport为进程内，Git revision、host/plain配置和post-start谓词为明确的NoGame测试输入；emitter另据实际EXE/Steam文件登记核对新版本。该结果不授实际bookmark、CLI emitter transport、host/native、GUI、业务或发布资格。原consumer缺目录/缺post-start的两次失败保留，补纯测试输入后通过，没有改产品来迎合测试。

## 后继实机与发布边界

公共入口继续使用 `tools/ck3_mod_acceptance.py`，产品external_mod=false；现注册source-courtier-ui只覆盖其明确子场景，whole_product_acceptance_credit=false。本候选不把SourceOnly、外部依赖加载、fixture marker、庭臣单元或其他mod通过继承为主产品全业务。

新build的实际庭臣取消/不足/收费交付、同信仰与异礼仪配置、原始死亡writer/reader/无嗣与有嗣终局、七格合同原有剩余实机范围、实际正常退出与发布仍由现场owner接续。旧Writer33/Reader12、Creator16、R15/R20及court58/full-subtotal UNKNOWN、R15 harness RED、R18 GUI RED、R19 OS1/RED按原范围保留，不把旧完整矩阵任意升级成新硬门，也不以软件通过声称本轮完成。

本次无正式Git/tag、实机或Steam发表资格；正常集成、正式构建与同条目短上线发布由Root继续。详细逐文件base/target、原失败、当前stock pins、完整runtime及资源原件位于 `D:/ck3-state/upgrade-20261118/main-florin121003-candidate-a01/delivery-final.json`。
