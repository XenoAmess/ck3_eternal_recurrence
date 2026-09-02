# 《一个 C 是怎样被生产出来的》二期导演处理稿

状态：**director treatment / 非 live / 非 builder input**。

本文只冻结二期宣传片的叙事、镜头与声音方向，不授权录制、TTS、字幕渲染、合成、发布，也不改变
`phase2-promo-project.json`、authoring ledger、八段 capture contract 或任何 readiness 结论。正式台词和入片主张仍须由同一
GREEN 实录、逐段可见观测、provider postcondition、claims audit 与两轮 1× 人审共同决定。

## 核心命题

一期的主角是一个官员：他怎样拿到 3.25、背上一个 C。

二期的主角是制度：事实怎样被切成配额，配额怎样经校准变成结果，结果怎样重新分配晋升、薪酬、HC 与项目，最后又怎样以
事故、债和默认规则的形式留到下一轮。

片名提问：**一个 C 是怎样被生产出来的？**

结尾回答：

> 一期结束时，一个官员背了 C。二期结束时，没人能说这个 C 只是他的问题。
>
> 人会调任，账不会。

这不是“幕后阴谋揭露”，也不是一个角色的逆袭故事。镜头观察的是多人组织网络中的记录、选择、责任与后果。不同 span
可能属于不同人物、不同案卷或不同周期；每次跨案件、跨角色、跨周期都必须在画面上明示，不能用蒙太奇伪造成同一条游戏内
因果链。

## 成片尺度

- 预计时长：**8–12 分钟**；导演目标约 `9:40`，硬上限仍为 `<20:00`。
- 后台结构：保留 `10` 个 canonical authoring chapters，即开场/结尾两张 generated card，加 `8` 个真实 gameplay spans。
- 前台结构：重剪为三幕八场。观众不需要看到“章节 1–10”的并列讲解感。
- 语言层级：简体中文为主叙事和主要视觉层级；英文为同步副字幕，不套用月报视频的 English-primary 规则。
- 配音：`zh-CN-XiaoxiaoNeural`。语气是冷静、礼貌、略带荒诞的企业培训，不煽情、不咆哮，也不替画面宣布尚未证明的结论。

## 三幕节奏

| 幕 | 约时长 | 戏剧任务 | 观众带走的问题 |
|---|---:|---|---|
| 第一幕：制造结果 | `00:00–03:00` | 事实、配额、校准与经理案卷把“表现”加工成可发布的组织结果 | 这个 C 是谁算出来、谁改过、谁签下来的？ |
| 第二幕：重新分配组织 | `03:00–06:40` | 结果进入晋升、薪酬、HC、项目、贡献和指标；申诉/PIP 只作 20 秒回扣 | 一个结果怎样改变人、钱、名额和机会？ |
| 第三幕：制度形成记忆 | `06:40–09:40` | 事故 X/Y/Z、跨周期债和默认规则把一次结果带进未来 | 人走以后，什么还留在系统里？ |

幕与幕之间用“账的形态”转场：榜单行 → 案卷号 → 薪酬/名额 → 项目结果 → 事故状态 → 下一周期默认规则。只有真实画面
能证明同一 identity 时才做连续动作匹配；否则使用短卡明确写 `另一案卷 / ANOTHER CASE`、`另一角色 / ANOTHER OFFICIAL` 或
`下一周期 / NEXT CYCLE`。

## 三幕八场

### 第一幕：制造结果

#### 场 1｜事实不是配额（`00:00–01:20`）

- canonical span：`phase2_fact_quota_calibration`
- producer：`facts-quota-calibration`
- 开场：第一秒直接进入可读的事实档/配额档或校准产品面，不出现 Launcher、主菜单或 loading。
- 镜头问题：同一份工作，为什么会有两本账？
- 可用证据：事实档与配额档在真实产品面上可区分；校准事件 identity-ready；校准后榜单/query revision 发生 provider-observed
  变化。
- 镜头设计：先给事实与配额两栏各一次完整停留，再切校准选择，最后回到 revision/榜单。数字至少保持两秒，不用快速推拉掩盖
  UI。
- 旁白语气锚点：“事实负责发生，配额负责解释。校准负责让两者在会上达成一致。”
- 不可推断：revision 变化不能单独证明“校准债已持久化”，也不能把任何未入镜的债务字段说成既成事实。

