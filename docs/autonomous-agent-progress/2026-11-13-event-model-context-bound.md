# Event14 决策请求输入上限修复

实际业务模型请求在 Event14 连续返回 HTTP400。最后一次自然请求的原响应明确给出 `input_tokens` 超限：provider 最大 1048576，prompt 至少 1048577 tokens；这是下界，不是精确 token 数。原请求 4674507B，`max_tokens` 已为256，降低输出不能解决输入越界。Runtime 于20:33:22.4222208Z正常结束原委托，保留同局、keeper、capture1619及C67/pending=null；没有事件控制 INTENT 或新增 SAVE。

具名原请求的字段审计显示 user 内容4236111 UTF8 bytes，其中 history3313981B、root_facts852978B，当前 snapshot39784B、proposal18468B。字段 canonical bytes不是 token 数，也不是原wire跨度。原请求和387B错误正文仍归档；本次没有为诊断重发该旧请求。

`RootOnlineDecisionSelector` 仅对精确的 `select-event-option-N` 前台事件候选建立 `xar.model-event-admission/v1` 任务投影：原 prepared command/id/bodySHA、完整当前 snapshot 未知字段、全部当前 capabilities、routable operations、action facts及选项文本/效果不可用说明保留。仅数组型 native command history 与其他历史集合不发送；这明确不是无损历史压缩或新的动作资格。event、actor、Game、frame、连接、option和原 fallback binding 必须相符；未知 phase 或不满足绑定时 WAIT，不回退大请求。Native freshness、option资格、派发和后验校验不改。

原完整 legacy selector wire 先由原 MaterialSink 归档，投影通过 `original_model_input` ExactRef 指回该原件；随后归档投影。整个最终 UTF8 HTTP wire 上限262144B，包括system消息、JSON字符串转义和外围参数。超界明确 WAIT、零HTTP，不截断当前事实，也不提高provider全局上下文。字节上限不等同精确token预算；实际provider usage仍须独立验收。非事件沿原路。

actual单TU4类首编成功，owner22最终单Test4类首编成功；原三项完整回归首次3P/0FES，21:18:23.283800Z释放。测试用真实公开PlanningRequest/ActionCodec和本机loopback SSE，验证完整原件引用、当前事实不变、坏id/SHA/额外指令拒绝、超界及未知phase零HTTP、非事件旧路。五个event wire为72422–72423B；另一个非事件wire120247B。没有provider HTTP、Game调用、控制派发或实际效果信用。

正式版本只加入相同的三处Source73插入，逆去后逐字恢复规范化旧formal源。正式既有byte equality/history dictionary、known-pending诊断、Life投影及SSE扫描差异保留。测试只把默认fixture路径改成模块内 `src/test/resources/event-model-context73.json`，显式 `event73.fixture` 覆盖仍可用；fixture为实际101045B小上下文，SHA256 `43910f65b1db692796bb9e06296defbf193aec74e83d1d494bdb6974ce5dd88c`，不包含4.67MB旧请求。formal两TU8类独立首编0，同三项回归独立首次3P/0FES，于21:26:40.538350Z释放；不是沿actual结果转授。formal原件为event-context73-formal-compile01及event-context73-formal-whole3-junit01，Jupiter48191B/SHA256 `0f30c0d5d62583c65c02027bf0bdca0b190a62d59f5d065aeffdc63f7d90b635`，输入未变、CLOSE释放。

模型首完整答复200/stop，共153006输入、2399输出tokens、34.174秒；其原稿因peaceful gate与active_event矛盾、失败回退full、缺完整原件引用及绑定而拒绝原样采用，未形成compiler RED。最终只partial借用policy/constants和DTO snapshot/command/final-plan/visits/action-facts构建；owner编写合法event gate、归档引用、完整registry及硬上限/WAIT接线。旧0采用切点保留，不能覆盖此后实际partial。

原件根为 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/life-postcondition-p0-20261112-01/event-model-context-p0-source73`：SOURCE-READY73及SOURCE-READY73-FORMAL、ACTUAL-REQUEST-STRUCTURE73、小fixture与规范化diff。实际生产96260B/SHA256 `f16de4254520c8070beea00737a21ddf8546096ccc65907d160c3acf71ad1988`；正式保差额100823B/SHA256 `2ad98a1c0fc5dbe3bf56979715846efb31546d0cd5c365a92f422b5d89d2b268`。

Native原件根为 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01`：event-context73-compile03、event-context73-test22-compile02、event-context73-test22-whole3-junit01。实际Jupiter46746B/SHA256 `b8b2c1be3c686e63c71e3a9a3cc37a4ebadd4ef3274630b2110cf33d8a811c0c`；POST输入未变、CLOSE释放。compile01/02的包装前置失败均零JVM，原件保留，不称源码RED。薄总件SOURCE73-WHOLE3-STRUCTURE-AND-175JVM-COST01保全部实际耗时与旧准备失败。

源码和软件通过不等于实际P0已解决。Runtime 独占成熟单叶normalfullreload和新鲜事件请求；实际provider200、事件效果、原事件关闭及SAVE各等具名回执。现有类private结构改变，不宣body-only/HCR或新增type能力；不把本地72KB请求等同在线token用量，不授提速或10秒目标。
