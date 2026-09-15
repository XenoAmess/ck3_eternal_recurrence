# user-picture-corpus-v8-native-r11

本目录是 `pictures.zip` 全部 7 个用例在 v8 depth/rotation 修复后的 CK3 原生验收证据。输入来自
`../user-picture-corpus-v8-budget-1024/`，运行源码为 commit `e4a3caa7`。本次运行只通过受管 MCP
操作家徽页并读取 framebuffer；没有 OCR、键盘、鼠标链或固定屏幕坐标。Steam 全程离线。

原生比较使用 `ck3-coat-of-arms-framebuffer-calibration-v3`：先用红/绿状态定位动态表面，再以黑底和
9 个原生 `ce_block_02.dds` 标记恢复 canonical UV 到 framebuffer 的仿射映射。实测 framebuffer
为 2560×1440，表面矩形 `[817,312,966,473]`，9 点最大重投影误差为 0 px。比较 mask 排除 CK3
木质盾框，因此目录中的 `native-crop.png` 可保留盾框供人工审阅，但盾框不参与指标。

预先冻结的像素门禁为 MAE ≤ 0.10、MSE ≤ 0.03、edge ≤ 0.16、最坏 8×8 空间块 MAE ≤ 0.25。

| 用例 | 实例 | Apply/Copy 核心计数 | Copy 严格语义 | MAE | MSE | edge | 最坏空间块 | 原生像素 |
|---|---:|---|---|---:|---:|---:|---:|---|
| picture-01 | 1,024 | 通过 | 通过 | 0.024855 | 0.005989 | 0.085420 | 0.084051 | 通过 |
| picture-02 | 580 | 通过 | rotation 被 CK3 规范化 | 0.024176 | 0.004273 | 0.093391 | 0.094393 | 通过 |
| picture-03 | 1,024 | 通过 | 通过 | 0.029431 | 0.007239 | 0.101466 | 0.082469 | 通过 |
| picture-04 | 1,024 | 通过 | 通过 | 0.043774 | 0.010389 | 0.132857 | 0.122049 | 通过 |
| picture-05 | 881 | 通过 | rotation 被 CK3 规范化 | 0.039884 | 0.009276 | 0.117462 | 0.140578 | 通过 |
| picture-06 | 1,024 | 通过 | 通过 | 0.020320 | 0.004009 | 0.058618 | 0.089200 | 通过 |
| picture-07 | 956 | 通过 | rotation 被 CK3 规范化 | 0.033684 | 0.007033 | 0.107750 | 0.088365 | 通过 |

7/7 都完成大于旧 128 KiB 单请求上限的分块 Apply、原生 Copy、计数回读和 UV 对齐 framebuffer
比较；7/7 像素门禁通过。逐图人工复核也确认人物主体、眼睛、头发、徽记及大块层序一致，没有再出现
r6 中 picture-07 前景被大块覆盖的现象。网页拟合预览和右侧编辑预览另由浏览器回归证明引用同一
canonical PNG 和相同展示几何，7/7 字节一致。

总报告仍为 RED（逐案为 4 passed / 3 failed），唯一原因是 picture-02/05/07 的 CK3 Copy 会把
小数 rotation 规范化为整数，严格字段序列因此失败；三例当前 Apply 后的原生像素门禁全部通过。
这项文本 round-trip 差异不得被误报成像素失败，也不能被宽松归一化藏掉。后续需要独立验证
“Copy 回读文本再次 Apply”是否产生可见差异。

`summary.json` 保存可审阅的校准、传输、计数、语义与指标收据；原始 12,297,893-byte report
因含重复的代码和 PNG base64 而由 `.gitignore` 排除，其 SHA-256 固定为
`5D197C08A57CA4F2AEF3977FB58D9741038EFC6EBE9C872DFF73AB84876E98B2`。runner 最终证明 CK3
进程树归零、watchdog 消失、共享槽位释放。

复现摘要：

```bat
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile C:\Users\1\Documents\PARADO~1\CRUSAD~1 --state-dir D:\ck3_coa_picture_corpus_native_r11 --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar-coa-picture-corpus-native-r11 --bridge-dll C:\xb\coa-wp1-v2-final\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-wp1-v2-final\xar_ck3_bridge_injector.exe --timeout 300 --picture-corpus docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-budget-1024 --picture-crop-dir docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r11 --output docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r11\raw-report.json
tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\summarize_native_picture_corpus.py docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r11\raw-report.json docs\coat-of-arms-fit-artifacts\user-picture-corpus-v8-native-r11\summary.json
```
