# 《project因果律》30:00 正片工程

本目录承接 30 分钟体系说明纪录片。权威导演案为
[`docs/project-system-promo-30m-director-treatment.md`](../../../docs/project-system-promo-30m-director-treatment.md)，精确时间结构在
[`structure.json`](structure.json)，四个章节之间的强制间隔与主题声明在 [`chapter-interludes.md`](chapter-interludes.md)，可执行的时间、
画面、声音和文案合同在 [`chapter-gates.json`](chapter-gates.json)。

## 当前状态

`2026-09-19-r5` 已完成精确 `30:00` 的无音乐 picture-lock 候选：中文合成旁白、简中主字幕、英文副字幕、真实产品/工程/智能体证据画面、
四个独立章门和四种专属章门声效均已合成。视频轨为 `54,000` 帧；当前仍须经过项目所有者 1× 连续审片，且没有接入音乐，因此不能称为
最终母版或已授权发布版本。

大体积本地产物位于：

```text
artifacts/project-causality/2026-09-19-r5/
├─ project-causality-30m-nomusic-picture-lock.mp4
├─ project-causality-30m-nomusic-picture-lock.video.json
├─ project-causality-30m.manifest.json
└─ qa/
```

视频 SHA-256：`DBDB9F5B6C3A57401405D0E10B427E3B76BCD6529247181C7C7D4F0656E07913`。完整机器可读记录见
[`build-records/2026-09-19-r5.json`](build-records/2026-09-19-r5.json)，人工接力步骤见
[`owner-review-handoff.md`](owner-review-handoff.md)。

## 可复现输入

- [`radio-script.json`](radio-script.json)：31 个宏段、86 个实际旁白 cue，精确覆盖 1,800 秒；
- [`structure.json`](structure.json)：30 个论证段与结尾的宏观时间合同；
- [`chapter-gates.json`](chapter-gates.json)：四个 20 秒章门、主题宣言与声效绑定；
- [`sfx/`](sfx/)：由 `tools/generate_project_causality_chapter_sfx.py` 确定性生成的四个 PCM 声效；
- [`music/suno-score-plan.md`](music/suno-score-plan.md)：项目所有者手动生成配乐时使用的六轨接力单。

构建入口：

```powershell
py tools/generate_project_causality_chapter_sfx.py
py tools/build_project_causality_30m.py `
  --manifest-output artifacts/project-causality/2026-09-19-r5/project-causality-30m.manifest.json `
  --output artifacts/project-causality/2026-09-19-r5/project-causality-30m-nomusic-picture-lock.mp4 `
  --work-dir artifacts/project-causality/2026-09-19-r5/work
```

构建器只读取冻结素材并生成本地候选，不启动 CK3、不操作 Suno、不上传媒体。

## 后续顺序

1. 项目所有者以 1× 连续观看无音乐 picture lock，按时间码给出必须修改项；
2. 项目所有者按 Suno 接力单手动生成并交回候选音轨与权利信息；
3. 后期只在锁定画面上完成选曲、裁切、ducking、响度和峰值控制；
4. 音乐接入后重新做一次完整连续审片；
5. 外部上传与发布仍需另行明确授权。

8:20 无音乐版本继续保留在上级目录，只作为预告与早期构建管线验证，不再承担体系正片职责。