#### 场 2｜谁在案卷上签字（`01:20–02:10`）

- canonical span：`phase2_manager_governance`
- producer：`manager-governance`
- 镜头问题：结果发布以后，经理是否也会留下自己的案卷？
- 可用证据：真实 manager-governance 事件可见且 identity-ready；AI-owned case 抵达 provider-observed terminal business state。
- 镜头设计：从榜单的“上司/经理”字段做视觉匹配，切到另一份明确编号的经理案卷；角标必须说明是否换了角色或案件。
- 旁白语气锚点：“经理当然也有经理。组织结构的优点，是每个人都能在另一张表里成为被解释的对象。”
- 不可推断：不能用等待时间或 command ACK 代替业务终态；若画面没有明确上司关系，只能说“经理案卷进入终态”，不能说
  “上司已经反评了他”。这里的“上司反评”指经理受到其上级评价，绝不解释为下属反向给上司打分。

#### 场 3｜申诉只改哪一本账（`02:10–03:00`）

- canonical span：`phase2_receipt_appeal_pip`
- producer：`receipts-appeals-pip`
- 镜头问题：结果有异议时，系统究竟追踪的是按钮，还是同一份案卷？
- 可用证据：真实告身/PIP response surface 可见；owner、subject、cycle、case identity 在回应过程保持一致；selected response state
  在动作后被 provider 观察到。
- 镜头设计：完整展示一次案卷 identity 与回应结果；不要在第一幕展开一期式申诉教程。保留信息，快速收束。
- 旁白语气锚点：“申诉可以重开案件，不能让案件从未发生。系统最擅长的，不是忘记，而是留下更完整的记录。”
- 不可推断：不得声称跨周期持久化，除非同一 case 的后续周期证据真实出现；不得把按钮点击当作改判或退款完成。

### 第二幕：重新分配组织

#### 场 4｜晋升不是一句话（`03:00–04:05`）

- canonical span：`phase2_promotion_compensation`
- producer：`promotion-compensation`
- 镜头问题：一个结果怎样进入职位和钱？
- 可用证据：真实晋升选择与薪酬结果事件都可见；promotion choice 与 compensation receipt 绑定同一 frozen case。
- 镜头设计：选择前给案卷号，选择后给薪酬回执；用相同 identity 位置做 match cut。若 identity 不同，禁止剪成一次连续操作。
- 旁白语气锚点：“晋升不是祝贺，是一份带回执的资源重排。没有同一案卷，承诺就还没有落账。”
- 不可推断：一条成功分支不能同时证明失败分支的 reservation release，也不能外推未入镜的长期薪酬影响。

#### 场 5｜没有 HC 也是结果（`04:05–05:10`）

- canonical span：`phase2_hc_workforce`
- producer：`hc-workforce`
- 镜头问题：组织如何把“人”变成名额与分支？
- 可用证据：A/B/C workforce outcomes 来自 hash-identical checkpoint，使用相同 owner/subject case；无 opening 的结果必须可见。
- 镜头设计：三分支用同构构图，不用“前后连续”语言；画面角标固定写 `同一检查点的分支比较 / BRANCH COMPARISON FROM ONE
  CHECKPOINT`。
- 旁白语气锚点：“没有 HC，不是页面加载失败。它是系统认真计算以后，决定让你继续提高人效。”
- 不可推断：A/B/C 是分支对照，不是同一时间线连续发生；无 opening 必须由可见结果证明，不能从缺少页面反推。

#### 场 6｜项目把结果分给更多人（`05:10–06:40`）

- canonical span：`phase2_projects_metrics`
- producer：`projects-metrics`
- 镜头问题：个人结果怎样进入项目、贡献与指标？
- 可用证据：真实 project-choice 与 contribution/metrics result 事件可见且 identity-ready；结果在动作后由 provider 观察到。
- 镜头设计：先显示选择对象和参与者，再显示贡献/指标结果；构图从一人案卷扩展到多人名单，让“制度成为主角”在视觉上成立。
- 申诉/PIP 回扣：本场中段最多 `20s`，只复现“记录可重开，但必须绑定同一案卷”的母题，不重新讲操作流程，也不暗示场 3 的
  case 与本场 project case 相同。
