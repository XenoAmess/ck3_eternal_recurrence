# 信仰与权力第一期：独立机制实验场景与准备流程（1.20.0.4）

本期采用独立的 867 阿拔斯 / 纳杰夫机制实验，先取得灰条件与一次原版采用的真实前后态。它用于补强普通游玩智能体的候选、权限与后验能力，不计入 Robert 原普通战役的成绩。

`machine_id: 4-8e1c2f1861`；源码与准备包观察时间 `2026-10-17T07:42:07Z` 至 `2026-10-17T07:58:00Z`；Git 来源 `7ba029435c54ef53ab484be86186ba45ebcad3bf`。来源为当前机器 CK3 1.20.0.4 / Steam build 25734779 的游戏脚本、下列 SHA 固定的外置准备包，以及当前 MCP 源码。安装 EXE、Steam 离线、现场占用、实际 DLC/mod、窗口与存档身份由每次执行另行读回；本文没有替任何后续运行授实机通过。

## 用户授权与制作边界

用户本轮明确选择：

> 允许独立机制实验存档，明确标注准备内容（推荐）

这是第一期独立机制实验的授权。根 AGENTS 中 Robert 29829 原普通战役唯一测试入口继续适用于普通智能体；不删除历史指令，不把全局默认人物改为阿拔斯，不放宽共享 MCP 的 player-only 限定。启动批准场景用一个默认关闭的封闭 target profile，角色由原版前端选择；不在开局后换玩家，不使用控制台。

影片固定标注：`独立机制实验｜867 阿拔斯｜额外虔诚2000｜B臂已准备马立克礼仪｜原版采用规则`。Hanafi/Maliki 的直接赋值差一项，但 tenets/doctrines、修正与可能的领袖状态都有派生变化，必须读回，不能称作纯单变量实验。准备资金不是智能体通过正常玩法赚得的资金。

## 固定定义与普通规划器的判断顺序

| 对象 | 固定定义键 / 源码输入 | 必须实际读回的内容 |
| --- | --- | --- |
| 场景人物 | `character:34014`，Al-Mu_tazz；`e_arabia` / `d_sunni` | 当前 player 完整 CharacterID、episode、连接 generation、日期、实际头衔、独立、HoF 身份。历史号不是 native ID。 |
| A 臂 | `rite:hanafi` / `faith:sunni` | 实际 rite/faith、全部核心/个人信条、原生采用条件与失败理由。 |
| B 臂 | 当前 player 直接准备为 `rite:maliki`，预期仍 `faith:sunni` | 核心 `tenet_adaptive` 的原生参数、faith 是否保持、HoF 是否保持及其他派生变化。 |
| 目标 | `holy_site:nadjaf` / `county:c_kufa` / `barony:b_an-najaf` | 完整 HolySite 实例与 type、county/barony、关联 faith/等级、inventory/artifact IDs。 |
| 自然县主与领土 | `character:34017`，Al-Muwaffak，Hanafi/Sunni；`c_kufa -> d_basra -> e_arabia` | 当前县主 faith、实际从属链与玩家 realm membership。 |
| 关联 faith 信众 | Shia 源码存在省份 `6156 / Uwal` 的 `ismaili` 输入 | 关联 faith 的完整名单及实际 `num_county_followers`，不能用省史一行代替完整 runtime 数量。 |

源绑定见已入库的 [圣地研究](faith-and-power-holy-sites-12004.md)；本轮增补的自然候选清单位于外置证据根 `C:/workspace/ck3-faith-and-power-20261017/episode01/scenario/natural-candidate-sources.json`，SHA `ebdee82bc67261bb4f0eaa8edd844a70855f761f86f39075eb353310f23ca8fb`。

规划器按 **管理权与独立 → 候选来源 → 同 faith 县主与领土 → 已有关联 → 名额/王国记录 → 兼容 → 关联 faith 县信众 → 原生费用/冷却** 分别诊断。Maliki 的核心 Adaptive 声明 `allow_adopt_any_holy_site`，只解决兼容分支；个人同名信条没有同一参数。不能据 Adaptive 直接生成 `legal=true`。

