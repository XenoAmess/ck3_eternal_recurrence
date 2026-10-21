# 二期重剪V2：朝圣账单与教首归属

`machine_id: 4-8e1c2f1861`；2026-10-21 13:43—14:03 UTC完成编码及技术检查，13:59 UTC完成Root九帧直接审阅。用户在[一期重合审计](episode01-overlap-audit-20261021.md)后明确要求“对。剪。”，本版据此重新组织既有材料，没有启动游戏或补拍。

**当前本地审阅片：[18分16.533秒MP4](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/episode02-recut-review.mp4)。** 相比原29:02.400版缩短10:45.867。主线改为“朝圣要准备多少钱；出钱建立教首后，谁拿到职位”，不再以圣地收益、圣物用途的重复基础教学开篇。完整人工播放和试听尚未完成。

## 实际删剪与导演路线

- 从88段中删除37段，保留51段原声画，新增3段转场，共54段；未重新生成保留段的声音。
- 原第二章人物收益、第四章圣物用途整章移出正文；旧片结尾三段删除，包括与一期原句相同的`E02-C7-P04`。
- 实际朝圣账单在01:05.600进入；教首建制案例在08:16进入，另一人获得头衔的结果在08:32出现。随后明确回看确认之前，避免把不同实验存档接成同一世界的连续动作。
- 殉道、奇迹改为末段补充，独立内容约2:12；加转场共2:26.667。结尾只留22.4秒。

| 开始 | 章节 | 观众新增的判断 |
|---|---|---|
| 00:00.000 | 70金币之外：先看实际账单 | 出发报价不能直接当作整个行程预算 |
| 01:37.067 | 回看出发前：资格、目的地和配置 | 根据计划选择目的地与配置，区分规则说明和本场结果 |
| 04:50.667 | 抵达、结算与201天行程 | 区分途中消费、抵达、活动结束与实际归返；201天为完整行程 |
| 08:16.000 | 建制结果：出钱的人为什么不是教首 | 付款人和新头衔持有人可能不同 |
| 10:13.867 | 回看付款前：资格与报价 | 先看授予顺序和资格；显示折扣不等于已经实现节省 |
| 13:25.333 | 建立教首之后：大圣战仍有权限门槛 | 建制完成不能代替最终发动许可 |
| 15:27.467 | 补充：殉道与奇迹的新差别 | 相比一期智慧之地，比较两种新增类型的条件与奖励 |
| 17:54.133 | 收束：行程预算与职位归属 | 用本期两项具体结果收束 |

**内容与字幕复核通过其检查范围。** 实际map、54段讲稿和三种SRT逐项核对，顺序与批准计划一致；原审计D/M两类段落全部未选中，原C2/C4与重复结尾不存在。三种SRT各142条，无越界或逆序，最后结束18:16.081，片尾留0.452秒。仍有少量保留段中的旧规则引用，不能称为逐句零重复，也不能把旧版24.89%的分类比例当作新版重复率。旧版审计和撤回原去重PASS的结论继续保留。

## 文件、伴随文本与实际检查

| 项目 | 实际结果 |
|---|---|
| MP4大小 | 60,964,582字节 |
| SHA-256 | `c01b130caba763d6849dc8dc341ad9d5fe54db89b8a8a053009ed52af30901ce` |
| 视频／音频 | H.264，2560×1440，30fps，32,896帧；AAC，48kHz双声道 |
| 实际时间轴 | 首视频PTS为0，末帧1096.500；画面及封装时长1096.533333秒，无继承旧片PTS原点 |
| 原始编码 | PID16296实际wait0；只执行一次最终视频编码，没有完整干声影片中间副本 |
| 技术检查 | 完整严格AV解码、probe、全部帧PTS、音频信号原进程均0；音频mean −22.5dB、max −3.7dB |
| 画面抽查 | Root直接查看8、100、300、516、539、770、915、935、1082秒九帧，标题、双语字幕与关键边界可读；仅支持抽样范围 |

