# 导演案如何进入现有 promo 工具链

第 1 集 R3→R5 的数值、证据、画面与交付复盘已整理为 [CK3 原生战争机制视频制作门禁](../docs/ck3-war-ai-numeric-video-lessons.md)；后续新集在句稿冻结和成片交付前按此核对。

## 2026-09-24 当前配乐制作入口

第 0 集 V5 以 V4 已完成的 IndexTTS 画面与旁白母版为输入，使用项目脚本 [`war_ai_promo/theme_mix.py`](integration/src/war_ai_promo/theme_mix.py) 调用正式 xar-promo 0.2.1 的 `AudioMixSpec/plan_audio_mix`，只复制原视频流并重混 AAC 音轨；没有重拍或改变原生机制结论。`start-run` 的配置快照、原曲 WAV、源片、脚本、混音命令、成片、媒体探测、审阅尝试和 OneDrive 回读保存在独立的 `v5-theme-film-attempt-001/`。V4/V5 编码视频包和时间戳完全一致后，V5 原生 review 的重复抽帧尝试保留为不完整状态；项目级审阅通过这一逐包等价证明继承 V4 的 106 张真实帧，并单独绑定新音轨的完整解码证据，不把继承包冒充原生 `review` GREEN。每次未来制作前仍按根 AGENTS 查询最新正式 Release，届时版本可能不同，不能把 0.2.1 当永久要求。