反例：同在巴格达县的 `ctesiphon/b_an-nahrawan` 与 `baghdad` 是不同模板。省史扫描中 Mazdakism 的四处基底均在 867 前或当日被覆盖，因此 Ctesiphon 的关联信众是额外未知，不能因地图有模板就当作可采用候选。本期选 Nadjaf 减少这项准备，不改变其他 faith 的县民来凑资格。该结论是源码推断，不是永久缓存的 `followers=0`。

## 准备包精确身份

本机外置根：`C:/workspace/ck3-faith-and-power-20261017/episode01/scenario/bootstrap`。以下恰好 6 文件，共 4518 字节；表内路径相对该根。没有覆盖原版文件，也没有 Workshop ID。

| 路径 | bytes | SHA-256 |
| --- | ---: | --- |
| `common/bookmarks/bookmarks/xar_faith_h01_867.txt` | 448 | `e7666ee4ab0736bf21362509f86d163548e7e3e8500164540a13c3a2d4c837d0` |
| `common/on_action/xar_faith_h01_start.txt` | 707 | `ba6e4d885cf3f678da8e749042f3e0b47af377a4ea6002f55df157faf39afbc6` |
| `descriptor.mod` | 90 | `74047ddd40b7b4293b136a2da4d8a9aa589ba575d47615063e70d29cd97a37bd` |
| `events/xar_faith_h01_prepare_events.txt` | 887 | `b60af0ae7bd2e1904eae86bc5cd7e3a525ec7ca9ce2487e89eae3cfa5278f872` |
| `localization/english/xar_faith_h01_l_english.yml` | 1226 | `eb2cae39babefb6d1ea681dcb64910f5078fc0b851647265b477f4fce5c333f7` |
| `localization/simp_chinese/xar_faith_h01_l_simp_chinese.yml` | 1160 | `f76bbf33d928f7ba95868140d836f2ee8c8ecf97617acdcf12ed1a59b1802a68` |

外层注册模板为同级 `bootstrap-registration.template.mod`，168 字节，SHA `298c4c712a9e2b4abe192776e54d63461bbfe60d497c99842e70d714fdb0429e`。仅由现场 owner 复制到本期隔离 userdir 的 `mod/` 注册并声明 active_mods，不装进玩家默认目录。其他机器复用代码时重新定位外置根、注册路径和证据身份，不从这些盘符推断机器相同。

准备入口为 `on_game_start_after_lobby` 的 `random_player`，同时要求当前人类玩家 `this=character:34014`、日期 867.1.1、存活、独立、持 `e_arabia/d_sunni`、Sunni/Hanafi 且尚无 funded flag。满足后仅给该 player `add_piety=2000`、添加一次性 metadata flag，并触发 `xar_faith_h01_prepare.1`。任一条件失败则不准备；没有 AI 事件链。

准备事件再次限制该 player/faith/rite；选项 `.a` 只记录 A flag，保留 Hanafi；`.b` 仅 `set_character_rite=rite:maliki` 并记录 B flag。两臂都不提前采用 Nadjaf，不修改县主、领土、county faith、全局 faith、站点/库存，也不修改原版决议条件、价格、冷却与效果。惰性 flags 为 `xar_faith_h01_funded`、`xar_faith_h01_arm_a`、`xar_faith_h01_arm_b`，仅作准备标识。

## 原版前端选择合同

封闭 profile 的实际约定由 frontend/runtime 线程对齐，当前值为：

```json
{
  "schema": "ck3-frontend-fixture-start-policy-v2",
  "schema_version": 2,
  "profile_id": "faith-and-power-e01-abbasid-867",
  "frontend_target": {
    "bookmark_key": "bm_xar_faith_h01_867",
    "character_name_key": "bookmark_xar_faith_h01_abbasid",
    "government_key": "clan_government",
    "start_date_raw": 51394920,
    "bookmark_group_key": "bm_group_867"
  },
  "post_start": {
    "government_key": "clan_government",
    "primary_title_tier_key": "empire",
    "independent": true
  }
}
```

