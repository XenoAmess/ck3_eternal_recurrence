# Episode 04 R186：十四日、陌生事件续行与观测零样本边界

`machine_id: desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0186`。本场实际发生于2026-10-16 UTC，属于北京时间10月17日工作批次。完成回执为 **14日，date53148432→53148768（1067-03-05→03-19）**；第15日实际到date53148792（03-20）出现事件，未生成第15日完成回执。原计划28日未完成。

录制正常封装 **36.700秒／1101帧**，wall40.390308秒，均未达到请求的100秒最低时长；不是截断文件。陌生事件按原生第一显示项处理并独立读回消失，随后普通保存、游戏正常exit0与屏幕释放。本场没有新增业务正例、continuous clean、完整1×观看或signoff；研究 **6/14（42.9%）**、业务 **4/11（36.4%）**、合格动态 **0/11** 不变。

本场可移机入口是[精简证据](evidence/episode04-r0186-20261017/README.md)、[原媒体事实](evidence/episode04-r0186-20261017/portable-facts.actual-a01.json)及[独立观测摘要](evidence/episode04-r0186-20261017/observations.actual.json)。55份小原件和5段精确字节子树供视频与智能体开发共用；原片、PNG、存档、DLL/EXE、fullDefender及sdk-ready未复制。完整Driver结果和R06大树保留精确外置pin，**不声称完整scene/closure replay已便携化**。不同机器仍须重新核验安装、离线、权限、容量和实机。

## 来源、身份与准入

runtime/native源均为 **`d05b0c780b615faa714fdf0535403bb2e6941faf`**。本场a29[生产资格](evidence/episode04-r0186-20261017/A29-PRODUCTION-QUALIFIED.actual-a01.json)绑定CK3 `1.20.0.4`／Steam build25734779，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；DLL13,000,704 bytes、SHA `e4f2b7200a0029a56d83904b627aff724fb654b6983753da4c66af9d4e06fbbf`。canonical bootstrap/recorder/deadline的源commit字节、SHA与CRC32见[索引](evidence/episode04-r0186-20261017/source-index.json)；后续改码不重释旧场。

R0186由[allocator](evidence/episode04-r0186-20261017/ALLOCATION.actual-a01.json)独立分配，[prepare](evidence/episode04-r0186-20261017/prepared.json)正常载入R185 checkpoint：73,864,691 bytes、SHA `500ed157a401f22e8ee5433a84b6fb24850f357a964e4474c7b8af4ce67335ff`、date53148432。本场不是新1066开局或ABC共同T0。[身份](evidence/episode04-r0186-20261017/runtime-actor-identity.actual-a01.json)绑定PID16240、创建FILETIME `134366417898733491`、generation1、episode `native-31254-68303c9ae4fb`、actor31254；罗贝尔来源链保留，历史1128到当前31254的直接字段仍未解码。

[当次Steam离线审阅](evidence/episode04-r0186-20261017/steam-offline-reviewed.actual-a01.json)与[容量sourcefix](evidence/episode04-r0186-20261017/CAPACITY.actual-a01.json)分别保留。后者16:17:58 UTC绑定本场和d05源，scene上限2,281,701,376 bytes，profile/driver各805,306,368，raw536,870,912，other134,217,728；复核期限19:16:40.776628 UTC，未继承旧场准入。16:52:17 UTC的[开拍前读回](evidence/episode04-r0186-20261017/preflight.actual-a02.json)记录C卷free28,766,527,488／required28,580,179,353，D卷free53,351,690,240／required23,326,401,668。它们仅代表该机器与时点，不保证之后各阶段无限可写。

## R06：本地空条目已经读稳，完整父来源未闭

16:38:46 UTC的原生查询经[离线严格分析](evidence/episode04-r0186-20261017/r06/ACTUAL-ANALYSIS.json)核验。普通军事分支widget220可见/启用，帝国分支238隐藏/启用；二者local-definition-only结果均available、`stable_double_read=true`、variable index0、declared type635、entry count1、active1，definition与local entry存在。唯一条目为 **mode0、flag0、direct_value_present=false、provider_present=false**；provider vtable/slot2 RVA与owner ID均null。

