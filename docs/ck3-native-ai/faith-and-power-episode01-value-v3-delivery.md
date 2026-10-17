# 《CK3：信仰与权力》第一期：圣地的收益与代价

新版[约30分12秒讲解审阅片](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v3-final-label-repair-build-a01/native-run/derived/direct/episode01-review.mp4)已在本机生成，中文旁白、中英字幕；[本地入口与字幕、逐句稿、章节时码](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v3-final-label-repair-build-a01/local-delivery/README.md)可直接使用。文案按玩家的收益、损失和使用场景重写。机器音画、字幕与时间戳检查通过，Root已做关键画面抽检；完整1倍速观看和全片听检仍待实际审阅。精确文件与检查结果见[交付记录](faith-and-power-episode01-value-v3-delivery.json)。

本页绑定机器`4-8e1c2f1861`，上下文核对于2026-10-17T21:34:09Z。本轮知识与整片制作代码冻结在`d5b4c90044117e8fb90fb163f61b3a189320ed05`；下述实机研究使用CK3 **1.20.0.4**，原生执行源码为`e23f9de04018b638c62e0b72d39d88b56f0010cb`。新制作提交不能代替新版本或新原生构建的实机资格。

下面前三行是有来源的类型定义价值，实际收益还取决于主要关联、县主信仰、有效圣物稀有度及各自消费者；不等于已经读到所有角色的净属性。

| 玩家要比较的选择 | 值得关注的收益与代价 | 研究入口 |
| --- | --- | --- |
| 保留麦加主要名额 | 每名骑士的月虔诚倍率项，及随有效稀有度增长的骑士效能、奉献等级影响。奉献等级影响放大当前等级已有修正，不能当作直接加虔诚、升等级或加名额 | [主要等级价值](holy-site-major-grade-value12004.md) |
| 升格纳杰夫 | 主要层的每级奉献外交、神职好感与稀有度缩放月虔诚；应与被降格圣地的损失一起比较 | [主要等级价值](holy-site-major-grade-value12004.md) |
| 升格智慧圣地 | 主要层的每级奉献外交、学识及外交生活方式经验倍率；地方学识+2属于普通也可保留的地方层，不能算作升格新增 | [主要等级价值](holy-site-major-grade-value12004.md) |
| 采用已有圣地 | 增加本信仰关联，先评估地方价值、容量、费用与以后是否值得占主要名额；历史空纳杰夫采用后仍未激活 | [采用与新建价值](faith-and-power-adoption-value-12004.md) |
| 供奉或直接替换 | 圣物库存由共享站点共用；本次直接替换旧物归操作者，未另做移除，虔诚余额不变。意见及夺回圣物宣战理由只读到原版预览 | [共享圣物研究](holy-site-shared-relic-value12004.md)、[R0010实测](faith-and-power-episode01-r9-r0010-observations.md) |
| 退出共享／最后关联 | 共享退出库存留站点；最后关联退出另走县主返还规则。本次返还角色同时是操作者和县主，圣地对象仍可读，关联与库存清空 | [R0011返还实测](faith-and-power-episode01-r0011-last-faith-exit.md) |

游玩智能体可先调用`ck3_query_holy_site_planning_knowledge_v1`，`action`支持`adopt`、`create`、`promote`、`demote`、`abandon`、`enshrine_relic`、`remove_relic`。它提供比较输入、来源及已测历史案例；知识查询继续保持`state_observed=false`、`native_legality=null`、`action_ready=false`，不把历史报价或成功结果当作当前许可。

当前世界应另用`ck3_query_player_holy_site_v1`核对站点、关联与等级，用`ck3_query_player_holy_site_relic_context_v1`分别读库存、认可、当前有效稀有度及世界缓存，用`ck3_query_player_holy_site_relic_action_context_v1`读实际所有权、槽位、原版许可和预览。创建的类型、男爵领、圣物组合及正常创建条件见[一期规划](faith-and-power-episode01-planning.md)与静态知识的`create`项；每次动作仍须绑定当时的原版上下文。

R0010独立观察确认供奉、直接替换和共享退出的单项结果，正常闭场后已释放资源。共享退出后的原生当前重算为失活／稀有度0，但持久世界缓存仍激活／稀有度2；不能据其中一层说界面或全世界收益都已刷新，也没有闭合所有信徒同步与单圣地净贡献归因。

R0011确认最后关联退出后的独立返还结果；其创建动作已录制，成功退出动作没有录到。游戏经原生GUI正常退出、public及keeper为0并已释放，但原生host实际为1、报告仍RED，保留早先UI打开错误；没有把它改成整段PASS。闭场事实见[混合结果勘误](faith-and-power-episode01-r0011-closure.json)。单项研究成功不授整产品或发布验收。

旧版短回看、长研究回看及其历史证据继续保留。本页只增加新版入口，不改写旧片的制作、交付或验收记录。本次本地交付沿用用户选择“先提供本地文件，继续制作（推荐）”；本地文件及精确身份已由Root写入交付记录。

## 2026-10-17T22:21:32.936035+00:00：本地交付补录

machine_id: `4-8e1c2f1861`。实际成片容器1812.288021秒、54368帧、105句／10章、2560×1440／30fps／48k双声道，103,610,210 B。新整片严格AV解码通过；8个修正段独立逐帧检查，54368个新视频包呈现时间戳与保留的原逐帧时间戳全部相等，三套297组SRT正文与时码匹配。原6帧抽检发现顶部重复图注，后继仅移除15条重复来源事件，97段复用；Root已回看修正后的两处。修正版与原片分别保存，未再拍摄或配音。机器检查不授人工听审或全片1倍速签核。

制作源`d5b4c900`的Official与Linear CI均SUCCESS；这与原生执行源`e23f9de0`及R0011混合终态分别记录。新版沿用现有七类规划知识和双圣物观察工具，不改变当前原生许可，也不增加普通罗贝尔战役成绩。