[中文字幕](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/text/episode02.zh.srt) · [英文字幕](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/text/episode02.en.srt) · [双语字幕](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/text/episode02.bilingual.srt) · [实际54段讲稿](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/text/episode02-script.md) · [章节时间表](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/root/episode02-chapters.txt)。

配乐检查保留一个真实失败及其定界结果：原producer PID8964最终wait1，原因是原`music_presence`的第五个尾窗未通过。前四窗通过；同一尾窗改用最终map绑定的最后一段`E02-C7-P03`直接读取干声，按32,224帧／30确定起点、局部16.399999667秒取样，原阈值下相关性0.985661、增益0.996218、误差比0.170592，全部通过。没有拟合信号移位、改阈值或重编码；Root据此接受“四个原窗＋同尾窗独立原片参考”的有限音乐抽样闭包。原随机concat取样FAILED、额外顺序concat参考未通过和诊断a01失败均保留，不能把producer最终退出改写为0，也不宣称整个原自动流程成功。

技术出处：[汇总交付与逐项原回执](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/JOINED-DELIVERY.actual.json)、[原生产等待](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/RENDER-ORIGINAL.actual.json)、[原配乐检查](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/music-presence.json)、[同窗独立参考诊断](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/tail-diagnostic-a02/RESULT.actual.json)、[九帧审阅](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/qa/final/VISUAL-REVIEW.actual.json)。未做人工整片1×播放或完整听审；新三段字幕句内时码按实测整段音长分配，未获得逐词语音对齐。

## 来源和研究边界

[机器可读交付及54段选择表](recut-v2-delivery-20261021.json)保存实际成片、51个旧段与3个新段来源、37项删除及新文字。原制作输入仍为C16 `5b477b42b0f90aad8a4cda96ee5916eff0656cc5`的2,112,195字节输入，SHA `b4caa6eb93b7fabf22d6fd0abedc7cca4e7d82892d8496d19bed02bfa5b63a7a`；本次Root来源为`6fd66d8b73bceade75e19a5fad6bf55d0d9ef60b`，重用生产器36,411字节、SHA `4bdc4f2ecae69c44263c45f875e34c4ccb91e993eb393412ea7b7f684ef10a8a`。原29:02.4版及其[交付记录](local-review-delivery-20261021.md)作为历史审阅版保留，不与本片混用字幕或时间轴。

本版不增加游戏业务验收信用。H1仍只有普通Native300虔诚／225金币与主要GUI200／150显示，完整主要臂报价和资格未核实；H2是独立恢复后的真实一次建制，付款人31254、新头衔持有人65865，礼仪领袖及主流礼仪未因此改变；H3最终发动许可未知，本场未发动。朝圣70金币是出发价，途中消费不能按钱包净差当作总旅费，历史经验差未知不补造。原R27／R29行政失败闭场及OS退出未证仍保持。

删去影片段落不删除研究知识。[游玩智能体参考文档](../../../../docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md)及注册MCP仍可查询历史研究，普通auto自动消费仍未接通。本机继续按[长期本地交付偏好](../../../../docs/maintenance/machine-preferences/4-8e1c2f1861.video-delivery.json)提供视频，不配置OneDrive；其他机器不由此改变。

存储沿用统一策略1.0.0和本次一次共享768MiB准入，不借用已闭场旧额度；本轮没有为腾空间删除旧媒体。成片与小型交付记录按record类180天复核，声音／片段按delivered_media类30天、可重建QA按derived类48小时复核，届时按用途判定，非到点自动删除。两个媒体scope实际共70,000,640字节分配上界、future0，释放未消费预约不是磁盘回收；见[媒体scope闭场](C:/workspace/ck3-faith-and-power-20261017/episode02/recut-v2-20261021-a01/render/SCOPE-CLOSURE.actual.json)。
