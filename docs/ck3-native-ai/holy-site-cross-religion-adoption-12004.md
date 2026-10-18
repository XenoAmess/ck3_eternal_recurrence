# 基督教与伊斯兰教双方向采用既有圣地：1.20.0.4规划合同

machine_id：`4-8e1c2f1861`；当前安装资源只读核对UTC：`2026-10-18T06:18:07.315046+00:00`；仓库HEAD：`fa0d46eec95064a2a25fb2af74abc9bcc5f4bd36`。游戏版本上下文为1.20.0.4，EXE身份`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`复用本会话已核记录，本lane没有重读EXE、启动游戏或教改。所有原版路径相对安装`game/`，精确SHA及逐行原文在[来源](holy-site-cross-religion-adoption-12004.evidence.json)。本包属于源合同，不授当前操作许可。

结论：**两方向均有原版脚本支持的规划路线，但核心选择、Faith与Rite身份、定向兼容、实际敌对度和其他采用条件必须一起成立。** 只占领圣地、只选个人综摄，或只在旧Faith下另建一支非主流Rite，都不足以证明路线完成。既有R5是同宗教内Sunni采用Nadjaf/Shia，不是双方向跨宗教实机。两场新跨宗教结果仍未拍、未执行。

## 两个方向怎样配置

| 主体保留的宗教 | 计划采用的关联信仰 | 应配置到拟采用Faith的核心 | helper需要的Faith参数 | 个人版 |
|---|---|---|---|---|
| 基督教 | 伊斯兰教内某Faith | 伊斯兰综摄主义 `tenet_islamic_syncretism` | `islamic_syncretic_actor` | 不提供该actor参数 |
| 伊斯兰教 | 基督教内某Faith | 基督教综摄主义 `tenet_christian_syncretism` | `christian_syncretic_actor` | 不提供该actor参数 |

N01 4180–4220及4100–4141：各核心禁止在它所综摄的同一个宗教内选择，因此这两种交叉方向恰不被该宗教排除；同时必须通过`unique_syncretism_trigger`，不能在所选核心中再叠一个综摄。额外的“当地有相应宗教存在”限制在这些块中是AI条件，不应凭空加给人类玩家。个人版虽然能给物品、研习或流亡者等相关能力，并不提供这条Faith兼容分支要查的参数。

**定向综摄本身能否解决迷途要求？能提供相应覆盖，不必再把多元主义当作这两条路线的必选项。** N01 4134–4141／4213–4220把带对应`special_doctrine_is_*_faith`教义的目标设为astray；I04 185–189明确是本Faith对目标Faith的覆盖。原版基督教R01 41、伊斯兰R02 51分别赋予该特殊教义。H01 1–42还设置目标看综摄Faith的反向astray，但采用只检查行动者Faith看关联Faith的方向。以上是规则配置的闭合，现场仍须核对实际Faith参数与敌对度，不能外推到任意模组、未明覆盖或未完成的教改。

## 不要把新礼仪误当新信仰

采用helper T01 1972–1975调用`actor.faith.faith_is_syncretic_with(F)`；T01 3537–3567在**Faith**上查`has_doctrine_parameter`。它没有调用另一个`rite_is_syncretic_with`。I02 58–60与I03 29–43、60–64说明主流Rite拥有Faith有效核心；个人信条参数另属I01 137–145。稳妥的配置目标，是拟采用Faith本身确实暴露所需参数，不能拿角色另一个Rite的同名信条、个人flag或图标代替。

这个版本的原GUI是`RiteCreationWindow`：G01 593–628分别调用EditRite/CreateRite，L03标题和确认文案按`DivergenceResultsInFaithCreation`区分新Rite和新Faith。G02 831的默认分歧阈值为100。**选了一个核心，不等于必定新建Faith，也不等于旧Faith主流已经改变。** 若能合法修改实际主流Rite，可检验修改后Faith参数；若创建的是新Faith，要检验它的mainline身份；若只是旧Faith内非主流Rite，不能直接认定Faith分支成立。费用、可选性、CanCreateRite/CanEditRite及原生blockers仍按当场检查。本包不猜创建引擎ABI，也没有验证一套具体教义组合恰好跨过100或已经创建成功。

