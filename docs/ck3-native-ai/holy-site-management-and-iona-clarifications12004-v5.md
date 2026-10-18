# 管理身份、放弃下限与艾奥纳：作者 a03 窄澄清

机器 `4-8e1c2f1861`；实际资源读取 `2026-10-18T06:49:59.274057Z`；读取时仓库 HEAD `2c741ad29b6091087c3a2197145f5c17029af8ab`。版本上下文 CK3 `1.20.0.4`，沿用本轮既有预检，没有重新散列 EXE、启动游戏、构建或修改主树。来源是实际安装的原版脚本、官方简中与已经入库的 exact-build 条件合同。逐行原文及 SHA 在[逐行来源](holy-site-management-and-iona-clarifications12004-v5.sources.json)，SHA-256 `56002d15c8c3605ede30683134f1200b777b4894d075f5bb76fafeaac7bcc34a`。

## 不是任命一个“神学代理”

官方概念 `puppet / puppeteer / clerical_puppet / external_clerical_puppet` 分别是“傀儡 / 操纵者 / 领地司祭傀儡 / 神职统治者傀儡”。观察接口或研究文字中的代理别名，不应当成游戏里的另一种职位。脚本关系 `theological_agent_puppet` 对应领地司祭傀儡，`external_theological_agent_puppet` 对应神职统治者傀儡。

取得关系用人物外交互动。官方互动“傀儡领地司祭”面向自己的宫廷司祭；“傀儡神职统治者”面向同信仰、有统治身份的神职人物，当前脚本也明确允许无地的神职统治者。后者要求《By God Alone》，而且**发送者actor当前礼仪**具备以下三项教义之一：`doctrine_theocracy_temporal`（官方“神权制”）、`doctrine_monasticism_accepted`（接纳隐修）、`doctrine_monasticism_encouraged`（鼓励隐修）。这里的“神权制”是圣职专权传统教义，不是政府flag；接收者身份和关系另行检查。成年、行为能力和现有傀儡等条件仍保留，不能只据三教义判断互动可用。不能把“领地外”的官方简介误当成脚本绝对排除领内人物：实际可发送分支包含目标是自己的封臣等情况。

可直接口播的具体示意：

> 假设你是独立的天主教国王。你控制了自己的领地司祭，还不能因此替代教宗管理圣地，因为这个信仰已经有教宗。你需要自己就是这个信仰的领袖，或者让这个领袖本人成为你的傀儡。后一种办法，是在教宗的人物外交互动里选择“傀儡神职统治者”，先取得足够的关系筹码，再付出界面所报的虔诚，并让对方接受。关系建立后，你是操纵者，教宗是神职统治者傀儡；这才满足这里的管理权条件，采用圣地的其他条件还要继续检查。

这是假设人物关系示意，并非本轮已完成的天主教实机结果。可发送关系条件是 OR：国王级及以上目标的牵制分支要求强牵制，较低目标用牵制；也可通过自己是其领主且目标畏惧等级至少 2、自己是其家主、脚本列出的良好关系、囚禁、`subordinate` 或旧操纵者关系。不能把其中一条写成所有路线都必需，也不能说强牵制自动成功。接受度另算，信仰领袖本身还有 `-30` 因素；脚本接受后才通过事件设置傀儡关系。费用是 `medium_piety_value × (目标最高头衔等级 - 1)`，实际报价须读界面；对同一目标互动冷却 10 年。

没有信仰领袖时，管理规则才换成另一条：可玩角色拥有领地司祭傀儡，或角色采用神权政府；这两者取一后，还要 AND 奉献等级至少 4。成为某人的傀儡并不会凭空绕过这条：缺领袖的傀儡行动路径回查操纵者资格。采用决议还另有“独立”等共同条件。

来源：`pam_game_concepts_l_simp_chinese.yml:2–20`；`pam_character_interactions_l_simp_chinese.yml:571–582`；`pam_puppet_types.txt:3–7,110–113`；`00_puppet_interactions.txt:256–362,419–439,516–528`；`pam_interactions_events.txt:5273–5279`；`pam_scripted_triggers.txt:1194–1230,1292–1337`。

2026-10-18T07:00Z后继scope澄清：互动的256–268行在actor上调用helper，helper1211–1220在actor.rite内判断上述三教义OR；recipient身份另见273–313行。官方“神权制”见`religion_l_simp_chinese.yml:837`（836行为圣职专权传统组）。无信仰领袖管理回退1331行才使用神权政府判断，两条规则不可互换；相应脚本原文和文件SHA见本页来源包，本段为其后继作用域澄清。

## 管理圣地、编辑礼仪与创建信仰分别检查身份

`2026-10-18T07:35:38Z` Root整合本轮来源线程对同机已安装1.20.0.4脚本的窄读：`can_create_rite` 调用 `can_create_rite_trigger`，其中无条件要求 `faith.religious_head != root`。创建者仍是当前Faith领袖时，这项规则拒绝；不能因领袖有管理圣地的权限，就推断他也能直接创建新信仰。完整创建许可还有其他条件，仍以原生Can与实际报价为准。

编辑走另一组条件，包括 `rite.head_of_rite == root` 和未编辑标记；编辑许可不等于创建许可。它也不能证明新配置会产生新Faith，实际创建分支、主流核心和参数仍要分别读取。

