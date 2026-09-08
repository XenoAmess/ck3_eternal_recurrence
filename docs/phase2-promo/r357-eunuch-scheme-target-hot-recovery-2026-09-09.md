# R357：宦官密谋目标变体与同 PID 驻留恢复

## 结论

R357 从冻结 R248 存档和同一 R296 product 自然推进，在 CK3 1.19.0.6
`date_raw=53222808` 暂停于 `ep3_story_cycle_admin_eunuch.2052`、event
instance `345`。玩家/root/emperor 为 `32904`，eunuch 为 `31801`，动态
scheme owner 为 `28315`，scheme target 为 `32364`。两个 native options
仍精确为 `(0, 1)`，选择尚未发生；authored option 2 / native option 1
继续是不暴露该 hostile scheme 的最小副作用终止路线。

旧合同只接受 shared story scope 中存在 `rival`、但所选 scheme 没有目标的
七项帧。本次真实帧相反：没有 `rival`，但有 `scheme_target`，因此仅旧合同的
scope 名称及 rival 必选检查失败。

## 原版定义与最小合同

CK3 1.19.0.6 原版定义给出两个彼此独立的可选来源：

- `ep3_story_cycle_admin_eunuch_save_scopes_effect` 仅在 story 的
  `var:rival` 存在时保存 `rival`；
- `.2052` 选择 hostile scheme 后，固定保存 `scheme` 与 `scheme_owner`，仅在
  `scheme_defender` 存在时保存 `scheme_target`。

合同因此只接受以下四个精确集合：基础六项、基础加 rival、基础加 target、
基础同时加 rival 与 target。`rival` 与 `scheme_target` 都必须是 character；
若存在，二者均不得指向玩家。原版 hostile-scheme trigger 还明确排除 defender
等于 eunuch，所以 target 必须与当前动态 eunuch 互异。原版未在此处证明 target
必须与 scheme owner 互异，合同不额外臆造该关系。

事件、root、日期窗口、owner/eunuch 互异、按钮投影及选择后 event-instance
推进检查均未放宽。

## 同 PID 驻留证据

本轮在启动前把 disposable live wrapper 改成合同 RED 驻留循环。RED 后先通过
MCP 复核 bridge 连接、PID、connection generation、map-ready、paused、event
instance 与 event definition，再接受外部 `retry`；单次 Ctrl+C 会被忽略，
不会进入 cleanup。

- CK3 PID：`159264`；
- connection generation：`1`；
- park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-1.json`；
- park SHA-256：
  `971B82CD7C75D6D64A7E6216AE1DC2E17C4CAEA0995BAB235F07C301B5FE7121`；
- RED report（驻留时快照）：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\report.json`，
  11,533,782 bytes，SHA-256
  `7701B3A512CD1F161B270ADA8A99B6C199B50B6FE52D3684EF23EEC6CF996D2B`；
- `selection_attempted=false`、`process_restart_required=false`、
  `hot_retry_authorized=true`。

静态合同在 normal 与 `python -O` 下验证四个合法组合，并验证 target 指向
玩家或 eunuch 时 fail-closed。提交并推送后在上述同一事件实例上发送 `retry`，
只热加载外部 Python 合同。

## 同会话第二次 RED：宦官索要宫廷职位

第一次 `retry` 已在 PID `159264`、connection generation `1` 上热加载提交
`4f273757d97a1e06ca4bca076ab90456832aafc0`，通过 `.2052` 后自然推进到
`ep3_story_cycle_admin_eunuch.2060`、event instance `346`、
`date_raw=53225016`。本帧仍在同一进程，选择尚未发生；完整六项 scope 为：

`story/emperor/eunuch/admin_title/candidate/liege`

其中 emperor / liege 都是玩家 `32904`，eunuch / candidate 都是 `31801`。
原版 `court_position_generator_effect` 明确把调用者保存为 candidate、把 employer
保存为 liege；shared story effect 的 `protege/student/rival` 各自可选，生成器
找到现任时还会独立保存 `old_holder`。因此新合同把六项设为必选、四项设为有限
可选，展开为 16 个精确名称集合；任何未知额外 scope 仍 fail-closed。

native option 0 会执行 `court_position_generator_assignment_effect`，实际任命
eunuch 并可能罢免 old holder；native option 1 不任命，只执行原版 story
downgrade、意见与 trait-dependent stress。合同选择 native 1，并要求 candidate
与 eunuch 同一、liege 与玩家同一，若有 old holder 则不得与 candidate 同一。

`.2060` 原版 cooldown 是五年，不是整局一次；7190 日产品观察窗可跨越多次
冷却，故 occurrence 使用 `repeatable-within-product-observation-window`，每次
仍重新验证完整帧。

- 第二次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-2.json`；
- park SHA-256：
  `ED2783F1B147F69C45012EB5AB65677907B670BD15913854C24022FA86B9C997`；
- 第二次 RED report 快照：23,058,717 bytes，SHA-256
  `FEE8B6660F0556E647B259A70C2D9D2204BE38C44DC024273A7C2BF82EB64529`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`，同 PID 热重试获准。

## 同会话第三次 RED：动态出身领主

第二次 `retry` 热加载提交
`00569d72652b1d55a31ed2a4356984077139ee21` 后，同一 PID `159264` 推进到
`ep3_story_cycle_admin_eunuch.3010`、event instance `351`、
`date_raw=53228184`。唯一失败项是旧合同把 `origin_liege` 固定为玩家
`32904`，而本帧真实值为 `32922`；其余完整七项 scope、玩家 root、eunuch /
rival 互异和唯一 native option 0 均通过，选择尚未发生。

原版 `ep3_story_cycle_admin_eunuch_save_origin_effect` 有两条明确路线：50%
从相邻顶级领主领地选择 realm owner；未选到时才把当前 root 保存为
`origin_liege`。因此固定玩家 ID 是旧实见值污染，不是原版不变量。当前 native
bridge 没有发布“相邻顶级领主”关系查询，合同能诚实绑定的是 character 类型、
精确名称集合及其余人物关系；不能把不可观测关系伪装成已验证。

同时，shared story effect 可独立保留 `protege/student`。合同现接受基础七项
加这两项的四个精确组合，未知超集仍拒绝。`.3010` 的 immediate 已选择/创建
rival、写入 story 并建立 rivalry；唯一 option 只是 `show_as_tooltip`，因此确认
按钮不增加业务状态。

- 第三次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-3.json`；
- park SHA-256：
  `9F80CB9B6E36ED6F45E07B06BDB109988C49CF4F71990B32862AAE1BD2684AE8`；
- 第三次 RED report 快照：11,632,234 bytes，SHA-256
  `0BCF8FBDF72B5F93D731D21B0FC362FA0C7A6AC8AC612EFCC0ACA1C2223A31F3`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`，继续只做同 PID 热重试。
