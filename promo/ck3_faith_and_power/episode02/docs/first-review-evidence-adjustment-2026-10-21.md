# 二期首版证据补充：显示费用对照与独立领袖案例

版本：`first-review-evidence-v1`。状态：**Root已整合并自审通过，纳入C16冻结范围。本轮R26预启动已真实闭场；新拍摄须使用C16实际来源绑定和新的准入。新增拍摄结果仍待实证。**

`machine_id: 4-8e1c2f1861`；本条来源读取时间`2026-10-21T02:16:39.057951+00:00`。目标仍是七章连续、约30分钟的第一可审阅版。这里区分首版可说的事实和仍缺的研究／实拍，不将原生工程目标改写成已经实现。本文仅版本化补充[导演案](director-plan.md)的H1—H3编排；原Native、caller、资格器、共享validator及旧结果不变。

## H1：同母档的显示费用对照

R24／R25均从B36新共同母档独立冷恢复，存档SHA-256为`bf894cd4fe458094a703e219085679e286803cb3a3df1554cc150338709abdb0`，大小69,030,071 B，人物31254、日期原值53144328。两场来源在各自prepared-case及[共同母档原件](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b36-h-demote-prep-a01/live/4-8e1c2f1861--faith-engine--R0023/case-output/new-common-mother.json)中绑定；不是旧R16与R21拼接出的对照。

| 首版使用的事实 | 实际证据 | 仍不能推断的结论 |
|---|---|---|
| 普通状态的建制报价为300虔诚、225金币 | R24两次明确fresh Native query，采集序号11208、69568；[单臂结果及两个原query引用](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b37-h-ordinary-a01/live/4-8e1c2f1861--faith-engine--R0024/case-output/new-mother-h1-arm-result.json) | 报价不等于已付款或已建制；不拿它代替后续独立H2场的当前报价 |
| 主要臂已合法将纳杰夫32升格，本信仰主要数2→3 | Root在01:39:36Z审过原图及原生许可；[独立升格后态](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b38-h-major-a01/live/4-8e1c2f1861--faith-engine--R0025/case-output/new-mother-promotion-independent-post.json)确认32关联false→true、升格前十资源报价为0、独立钱包已观测金币／威望／虔诚扣款均0 | 升格免费不等于创建领袖免费；不把升格报价的十资源零向量当作建制报价 |
| 升格后的创建领袖窗口显示200虔诚、150金币 | R25原片实际PTS70.067秒的原始点帧，费用文字未被公国tooltip遮挡；[01:56:10Z有限媒体审阅](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b38-h-major-a01/observer-qa-a01/RESULT.actual.json)包含精确图像／原片pin | 只是两项GUI显示值，不证明完整十资源报价、当前CanConfirm、已建制或实际付款；未签整段连续clean |

首版可说：**“普通状态报价是300虔诚、225金币；升格后的窗口显示200虔诚、150金币。两项显示数字分别少100和75。”** 必须紧接说明主要臂的完整原生建制报价未核实。不能改说“已经省下100虔诚、75金币”“已经按这个价格付款”或“四份Native报价都通过”。未知资源项、确认许可和真实成交仍是未知，不按GUI补齐。

R25在01:40:28Z的[020原query](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b38-h-major-a01/live/4-8e1c2f1861--faith-engine--R0025/case-output/h1-promote-020.actual-results.json)返回`selected_terms.available=false`，原因`selected_terms_nonempty_parameters_not_yet_qualified`，`named_parameter_count=3`、采集序号32437，Can／cost／resource quote均null。这是提供方读取范围未覆盖，不是游戏拒绝或资金不足。主要臂两份可用Native建制报价尚未取得，**原四份Native报价闭环仍为`NOT_COMPLETE`**。

[R25执行原件](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b38-h-major-a01/live/4-8e1c2f1861--faith-engine--R0025/case-output/new-mother-execution-result.json)保持PARTIAL、30次公共调用、一次升格且结果已独立确认、HOF提交0、H3 null、`business_pass=false`。[R24闭场](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b37-h-ordinary-a01/SCENE-CLOSURE.actual.json)于01:24:19Z、[R25闭场](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b38-h-major-a01/SCENE-CLOSURE.actual.json)于01:43:32Z均为正常，原`native_business_pass=false`仍保留。首版使用混合证据不追认原生或业务通过。

