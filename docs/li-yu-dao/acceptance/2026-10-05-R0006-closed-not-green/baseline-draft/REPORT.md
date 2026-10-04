# 礼与道 R0006 中文验收报告草稿

本轮普通1066战役已开始，原版儒家入口夹具、正式入学、择师与朱子祭修的限定场景已取得独立存档读回。但 I2 资格后置检查失败，实际错误日志到达100,000条输出上限；整体 **NOT_GREEN**。这是运行中的证据快照草稿，退出、最终日志与source freeze释放均 **PENDING**，不能当最终已闭合报告。

冻结提交 `3d3305e75cf642a7a82bef5f9aee03dc76b3c10e`，产品树 `2e290b9b7fca02c38a33e4c73f5c46e7060dc9fa`，CK3 1.20.0.3 / build25652598；实际run R0006、execution `a29d24c0-d479-4989-bf90-16d4e1de0ea0`，PID12500／HWND2491650。快照截止 `2026-10-04T15:44:02.270631+00:00`。实际挂载59件产品＋7件普通入口夹具＋7件I2夹具，逐项原SHA校验匹配。PREPARED的NOT_RUN/false是准备时状态，后续真实启动/attach由独立run回执证明，不改写该原件。

## 已取得的限定结果

| 独立保存场景 | 结果 | 检查数 |
|---|---|---:|
| original-confucian-fixture | PASS_EXPLICIT_SAVED_SCENARIO | 34 |
| formal-entry | PASS_EXPLICIT_SAVED_SCENARIO | 42 |
| chooser-cancel | PASS_EXPLICIT_SAVED_SCENARIO | 52 |
| zhuxi-choice | PASS_EXPLICIT_SAVED_SCENARIO | 49 |
| practice-cancel | PASS_EXPLICIT_SAVED_SCENARIO | 52 |
| practice-a | PASS_EXPLICIT_SAVED_SCENARIO | 62 |
| i2-qualification-red | RED_QUALIFICATION_POSTCONDITION | 60 |
| i2-setup-fixture-only | PASS_SAVED_SETUP_GRAPH_ONLY | 96 |
| i2-after-actual-two-days | PASS_ACTUAL_D_PLUS2_OBSERVATION_ONLY | 110 |

baseline独立读回确认普通Robert Guiscard：Character31254、history1128、1066.9.15，初始Catholic/Roman rite、gold244、piety150、prestige2200。正式入学后Faith32儒家共宗、mainRite150孔门、36派；朱子择师后actorRite169。原版儒家夹具仅是正式入学的前置，不将夹具改宗算正式产品功能。

六项成功读回只覆盖各自明确场景。朱子祭修A已保存其费用、资源／XP、压力及冷却变化；其中的压力净变化另有原始解释。没有据一次朱子祭修推断36派全部选项通过，保存人物／family／title保护检查也不能代替UI验收。[checkpoint索引](checkpoint-index.json)绑定原存档bytes／SHA、SDK／wrapper和完整外置读回包，不重复复制约90MB存档或12MB全图。

I2资格夹具实际保存base Learning由7增加到14；同一次effect记录before8、delta7、after getter仍8，原失败事件存在，result为RED_QUALIFICATION_POSTCONDITION。60项检查通过是在正确记录这次失败及保护条件，不能把它写成资格成功。`0027-i2-qualified-save`文件名是当时意图标签。

随后夹具setup独立96项检查确认实际Faith32留下35派、Faith104新经疏仅Rite159；两个实际NPC65856／65857在玩家宫廷，actor仍朱子Rite169，两faith无宗主，保留人物／家族／世俗头衔保护。setup记录该对divergence3，同核心是LYD保守的main Doctrine集合比较，不能叫原生has_same_core接口。这个PASS仅是实际35＋1图；没有seed议案、投票、同意、签署、军费或正式合分结果，资格与whole-log仍RED。

## 日志零错误阶段与100,000条上限

早期loading、大厅、普通战役、formal-entry等实际已复制快照error为0；formal-entry回执13:06:45.878821Z及原0bytes文件保留。打开资格夹具后快照共47,166[E]，之前[51件完整诊断](prior-diagnosis/REPORT.md)不变。新的setup-submitted整份error为40,866,397bytes，SHA `fd8b659ef333ffe7e1a1dad1a20e7a8f892071bbcc41d36ec4866f229cd9827b`，100,000[E]全部逐条分类；原字节在[无损gzip](logs/i2-setup-error.raw.log.gz)，解压SHA逐字节验证。

