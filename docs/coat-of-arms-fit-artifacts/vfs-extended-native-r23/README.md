# CK3 CoA VFS 扩展原生证据 R23

状态：`passed`。最终报告在干净工作树的主线提交 `d2cddad56bfe9cbea367bf63b357654952a63723` 上执行。本轮不覆盖 R22，
而是在 exact CK3 `1.19.0.6` 中新增两类直接 DDS precedence 证据：

1. 基础游戏 `pattern_checkers_06.dds` 与启用目录模组提供的同路径 DDS 冲突时，目录模组胜出；
2. 较早目录模组与较晚 ZIP archive 模组提供同一已注册 DDS 路径时，较晚 archive 模组胜出。

这不是从文件顺序推断。夹具为每一侧另外注册一个内容逐字节相同、名称唯一的 reference pattern；受管 CK3 会话依次 Apply、原生 Copy，
再通过 reference-free framebuffer MCP 捕获 230×230 对齐内容。全过程 `mcp_only=true`、Steam 离线、零 OCR、零键盘、零鼠标；结束时
`cleanup_proven=true`、`tree_gone=true`。

## 预登记门禁与结果

- 捕获噪声门限：最大通道误差 `1`、归一化 MAE `<= 0.00001`、alpha 差异像素 `0`；
- base conflict vs mod reference：MAE `0.0000075249842`、最大通道误差 `1`，门限内等价；
- base conflict vs base reference：MAE `0.2694562781`、最大通道误差 `178`，明确不等价；
- archive conflict vs later archive reference：MAE `0.0000061764207`、最大通道误差 `1`，门限内等价；
- archive conflict vs earlier directory reference：MAE `0.2694592449`、最大通道误差 `178`，明确不等价；
- 6 个 case 的 Apply、native Copy 语义投影、route-stable preparation 和 reference-free capture 全部通过；6 个预登记 pair gate 全部通过。

机器可读证据为 [`evidence.json`](evidence.json)，并随附 6 张 SHA-256 绑定的原生对齐 crop。原始完整报告保留在本机
`D:\ck3_coa_vfs_native_r23_exact\report.json`，共 `3,523,886` bytes，SHA-256
`F8B3609BDFEE531605D992E08C017C0BE62D0D6760C4F94D3AEE978E7FB32230`；仓库只保存 compact evidence，避免重复提交 framebuffer/base64。
第一次未冻结源码的 provisional 运行与 artifact 已移至本机 `D:\ck3_coa_vfs_native_r23*` 保留，不作为本结论证据。

## 能力边界

本结果只证明 exact build、该隔离 profile 和已注册直接 DDS 路径中的两类 precedence。它没有证明 DLC mount、`replace_path`、
definition merge 或任意脚本定义类别的胜者。正式网页仍不读取或连接本机 CK3；它只消费经 receipt 解析的静态 asset pack。

## 复现

```text
set PYTHONPATH=ck3_autonomous_player\src;ck3_autonomous_player&& tools\.venv\Scripts\python.exe -m unittest ck3_autonomous_player.tests.unit.test_prepare_coat_of_arms_vfs_fixture

set PYTHONPATH=ck3_autonomous_player\src;ck3_autonomous_player&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\prepare_coat_of_arms_vfs_fixture.py --extended --base-profile C:\Users\1\DOCUME~1\PARADO~1\CRUSAD~1 --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --output D:\ck3_coa_vfs_native_r23_exact_source

set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile D:\ck3_coa_vfs_native_r23_exact_source --state-dir D:\ck3_coa_vfs_native_r23_exact\state --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar_ck3_coa_vfs_native_r23_exact --bridge-dll C:\xb\coa-wp1-v2-final\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-wp1-v2-final\xar_ck3_bridge_injector.exe --timeout 420 --vfs-extended-matrix --vfs-extended-crop-dir D:\ck3_coa_vfs_native_r23_exact\crops --output D:\ck3_coa_vfs_native_r23_exact\report.json

set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\summarize_coat_of_arms_vfs_extended_matrix.py --report D:\ck3_coa_vfs_native_r23_exact\report.json --fixture D:\ck3_coa_vfs_native_r23_exact_source --artifact-dir docs\coat-of-arms-fit-artifacts\vfs-extended-native-r23 --output docs\coat-of-arms-fit-artifacts\vfs-extended-native-r23\evidence.json --check
```
