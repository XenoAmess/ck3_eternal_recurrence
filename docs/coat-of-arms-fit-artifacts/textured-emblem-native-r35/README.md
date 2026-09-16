# `textured_emblem` 原生验收 R35（GREEN）

R35 在 Steam 离线、CK3 `1.19.0.6` exact build 下，用修复后的受管 runner 完成单一标定样例的原生闭环。整轮只使用 typed MCP；没有 OCR、键盘、鼠标或固定屏幕坐标。

## 通过的门禁

- 原生路由进入角色设计器家徽页，reference-free v3 标定最大重投影误差为 `0` px。
- 172-byte wire source 经分块合同 Apply；CK3 Copy 回读 171 bytes。格式被规范化，但 pattern、texture、颜色以及全部九类语义字段顺序保持。
- 浏览器→原生 framebuffer：MAE `0.0072777048`、color MSE `0.0002390189`、edge loss `0.0271662716`、最差 8×8 空间 MAE `0.0292250253`；预声明上限分别为 `0.10 / 0.03 / 0.16 / 0.25`。
- 原生 Copy→重新 Apply framebuffer：MAE `0.0000153959`、color MSE `0.0000000604`、edge loss `0.0001159065`、最差空间 MAE `0.0001021242`；更严格上限分别为 `0.01 / 0.001 / 0.02 / 0.03`。
- 1/1 样例通过文本、语义、原生像素、Copy 重放与视觉门禁；报告 overall GREEN。
- 总耗时 `223.456` 秒；受管清理 GREEN，CK3 进程树归零，共享槽位已释放。

## 回执

- runner 源码 commit：`e71002970d5c4aa9c590908a019ab863de7f1e9e`。
- 完整报告：4,795,520 bytes，SHA-256 `C417943838093F62CE2AFF1B9BCDC3AFDBCE9A469A2F16D22F45D127FB085829`。
- 原生 Apply 对齐图：62,911 bytes，SHA-256 `365E4C2DAEF17708DB4077312CA128D34EC6182AE2E291E18B27646FD7C589DF`。
- Copy 重放对齐图：62,928 bytes，SHA-256 `EA94688BFAFE74FD6BDED75DEF13B68B28297F61A28F7B71AA3FEF751C012BD8`。

机器可读精简回执见 [`summary.json`](summary.json)，完整报告见 [`report.json`](report.json)，对齐图见 [`crops/`](crops/)。本结果证明当前唯一注册 `_default.dds` 的浏览器 shader 模型在声明阈值内与原生一致；它不证明逐字节像素相同，也不外推未注册 texture、DLC/mod definition merge 或其他 shader 分支。

## 复现命令

```text
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile D:\ck3_coa_textured_emblem_native_r34\profile --state-dir D:\ck3_coa_textured_emblem_native_r35 --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar_ck3_coa_textured_emblem_r35 --bridge-dll C:\xb\coa-vfs-r27\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-vfs-r27\xar_ck3_bridge_injector.exe --timeout 600 --single-reference-case docs\coat-of-arms-fit-artifacts\textured-emblem-browser-r31 --picture-crop-dir D:\ck3_coa_textured_emblem_native_r35_crops --output D:\ck3_coa_textured_emblem_native_r35_report.json

tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\summarize_native_picture_corpus.py docs\coat-of-arms-fit-artifacts\textured-emblem-native-r35\report.json docs\coat-of-arms-fit-artifacts\textured-emblem-native-r35\summary.json
```