双向实验中的阿拔斯方案因此明示准备：将 `d_sunni` 交给实际成年、同Faith的宫廷司祭，随后独立读回Faith领袖引用与实际控制关系，再核正常Can。转授ACK不是领袖身份已更新；该准备不直接赋予综摄核心、采用参数或圣地关联。本段是来源结论与场景方案，没有新增实机执行信用。

来源：`common/scripted_rules/00_rules.txt:24–33`，SHA-256 `c7ba2ae71e4461e88c6d5c86d8fc15fa7ccc73edae1e28fb3b65f0e362c4560f`；`common/scripted_triggers/00_religious_triggers.txt:3022–3069,3175–3178`，SHA-256 `e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2`。本段来源是本会话faith_research当次窄读与场景交接，未改旧逐行来源包。

## 放弃圣地：默认最低保留一处

正常放弃决议要求选中地点属于当前信仰、不是主要圣地，并且当前信仰的圣地总数严格大于 `faith.religion.holy_sites_min`。默认最低值是 **1**，因此当前至少有 **2** 处时，才可能在数量这一项允许放弃 1 处，放弃后仍留至少 1 处。不是要求保留五处，也不是数量够了就保证整项决议可按；管理权、目标、报价和冷却仍分别核实。

Religion 可以显式覆盖 `holy_sites_min`。本轮既有完整检查中，实际安装的 49 个 Religion 定义没有覆盖，沿用默认 1；这不能外推到其他版本、mod 或任意后续运行。

来源：`50_holy_site_decisions.txt:337–350`；`00_defines.txt:925–926`；`_religion_types.info:18`；既有 `effect-condition-contract-a03.json` 的 `limits` 及所绑定的完整定义清点。

## 普通圣地也能给特殊能力：艾奥纳完整例子

官方简中是 **“艾奥纳”**，任务名是 **“改变伯爵领信仰”**。可直接口播：

> 艾奥纳即使只是普通圣地，也能帮助在不列颠传教。宫廷司祭所属的信仰必须关联艾奥纳，还要控制具备这项能力、已经生效的圣地。这里的控制看当地伯爵领持有者是否属于司祭的信仰，不看最高领主的地图颜色。司祭在不列颠范围执行“改变伯爵领信仰”时，原版按基础传教值的百分之三十追加进度。它不是升格才解锁，也不等于完成时间直接缩短百分之三十。

严谨脚本 AND 合同如下：

1. 存在传教目标 `scope:county`。
2. 请求主体是 **`scope:councillor.faith`**，不是无条件使用玩家或最高领主的信仰。该 Faith 的 `controls_holy_site_with_parameter = iona_conversion_bonus` 为真。
3. `title:b_islay.is_holy_site_of = scope:councillor.faith` 为真，即艾奥纳所在地与该 Faith 的圣地关联门满足。不要把 barony key 擅改成并不存在的 `b_iona`。
4. 目标伯爵领的 `title_province` 属于 `world_europe_west_britannia`。
5. 条件成立后，本项贡献为 `0.30 × court_chaplain_conversion_base_total`；后者是基础值与司祭学识所给月进度之和。其余加减、乘数与任务资格依旧保留。

第 2 项的已核原生语义是：遍历请求 Faith **全部关联圣地**，找到缓存 Active 为真、类型含该参数、当地伯爵领持有者当前 Faith 等于请求 Faith 的地点；**不要求主要**。第 3 项的 `is_holy_site_of` 则只检查地点关联，不自行检查 Active。这两个谓词是分开的 AND，不能用其中一个替代另一个。Active 指缓存值，不能拿当前重评值或图标代替整个消费条件。

实际脚本 `0.30` 与官方说明的 `+30%` 一致；类型文件旁的旧 `+20%` 注释不应采信。没有新增任务实拍或最终传教时长验收。

来源：`00_holy_site_types.txt:464–469`；`99_court_chaplain_values.txt:535–538,973–990,2021–2032`；`00_court_chaplain_tasks.txt:235,453`；`religion_l_simp_chinese.yml:182–183`；`council_tasks_l_simp_chinese.yml:331`。原生语义复用 `effect-condition-contract-a03.json` SHA `af3c8c003f0287a147575d7ebd5f5945ddc67693adaf53c9e3c947bd446c595e` 中 `controls_holy_site_with_parameter` / `is_holy_site_of`，没有新增逆向。

## 可选嗣子论旁支的完整范围

官方简中 DLC 名称原文就是 **《By God Alone》**。嗣子论的核心可选条件为宿主有该 DLC、Religion 是基督教、且没有同时选入另一项互斥基督论核心（嗣子论、合性论、一性论属于该唯一组）。核心版本才包含此处讨论的 `allow_adopt_any_holy_site`；个人信条版本不能据同名视为相同效果。它的显示名称还会随礼仪语言成为“继承说”“义子论”或默认“嗣子论”。若主片不展开这个可选旁支，可留作者注，不需要用“还有若干条件”带过。

来源：`00_pam_tenets.txt:1575–1578,1616–1625,1638–1649`；`00_religious_triggers.txt:2061–2070`；`00_has_dlc_scripted_triggers.txt:95–97`；`dlc_l_simp_chinese.yml:50,110`；`pam_tenets_l_simp_chinese.yml:1236–1238,1462–1465,1543–1545`。
