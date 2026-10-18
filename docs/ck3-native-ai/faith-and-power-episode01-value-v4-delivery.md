# 第一期 v4：圣地的收益、圣物与管理权

[播放新版 35:00.288 本地视频](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v4-final-build-a01/native-run/derived/direct/episode01-review.mp4)。[字幕、讲稿与十三章时码](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v4-final-build-a01/local-delivery-a01/README.md)已一同生成。新版使用115段中文旁白、347组中英字幕，已实际混入用户指定的战争系列配乐。

文案从玩家的收益、损失和操作场景出发，回应十项审片意见。全片音画解码、63008帧时间戳、三套字幕和音乐存在性检查通过；Root直接看过八处成片画面。完整人工听审与1倍速观看尚未完成。精确文件身份和证据见[交付索引](faith-and-power-episode01-value-v4-delivery.json)。

本页绑定 `machine_id: 4-8e1c2f1861`；实际生产闭场 `2026-10-18T04:56:10.260292Z`，Root画面审阅记录于 `2026-10-18T04:56:45Z`。影片为2560×1440、30fps、48kHz双声道，94,478,369字节，SHA-256 `3b6586ec511eb29823d43589092f7ca10ea05c0c01d10882422dda727a0714fa`。容器时长2100.288021秒；视频帧时间线2100.266667秒，二者分列。

本轮研究的玩家结论如下，完整条件与来源保存在[十项机制更正](faith-and-power-episode01-v4-mechanics-corrections-12004.md)：

| 玩家要决定什么 | 新版讲清的取舍 |
| --- | --- |
| 升格或降格 | 主要等级影响全信仰角色修正及部分其他消费者；地方效果和类型参数另查条件。比较新增收益时必须减去被降格地点的损失，不能把普通也有的收益算作升格新增。 |
| 采用还是新建 | 采用增加信仰关联，不转移土地，也不自动取得建筑、圣物或主要等级。原版均为总计9处、其中最多3处主要圣地；未找到正常决议、事件或效果提高最大值的路径。 |
| 放什么圣物 | 以当地伯爵领持有者的信仰、关联与认可判断逐槽累加。当前重算和世界缓存分开读；巴格达实测出现当前0、缓存2。 |
| 谁能取走、换物 | 三种地域身份只是完整许可的一部分；直接取走与替换的旧物归操作人。最后关联退出的返还另走当地持有者分支。 |
| 防范AI与关系代价 | 原版存在AI供奉替换和清理路径，没有普遍的人类捐献者保护；自然AI实际取物未观察。+15／−20好感修正指特定角色对操作人，不是全信仰普遍变化。 |

[官方术语](faith-and-power-episode01-v4-official-terminology-12004.md)、[等级与动态上限](holy-site-grade-effects-and-limits-12004.md)、[稀有度算法](holy-site-rarity-calculation12004-v4.md)、[管理、AI与好感](holy-site-relic-management-ai-opinion-12004.md)、[虔诚与奉献](holy-site-piety-experience-consumer12004.md)均已入库。新稿统一使用“伯爵领”“总宝物稀有度等级”“智慧之地”等官方用词，不再用“占用的网络”。

研究已接入现有 `ck3_query_holy_site_planning_knowledge_v1` 的七类动作，并为原有圣物context增加[逐槽解释](holy-site-relic-rarity-decomposition-python12004.md)；[规划澄清](holy-site-planning-v4-clarifications12004.md)保存具体合同。知识不冒充当前状态：`state_observed=false`、`native_legality=null`、`action_ready=false`。实际操作继续读当时的原版上下文与后态。

本片是附实机例证的机制讲解：真实录像91.6秒、退出后实机静帧4秒、原生读回图174.9秒、规则图1829.766667秒。图解不计作新增实机。R0010/R0011来自同机独立机制实验，游戏为1.20.0.4/build25734779，原生执行源码 `e23f9de04018b638c62e0b72d39d88b56f0010cb`；没有新增罗贝尔战役成绩。最后退出成功动作未录到，实际后态静帧已明确标注。复用录像中的旧蓝面板按用户授权保留；[退役检查](../../promo/ck3_faith_and_power/integration/legacy-decision-panel-retirement.md)约束今后的新录制。

配乐直接引用 `promo/ck3_native_war_ai/assets/music/quiet-courtly-tension.wav`，SHA-256 `fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f`。旁白0dB、音乐−17dB，循环原曲，2秒淡入、8秒淡出，关闭ducking和自动归一化。五个固定4秒窗口中，实际音轨残差与原曲相关性为0.996978–0.999624，增益0.996802–0.999050，误差比0.027433–0.077731，全部通过原阈值；这项机器检查不代替听感审阅。

原生产进程92713实际退出1：音乐验证用的独立参考音频相对seek时间基错误，随后校准又错误平移了整条最终信号。原RED和原run均保留。修正仅让参考音频按绝对PTS读取，最终音轨和原曲不移位；五窗后继验证与独立metadata恢复均实际退出0，影片字节未改，不重编码，也未重复全片AV或PTS检查。[配乐与修复说明](../../promo/ck3_faith_and_power/integration/episode01-music-profile.md)记录复用边界。

实际编码源码固定为 `8c76e5c4df19c181abff9a345ddea3e7b3d86a6c`，其Official与Linear CI均成功。后继证明修复另有两项新增纯回归测试通过，不把它们或后续文档提交冒充新的游戏实机资格。字幕分组与面板切换是作者编排，未做逐字强制对齐；本次八帧抽检不授整片人工签核。

本地先交沿用用户明确选择。素材按[统一存储策略](../storage-retention-policy.md)分类：最终MP4为delivered_media，默认30天复核；中间编码与抽帧默认48小时；必要配音、修正图的精确重建成员仅有限保护至2026-10-25T04:14:48.341907Z。旧素材期限不因本次交付自动续期，精确闭场与登记见交付索引。
