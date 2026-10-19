# CK3:信仰引擎：第一期成功后的维护交接

**第一期已完成，用户明确确认“一期成功”。** 本交接供后续同事接手系列研究与制作，当前任务是保存成功基线并开展后续选题，不再从旧V6缺图清单、旧百分比或旧排期恢复一期生产。

用户原话：“信仰引擎一期成功了。你要去度假了。编写交接文档给后续接手的同事，到docs。”正式系列名为 **`CK3:信仰引擎`**；战争系列正式名为 **`CK3:战争机器`**。旧文档与媒体中的“信仰与权力”是历史工作名。

编写日期2026-10-20（北京时间）。本次执行机器 **`machine_id: 4-8e1c2f1861`**；读取基线`ab7e90cdcad8407aeb761f46207fad9455566e99`。`2026-10-19T18:22:33.967614+00:00`只读核对最终媒体、字幕、关键输入和封面，共19个对象通过存在性、大小及适用的小文件SHA核对；没有启动CK3、配音、录制或重新编码。用户确认、源文件身份和本次核对范围另见[成功交接小索引](../ck3-native-ai/evidence/faith-engine-episode01-success-20261020.json)。

## 1. 接手先读，以及当前状态

| 顺序 | 入口 | 用途 |
| --- | --- | --- |
| 1 | [根AGENTS](../../AGENTS.md) | 机器身份、Steam离线、原生接口、完整规划器、存储与Git规则。 |
| 2 | [系列方法](../../promo/ck3_faith_and_power/docs/production-lessons.md)、[制作经验](../../promo/ck3_faith_and_power/docs/production-experience.md) | 用户反复指导后形成的研究、讲解、拍摄、审校和封面方法，后续每期必读。 |
| 3 | [一期V7交付](../ck3-native-ai/faith-and-power-episode01-value-v7-delivery.md)、[V7冻结讲稿](../../promo/ck3_faith_and_power/docs/episode01-narration-v7.zh.md) | 一期实际交付内容、成片路径及适用版本。 |
| 4 | [V7修订与免责声明](../../promo/ck3_faith_and_power/docs/episode01-revision-v7.md)、[永久逐段审校](../../promo/ck3_faith_and_power/docs/evidence/episode01-v7-textual-audit-20261019.json) | 两种领袖、官方中文、全文口吻和转场的审定依据。 |
| 5 | [品牌记录](../../promo/ck3_faith_and_power/series-brand.json)、[当前D封面](../../promo/ck3_faith_and_power/docs/cover-design.md)、[四方案存根](../../promo/ck3_faith_and_power/docs/type-options-20261020.md) | 已确定的名称、人物气质、字体及双比例封面。 |

本次用户确认是后继的完成事实。生产时的`LOCAL_ENCODED_REVIEW_PENDING_HUMAN`和“签收未完成”保留其当时身份，不再作为要求重做或等待一期验收的阻塞项；同样不据一句成功补造具体观看方式、Bilibili上传动作、BV号或播放数据。本执行没有进行平台上传，用户侧发布状态及链接未在本次交接提供。

[2026-10-19 V6休假交接](2026-10-19-faith-power-episode01-v6-handover.md)、[V6恢复日志](../ck3-native-ai/faith-power-v6-resume-20261019.md)、[初始导演案](../../promo/ck3_faith_and_power/director-plan.md)均为可追溯历史，不能用其中的“尚未成片”“135段”“460组”“42:41.067”覆盖现在的V7与用户确认。

## 2. 已完成一期的交付基线

| 项目 | 最终结果 |
| --- | --- |
| 内容基线 | V7；研究与演示版本 **CK3 1.20.0.4**。 |
| 声画 | 2560×1440、30fps；48kHz双声道；79,024帧；帧跨度 **43:54.133**。容器2634.154687秒、首视频PTS 0.021354秒，具体时间以最终映射和字幕为准。 |
| 文案 | 136段旁白、467组中英字幕、17章；13段新声音、123段精确复用旧音频。 |
| 成片身份 | 149,978,004 B；生产者SHA-256 `befe1a2293741c76dd5fcbbf64cd58a5889c9da4f63c88a5007551fdc89cabad`。 |
| 用户状态 | 已明确确认一期成功。 |
| 封面 | D「秘仪符刻」，16:9和4:3的JPG、PNG齐备；A/B/C/D全部留库存根。 |

