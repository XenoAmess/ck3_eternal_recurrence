# 《超人强》工坊封面

2026-10-04 使用 Codex 内置 `image_gen.imagegen` 生成原创主视觉。画面为成年中世纪统治者与象征六项属性的能量转移，角色均穿着完整服装；标题为“超人强”，副标题为“越超人越强”。未使用既有同名动画人物或其形象。

原图和 640×640 缩略图均已直接审阅：两行简体中文准确可读，六项属性符号完整，未出现额外文字或水印。此图是宣传封面；实机验收及工坊媒体截图另行记录。

| 文件 | 尺寸 | 字节数 | SHA-256 |
| --- | --- | --- | --- |
| [`images/superman_qiang_key_art.png`](../../images/superman_qiang_key_art.png) | 1254×1254 RGB | 2,669,088 | `4dd30fc9e8c50064c709e3cb42479342e419202961f9a6c3b66e015569a6a617` |
| [`thumbnail.png`](../thumbnail.png) | 640×640 RGB | 778,046 | `732deee357a6d322340fa9e6bb6d7b619b8c9da44b3c68711c23154079df863f` |

缩略图只能通过 [`tools/compose_superman_qiang_key_art.py`](../../tools/compose_superman_qiang_key_art.py) 从源图生成：转换为 RGB，以 Pillow LANCZOS 居中投影到 640×640，保存优化的 PNG，`compress_level=9`。脚本拒绝大于或等于 1,000,000 字节的输出。

```text
tools\.venv\Scripts\python.exe tools\compose_superman_qiang_key_art.py
tools\.venv\Scripts\python.exe tools\compose_superman_qiang_key_art.py --check
```

`--check` 已通过，证明仓库缩略图与重建结果逐字节相同。构建器应只将缩略图收入正式 staging，不携带源图、生成提示词或外置过程素材。

内置工具原始输出永久保留于 `C:/Users/1/.codex/generated_images/01a10325-ec45-72c0-a0c5-787c69cd3f00/exec-afd3b9e1-97e6-43be-a55f-8354ed2c3b5f.png`。独立过程副本、完整提示词和 JSON 元数据保留于 `D:/ck3-experience-drain-feasibility-20261004/superman-key-art-20261004/`。

## 最终生成提示词

```text
Use case: ads-marketing
Asset type: square Steam Workshop cover for an original Crusader Kings III mod.
Primary request: Create a polished original medieval fantasy key art showing an exceptionally powerful adult ruler receiving a flowing stream of symbolic attribute energy from another fully clothed adult ruler.
Scene/backdrop: a shadowed medieval great hall with a throne and subtle carved stone arches.
Subject: a confident adult ruler in richly embroidered crimson and black court clothes, a restrained gold crown, a strong human face, and a raised hand gathering six small luminous symbolic orbs representing diplomacy, warfare, stewardship, intrigue, learning, and prowess. The adult donor is a secondary figure in the background, clothed in medieval court dress; show only a symbolic energy transfer. All people are clearly over 25.
Style/medium: elegant detailed painterly historical fantasy illustration, substantial realism, bold cinematic poster composition, excellent craft and readable forms at thumbnail size.
Composition/framing: square 1:1 composition. Main ruler occupies the upper two thirds. Reserve the lower third for a very large, crisp, correctly spelled Simplified Chinese title. No UI screenshot elements.
Lighting/mood: warm golden energy contrasts with deep crimson and midnight blue. Confident, powerful, slightly playful heroic mood.
Text (verbatim): "超人强" as the large headline in the lower third, elegant bold gold Chinese lettering, exact three characters, crisp and legible. Directly below it, smaller but clearly readable text: "越超人越强". Render only these two text strings, no book-title brackets.
Constraints: This is entirely original medieval human character artwork. No cartoon pig, no animated television character likeness, no contemporary superhero costume, no existing superhero logo, no sexual act, no nudity, no erotic pose, no violence, no watermark, no extra text. The image must remain dignified and suitable for a public game Workshop cover.
```
