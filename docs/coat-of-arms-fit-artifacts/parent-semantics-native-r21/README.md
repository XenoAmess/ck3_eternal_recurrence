# CK3 1.19.0.6 `parent` 剪贴板预览矩阵（R21）

状态：**GREEN（MCP-only 原生证据）**  
执行日期：2026-09-16（Asia/Shanghai）  
前驱：`parent-semantics-native-r20`（探索性；没有预先登记量化噪声门限）

## 结论

在角色设计器的“自定义纹章 → 从剪贴板粘贴”路径中：

- `parent = k_england` 会被接受，并由原生 Copy 原样保留；
- 但有效的 `k_england` 与不存在的 `c_england` 在预览 framebuffer 中处于同一量化噪声范围，`k_england` 的白色飞龙没有被物化；
- `parent = k_england color1 = blue` 与只有 `parent = k_england` 同样处于量化噪声范围，缺少 `pattern` 时根颜色覆盖没有改变预览；
- 与 `parent` 同级写入的显式 `colored_emblem` 会正常改变预览。

因此，生产网页必须保留并导出 `parent`，但不能把静态数据库 definition 自动展开成“CK3 剪贴板预览”。若未来增加数据库 definition 浏览模式，它必须作为独立的解释性视图，不能冒充这个原生路径。

## 预先登记的门禁

R21 在启动 CK3 前已把独立 8-bit framebuffer 捕获噪声门限写入 runner：

- 最大通道差：`1`；
- 归一化平均绝对误差：`<= 0.00001`；
- alpha 差异像素：`0`。

三个诊断对全部按预期通过：

| 对照 | 预期 | 实测 MAE | 最大通道差 | 结果 |
| --- | --- | ---: | ---: | --- |
| `parent-only` / `unresolved-parent-control` | 等价 | `0.0000072219` | 1 | PASS |
| `parent-only` / `parent-override-blue` | 等价 | `0.0000082054` | 1 | PASS |
| `parent-only` / `parent-plus-child` | 不等价 | `0.0057570518` | 32 | PASS |

显式 literal `k_england`（`pattern_solid.dds` + `ce_wyvern.dds`）与三个 parent 对照均明显不同，最大通道差为 201。七个 case 全部完成 Apply、原生 Copy、准备和 reference-free capture。

## 证据边界

- 交互：受管 MCP；无 OCR、键盘或鼠标链。
- Steam：离线。
- 捕获：一次 affine calibration 后的 230×230 reference-free aligned crop；没有向捕获工具提供待验证参考图。
- 清理：CK3 进程树消失，runner 报告 `cleanup_proven=true`、`tree_gone=true`。
- 本目录保存紧凑 `summary.json` 与七张 SHA-256 绑定 PNG；完整的 4,104,921-byte、含 base64 原始报告保存在本机 `D:\ck3_coa_parent_semantics_native_r21\report.json`，其路径与 SHA-256 已写入摘要。

这只证明 exact 1.19.0.6 的角色设计器剪贴板路径，不证明其他 CK3 UI、脚本化 title/dynasty definition 加载或未来版本采用相同语义。

## 复现

```bat
set PYTHONPATH=ck3_autonomous_player\src
tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile C:\Users\1\DOCUME~1\PARADO~1\CRUSAD~1 --state-dir D:\ck3_coa_parent_semantics_native_r21\state --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar_ck3_coa_parent_semantics_r21 --bridge-dll C:\xb\coa-wp1-v2-final\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-wp1-v2-final\xar_ck3_bridge_injector.exe --timeout 420 --parent-semantics-matrix --parent-crop-dir D:\ck3_coa_parent_semantics_native_r21\crops --output D:\ck3_coa_parent_semantics_native_r21\report.json

tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\summarize_parent_semantics_matrix.py --report D:\ck3_coa_parent_semantics_native_r21\report.json --artifact-dir docs\coat-of-arms-fit-artifacts\parent-semantics-native-r21 --output docs\coat-of-arms-fit-artifacts\parent-semantics-native-r21\summary.json
```
