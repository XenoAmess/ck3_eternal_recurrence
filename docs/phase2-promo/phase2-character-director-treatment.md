# 《天朝特色 361 制》二期人物版导演方案

状态：**正式并行成片方案（character-led cut），不是废案，也不是制度版的草稿。**

对应的另一条独立成片路线是 `phase2-institution-director-treatment.md`（制度群像版）。两版共享二期的真实实机素材合同、十章结构和八个 canonical span，但采用不同的叙事主角、旁白组织和剪辑节奏；最终应分别导出、分别审阅，不得只把同一条片换标题交付两次。

## 一句话定位

跟着一名真实历史官员走完一个绩效季：他先被算成一个档位，随后发现这个档位会进入案卷、碰到经理、争夺晋升和编制，并在下一轮继续追上他。

这版的戏剧问题是：**“当一个人被组织写成一个 C，他还能把自己改回来吗？”**

它与一期的区别不靠宣称“功能更多”，而靠完整呈现二期新增的组织后果。人物是观众的入口，真正逐步展开的仍是事实档/配额档、经理治理、晋升薪酬、HC、项目指标、事故和跨周期制度债。

## 成片规格

- 目标时长：`09:30`，允许随真实语速和画面节奏落在 `08:00–12:00`。
- 中文主叙事、简体中文主字幕；英文为同屏次层字幕，不抢中文层级。
- 旁白：`zh-CN-XiaoxiaoNeural`，语气像一条过分礼貌的企业培训片。笑点冷处理，不用夸张综艺音效替代信息。
- 画面：1920×1080、H.264/yuv420p、AAC 48 kHz stereo；最终仍以有效媒体合同和构建门禁为准。
- 十章固定：开场和结尾为双语生成卡；中间八章依次绑定八个 canonical gameplay span。
- 第一次可见画面直接进入人物、榜单或案卷，不出现 Launcher、主菜单和 loading。

## 主角与配角

### 主角

在最终 canonical seed 中选择一名**真实历史角色**作为贯穿人物，满足：

1. 不是临时生成角色、测试角色或 fixture 专用角色；
2. 在人物界面、榜单、告身或正式事件中能被清楚辨认；
3. 尽量同时出现在考核、PIP/申诉、晋升/薪酬与 workforce 等片段；
4. 其稳定身份必须由最终 capture/artifact 证明，导演稿不预写姓名、官职或最终档位。

成片第一次出现时用一个克制的双语 lower-third：

> `[真实姓名]｜本轮受评官员`
> `[HISTORICAL NAME] | OFFICIAL UNDER REVIEW`

若某个 canonical span 的真实产品事件不能证明它仍属于同一人物，就不把该段冒充他的亲历。镜头改为“他所在制度的另一处正在发生什么”，旁白使用“与此同时”“在同一套制度里”，不能使用“因此他”“正因为刚才”之类因果连接词。

### 配角

- 直属经理：既是打分者，也是 `manager-governance` 中被更上层制度约束的人。
- 同侪：承担配额边界、背靠背互评、项目贡献与 HC 竞争的可见压力。
- 组织本身：通过榜单修订号、冻结案卷、事件状态和跨周期债务反复出现，形成无形反派。

配角也只使用真实历史角色。无法由实机身份账本支持的姓名、关系和动机，一律不写进旁白。

## 导演原则：让观众追人，不替证据编故事

人物版允许建立情感连续性，不允许制造事实连续性。

- 可以说：“这份档位开始进入他的工作生活。”前提是画面确实展示同一冻结案件。
- 不可以仅凭相邻剪辑说：“因为经理压了他的分，所以他失去了晋升。”除非同一冻结案件和后果被 provider-observed。
- 操作按钮和 command ACK 不是结果；动作后的真实状态、正式事件和身份绑定才是结果。
- 八段素材必须满足拍摄时有效的 `zg361_phase2_footage_intake` 合同：共享同一 canonical seed/save lineage 与精确 source/game/mod-mount identity；每个 span 内的 pre → action → post 保持同一 session/PID/generation/revision chain。不同 span 可以按合同干净重启 CK3，但剪辑不得把重启伪装为单次不间断实录。
- 旧一期画面只允许作为明确标注的十秒回顾，不得混入八个二期实机证明段；fixture、测试按钮、验收 UI、生成角色和旧 take 都不能冒充二期 live。
- 所有具体结论在第一次 1× 素材审阅后按实际画面缩短或删除；不得为了保住本稿句子去寻找看似相符的装饰画面。

## 十章时间线与可拍摄分镜

### 01｜00:00–00:35　冷开场：他的名字被写进榜单

