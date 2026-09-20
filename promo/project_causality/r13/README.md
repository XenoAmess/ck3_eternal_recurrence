# Project 因果律 r13：抓人开场审片版

r13 在冻结的 r12 主体前增加约 110 秒冷开场，先回答模组作者为什么需要这套体系，再进入“咒、术、道、辉煌愿景”。主体旁白与罗贝尔连续实机段不改写；音乐仍按项目所有者要求延后处理。

## 冷开场结构

1. 每次修改以后，模组究竟还能不能正常运行？
2. 按钮、事件和版本更新为什么带来昂贵的重复验证？
3. 系统怎样检查模组、启动 CK3、读取状态、决策、打赢战争并留下证据？
4. 已有模组、新创作者与 CK3 本体研究分别得到什么？
5. 当创作、测试、游玩和核验相连，项目能否开始自我演进？

## 创意工坊卡

结尾卡列出仓库体系内 9 项已发布 Mod：

| Mod | Steam Workshop ID |
|---|---:|
| 琉焰卿的永恒轮回 | 3784706360 |
| 白绮特供独立版 | 3787304042 |
| 天朝特色 361 制官员绩效考核 | 3792585972 |
| 牛来 | 3790635143 |
| XenoAmess 的体验优化 | 3798133925 |
| 自动升级建筑（维护版） | 3800124956 |
| 重整河山 | 3798404599 |
| 肃清曼荼罗伪信 | 3797711947 |
| 驱策朝贡国 | 3801490405 |

《牛来》工坊页：<https://steamcommunity.com/sharedfiles/filedetails/?id=3790635143>

## 构建

```bat
set XAR_PROMO_SOURCE=Z:\workspace\xar_promo_toolchain
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\build_project_causality_r12.py ^
  --config promo\project_causality\r13\edit-config.json ^
  --output-dir artifacts\project-causality\2026-09-20-r13 ^
  --new-audio-dir artifacts\project-causality\2026-09-20-r13\work\generated-cues ^
  --robert-edit promo\project_causality\r12\robert-continuous-edit.r30-main-menu.json ^
  --render --preset fast --crf 18
```

冷开场视觉由 `tools/build_project_causality_r13_hook_assets.py` 生成。结尾卡由 `tools/build_project_causality_r12_assets.py --cta-only --force` 生成，r13 复用同一发布卡。

## 当前成片

- 路径：`artifacts/project-causality/2026-09-20-r13/project-causality-r13-owner-voice-nomusic.mp4`
- 时长：52:17.126
- 画面：2560×1440，H.264 High，30 fps，yuv420p
- 声音：AAC 双声道，48 kHz；综合响度 -15.9 LUFS，LRA 4.4 LU，True Peak -1.5 dBFS
- 字幕：简体中文烧录；英语 `mov_text` 可选轨
- SHA-256：`FF2FC4B9F49ED19C851708F2CE0F19D72AEC463550A2DFD19CF015E0828BB089`
- 音乐：无；由项目所有者明确延后

## 验收

- 119 个 cue 全部生成并封装。
- `ffprobe` 确认视频、中文音轨、英语字幕轨和章节数据存在。
- 全片视频与音频完整解码，退出码为 0，未报告解码错误。
- 开场、全片抽帧和结尾抽帧已目视检查；九项工坊条目均在安全区内。
- 构建计划、字幕与审计报告未发现 Unicode replacement character。
- 逐句文案审计覆盖 328 个朗读语义句，报告见 `docs/project-causality-r13-line-audit.md`；按要求仅报告，不改稿。

当前文件是无音乐审片成片，sidecar 仍保持 `publication_authorized: false`，等待项目所有者完成人工复审与后续配乐决策。