以下绝对路径均属于`machine_id: 4-8e1c2f1861`，并已于上述核对时间读回。跨机接手先核机器与文件是否实际可读，Git中的索引不等于其他机器已具备媒体。

| 文件 | 直接入口 |
| --- | --- |
| 最终视频 | [episode01-review.mp4](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/episode01-review.mp4) |
| 中文字幕 | [episode01.zh.srt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01.zh.srt) |
| 英文字幕 | [episode01.en.srt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01.en.srt) |
| 双语字幕 | [episode01.bilingual.srt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01.bilingual.srt) |
| 中英完整讲稿 | [episode01-script.md](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01-script.md) |
| 17章时间点 | [episode01.chapters.txt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01.chapters.txt) |
| 本地交付索引 | [LOCAL-DELIVERY-a04.json](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v7-20261019/LOCAL-DELIVERY-a04.json) |
| 最终制作输入 | [formal-input.final-a04.json](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v7-20261019/production-plan/visual-repair-build-a03/formal-input.final-a04.json) |

这次对视频只核存在性和大小，SHA沿用原生产者记录；没有重新全片哈希、解码或播放。小文件按[成功小索引](../ck3-native-ai/evidence/faith-engine-episode01-success-20261020.json)记录的范围实际核SHA。原生产的wait0、整片AV解码、全帧PTS/CFR、字幕章节、音频与音乐检查在[V7交付证据](../ck3-native-ai/evidence/faith-power-v7-local-delivery-20261019.json)，不覆盖改写历史回执。

## 3. 一期实际上已经讲了什么

初始导演案曾把圣地安排为三期。后续V5—V7重排已把大量内容合进第一期，接手不能照旧表直接再拍“第二期：圣物收益”。实际17章详见上表章节文件，主要范围如下。

| 最终时间区间 | 已进入一期的内容 |
| --- | --- |
| 00:00—13:37 | 纳杰夫、坎特伯雷双向跨宗教采用；信仰/礼仪身份；创建新信仰与修改现有礼仪；权限、名额、费用和替代路线。 |
| 13:37—20:45 | 唯一共享库存、认可与有效贡献；普通/主要圣地的收益域、名额与边际取舍。 |
| 20:45—25:33 | 具体类型、核心信条、特殊能力与特殊建筑的要求，建造与启用分别解释。 |
| 25:33—38:04 | 圣物供奉、取出与直接更换，费用、好感、AI清理/操作边界和为圣物开战的条件。 |
| 38:04—42:42 | 退出共享圣地、新建智慧之地、最后关联退出的真实物品去向，以及当前值/缓存值的区别。 |
| 42:42—结束 | 回到玩家目标，比较采用、新建、主要名额、圣物用途和政治代价。 |

第一期已经形成“怎样做、谁得益、谁能再次改变、失去什么、替代方案是什么”的完整主线。后续研究仍可以深入上述主题，但应说明新的玩家问题与新证据，避免仅换实例复述一期。

发布标题格式沿用户给定的 **`【CK3:信仰引擎#1】……`**。会话中曾提供八个候选，未收到具体标题定稿指令；不要将其中某个候选写成已定标题。V7媒体中历史工作名与文件名保持原身份，不因正式系列改名自动重渲染或改写SHA。

## 4. 后续每期必须继承的表达与审校要求

### 机制先服务于玩家判断

从会影响选择的问题出发，研究具体权限、完整条件、成本、受益者、损失、后续可变因素与替代路线。条件复杂时追到原版脚本和引擎语义；不要以“可能”“还有条件”掩盖缺口，也不要把源码、原生许可、调用ACK和真实后态混成一种成功。

