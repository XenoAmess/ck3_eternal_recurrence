# CK3 1.20：政体、头衔与信仰领袖

当前来源为CK3 1.20.0.4/build25734779；`machine_id: desktop-3fevhd2-1c74096080`，观察于2026-10-25T19:48:06Z及19:54:29Z。实际EXE SHA为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。原版脚本、随游戏提供的格式说明和来源摘要见[来源索引](research/government-faith-head-12004-2026-10-26.json)。本专题没有启动游戏或授予头衔，不授实机资格。

## 政体的归属与选择

运行时政体是人物的状态；头衔是初始化和转移的重要输入，头衔等级本身不等于政体。开局历史可给头衔明确指定 `government`，并在历史持有者初始化时使用。获地、继承、升阶和制度转换另受政府定义、旧持有者／领主、首都地产、文化与区域、宗教和DLC等条件影响。

原版 `common/governments/_governments.info` 的 `use_as_base_on_landed` 和 `use_as_base_on_rank_up` 说明，取得第一块领地或特定升阶场景可以旧持有者的政体为基础。`can_get_government` 是角色取得资格；`primary_holding` 与 `valid_holdings` 控制相应地产规则。`fallback` 则在没有其他适用选择时按优先级回退；封建制为fallback1。这不是每次改信都清空旧政府、重新选封建的规则。

原生完整排序、自建统治者替换具体职位时的政府继承、sticky政府与特殊身份冲突的所有分支尚未完成逆向。不能仅据字段名把“必定保持”或“必定改变”写成已验证行为。

## 教宗国为何是教会制

| 层次 | 原版来源 | 实际作用 |
| --- | --- | --- |
| 初始政体 | `history/titles/00_other_titles.txt:1–5`，`k_papal_state`在30.1.1明确写 `government = ecclesiastical_government` | 给教宗国指定初值，`k_`只表示王国等级。 |
| 宗教映射 | `common/religion/religion_types/00_christianity.txt:1–7`，`theocracy_government_type = ecclesiastical_government` | 指定基督教神权统治者采用哪种神权政体；Faith可以覆盖。它没有把所有基督徒变成教会制。 |
| 政府资格和地产 | `common/governments/02_theocratic_government_types.txt:75–140` | 决定适用人物与合法地产。教会制可以持有部分非教堂地产，不能只看首都城堡推断封建。 |
| 运行时对齐 | `11_dlc_pam_scripted_effects.txt:392–402`，`pam_align_theocracy_with_faith_government_effect` | 已有 `government_is_theocracy`、尚非教会制且宗教映射／资格满足时，改为教会制。 |
| 对齐的调用者 | `title_on_actions.txt:279`、`government_on_actions.txt:112–113`、`yearly_on_actions.txt:2432` | 授予头衔、改变政府与年度维护调用，并非所有普通信徒按宗教改政府。 |

`government_is_theocracy` 等是当前政府定义提供的分类标签，不是独立人物特质；给人物添加一个同名普通flag不能代替改变政府。

## 贤能制的对应例子

`history/titles/e_goryeo.txt:1–4` 在500.1.1明确指定 `meritocratic_government`，918.1.1再指定高丽首位持有者。朝鲜贵族家族头衔历史也有明确政府配置。因此高丽初始贤能制不能仅由帝国等级、儒家或朝鲜文化推出。

运行中 `00_administrative_effects.txt:106–213` 依据所选制度、领主和区域等选择行政分支；贤能分支处理地产与庄园，再执行 `change_government = meritocratic_government`。`tgp_should_become_meritocratic_trigger` 检查DLC及相应领主／邻近政府机制和地域条件。这是进入制度流程时的候选条件，不是所有亚洲信徒自动贤能的规则。无对应DLC时 `game_start.txt:1341–1353` 另有封建回退。

## 信仰领袖头衔能否指定政府

`Faith.faith_details.religious_head` 绑定信仰领袖的实际头衔；持有者取得该职位。`e_`只决定帝国等级，不能直接指定封建、贤能或教会政体。礼仪领袖 `head_of_rite`、信仰领袖和宗族族长是不同职位。

当前原版世俗领袖授予事件 `faith_creation.0011` 使用正常TitleAndVassalChange并设置世俗领袖继承法，没有直接调用 `change_government` 或 `set_primary_title`。这只能证明脚本没有显式改政府，不能证明获地／升阶／继承时的原生政府选择绝不发生。神职领袖的候选、创建与政府规则又是另一分支，不能用世俗路径概括所有领袖。

所以“拿领袖头衔即可强制指定政体”与“拿领袖头衔绝不可能伴随政府变化”都超出了现有证据。需要对实际人物、其原政府、领主与地产，以及确切教义组合，保留授予前后政府key和主头衔读回。

## 原版正常建立领袖的调用链

主动入口为 `create_hof_decision` → `can_create_head_of_faith_title_trigger` → `force_create_head_of_faith_title_effect` → `faith_creation.0001/0011`。没有预定义头衔时，世俗路径创建动态公国；预绑定空头衔时0011把它授给执行人。具体圣地、奉献等级、费用、领主等级与教义条件须按对应build和Faith读回。

首次Faith激活和Rite更新也会触发原版0001；0001没有以“已存在预绑定领袖头衔”排除动态创建。给新Faith预绑定较高等级头衔时，必须检查完整调用者，而不能只验证主动决议0011。保留原版正常自动建立不等于新增无条件免费授予。

来自“宗族化密教”两预置Faith的具体实现、特殊组合和游戏结果另归[产品需求](../mod_dynastic_esotericism/docs/requirements.md)与其测试记录。这里仅富化通用政府及领袖知识，不把两项产品的未来结果外推到所有宗教。
