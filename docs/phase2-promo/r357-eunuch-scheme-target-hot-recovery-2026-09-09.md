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

## 同会话第四次 RED：秘密事件继承 rival

第三次 `retry` 热加载提交
`11eb3afe5c1052b156dee7ed159d863bc9e1f062` 后，同一 PID `159264` 推进到
下一次 `ep3_story_cycle_admin_eunuch.2051`、event instance `356`、
`date_raw=53233344`。本次完整八项 scope 同时包含 shared story 的
`rival=16834604` 与所选秘密的 `secret_target=35570`；secret owner 为
`31257`。旧合同虽已接受有/无 secret target，却没有建模
`protege/student/rival` 的合法继承，因此只在 scope 名称/数量上 RED，选择仍未
发生。

`.2051` 同样先调用 shared story save effect，再保存必有的 secret owner 与
可选 secret target。合同现以基础六项加
`protege/student/rival/secret_target` 四个有限可选项，展开 16 个精确集合；
rival 存在时仍不得等于玩家或 eunuch。原版没有为 `.2051` 定义整局 occurrence
上限，故不再把单次实见冻结成 `max_occurrences=1`，改由同一个 7190 日产品窗口
限界，每次投递仍执行完整合同和选择后推进检查。

- 第四次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-4.json`；
- park SHA-256：
  `DBBFDC9BCD3E6F19A3BEBAB761F175A17D8E899C9929AF752A0C798FCBC2EE64`；
- 第四次 RED report 快照：11,787,076 bytes，SHA-256
  `D06B0EDE8B730B3B2E15AE7B476D75C582FE429C142CE37513B2C6E842E962C8`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`，不需要重启 CK3。

## 同会话第五次 RED：学生创建的动态 origin owner

第四次 `retry` 热加载提交
`d616ac346e33c33fb3a6c93334b897fc0cc85c6f` 后，同一 PID `159264` 进入
`ep3_story_cycle_admin_eunuch.3001`、event instance `357`、
`date_raw=53233872`。完整八项 scope 中，origin liege 为动态角色 `30921`、
student 为 `33596937`，而旧合同只接受 origin liege 与 eunuch `31801` 同一；
唯一失败项为 `scope:origin_liege:matches_any`，选择尚未发生。

源码确认 `.3001` 先尝试现有 close-family/courtier 学生；只有两者均不存在时，
才在 `scope:eunuch` 内调用 origin helper 并创建新学生。此时 helper 的 fallback
是 eunuch，自身 50% 随机成功分支则是动态相邻顶级领主 realm owner。因此合同
不再冻结 origin liege 的具体 ID，只要求其为非玩家 character；并把
`origin_liege/origin` 建模为成对出现的创建分支，绝不接受只出现其中一个。
`protege/rival` 是 shared story 的独立可选项，连同有/无 origin pair 形成八个
精确名称集合。student 始终为 character、不得等于玩家或 eunuch。

`.3001` immediate 已设置 employer/mentor、增加两点技能并把 student 写回
story；唯一 option 为空确认按钮。本修复没有修改选择路线。

- 第五次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-5.json`；
- park SHA-256：
  `B50BF8C0CAD7CFF175E9FC981065D320CB93079FAC286DB484236A7912090E62`；
- 第五次 RED report 快照：11,866,743 bytes，SHA-256
  `2289414BE7CDA9C2E401AC70B4AF5897E281FB15DA8D81A43F38180DFEB3A8F4`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`，继续同 PID 热重试。

## 同会话第六次 RED：宦官家族成员索要宫廷职位

第五次 `retry` 热加载提交 `217e9468a2abfd57d187c0523574676b3d6d0355` 后，同一 PID
`159264` 推进到 `ep3_story_cycle_admin_eunuch.2061`、event instance `363`、
`date_raw=53239872`。本帧九项 scope 为
`story/emperor/eunuch/admin_title/student/rival/positioner/candidate/liege`；
其中 `positioner=candidate=31440`，`emperor=liege=32904`。旧合同尚未收录该原版
事件，故在选择前 fail-closed。

原版 `.2061` 先调用 shared story save effect，再从宦官近亲中选择没有宫廷职位的
`positioner`，把其雇主改成玩家，并在该角色 scope 中调用
`court_position_generator_effect`。因此 `candidate` 必须与 `positioner` 同一，
`liege` 必须与玩家同一；`protege/student/rival` 来自 shared story，`old_holder`
来自职位生成器，四者均为彼此独立的有限可选 scope。合同以七项基础集合加四项可选
集合展开 16 个精确名称集合，未知超集仍拒绝；若 `old_holder` 存在，则不得与
`candidate` 同一。

native option 0 会正式任命家族成员，并可能撤换旧任；native option 1 拒绝请求、
降低 story 进度，并把该家族成员送回宦官家主宫廷或角色池。合同选择副作用更窄的
native option 1。该原版事件是五年 cooldown，不是整局一次，故 occurrence 采用
`repeatable-within-product-observation-window`。

- 第六次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-6.json`；
- park SHA-256：
  `D6F95C7715FDEFDC31BA5611223441B22946CA91A278DF8D27D81BD3D620A7BB`；
- 第六次 RED report 快照：24,294,999 bytes，SHA-256
  `2FB72391FE930503BD037F3EA2E8E99AD3B6B5835A794E740EA41F72A9E4230E`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`、
  `process_restart_required=false`，允许继续同 PID 热重试；
- manager recovery 分片 normal / `python -O` 各 `45/45`（含一个环境 skip），
  promotion source checkpoint runner normal / `python -O` 各 `83/83` GREEN。

## 同会话第七次 RED：家族争执继承 student

第六次 `retry` 热加载提交 `3cf22a5344e0fab461f04c98959390e9d460917a` 后，同一 PID
`159264` 推进到 `ep3_story_cycle_admin_eunuch.5010`、event instance `364`、
`date_raw=53243880`。本帧六项 scope 为
`story/emperor/eunuch/admin_title/student/rival`。事件、root、两项 native option、
eunuch/rival 关系均通过；旧合同只接受基础五项，因合法继承的 `student` 在名称和数量
检查上 RED，选择仍未发生。

原版 `.5010` 先调用 shared story save effect，故 `protege` 与 `student` 都可能独立
存在；随后从玩家近亲或配偶中重新选择并保存必有的 `rival`，建立其与宦官的 rival
关系并写回 story。因此最小修复只把 `protege/student` 加入有限可选集合，展开四个
精确名称组合，未知超集仍拒绝。原路线继续选择 native option 0：它只添加意见和可能
的 stress，避免 native option 1 额外降低宦官 story。事件原版 cooldown 为五年，
7190 日产品观察窗内可再次发生，occurrence 同步改为窗口内可重复且每次完整验帧。

- 第七次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-7.json`；
- park SHA-256：
  `E452B7ACCFFC205CD618C55D27BEE3FE0EC387871334F609318A887602FE32EB`；
- 第七次 RED report 快照：12,159,332 bytes，SHA-256
  `A4AC597E025DB71FE80E01041C9A9D0BC0EC999CE5B077BF6ADB11E183A9A07C`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`、
  `process_restart_required=false`，继续同 PID 热重试。