| 完整100,000条的类型 | 数量 |
|---|---:|
| var链接unset scope | 33,319 |
| initial_source_faith变量未设置 | 17,598 |
| 比较右侧var无效 | 17,598 |
| learning_delta变量未设置 | 15,721 |
| ScriptValue none类型 | 15,721 |
| 条件／动态本地化缺失 | 43 |

主要位置全部属于实际I2夹具，产品主要位置0、Unknown parser/API0、未分类0。资格effect76为47,163条；setup后置trigger76为52,794条；其余43条是夹具display文本缺失（NOT_has_variable4、rite_faith_equal36、count2、main_rite_equal1）。原版debug trigger-localization引用是次级位置。[完整逐条账](classification/all-100000-records.jsonl.gz)与[签名](classification/signatures.json)保存首时间／位置／原块；首本地21:53:36，末22:21:12。显式tooltip标记、未标记none类型分开记录，不把显示预览问题冒充效果实际执行证明。

根确认native错误输出已达cap，完整原文件恰100,000个[E]；本包未从原文件发现独立cap-warning footer，因此保留这条证据边界。**后续没有新增行不能证明后续运行无错**；对后续正式议案／资格刷新等，日志观察覆盖不可用。实际setup保存图通过与满上限错误日志RED并存。

## 时间推进与请求真实状态

名为D+1/one-day的探针请求raw+24，实际raw53144328→53144376、+48，即从1066.9.15推进到1066.9.17，共两日；暂停回执实际paused=true，没有cooldown reset／game-state patch。report中的actually_reached_requested_delta=true表示已越过阈值，不能当精确一天。[原clock回执](run/clock-probes/i2-learning-refresh-001/REPORT.json)保持原字段；两日独立读回以另一个agent已冻结compact是否到齐为准，当前状态见report.json。

全部原请求、MCP request／response／SDK result和UI before／after／stdout／stderr按原字节保留或无损gzip。[请求状态账](request-statuses.json)分别记录dispatcher、SDK与native字段，`MCP_RESULT_RECORDED`或存档ACK不能证明资格业务成功。原0007等缺响应请求记NO_DISPATCH_RESPONSE_FOUND，不补造执行或失败回执。误名的qualified／one-day文件原名保留，真实结果如上；仅留在root工具输出的失败需另标tool-output-only，不虚构本地原件。所有图像原件仍在外置run，截图元数据、坐标回执和原SHA保留；本草稿精选Steam位移前后原PNG，不重复每个2MB画面。

## 官方CI、当前进度估算与下一步

- [Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37200670917)：run `37200670917`／job `111431527422`，精确3d源，实际completed/success。
- [Li Yu Dao static checks](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37200670823)：run `37200670823`／job `111431526874`，精确3d源，实际completed/success。

上述均为静态L0，不授予campaign／MCP／R6或发布验收信用。已有精确3d的[完整CI包](ci/README.md)含初始状态至终态、完整connector envelope和结构化UTF-8内容；原CI报告明确不作HTTP原始传输字节claim。只复制现有冻结原件，本次没有联网重查或触发CI。

向用户报告的约 **60%** 是当前开发进度估算，**不是测试通过率、36派完成验收率或可发布比例**。10月5、6、7—8、9是当次预计里程碑日期；遇到当前资格／显示错误、共识及宗主生命周期实机问题可能调整，不以预计日期写未来通过事实。

| 日期估算 | 目标／当前边界 |
|---|---|
| 2026-10-05 | parent exact scope pending |
| 2026-10-06 | parent exact scope pending |
| 2026-10-07—2026-10-08 | parent exact scope pending |
| 2026-10-09 | parent exact scope pending |

当前还需完成：真实学识刷新/资格条件确认；正式I2提案、各派/全部玩家同意、双方代表签署、实际join/detach及重复流程；I3教师／宗主缺位、挑战、认可及owned title生命周期；36派实际选项覆盖；D+30及reload；最终正常退出与冻结释放。军会／圣物仍未实现，不因全目录静态定义或这次setup引入测试信用。

## 永久投影与待最终闭合

[source投影账](source-projection-map.json)记录原路径／原bytes／原SHA、是否无损gzip及投影SHA。大存档、全图、重复PNG、历史总线／keeper journal原件永久外置；不删除、不再编码、不改原report或失败attempt。当前mutable native-state／心跳、live stdout不作为冻结最终证据。已有51件诊断不改写。后续root真正close后必须另建finalize新包补实际最终日志、process absence、keeper FINAL/CAS、allocator状态及freeze release；本draft保持历史原样。

本包操作限外置只读分类和复制：tracked/git/game/screen/CI网络操作均0；没有重新解析存档、制造同意或改任何游戏状态。
