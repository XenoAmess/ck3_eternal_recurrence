# 天朝二期人物线版：未来审阅与审计包

状态：**仅为待绑定模板 / 非审核回执 / 非 sign-off / 非放行证据**。

本包对应 `character-led` 独立成片，最终文件名固定为
`zhongguo-361-phase2-character-led.mp4`。它把人物版导演稿、人物版项目配置、人物版
authoring overlay、共享八段素材合同和宣传工具的现行审阅格式接在一起；目前没有真实素材、候选成片、
审核人、审核时间、决定、签名、字节数或成片 SHA-256 被填入。

## 权威输入

| 角色 | 路径 | 本模板编写时的真实 SHA-256 |
|---|---|---|
| 人物版导演稿 | `docs/phase2-promo/phase2-character-director-treatment.md` | `B573A1A0A09FC532D9190ED765222943E95948D833666B898A5AD32F5BE9A44B` |
| 人物版项目配置 | `mod_zhongguo_style/promo/phase2-promo-character-project.json` | `963735C8D32725A83D4A764CFD92D3C85519500C44FB2D71823F51992DB7042F` |
| 人物版 authoring overlay | `mod_zhongguo_style/promo/phase2-authoring-character-claims.json` | `16FFAB1415D33CCDE02685AD97AC51A65960DE5D0EC73EB013AADAB174EEBF71` |
| 八段共享 claim matrix | `mod_zhongguo_style/promo/phase2-authoring-claims.json` | `9AD63985561C4BF08BBCCE7B7676579C71C0953C7BEF718E56BE45C2C722B11B` |

审阅模板遵循宣传工具 `claims-review-v1` 的 `xar-promo-review-checklist` 结构。本模板编写时读取的工具
checkout 为 `57c42fca13ea459432c1caf76e069a1fbccf602c`，本地 `HEAD == origin/main`；schema 文件 SHA-256 为
`3847162765650F46E4FFF4D0689646ED9D2330883F186CEECF39C84DBDAE8A7B`。这只是格式来源记录，**不替代正式
制片前要求的 fresh fetch / fast-forward / clean / `HEAD == origin/main` 验证**。

## 待真实产物生成后绑定的字段

不得用占位哈希、零哈希或假签名补齐以下字段。真实字节存在后，另存一份实例，不覆盖本模板：

1. 第一轮：八段 source clip 的路径、字节数、SHA-256、artifact ID、capture/intake report 与 SHA-256，
   canonical seed/save lineage、逐段 session/PID/generation/revision、source commit、CK3 EXE、mod mount、
   postcondition 和 cleanup receipt；再把这些精确绑定汇总为 source-review manifest artifact。
2. 第二轮：候选成片路径、artifact ID、字节数与 SHA-256，storyboard、bound ffprobe、review-package、
   抽帧和命令审计目录各自的路径与 SHA-256，以及使用的项目配置、overlay 和宣传工具精确版本。
3. 每一轮真人看完以后：该轮规范化 checklist 的 `checklist_sha256`、审核人、带时区时间、逐项结果、
   总决定和备注。审核 response 必须另写，模板本身始终保持 `template_only=true`、`is_signoff=false`。
4. 最终 sign-off：仅在两轮均对同一条素材链和最终 MP4 精确字节完成真人审阅后，通过宣传工具的
   `signoff` 独立记录；任何自动审计 GREEN、抽帧成功或 pending review package 都不能代填批准。

## 两轮 1× 审阅

### 第一轮：八段原始素材审阅

使用 `character-led-source-review-checklist.template.json` 生成一份新的、已经填入精确 source-review
manifest 绑定的 checklist。审核人必须把最终会入片的每条 live clip 从第一帧到最后一帧以 `1.0x`
完整播放，不跳看、不拖动、不倍速；静帧只能辅助定位，不能代替连续观看。

本轮决定每句人物线旁白是“保留、收窄还是删除”，并检查人物身份、同案连续性及下表中的可见事实。
某段不能证明仍是同一人物亲历时，只能改写为“与此同时 / 在同一套制度里”，不得靠相邻剪辑补成因果。

### 第二轮：最终人物线成片审阅

