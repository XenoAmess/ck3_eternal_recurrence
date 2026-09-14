# 驱策朝贡国：Steam 玩法实机截图清单

状态：上传副本已从 CK3 `1.19.0.6` 的 **R0009 GREEN 实机验收**确定性生成并完成人工视觉检查；Steam media strip 上传与公开回读尚未完成，首发在补齐下列公开证据前不得标为完成。

## 权威来源

- Run：`tea_source_R0009`
- Artifact：`D:\workspace\ck3_eternal_recurrence_process_assets\tributary_expansion_directives\runs\tea_source_R0009`
- Report：`report.json`，结果 `GREEN`，SHA-256 `B90D4C7EA94E3828EFB6A44F19398A1E35273DCB78CF0D996884AEC493A4D020`
- 游戏版本：CK3 `1.19.0.6`
- EXE SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- 产品发布树 SHA-256：`AAB1CF1AAA89955A6F4D3CA797688D8B7D2FD9EFF9F807D90BB3A1DE5473F6F3`
- 原始截图：`cell/07_directed_war_live.png`，2560×1440，4,806,863 bytes，SHA-256 `D4899B56FA6E4C420DFB65D86BBA8E04AE7ED089E3175153C4661D2472B44241`
- 投影脚本：`tools/compose_tributary_expansion_directives_workshop_media.py`
- 编码：Pillow quality 90、optimized progressive JPEG、4:4:4；Steam 单图低于 2 MB

## 上传顺序

| 顺序 | 玩家可见内容 | 裁切 `(left, top, right, bottom)` | 仓库文件 | 尺寸 | JPEG bytes | SHA-256 |
| ---: | --- | --- | --- | --- | ---: | --- |
| 1 | 朝贡国拒绝拓疆令，宗主仍支付 150 威望 | `320,0,1680,765` | `workshop/tributary_expansion_directives_media/01_directed_war_live.jpg` | 1360×765 | 303,241 | `6B9D837A4BF34545C92EC4A13893F3E58A19C177698459C9AEF37B8DF5721200` |

推荐标题：`命令遭拒，威望照付 / A refusal still costs Prestige`

## 视觉取舍

- 原始画面右侧仍打开外置验收夹具的决议面板；确定性裁切完整排除了该测试 UI。
- 上传副本只保留 CK3 正常地图、资源栏与产品 toast“拓疆令遭拒——威望已经付出”，直接展示玩家会遇到的真实拒绝分支与威望代价。
- 人工原尺寸检查未见测试标记、调试文字、紫色缺图、拉伸、错误裁切或生成式改写。该图是实机画面的裁切/压缩副本，不是 thumbnail、概念图或静态合成图。

## 发布证据

待首发后补写：Workshop item ID、公开页面、`highlight_strip_item` 精确数量与顺序、Steam CDN 原图 URL、匿名下载尺寸/bytes/SHA-256，以及放大图人工复核结果。
