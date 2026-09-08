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