这是稳定的本地空值，不能改写为provider读取失败、RVA0、来源模块已找到或补员已关闭。完整candidate仍 `unavailable/candidate_parent_depth_exhausted`，pass1/read51/depth8、parent_walk；full entries空、index/type null、native_receiver_selected=false。local成功与full失败是不同层，不能合并成最终receiver成功。

[来源说明](evidence/episode04-r0186-20261017/r06/ROOT-FINDINGS.md)给出已持有的`.4`调用链：mode0有复制entry值的源码分支，但本次没有观察生产调用或临时变量表；父层可能另有匹配项。下一最小观测是保全现有8层中已读取的祖先prefix并独立双捕获合法来源，不凭空追查provider RVA、不静默扩大到16/32层。没有开关动作、4A9转移、自然准备或实际ADD，**不授完整R06业务正例**。两份candidate子树及frame/public binding按原字节区间入包，原1,029,909B完整响应只作exact external pin。

## 付款与自然阶段：计数必须有对象和覆盖范围

17:13左右的[付款后态](evidence/episode04-r0186-20261017/r186-payment-after-a01.response.json)为同PID、受控no-load窗口1/epoch1：4条raw callback、30条natural parent return、qualified_records0、qualified_boarding_debits空；付款journal overwritten0，natural_journal overwritten0。四个raw callback的实际army ID是 **188、33、202、212**，不是Army18。当前actor原始context四值 `2c0/2c8/28/30` 均0，且本帧读取完整/稳定；它们不能证明整个窗口支出为0或已付维护完成，`maintenance_attribution=unclosed`，paid资格保持false。

[full-army查询的小回执](evidence/episode04-r0186-20261017/r186-natural-after-a01.response.json)将完整Driver结果保存为12,078,341 bytes、SHA **`df9b5db540b6176bd23ff55b4340048ca2235b8b8b945277bc593ec283a86deb`**。本包实际核验大小/SHA后，从 **`/army_strengths/0`** 提取精确子树；并不是顶层字段。该原件是完整Driver结果，`wire_bytes_preserved=false`，不能包装成原始pipe字节。

Army18 `army_natural_phase_observations_v1`有30条parent记录，membership依据是parent roster中的full CArmy ID occurrence；15条post-date的 `saved_mask02_admitted` 全false。**Army18出现在parent roster，不等于其实际调用了对应callback**。selected regular-core、assault/cleanup等字段为null；compiled-effect与late-event安装可见但所选事件数0。这些null/0各自保留，不外推为全游戏永不调用。

| 日志族 | Army18选择结果 | 该族全局覆盖边界 |
| --- | --- | --- |
| loss writer | event_count0 | oldest3239、latest3750、**overwritten_events3238**；不能声称窗口所有损耗writer均完整保留 |
| supply callback | event_count0 | 全局overwritten0；不能据零匹配推出已经发生库存结算 |
| payment callback | qualified0，raw为其他四军 | 自己的overwritten0不能外推到loss writer |

完整parent roster、所选loss/supply/compiled/late子树都作为[精确字节子树](evidence/episode04-r0186-20261017/source-index.json)保留，附原Driver hash与offset。它们能支持本次有限零样本诊断，不能闭合县损耗、饥饿、补员或军事维护实付。本场预定d27才启动的writer hook因d15事件提前结束未触发；[闭场](evidence/episode04-r0186-20261017/NORMAL-SAVE.actual.json)明确`NOT_STARTED_NO_OBSERVER_START_CLAIM`，没有observer启动或终止事实，不得将其写成正常采样完成。

## 第15日陌生事件已当场处理

第14份完成回执停在53148768；d15实际snapshot到 **53148792** 且event instance2出现，早停原因是native modal，不能将实际日期到达改记为第15份合格完成。原计划28日仍差14份完成回执；最低100秒等待按early-stop路径跳过。

