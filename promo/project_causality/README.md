# 《project因果律》宣传片工程

> 副标题：伪天司的辉煌愿景  
> 状态：30:00 无音乐 picture-lock 候选已生成并通过自动媒体验收；等待项目所有者连续审片与手动生成 Suno 配乐
> 冻结日：2026-09-19（Asia/Shanghai）

本目录保存《project因果律》的宣传片生产工程。`8:20` 版本已经验证中文旁白、双语字幕、人物资产、来源 sidecar 和自动构建管线，但事实
证明它只能承担预告，不能充分解释整套体系。现行正片已经转为精确 `30:00` 的体系说明纪录片，并完成无音乐画面锁定候选；入口见
[`30m/README.md`](30m/README.md)。

## 当前冻结

| 项目 | 冻结值 |
|---|---|
| 制作基线 commit | `8840ee81e0dc30d9a3330ee63ab9ec17a3a8f48c` |
| CK3 exact build | `1.19.0.6` |
| 片长 | `1800.000 s` 视频轨 / `54000` frames at 30 fps |
| 画幅 | `2560×1440` |
| 旁白 | 简体中文；Edge TTS `zh-CN-XiaoxiaoNeural` 作为当前制作声线 |
| 字幕 | 简中主字幕 + 英文副字幕 |
| 音乐 | 纯音乐；Suno V5/V5.5；由项目所有者操作网页生成，当前执行者不得操作 Suno 网页 |
| 发布 | 只制作本地候选；不上传、不发布 |

这次制作是项目所有者在 2026-09-19 对体系宣传片的新明确授权。它不恢复天朝 361 二期宣传：影片只使用公开版或已经公开验收的
361 素材，二期内容仍完全排除。

## 文件

| 文件 | 职责 |
|---|---|
| `project-config.json` | 画幅、时长、语言、冻结版本和产物合同 |
| `timeline.json` | 精确到秒的 35 个 cue、画面来源和证据分级 |
| `claims.json` | 能力声明、允许措辞和禁止外推 |
| `narration.zh-Hans.md` | 中文旁白定稿及对应英文语义 |
| `subtitles.en.md` | 英文副字幕定稿 |
| `storyboard.md` | 镜头和转场设计 |
| `shot-list.md` | 历史素材复用与最小补拍清单 |
| `visual-style.md` | 人物、字体、颜色、标签和安全区规则 |
| `music/suno-score-plan.md` | Suno 母题、Style Box、结构标签和生成选择标准 |
| `music-rights.json` | 音乐来源与权利状态；未生成前保持 pending |
| `review-checklist.template.json` | 人工连续观看和最终签核清单 |
| `owner-review-handoff.md` | 项目所有者次日审片、操作 Suno 和交回素材的最短步骤 |
| `build-records/2026-09-19-r1.json` | 首个 8:20 无音乐预演片的哈希、自动检查与未完成项 |
| `30m/radio-script.json` | 30 分钟、86 个 cue 的双语旁白与画面合同 |
| `30m/music/suno-score-plan.md` | 30 分钟正片的六轨配乐接力单 |
| `30m/build-records/2026-09-19-r5.json` | 30 分钟 picture lock 的哈希、媒体探针和验收边界 |

可复现构建入口为 `tools/build_project_causality_promo.py`。它会先检查 35 个 cue 是否无缝覆盖精确 500 秒、所有 claim 是否存在，随后将
时间线投影给通用视频构建器。脚本不会启动 CK3、操作 Suno 或上传媒体。

30 分钟正片使用 `tools/build_project_causality_30m.py`。它校验宏观结构、86 个 cue、四个章门和 claim/evidence 绑定，再投影给同一通用
视频构建器；同样不会启动 CK3、操作 Suno 或上传媒体。

## 事实边界

- 生成的人物主视觉和章节图只作 `DIAGRAM` / `VISION` 包装。
- Workshop 实机截图可以证明对应公开产品的可见形态，但不能代替完整流程录像。
- 自动玩家只展示已绑定 artifact 的有界 observation/action/verification；不得宣传为完整 CK3 自治。
- 任何缺少合格实机素材的产品只进入产品矩阵，不用概念图冒充 gameplay。
- 本地候选和自动化审计都不等于人工签核；外部上传需要新的明确授权。

## 制作产物

大体积媒体输出到忽略 Git 的目录：

```text
artifacts/project-causality/2026-09-19-r1/
├─ project-causality-820-nomusic-previz.mp4
├─ project-causality-820-nomusic-previz.video.json
├─ project-causality-820.manifest.json
├─ project-causality-820-contact-sheet.jpg
├─ qa-*.png
└─ work/
```

仓库只保存可复现输入、脚本、清单、审计规则和最终 sidecar 索引。

## Suno 操作边界

项目所有者将在次日亲自操作 Suno。当前制作不得打开、登录、自动控制或尝试绕过 Suno 网页；只允许准备提示词、结构标签、目标时长、
选择标准和后期接入点。没有最终音乐不会阻塞无配乐旁白粗剪，但正式候选在音乐接入、权利记录和完整混音前不得签核。

## 当前 picture-lock 边界

`2026-09-19-r5` 是 30 分钟正片的本地无音乐 picture-lock 候选，不是最终母版。它使用公开产品实机画面、可核验证据卡、历史有界自动玩家
片段和明确标注的愿景图；自动验证为 54,000 个视频帧，四个章门专属声效已经接入。它仍必须经过项目所有者 1× 连续观看；音乐接入后，
本次无音乐审片结论还必须重新复核。`2026-09-19-r1` 保留为历史 8:20 预告。
