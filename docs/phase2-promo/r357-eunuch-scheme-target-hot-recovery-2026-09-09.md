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

## 同会话第八次 RED：傀儡继承人继承完整 story 角色

第七次 `retry` 热加载提交 `980b2d07017afc0fbd551d3ae6366236fbd3ebdc` 后，同一 PID
`159264` 推进到 `ep3_story_cycle_admin_eunuch.5020`、event instance `366`、
`date_raw=53246016`。本帧八项 scope 为
`story/emperor/eunuch/admin_title/student/rival/current_heir/puppet`；失败仍仅为
旧合同把 `rival` 冻结为必有、且没有接收 `student`，选择尚未发生。

原版 `.5020` 的 trigger 明确要求 story 中不存在 `protege` 和既有 `puppet`；因此
shared save effect 在这里不会产生 `protege`，但 `student/rival` 均可独立存在。
immediate 另固定保存当前继承人，并从玩家近亲中选出一个不是当前继承人的 `puppet`，
建立其与宦官的友谊后写回 story。合同据此把六项事件自身 scope 设为必有，把
`student/rival` 设为两个有限可选项，展开四个精确集合；current heir / puppet
互异与非玩家约束保持不变。唯一 native option 会赋予 puppet 修正并提高任命投资，
原版没有无副作用退出路线，故只在完整验帧后确认。

- 第八次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-8.json`；
- park SHA-256：
  `A10E2E0E056DFF0A95EA4A0E9FB1F20530194CA0C05D809508FD863148C6C9A9`；
- 第八次 RED report 快照：12,265,308 bytes，SHA-256
  `58ABE2C984C374003DA85765315BF8848976A95702FC72CBAEF07C7E37B1E808`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`、
  `process_restart_required=false`，继续同 PID 热重试。

## 同会话第九次 RED：诱奸事件的 50% 随机分支未执行

第八次 `retry` 热加载提交 `05707d1b7e70752e5291f6ed4e1e945cff18bff5` 后，同一 PID
`159264` 推进到 `ep3_story_cycle_admin_eunuch.4010`、event instance `368`、
`date_raw=53247768`。本帧八项 scope 为
`story/emperor/eunuch/admin_title/student/rival/spouse/seducer`，角色 ID 分别确认
student `33596937`、rival `16834604`、spouse `32797`、seducer `31440`。
三个 native options `(0,1,2)` 与其余身份检查通过，选择尚未发生。

旧合同来自另一真实帧，冻结了 50% hidden random 执行后的四项：
`had_sex_root_character/had_sex_with_effect_partner/new_memory/secret`。原版定义表明
这个 random 整块可能不执行；执行时 `had_sex_with_effect` 固定把前两项绑定到
seducer/spouse，并生成性交记忆，随后保存 lover secret。当前真实帧正是合法的
未执行分支，不是 CK3 或 MCP 状态损坏。

最小修复保留两种已由原版定义与真实帧闭合的随机分支：四项全无，或四项成组存在；
shared story 的 `protege/student/rival` 仍各自有限可选，共展开 16 个精确名称集合。
为不在分支缺席时削弱旧帧的别名验证，合同检查器新增“可选 character alias”语义：
scope 缺席即通过，存在时必须分别等于 seducer/spouse。原路线继续选择 native option
2，只承担 prestige/stress，避免 native option 0 的 duel 与 native option 1 的三人
监禁和 tyranny。该事件 cooldown 为 15 年，而产品窗约 19.7 年，occurrence 改为
窗口内可重复且每次完整验帧。

- 第九次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-9.json`；
- park SHA-256：
  `15DA239453F987FB898B3C6633CA4E8DD336763BD0857342BE4AD34BE281DBB7`；
- 第九次 RED report 快照：12,364,226 bytes，SHA-256
  `285CAFCD255EDF5FF789DD91E19CD310D4D96B04C7706B38EA409A39035C4B66`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`、
  `process_restart_required=false`，继续同 PID 热重试。

## 同会话第十次 RED：目标角色持有自己的秘密

第九次 `retry` 热加载提交 `fec2e27b3c71ef0f4e79d2a4d1e2691eb894fa2c` 后，同一 PID
`159264` 推进到 `spymaster_task.0359`、event instance `371`、
`date_raw=53254608`。十项 scope 名称、类型、唯一按钮和所有 task alias 均通过；
实际 `target=target_character=secret_holder=29628`，旧合同额外要求 secret holder
与 target 互异，导致两项关系检查 RED。选择尚未发生。

原版 Find Secrets 先在 `target_character` 的本人、廷臣、宾客和直属封臣中汇总可发现
秘密，再直接把被选秘密的 `secret_owner` 保存为 `secret_holder`。因此当目标角色本人
持有被选秘密时，secret holder 与 target 相同完全合法；`.0359` 本身只要求
`secret_to_reveal` 存在，唯一 option 将该秘密揭示给玩家。最小修复删除不存在于原版
定义的 target/secret-holder 互异假设，同时保留 target 与 target_character 同一、
owner/councillor/active_councillor 同一及 spymaster 与另外两方互异。重复事件的窗口
策略和唯一确认按钮不变。