候选 MP4 生成后，先保留为新的 artifact，生成 bound ffprobe、storyboard 和独立 review package，再从
`character-led-final-review-checklist.template.json` 实例化 checklist。审核人必须对精确 MP4 字节从头到尾
以 `1.0x` 连续观看，覆盖十章、所有转场、字幕、声音和首尾帧。

若任一必选项失败，决定必须是 `rejected`，保留原字节及回执，修正后输出新 artifact、使用新目录并完整重审。
第一轮通过不能替代第二轮；制度群像版的任何审核也不能替人物版签核。

## Claims-to-shot 映射

| Canonical span / producer key | 人物版镜头必须明确拍到 | 允许的准确结论 | 禁止靠剪辑补出的结论 |
|---|---|---|---|
| `phase2_fact_quota_calibration` / `facts-quota-calibration` | 事实档与配额档分别可读；校准事件身份明确；动作后榜单/查询 revision 变化 | 该真实案卷在校准后出现可观测修订 | schema/handler 存在就等于 live；未展示的跨周期校准债 |
| `phase2_receipt_appeal_pip` / `receipts-appeals-pip` | 正式告身/PIP surface；owner、subject、cycle、case 四元组贯穿；所选状态由 provider 在动作后观测 | 同一案卷确实抵达画面展示的 response state | 所有申诉都会成功；未验证的 PIP 跨周期持续性 |
| `phase2_manager_governance` / `manager-governance` | 真实 manager-governance 事件身份明确；AI-owned case 达到 provider-observed 业务终态 | 该经理案件抵达所示终态 | ACK 或等待时间等于连责；经理案必然直接改变主角评级 |
| `phase2_promotion_compensation` / `promotion-compensation` | 晋升选择与薪酬结果事件均可见，并绑定同一个 frozen case | 同一冻结案卷留下了画面所示选择和回执 | 预留名额保证晋升；没有同案证据便宣称职级/薪酬已兑现 |
| `phase2_hc_workforce` / `hc-workforce` | A/B/C 从 hash-identical checkpoint 出发；owner/subject 相同；no-opening 明确可见 | 同一检查点存在三种受编制约束的分支结果 | 三个分支按时间连续发生；fixture 等于正式 live；已经穷尽全部情形 |
| `phase2_projects_metrics` / `projects-metrics` | project-choice 事件身份明确；贡献/指标 result event 可见；动作后 provider observation | 画面中的项目选择产生了所示贡献/指标结果 | 静态 handler 已证明归属 live；相邻人物必然参与同一项目 |
| `phase2_incidents_operations` / `incidents-operations` | X/Y/Z surface 按序可见；每次转换与 closure 均由动作后的 provider state 证明 | 该事故链按画面所示走到结案 | ACK 就是转换/结案；主角制造或解决事故（除非身份画面明确支持） |
| `phase2_cross_cycle_endgame` / `cross-cycle-endgame` | terminal institutional event 身份明确；与 carried debt/default-change cycle 保持绑定 | 画面所示制度债进入对应下一周期 | 跨周期债在未过 span 前已 production-live；终局清空全部状态；主角必然调任 |

开场卡 `phase2_minimal_recap` 和结尾卡 `phase2_finale` 不承担 gameplay 证明。结尾证据卡只列最终真正入片且
已过第一轮的 spans，不写 `complete`、`live-proven`、`exported` 或 `published` 等超出回执范围的词。

## 自动审计与真人判断的分工

自动审计应检查精确字节绑定、文件哈希、storyboard 时间范围、bound ffprobe、媒体规格、十章完整性、八个
producer key 的 reference closure、配置/overlay/tool 版本和输出 basename。它只能报告自动检查结果，并保持
`manual_approval_granted=false`。

真人审阅负责判断角色是否可辨认、具体机制是否真的可见、字幕与声音是否可读、人物线是否伪造了同一人物或
同一案件因果，以及成片是否达到发布质量。机器通过不能替代真人决定；真人批准也不能修复自动审计失败。

最终候选路径必须以 `deliverable/zhongguo-361-phase2-character-led.mp4` 结尾。外部发布仍需独立 publication
receipt；本包不会上传、发布或授权购买。

