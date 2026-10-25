# 新宗族初建后把族长交回真实请求者

需求依据：[REQ-18](requirements.md) 与 [LIVE-11](test-plan.md)。本次仅实现新绑定初建后的领袖归属，不把已有绑定重新启用或周期维护变成重新夺取族长的入口。

机器：`machine_id: desktop-3fevhd2-1c74096080`。源码及原版只读观察时间：2026-10-25T15:17–15:23Z；身份由当前 `tools/ck3_live_run_id.py machine` 读回。下列是源码候选及静态检查结果，**新行为尚未实机**，不追认 R0013／R0015 的 NPC 族长为满足新需求。

## 原问题与实际入口

此前 `des_create_rite_dynasty_effect` 保存了原请求者与实际建族者；原请求者受原版 House head／Dynast 限制时，可能由另一真实信徒或生成的真实成年 NPC 建族。建族后只写入 Rite ↔ Dynasty 与默认 House 引用，再让全员迁族，没有把新 House head 交回原请求者。

此外，`des_on_rite_updated` 的 root 是 Rite，原实现直接遍历信徒同步。第一次改革开启宗族化时，迭代器的第一个人物可能先触发建族，不能将其称为实际改革者。

原版创建回调 `on_rite_created` 的 root 明确是创建者；原生产入口已先同步该人物，再同步全部信徒，本次保留此顺序。更新回调现在先保存实际 Rite，并在存在存活、同 Rite／Faith 的 `head_of_rite` 时先调用同一绑定入口，然后才执行原全员同步。原版原生界面编辑资格与一次编辑锁都归当前 Rite head；延迟更新回调本身没有独立 editor 字段，所以仍须在实机保存实际提交 actor，并与当时原生 head 逐项核对。没有真实界面编辑 actor 的脚本更新不能因此宣称为玩家改革通过。

新预置信仰若初始没有信徒、创建／改革 actor，后续真实入教者仍从原 `on_rite_change` → `des_sync_character_effect` → 绑定路径进入。该人物是这次建族的真实请求者，不伪称预置 Rite 的历史创建／改革者；没有更换玩家或虚构人物来源。

## 唯一建族路径中的修改

仅在本次原生 `create_dynasty` 成功、实际建族者已属于新 Dynasty 且已取得真实 House、双向绑定已经写入的分支，调用 `des_finalize_new_rite_head_effect`，Character scope 为此前保存的真实请求者。

调用前再次核对：请求者存活且仍同 Rite／Faith，双向绑定与本次新对象一致，新 House 的 `house_dynasty` 正确，新 Dynasty 当前 `dynast` 仍是本次实际建族者，且不存在处于其他 House 的实际 Dynasty 成员。这个守卫结合本次 fresh `create_dynasty` 的初始单 House 来源限制调用范围；它不枚举无成员的空 House，也不把既有多 House 宗族当作初始单 House。实机独立 Save 仍须读取全部 House 拓扑，不能以成员守卫代替完整拓扑验收。

条件成立时，只把请求者本人迁入本次新 House；重新核其实际 House／Dynasty 后，如果该 House head 已是请求者便不重复调用，否则仅调用一次原版 `set_house_head`。真实中间建族者继续存活，没有被杀死、删除或改成临时身份。随后分别读取新 House 的 `house_head` 与新 Dynasty 的 `dynast`；两者及请求者身份不同时，在 Rite 留下 `des_creator_head_fault=yes` 与诊断日志，而不写“成功”旗标、不改原生 head 读回。

`des_creator_head_fault` 只诊断本次初建领袖转交；它不参与普通绑定修复，不由每月维护清除或重试。它不会把真实失败隐藏为一般绑定修复成功。初建成功时移除该诊断变量。已有绑定、合法旁支、关闭后重开、普通新信徒迁族、保存加载和后续死亡／继承都不会调用这个领袖转交 helper，原版自然继承继续有效。