研究应主动深入，不能只按用户点名的对象查字典；同时优先补会改变决策的未知，不以穷尽整个宗教系统为开拍前提。比较普通/主要、采用/新建、供奉/个人使用、取出/退出时保留边际收益和机会成本。

### 讲成连续讲解

观众应能跟上“问题—现象—原因—选择—验证”。新指标在使用前解释，转场从上一个选择自然引出下一问题；独立实验重新说明初始条件，不把两份存档剪成一条资源流水。来源、日志、接口和验收术语留在研究记录，不让旁白出戏成检查报告。

原版画面呈现正在讲的具体对象，裁切保留名称、身份、当前/已知/草案状态、关键条件与操作关系。图解可解释规则，不能把示意或准备场景伪装成自然实机结果；没有拍到的过程不能由后态补造。

### 官方中文与两种领袖

本期1.20.0.4官方名称为 **信仰领袖**（`head_of_faith`，`faith.religious_head`）与 **礼仪领袖**（`head_of_rite`，`rite.head_of_rite`）。两者作用范围不同；人物可以兼任，能修改礼仪本身不证明有代表整个信仰采用圣地的身份。坎特伯雷案例真实兼任，两种权限已分别解释。

天主教页面“你的总主教”来自首都教区持有者，不能随手当作已经核实的宫廷司祭或礼仪领袖。Faith、Religion、当前礼仪、主流礼仪、核心信条和个人信条也须分别定位。

其他已审定用语包括创建界面的“分歧”、当前“亚美尼亚使徒礼”、“奉献经验”与奉献等级的区别，以及“聂斯脱里派”等该版本官方名称。完整条件和名称以[逐段审校](../../promo/ck3_faith_and_power/docs/evidence/episode01-v7-textual-audit-20261019.json)、[官方术语专题](../ck3-native-ai/faith-and-power-episode01-v4-official-terminology-12004.md)与实际版本为准，不机械替换全文或凭习惯换译名。

### 开场免责声明与版本

后续延续“钩子之后立即说明游戏范围与研究版本”的位置和口吻。第一期已实际口播、上字幕和版本字样：

> 先说明一下：本视频只讲《十字军之王III》的游戏机制。片中涉及的宗教、历史、文化与政治名词，仅用于解释游戏设定，不表达对现实宗教、历史、文化或政治的评价与立场。请勿将游戏中的操作和取舍套用到现实。本期研究与演示基于CK3 1.20.0.4版本。

新一期按真正使用的版本更新这句话与来源锁；不能把0.4结论直接改标成当前最新补丁。源镜像0.4固定提交`074429b3f6d9352a3cf4c5671725fee2f41267ba`；1.20.1及以后的变动另核，[来源调查](../../promo/ck3_faith_and_power/source-provenance-review-2026-10-17.md)保存原比较边界。

## 5. 声音、字幕与制作链怎样复用

继续使用已有中文参考声与IndexTTS链，沿[制作经验](../../promo/ck3_faith_and_power/docs/production-experience.md)及原V7配音/增量输入定位，不另换TTS音色。未改句和片段可按精确身份复用；改了语音或总声钟，字幕、章节、图层映射与最终检查必须随真实新时间轴生成。

主题音乐沿用战争系列 **`promo/ck3_native_war_ai/assets/music/quiet-courtly-tension.wav`**。第一期实际设置为旁白0dB、音乐−17dB，循环铺底、淡入2秒/淡出8秒，不做自动normalize、ducking或侧链；后续沿用这一静态设计，若改混音参数须记录并听实际输出。

双语字幕以同一语义单元成对安排。完整拼接正确不等于中英文与听到的词句同步；使用正式字体检查实际裁切和合成像素、行宽、阅读量与当前概念，不能只查关键词或文本长度。

生产入口继续是[现有integration](../../promo/ck3_faith_and_power/integration/README.md)，主要封装为：

