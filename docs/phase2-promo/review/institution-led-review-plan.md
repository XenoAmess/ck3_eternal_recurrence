# 制度群像版：未来审片与声明审计包

状态：**template-only / pending media / 非回执 / 非批准 / 非签名**。

本文件为 `institution-led` 成片预先冻结审片顺序、逐项检查与 claims-to-shot 映射。它不表示素材已拍摄、候选片已生成、
审阅已发生、审计已通过或发布已完成；本目录中的两个 JSON 也只是空白 checklist，不能放进 completion attestation 的
`reviews` 字段冒充 `zg361_phase2_1x_review_receipt`。

最终候选文件名固定为：

`zhongguo-361-phase2-institution-led.mp4`

正式 run artifact ID 固定为 `zhongguo-361-phase2-institution-led-video`，默认 run ID 为
`phase2-institution-led-candidate`。候选应位于独立 institution work directory 的
`deliverable/zhongguo-361-phase2-institution-led.mp4`；不得与人物版共用 candidate、run manifest、审阅回执、signoff、
export bundle 或 publication receipt。

## 本模板依据

| 权威输入 | 当前模板绑定 | 用途 |
|---|---|---|
| `../phase2-institution-director-treatment.md` | SHA-256 `D9EA9CB3804C11FA4877B7444BB66D1CD3F3A9C047AE0E340F4E76C957AD97B8` | 三幕八场、声音、字幕、连续性和不可宣称边界 |
| `../../../mod_zhongguo_style/promo/phase2-promo-institution-project.json` | SHA-256 `77537A37D2D1B3E00F38120667491F8CF7047E999DFEEF640DCB8D4343524C7E` | 十个后台 chapter 与最终片名 |
| `../../../mod_zhongguo_style/promo/phase2-authoring-institution-claims.json` | SHA-256 `ED634490A66773C10B82DD144C782B02A32538D11D7CE23D13B75F0C0760ADCD` | institution 专属 cue、字幕和卡片覆盖层 |
| `../../../mod_zhongguo_style/promo/phase2-authoring-claims.json` | SHA-256 `9AD63985561C4BF08BBCCE7B7676579C71C0953C7BEF718E56BE45C2C722B11B` | 八段共享 footage binding、可见观测、postcondition 与 cannot-claim |
| promo tool `claims-review-v1.schema.json` | 工具 commit `57c42fca13ea459432c1caf76e069a1fbccf602c`；schema SHA-256 `3847162765650F46E4FFF4D0689646ED9D2330883F186CEECF39C84DBDAE8A7B` | 两份 checklist 的当前结构 |

这些 SHA 只绑定本模板读取过的权威输入，不是未来媒体、审阅回执或人工签名。任一权威输入变化时，先重做本映射并更新模板；
正式制作前仍必须按总合同 fresh fetch/fast-forward 宣传工具，再以更新后的工具/schema 复核 checklist。

## 必须晚绑定的字段

媒体尚未存在，因此现在不得填写下列字段：

- candidate absolute path、bytes、SHA-256、bound ffprobe envelope 与 run manifest；
- 八个 canonical source spans 的绝对路径、bytes、SHA-256、时间码、session/PID/generation/revision、checkpoint/save 与 cleanup receipts；
- claims bundle/evidence bundle/automated audit 的路径、bytes、SHA-256 或状态；
- 两轮 checklist 的 canonical `checklist_sha256`；
- reviewer、reviewed_at、逐项结果、decision、review receipt SHA-256 与人工 signoff；
- export bundle/manifest、发布目标、账号、凭据引用、远端 locator 与 publication receipt。

真实媒体到位后，先复制相应 `.template.json` 到新的 attempt 目录，再把 `deliverable: null` 替换为工具生成的真实 artifact binding。
由工具对完整 checklist 规范化并得到 `checklist_sha256`；审阅者实际看完后才写 response。任何改变候选字节、checklist 项目或顺序的
修改都使旧 response 失效。

## Claims-to-shot 映射

后台 canonical capture 顺序仍是 `事实/配额 → 告身/PIP → 经理 → 晋升/薪酬 → HC → 项目/指标 → 事故 → 跨周期`。
制度版前台允许把经理场放在告身/PIP 场之前，但这只是剪辑重排。跨人物、案件或周期时必须出现双语角标；不得把重排解释成一条
连续的游戏内因果链。