- 旁白语气锚点：“到项目里，一个人的 C 开始拥有更多共同作者。贡献被记录，指标被发布，责任则等待下一张表。”
- 不可推断：不得宣称独立项目仲裁、完整抢功裁决、重组或共享官署已经完成；command ACK 不证明贡献/指标结果。

### 第三幕：制度形成记忆

#### 场 7｜事故不是一个按钮（`06:40–08:00`）

- canonical span：`phase2_incidents_operations`
- producer：`incidents-operations`
- 镜头问题：组织结果进入运行以后，错误怎样变成可追踪状态？
- 可用证据：真实 X、Y、Z incident surfaces 按序可见；每次 transition 与 final closure 都由动作后的 provider 状态证明。
- 镜头设计：X/Y/Z 各留一个可读全屏节点，以状态和 identity 连续性形成节奏；不能用音效、闪白或旁白跨过缺失阶段。
- 旁白语气锚点：“事故处理不是按过按钮。X、Y、Z 都要留下状态，结案也要有人在系统里看见。”
- 不可推断：任一 transition 或 closure 都不能从 ACK 推断；若缺一个可见阶段，整场降级或删除，不能用 generated card 补成 live。

#### 场 8｜下一轮先继承上一轮的账（`08:00–09:20`）

- canonical span：`phase2_cross_cycle_endgame`
- producer：`cross-cycle-endgame`
- 镜头问题：人可以调任，制度记忆怎样跨过周期边界？
- 可用证据：terminal institutional event 可见且 identity-ready；它与 carried debt/default-change cycle 保持绑定。
- 镜头设计：明确显示 `下一周期 / NEXT CYCLE`，将 carried debt、默认规则与终局事件放在同一证据节奏中。可回切场 2 的经理案卷作为
  主题押韵，但必须标 `Earlier case`，不得冒充同一 case 的新增后果。
- “上司反评”回环：只有当场 2 真实画面明确显示经理及其上司评价关系时，结尾才可短回放“评人的人也在别人的表里”；否则沿用
  更窄的“经理案卷也会进入终态”。
- 旁白语气锚点：“默认规则可以改，旧债不会因此礼貌地消失。人会调任，账不会。”
- 不可推断：终局不是 reset；不能声称所有债都已清偿、所有默认规则都已永久改变，或八段属于同一人物/同一案卷。

`09:20–09:40` 使用 `phase2_finale` generated card 收尾。卡片不是 gameplay evidence，只承担结论：

> 一期结束时，一个官员背了 C。二期结束时，没人能说这个 C 只是他的问题。

英文副字幕建议保持克制：

> Season one ended with one official carrying a C. Season two ends with no one able to call it his problem alone.
>
> People transfer. The ledger remains.

## 后台十章 / 八段证据映射

| 后台 chapter | 前台位置 | canonical producer/evidence | 剪辑角色 |
|---|---|---|---|
| `phase2_minimal_recap` | 冷开场，约 10–15s | future generated card；不证明玩法 | 从一期“个人背 C”提出二期问题 |
| `phase2_fact_quota_calibration` | 场 1 | `facts-quota-calibration` | 事实、配额、校准制造结果 |
| `phase2_receipt_appeal_pip` | 场 3；场 6 最多 20s 回扣 | `receipts-appeals-pip` | 案卷 identity 与回应状态 |
| `phase2_manager_governance` | 场 2；场 8 条件式回环 | `manager-governance` | 经理也进入组织案卷 |
| `phase2_promotion_compensation` | 场 4 | `promotion-compensation` | 结果进入职位与薪酬 |
| `phase2_hc_workforce` | 场 5 | `hc-workforce` | 结果进入名额与人员分支 |
| `phase2_projects_metrics` | 场 6 | `projects-metrics` | 结果扩散到项目、贡献、指标 |
| `phase2_incidents_operations` | 场 7 | `incidents-operations` | 结果成为运行状态与事故链 |
| `phase2_cross_cycle_endgame` | 场 8 | `cross-cycle-endgame` | 债与默认规则跨周期留下记忆 |
| `phase2_finale` | 尾卡，约 20s | future generated card；不证明玩法 | 回答片名，落到“人会调任，账不会” |

前台重排不改变 canonical capture 顺序，也不改变每个 span 的 postcondition。复现或回切镜头仍引用原 span 的同一字节、时间码与
证据等级，不能制造第九段“推论镜头”。

## Shot 与画面规则