- [episode01_formal.py](../../promo/ck3_faith_and_power/integration/episode01_formal.py) → `faith_power_promo.formal_episode`：来源绑定的正式输入、inspect和生产准入。
- [episode01_full.py](../../promo/ck3_faith_and_power/integration/episode01_full.py) → `faith_power_promo.full_episode`：已有完整合成入口。
- 最终可复用配方以V7的`formal-input.final-a04.json`、原文案冻结、`completed-review.json`及`raw-to-final-map.json`为锚点。旧ProjectConfig中的planned/CAPTURE_PENDING仅属于早期试拍，不代表一期现在缺成片。

仅在新任务确有修改时再走相应入口。新输出、新容量准入与原进程wait必须真实绑定，旧失败与新成功分别保留。遇到版本查询403/429，使用现有有限备用逻辑并核实际返回，不因源码有回退就宣布走通过；FFmpeg布局要检查偶数目标尺寸。V7 a02/a03失败与a04成功已有记录，不重跑不变范围或为修小问题另建整套后期平台。

## 6. 正式视觉资产与选型存根

正式采用 **D「秘仪符刻」**：冷银定制中文字形、细刻幽青光路、不完整仪轨圆环。宗教空间保持肃穆，未知与异常光线带出神秘和诡谲，人物保持冷静、聪明、略带危险感的数据幽灵气质。

| 比例 | JPG | PNG |
| --- | --- | --- |
| 16:9，1664×936 | [正式使用图](../../promo/ck3_faith_and_power/assets/covers/faith-engine-v4-d/faith-engine-16x9.jpg) | [PNG](../../promo/ck3_faith_and_power/assets/covers/faith-engine-v4-d/faith-engine-16x9.png) |
| 4:3，1448×1086 | [正式使用图](../../promo/ck3_faith_and_power/assets/covers/faith-engine-v4-d/faith-engine-4x3.jpg) | [PNG](../../promo/ck3_faith_and_power/assets/covers/faith-engine-v4-d/faith-engine-4x3.png) |

16:9精确保留用户选中的D图，JPG SHA `3bbfca07601d7b84f3fe87a73a9f601443de0749ee5cc3a5c3a399e0d2dedc94`。4:3是以D字形与已有4:3场景单独生成的适配，不是直接裁掉横图；JPG SHA `4d766e1794ef3793b74d29beb3266c1c7adca9e2f0a89c3b7b947a7557bbef20`。参数、提示词、原图来源及核对范围见[正式素材记录](../../promo/ck3_faith_and_power/assets/covers/faith-engine-v4-d/provenance.json)。

用户明确要求四个方案全部上库作为存根：[A圣典泥金、B圣堂碑铭、C圣物银饰、D秘仪符刻](../../promo/ck3_faith_and_power/docs/type-options-20261020.md)。四张JPG与提示词首次入库于`17104af448d4b3d698139ba2ebfee8f5b1f88f94`；正式D双比例及采用记录在`ab7e90cdcad8407aeb761f46207fad9455566e99`。保留存根，不把A/B/C误当待交付版本。

人物图只是角色形象参考，允许改变动作、行为与视角；先围绕主题构造完整场景，再让人物实际参与。白发、红瞳、黑衣、红色旋纹徽记与青色数据幽灵保持识别，手、身体、道具和环境共享透视与光照。不能把头像直接贴到背景上。

两次字体教训均已进入文档：战争式红褐斑驳显血色；全部洗成普通银白宋体又太朴素。后续应设计有辨识度的字形、宗教工艺、符号秩序和反光，保持可读与主次；不能只换颜色。场景暗光不等于标题毫无装饰，也不把画面提亮成金色宫廷海报。

## 7. 研究和智能体成果从哪里续

研究继续归入`docs/ck3-native-ai/`，把输入、候选、许可、成本、收益、风险和独立后态接入现有智能体。不要建立视频专用作弊旁路，也不要仅把知识停留在讲稿。

