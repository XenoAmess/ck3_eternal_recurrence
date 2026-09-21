# Project 因果律 r12 无音乐候选版

r12 是当前用于所有者审片的 1440p 长版候选。它把每个核心章节组织成同一条闭环叙事：先让非工程观众听懂价值并看到直观结果，再完整保留工程实现与证据论证，最后用新的价值结论和行动方向收束。`Why / What / How` 只存在于幕后编排，不作为画面标签或旁白术语出现。

## 成片

- 本机路径：`artifacts/project-causality/2026-09-20-r12/project-causality-r12-owner-voice-nomusic.mp4`
- 时长：`50:27.639`
- 画面：`2560×1440`、30 fps、H.264、yuv420p
- 声音：所有者授权声线、AAC、48 kHz、双声道、`-15.9 LUFS`、true peak `-1.5 dBFS`
- 字幕：简体中文烧录；MP4 内含可选择的英文 `mov_text` 字幕轨；另输出英文 SRT
- 章节：7 个容器章节与 YouTube 时间码
- 音乐：未加入；按所有者要求继续后置
- SHA-256：`BB1CFD1AC6C286806205CD77053F6503F93C9B80EB61464A561DDF1620A50CC1`
- 状态：本地 publication candidate；尚未授权外部上传

48 kHz 是本项目既有媒体合同，不是声称“高于 48 kHz 一定不合规”。IndexTTS 本轮原始输出为 22.05 kHz；将它封装为 96 kHz 只会上采样，不会产生新的声音细节。48 kHz 用于统一视频、音效、旧素材和交付工具链。

## 当前结构

| 时间 | 内容 |
|---|---|
| 00:00 | 开场：为什么需要 Project 因果律 |
| 01:59 | 咒：今天已经可以使用的产品 |
| 12:20 | 罗贝尔：从稳定 CK3 主菜单开始的连续自主游玩 |
| 21:15 | 术：一条改动怎样走到发布 |
| 33:20 | 道：什么才算真的完成 |
| 39:37 | 辉煌愿景：四个无限演进 Loop |
| 49:37 | 从这里开始：已有 Mod 与新创作者 |

四章各自拥有独立的章末闭环：

- 咒：从功能清单升华为可延续的创作能力；
- 术：从工具组合升华为可控、可追、可复现的修改；
- 道：从规则顺序升华为可被下一位维护者继承的可信度；
- 辉煌愿景：从自动化升华为把人的判断放到更高处。

## 罗贝尔连续实机

`robert-mcp-showcase-main-menu-continuous.mp4` 来自 R30 原始母带的连续时间区间。首帧是真实 CK3 主菜单，并编辑性停留三秒；此后画面按原始时间顺序进入新游戏、1066 选人、罗贝尔新局、开局读取、动态择敌、宣战、集结、行军、胜利核验与后续防御战争。没有游戏过程跳切、倒序或人为加速。

这段证明本局真实发生的能力，不补拍本局没有出现的事件选择，也不把 ACK 冒充游戏状态。实机之后继续保留 exact build、ABI、War ID、target ledger、OODA 与 production-live evidence 的工程说明。

## 可复现构建

先生成 r12 动态视觉与发布图：

```cmd
py tools/build_project_causality_r12_assets.py
```

本机使用独立宣传工具 checkout 和共享工具 venv：

```cmd
set XAR_PROMO_SOURCE=Z:\workspace\xar_promo_toolchain
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe ^
  tools\build_project_causality_r12.py ^
  --robert-edit promo\project_causality\r12\robert-continuous-edit.r30-main-menu.json ^
  --render --preset fast --crf 18
```

新增或改写旁白尚未进入缓存时，改用 IndexTTS venv 并加 `--synthesize`。构建器按 cue id 与文本 SHA-256 复用已授权语音，不改变语速；整片上限为 3600 秒。

## 相关文件

- `edit-config.json`：114 个 cue 的权威编排、文本覆盖、视觉覆盖与 60 分钟合同；
- `custom-showcase.json`：新增直白入口、实机后工程深潜、具体流程和四章价值回环；
- `robert-continuous-edit.r30-main-menu.json`：连续母带的无间隙语义分段；
- `publication-package.md`：标题、简介、章节、置顶评论与发布检查；
- `technical-index.md`：术语、证据、素材与能力边界索引。
