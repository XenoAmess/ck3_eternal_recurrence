# 图片素材命名与投影约定

本项目把可编辑的图片源文件放在仓库根目录 `images/`，把 CK3 实际加载的纹理放在对应 mod 的 `gfx/`。源文件只用于生成和审阅，不进入正式 staging；`build_release.py` 只允许发布 `.dds` 产物。

## 源文件命名

源文件名使用英文小写、下划线分词和语义主题，不加 mod 命名空间前缀。后缀描述用途：

| 用途 | 命名模式 | 当前例子 |
|---|---|---|
| 事件场景宽图 | `<主题>_wide.png` | `glassfire_avatar_wide.png`、`recurrence_end_wide.png` |
| 决议插图 | `decision_<主题>.png` | `decision_glassfire_ledger.png` |
| 方形头像/特质图标 | `<主题>.png` | `glassfire_avatar.png`、`glassfire_trait.png` |
| 独立版主视觉 | `<版本>_<主题>_key_art.png` | `vivhite_courtier_key_art.png` |
| 生成图提示词 | 与源图同名的 `.txt` | `decision_lifetime_contract_prompt.txt` |

事件场景源图应与事件窗布局匹配：宽画布、主体尽量放在右侧、左侧留出可读的事件文本区域，不要把自然语言或有方向性的标识烧录进图中。

## CK3 产物命名与尺寸

原版 mod 的产物使用 `xar_` 前缀；白绮独立版使用 `ervc_` 前缀。事件场景和决议图均使用 DDS/DXT1：

| CK3 用途 | 产物目录 | 尺寸/格式 | 示例 |
|---|---|---|---|
| 事件场景 | `gfx/interface/illustrations/event_scenes/` | `1592×848`，DXT1 | `xar_recurrence_end.dds` |
| 决议插图 | `gfx/interface/illustrations/decisions/` | `1100×440`，DXT1 | `decision_xar_ledger.dds` |
| 特质/轨道图标 | `gfx/interface/icons/.../` | `120×120` DDS | `glassfire_trait.dds` |
| Workshop 预览 | mod 根目录 | `640×640` PNG，低于 1 MB | `thumbnail.png` |

## 生成与引用链

事件场景源图由 `tools/compose_avatar.py` 的 `ASSETS` 表登记，脚本执行覆盖裁切、左侧渐变压暗并生成 DXT1 DDS。生成的 `xar_recurrence_end.dds` 先在 `common/event_backgrounds/xar_event_backgrounds.txt` 注册背景键，再由事件写入：

```text
override_background = { reference = xar_recurrence_end }
```

这样事件脚本只依赖背景数据库键，不直接拼接纹理路径。`tools/validate_static.py` 会同时检查源图、生成产物的逐字节 parity、DDS 尺寸/格式以及 `xar.1001` 的背景引用；改动源图后必须重新运行生成器并审阅差异。

正式构建只从 mod 源目录的 allowlist 投影 `.dds`、脚本和本地化文件，`images/` 源图与 `tools/` 生成器不会上传到 Workshop。