| 主题 | 优先入口 |
| --- | --- |
| 圣地总模型与原始来源 | [圣地研究](../ck3-native-ai/faith-and-power-holy-sites-12004.md)、[V4机制勘误](../ck3-native-ai/faith-and-power-episode01-v4-mechanics-corrections-12004.md) |
| 双向跨宗教采用、信仰/礼仪参数 | [采用专题](../ck3-native-ai/holy-site-cross-religion-adoption-12004.md)、[参数作用域](../ck3-native-ai/faith-rite-parameter-scopes12004-v6.md) |
| 普通/主要、有效贡献和收益比较 | [主要等级价值](../ck3-native-ai/holy-site-major-grade-value12004.md)、[稀有度算法](../ck3-native-ai/holy-site-rarity-calculation12004-v4.md)、[共享圣物价值](../ck3-native-ai/holy-site-shared-relic-value12004.md) |
| AI与好感 | [清理与宣战条件](../ck3-native-ai/holy-site-relic-ai-cleanup-conditions12004-v5.md)、[好感主体与叠加](../ck3-native-ai/holy-site-relic-opinion-conditions12004-v5.md) |
| 放弃圣地收件人 | [原版精确规则](../ck3-native-ai/holy-site-abandon-relic-recipient12004-v5.md)、[R0011最后退出实证](../ck3-native-ai/faith-and-power-episode01-r0011-last-faith-exit.md) |
| 建筑与神职呈现 | [特殊建筑门槛](../ck3-native-ai/special-building-religion-holy-site-gates12004.md)、[建筑导航](../ck3-native-ai/faith-power-building-track207-v6.md)、[神职预览](../ck3-native-ai/faith-power-clerical-preview-12004.md) |
| 原版界面与真实补拍来源 | [界面呈现与清栈](../ck3-native-ai/faith-power-presentation-ui12004-v6.md)、[R27—R32实际恢复](../ck3-native-ai/faith-power-v6-resume-20261019.md) |
| 研究回流MCP | [价值分析接线](../ck3-native-ai/faith-and-power-episode01-value-analysis-mcp-12004.md)、[V5知识](../ck3-native-ai/holy-site-planning-v5-mcp-knowledge.md)、[规划知识实现](../../ck3_autonomous_player/src/xar_autoplayer/holy_site_planning_knowledge.py) |

已有 `ck3_query_holy_site_planning_knowledge_v1` 支持adopt/create/promote/demote/enshrine_relic/remove_relic/abandon七类知识，不应另起同义工具。返回静态来源知识时`state_observed=false`、`native_legality=null`、`action_ready=false`保持真实；历史案例也不能替代当前局面的Can、报价与独立后态。

一期成功不把未验功能追认为实测通过。后续确有选题需要时再处理：

- 完整Construct候选与全部建造条件、外部默认神职预览、typed tooltip join/全局清栈仍有[V6最终交付](../ck3-native-ai/faith-and-power-episode01-value-v6-delivery.md)记录的业务边界。
- R32九个建筑讲解目标只有四个取得目标本体；其他五个使用真实当前对象配原版来源规则图解，不能改名伪装为目标阶段。
- 当前重评值与世界缓存值、角色总聚合与单站净贡献、定义数值与实际收益到账分别处理。不能从“算法已核”推定所有收件人的即时净增益已测。
- 本机历史构建资格、源码、SDK注册、运行时加载态各有来源；不能将早期能力页中的OFF/未部署当作永久现状，也不能拿新HEAD替旧DLL补资格。

这些是技术与后续研究边界，不是把已获用户认可的一期重新列为未完成。源码定向测试、GitHub CI、影片检查、真实游戏业务分别记账。

## 8. 下一位同事的建议开工顺序

