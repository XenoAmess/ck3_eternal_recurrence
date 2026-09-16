# user-picture-corpus-v11-native-r13

本目录对 v11 最终浏览器候选的全部 7 个 `pictures.zip` 用例做了新的 CK3 原生复验，不继承 v8
的 framebuffer 结论。运行源码为 commit `b3bd10b4`；Steam 全程离线，所有页面导航、分块 Apply、
原生 Copy 和 framebuffer 捕获均由受管结构化 MCP 完成，没有 OCR、键盘、鼠标链或固定坐标。

本次必须把两个结果分开报告：

- **视觉一致性通过**：网页 canonical → 首次 CK3 Apply 为 7/7；首次 CK3 Apply → 原生 Copy
  再 Apply 也为 7/7。
- **严格原始文本字段序列为 4/7**：picture-02/05/07 的 fractional rotation 被 CK3 Copy
  规范化为整数，与 v8 r11/r12 的既有行为一致。runner 因此按 fail-closed 合同返回非零退出码，
  不把这三例伪装成文本全等；但每例的计数完整，且规范化前后原生像素通过更严格门禁。

framebuffer 为 2560×1440，v3 校准矩形 `[813,312,970,478]`；9 个原生 UV 标记的最大重投影
误差为 0.334 px（门禁 2.5 px）。首次网页→CK3 使用运行前冻结的 MAE 0.10 / MSE 0.03 /
edge 0.16 / 最坏空间块 0.25；Copy 再导入使用 0.01 / 0.001 / 0.02 / 0.03。

| 用例 | 实例 | 首次 MAE | 首次 MSE | 首次 edge | 首次最坏块 | Copy 再导入 MAE | 再导入 edge | 再导入最坏块 | 严格字段序列 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| picture-01 | 1,024 | 0.019919 | 0.003865 | 0.068665 | 0.083219 | 0.0000363 | 0.000239 | 0.000171 | 通过 |
| picture-02 | 640 | 0.018951 | 0.002948 | 0.071505 | 0.075010 | 0.0000270 | 0.000180 | 0.000165 | rotation 规范化 |
| picture-03 | 1,024 | 0.023621 | 0.004533 | 0.082741 | 0.092472 | 0.0000449 | 0.000287 | 0.000156 | 通过 |
| picture-04 | 1,024 | 0.033104 | 0.005153 | 0.098117 | 0.108654 | 0.0000771 | 0.000378 | 0.000236 | 通过 |
| picture-05 | 917 | 0.032310 | 0.005396 | 0.095654 | 0.097068 | 0.0000793 | 0.000379 | 0.000227 | rotation 规范化 |
| picture-06 | 1,024 | 0.018534 | 0.003112 | 0.052258 | 0.070266 | 0.0000278 | 0.000155 | 0.000142 | 通过 |
| picture-07 | 986 | 0.024285 | 0.003833 | 0.077923 | 0.052650 | 0.0000512 | 0.000276 | 0.000181 | rotation 规范化 |

每个 `picture-*` 目录保存首次 Apply 的 `native-crop.png` 与 Copy 再导入后的
`native-copy-reapplied-crop.png`。这些是按原生 UV 标定回 canonical 空间的内容证据；游戏的金属/木质
外框不属于网页家徽纹理，不进入评分 mask。所有 7 例的绘制实例、逻辑层和 `colored_emblem` 块数均
完整保留。7 对 canonical/首次原生裁图也已逐一直接复核：主体、颜色分区和前后遮挡关系一致；可见的
稳定差异限于 CK3 框体与原生采样柔化，没有再次发现旋转方向、depth 层序或规则网格错位。

`summary.json` 是可审阅的精简收据。原始 22,112,617-byte report 含完整代码、响应与 PNG base64，
按仓库规则由 `.gitignore` 排除，SHA-256 为
`8DCE71B2AADFD1ACD98D8B01DA7414BA147AA5CFA2D264277324D668A1625410`。清理收据证明 CK3 进程树归零、
watchdog 消失、启动锁和状态锁均已释放。

复现：

```bat
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile C:\Users\1\Documents\PARADO~1\CRUSAD~1 --state-dir D:\ck3_coa_picture_corpus_v11_native_r13 --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar-coa-picture-corpus-v11-native-r13 --bridge-dll C:\xb\coa-wp1-v2-final\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-wp1-v2-final\xar_ck3_bridge_injector.exe --timeout 420 --picture-corpus docs\coat-of-arms-fit-artifacts\user-picture-corpus-v11-preview-projection-budget-1024 --picture-crop-dir docs\coat-of-arms-fit-artifacts\user-picture-corpus-v11-native-r13 --output docs\coat-of-arms-fit-artifacts\user-picture-corpus-v11-native-r13\raw-report.json
tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\summarize_native_picture_corpus.py docs\coat-of-arms-fit-artifacts\user-picture-corpus-v11-native-r13\raw-report.json docs\coat-of-arms-fit-artifacts\user-picture-corpus-v11-native-r13\summary.json
```