[原生事件context](evidence/episode04-r0186-20261017/event02-context.response.json)识别 `pam_bull_events.0004`、calculated ID4380004、root角色31254、actor/bull_issuer30490；第一实际显示项为 **“就这样吧。”**，rendered/native index0、shown/enabled。初始snapshot报告option_count2，而实际显示context仅列出上述第一项，本包保留两种观测的层次，不伪造第二显示项。

当场[知识查询](evidence/episode04-r0186-20261017/event02-knowledge.response.json)返回 `event_definition_key_not_registered`，没有因此阻止按用户规则续行。17:06:01 UTC仅提交一次[原生option1](evidence/episode04-r0186-20261017/event02-select-first-once.response.json)；回执的postcondition_verified=true、old instance2→null、native52/public53→native53/public54，随后独立after snapshot的active_event=null，exact pin保存在[观测摘要](evidence/episode04-r0186-20261017/observations.actual.json)。ACK、选择后验、独立窗口消失分别记录，没有重投。事件定义与选项效果的持久研究由独立事件包交付，本条不声称旧registry已经覆盖此事件。

## 媒体与正常闭场

canonical recorder按已核CK3客户区屏幕矩形 **`[640,360,1920,1080]`** 采集1280×720，桌面2560×1440，HWND33950264与前台一致，初始遮挡空。实际为`gdigrab -i desktop`的客户区屏幕区域，**不是独立HWND渲染捕获，也没有录整张桌面**；guard未报错不代替全帧遮挡审查。

原片23,147,412 bytes、SHA **`7ca4edbcac4f46bd9dda6d796dadb20b619ad22cbdb5ec0333f18c1f23fda0bc`**，H.264／30fps／无音轨；1101帧、首PTS0、末PTS36.667秒、末帧结束36.700秒，无缺失或倒退时间戳。[完整AV解码](evidence/episode04-r0186-20261017/media.audit.actual.json)exit0、诊断空、未报告premature end；正常finish不等于100秒最低时长通过。实际ready→resume ACK为 **3.8324387秒**；3.272059属于R185，不能复用为本场值。

Root直接审阅三张1280×720原图的[限定回执](evidence/episode04-r0186-20261017/root-three-frame-review.reported.json)：首帧暂停03-05、Army18显示1173／1%／300/300；中帧03-11运行中、仍1173；末帧03-20暂停、中央“礼仪变化”事件框已出现但正文在该帧仍空。三帧未见外来窗口/桌面/Steam，不推未测人数变化；精确Root观看时间未随报告提供，回执分别记报告入档时间。三帧不是完整1×、clean或因果；17:06的选择发生在原片正常结束之后，不能作为片内事件选择镜头。

17:13:25 UTC[正常保存](evidence/episode04-r0186-20261017/NORMAL-SAVE.actual.json)为date53148792、checkpoint74,262,421 bytes、SHA `934aa1b99cc59874eb7365eb997f520753c4db4e31afd91a2d416e28a0244aef`；17:15:44 UTC[bootstrap](evidence/episode04-r0186-20261017/bootstrap-result.json)正常process_exit0、树清空、SDK/keeper/recorder闭场。[屏幕释放](evidence/episode04-r0186-20261017/SCREEN-RELEASE.actual.json)17:17:54 UTC实际exit0、seq5814、done、resources[]；`capacity_reservation_returned=false`，不据屏幕释放声称容量台账已经返还。新run可从正常存档独立接续，不能重用本场once动作、epoch或资格。

来源根为 `D:/workspace/ck3_native_war_ai_promo_work/e04-r186-window-capture-a01/`；机器盘符变化不改变machine ID，也不赋予其他机器状态。视频下游审查精确raw区间，开发决策下游按对象、调用者、父上下文及journal覆盖范围消费观测；所有素材与小原件继续按[统一存储策略](../storage-retention-policy.md)复核，不因本包续期额度或保护。
