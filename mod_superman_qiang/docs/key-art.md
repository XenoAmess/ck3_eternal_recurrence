# 《超人强》当前工坊封面

2026-10-04 按用户要求，将首发封面的背景成年男性替换为与三张新横幅一致的成年王后。当前主体为一位成年国王与一位成年王后，王后面容在640缩略图中清晰可辨；完整服装、六技能符号、金色力量流转、中文标题“超人强”及副标题“越超人越强”保留。

这是一张原创宣传插画。使用内置 `image_gen` 编辑，未使用API/CLI fallback。完整实际提示词、编辑目标/参考图角色、生成路径及字节身份见 [来源记录](../../images/superman_qiang_cover_v2/provenance.json)。root直接审阅1254源图与精确640发布PNG，见 [审阅记录](../../images/superman_qiang_cover_v2/root-review.json)。

| 当前文件 | 尺寸 | bytes | SHA-256 |
|---|---|---:|---|
| [源图](../../images/superman_qiang_key_art.png) | 1254×1254 RGB PNG | 2,615,490 | `c58fffe3e52eedb1dd1d11f96bb2cff813ecf0bd2be5cadab77dccec63822178` |
| [thumbnail.png](../thumbnail.png) | 640×640 RGB PNG | 785,139 | `e70f54115bef351ee6e363bb116ee81bb25570f683cdc7606cf769b45d2b4f9b` |

正式缩略图只由现有 [composer](../../tools/compose_superman_qiang_key_art.py) 生成：RGB、居中ImageOps.fit/LANCZOS、优化PNG、compress_level9，严格小于1,000,000 bytes。canonical文件已实际生成，`--check`逐字节通过；不手改生成PNG。

```text
tools\.venv\Scripts\python.exe tools/compose_superman_qiang_key_art.py
tools\.venv\Scripts\python.exe tools/compose_superman_qiang_key_art.py --check
```

首发旧1254源及640副本、旧输入和完整生成过程保留于 `C:/ck3-superman-qiang-media-redo-20261004/cover-P0001/history/`，亦可从原不可变tag `superman-qiang-v1.0.0` 取回。[首发文档快照](key-art-initial-1.0.0.md)按该历史tag解释，其旧路径不代表本次新文件身份。旧tag及原GitHub附件不修改。

本次正式staging重新构建，仍为22文件：仅thumbnail字节变化，其余21文件必须与首发验收包逐字节相同。实际公开封面回读随展示修订发布报告记录，生成或审图通过不表示已经上传。