类型：`generated_card` + 经审阅的极短实机闪切
章节 ID：`phase2_minimal_recap`

画面编排：黑场先听到翻页声；榜单一闪，切人物肖像，再切一份尚未揭示结果的案卷。标题不立刻说“C”，先让观众看见一个人被压缩成一行数据。八秒后出双语片名：

> **《一个 C 的漫长一年》**
> **THE LONG YEAR OF ONE C**

中文旁白草案：

> 上一次，我们看见一份考核怎样追着一个官员走。
> 这一次，我们跟着他多走一年，看看一个档位怎样长出经理、名额、项目，以及下一轮。

英文次字幕：

> Last time, one rating followed an official.
> This time, we stay for the managers, openings, projects, and the next cycle it creates.

证据边界：开场卡只负责立题，不证明任何 gameplay capability；最终姓名、档位和肖像必须由真实素材决定。

### 02｜00:35–01:45　两本账：他做了什么，与组织需要什么

类型：`ck3_clean_span`
章节 ID：`phase2_fact_quota_calibration`
producer key：`facts-quota-calibration`

画面编排：先以较长停留展示事实档与配额档确实分开；轻推至主角所在行。校准前保留 revision/榜单状态，再展示身份明确的校准事件与动作后的修订变化。不要用快切遮掉关键数字。

中文旁白草案：

> 先别急着替他喊冤。事实档记录他做了什么，配额档记录组织今天需要多少个好结果。
> 校准落笔之后，榜单和查询修订号必须一起变化。否则我们看到的只是一次点击，不是一次决定。

英文次字幕：

> Facts record what he did; quota grades record what the organization needs today.
> After calibration, the board and observed revision must change together.

必须拍到：事实档/配额档为不同可读记录；校准事件 identity-ready；动作后 scoreboard/query revision 变化。

不能声称：仅因 handler/schema 存在就证明校准债跨周期延续；不能替主角解释未被显示的评分原因。

### 03｜01:45–02:40　案卷：按钮过去了，记录没有

类型：`ck3_clean_span`
章节 ID：`phase2_receipt_appeal_pip`
producer key：`receipts-appeals-pip`

画面编排：从人物脸部切到告身/回执，画面上短暂框出 owner、subject、cycle、case 四个身份位。展示 PIP 回应界面、选择动作及之后的 selected response state；回避把一次特定结果剪成“所有申诉都会成功”。

中文旁白草案：

> 他可以认下，也可以回应。但申诉和 PIP 不是按完按钮就算翻案。
> 上司、当事人、周期和案件都还是同一份，所选结果真正落到账里，这一步才结束。

英文次字幕：

> He may accept or respond, but an appeal is not proven by its button.
> The same owner, subject, cycle, and case must reach the selected state.

必须拍到：正式告身/PIP surface；同一四元身份贯穿；provider-observed selected response state。

不能声称：所有申诉成功；未验证的跨周期 PIP 持久化；按钮 ACK 等于结果。

### 04｜02:40–03:35　经理也有经理

类型：`ck3_clean_span`
章节 ID：`phase2_manager_governance`
producer key：`manager-governance`

画面编排：第一次主动离开主角。先把他的经理放在画面权力位置，再展示经理自己的正式治理事件；等待 AI-owned case 到达可观察的业务终态。末尾切回主角肖像，但不宣称经理案卷已经改变了他的档位。

中文旁白草案：

> 给他落笔的人，也活在另一张考核表里。
> 经理会留下自己的案卷；真实事件抵达业务终态，连责才算发生。组织最公平的地方，大概是每个人都有上司。

英文次字幕：

> The person rating him lives inside another review.
> Manager accountability counts only when the real case reaches a business terminal.

必须拍到：真实 manager-governance 事件 identity-ready；AI-owned case provider-observed terminal business state。

不能声称：事件定义本身证明经理连责 live；经过时间或 ACK 就等于业务终态；经理案卷与主角档位存在未证明的直接因果。

### 05｜03:35–04:35　晋升不是一句“以后再说”

类型：`ck3_clean_span`
章节 ID：`phase2_promotion_compensation`
producer key：`promotion-compensation`

画面编排：把晋升选择与薪酬回执做成同一案件的视觉对照。先拍选择，不立刻庆祝；等正式结果出现后，再用 lower-third 标识 frozen case identity 一致。若真实路径是失败或保留，按实际结果写旁白，不剪成成功。

中文旁白草案：

> 好评也不能拿一句“组织会看见你”结账。
> 晋升选择与薪酬回执留在同一个冻结案卷里，机会才从口号变成一项可追踪的结果。

英文次字幕：