- 第十次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-10.json`；
- park SHA-256：
  `BCB20CF842FD4C621B1D8F6609D1D341AE3BEA0C1E2479511385C0944A525AAC`；
- 第十次 RED report 快照：12,507,516 bytes，SHA-256
  `08E40F0B2ACF6E92CC1B23B42C1999A166CAA4560FF7663B7FAD585498D984CD`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`、
  `process_restart_required=false`，继续同 PID 热重试。

第一次加载上述提交后，同一事件仍返回旧的两项关系 RED。证据确认 CK3 PID、event
instance 和完整事件帧均未变化；原因是 live wrapper 只 reload 主 production-entry
模块，而 `.0359` 合同位于独立 spymaster shard，Python 的 `sys.modules` 仍缓存旧
shard 对象。该问题不要求、也不应通过重启 CK3 处理。production-entry 现会在重载
自身时先刷新已经加载的 `zg361_phase*_contracts` 数据分片，再重新汇总合同映射，
从而让任意合同分片修改都能在原暂停帧传递热生效。

- 第十一次 park 仍为 PID `159264`、event instance `371`：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-11.json`；
- park SHA-256：
  `0C84EAD74A230BE073338506DF79CB32EE6304314CDCA3A675FC54AD760069CC`；
- 缓存 RED report 快照：12,567,012 bytes，SHA-256
  `AA0AA50BFAF184E77538416AA9B6BF0C79FBFBEEAB30D8648063CF00DDF5087C`；
- 再次驻留检查 `7/7` GREEN，`selection_attempted=false`、
  `process_restart_required=false`。

## 同会话第十二次 RED：恩惠提案的囚禁叛军分支

第十一次 `retry` 热加载提交 `004c8d97f7a2bfe88ef4879adb7a9b302d978a4e` 后，分片修复
在原 `.0359` 实例上生效；同一 PID `159264` 随后推进到
`ep3_story_cycle_admin_eunuch.2050`、event instance `374`、
`date_raw=53255856`。本帧九项 scope 为
`story/emperor/eunuch/admin_title/student/rival/boon_faction/boon_victim/eunuch_boon`，
其中 faction 类型已由 MCP 确认为 `faction`，victim 为角色 `16843415`。旧合同只冻结
无目标 boon 帧，故仅名称和数量 RED；选择尚未发生。

原版 `ep3_story_cycle_admin_eunuch_select_boon_effect` 有四类精确输出形状：debase、
raise-taxes、influence 不保存目标；fabricate-hook 只保存 `boon_victim`；
imprison-rebel 成对保存 `boon_faction/boon_victim`；candidacy 保存
`boon_title/boon_victim/boon_target`。结合 shared story 独立可选的
`protege/student/rival`，合同展开 32 个精确集合，未知或残缺组合仍 fail-closed。
原版 `.2050` 没有 campaign-global occurrence 上限，故改为产品窗口内可重复。选择仍为
native option 1：拒绝 boon，只承担 story downgrade/stress，避免修改税收、继承投资、
hook 或监禁状态。

- 第十二次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-12.json`；
- park SHA-256：
  `56C9BDB094FDD0209B5CDEBDD0791A71F7A3DCFA2CB12342F404E1D36F7270F7`；
- 第十二次 RED report 快照：12,698,883 bytes，SHA-256
  `6735D1B19E907F6737888626C0D4F048A66D677333A588098ED79B4D3696FEBD`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`、
  `process_restart_required=false`，继续同 PID 热重试。

## 同会话第十三次 RED：宦官本人索要议席

第十二次 `retry` 热加载提交 `c9aeb0cdfe037ac0f3ad583db5428c12065e28c8` 后，同一 PID
`159264` 推进到此前未登记的 `ep3_story_cycle_admin_eunuch.2040`、event instance
`378`、`date_raw=53258328`，因此在选择前按未知事件 fail-closed。MCP 读取的九项
scope 为 `story/emperor/eunuch/admin_title/student/rival/petition_liege/`
`petition_vassal/second_party`：petition liege 与玩家同一，petition vassal 与宦官
`31801` 同一，现任议员 second party 为 `29346`；两个 native options 均可用。

原版 immediate 固定把 root 保存为 `petition_liege`、把宦官保存为
`petition_vassal`，再按其能力选择最合适的议席；仅当该席已有现任时才保存
`second_party`。native option 0 会开除现任、任命并保护宦官，还升级 story；native
option 1 不改议会阵容，仅执行 story downgrade、意见和特质相关 stress。合同因此
选择 native 1，并以六项基础 scope 加 shared story 的 `protege/student/rival` 与
可选现任展开 16 个精确集合；别名、非玩家和现任互异关系继续 fail-closed。事件
cooldown 为五年，产品窗口内可重复。

- 第十三次 park：
  `Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource\hot-recovery-park-13.json`；
- park SHA-256：
  `59E127745B231794097265A94199EA774C61EEC2801523F6E59177A63AEF2941`；
- 第十三次 RED report 快照：25,869,382 bytes，SHA-256
  `0F5C39423FB748A9D2736CA6AD74D34623AD18C0084573268B0E258BC27207A6`；
- 驻留检查 `7/7` GREEN，`selection_attempted=false`、
  `process_restart_required=false`，继续同 PID 热重试。
