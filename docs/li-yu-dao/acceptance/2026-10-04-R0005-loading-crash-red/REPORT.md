# 礼与道 R0005：加载 RED、观察到崩溃的永久小包

结论仍为 **NATIVE_LOADING_RED_AND_CRASH_OBSERVED**，`normal_exit=false`、`cause=NOT_PROVEN`。实际提交 `18b1944d1784d3e4ec57189c016335ef135b9b34`，产品树 `77f74591f299874efcd20c2672f143c362e54caa`，execution `bf0a2e3a-f038-4fac-9ab1-f7b6d1ccba6d`。原234件22,721,214bytes外置包保持原字节，本包另有独立索引，供永久入库。

完整事实与原始链见[外置大包原报告](C:/workspace/ck3_lyd_runtime_20261004/r5-loading-crash-red-package-001/REPORT.md)及[本地原报告副本](outer-REPORT.raw.md)。完整run原件仍在 `C:/workspace/ck3_lyd_runtime_20261004/live-attempt-005`，crash原7件39,858,628bytes全部保留，没有删除或改写。

## 本包保留的必要证据

实际挂载生产59件、入口夹具7件、全36派I2夹具7件，全部原字节与[PREPARED](inputs/PREPARED.json)、[manifest](inputs/production.manifest.json)匹配。I2输入预期36→35+1，但本轮没有执行setup。精确[18b官方CI](ci/README.md)完整初始pending／终态原件保留，只证明静态L0成功。

[最终error.log](logs/crash-observed/logs/error.log)记录4个[E]：I3未知`hidden_trigger`1条，I3连续`prev`链3条。[分类账](error-classification.json)原样保存。早先R4同核心／divergence、employer/location及变量诊断仅在本次最终error中确证未出现，不表示正式流程通过，也不证明后续崩溃原因。

保留[Steam位移前](offline/steam-before.png)与[位移后](offline/steam-moved.png)原图、[位移回执](offline/steam-frame-freshness.json)、[root离线审阅](run/offline-reviewed.json)，保留[实际冷加载](screens/loading-first.png)、[11:24:17Z大厅](screens/normal-exit-check.png)及其原元数据。必要原图没有缩放、裁切或再编码。

[crashed-exit-readback.png](screens/crashed-exit-readback.png)显示Steam前景及Paradox Reporter任务栏标签，不能说报告窗体清晰可见；其[原窗口／进程元数据](run/crashed-exit-readback.json)及[crash报告](logs/crash-observed/report.json)才绑定CrashReporter PID2596／HWND13829678。双进程退出由[独立process回读](run/crash-exit-processes-001.json)证明，不把这张此前原图当退出成功画面。

## 退出与未执行边界

[WM_CLOSE原回执](run/normal-close-request.json)时间为11:21:44.417Z（口头约11:21:45）。11:24:17Z原图仍是大厅；[exception原件](crash/ck3_20261004_192419/exception.txt)随后记本地19:24:21的`C0000005`，CK3栈没有可用函数名，因果关系未证实。11:27:32坐标命令参数校验拒绝只有root工具输出注记，没有独立原始拒绝回执，不记鼠标／键盘输入、点击或正常退出。

CrashReporter经语义WM_CLOSE请求关闭，11:31:22Z原process回读确认CK3与Reporter均不存在。keeper FINAL2698与CAS2699、allocator新的completed-red reason和实际helpers原字节都保留。没有campaign、attach、当前native profile或save；I1/I2/I3/I4正式流程、D+1、D+30、reload全部 **NOT_RUN**。

## 投影、省略与保全

体积最大项为4,772,806bytes完整CK3 stdout、1,935,633bytes全历史prelaunch notices、重复冷加载／WM_CLOSE后截图及多份相同debug日志。前两项完整原件保留大包，必要root review和当前run原回执保留小包。省去第二张相同加载阶段原图、重复WM_CLOSE后大厅图、初始Steam图及相同debug复本；保留一张未编辑冷加载图、一张大厅图、Steam位移对照和崩溃后桌面／元数据，足以保留本轮判别证据。

[完整外置索引](full-external-index.json)仍原样保留4211件原文件路径／bytes／SHA及省略记录；[投影账](projection-map.json)逐件说明原234件大包在本小包是否保留、原哈希和省略理由。[大包原索引](outer-index.raw.json)与新index分别绑定原件和投影。所有省略原件仍在外置原位置，不用小包替代保全。

crash小件、settings、logs、原crash全索引和[dump元数据](crash/dump-metadata.json)保留，39,386,417bytes minidump不复制、不符号化、不诊断。生成只读原包并复制选定原字节；未改原234件、tracked、游戏／屏幕或CI。最终文件数、体积与独立索引以[投影JSON报告](report.json)为准。