必要读回是：角色Faith、当前Rite、Faith主流Rite、各自核心与参数、两Faith实际敌对度，以及最终采用详情。这里没有独立重映射Faith.has_doctrine_parameter在C++内部如何委托Rite；不把主流模型说明与另一个Rite读口偷换成对该原生别名的实验验证。

## 其他允许路径与选择代价

1. **核心顺应。** N01 1743–1758要求所选教义不含基要主义或正义，典型配置为多元主义；提供`allow_adopt_any_holy_site`。基督教和伊斯兰教没有在该核心块中被禁止。D01 521–527直接查**行动者当前Rite**，这条特殊OR可绕过关系与敌对度组。个人顺应1777–1780不给此参数。它与前述Faith级定向综摄不是同一作用域。
2. **基督教的adoptionism核心。** N02 1575–1649要求`by_god_alone`／`has_pam_dlc`、基督教宗教及基督论互斥条件，核心给相同allow-any参数，个人版不给。官方名按语境显示继承说、义子论或嗣子论（L02 1462–1464）。资源文件存在不证明当前DLC功能已启用。
3. **本来就有兼容关联信仰。** 目标若同时关联一个与我们同Religion且敌对度不高于astray的Faith，无须为了这个关系条件另装定向综摄；但已属于我方Faith的地点不能重复采用。地名或宗教名胜印象不能代替完整关联集合。

这些路线都要比较放弃的旧核心能力、教改本身的资源与政治影响、后续经营收益和替代地点。只为取得一次操作权限而变更整个信仰，未必优于经营已有圣地。建筑还应交由对应AND/OR条件判断，不能把新增关联当成所有宗教建筑的统一解锁费。

L02 1699对allow-any的官方解释还提到“与主流礼仪有相同核心信条”。D01显式特殊分支没有另写目标同核心谓词；本包按实际脚本列出的分支，不从提示文案凭空补额外脚本条件，也不据flag英文名字宣称所有门槛消失。参数实际是否存在、最终许可如何，仍以原生当前上下文为准。

## 最终采用是哪些AND条件

```text
独立 + 本Faith圣地管理权限 + 总数未满 + 目标存在
+ 目标伯爵领持有者在己领地内且同一Faith
+ 目标尚非本Faith圣地 + 本Faith法理王国记录允许
+ [当前角色Rite有allow-any
   OR 存在一个关联Faith F：
        (同Religion OR 本Faith定向综摄F)
        AND 本Faith对F的敌对度<=astray]
+ 存在关联Faith G的全局伯爵领信徒数大于零（不要求在目标伯爵领） + 当前费用/冷却允许
```

F必须同时满足关系和敌对度，不能从两个不同关联Faith各拼一半。G属于另一次any遍历，可以不同于F。D01 529–534的active-site文案检查的是`num_county_followers>0`，**不是HolySite.Active，也不要求先把圣物供奉生效**。只看当地民众信什么同样不能替代持有者同Faith。

管理权限T02 1294–1337：已有信仰领袖时，角色自己或指定神学代理要对应领袖；无领袖时，有puppeteer则检查其资格，否则检查角色，要求可玩角色有神学代理或为神权政府，并且奉献等级至少4。不能概括成“独立皇帝自动有权”，也不能把无领袖分支的等级条件推广成所有路径。它也不是供奉/移除圣物那组三种地域身份。

王国限制T01 2000–2023检查**本Faith**的dynamic_holy_site_kingdoms；当列表和目标男爵领.kingdom存在时，不能重复使用该王国。不是全世界、整个宗教或所有初始圣地统一“一国一座”。基础采用费为monumental值1000，配置冷却5年；本Faith有免费次数时相关值归零并消耗一次（D01 543–561、C01 13–28、C02 1136、E01 1285–1294）。它们不豁免其他AND条件，也不是当前钱包的预先实测结果。