[全系列唯一主题音乐规则](series-roadmap.md#全系列唯一主题音乐)绑定用户提供 WAV 的 SHA-256。后续新集也只用这首原曲，旁白保持 0 dB，音乐使用静态 -17 dB 起始设定，关闭 ducking 与 `amix` 自动归一化；循环、首尾淡化及任何调整都写入该集独立 run 和构建记录。片长、证据门与用户审片仍按各集要求处理。[V5 构建记录](build-records/v5-theme-fullfilm-20260924-r1.json)与[合集概念图记录](build-records/series-concept-20260924-r1.json)是本阶段准确状态；下文较早的“未执行”“尚待制作”只反映 2026-09-22 初案时点。

## 2026-09-22 开始制作

当前运行入口已实现于 [integration](integration/pyproject.toml)，实际配音、项目 composer 和样片进展见[制作记录](production-stage.md)。下文未实现接线的描述记录导演 authoring 阶段；不能用它否定后续样片，也不能把单章样片反写成当时已经完成的事实。完整影片仍待制作和审片。

## 现行长篇方案

用户选择 **20–40 分钟宽松片长**。当前消费入口是 [longform/director-plan.md](longform/director-plan.md)、
[longform/shot-list.md](longform/shot-list.md)、[longform/timeline.json](longform/timeline.json) 与根目录 `promo-project.json`。
三案例、8 章采用约 30 分钟的参考编排；45 个镜头组可随句稿拆并。参考 1800 秒不生成精确成片帧数门，也不作为剪辑必须填满的长度。
ProjectConfig 的 `duration_limit_seconds=null`，不把 40:00 另立为逐秒硬门。1200–2400 秒的工作范围与 1800 秒参考值写在本片 timeline 中，
`range_policy=soft-editorial`；最终由实际口播与画面决定，不为轻微边界偏差损害表达。

本轮新建 `D:/workspace/ck3_native_war_ai_promo_work/longform-director-20260922-r1/`，按原生 `start-run → preserve → validate` 封存当前输入，
运行索引见 [longform-director-20260922-r1.json](build-records/longform-director-20260922-r1.json)。知识源仍按原 source-lock 的 commit/字节冻结，
不把其他任务后来更新的文档悄悄套进旧结论。新增研究另立方案和证据，按需更新之后的 claim/run。

## 当前版本政策（2026-09-22 更新）

项目所有者已明确要求 **`xar-promo` 永远使用最新版本**。每次工具链任务或新 run 前查询独立仓库最新正式 Release，更新 requirements
的精确 URL/SHA 并安装验证；不再按旧指南停留 0.1.0。本次在线确认最新正式发布为
[v0.2.1](https://github.com/XenoAmess/xar_promo_toolchain/releases/tag/v0.2.1)，隔离 venv 已升级并通过本片 ProjectConfig 与既有 run 的完整只读验证，
记录见 [版本更新收据](build-records/toolchain-latest-policy-20260922.json)。此处的版本号只记录本次查询结果，后续仍重新查最新发布。

下面的 `director-20260922-r1` 表格记录升级前的真实历史；旧 run、快照和封存素材保持原样。当前目录的工作流说明按本节执行，后续新
run 使用届时最新版本，不把历史版本记录当作安装要求。

## director-20260922-r1 已采用的边界（历史记录）

本目录沿用 `promo/reclaim_the_motherland/` 的原生 ProjectConfig/run 结构与 `promo/project_causality/` 的导演、分镜、时间线、声明来源分工。通用实现仍在独立 [xar_promo_toolchain](https://github.com/XenoAmess/xar_promo_toolchain)；本目录只保存本片意图、内容与运行索引。

本次使用项目指向的 [promo-video-pipeline SKILL.md](../../../xar_promo_toolchain/codex-skill/promo-video-pipeline/SKILL.md) 工作流，以及其 workflow、manifest、CK3 capture adapter 参考文档。这个相对 Skill 链接对应本机并列 checkout；跨机器操作请在独立仓库的相同路径读取。读取独立仓库时 HEAD 为 `adb52f4404d21072f13762dc4e674e75e2c63a9b`，其 README 已描述 0.2.1；本案实际命令以以下安装版本及该版本 `--help` 为准。

| 项目 | 本次记录 |
| --- | --- |
| 隔离工作区 | `D:/workspace/ck3_native_tree_docs_audit_20260922` |
| 创建依据 | 最新远端 master 在本次任务开始时的 `68459f225270f138345785572d31ef9f722f3cae` |
| 当前解释器 | `tools/.venv/Scripts/python.exe`，Python 3.14.7 |
| 解释器来源 | 明确使用主工作区 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 创建本工作区 venv |
| 实际工具版本 | `xar-promo-toolchain==0.1.0`，GitHub Release wheel；本次只需标准库核心 authoring 功能 |
| wheel SHA-256 | `39afc58f724e75398f6727d3d36f1b184a89f3febff66de193a2f5c4889c1f0f`，来自安装包 direct_url 记录 |
| 版本差异 | 主 venv 和 `tools/requirements-promo-toolchain.txt` 已为 0.2.1，根 AGENTS 的冻结合同仍要求 0.1.0。本案隔离安装 0.1.0；未改主环境或全仓依赖 |
| 本次 run | `D:/workspace/ck3_native_war_ai_promo_work/director-20260922-r1/run-manifest.json` |
| 达到的阶段 | authoring config/run 的完整文件与哈希验证、导演输入与研究来源保全 |

首个 run 没有使用 0.2 的新 capture receipt、claims-review 与多音轨 API。后续制作按上方最新版本政策执行，在新 run 记录实际依赖和项目集成验证，再采用对应 API；导演内容与旧 run 的历史事实保持原样。

## 文件的消费关系

```text
longform/director-plan.md + shot-list.md        导演/拍摄意图（同一 longform 目录）
                 |
longform/timeline.json + 根 claims/source-lock 本片时间预算与来源
                 |
promo-project.json                            通用 ProjectConfig，8 章 planned
                 |
start-run -> config snapshot -> preserve       本次实际完成的 authoring 保全
                 |
未来项目 composer + 已绑定素材                 制作阶段才接入
                 |
plan -> build -> audit -> review -> signoff -> export
```

`longform/timeline.json` 与 `claims.json` 是本片自己的编辑输入，不能直接冒充通用 review storyboard 或 0.2 的 claims-review schema。逐句稿尚未冻结，ProjectConfig 的 cues 为空；八章均为 `planned`，artifact_ids 也没有填写不存在的片段。后续 composer 把已完成的句稿、字幕、时间和素材投影成实际工具接口需要的对象，并按真实音频重算最终时间线。

## 13:30 初案命令记录（历史）

以下从本仓 worktree 根目录运行，使用 cmd 或 Python subprocess。创建本次 authoring run 时实际调用了同一组命令，完整 argv/stdout/stderr 与结果见 [run 索引](build-records/director-20260922-r1.json)。

```text
tools\.venv\Scripts\python.exe -m xar_promo --version
tools\.venv\Scripts\python.exe -m xar_promo --help
tools\.venv\Scripts\python.exe -m xar_promo validate promo\ck3_native_war_ai\promo-project.json --json
tools\.venv\Scripts\python.exe -m xar_promo start-run promo\ck3_native_war_ai\promo-project.json --run-id director-20260922-r1 --run-directory D:\workspace\ck3_native_war_ai_promo_work\director-20260922-r1
tools\.venv\Scripts\python.exe -m xar_promo preserve promo\ck3_native_war_ai\director-plan.md --run-manifest D:\workspace\ck3_native_war_ai_promo_work\director-20260922-r1\run-manifest.json --artifact-id director-plan-v1 --collection raw --role director-plan --media-type text/markdown
tools\.venv\Scripts\python.exe -m xar_promo validate D:\workspace\ck3_native_war_ai_promo_work\director-20260922-r1\run-manifest.json --json
```

已有 run 不覆盖；改稿使用新 run ID 和新目录。实际封存还包括镜头表、时间线、声明表、来源锁定表、工作流、研究文件和本次检查记录。每次保全后验证 config/run。索引文件在 run 完成后生成，不进行自引用哈希绑定。

## 制作阶段的具体接入任务

| 层 / 入口 | 本片需要做什么 | 当前状态 |
| --- | --- | --- |
| 项目 preset | 读取 20–40 分钟工作范围、画幅、字幕安全区、标签、声线、逐句稿与音乐安排；预留 ID `ck3-native-war-ai-longform-zh-v2`；最终时长跟随真实句稿/音频 | 意图已写；注册 factory 尚未实现 |
| 项目 adapter | 预留 ID `ck3-native-war-ai-v1`；读本片素材索引，分清示意图、实机说明画面、自然 AI 个案与 fixture；校验 claim 与实际证据关系 | 尚未实现，无已绑定录像 |
| 通用 CK3 adapter | 有合格既有 capture bundle 时调用 `xar_promo.adapters.ck3.load_capture_bundle` 验证 report/index/timeline/raw/marks/clean spans | 已读合同；本次没有提供或加载 bundle |
| 项目 composer | 在本目录 `integration/` 提供真实可 import 的 `PipelineComposer`，消费已绑定输入，委托通用 TTS/媒体/保全功能；声明实际 module:attribute | 尚未实现，不填写假的 composer 路径 |
| `plan` | 注册 adapter/preset 且 composer 可 import 后，以显式 `--composer` 检查只读编排；计划目录不能创建，也不能调用 provider | 未执行；本案完成不等于 plan GREEN |
| `build` | 新 run、新 workdir，调用明确 composer；保留 TTS 请求、音频、字幕、章节段、拼接输入、stdio、partial 与失败 attempt | 未执行 |
| `audit` | 对已 preserve 的成片和真实 evidence bundle 作自动检查；本片负责规则/例证对应的语义判断 | 未执行 |
| `review` | 实际成片先用公开 `probe_and_write_bound_media` API 生成精确字节绑定的 probe，再产生 pending-human-review 包；显式 preserve 全部审片材料 | 未执行 |
| `signoff` | 所有者实际 1× 连续观看后，记录姓名、决定、说明与精确成片 SHA；换任何成片字节都重新审阅 | 未发生 |
| `export` | 成片、字幕、来源 sidecar、封面与审计按项目 allowlist 输出新离线 bundle | 未执行；不包含上传 |

通用 CK3 adapter 只读消费已存在的证据，不会录屏或启动游戏。若现有战争素材没有它要求的 capture report/index/clean spans，先将素材如实登记为普通原始视频，再由实际 producer 产出可验证记录；不能给旧素材补造 GREEN 报告。新取材按根 AGENTS 的 CK3 排他、离线、编号与原生观测流程执行。

G2 自动玩家的战略决定、我方 planner 的路线修复和玩家输入录像不能用来证明原生 AI 决策。它们只有在说明界面或结果时才可作为配图，并明确标识操作者及用途。

## 保留与验收

每次录制、配音、渲染或审计采用独立 attempt。`D:/workspace/ck3_native_war_ai_promo_work/` 保留所有原始素材、失败素材、配置快照、命令和中间结果，不清理旧 run。Git 保存本目录的可复现输入和体积小的索引；实际媒体及完整素材库留在工作目录。

本次长篇检查只回答：8 章与 45 个镜头组的参考节拍是否一致、伸缩预算是否对应 20/30/40 分钟、claim/案例/来源是否可回链、通用 ProjectConfig/run 是否可验证且保存了精确输入。它不把参考 1800 秒当实际片长，不回答配音时长、实际画面、成片审美或人工作品批准；这些需要后续实际产物。
