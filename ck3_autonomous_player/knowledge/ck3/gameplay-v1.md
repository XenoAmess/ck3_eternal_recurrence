# CK3 玩法模型 v1

## 2026-10-21：R228 军费已计入正净结算的有限证据

[军费净结算条目](../../../docs/ck3-native-ai/episode04-r228-net-military-settlement-12004.md)供文件读取型智能体显式参考；普通 planner 不会自动加载 Markdown。R228 完成的钱包 ADD 为 111391，稳定 raw 项 a=384653、b=0、c=273262、d=0，a−b−c−d 与余额差相等；钱包自身 source/caller/unwind 支持这一条净额已计入非零军费缓存，现金上涨不能推军费为 0，也不需要再找一笔 gross-c 独立扣款。

此条不闭合 c 刷新 epoch、payer 或 cadence；原 paid/payer/cadence=null、natural_parent_matches=false 保留，fullR08=false。使用当前原生余额、已有承诺、未来军费与应急雇佣资金决策，输入不足只延后可选建设，继续合法战争处理；不要将已结算净额里的 c 再记成一笔实际扣款，也不要删掉未来军费预算。机器与原件 SHA、异常宽日期、跨采样器 join 限制见专题及来源索引；此为可引用知识候选，不是 planner 已消费记录。


## 2026-10-20：1.20.0.4 信仰引擎研究入口

[二期智能体参考](../../../docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md)提供装备／供奉、缓存、朝圣、精神领袖与大圣战的当前知识入口。实际知识 MCP 为 `ck3_query_holy_site_planning_knowledge_v1`，二期摘要在 `knowledge.episode02_research`；普通 auto 尚未自动调用。下文 2026-08-21 的 1.19.0.6 与旧屏幕／OCR流程按历史身份保留，不能覆盖当前 AGENTS 的原生事件处理及机器资格要求。

## 资料与版本边界

