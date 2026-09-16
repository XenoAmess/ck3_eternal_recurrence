# exact 1.19.0.6 DLC 家徽来源清单 R36（MCP GREEN）

R36 通过官方 Python MCP client 调用闭合 schema 的 `ck3_query_coat_of_arms_installed_dlc_sources_v1`，只读核查本机 exact CK3 `1.19.0.6` 安装。此验收不启动或连接 CK3，不使用 OCR、键盘、鼠标，也不把磁盘安装冒充商店授权或运行时注册。

## 结果

- 已安装 `.dlc` 描述符：29。
- 物理内容树中含九类 CoA 候选目录的 DLC：0。
- DLC CoA `.txt`：0。
- DLC CoA `.dds`：0。
- exact-build、闭合输入 schema、描述符计数与“仅物理清单”边界全部通过。
- 报告：71,707 bytes，SHA-256 `E513966CA50B4C30D6BCD3B40682223B315CCB472229498639B669752AAA634D`。

因此，对这份 exact 安装而言，29 个 DLC mount 不会给基础 1,630 项网页素材包增加额外的直接 CoA DDS 或 definition 文件；DLC 风格素材已经位于基础游戏树。这个结论不外推其他 CK3 build、未安装 DLC、商店 entitlement、模组或未来资源布局。

完整 MCP 返回保存在 [`report.json`](report.json)。

## 复现命令

```text
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_coat_of_arms_source_inventory_mcp.py --game-directory C:\SteamLibrary\steamapps\common\CRUSAD~1 --output D:\ck3_coa_source_inventory_r36.json
```
