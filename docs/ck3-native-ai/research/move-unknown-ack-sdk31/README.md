# SDK31 移动回执不确定的公开提取

正式修复在公共 `native_driver.py`，可复用分类器在
`tools/g2_saved_campaign/move_unknown_ack_outcome.py`。这里保留原外置纯分类增量，
供审计历史 AST loader 合同；它需要宿主的 `classify_gameplay_start_binding_v1`，
不可当作独立运行器，也没有执行游戏动作的入口。

原 AUTO417 报错，随后 SEM418 已看到同日完整目标路线；错误回执保留，原命令没有重发。
正式 Driver 只有在同 Game、角色、日期、连接下，原始 Native 请求/失败结果完整绑定，
且独立更新的帧出现新的完整目标路线时，返回 `observed_after_native_error`。
`accepted:false` 表示没有可信 ACK，另有 `native_ack_status:unknown_after_error` 和
`business_submission_may_have_applied:true` 明确其边界。路线意图不等于到达、胜利或可靠 ACK。

公共便携测试执行真实 Service → Driver → `_execute_primitive_step` → FakeEndpoint I/O，
使用 public256/native3207，随后257/3208；没有替换 primitive，也没有用 Hybrid 返回预计算 DTO。
Native 快照、Native wire 返回、预选计划和旁路镜头输入是合成测试边界；测试不证明普通 chooser
选择、原生 ABI 执行或未来自动恢复分支已在实机发生。旧 equal-revision/Hybrid 的三项 GREEN 已被替代。

相关测试：

```text
python -B -m pytest -q -p no:cacheprovider ck3_autonomous_player/tests/unit/test_move_unknown_ack_recovery.py
```

运行时设置 `PYTHONPATH=ck3_autonomous_player/src`。新用例9项 GREEN；连同既有 typed move 和 exact
move-stop 回归共26项、22个子用例 GREEN。原始场次大文件仍在外置证据根，仓库只保留3.6KB投影、
原件 SHA、纯源码和验收边界。原417究竟在 Native 哪个分支失败仍未知，见军事迁移专题的 AL ABI 审计。
