# R355：重复辩论投递与同 PID 热恢复

## 结论

R355 在 `date_raw=53236224` 遇到本时间线第 4 次原版
`debate_event.5110`。事件仍为精确的 7-scope regular variant、native options
`(0, 1)`，玩家为 `32904`，且尚未选择按钮；唯一 RED 是旧合同
`max_occurrences=3`。

原版 `debate_events.txt` 的 “Should only fire once” 位于单场 debate activity
的结束投递逻辑内，限制的是每场活动一次，不是整局或 5,000 日产品观察窗只能
投递一次。R285、R327 与 R355 已累计证明同一受限产品时间线可由不同活动合法
投递至少四次。继续把实见次数逐次写成全局上限只会制造 harness RED，不提供
额外的事件身份保护。

合同因此改为
`occurrence_policy=repeatable-within-product-observation-window`：

- 不再对该事件施加按实见次数增长的全局 occurrence cap；
- 每次投递仍完整核验 event key、root、日期观察窗、所有 scope 名称/类型/别名、
  option 投影及 event-instance-advanced 后置条件；
- 仍固定选择确认计算胜者的 authored option 2 / native option 1；
- 总推进仍受 `MAX_ADVANCE_DAYS=5000` 与 absolute end date 约束。

## 同 PID park

R355 的临时 source-capture owner 在合同异常处先复核 paused/map/event instance，
再进入 Python 热恢复控制台，没有退出 supervisor：

- CK3 PID：`69176`
- connection generation：`1`
- event instance：`356`
- park artifact：
  `Z:\ck3_mod_rewrite\_runtime\p2r355endgamesource\contract-red-hot-park.json`
- park SHA-256：
  `BA3906CB618569ECE4BCCD20B3C5416ED82FC9DE238EDC1C456FC206B5CEAA41`
- `safe_paused_event_unchanged=true`
- `selection_attempted=false`

外部合同提交后只 reload Python 合同/production-entry 模块并从该事件继续；不因
runner-only 修复重启 CK3。若 paused frame、PID/connection 或 event instance 已
变化，则此路径拒绝热续。

## 静态回归

- occurrence-policy 精确测试：normal `1/1`、`python -O` `1/1` GREEN。
- manager-recovery 合同组：normal `41/41`、`python -O` `41/41` GREEN
  （各含 1 个环境条件 skip）。
- promotion source checkpoint runner：normal `83/83`、`python -O`
  `83/83` GREEN。

最终 live continuation、source registry 与 cleanup 字段将在同一 R355 会话完成后
补入本页。

## 同会话第二次合同 RED：查找秘密兜底

热恢复越过辩论事件后，同一 CK3 PID、connection generation 和暂停恢复链在
`date_raw=53239344` 遇到 `spymaster_task.0359` 的下一次精确投递。旧合同仅因
此前 R201 实见两次而设置 `max_occurrences=2`，因此在选择按钮前以
`known-interrupt-occurrence-bound` 保留 RED。

CK3 1.19.0.6 原版 `councillor_on_actions.txt` 将 `.0359` 放在
`task_find_secrets_reveal_selection` 的 `first_valid` 末位：每当一次 Find Secrets
任务发现的秘密没有更具体事件可用时，它都会作为兜底重新投递。事件定义的唯一
option 只对本次 `secret_to_reveal` 执行 `reveal_to = root`，不存在整局两次上限。

因此该合同同样改为
`occurrence_policy=repeatable-within-product-observation-window`。这不放宽任何
事件形状或选择条件：完整十 scope、角色别名/互异关系、root、唯一 native option
与 event-instance-advanced 后置条件仍逐次验证；总运行仍受 5,000 日产品观察窗
限制。该修复属于外部 Python 合同变更，将继续在 PID `69176` 上热重载，不重启
CK3。

## 同会话第三次合同 RED：预兆回复投影

第二次热恢复继续前进后，PID `69176` 在 `date_raw=53243544`、event instance
`364` 暂停于 `ep3_emperor_yearly.2211`。MCP 的 exact current-event 查询确认：