> A good rating cannot be settled with “the organization sees you.”
> The choice and compensation receipt must remain in one frozen case.

必须拍到：真实 promotion choice 与 compensation result event；两者绑定同一 frozen case。

不能声称：预留晋升包保证成功；没有同案实机证据时宣称职级和薪酬已兑现。

### 06｜04:35–05:30　没有位置，也是位置的答案

类型：`ck3_clean_span`
章节 ID：`phase2_hc_workforce`
producer key：`hc-workforce`

画面编排：使用 hash-identical checkpoint 展示 A/B/C 三条 workforce 结果，每条都保留足够时间让观众看清同一 owner/subject。用三联画或连续回放表达“同一个人面对三种制度选择”，但屏幕必须明确这是同一检查点的分支证明，不是假装它们按时间先后都发生过。

中文旁白草案：

> 他可以准备好，组织却未必准备好一把椅子。
> HC 让继任与流动受真实名额约束。没有编制也是一个完整结果，不是系统忘了做下一页。

英文次字幕：

> He may be ready while the organization has no chair ready for him.
> Headcount constrains succession and mobility; no opening is a real outcome.

必须拍到：A/B/C 从 hash-identical checkpoint 出发；同一 owner/subject case；no-opening outcome 明确可见。

不能声称：三个分支在同一历史中连续发生；fixture checkpoint 等价于真实 managed span；所有 workforce 情形都已穷尽。

### 07｜05:30–06:30　功劳需要一个签名

类型：`ck3_clean_span`
章节 ID：`phase2_projects_metrics`
producer key：`projects-metrics`

画面编排：从主角和同侪同屏开始，展示 identity-ready project-choice event；动作后等待贡献/指标 result event。数字变化可以放大，但不得加动画伪造不存在的项目关系图。

中文旁白草案：

> 项目结束，不等于功劳自动找到了主人。
> 选择必须离开按钮，贡献与指标必须出现在身份明确的正式结果里。否则所谓抢功，只是一句很像大厂的旁白。

英文次字幕：

> A finished project does not make credit find its owner.
> Contribution and metrics must appear on identity-ready result events, not stop at an ACK.

必须拍到：真实 project-choice event；identity-ready contribution/metrics result；动作之后的 provider observation。

不能声称：静态 handler 已证明贡献归属 live；未出现的重组、抢功或项目结果已被覆盖；相邻人物一定参与同一项目。

### 08｜06:30–07:30　事故会等到考核结束吗

类型：`ck3_clean_span`
章节 ID：`phase2_incidents_operations`
producer key：`incidents-operations`

画面编排：节奏突然加快，但 X/Y/Z 三个正式 surface 都至少完整停留一次。每次动作后留出状态观察，不用按钮点击声冒充完成。最终 closure 出现后安静两秒，让“结案”和“没有事故”形成反差。

中文旁白草案：

> 就在大家讨论他的潜力时，事故开始按自己的节奏工作。
> X、Y、Z 三个阶段和最终结案，都要由后续真实状态作证。命令回执最多证明有人点过，不能证明问题已经消失。

英文次字幕：

> While everyone reviews his potential, the incident keeps its own schedule.
> X, Y, Z, and closure need later real-state proof; an ACK proves only that someone clicked.

必须拍到：X/Y/Z surface 按序可见；每次 transition 与 closure 均在动作后由 provider observation 证明。

不能声称：脚本定义已证明运营债 live；ACK 证明转换或结案；主角本人制造或解决了事故，除非画面身份明确支持。

### 09｜07:30–08:45　下一轮：人可以调走，账不会

类型：`ck3_clean_span`
章节 ID：`phase2_cross_cycle_endgame`
producer key：`cross-cycle-endgame`

画面编排：回到主角，从本轮案卷缓慢溶解到下一周期界面。展示 terminal institutional event，并把其 carried debt/default-change cycle identity 作为屏幕证据。最后一次看到主角时，不给他胜利或失败特写，而让榜单覆盖人物界面的一部分。

中文旁白草案：

> 他可以换岗位，经理可以换名字，本轮也可以改掉明天的默认规则。
> 但昨天的制度债仍要偿还。终局不是重置按钮，只是组织翻到了下一页。

英文次字幕：

> He may move, managers may change, and this cycle may alter tomorrow's default.
> Yesterday's debt remains. The endgame turns the page; it does not reset the ledger.

必须拍到：terminal institutional event identity-ready；事件绑定 carried debt/default-change cycle。

不能声称：尚未通过实机 span 的跨周期债已 production-live；终局清空所有制度状态；调任一定发生在主角身上，除非画面支持。