这是 v2 文件中的场景字段摘录，其他 v1 必填字段由 common runtime owner 生成完整文件，不能把本摘录冒充可直接启动的完整 policy。native closed enum 为 `faith_e01_abbasid_867`，steps suffix 为 `faith-e01-v1`。公共 host 沿用 `--fixture-profile --frontend-robert-bootstrap --frontend-fixture-start-policy <本期完整v2文件>`；旧参数名不表示实际选择 Robert，场景实际走新增无参 MCP `ck3_submit_frontend_fixture_scenario_start_v1`。其离线集成与 exact-build preflight 完成情况另记；没有成功查询前不写该 selector 已实机通过。

`51394920` 是现有 Rurik867 同日 target 的预期；本次实际 date/government/player fullref 必须独立后读。书签 `history_id=34014` 只供原版选择器解析，不能写作 live fullref。普通 Robert 的入口和默认 profile 不改。

本期 common runtime owner 约定的物化目标为 `C:/workspace/ck3-faith-and-power-20261017/episode01/runtime/state-ep01-a01/profile`，public prepare 输出为 `C:/workspace/ck3-faith-and-power-20261017/episode01/runtime/common/prepare-ep01-a01`。通过现有 `materialize_product_profile` 把这唯一准备 mod 物化为隔离 profile 的 `mod/product.mod`，随后公共 `_finish` 冻结完整 fixture policy；不挂主永恒轮回，也不为满足计数增加第二个 mod。本段记录协作时约定的输出路径，不代替 profile 真实生成、加载与 source hash 读回，不授任何发布产品 GREEN。

启动必须等到的日志 literal 为 `XAR_H01 PREPARATION actor34014 piety_plus2000; no adoption performed`。A/B 选项后的 marker 分别为 `XAR_H01 PREPARATION armA Hanafi retained; no adoption performed` 与 `XAR_H01 PREPARATION armB current player Maliki assigned; no adoption performed`，后二者不能成为启动前置。日志只定位准备来源，实际资金、角色、事件及站点关系另读原生状态。

F 的 case contract 应允许并明确要求预期准备事件，不能套用 `no_active_event` 或自动陌生事件首项续行：paused、当前 player 历史来源 34014、Sunni/Hanafi、HoF=current player、`event_definition_key=xar_faith_h01_prepare.1`、事件 root=current player，实际 options 为 `.a/.b`。option fullID/native index 均从当前窗口读取。A/B 后态才要求该准备事件消失。若通用 runtime 现有字段尚不能表达 F 的预期活跃事件，由 runtime owner 记录这项具体接口差异，不能关闭实际事件后声称仍保存了 F。

## F / A / B 与无准备 mod 的正式输入

1. 现场 owner 在本期隔离 profile 注册本包，取得机器身份、当前 EXE/build、fresh Steam offline 和排他现场准入，由原版书签选择 867 阿拔斯后正常 Start；不在本线程或其他线程并发占屏。
2. 暂停后读实际 actor/date/faith/rite/HoF/资源及准备事件。用 `ck3_query_current_event_window_context_v1(event_instance_id=当次实际值, expected_revision=当次值)` 固定事件定义、实例、实际选项和 native option index。
3. **先**调用 `ck3_save_checkpoint(expected_revision=当次值)`，将回执中实际 checkpoint 文件复制为不可覆盖的共同母档 **F**，记录 SHA/大小与 profile/mod/episode。F 含待选准备事件，恢复它仍需要准备 mod 的事件定义。不能让后续固定路径 checkpoint 覆盖 F 后仍引用旧路径。
4. 由 F 选择 A：`ck3_select_event_option(option_number=实际native_option_index+1, event_instance_id=实际值, expected_revision=实际值)`。不能按显示位置猜编号。独立后读事件消失、Hanafi/Sunni/HoF/钱包，再保存并冻结 **A-pre-adopt**。
5. 恢复 F 的原始字节和准备 profile，重新查询新实例/选项后选择 B，独立后读实际 Maliki/Sunni、HoF、全部派生字段与钱包，再保存并冻结 **B-pre-adopt**。不复用上一进程的 runtime ID，也不先采用再删除站点伪造前态。
6. 两臂正式测量均在事件已关闭的 A/B 保存上执行：正常保存退出，按 keeper/租约合同释放现场，移除准备 mod 的 active_mods，再正常冷载该臂；核实际加载 mod、事件队列及全部业务输入。原版 faith/rite/title/site 定义仍存在，准备 flags 成为惰性元数据。**无 mod 冷载尚未实机验证**；缺失 mod 提示或拒绝原样留证，不改 save 元数据掩盖。无 mod 的恢复母档是已处理事件的 A/B，不是仍含准备事件的 F。
7. A 只拍实际灰条件，不提交。B 只有在原生最终许可与实际余额成立时，走原版参数化 `adopt_holy_site_decision` 一次提交；随后独立读回实际结果。MCP HolySite context/参数化采用入口由对应能力包实现，本文不把 GUI 方法名猜成已可调用的业务协议。