1. `fetch`后按根规则同步主线，读本文、方法、V7讲稿和17章内容；确认当前用户是否给了新的选题或修订要求。
2. 以一期已覆盖范围作去重，形成下一期真正新增的玩家问题。可优先考虑“创建信仰与修改礼仪怎样改变权责和长期收益”或其他宗教系统专题；这是建议，不是已确定片名或已开拍事实。用户要求继续时可在既定系列范围内自主推进研究和提案，不新增例行审批等待。
3. 先列会改变结论的未知、已有可复用知识与最小实证，再写连贯讲解和逐句需要看见的对象。旧三期提案作为选题仓使用，不作为必拍任务清单。
4. 新版本、新原生观察或动作有需要时才开新场；通过现有MCP和公共现场流程。画面或媒体只需局部修订时按实际变化范围复用，不重做全部配音、研究或实验。
5. 将新规则、反例、条件和实际失败写回原生专题、系列方法与现有智能体；交付时更新当前入口、实际证据和进度。百分比与时间节点针对新的工作包重新估算，不继承旧V6的75%或10月19日旧排期。

## 9. 机器、实机和容量的接手边界

本机工作根为`C:/workspace/ck3_eternal_recurrence`，外置一期根为`C:/workspace/ck3-faith-and-power-20261017/episode01`，此次只读核对属于`machine_id: 4-8e1c2f1861`。Git包含知识、代码、讲稿、封面和小回执；MP4、配音、原片及大量生产输入在外置目录。跨机先实际核可读性与必要材料，再按现有来源迁移，不能用同名文件或SHA摘要冒充现存原件。

本交接没有切换Steam、启动游戏或更改系统权限。下一场实机先重新读机器ID、核实际EXE/build/加载来源，按[Steam离线恢复](../ck3-native-ai/desktop-steam-offline-recovery-2026-09-27.md)及[新鲜画面规则](../ck3-native-ai/steam-offline-frame-freshness.md)取得当次离线证据；原生身份、场次、存档和观察绑定后再操作。别的机器的离线、安装、Defender或资格不能外推。

Windows操作使用Python与`cmd.exe`，禁止PowerShell。新录制不得出现退役的旧蓝色决策面板；保留现有原生决策与新显示链。自动游玩使用完整规划器，处理真实战争，不能恢复nonwar-only路由。陌生事件按根规则采集、合法续行、批后离线补知识；原生通道能用时不以OCR或鼠标替代。

后续存储遵守[统一策略](../storage-retention-policy.md)与[参数](../storage-retention-policy.json)，不继承旧“全部永久保留”或“完结就整树删除”。最终视频、当前必要来源、D正式封面和用户要求的四方案存根分别分类；可重建过程件与已替代导出另作精确评估。先读用户永久保留索引，按身份、用途、替代证据和期限处理，不按目录名删除。

旧媒体保护复核最迟2026-10-26，以各原回执更早期限为准，本次交接不重置旧期限。四方案已按用户要求转为仓库设计存根，跟踪文件按记录维护，不进入本地派生物自动清理；新保护不等于永久豁免。当前必要输入跨机转存如用于删除本地原件，须先核对远端精确对象可读及大小/SHA。

本次文档工作包使用新4MiB有限额度；先前D封面包已闭账future0，旧V7渲染和各场次额度也已关闭。只读准入时（`2026-10-19T18:20:41.832735+00:00`）该机器项目旧保守上界48,667,516,453 B、有效配额51,177,672,294 B；这是来源机器当时的保守账，不能直接给后续录制/构建沿用。新任务按新鲜卷读回、并发预留、系统增长和峰值重新准入；不把取消预留算物理释放。

所有新任务遵守任务总线登记、轮询和共享资源归属；有受管现场时checkout冻结，正常收场释放后再应用tracked修改。完成的独立工作包按根规则验证一次、提交英文信息、`fetch + rebase`后普通推送，禁止merge和force-push。

## 10. 交接完成范围

这次移交的是**用户已确认成功的一期V7、已选定D双比例封面、四方案存根，以及可以继续使用的研究和制作方法**。没有重编码、重拍、改变已选图像或另开下一期；原视频、封面和历史证据保留各自身份。

后续同事从新任务的玩家问题出发继续系列即可。一期的旧缺图与旧待签收状态不再是接手阻塞项；技术缺口按后续实际用途处理，平台发布信息按实际提供的记录维护。
