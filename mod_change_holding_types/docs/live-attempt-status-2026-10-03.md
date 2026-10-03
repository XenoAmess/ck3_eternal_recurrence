# 2026-10-03 实机 attempt 状态与能力边界

产品：地产类型转换（XenoAmess维护版）。本记录只记已经发生的结果；R0002 记录时仍在进行，没有产品实机 GREEN 或发布成功事实。

## 冻结输入

- CK3 `1.20.0.3`，Steam build `25652598`。
- EXE SHA-256：`94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。
- 正式候选：17 文件，九语言各44 key。简中／英文保留冻结字节；七語候选、格式与token检查和审阅边界见 [localization-coverage-2026-10-03.json](localization-coverage-2026-10-03.json)。该报告明确 `native_speaker_reviewed=false` 和 `live_verified=false`。
- canonical LF 候选的 [正式静态 R0003](release-static-R0003-2026-10-03.json) 为 GREEN；静态结果不证明 GUI 或玩法。
- 两个 live attempt 的 `production.manifest.json` SHA-256 相同，为 `9bb6793a36c264b8a1ba17fd58a1961229259cdd22f347f37e97ff993519a797`。运行staging和fixture作为冻结输入保留，不因文档工作改写。

## R0001：harness RED，未测产品

完整 run ID：`bf-202609141645-5434332d4d--change-holding-types--R0001`。

SDK `list_tools` 返回对象的处理异常中断会话脚手架；没有完成产品场景、目标选择、生产effect或付款断言。因此分类为 harness RED，不能用它判断产品适配失败或通过。

原始 `session/session-final.json` 保存 `status=RED` 和 `ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)`，还保存清理错误 `'EnvironmentSpec' object has no attribute 'pid_file'`。本记录不把“清理函数返回错误”改写为已确认退出，也不改写失败attempt。

外置证据根：`C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0001/`。
`session/session-final.json` SHA-256：`d2fe37738d2125fee33d1a5c66b54ea46f4dc48cd2572a1e930561878a7237ef`。

## R0002：exact-build handshake 成功，frontend route 未在 DLL 注册

完整 run ID：`bf-202609141645-5434332d4d--change-holding-types--R0002`。本记录的 native diagnostics 对应 PID `19500`。

`session/002-diagnostics-result.json` 实际读回 `connected=true`、`connection_generation=1`、`game_adapter_status=ready`、`ck3_build_match=true`，并绑定 `expected_ck3_version=1.20.0.3` 与上述EXE SHA。这证明本次连接和 exact-build匹配；不能外推为全部能力已部署。

`session/001-route-result.json` 的 transport 为成功，但工具返回 `isError=true`：

```text
native DLL does not advertise required capability game.command.query-frontend-gui-route-v1
```

Python MCP `tools.json` 中存在 `ck3_query_frontend_gui_route_v1` wrapper；真正缺失的是本次DLL hello内的native capability。wrapper名称、SDK list成功和handshake都不能替代原生功能已注册。此处是本轮已经触发的工具能力边界，不是holding脚本错误。

早期两次只读检查时 `state/profile/logs/error.log` 为0字节，其他日志已有生成；这只说明检查时刻未看到诊断，不能写成完整加载或玩法验收通过。夹具声明的10项状态断言、真实决议选择／执行／付款、保存重载等结果都要等实际证据追加。本记录没有这些PASS事实。

外置证据根：`C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0002/`。

- `session/001-route-result.json` SHA-256：`b111fa296cd305baafdb1cdb5d5ff2463525405eb86b4728ab89c30178b4acb2`。
- `session/002-diagnostics-result.json` SHA-256：`d83e79ae13c04087eeacefd90ce88146e67e5a56f8d0669842ec5a29eb7cfc8a`。

## 下一项收据

父任务继续同一R0002现场时追加原生状态、生产fixture结果和玩家入口证据；发生新冷载则分配新的mod run ID。失败或未实现的能力继续如实记录，不能把partial连接、命令ACK或空error.log写成产品GREEN。Workshop上传、完整公开Change Notes、fresh缓存与永久changelog仍各自等待实际交付。

## 2026-10-03 补记：R0003 重载与干净矩阵

[R0003 冻结核验报告](live-R0003-reload-2026-10-03/README.md) 已记录实际 ready snapshot002：人物 `31254`、同日 `53144328`、暂停、金币 `846`，保存 bytes 与 R0002 保存源 size／SHA 一致。原生日志证明 Rossano 的玩家直辖城市结果持久化，未选中首都仍为城堡。修正后的 fixture02 十项生产矩阵 PASS，连同两项保存状态共十二 PASS，START／END／AI actor 完整；捕获 error.log 为零字节。R0002 原错误继续保留。

英文截图已观察六名称、费用400和条件；完整 warning 的无遮挡稳定截图及七语视觉尚待 R0004 独立结果，母语审阅未完成。结论只适用本机固定 `1.20.0.3` EXE/build，不外推整个 `1.20.*` 系列，也不代表发布、公开 Change Notes、缓存或 changelog 已交付。早期 Taranto 地名误记以 [追加勘误](corrections-2026-10-03.md) 更正为 Trani／特拉尼，原候选不覆盖。

## 2026-10-03 补记：R0004 英文视觉与未完成语言门

[R0004 报告](live-R0004-visual-route-2026-10-03/README.md) 确认英文六名称、城市说明、Trani目标及成本400；完整警告仍被tooltip遮挡，名为unobscured的末帧也不满足门禁。debug French按钮／控制台路线后HUD仍英文，分类为测试路线 FAIL，产品法语及其余六语视觉均未测，后续应新run冷启动每种语言。debug原版 `is_ai` trigger perspective 诊断及产品调用上下文完整保留，没有改 runtime。实际session-final与bus-release证明清理／屏幕释放；R0003 register回执误覆盖另见 [追加勘误](corrections-2026-10-03.md)。

当前发布状态仍 pending：已有真实城市GUI执行／付款和 R0003 保存重载／干净十项矩阵；剩余完整警告、七语冷载视觉以及正式上传／公开全文Change Notes／fresh缓存／永久changelog，不把R0004路线失败或部分英文截图写成正式release完成。