名称／纹章接线的唯一位置在 `des_binding_effects.txt` 的新 Dynasty ↔ Rite 与默认 House 引用写入之后、`des_finalize_new_rite_head_effect` 之前：`scope:des_binding_rite = { des_apply_rite_identity_effect = yes }`。该 Rite scope helper 由同轮独立的 `des_identity_effects.txt` 提供，仅处理名称与两项新预置的静态 CoA，不处理人物 head。通用自创 Rite 的动态图标复制当前没有合格的原生 scope 通道，仍未完成；这条接线不为该能力授予通过，不改造或猜测 `set_coa` 原语。

## 精确原版来源

本次重新计算实际 EXE SHA-256：`C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，与既有 1.20.0.4／build25734779 的研究来源一致。没有启动 CK3。脚本均从此安装的 `game/` 下重新读取；下表是完整文件 SHA-256。

| 原版来源 | 作用与完整 SHA-256 |
| --- | --- |
| `common/on_action/religion_on_actions.txt:418–422`、`725–732`、`833–847` | 创建 root 为 creator；更新 root 为 Rite；原生界面编辑立即对 `head_of_rite` 写入 `has_edited_a_rite`。SHA `ef9367ddf5f89c912b895743f8b72441e88af3a5b03a5c1a9eddea0e5681ee2d`。 |
| `common/scripted_effects/03_dlc_fp3_scripted_effects.txt:721–747` | 真实新旧 head、家族专属头衔处理后，在新 head 的 House 调用 `set_house_head`。本次只复用底层 head 原语，不整套调用这个含头衔转移的 helper。SHA `1eaec32f3eda78ba70f25ff2ee0401836fa167a68ab6ce780d4594ea15abf6d2`。 |
| `events/title_events.txt:539–547` | 原版先核实际 House head／courtier 条件，再在该 House 对真实 root 转交 head。SHA `eca9ef652b1ae6adf1393bbc34b36d1a876e0c528998072a6e525a9bbb51d726`。 |
| `common/scripted_triggers/00_courtier_guest_management_triggers.txt:817` | Dynasty scope 的 `any_dynasty_member` 原版用例；本次用它拒绝其他有成员 House，没有新增未经核实的 `any_dynasty_house`。SHA `6ff4bc8350d2f21372967e98cacbc4e1d367745f70e649a4f3ee25bdbd131382`。 |

精确 `.4` 的原生 head 研究复用 `C:/ck3-dynastic-esotericism-20261024/R9-voluntary-house-head-transfer-a01/NATIVE-TRANSFER-SOURCE.txt`，SHA `b32d50d13eb24fa2100796ff040dfae28c6b8f6ee05c8df91257e28fa3b20652`。House scope 原语 `set_house_head` 的实际调用链为 `0x142D63EB0 → 0x1422F1E10 → 0x1422F2B20 → 0x142453410`：设置 House head，处理该 House 的 noble-family title，再从实际 House heads 重算 Dynast；不是独立 `set_dynasty_head`。底层拒绝空／无效目标及同一现任，本产品额外限定存活、同 Rite、实际新 House 成员和新对象来源。普通封建领地与原玩家不由本次代码主动更改，贵族家族专属头衔的原版联动仍须实际读回。

## 检查范围与后继验收

实际执行既有 Java grammar parser，对完整 `des_binding_effects.txt` 与 `des_on_actions.txt` 分别得到退出 0、`diagnostics=[]`、`roundTrip=true`；`git diff --check` 退出 0。grammar 只能说明解析／往返，不能证明 `.4` 的原生作用域、head 重算或游戏业务成功。两份游戏源文件保留 UTF-8 BOM。没有运行 Maven、构建新 runtime、启动游戏或提交 Git。

后继必须由真实 emitter／manifest／全部消费者的默认 Maven 验证与新正式树、新 fixture、新 runtime 开始；不能热改 a15。LIVE-11 依次覆盖直接建族、旧 House 真实交接、singleton NPC 后备，以及旧 Rite 的真实首次改革开启；每例在 Native 和独立 Save 同时检查实际提交 actor、默认 House、完整 House→Dynasty 拓扑、`house_head`、`dynast`、NPC 存活且非最终 head、原玩家及领地头衔。取消不能进入本路径。重复初始化与关闭重开不能建族、生人或把后来的 head 抢回；随后真实死亡／继承与冷载继续各自保留原件。任一领袖不符或出现 `des_creator_head_fault` 都不能授予 LIVE-11 通过。