原版圣地窗通过 `PdxGuiWidget.MakeDecisionTypeWithParam('adopt_holy_site_decision','selected_item',HolySite.MakeScope)` 打开决议。该决议 invisible，普通 decisions list 没列出它不能证明无采用能力。输入使用当次真实站点 scope，不能拿定义 key 或历史号充 runtime identity。

后验至少包含：Sunni 的完整站点集合是否新增同一实例、默认等级、type/库存/其他 faith 关联是否保留、实际 piety/free actions/该决议 cooldown、日期及 actor/faith/rite。采用的默认等级和保留行为未取得实机后态前保持未知。ACK 只记接收；结果未知先 query，不重发未知动作。

## 已有验证与尚未取得的信用

本机 `bootstrap-static-report.json`（SHA `81bfa956747b6917cb2b5d701c8dd19e617942ed563653bd1394c7c049351351`）：仓库 Clausewitz 结构 AST 对 4 个 `.txt/.mod` 文件 PASS；两份 localization 为 UTF-8 BOM、版本 0 字段。它不校验 CK3 scope、DLC 或实际启动语义。

本机 `bootstrap-open-kaishek-preflight.json`（SHA `415cf778bd74cc82c14941704cef06061d5a79cff8883a13ba076e8964649473`）：实际本地 checkout `2b559966c72f4e845111e3e15652ae2354aaed57`、JAR SHA `6ac143ebf03f3e1a041dff01b2d808e60de8e289d18cebf9855682f0a80b6d82`，执行 `preflight --root <上述bootstrap> --profile ck3-1.19.0.6-zg361 --fixture xar-faith-h01-867-bootstrap`。`root_scan.parser=GREEN`（3 script、2042 bytes）；整体 `RED/unknown-fixture`，旧 profile 对 custom bookmarks/准备 opcodes 为 `UNKNOWN_DIRECTORY/UNKNOWN_OPCODE`，IR/runtime 不支持此 fixture。保留原 RED，不改写 GREEN，也不把它当成 CK3 已证错误。

交付清单 `bootstrap-delivery.json` 的 SHA 为 `0738850c4b2f969bc4b0cd8a784690902fb9df0d17fbd0f301a33e44cae86d4b`；观察时间 `2026-10-17T07:56:39.225879Z`。截至该收据：未部署、未启动、未修改玩家存档，captured clips = 0。仍待验证：原版前端选择、准备 effect/事件、F 回载、A/B 剥离准备 mod 冷载、原版采用合法性/扣费与后态。完成这些步骤后追加当前机器带时间的 evidence，不覆盖这份历史边界。

存储按[通用政策](../storage-retention-policy.md)和[版本参数](../storage-retention-policy.json)。F/A/B 是活跃输入，各留一份；不要复制整个 userdir。闭场记录 SHA、真实路径、加载 mod、准备 flags、原片引用；checkpoint 默认 14 天复核，必要保护至多 7 天并注明理由。本包当前复核点 `2026-10-24T07:56:39Z`，不永久续存全部过程副本。