### 10｜08:45–09:30　结尾：他离开镜头，案卷留在桌上

类型：`generated_card`
章节 ID：`phase2_finale`

画面编排：主角肖像淡出，留下冻结案卷、榜单和制度债的三个视觉符号；最后生成双语证据卡，列出实际入片的八个 span，不写“全部能力完成”。片名回扣后静默半秒结束。

中文旁白草案：

> 一期结束时，一个官员背了 C。
> 二期结束时，他终于看见：榜单、案卷与制度债，会把每个人的选择带进下一轮。
> 旅人，人会调任，账不会。组织会记得，也会等你回来解释。

英文次字幕：

> Phase one ended with one official carrying the C.
> Phase two reveals the boards, cases, and debt carrying everyone's choices forward.
> Traveler, people transfer. The ledger does not.

结尾主标题：

> **人会调任，账不会**
> **PEOPLE TRANSFER. THE LEDGER REMAINS.**

证据边界：生成卡不是 gameplay 证明；只有八段均通过、两轮 1× 审阅、媒体/声明审计、导出与明确发布收据全部闭合后，才能在交付记录中写 release-ready/exported/published。成片内不使用“组织能力建设完成”。

## 视觉语法

### 人物连续性

- 主角每次重返画面都使用同一构图方向和同一 lower-third 色条，让观众立即认出他。
- 组织介入时，画面从人物肖像向榜单、案卷或事件窗移动；下一章回人时采用反向移动。
- 片中最多三次使用“人物 → 一行数据”的 match cut，分别落在校准、晋升/HC、跨周期。重复过多会把制度压力拍成模板动画。

### 信息层级

1. 第一层：真实 CK3 产品 surface，保持可读；
2. 第二层：中文主字幕，不遮挡人物名、事件选项和关键数字；
3. 第三层：较小英文副字幕；
4. 证据标记：只在必要处短暂显示 `same case`、`post-state observed` 等，不把宣传片剪成测试报告。

不使用伪造鼠标轨迹、假事件框、补画数字或 AI 生成的 CK3 截图。生成视觉仅限明确可识别的章节卡、片名卡和结尾证据卡。

## 声音设计

- 开场只有翻页、印章和低频环境声；主角名字出现后才进入音乐。
- 校准/案卷段用稳定节拍，像会议室时钟；晋升处不提前进入胜利音乐。
- HC 三分支用同一短乐句的三种结尾，帮助观众理解“同一检查点的不同结果”。
- 事故段提高节奏，但每个 provider-observed state 出现时短暂抽掉鼓点，给观众阅读时间。
- 终局逐层拿掉音乐，只留下翻页声；最后“账不会”之后留半秒静默。
- UI 点击声只作为动作反馈，绝不承担“结果已经发生”的叙事功能。

## 剪辑与审阅清单

第一次 1× 素材审阅后：

1. 确认主角真实身份与可见范围；把无法支持同一人物的章改为“与此同时”，不换一名长得相近的角色冒充。
2. 按 `phase2-authoring-claims.json` 逐章核对 required visible observations；缺一项就删除对应句子或整段，不用旁白补证据。
3. 确认八个 producer key 顺序完整，begin/end、source hash、postcondition 与有效 intake 报告一致。
4. 确认 A/B/C 是同检查点分支表达，不被剪成一条时间线。
5. 完整检查测试 UI、fixture 字样、生成角色、Launcher/loading、Toast 遮挡和字幕安全区。
6. 将中文旁白按实际画面压缩；英文只做忠实次层，不添加中文没有的更强结论。

最终 1× 成片审阅后：

1. 观众能否在前三十五秒认出主角和问题；
2. 每次离开主角是否都有明确的“组织层”理由；
3. 有没有相邻剪辑制造未被同案证据支持的因果；
4. 关键身份、数字和结果 surface 是否至少完整可读一次；
5. 中文是否是主视觉层，英文是否没有挤出安全区；
6. 片尾是否诚实列出实际入片证据，且没有 `complete`、`live-proven`、`published` 等越界措辞。

## 与制度群像版的独立交付边界

人物版的价值是代入感：让观众记住“这个人怎样被一套制度追着走”。制度群像版的价值是结构感：让观众看见“不同人如何共同生产一个组织结果”。两版可以共享经哈希绑定的 clean source spans，但必须拥有：

- 独立项目配置/剪辑时间线；
- 独立旁白与双语字幕；
- 独立候选文件和 SHA-256；
- 独立的两轮 1× 人工审阅与 sign-off；
- 独立导出记录；若发布到外部平台，还要各自对应明确的发布回执。

共享素材不等于共享结论。任何一版通过都不能替另一版自动签核。