- 本机目标版本：**CK3 1.19.0.6 (Scribe)**；访问日期：2026-08-21。
- 入口：[CK3 Wiki](https://ck3.paradoxwikis.com/Crusader_Kings_III_Wiki) 与
  [新手指南](https://ck3.paradoxwikis.com/Beginner%27s_guide)。
- Wiki 页面更新速度不一致：Character、Traits、Resources 等索引为 1.19，Warfare/Titles 的部分内容仍是 1.18，
  Succession 还有更旧段落。Wiki 用于建立机制图谱；数值、DLC 门槛、按钮与 AI 接受度必须在本机 1.19.0.6
  可见 UI、原版文件或实机回放中重新确认。
- 1.19.0.6 调整过密谋邀请，并修复了此前偏低的瘟疫与自然灾害致死率，旧攻略的长寿风险不可直接照搬：
  [Paradox 官方 1.19.0.6 公告](https://steamcommunity.com/ogg/1158310/announcements/detail/677373278422041208)。
- “只带一个 mod”不等于“禁用 DLC”。本智能体保留玩家拥有的 DLC，并把安装内容指纹写进环境；政府/DLC 不同的
  episode 必须分层比较。

## 这个游戏在玩什么

CK3 的主体是角色和宗族，不是不会死亡的国家。时间实时推进但可以暂停、变速；一个角色会经历教育、婚育、
生活方式成长、统治、压力、疾病与死亡，死亡后原版进入继承。本 mod 的正式评分 episode 则在当前统治者死亡结算后结束。

核心可见状态：

- 六项能力：外交、军事、管理、谋略、学识和勇武。教育在成年时形成教育特质，生活方式继续积累 perk。
  参见 [属性](https://ck3.paradoxwikis.com/Attributes)、[特质](https://ck3.paradoxwikis.com/Traits)、
  [生活方式](https://ck3.paradoxwikis.com/Lifestyle)。
- 直辖领地是主要税兵与建筑收益来源；超过直辖上限会损害经济。封臣领地属于领地规模，但只按制度上缴一部分税兵。
- 金钱用于建筑、军队、雇佣兵、活动和礼物；威望、虔诚分别是世俗与宗教互动资源；影响力只在部分政府的 HUD 与核心
  循环中显示。角色底层影响力在其他政府下是否仍可被本 mod 改变并参与计分，必须在 1.19.0.6 实机验证，不能以 HUD
  不可见推断其为零；宗族威望属于整个宗族。参见 [资源](https://ck3.paradoxwikis.com/Resources)。
- 信仰决定婚制、罪恶美德、神职、圣战与改宗规则；文化决定创新、传统、兵种和部分继承选项。
  参见 [信仰](https://ck3.paradoxwikis.com/Faith)、[文化](https://ck3.paradoxwikis.com/Culture)、
  [政府](https://ck3.paradoxwikis.com/Government)。

## 一生中的基本循环

1. 稳住统治：结婚与继承人、宫廷医师、内阁与教士、配偶协助、直辖上限、财政和短朝意见。
2. 选择成长方向：按角色特质和近期目标选择生活方式，避免违背性格造成不可控压力。
3. 经营核心领地：优先建设长期亲自持有的首都圈，同时保持军费与意外事件储备。
4. 获取合法扩张入口：宣称、宗教/文化理由、附庸与婚姻宣称；宣战前核对敌我军力、盟友、财政和补给。
5. 打赢战争：职业兵、克制关系、骑士和统帅决定战斗效率；攻城兵决定占领速度；避免跨河、恶劣地形与缺粮。
   统治者亲自领军会增加受伤、被俘和死亡风险。参见 [战争](https://ck3.paradoxwikis.com/Warfare) 与
   [军队](https://ck3.paradoxwikis.com/Army)。
6. 扩展宗族：婚姻同时用于合法后代、联盟、宣称与遗传特质。“儿子父系婚、女儿母系婚”只是让后代通常留在玩家宗族的
   启发式，不是规则保证；信仰婚制、性别教义、婚姻接受度和后续支系创建都会改变结果。宗族相同也不保证始终属于同一
   家族，智能体必须从人物关系中复核。参见 [家庭](https://ck3.paradoxwikis.com/Family) 与
   [宗族](https://ck3.paradoxwikis.com/Dynasty)。
7. 管理本代的婚姻与继承风险：分割继承、合格子女和玩家继承人用于判断当前角色的宗族、联盟、宣称与猝死风险，
   **不用于玩家死亡后继续扮演继承人**。本项目是只玩一代的 Rogue episode；当前统治者死亡后读取结算并结束本局。
   参见 [继承](https://ck3.paradoxwikis.com/Succession) 与 [头衔](https://ck3.paradoxwikis.com/Titles)。
8. 控制死亡风险：压力跨越 100/200/300 会进入更严重阶段；瘟疫、旅行、战斗、攻城陷落、密谋和活动都可能提前终局。
   死亡是本局终点；下一角色必须从新的 episode 开始，并只继承跨局策略记忆与 mod 允许的永久记录。

## 感知与动作分解

智能体不能从“把地图变大”直接生成坐标点击。每个战略意图必须拆成：

```text
可见状态采集 → 候选动作 → 玩家可见 tooltip 核对 → 风险预算 → 点击 → 可见后置条件反证
```

第一批屏幕类别应覆盖主菜单、大厅、地图 HUD、人物、领地、议会、军事、事件、当铺、垂青、账簿和死亡结算。
Phase B 的强制设计契约是：任何不在分类器能力内的模态窗口都必须先在游戏内暂停、保存全屏与 OCR 证据，再退出本次尝试，
不能盲点一个“看起来像确认”的按钮。Phase A 尚无通用分类器或游戏内暂停动作；它目前只会等待主菜单【新游戏】两帧稳定 OCR，
超时则保留截图/OCR，并在进程树清理证明完成后终止 smoke。
