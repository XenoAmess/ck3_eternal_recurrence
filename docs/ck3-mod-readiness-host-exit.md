# 公共 readiness：原 host 在报告前退出时立即失败

2026-10-15 MTS R0015、R0016 在公共 host 准备阶段实际退出，`host-original-process-exit.json` 已由原 supervisor 的 retained `Popen.wait()` 写入，`native-report.json` 尚未产生。旧 `CaseClient.wait_hold()` 将报告缺席一直当作“还在启动”，浪费完整400秒 readiness预算，最后只显示超时，掩盖更早的原始校验错误。

`CaseClient.host_exit_before_report()` 只读取本场原始文件。原 host-started 与 host-exit 必须匹配当前 frozen run、完整 argv、相同正整数PID、actual retained Popen和实际 original wait。报告尚未产生且这些收据完整时，`wait_hold()` 立即记录 `READINESS_HOST_EXIT_BEFORE_REPORT`，抛出固定前缀 `ValueError: Original shared host exited before report (exit N):`，附原stderr最后8192字节解码摘要。完整stderr与原始start/exit文件分别记录精确pin，原文件不改写。

readiness结果新增 `host_exit_before_report`，包含 `host_started/host_exit/host_stderr` pins、`host_returncode`、`stderr_tail`，并明确 `native_report_observed/normal_close_qualified/native_exit_zero_proven/business_pass=false`。stderr缺席时其pin为null；退出码0但没有原生报告仍不授正常退出或业务通过。报告缺席不能证明CK3未启动，后继allocator必须独立核对已知prelaunch原因与真实资源闭合。

没有原exit收据时沿用原等待、预算和超时。receipt正在写入而JSON不完整时只等下一个原轮询，不重启窗口、不重放host。完整收据跨run/PID/argv或缺原wait时保留 `READINESS_ERROR`。已有原生报告、正常hold、保留游戏句柄和正常Quit流程不变。

本修复只作用未来场次。R0015、R0016原始400秒等待及RED保留，不追改成提前失败，不改正在运行的冻结工具。独立MTS保留产品和具体两场证据，本仓只保存公共readiness方法与实现；来源项目为 `ck3_mod_more_tenant_slots` 的2026-10-15用户bug整改工作包。

2026-10-15实际只读回放新helper对两场原档的消费：R0015原host返回1，原stderr末行为 `ValueError: effective host differs from reviewed projection`；R0016原host返回1，原stderr末行为 `ValueError: normal-exit private V1 does not support enabled mod GUI files`。两份原exit文件分别为254/255 B，SHA-256 `c7ad986d9abe2b89bad128c94b15349a1db7da04853400f422265d795fa32f1d` / `4b2771dc0385e62cad1de71baf4cba7f11086dc019d9ed78ce7cd33c7ef07a66`。原readiness窗口和错误记录完全未改；此回放不追授任一实机或闭场信用。

离线验证使用真实公共 `retain_host` producer与无害Python子进程，覆盖原host失败立即识别、exit0不授native0、PID绑定和原receipt完成写入；另复用原readiness窗口回归。无CK3、桌面、Steam、任务总线或native操作；实际新场仍须从公共入口独立记录。

实际命令为配置Python的 `-B -X utf8 -m unittest test_ck3_mod_acceptance_readiness_host_exit test_ck3_mod_acceptance_readiness_window -v`（工作目录 `tools`），最终11项/0.400秒通过、exit0。首轮原最小client测试缺report_path使1项ERROR；将无原exit收据的常规路径提前返回后复测通过，没有修改既有7项窗口测试或放宽原预算。
