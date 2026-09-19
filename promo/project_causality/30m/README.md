# 《project因果律》体系正片工程

本目录承接《project因果律：伪天司的辉煌愿景》体系说明片。目录名保留为 `30m` 以避免破坏已有构建路径；项目所有者允许最终成片落在
20–45 分钟，本轮 r8 picture lock 为 33:44.797。

权威导演案为 [`docs/project-system-promo-30m-director-treatment.md`](../../../docs/project-system-promo-30m-director-treatment.md)；
四个章节之间的主题声明见 [`chapter-interludes.md`](chapter-interludes.md)，架构图的原生 Mermaid 画幅与视频合同见
[`docs/project-causality-architecture/video-integration-2560x1440.md`](../../../docs/project-causality-architecture/video-integration-2560x1440.md)。

## 当前状态

`2026-09-19-r8` 是当前无音乐 picture-lock 候选：

- 时长：容器 2,024.797 秒，60,743 帧；
- 规格：2560×1440、30 fps、H.264 yuv420p、AAC 48 kHz 双声道；
- 旁白：中文合成声线；简中主字幕与英文副字幕已烧录；
- 价值：新增 3 分钟“两种入口、四类收益”，明确已有 Mod 与新作者怎样进入体系；
- 实机：新增 5 分钟罗贝尔固定回归时间线与 90 秒当前原生循环；
- 结构：四个 20 秒章门全部改用场景内艺术文字；
- 架构：新增第 12 张 Mermaid 原生拓扑“两种入口、四类价值”；
- 背景：四张章门图基于角色设定生成 CK3 / 中世纪奇幻场景，不直接贴原头像；
- 音乐：未接入；没有打开、登录或自动操作 Suno；
- 状态：仍等待项目所有者 1× 连续审片，未授权发布。

本地产物：

```text
artifacts/project-causality/2026-09-19-r8/
├─ project-causality-r8-nomusic-picture-lock.mp4
├─ project-causality-r8-nomusic-picture-lock.video.json
├─ work/
└─ qa/contact-sheet-r8.jpg
```

视频 SHA-256：`CF5E9227C1052C54DA53D94A0FBEA4445F50F8F2160F863F69D3D4B27732BC0C`。机器可读记录见
[`build-records/2026-09-19-r8.json`](build-records/2026-09-19-r8.json)，人工接力见
[`owner-review-handoff.md`](owner-review-handoff.md)。

r6/r7 保留为源时间坐标和历史基线。r8 没有把历史罗贝尔路径冒充当前通用战争自治；固定回归、production-live 与 fixture-live 在画面中
持续分级。r5 已被 owner 以“文案太呆、机械朗读标题”明确否决，不再进入审片。

## 架构图合同

12 张图全部使用 Mermaid `flowchart` 节点—连线拓扑，不再保留 `block-beta` 网格图。普通节点与分区外框在 Mermaid 渲染阶段生成圆角，
判断节点保留菱形，人类/用户节点保留圆形或胶囊形。原生 SVG 纵横比必须位于 1.40–2.45；视频只做全拓扑高亮，不重排节点、不重画边、
不裁掉返回路径。

四章背景来自 `images/project_causality/character/generated_atmospheres/`。原始人物图仅作为生成参考，正式画面使用角色自然处于宫廷、
工坊、档案库与四环王国中的完整场景。

## 可复现输入

- [`radio-script.json`](radio-script.json)：31 个宏段、86 个实际旁白 cue；
- [`structure.json`](structure.json)：r6 源时间结构；
- [`architecture-shot-plan.json`](architecture-shot-plan.json)：架构图源时间锚点、焦点节点、实机插镜与重定时政策；
- [`chapter-gates.json`](chapter-gates.json)：四个 20 秒章门、主题宣言与声效绑定；
- [`sfx/`](sfx/)：四个确定性章门声效；
- [`music/suno-score-plan.md`](music/suno-score-plan.md)：项目所有者手动生成配乐时使用的六轨接力单。

构建入口：

```powershell
py tools/render_project_causality_architecture.py
py tools/build_project_causality_r8.py
```

构建器只读取冻结素材并生成本地候选，不启动 CK3、不操作 Suno、不上传媒体。

## 后续顺序

1. 项目所有者以 1× 连续观看 r8，按时间码给出必须修改项；
2. 项目所有者按 Suno 接力单手动生成并交回候选音轨与权利信息；
3. 后期在锁定画面上完成选曲、裁切、ducking、响度与峰值控制；
4. 音乐接入后重新完成一次全片连续审片；
5. 外部上传与发布仍需另行明确授权。

8:20 无音乐版本继续保留在上级目录，只作为预告与早期构建管线验证，不承担体系正片职责。