- 组织网络优先：多用名单、榜单、案卷、关系字段、项目参与者、状态流和周期卡；少用英雄式人物特写。
- 真实历史角色仍是唯一可入片人物。每个可见角色按 provenance 标注 history ID、显示名和其在当前案件中的 role；不使用测试角色或
  世界生成坊正姓名。
- 跨角色/案件/周期必须显式角标；未证明 continuity 时默认“不连续”。蒙太奇只表达主题类比，不表达游戏内因果。
- UI 数字、案卷 identity、revision、结果状态至少停留两秒。观众读不清的证据不靠旁白补成“已看到”。
- 不裁切、遮罩或重绘 fixture/test UI；含 `ZGA`、验收决议、debug/fixture 文本、Launcher/loading 的 take 直接排除。
- generated card 只用于冷开场、幕间提示和结尾，不替代八段 gameplay evidence；卡片若承载边界说明，明确标
  `GENERATED EVIDENCE/BOUNDARY`。
- 节奏由“记录出现—选择发生—状态确认”驱动。禁止用过密闪切把动作 ACK 和后置状态拼成未经证实的成功。

## Audio 与旁白规则

- Xiaoxiao 保持培训师式冷静：语速稳定、停顿精准，笑点来自礼貌措辞与残酷组织逻辑的落差，不靠夸张情绪。
- 每个关键 UI 出现前后留 `0.4–0.8s` 呼吸；identity、金额、名次、名额、X/Y/Z 状态与周期变化不被旁白压住。
- CK3 原声仅用于建立真实操作感；不添加“成功提示音”来代替 provider-observed postcondition。
- 三幕声音递进：第一幕是单据与会议的克制节奏；第二幕增加多人/资源切换；第三幕减少音乐密度，让事故状态和结尾句更冷。
- 不合成角色对白，不伪造会议录音，不用音效暗示画面外发生了晋升、退款、结案或跨周期清偿。

## 双语字幕规则

- 简体中文在上位主要视觉层级，英文为较小的同步副字幕；每个 cue 同时出现，时间边界一致。
- 中文按句意与编辑行断句，英文按对应语义分行；先保留 authoring ledger 的显式 editorial newline，再在各行内按真实字体宽度自动
  换行。
- 两种语言各自最多两行并保持 1920×1080 safe area；不得为了塞入一句话缩到不可读，也不得让英文抢占中文证据区域。
- `ANOTHER CASE`、`ANOTHER OFFICIAL`、`NEXT CYCLE` 等连续性角标必须中英双语并与相关镜头同时可见。
- 最终字幕仍需成片抽帧和两轮 1× 人审；本 treatment 中的语气锚点不是已批准的 release cue。

## 不可宣称边界

- 不得称二期 live、complete、release-ready、exported 或 published；本文只是导演处理稿。
- 不得声称八段来自同一个人物、同一个案卷或一条连续因果链，除非真实 capture identity 明确证明。
- 不得把 ACK、按钮出现、经过时间、schema、fixture、静态测试或 generated card 当作业务后置状态。
- 不得把“上司反评”宣传成下属给上司评分；只能呈现已证实的经理被其上级纳入考核案卷。
- 不得把事实/配额 revision 外推为持久校准债，把一次 PIP 回应外推为跨周期结果，或把一个晋升分支外推为全部薪酬/释放语义。
- 不得把 HC、项目、贡献、指标、事故或制度终局包装成超出现有可见 surface 与 provider postcondition 的独立完整系统。
- 不得用旧一期镜头、fixture、假视频、生成插画或边界卡冒充二期新增 gameplay。
- 不得因叙事更流畅而隐藏失败 take、跨案件标识、证据等级或仍为 pending 的 footage/publish gates。

## 进入制作前的导演门

只有在真实八段 footage 到齐后，导演与 claims reviewer 才逐场决定“保留、收窄或删除”。每场至少核对：canonical span、producer
key、可见 surface、identity、postcondition、原始字节哈希、clean-frame gates 与跨案件标识。任何场次若无法支撑 treatment
中的因果措辞，就改写措辞；不得先保留结论再寻找能圆上的镜头。

正式制作的第一步仍是 fresh fetch/fast-forward 独立宣传工具，验证 clean 且 `HEAD == origin/main`，再生成新的 environment receipt。
本文件不会替任何 footage、media、review、export 或 publish gate 开绿灯。
