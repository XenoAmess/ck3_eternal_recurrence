# user-picture-corpus-v12-native-r14

本目录对 v12 浏览器候选的 `pictures.zip` 全部 7 个用例重新执行 CK3 原生验收。运行源码为
commit `1080affa`；Steam 全程离线，Apply、Copy、framebuffer 捕获和页面导航全部走结构化 MCP，
未使用 OCR、键盘、鼠标或固定截图坐标。

绝对门禁结果必须与候选晋级结论分开：

- 网页 canonical → CK3 原生像素为 **7/7 通过**；最坏 MAE `0.041775`、MSE `0.009702`、
  edge `0.139285`、最坏 8×8 空间块 `0.225221`，均低于运行前冻结的
  `0.10 / 0.03 / 0.16 / 0.25`。
- CK3 Copy 全文再次 Apply 为 **7/7 通过**；最坏 MAE `0.0000729`、MSE
  `0.000000286`、edge `0.000337`、最坏空间块 `0.000523`。
- 首次 source → Copy 严格字段序列为 **4/7**。picture-02/05/07 的小数 rotation 被 CK3
  规范化为整数；实例、逻辑层和块计数完整，Copy 文本自身再次往返为 7/7。
- 本轮绝对阈值通过不证明 v12 优于 v11。跨 CK3 会话的未变样本也有明显采样漂移，因此另建
  `user-picture-corpus-v11-v12-native-ab-r15` 做同会话 A/B。

| 用例 | 实例 | 首次 MAE | 首次 MSE | 首次 edge | 首次最坏块 | 严格字段序列 |
|---|---:|---:|---:|---:|---:|---|
| picture-01 | 1,024 | 0.015428 | 0.001731 | 0.065255 | 0.075902 | 通过 |
| picture-02 | 640 | 0.016616 | 0.001882 | 0.078172 | 0.107228 | rotation 规范化 |
| picture-03 | 1,024 | 0.022211 | 0.003139 | 0.096215 | 0.088661 | 通过 |
| picture-04 | 1,024 | 0.038211 | 0.008299 | 0.127428 | 0.130051 | 通过 |
| picture-05 | 917 | 0.041775 | 0.009702 | 0.139285 | 0.225221 | rotation 规范化 |
| picture-06 | 1,024 | 0.026011 | 0.006381 | 0.072937 | 0.103525 | 通过 |
| picture-07 | 986 | 0.025481 | 0.005012 | 0.088557 | 0.092825 | rotation 规范化 |

每个 `picture-*` 目录保存首次 Apply 和 Copy 再 Apply 的 UV 对齐内容裁图。`summary.json` 是精简
收据。被 `.gitignore` 排除的原始 report 为 22,525,926 bytes，SHA-256
`6DEC3C00E614B71307FDD481D94B614D3C25D51B9EBB97A6C1548B701076AC53`。清理收据证明 CK3
进程树、watchdog 和两个共享锁均已释放。

复现：

```bat
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile C:\Users\1\Documents\PARADO~1\CRUSAD~1 --state-dir D:\ck3_coa_picture_corpus_v12_native_r14 --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar-coa-picture-corpus-v12-native-r14 --bridge-dll C:\xb\coa-wp1-v2-final\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-wp1-v2-final\xar_ck3_bridge_injector.exe --timeout 420 --picture-corpus docs\coat-of-arms-fit-artifacts\user-picture-corpus-v12-mixed-shape-budget-1024 --picture-crop-dir docs\coat-of-arms-fit-artifacts\user-picture-corpus-v12-native-r14 --output docs\coat-of-arms-fit-artifacts\user-picture-corpus-v12-native-r14\raw-report.json
tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\summarize_native_picture_corpus.py docs\coat-of-arms-fit-artifacts\user-picture-corpus-v12-native-r14\raw-report.json docs\coat-of-arms-fit-artifacts\user-picture-corpus-v12-native-r14\summary.json
```
