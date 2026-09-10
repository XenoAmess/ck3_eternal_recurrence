# 二期离线预验记录（2026-09-10）

- open_kaishek commit：`890b32de49081b7b5510e40c5518dfb59d5c8a6d`
- 工具版本：`kaishek-cli 0.1.0-cli`
- profile：`ck3-1.19.0.6`（static）
- CK3 exact build：`1.19.0.6`
- CK3 EXE SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- corpus：`mod_xenoamess_quality_of_life`，13 个可识别脚本文件，198428 bytes
- corpus SHA-256：`834e9bb0934829d961dca208d51157e297b5f28520840f36a666e0f65f9de77d`

命令：

```powershell
java -jar D:/workspace/open_kaishek/kaishek-cli/target/kaishek-cli-0.1.0-SNAPSHOT-shaded.jar corpus --file mod_xenoamess_quality_of_life
java -jar D:/workspace/open_kaishek/kaishek-cli/target/kaishek-cli-0.1.0-SNAPSHOT-shaded.jar preflight --root mod_xenoamess_quality_of_life --profile ck3-1.19.0.6
java -jar D:/workspace/open_kaishek/kaishek-cli/target/kaishek-cli-0.1.0-SNAPSHOT-shaded.jar parse --file mod_xenoamess_quality_of_life/gui/event_window_widgets/xqol_conversion_threshold_slider.gui
```

结果：corpus parser GREEN（13/13、0 diagnostics），滑条 GUI 单文件 parser GREEN（39066 bytes、5801 tokens、119 blocks、round-trip true）。完整 preflight 的 parser、synthetic IR 和 finite runtime 均 GREEN；validator 因该 profile 不认识 XQOL 使用的大量 CK3 interaction/effect opcode 而返回 2820 个 `UNKNOWN_OPCODE`，归类为 open_kaishek 覆盖范围 RED，不是 CK3 capability RED，也没有据此修改生产语义。

明确不支持/尚未证明：CK3 interaction schema、scripted GUI 执行、事件 widget 数据绑定、`run_interaction` 异步回调、战争 scope 和真实游戏后果。它们仍须真实 CK3 paused artifact、日志与结果查询验收。全过程未启动 CK3、未修改存档、未使用网络。