候选producer D01 588–601遍历realm County中的HolySite，只排除已关联；selector的is_item_valid 603–616也不含全部最终条件。**列出来、能选中、教改按钮存在都不等于最终CanConfirm。** 任何结果未知的Confirm先独立查后态，不能盲目重发。

## 两场新实机怎样取材才回答问题

地名候选：基督教到麦加或纳杰夫，伊斯兰教到罗马。它们都是未筛的新场景建议，不能预写现场registry ID、资格或成功。耶路撒冷等共享地点甚至可能已在我方名单内，不能只凭名胜归属挑实验。

| 阶段 | 两方向各自需要的观察 | 不能替代它的材料 |
|---|---|---|
| 教改前 | 当前Faith/Religion、当前Rite、主流Rite、核心/个人区别及目标关联集 | 只展示一个同名信条图标 |
| 教改草稿 | 核心综摄方向、互斥/选中状态、CanCreate/Edit、费用、是否实际创建Faith | 仅有静态can_pick或创建窗口 |
| 教改后 | 新/原Faith身份、mainline核心、所需Faith参数、实际敌对度；管理权仍成立 | 只看到另一个非主流Rite名字 |
| 采用前 | 同一实例、holder同Faith/realm、名额/王国/仍存Faith、原版完整terms、正常CanConfirm、实际quote/cooldown | 候选可见、旧R5允许或静态知识 |
| 一次采用 | 正常原版Confirm一次；unknown ACK与业务结果分开 | 重放未知结果动作 |
| 独立后验 | 我方名单、同一site的各Faith关系/等级、钱包、库存；再谈实际改变 | UI关闭或ACK本身 |

没有必要为了这章再重复整个升降/收益矩阵；后验需要把关联是否新增、钱花多少、原关系与库存如何说清。实际受益另看对应条件，不能先把采用拍成全套加成到账。两方向新动作与结果目前均为null，拍摄权限、预算和MCP写入口资格由Root另行安排。

## 已有实例与V4具体漏讲点

R5（machine_id同上，2026-10-17 12:01:34–12:01:36 UTC）实际角色15893、Rite15、Faith50、mainRite13；一次正常Confirm且bypass0。独立后读列表由26/27/0/14/29增32，目标32/nadjaf对Faith50为普通，关联51保留，实际扣1000虔诚，空库存仍空、未生效。R03 608–626定义Maliki属于Sunni并有核心顺应。**这不是基督教与伊斯兰教之间的实机；本lane也没有把各关系子谓词逐一做隔离实验。** R5只观测51 after主要，before等级缺字段，不补写等级一直未变。

V4讲清了采用不转移土地与一般价值，但未把“基督→伊斯兰／伊斯兰→基督”配置成可跟随的两条路线；未具体解释定向核心、个人版差别、Faith与当前非主流Rite、综摄自带迷途覆盖、完整AND及候选/最终许可分层；已有同宗教案例不能替代这两个新问题。本包是这些缺口的源合同，不是给旧片追加未发生的结果台词。

## 智能体可消费的交付

[knowledge-payload](evidence/holy-site-cross-religion-adoption12004-v5/knowledge-payload.json)按现有adopt知识的补充数据设计：两方向核心配置、actor-Rite特殊分支、共同AND、同一F/G见证规则、教改身份观测、失败/恢复和历史边界均有source refs。仅供现有MCP owner接入常量，不在运行时读取外置文档或绝对机器路径，不新增策略或授权：state_observed=false、native_legality=null、action_ready=false。

已有采用detail/open/confirm原生链可复用；已知教改draft/edit/create Faith或Rite的真实MCP取材缺口由能力owner盘点。本lane不凭函数名称猜ABI或声称这些写入口已合格。章节候选包含15段稳定解释和两个null结果槽，供同一部影片的主线编排；整体进展见[一期重排](../../promo/ck3_faith_and_power/docs/episode01-revision-v5.md)，未发生的结果不提前写入配音。
