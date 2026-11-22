# 未启用 Mod 创建的旧档：加载初始化修复 / Existing saves without DES

0.2.3 是用户2026-11-23要求的修复候选，当前尚未公开。已公开版本仍为
0.2.2、canonical Workshop3826991345；旧包、标签及其有限验收保持原事实。

## 根因和产品改动

0.2.2 在 `on_game_start` 和 `on_game_start_after_lobby` 初始化世界；没有本
产品状态的旧档加载不会自动经过这条新局链。原 Rite／角色回调、年度恢复和
月度维护又均要求 `des_initialized`。原 REQ16 提供了正常的
`des_initialize_decision` 手动兼容入口，不能因此说“旧档读取后自动生效”已覆盖。

修复在正式运行载荷增加透明1×1 ScriptedWidget。实际玩家出现后，它用原生
`GetPlayer.MakeScope`／`GuiScope.SetRoot` 进入正式 ScriptedGui，仅对存活人类
玩家且世界尚未初始化时执行。效果在执行时再次检查同一条件，然后调用原有
`des_initialize_world_effect` 和 `des_maintenance_effect`，与原手动兼容决议一致。
不需要夹具、控制台或手动执行初始化效果；原决议保留为补路。

新增入口不单独预设一次旗标；真正的 `des_initialized` 由原世界初始化效果设置。
重复窗口采样、重复回调和已初始化的旧档不重做初始化。DES 没有新增游戏规则，
这些初始化效果也不依赖 `has_game_rule`，不向旧档注入或修改规则。

原世界效果只给两种 DES 选项均缺失的 Rite 补“无”，不覆盖已选“无”或“宗族化”；
按原 `is_playable_character` 资格为存活角色补知识，保留其他 provider 的默认
登记，使用原发现／同步和持久 Religion 维护链。新入口不重写玩家原信仰、领地、
政体或宗族／家族，不把原版 Rite 自动改成宗族化。正常宗族化 Rite 已有的原产品
同步仍按原合同执行。已初始化世界不会从这个入口重跑同步或清已有绑定／原生
创建令牌。

仅新局的 `des_new_game_preset_clergy_pending` 与预置圣职校正完全沿原入口，
加载入口不授予该令牌，也不调用 `des_reconcile_new_game_preset_clergy_effect`。
正式 Java builder 的显式清单同步增加三个真实运行文件，开发39／发布60；不把
文件留在仅验收夹具里。

## 实际离线验证与边界

- 同一新增文件回归对原源码真实退出1：原加载入口与运行清单均缺失；1 failure、
  8 errors 保留，没有当成旧引擎现场失败。
- 首轮候选5项通过、5项失败，原因是测试解释器虽声明发现／维护为记录边界，
  却漏把发现调用接到该边界。保留该测试原件与日志，只修测试分派一行。
- 修后同一小组10/10通过，实际退出0、0.4775345秒。读取实际 Clausewitz AST，
  覆盖运行入口链、空规则旧世界的缺省／知识／维护排程、已有教义、其他登记、
  重复触发、已有 DES 状态、AI／死亡／过期 GUI 快照，以及新局令牌隔离。
- 未改变的 Rite 发现／维护内部业务在该测试中只是明确的调用边界。AST模型不
  证明引擎窗口生命周期、全部世界循环、真实保存、宗族业务、Java编译或发布。
  后继受影响 Java 工具已复用原开发／target／Maven缓存完成四个原wholeclass
  共26项、零失败／skip；仅DES12生产类／12测试类重编，共享save-core未重编。
- 新Quarkus工具package实际0、跳过重复测试，随后仅一次发布清单候选build
  与verify均0，60文件／ZIP逐项精确。59叶与源码原字节相同，descriptor
  由既有CompatibilityTags按唯一registry投影Florin标签；候选未创建正式tag。
  初descriptor原字节审计假设与FileID字段采集错误分别保留，只修离线collector，
  没有重复builder或26项测试。旧57工具app同卷保全。
  [实际软件和候选包索引](../../docs/maintenance/evidence/des-old-unmodded-save-tools-candidate60-a850.json)。
  真实无Mod旧档引擎测试仍待Root现场；没有重跑旧完整Faith／颜色矩阵。

## 最短真实复现与验收

1. Root 通过现有官方前端路线，真正 `enabled_mods=[]`、零夹具创建新世界，
   取得实际角色／日期／Core，首次正常保存并正常退出。保存原件、创建配置和
   SourcePin，确认源保存没有 DES 初始化／教义／知识／绑定状态。已有含 DES
   的 B0、N1，或删除现有状态伪装的保存均不合格。
2. 新独立进程仅启用真实0.2.3产品，不挂初始化观察夹具，不调用初始化决议或
   scripted effect，加载同一原件。保持暂停，核实际玩家／日期／原信仰／Rite／
   头衔／角色来源一致，等待普通加载生命周期自然执行一次。
3. 独立读回初始化、普通原 Rite 的“无”、合资格玩家的两项知识和默认登记；
   不以 `des_initialized` 单值代替其他状态。用现已合格的后台信仰／Rite编辑
   入口观察 Dynastic 类别和真实选择资格，必要只改草案后取消；原 Rite／角色
   不得已被自动宗族化。当前固定 Native 不授任意选择“无”，因此不能虚称
   全部动态选项已测。无新局预置校正令牌；新脚本无加载错误。
4. 本场需要时仅一次真正 Native checkpoint，独立物理保存与完整读回后正常
   退出；冷载该精确保存，核已有初始化／知识／教义／绑定和外部登记保留、未
   重建／重复初始化。冷载只读已足够时不为凑门新增保存。原 v14 同进程同日
   fence 与所有 UNKNOWN 保留。场／保存／Reader资源由 Root另按实际准入。

如需要现场对照，可独立加载原0.2.2观察原手动边界并保留结果；这不是额外规定
的完整矩阵或必需重复场。原 `old_save_bootstrap` case 明确先未初始化、再手动
决议，不能删其断言把新自动路径冒成旧手动case通过。新有限自动加载事实与
旧手动合同分别记账。实机和Java工具结果齐后，用户已经授权修复→测试→发布，
按同 canonical 条目正常更新，无需新增发布确认。
