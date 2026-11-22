# 新建宗族的家主跟随绑定礼仪领袖

这是2026-11-23新增用户要求的独立产品源码候选，仍沿0.2.3，未tag或发布。
实际文件级回归与未来游戏行为分列。本包只使用当前1.21.0.3原版可核脚本，
不引入Native/GUI输入或凭空填写引擎setter成功。

## 身份与作用范围

- “家主”落实为稳定宗家这个真实House的 `house_head`，以House作用域的原版
  `set_house_head` 设置，不把当前Dynast当成宗教领袖。
- “信仰领袖”在本产品按所绑定Rite的实际 `head_of_rite` 解析。该人物必须存活，
  当前Rite及Faith都精确匹配目标Rite。不会回退到一个不属于该Rite的共享教宗。
- 仅 `des_binding_mode = flag:new_dynasty`：这是产品真正新建的宗族。
  `native_dynast_reuse` 沿用玩家旧宗族的原合同，不取得强制更换其家主的新权限。
- 目标为Dynasty已经保存的 `des_cadet_main_house`，必须仍属于同Dynasty，
  并与新建绑定的 `des_join_house` 相等。不重选锚点，不改绑定反向引用，
  不用现dynast、继承人的当前家族或任意支系替代宗家。

House head和Dynast是不同状态。已核原版提供House的 `set_house_head`；本包没有
虚构 `set_dynast` / `set_dynasty_head`。引擎是否随实际House状态重算Dynast须独立读回。
年度全员回宗家后可为引擎的Dynast归属提供实际成员状态，但源码及House setter
本身不授“Dynast已经跟随”的结论。

## 时序

1. 原创建、Native首绑/编辑claim及普通成员同步保持。`des_sync_rite_effect` 最后
   调用新同步：实际宗教领袖走原有信徒入族路径，然后只在同一绑定宗族内进入宗家。
2. 对原版 `on_title_gain` 的真实新holder增加一条子action。仅新holder正是该绑定
   Rite的实际head时调用原完整同步路径，支持宗教领袖头衔继承/转交后的及时同步。
   不把任意得头衔者当领袖，也不覆盖原版on_title_gain的effects/events。
3. 原 `on_rite_updated` / 创建流已经走 `des_sync_rite_effect`，因此使用相同逻辑。
   既有30日维护也只多做这项固定head检查，不增加全世界逐日扫描。
4. `yearly_global_pulse` 的顺序保留 watchdog，再做原cadet全体在世成员（含玩家）
   回宗家，最后做新家主同步。原cadet effect、稳定锚点和不改死者谱系的规则不变。

遇到原 `des_binding_in_progress` 或 `des_native_head_claim_pending` 时不进入新策略，
不消费、改写或代替旧pending。新策略自己的重入标记仅保护一次当前同步。
原宗族中真正同Rite的领袖入族沿既有信徒迁移合同，不删除其原Dynasty/House对象；
不同Rite共享领袖只允许该人物实际所属Rite进入，其他绑定保留pending，不来回抢人。

## 观察与失败

先记录 `des_house_leadership_pending`，再执行有据的成员/House/setter步骤。
原领袖、完整绑定、稳定宗家及人物存活/同Rite/Faith在原adoption后重新核对。
只有实际 `main_house.house_head` 读回等于该人物，才清pending并记录
`des_last_religious_house_head`。仅人物入家、调用setter或打印日志都不算家主成功。
无领袖、异Rite共享Pope、失效/歧义锚点或引擎未改变house_head时保留pending。
未开启宗族化、反向绑定不一致或复用旧宗族时不强制迁移/设置家主。

## 本次资格与真实后继

本次28项文件级AST回归：新leader13项及原cadet15项。覆盖创建后同步、换领袖、
重复执行、旧DY复用、共享Pope/异Faith/死者、失效锚点/反向绑定、原pending、
adoption后领袖改变、重入、setter无效果时不报成功，以及cadet玩家年度回归不退化。
测试沿现有cadet模型/原解析器，知识和绑定内层为明确未扩资格的边界，不授引擎实机P。

后继只需对一个真实产品新建绑定及真实head变更核House/Dynasty/head身份：
创建后读宗家/家主/Rite领袖；实际合法转交/继承后读新head与house_head；
自然下一Jan1核cadet包含玩家回宗家后家主同步，HouseHead和Dynast分列读回。
不用完整365日新门，不把手动年度effect当自然pulse，不重复已通过Faith/颜色矩阵。
缺少实际引擎行为证据时仍为PENDING，不用本源码或28项软件通过替代。

新增生产文件只有leadership effects和triggers两叶，69→71；旧binding/cadet
runtime完整保留。Java唯一正式增量工具编测/清单构建/Git，Root唯一实场与发行。