- root / liege：`32904`；动态 vassal：`30987`；
- scope 名称和类型仍精确为 `potential_title/liege/vassal`；
- 本次实际显示 native options `(1, 3)`，即原版 B/C；
- 既有 R250 投影为 `(1, 2, 3)`，即 B/D/C；
- 选择尚未发生，C 仍为 native 3 / authored 4 的最小副作用终止路线。

原版 A、B、D 分别带互有关联的性格/迷信条件，D 还可由请求附庸与玩家的信仰
差异显示；C 无 trigger、始终可见。因此合同只增加源码允许且实机冻结的第二种
精确投影 `(1, 3)`，不接受任意子集。`.2210` 位于 administrative yearly 池，
25 年 cooldown 属于发起请求的附庸；不同附庸仍可在同一产品观察窗向玩家发送
`.2211`，所以 occurrence 也改为按产品时间窗可重复。此处不新增通用宗教观测或
策略，只消费原生已计算的选项投影。

该变更仍只涉及外部 Python 合同和测试；保留同一 paused event，提交后热重载，
不重启 CK3。

## 同会话第四次合同 RED：年度总览跨域栈

第三次热恢复越过原版预兆回复后，同一 PID 在 `date_raw=53247792`、event
instance `366` 暂停于产品年度总览 `zg361.1`。MCP 查询证明 root 为 `32904`、
唯一 authored/native option 均为 `0`，事件尚未选择；旧合同唯一失败项是
`saved_scope_names_exact`。

本次 64-scope 集合与既有 R288 full cross-domain 精确集合相比，唯一增量为
`zg361_pp_prompt_owner/subject/cycle/case/state/mechanism` 六字段，类型分别为两个
character 和四个 value。这是年度发布事件在晋升提示调用栈尚未退栈时合法继承的
外层 scope；`zg361.1` 自身仍只复制四个已发布计数，唯一确认 option 没有 effect。

合同只加入这一组精确名称集合及六个可选类型检查，不接受任意组合。由于该事件
由每轮年度考核发布触发，occurrence 同样按 5,000 日产品观察窗可重复，每次仍
核验完整 scope 集合和唯一按钮。修复仍只在外部 Python 合同层，继续热重载当前
暂停实例，不重启 CK3。

## 同会话第五次合同 RED：年度淘汰动态主体

年度总览确认后，同一 PID 在 `date_raw=53247816`、event instance `367` 进入
`zg361.5`。MCP 查询确认 root `32904`、三个 authored/native options `(0,1,2)`
完整且尚未选择。事件源码表明 immediate 仅新增 `zg361_n_elim`，其余均为外层
状态；实际新栈等于既有 R293 cross-domain 集合加六个 `zg361_pp_prompt_*`
字段，并只保留 `zg361_n_elim` 一个本事件计数。

旧 R293 variant 把当时的 CH-D/CP-E/P3 subject `26505` 与 cross reviewer
`27448` 冻结成跨周期身份。本次实机证明四条当前 subject 链一致为 `30938`，
cross reviewer 合法变化为 `27928`；B1 reopen、PIP/notice 与 compensation 仍各自
保持独立且内部一致的主体。新 R355 variant 因此精确绑定完整 61-scope 名称集，
用 alias equality、与 root 互异及 reviewer/subject 互异来验证动态身份，而不接受
任意字段或任意角色。年度淘汰每轮都可能发生，合同 occurrence 也改为在产品观察
窗内可重复。

该修复不改变 mod 文件或 CK3 内存，只更新外部验证合同；当前事件继续同 PID 热
恢复。

## 同会话第六次合同 RED：勾引成功被领主发现

第五次热恢复后，PID `69176` 在 `date_raw=53248656`、event instance `401`
暂停于原版 `seduce_outcome.3901`。MCP 查询确认 root / `target_liege` 均为玩家
`32904`，动态 `owner=31496`、`target=37337`，唯一显示按钮为 authored 1 /
native 0，且选择尚未发生。完整 scope 栈共 11 项；其中 immediate 创建的
`dummy_servant_gender` 类型为 character，但 native bridge 不提供该临时 dummy
的稳定角色 ID，因此合同精确要求其 typed identity 为 unavailable，而不是把它
误当作任意普通角色。

