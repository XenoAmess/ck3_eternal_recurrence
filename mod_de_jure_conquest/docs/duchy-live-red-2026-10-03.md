# R0001 普通宣战费用与参战方诊断

本记录是 CK3 1.20.0.3 的实际 R0001 现场诊断，不能据此认定整个产品通过。公国费用已取得实际证据，分项探针随后实证Naples未加入。最小修复候选完成静态与构建检查，尚未实机；没有发布事实。

执行者 root 通过普通 GUI 以罗贝尔（history 1128，当前原生角色 31254）向卡普阿的 Richard（原生角色 32512）发动 `duchy_de_jure_greatwar`，目标 `d_capua`（原生 title 2221）。预览显示50威望／200虔诚。原生010与014快照同为 paused、同一日期53144328、同一玩家；威望 raw 10220000000→10215000000，虔诚 raw 10015000000→9985000000，scale均为100000，实际总扣除50威望／300虔诚。014出现战争4、目标title2221及目标省份2606／2608，证明宣战和扣款确实发生；不能把预览200写成实际总扣款200。

2026-10-03数值勘误：早先沿用预览费用，把上面的raw差额误写为200虔诚。逐项Python算术审计发现 `(10015000000-9985000000)/100000=300`，已更正当前记录。错误预期触发的审计R0001及输入全部保留，新的正确审计R0002见 [三档宣战费用](gui-declaration-fees-2026-10-03.md)，旧原始证据从未改写。

root 通过外置固定 inbox 执行 `djc-duchy-ui-postconditions-01.txt`。fresh debug.log 10:26:36出现 `FAIL primary-and-secondary-defenders` 与 `FAIL exact-target-d-capua`。后者通过 `war.casus_belli` 内 `target_titles` 列表断言；原生快照已经独立证明目标title2221，故这一 FAIL 不能直接解释为游戏选择了错误目标。前者把两个防守方合并成一条检查，目前尚不能仅由该条断言区分哪个防守方缺失。

旧生产 hook 同样通过 `scope:war.casus_belli` 读取 `target_titles` 后调用加入 helper。当前原版 `war_on_actions.txt:309–310` 说明 `on_war_started` 具有 CB `on_declaration` 的相同 scopes；`_casus_belli.info:147` 说明默认 CB 回调的 context 是 CB。另一方面原版结束战争回调 `war_on_actions.txt:1663`、`:1827` 确实包含 `scope:war.casus_belli` 后遍历 `target_titles` 的示例。因此语法存在，回调列表的可用时机和普通 inbox 的访问行为仍需实测；本记录未把猜测写成确定原因。

已生成外置只读 `djc-duchy-readonly-scope-probe-R0001.txt`，SHA-256 `8a5deaba22800c15c0c20dfc2c58d186dda64f91eaf69131c98bd3e350e8b13a`。它分别检查 Capua／Naples holder及top liege、角色 `is_defender_in_war`、实际CB，dump参与者与war／CB目标列表；只记录日志和临时命名scope，不改变费用、头衔、参与者、日期或触发事件。准备阶段只有结构parser通过，尚未记录实机执行结果。

后续原生016实际执行该probe：Capua holder／top liege／primary defender及角色is_defender_in_war均PASS，Naples对应三项均FAIL，using_duchy_CB PASS。war与war.casus_belli两处target_titles枚举均0条，参与者scope仅罗贝尔与Richard。新鲜debug.log的这些结果已独立读取、精确核查并保存在 `de-jure-duchy-red-R0002/`（33文件），[证据索引](duchy-live-red-evidence-2026-10-03-R0002.json) SHA-256 `c361126fd9a3366eecac9fb429f8cc94a5c44cda0a65b6c3351401aca6255a96`。这区分了真实漏加参战方与inbox目标列表断言不可用；没有把空列表解释为原生目标改变。

最小修复令三CB的原生 `on_declaration` 直接调用加入helper，WAR参数为该CB的 `root.war`。`target_titles` 真实循环中的选中title保存为这场war的 `djc_goal_title`，不从fixture预设输入反填；三CB的 `mutually_exclusive_titles=yes` 已静态确认单目标。旧public hook身份与玩家guard保留，去掉war→CB二次scope切换，重复参战方仍被排除。只改5个runtime脚本，九语、图、descriptor与费用保持原字节。

新 `de-jure-fixture-R0004/` 7文件生成一致性／结构parser PASS，72marker合同不变；目标检查改为对war上的真实捕获变量作存在性guard与identity比较。没有捕获就FAIL，不再在普通事件中重建callback目标列表。正式16文件静态R0003 GREEN（[精确报告](release-static-2026-10-03-R0003.json)，SHA-256 `f45cd67906032e98df70a399466cb58c7fdc3bce27663e07f8abbdf30b4f61cb`），双构建manifest／ZIP一致。完整改动集合、构建hash与fixture检查见 [修复复核](production-repair-review-2026-10-03-R0001.json)。这些均不证明新候选已加参战方或结算成功，新候选live仍NOT_RUN。

另准备外置只读 `djc-postrepair-readonly-goal-participants-R0001.txt`（SHA-256 `76944526d25011f078e433bf001bf93c6f184379218c9ae03f00aa18604564a5`），检查实际匹配的三档战争的主／次防守realm、native目标捕获与identity。只有当前真实存在的匹配战争才产生相应tier检查；BEGIN／END不能替代四项PASS。准备阶段parser PASS、游戏执行NOT_RUN。

原始证据保全目录为 `C:/workspace/two-mod-maintenance-20261003/de-jure-duchy-red-R0001/`，31文件包含fresh日志、production全16文件与manifest／identity、010／014／015原生回执、相关截图及操作回执、原断言脚本。精确保全manifest SHA-256 `f7b7aea05dfef287abcf9ba97080861c77c43a022e29da9c8396cb490ca35875`，仓库副本见 [证据索引](duchy-live-red-evidence-2026-10-03-R0001.json)。原R0001冻结树和已保存证据保持原样；生产修复与新attempt必须单独记录。
