# 帝国领袖恢复的合法前态

观察：2026-10-25T22:44:13.149558Z，`machine_id: desktop-3fevhd2-1c74096080`。只读来源根为 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game`。版本绑定沿本任务已核的1.20.0.4/build25734779、EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；本次研究未重新读取EXE或启动游戏。两项restore公共case仍为 **NOT_READY**，以下仅来源候选。

恢复消费者已闭合：`pam_decisions.txt:1157–1222` 的 `create_hof_decision` → `00_religion_effects.txt:279–307` 的 `force_create_head_of_faith_title_effect` → 已有title分支的 `faith_creation_events.txt:111–151`。实际头衔存在但无holder、temporal教义、合格圣地、奉献等级及产品帝国层级条件满足后，原版`.0011`授予同一title并添加原继承法。正常费用必须实际扣除。

## 尚未资格化的输入

较小候选是普通头衔窗口销毁：`gui/window_title.gui:1279–1284`读取`ShowDestroy`、`IsValidCommand(GetDestroyTitle)`并打开原版确认。一般销毁限制位于引擎，`00_rules.txt:1390–1399`的脚本只添加额外条件；源码不能证明非主宗教领袖头衔可销毁。必须先经合法普通途径取得另一同级或更高头衔，再查询实际原生按钮；只有可见且enabled才可继续。当前没有该native Can观察，不用fixture `destroy_title`替代。

另一路原版来源是接受真实解体派系要求。`00_nation_fracturing_faction.txt:48–74`保存实际faction／leader／target并在五天后发送`faction_demand.1000`；`faction_demands.txt:3235–3330`的接受项先处理派系成员独立，再摧毁当前持有、与主头衔同级的全部头衔。如果`e_des_*`是主帝国，原个人公国及直辖圣地县不在该集合中；教义不改变。前提是原政府与派系条件合法，`00_faction_triggers.txt:189–198`还要求原生`can_join_or_create_faction_against`。自然产生及公共原生操作尚未验证；不得伪造scope直接触发要求事件。

## 排除的输入

- 普通Faith／Rite改宗在`00_rules.txt:40、96`拒绝当前宗教领袖；强制`set_character_rite`绕过该合法性。
- `religion_on_actions.txt:822–828`触发的`faith_creation.1100`只在主Rite同时没有temporal／spiritual领袖教义时销毁。用户要求保留temporal教义，不采用该路径。
- `destroy_if_invalid_heir=yes`的原生非法继承人判定未闭合；准备无继承人并杀人不能冒认普通恢复。

实际程序仍须“正常取得 → 真实合法失去holder → 原生及独立Save确认同一title空缺、教义／CoA保持 → 原版付费恢复 → 同一title身份及实际扣费”。源码候选不能解除NOT_READY。

## 来源SHA-256

| 相对game路径 | 完整文件SHA-256 |
| --- | --- |
| `common/factions/00_nation_fracturing_faction.txt` | `195e160d2c534f00d62e75ae1a44b88dc54fee01650d481bd8ea20560aa1d336` |
| `common/scripted_triggers/00_faction_triggers.txt` | `dd7b3a650b559b26959ed1708fc7cacd009d1cbb6735fa9d27905fb40570c517` |
| `events/factions/faction_demands.txt` | `eb17720ca9d48acfb8cc24e5f61edc62fd2d4d2d599561c92854fc762104eccd` |
| `common/scripted_rules/00_rules.txt` | `c7ba2ae71e4461e88c6d5c86d8fc15fa7ccc73edae1e28fb3b65f0e362c4560f` |
| `gui/window_title.gui` | `c030230fa9468b02b94f65ef6895a48dad9157aa7292d55c94a35d0288518be3` |
| `common/decisions/dlc_decisions/pam/pam_decisions.txt` | `fe113568051ccf2243f08543a522bc5afeb3e25e6fb97e5440d2fae7a4cb7a64` |
| `common/scripted_effects/00_religion_effects.txt` | `5bf6b0df3316f72f711507c310a349d508a3b83aef99373ea6440de20e4e4931` |
| `events/religion_events/faith_creation_events.txt` | `419c04b9ca889e96e572b894ec346ae6119af2fd6eb9be4833d6659edfba923e` |
| `common/on_action/religion_on_actions.txt` | `ef9367ddf5f89c912b895743f8b72441e88af3a5b03a5c1a9eddea0e5681ee2d` |
| `common/laws/01_title_succession_laws.txt` | `48593c818edb66b1ad1b41602f77ad9395ab92d6d16f11cf5b95b378b92e0d14` |
