# CK3 1.19.0.6 CoA 目录模组直接 DDS 胜者矩阵（R22）

## 结论

R22 在 exact CK3 1.19.0.6 中验证了一个有意收窄的 VFS 事实：当 `dlc_load.json` 的 `enabled_mods` 依次启用两个目录模组，
二者均注册并提供同名、同直接路径的 pattern DDS 时，后一个启用模组（本夹具 `load_order=1`）的 DDS 成为角色设计器实际渲染结果。

这不是对整个 CK3 VFS 的泛化声明。R22 **没有**证明基础游戏与模组、DLC mount、archive 模组、`replace_path`、脚本 definition
merge 或未注册裸文件的胜者规则；这些范围继续标记为未覆盖。

## 固定夹具与预登记门禁

- 启用顺序：`coa_vfs_fixture_first.mod`，随后 `coa_vfs_fixture_second.mod`。
- 冲突名：`pattern_xar_vfs_shared.dds`。
- `load_order=0` 源 DDS SHA-256：`58B4322BBE5046AFEDC4E350F283A1AAEF48A6E86A5A40BF5FDB20321C519849`。
- `load_order=1` 源 DDS SHA-256：`ED859E29211712AC51E2BFF108CBAB58A72B48F62C1D875494CB036979B71A0C`。
- 启动配置 SHA-256：`EC52511EEFE4AD0CA1ADB36C8F8C1D2CB8F1FC8F46079C7FFB2D3E94D16B02F4`。
- 运行前假设：共享路径应与 `load_order=1` 的唯一参考等价，并与 `load_order=0` 的唯一参考不等价。
- 独立捕获噪声门限：最大通道误差 `1`、归一化 MAE `<= 0.00001`、alpha 差异像素 `0`。

## 原生结果

| 对照 | 预期 | 230×230 归一化 MAE | 最大通道误差 | 可见差异像素 | 结果 |
|---|---|---:|---:|---:|---|
| shared / load-order-0 | 不等价 | `0.2709360266` | `178` | `28,203` | PASS |
| shared / load-order-1 | 噪声门限内等价 | `0.0000076908` | `1` | `282` | PASS |
| load-order-0 / load-order-1 | 不等价 | `0.2709363516` | `178` | `28,226` | PASS |

三个 case 均完成 Apply、原生 Copy 回读、同 route/generation reference-free framebuffer capture。交互全程为 MCP-only，
`uses_ocr=false`、`uses_keyboard=false`、`uses_mouse=false`，Steam 保持离线。清理证据为 `cleanup_proven=true`、
`tree_gone=true`，没有遗留 CK3 会话或共享槽位。

## 产物

- [`summary.json`](summary.json)：压缩后的机器可读证据；schema `ck3-coat-of-arms-vfs-winner-evidence-v1`。
- [`shared-conflict.png`](shared-conflict.png)：共享冲突名的原生对齐 crop。
- [`load-order-0-reference.png`](load-order-0-reference.png)：第一个模组唯一参考。
- [`load-order-1-reference.png`](load-order-1-reference.png)：第二个模组唯一参考。
- 原始报告：`D:\ck3_coa_vfs_native_r22\report.json`，2,488,214 bytes，SHA-256
  `C512EB1BAFB6A63F6F9A626811EA34FF2DF2782D22D151F0F900867DF0DA1EDC`；大体积 framebuffer/base64 过程证据不重复提交。

## 复现

```bat
set PYTHONPATH=ck3_autonomous_player\src
tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\prepare_coat_of_arms_vfs_fixture.py --base-profile C:\Users\1\DOCUME~1\PARADO~1\CRUSAD~1 --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --output D:\ck3_coa_vfs_native_r22_source

tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile D:\ck3_coa_vfs_native_r22_source --state-dir D:\ck3_coa_vfs_native_r22\state --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar_ck3_coa_vfs_native_r22 --bridge-dll C:\xb\coa-wp1-v2-final\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-wp1-v2-final\xar_ck3_bridge_injector.exe --timeout 420 --vfs-winner-matrix --vfs-crop-dir D:\ck3_coa_vfs_native_r22\crops --output D:\ck3_coa_vfs_native_r22\report.json

tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\summarize_coat_of_arms_vfs_winner_matrix.py --report D:\ck3_coa_vfs_native_r22\report.json --fixture D:\ck3_coa_vfs_native_r22_source --artifact-dir docs\coat-of-arms-fit-artifacts\vfs-winner-native-r22 --output docs\coat-of-arms-fit-artifacts\vfs-winner-native-r22\summary.json --check
```

重新实跑会启动 CK3，必须先遵守共享槽位与 Steam 离线规则；只复核已冻结 summary 时不需要 CK3。