| claim/chapter | 前台 shot 与来源 | 必须在画面中看见 | 审阅时必须拒绝的偷换 |
|---|---|---|---|
| `phase2_minimal_recap` | 冷开场 generated card | 中英标题清晰；明确是叙事提问，不是 gameplay evidence | 用一期素材、生成卡或旁白冒充二期实机证据 |
| `phase2_fact_quota_calibration` | 场 1；span `phase2_fact_quota_calibration`；producer `facts-quota-calibration` | 真实产品面上的事实档与配额档可区分；校准事件 identity-ready；动作后榜单/query revision 可见变化 | 由 schema、ACK 或单独 revision 推断持久化校准债 |
| `phase2_manager_governance` | 场 2；span `phase2_manager_governance`；producer `manager-governance` | 真实经理治理事件 identity-ready；AI-owned case 达到 provider-observed terminal business state | 用等待时间或 ACK 代替终态；把“上司反评”说成下属给上司打分 |
| `phase2_receipt_appeal_pip` | 场 3，场 6 最多 20 秒回扣；span `phase2_receipt_appeal_pip`；producer `receipts-appeals-pip` | 真实告身/PIP surface；owner/subject/cycle/case 在回应中一致；所选状态由 provider 在动作后观察到 | 把按钮点击说成改判/退款完成；无同案证据却宣称跨周期持续 |
| `phase2_promotion_compensation` | 场 4；span `phase2_promotion_compensation`；producer `promotion-compensation` | 真实晋升选择和薪酬结果事件；两者绑定同一 frozen case | 一条成功分支证明全部失败/释放/长期薪酬语义 |
| `phase2_hc_workforce` | 场 5；span `phase2_hc_workforce`；producer `hc-workforce` | A/B/C 使用同一 owner/subject case，来自 hash-identical checkpoint；no-opening 结果可见 | 把三分支剪成同一时间线；以页面缺失反推 no-opening；以 fixture 替代 managed span |
| `phase2_projects_metrics` | 场 6；span `phase2_projects_metrics`；producer `projects-metrics` | 真实 project-choice 与 contribution/metrics result 事件 identity-ready；结果由 provider 在动作后观察到 | 由 ACK 推断贡献结果；外推未入镜的仲裁、抢功、重组或共享官署 |
| `phase2_incidents_operations` | 场 7；span `phase2_incidents_operations`；producer `incidents-operations` | X/Y/Z surface 依序可见；每个 transition 及 closure 都有动作后的 provider state | 用音效、闪切、旁白或 ACK 跨过缺失阶段 |
| `phase2_cross_cycle_endgame` | 场 8；span `phase2_cross_cycle_endgame`；producer `cross-cycle-endgame` | terminal institutional event identity-ready，并绑定 carried debt/default-change cycle；`NEXT CYCLE` 连续性角标可读 | 把终局说成 reset/清债；把早先经理镜头伪装成同案新增后果 |
| `phase2_finale` | 尾卡 generated card | 两版语言同步可读；结论落在“人会调任，账不会”；证据卡只列真实入片 spans 和诚实边界 | 写 `COMPLETE`、release-ready、exported 或 published；让卡片补足缺失 live evidence |

所有 live shot 还必须共同满足：只出现 provenance-bound 真实历史角色；无测试/fixture/debug/Launcher/loading UI；不靠 crop、mask、
blur 或重绘隐藏污染；关键 identity、数值、状态至少可读两秒；跨案/跨人/跨周期标识不能被字幕或 lower-third 挡住。

## 两轮完整 1× 审阅

两轮都必须播放**同一份最终候选 MP4 的完整时长**，从第一帧到最后一帧，速度恰好 `1.0x`，不跳过、不拖动、不倍速。
抽帧 package 只用于定位 chapter 边界，不能替代连续播放。两轮由两名不同的具名审阅者完成；第二轮不能复用第一轮 reviewer。

### 第一轮：claims-and-source-pass

使用 `institution-led-claims-and-source-checklist.template.json`。审阅者将最终候选逐镜头反查到八个 canonical source spans，核对：

1. candidate、source span、intake/timeline/evidence index 和 claims audit 都绑定真实字节；
2. 十章齐全，八段 gameplay 各有可读 surface、identity 与 provider-observed postcondition；
3. 前台重排、回切和蒙太奇没有制造跨案、跨人、跨周期因果；
4. 每一句旁白/字幕都由对应镜头支持，所有 cannot-claim 均未进入成片；
5. 五项 CK3 内容声明全部满足：`historical_characters_only`、`no_generated_official_name_visible`、
   `fixture_test_ui_absent`、`full_clip_reviewed`、`no_crop_mask_or_redaction`；
6. 图片、声音、双语字幕连续、同步、清晰，首尾和全部 chapter 边界正常。

任一 required 项失败即 `rejected`。修复后生成新字节、新 attempt、新 checklist hash，并从头完整重审。

### 第二轮：final-candidate-pass

使用 `institution-led-final-candidate-checklist.template.json`。另一名审阅者在第一轮问题已关闭后独立完整观看相同候选，核对：

1. basename、artifact ID、run ID、candidate bytes/SHA 与第一轮、claims audit、bound probe、run manifest 完全一致；
2. H.264/yuv420p、1920×1080、AAC 48 kHz stereo、正时长且短于 1,200 秒；
3. 中文为主视觉，英文为同步副字幕；两种语言各最多两行，按句意断句，均在 safe area 内；
4. institution-led 的组织群像逻辑成立，没有滑回“单一官员完整逆袭”的人物版，也没有用叙事流畅掩盖证据边界；
5. 全片无黑帧、冻帧、音画错位、爆音、字幕截断、坏转场、污染 UI、错误首帧或尾帧；
6. 结尾与证据卡不宣称尚未完成的 live、export 或 publication 状态。

同样，任一 required 项失败即 `rejected`，保留失败 artifact 和证据，另起 attempt。

## 从模板到可验收回执

两份 checklist 是 promo tool 的 `xar-promo-review-checklist`，不是 completion gate 所需的项目回执。完成实际观看后，应依次形成：

1. 工具生成的 pending review package 与 hash-bound checklist/response；
2. 对同一候选的 `xar_promo_audit_report`，其 automated audit 通过且 manual signoff 读取真实已批准记录；
3. 两份独立 `zg361_phase2_1x_review_receipt`：scope 分别为 `claims-and-source-pass` 与
   `final-candidate-pass`，包含真实 `attempt_id`、`playback_speed: 1`、`full_duration_reviewed: true`、具名 reviewer、带时区时间、
   candidate bytes/SHA 和 claims-audit SHA；
4. run manifest 中对 artifact `zhongguo-361-phase2-institution-led-video` 的真实 approved signoff；
5. completion attestation 只引用这些已经存在且 byte-bound 的文件。

自动化不得预填 reviewer、时间、决定、逐项通过、签名或 GREEN。第一轮通过也不替代第二轮，任一版本的回执也不得替另一版本开门。