## H2／H3：改用独立Parent冷恢复，不接成R25后续

后续采用现成`tools/ck3_mod_acceptance_cases/faith_e02_r19_ghw_adapter.py`的`faith-engine-e02-r19-hof-ghw-combined-v1`。从原Parent存档独立冷恢复：SHA-256 `de0f97b142ea88f13797d2f025380a52c5bab396b3d4986b8be6bf3ef653cc07`、大小69,030,069 B、人物31254、日期原值53144328。Parent与H1新母档是两份不同输入；片中明确标注“独立建制案例”，不用R24的报价替代当次观察，也不剪成R25升格后直接建制。

拍摄沿现有combined caller：核当场身份、无领袖和once账本 → 原版stock1默认参数入口第一份fresh报价 → Root亲审本场原图和第一份完整原生报价，批准最多一次Create → 再核身份、钱包并取得第二份独立fresh报价，按既有`verify_quote_pair`合同严格核对 → 最多一次canonical HoF Confirm → 独立钱包、头衔、持有人及Faith／Rite后态 → 按原生实际显示的第一选项处理事件并保存独立消失后验 → 同一建制世界两次独立H3只读。第二份不一致或不可用即保留真实拒绝／未知，不提交、不自动重试；不虚构第二次Root截图审核。这里的stock1是既有默认参数入口，不是“仅一处主要圣地”的数量声明；所有新报价、确认、付款、收件人及H3结果均待实机。

H2必须以实际头衔和持有人读回证明创建，不能用ACK或窗口关闭代替。H3保留解锁标记、等待、对象与实际决议行的读取范围；缺席、false与不可用分开，真实unknown如实呈现，不为首版制造正向许可。该场禁止GHW launch和战争提交，执行上限均为0；本文不批准发动战争。

R25实际没有HOF提交；本条读取时Parent的canonical HOF claim不存在，具体路径与观察时间写入外置来源清单。这不是未来永久未消费的保证。若新H2实际消费Parent once账本，后续v1 H1 caller必须显式reconciliation后再评估；不得删claim、重置提交标记或换标签绕过一次性限制，未知提交结果不重放。

## 首版还缺什么

| 项目 | 首版前仍需取得或整合 | 研究边界 |
|---|---|---|
| H1显示对照 | 选定普通Native与主要GUI原件并在版本化作者输入中逐项绑定，字幕披露读取失败 | 主要臂多参数完整Native报价仍未闭合，独立列为研究缺口；不阻止按本文限定展示两项费用 |
| H2／H3 | C16整合和Root自审后，取得新独立场的当次报价、一次创建及头衔／持有人／钱包后态，再做两次H3只读 | 未实拍项保持pending；最终发动许可可以真实unknown，不能省略实际读取 |
| 遗物与A2 | B31的R26在游戏启动前失败并真实闭场；新版两臂在C16冻结后继续，结果待各自原件和作者接入；A2合同由独立任务审读 | 本补充不猜A2输入，也不把H1例外推广成其他原生资格通过 |
| 完整首版 | 合入实际旁白、字幕、图像与结果来源，完整时间轴测量后生成本地MP4供审阅 | 约30分钟仍是成片目标，不能用已配音长度或单场录像长度宣布完整影片完成 |

原导演案和B24模板的“四份原生报价”目标继续保留其未完成状态。本文不改Native／caller／qualifier／共享validator，也不把GUI值填进Native DTO。作者若采用此首版范围，须另存版本化事实与诊断unknown的来源选择，保留原失败及原24槽身份；在实际作者消费者接收前，不预写槽已闭合。Root自审核对了实际caller的审核与双报价顺序，并亲审R25费用原始点帧；实际提交和来源绑定回执另存C16记录，之后才拍新增H2／H3。
