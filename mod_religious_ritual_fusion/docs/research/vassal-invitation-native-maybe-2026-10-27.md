# 原版 Rite 邀请的 Maybe 发送阈值

- `machine_id: 4-8e1c2f1861`
- 原始源码基线：`7b671baf21af26a096dd86a34a67503c49b65426`。
- 本机静态读取与回执复核：2026-10-27 UTC；逐项实际时间、文件 Pin、EXE 字节 Pin 见下述诊断包。
- 状态：已修改共享脚本与现有 Java 回归，尚未执行本次 Maven、测试或修复后的实机验证。本文不授予新的 live PASS。

## 真实断点与证据边界

RRF 结果页的邀请按钮调用 `rrf_invite_vassals_gui`，进入 `rrf_invite_previewed_vassals_effect`。该效果消费已显示的预览快照，逐人重新检查原生资格，并在 `run_interaction` 前记录 `rrf_vassal_invited`。结果检查把尚未处于结果 Rite 的已尝试角色列为 `rrf_vassal_pending`；它并不查询原版互动队列，也不能证明互动已经发送。

同 Faith 的 AI 分支使用原版 `sway_vassal_to_my_rite_interaction`。本机原版 `game/common/character_interactions/pam_interactions.txt:3201` 的定义包含 `special_interaction = rite_conversion`、`ai_maybe = yes`，回复窗口为 1 至 5 日。原来的共享调用仅指定 `execute_threshold = accept`，没有发送阈值。

本机 CK3 `1.20.0.4` 的 EXE 为：

`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/binaries/ck3.exe`

SHA-256：`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。

该 EXE 的 `CRunInteractionEffect` 执行函数为 RVA `0x2D2F420..0x2D2FBE7`（末端不含），完整 span SHA-256 为 `f6ff7f0823ec0dd7050a54e8c4a2ea9513c334edadf5d62eec7fbe2deaf72322`。函数构造并验证原版互动上下文，然后分别检查执行与发送阈值。两阈值默认值均为 3，表示未设置；实际回答为 1、执行阈值为 0、发送阈值为 3 时，既不立即执行也不发送。当前 `run_interaction` 名称字符串 RVA 为 `0x4865F10`；历史研究中的 `0x4864D10` 不能套用于此 EXE。

回答函数 `0x307BD70..0x307C016` 有独立的中间回答分支。其定义字段 `+0x2728` 与源码 `ai_maybe` 的解析绑定未在本次研究中独立闭合；R24 两名角色的实际回答枚举与分数也未被观察。因此，本次证明的是确实存在的阈值无动作路径，不能把它写成 R24/R28 两人未转换的唯一已证原因。

R24 的 `r24-d1-06-invite-once` 于 `2026-10-26T19:29:55.041849Z` 激活 generation 14、widget 20，记录 `dispatch_invoked/native_handled=true`，同时保留 `verification_pending=true`、`postcondition_verified=false`。钱包前后均为 5500。它证明控件回调被调用，未证明某一原版互动已发送、付费、回复或执行。

Root 在 R28 五日后实际读回 45464、45458 仍为 Rite 0/Faith 13，相关七项要求仅 6/7，按 incomplete 正常收口。本专题中的这部分是 Root 提供的实际观察，不能冒充本代理重新调用 Game 得到的结果。

## 最小共享修复

仅在 `common/scripted_effects/rrf_conversion_effects.txt` 的同 Faith AI sway 分支保留：

```text
execute_threshold = accept
send_threshold = maybe
```

接受回答仍可由原版立即执行；Maybe 走原版发送路径，由其真实回复决定结果。人类分支与异 Faith 的 `ask_for_conversion_interaction` 不改。后者的本机原版定义没有 `ai_maybe = yes`，不能仅因结构对称就扩大修复。

本机原版 `game/common/scripted_effects/pam_effects.txt:11645` 的接受效果进入 `puppet_or_actor`，并于 11668 行直接执行 `set_character_rite = scope:puppet_or_actor.rite`。此处没有第二个“五日后转换 Rite”的任务。共享代码不直接设置收件人的 Rite，不强制 Maybe 立即接受，不绕过原版费用、资格和回复，也不重新发送旧的 UNKNOWN 尝试。

## 回归与验收范围

继续使用 `OptionalReformAndConversionTest.java` 的真实生产 Clausewitz AST 解释器。旧模型只有可用、预期接受及“实际转换”布尔输入，会在到达 `run_interaction` 后直接采用转换布尔值，遗漏了执行／发送阈值决策。

本次模型明确区分强类型回答、阈值、调用尝试、立即执行、已发送 offer 和实际回复：

- 从实际生产 AST 中仅移除该 AI sway 的发送阈值，并经序列化往返，重现预览可入选、记录 invited/pending，却没有执行、发送或转换的旧故障路径。
- 实际修复后的生产 AST 在 Maybe 时只发送，保持 pending；明确接受回复后才改变收件人 Rite。未定结果不能自动重试。
- 拒绝回复及实际 Decline 回答不被强制转换；原人类 offer 也必须经明确回复才能转换。
- 现有逐人资格重验、预览快照、异 Faith 路由、源 Rite 保护及新结果重置用例继续保留。

这些是测试边界输入，不是原生回复的替代证据。本次尚未运行测试。后继由统一准入执行完整 RRF Maven verify 与正式 staging 验证，再通过真实 source-freeze、六链资格、runtime 和公共 prepare 进入新实机。成功标准仍是原版实际回复与保存后的逐 ID Rite 后态；预览、控件 ACK、pending 成员和等待五日均不能单独授予转换成功。

## 原始来源

本机原版来源还包括 `game/common/scripted_triggers/pam_scripted_triggers.txt:1948`、`game/common/script_values/pam_values.txt:9563` 与 `game/common/character_interactions/00_religious_interactions.txt:2`。其当前完整文件 SHA 均收录于诊断包。

有界诊断包位于：

`C:/workspace/rrf-development-20261024/review-fixes-a01/ui-and-shared-save-a01/metadata/invite-day5-diagnosis-a01/DELIVERY.candidate.json`

该 delivery 为 2268 B，SHA-256 `f165ec63837dcfc4bc85e89f1a2cb9ed66d0737aea06835f3d17fa04f2b8732f`。它引用完整输入 Pins、当前 EXE 的函数 span 与分支字节，以及 R24 原始回执摘录；它是只读诊断和未执行修复提案，不是测试执行资格。原始大证据按通用存储策略继续做有期限的用途复核，不因本文引用而永久保留。
