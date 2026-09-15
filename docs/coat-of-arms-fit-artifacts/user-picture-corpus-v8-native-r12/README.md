# user-picture-corpus-v8-native-r12

本目录继承 r11 的 7 图原生 UV 对照，并新增每例的完整第二阶段：首次 Apply → 原生 Copy → 把 Copy
全文重新分块 Apply → 再次捕获。它不覆盖 r11；r11 固定首次网页/CK3 对照，本 run 专门回答
picture-02/05/07 的 fractional rotation 被 CK3 Copy 取整后是否产生可见变化。

运行源码为 commit `40113074`。Steam 全程离线；全部操作经受管 MCP 完成，没有 OCR、键盘、鼠标链
或固定坐标。framebuffer 为 2560×1440，v3 校准矩形 `[818,312,965,478]`，9 个原生 UV 标记的
最大重投影误差为 0.464 px（门禁 2.5 px）。首次网页→CK3 沿用 MAE 0.10 / MSE 0.03 / edge
0.16 / 最坏空间块 0.25；Copy 再导入使用更严格且运行前冻结的 0.01 / 0.001 / 0.02 / 0.03。

| 用例 | 首次 MAE | 首次 MSE | 首次 edge | 首次最坏块 | Copy 再导入 MAE | 再导入 edge | 再导入最坏块 |
|---|---:|---:|---:|---:|---:|---:|---:|
| picture-01 | 0.015428 | 0.001731 | 0.065255 | 0.075902 | 0.0000336 | 0.000216 | 0.000239 |
| picture-02 | 0.017741 | 0.002166 | 0.081027 | 0.152326 | 0.0000237 | 0.000167 | 0.000500 |
| picture-03 | 0.022211 | 0.003139 | 0.096215 | 0.088661 | 0.0000306 | 0.000202 | 0.000145 |
| picture-04 | 0.038211 | 0.008299 | 0.127429 | 0.130051 | 0.0000336 | 0.000156 | 0.000523 |
| picture-05 | 0.044035 | 0.010731 | 0.140460 | 0.225221 | 0.0000771 | 0.000345 | 0.000272 |
| picture-06 | 0.026011 | 0.006381 | 0.072937 | 0.103525 | 0.0000418 | 0.000167 | 0.000234 |
| picture-07 | 0.031259 | 0.006750 | 0.102745 | 0.098571 | 0.0000510 | 0.000246 | 0.000135 |

结果分级：

- 网页 canonical → 首次 CK3 Apply：7/7 通过。
- CK3 Copy 文本 → 再次 CK3 Apply：7/7 完成严格二次传输/计数/语义闭环。
- 首次 CK3 像素 → Copy 再导入 CK3 像素：7/7 通过更严格门禁；最高 MAE 为 0.0000771，最高
  edge 为 0.000345，最高最坏空间块为 0.000523。
- v8 原代码 → 首次 CK3 Copy 的字段序列仍是 4/7；picture-02/05/07 的 rotation 取整事实继续保留，
  不用宽松归一化改写成文本全等。新增证据只说明该原生规范化在当前实际家徽表面分辨率下像素等价。

每个 `picture-*` 目录同时保存 `native-crop.png` 和 `native-copy-reapplied-crop.png`，人工逐对复核也
没有可见差异。`summary.json` 保留精简收据。原始 22,298,611-byte report 含重复代码和 PNG base64，
由 `.gitignore` 排除；SHA-256 为
`FEC97D8F317C608D91F55106F19BA2B05A37A4863DF1133A464CB0FE05F0ABD2`。runner 最终证明 CK3
进程树归零、watchdog 消失、共享槽位释放。

复现：

```bat
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile C:\Users\1\Documents\PARADO~1\CRUSAD~1 --state-dir D:\ck3_coa_picture_corpus_native_r12 --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar-coa-picture-corpus-native-r12 --bridge-dll C:\xb\coa-wp1-v2-final\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-wp1-v2-final\xar_ck3_bridge_injector.exe --timeout 420 --picture-corpus docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-budget-1024 --picture-crop-dir docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r12 --output docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r12\raw-report.json
tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\summarize_native_picture_corpus.py docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r12\raw-report.json docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r12\summary.json
```
