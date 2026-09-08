# R356：宦官秘密事件的可选目标变体

## 结论

R356 在真实 CK3 1.19.0.6 产品时间线的 `date_raw=53251848`、event instance
`356` 暂停于 `ep3_story_cycle_admin_eunuch.2051`。本帧仍有两个精确 native
options `(0, 1)`，root / emperor 均为玩家 `32904`，动态 eunuch 为 `31801`、
secret owner 为 `33556`，并比既有六项合同多出
`secret_target: character 62189`。选择尚未发生；既定的 authored option 2 /
native option 1 仍是不向玩家揭露秘密的较窄终止路线。

CK3 1.19.0.6 原版定义在事件 immediate 中使用：

```text
scope:secret ?= {
    secret_owner = { save_scope_as = secret_owner }
    secret_target ?= { save_scope_as = secret_target }
}
```

所以 `secret_target` 本来就是随所选秘密有无目标而出现的可选 scope。对应
scripted trigger 同时明确排除 `secret_target = root`，但没有证明目标必须与
secret owner 或 eunuch 互异。最小修复因此只接受以下两个完整集合：

- 六项无目标帧：`story/emperor/eunuch/admin_title/secret/secret_owner`；
- 七项有目标帧：在上述集合上精确增加一个 character 类型的
  `secret_target`，且其 ID 不得等于当前玩家。

其余 event key、root、日期窗口、owner/eunuch 别名关系、两个按钮以及选择后
event-instance 推进条件全部保持不变；不增加未经原版定义证明的人物关系约束。

## RED 与进程生命周期

- live report：
  `Z:\ck3_mod_rewrite\_runtime\p2r356c_endgamesource\report.json`
- report SHA-256：
  `B6C112E4393BDE9B2DF15126A03B42BA333BE90D2C92C808038872C0DD0E04AB`
- 分类：`known-interrupt-contract-drift`；失败项仅为旧合同的
  `saved_scope_count` 与 `saved_scope_names_exact`；
- `selection_attempted=false`；
- CK3 PID `112220` 随旧临时 wrapper 的 `finally` 被正常清理，cleanup 为
  GREEN。该退出不是外部合同修复所需的冷启动，而是 wrapper 尚未把合同 RED
  自动驻留；下一轮在启动前补齐驻留循环，单次 Ctrl+C 不再释放 supervisor。

## 静态验证

精确合同测试同时覆盖六项与七项合法帧、目标指向玩家时 fail-closed，以及
manager 切换后排除 ID 随新玩家重绑定。manager-recovery 与完整 promotion
runner 均要求 normal / `python -O` 两种解释模式通过后再提交。