原版 `seduce_outcome.2900` 在成功勾引被发现后，把 `.3901` 投递给目标的领主；
`.3901` 的唯一 option 对本次 `target` 执行
`seduce_outcome_success_discovered_effect`，没有无副作用替代路线。合同因此只接受
本次精确 root、11-scope 名称/类型/人物关系和唯一 native option。不同勾引计划
可分别产生该通知，所以 occurrence 按有绝对 5,000 日上限的产品观察窗可重复，
而非按当前实见次数设置整局上限。

该改动仍仅涉及 CK3 进程外的 Python 合同、测试与文档。事件保持暂停，提交后
热重载同一进程并继续，不重启 CK3。

## 同会话第七次合同 RED：部院预算请愿分支

勾引发现事件热通过后，同一 PID 在 `date_raw=53248848`、event instance `408`
暂停于 `tgp_decision_events.0101`。本帧 root、`hegemon` 与
`petition_recipient` 均为玩家 `32904`，动态 `petitioner=29346`；完整 scope
集合是 `petitioner/actors_movement/hegemon/petition_recipient/`
`increase_budget_ministry`，三个 authored/native options 均为 `(0,1,2)`，尚未
选择。旧合同只枚举了法律、考试和省制分支，因而把这个原版预算分支误报为漂移。

CK3 1.19.0.6 的 movement-petition decision view 明确定义三个预算选择值
`increase_budget_salary/ministry/military` 与两个退休法选择值
`increase/decrease_retirement_law`；它们进入 `.0101` 时都继承同一种五-scope
紧凑形状。修复只把这五个源码枚举值加入精确 `scope_variants`，仍固定选择拒绝
请愿的 authored 3 / native 2，避免应用请求或打开还价链。独立角色可以重复发起
请愿，原版没有整段产品时间线两次上限，因此 occurrence 改为受绝对产品观察窗
约束的可重复；每次 event/root/scope/options 和选择后实例推进仍逐项检查。

这里同样没有修改 CK3 已加载内容；提交后继续热重载 PID `69176`。

## 同会话第八次合同 RED：洪水河流区域 scope

预算请愿热通过后，PID `69176` 在 `date_raw=53254632`、event instance `498`
暂停于第二次 `natural_disaster.8001`。root、`ruler`、
`disaster_province_ruler` 均为玩家 `32904`，唯一 authored/native option 为
`1/0`，尚未选择。与 R247 八-scope 帧相比，本次完整集合只多
`river_region: geographical_region`，其余类型和身份完全一致。

原版 `natural_disaster_save_base_scopes_effect` 明确对
`scope:situation.var:river_region` 使用条件式 `save_scope_as=river_region`：洪水
situation 保存该字段，非河流灾害不保存。因此合同新增且只新增精确的九-scope
洪水 variant，八-scope 旧形状继续保留；缺字段、多字段或错误类型仍 fail-closed。
`.8001` 是玩家加入每个独立灾害 warning phase 时的通知，原版没有整局一次上限，
故 occurrence 改为受 5,000 日产品观察窗约束的可重复。唯一按钮仍只调用
`natural_disaster_warning_tooltip_effect`。

修复只改进程外合同、测试与文档，当前 CK3 实例继续热加载，不重启。

## 同会话第九次合同 RED：洪水预警脉冲

九-scope `.8001` 热通过后，同一灾害在 `date_raw=53255112`、event instance
`499` 投递 `natural_disaster.7021`。实帧 root 为玩家 `32904`，完整 scope 为
`situation/situation_sub_region/epicenter_county/river_region`；snapshot 有三个
authored slot，实际显示 native `(0,2)`，选择尚未发生。

原版 `natural_disaster_warning_events` 明确把 `.7021` 列为四种等权 warning
事件之一。native 0 会增加压力并启用 manage-from-home 权力分享，native 1 会打开
隔离家族决议；本帧 native 1 因 trigger 不满足而隐藏。native 2 只显示灾害提示，
事件共用 after 随后记录已收到首次警告。因此最小合同精确选择 authored 3 /
native 2，并绑定完整四-scope 和稀疏 option 投影。不同灾害 situation 可再次选择
该 warning，occurrence 只受产品观察窗限制。

该修复仍不触碰 CK3 已加载文件；完成静态验证与推送后在 PID `69176` 上热续。
