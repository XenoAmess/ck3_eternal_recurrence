# 战争系列第二期视频和机制研究交接

2026 年 10 月 2 日，由本轮执行者 `/root` 写给接手同事。第二期 a09 已重制并放入指定 OneDrive 目录，客户端显示同步完成；尚未取得人工按正常速度完整观看和听审签核。接手后先审当前成片，再处理有明确证据缺口的机制。用户随后询问下一期 20–40 分钟的选题，讨论被交接指令打断，第三期尚未定题或开工。

本文记录的是本机接续工作所需的入口。小型文案、脚本和报告随独立分支保存；大体积视频、原始素材、存档和失败 attempt 留在本机，不能只克隆 Git 就认为素材齐全。机器可读的文件清单见同目录 [交接清单](2026-10-02-war-episode02-inventory.json)。

## 分支和操作约束

用户明确要求在本机保持独立分支，在其允许合入前，禁止拉取或合入 master。根目录 `AGENTS.md` 的一般主线开发约定不能覆盖这条指令。冻结 master 基线为 `c69260e65b63bf8f8b8ae42e3aee8f2a68561660`；不要 fetch/pull master、merge/rebase master、cherry-pick 或复制冻结点之后的 master 内容，也不要向 master 推送本任务。

| 用途 | 本机工作树 | 独立分支 | 交接前精确提交 |
| --- | --- | --- | --- |
| 视频文案和制作 | `C:/w/e2gold1001` | `codex/war-series-brown-gold-20261001` | `8306ce103bf3374765c81427a297453ac0d181ec` |
| 机制研究结论 | `C:/w/e2research1001` | `codex/war-e2-mechanism-closure-20261001` | `c4e87182397e19ccb4112617bde13168d96eb50d` |
| R0148 采集冻结源码 | `C:/w/e2cap1001i` | `codex/war-e2-identifier-append-capture-20261002` | `431461d6841604ebd19e65670661ca2a732dbff8` |

上述三棵树在交接检查时均无真实脏项。Windows 深路径证据较多，Git 命令必须带 `-c core.longpaths=true`；未开启时可能显示虚假的文件删除和目录过长警告，不能据此清理、恢复或提交证据。本次交接提交和推送只针对视频独立分支；研究树与采集冻结树保持原样。

全项目执行根目录 AGENTS 的 Windows shell 禁令。命令使用 Python 的 `subprocess` 参数数组，或明确选择 `cmd.exe`。不要把主工作树 `D:/workspace/ck3_eternal_recurrence` 当作本任务编辑目录，它还有其他任务的未跟踪文件。

本轮没有启动游戏或更改 Steam 状态。后续实机仍须先查看当次新鲜 Steam 离线原图、取得本机屏幕和 CK3 排他资源，并按当前原生采集合同分配新 run。旧离线截图、旧 cleanup 回执与任务总线 stale 状态都不能证明当前现场可占用。坐标和键盘输入遵守根指南及 `docs/desktop-coordinate-mapping.md`。

## 当前供审阅成片

交付文件为 [第二期 a09 视频](C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-War-AI-Episode02-BrownGold-BGM-20261002-a09.mp4)。固定交付目录已经获用户授权，后续仍只放入用户指定的视频文件，由 OneDrive 桌面客户端同步；不要上传源码、素材目录或报告，也不要下载其他云端文件。

| 项目 | 精确值 |
| --- | --- |
| 原始交付版 | `C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-copy-bgm-20261002-a02/native-build-attempt-01/CK3-War-AI-Episode02-BrownGold-BGM-20261002-a09.mp4` |
| 文件大小 | 247,708,305 bytes |
| SHA-256 | `BA2E27878FD19D04667ECE628945B25E6C6C340E0C5844214CE43C2C2D07AD6D` |
| 时长 | 1911.3 秒，即 31 分 51.3 秒 |
| 格式 | 1920×1080，30 fps，H.264；AAC 48 kHz 双声道 |
| 内容 | 六章，177 句中文旁白，中英双语烧录字幕，棕金配色 |
| 同步结果 | `CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED`；客户端 InSync、全尺寸 validated、modified 为零；没有独立远端字节回读 |
| 人工审阅 | 未进行完整 1× 观看或全片听审，没有 signoff |

六章依次为开场、追击三日、骑士事件、增援入账、终局与战争账本、结语。各章包含独立回放，不能把跨回放数字剪成一场连续战斗的因果链。

本次同时完成文案和媒体重制：原稿 167 句逐句审计，修订 90 句、保留 77 句、新增 10 句，形成 177 句；制作时生成 100 句新配音、核验复用 77 句旧配音，更新 98 张图卡。最终又在新 run 中修正一张 175% 教学示例标签，复用其余 24 段，重编码一段后重新混音和检查。旧 a08 和首个 a09 候选均保留。

193 项机器检查通过，包括完整音视频解码、尺寸、章节、时长、177 句素材和来源、字幕行数及削波检查。执行者实际查看了最终视频的 33 张抽样帧、9 张拼图；原始死亡通知显示与消失也在抽样中。它们不是人工全片验收。音频均值 −22.1 dBFS、峰值 −3.1 dBFS；没有声称这些数值证明听感已合格。

仓库内 [制作报告](../../promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a09-video-bgm-20261002/production-report.json) 与 [制作摘要](../../promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a09-video-bgm-20261002/delivery-summary.txt) 是当前交付状态入口。`final-artifact.json` 的原始状态字段仍为生成时的 `pending-machine-and-human-review`，不覆盖历史字段；后续机器检查与同步结果以各独立报告为准。

## 系列配色和背景音乐

用户已明确要求战争系列统一棕黄色，不能回到 promo 默认蓝色。真实游戏界面保持原始像素，说明卡和周边版式使用棕金系列风格。

唯一使用的系列 BGM 为 **Quiet Courtly Tension**，直接复用此前战争系列保留的原 WAV：

```text
D:/workspace/ck3_native_war_ai_promo_work/v5-theme-film-attempt-001/run/artifacts/raw/sha256/FD/FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F.wav
```

其大小 30,726,160 bytes，SHA-256 为 `FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F`。系列约定在 `promo/ck3_native_war_ai/build-records/v5-theme-fullfilm-20260924-r1.json`。

实际混音沿用原系列政策：旁白 0 dB、音乐 −17 dB，循环覆盖全片，片头 2 秒淡入、片尾 8 秒淡出，不作自动归一化或动态 ducking。20 个窗口对“最终 AAC 减去独立解码旁白”与精确源音乐作信号比对，全部通过，最低相关系数约 0.9981；完整解码的三个音轨仍在最终 run 的 `audio-proof/`。检查记录见 [真实音轨音乐比对](../../promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a09-video-bgm-20261002/music-presence.json)。后续版本必须实际混入音乐并检查最终音轨，不能仅写一个 BGM 配置字段。

## 机制研究完成范围

研究对应 CK3 1.19.0.6，Steam build 23530548，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。接手时这只是已保存的研究身份；开始新采集必须重新核对实际 bytes 和版本。

R0148 的“六项 100%”只指指定原版受控击杀案例：victim 33437 图尔吉塞、killer 34120 阿姆鲁、Combat 16777218、1066.12.29 → 12.30。六项包括次日人物页、完整名单变化、完整战斗窗、骑士选择器、唯一相关死亡路径、13 域可变状态链。它不代表战争机制全域完成，也不关闭非零掩护或所有成长条件。

| 问题 | 当前结果和边界 |
| --- | --- |
| 骑士次日状态 | 原图显示图尔吉塞存活标记变死亡标记、有效勇武 4 → 2；阿姆鲁威望 301 → 451。两侧 tooltip 数量 11 → 10、19 → 19。人物名单、原生 active entries 69 → 68 是不同口径。 |
| 选择器和死亡因果 | 原候选 19 项及筛选后 14 项已核对，实际 index 8 选中阿姆鲁。本受控窗口的相关 request/enqueue/commit 各一次；唯一性只覆盖这条相关路径。复算 draw 值不能说成直接采到的字段。 |
| 可变状态链 | 13 域区分实际写入、相关支路未执行和保存端点；不能由前后相等推断全天没有写入。当前空成长分支没有成长写。 |
| 增援完整同帧 | R0149 从 D11 独立冷载，1066.12.14 → 12.15，补齐日期、暂停、完整战斗窗、底部构成和相对军力 tooltip。面板人数 893/1603 → 827/4106，tooltip 另一个口径 827/1546 → 740/4047，最终战宽 1480 → 2220；不同口径、hook 时刻与暂停 UI 时刻不得混写。 |

研究结论入口是本机 [R0148 六项结论](C:/w/e2research1001/docs/ck3-native-ai/episode02-r148-six-gap-closure-2026-10-02.md) 和 [R0149 增援同帧结论](C:/w/e2research1001/docs/ck3-native-ai/episode02-r149-reinforcement-full-frame-2026-10-02.md)。两份文档已在研究独立分支提交；不要为读取它们合入任何分支。

精确原件分别在：

- `C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-12-identifier-append-safe/R0148-six-gap-finite-case-semantic-closure-a01.json`，172,344 bytes，SHA-256 `17751A015324D4F995D0F5B9668F9EFE5B70784230A9C9F62CD6622E764E6091`。
- `C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0149-actual-join-control-audit-reinforcement-a01/R0149-finite-reinforcement-facts-a01.json`，21,669 bytes，SHA-256 `A91B333219864C161999FE74D4C6040B05A9EBCBA2D9BB3D9E8C1EC6C3D19819`。
- `C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-13-reinforcement-full-frame/R0149-root-finite-capture-completion-a01.json`，记录实际收尾与原 cleanup RED 的区别。

原 bundle/global readiness 的 false、未发布字段、过期 claim 的 `unresolved_red`、早期 UI/导入/入口错误和失败 stdio 均保留。有限案例根结论另行追加，不覆盖历史 RED，也不把它投影成完整自动游玩循环。

## 四项文案调查和未完成机制

四项调查已落在 [调查说明](../../promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a09-copy-audit-20261002/four-question-findings.txt) 和 [逐句证据稿](../../promo/ck3_native_war_ai/episode-02-battle-second-half/project/review-story-a09-story.json)。其中“未生成新视频”等表述属于文案审计完成时的历史状态，当前成片以本交接的 a09 制作记录为准。

1. **非零败方掩护仍缺实机跨日对拍。** 已有静态原版公式、整数算序和离线向量，已有三次零掩护追击对拍。至少还需 `0<S<P` 与 `S>P` 两组败方有效掩护和软伤均非零的真实案例，采同帧两侧有效属性、修正、征召兵和兵士冻结池、存储顺序，再核对原版预算、逐团写回、次日软伤和可读硬伤。胜方 screen 非零不能替代败方 screen；不可读硬伤保持缺失。具体采集合同见研究树 `docs/ck3-native-ai/pursuit-screen-nonzero-branch-contract-2026-09-27.md`。本片 p030/p030a/p030b 已明确说明缺口，没有新采到这一分支。
2. **骑士战斗力公式已补入成片。** 若百分比为 `E`，倍率是 `E/100`；伤害属性为有效勇武 × 50 × 倍率，坚韧属性为有效勇武 × 10 × 倍率。属性不是每日击杀人数。175% 的每点勇武示例明确标“原版静态公式”；旧 039→040 同源案例再用有效勇武 11 → 7 验算伤害 962.5 → 612.5、坚韧 192.5 → 122.5，不能说这些就是 R0148 的人物数值。
3. **47032 已具名。** 历史同源存档和原版本地化绑定 47032 = Muhammad / 穆罕默德、34333 = Geoffroy / 若弗鲁瓦；本轮图尔吉塞 33437、阿姆鲁 34120 则来自 R0148 人物页。不得仅凭同名把另一人物页绑定到历史 ID。
4. **成长分支已展开，非空写回仍为静态证据。** 原版选定击杀者后给威望、执行成长抽签，再写战报和请求死亡。三项基础权重 60/30/10 对应空条目、基础勇武 +1、剑术大师成长；权重受学识、王朝、教育、特质和文化条件修改，满级剑术大师项归零，不能当作固定概率。剑术大师项在无特质时添加，在已有且经验不足 100 时加 10 经验；阈值 50/100 对应等级，经验 +10 不是勇武 +10。历史实采 40/30/15 总和 85 与本轮空条目分开讲；本轮没有新采非空成长写回。后续玩家领主功绩分支本轮未执行子效果。

其他仍未闭合的范围包括未来增援到达、主动撤退决策、其他人物成长条件、trait-track 非零保存比例、家族关系 guard 的具体失败子条件、其他战争理由的完整计分和整场胜率。它们不是上述六项有限案例关闭的必要补丁，不要重新打开已验证六项或把所有范围并成一个百分比。

## 制作文件和重跑入口

项目目录为 `C:/w/e2gold1001/promo/ck3_native_war_ai/episode-02-battle-second-half`。当前文案提交是 `d9de6c15bfbb3085dd385fa4abd93017654fcf55`，成片脚本和检查记录提交是 `8306ce103bf3374765c81427a297453ac0d181ec`。

| 文件或目录 | 用途 |
| --- | --- |
| `project/full-narration-zh-a09.txt` | 完整中文稿 |
| `project/full-narration-zh-en-a09.txt` | 完整中英文稿 |
| `project/review-story-a09-story.json` | 177 句、逐句事实来源、画面用途和范围 |
| `project/review-story-a09-project.json` | checked-in ProjectConfig |
| `evidence-a09-copy-audit-20261002/` | 四项调查、原版脚本摘录、167 句前后审计和字幕预检 |
| `evidence-a09-video-bgm-20261002/` | 当前机器检查、音乐证据、帧抽查、OneDrive 回执、保全及 pending review package |
| `compose_copy_bgm_a09.py` | 新 run 准备、最新正式 wheel 核验、配音、章节和干旁白母片 |
| `boards_copy_a09.py` | 新文案图卡和真实 UI 来源使用 |
| `native_mix_a09.py` | 正式 CLI composer，实际系列 BGM 混音 |
| `finish_copy_bgm_a09.py` | 混音、完整解码检查、音轨比对、抽帧、review package、原生完整性 audit 和保全 |
| `refine_copy_bgm_a09.py` | 本次第二个 run 的单卡标签修正及其余精确字节复用 |
| `record_copy_bgm_a09.py` | 记录实际有限帧审阅和最终交付事实；quality 阶段只能在实际审阅后调用 |

主解释器明确使用 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，Python 3.14.7。视频 worktree 没有自己的 venv；不要默默回退到裸 `py`。本次 run 查询确认的正式工具链为 `xar-promo-toolchain 0.2.1`，wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，实际版本与依赖记录在最终 run 的 `sources/environment.json`。这只是当次版本；每次后续新 run 都应重新查询最新正式 GitHub Release、必要时更新精确 requirements、验证解释器、版本和实际 `--help`。不要为重用本说明强制降级。

方法 Skill 位于 `D:/workspace/xar_promo_toolchain/codex-skill/promo-video-pipeline/SKILL.md`；正式运行使用安装的 wheel，本地 skill 不是运行时。现有 composer 调用正式 `xar_promo plan/build`，不得把 library API 编造成 CLI 命令。项目 entry point 使用私有树 `promo/ck3_native_war_ai/integration/src` 的实现，不能无意改从主工作树导入后续 master 代码。

完整运行资产在：

- 最终 run：`C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-copy-bgm-20261002-a02/`。
- 首个 a09 候选：同级 `episode02-brown-gold-copy-bgm-20261002-a01/`，保留原 175% 标签和首次整片制作。
- a08 历史输入：同级 `episode02-brown-gold-research-20261002-a02/`。
- 命令执行、失败和成功 wrapper：`C:/Users/1/ck3-e2-copy-bgm-20261002-a01/`。
- 文案审计过程：`C:/Users/1/ck3-e2-copy-audit-20261002-a01/`。
- 待人工审阅包：最终 run 下 `pending-human-review/review-package.json` 和 `review-template.json`。
- 最终 run 下 `native-run/run-manifest.json`、`retained-process-index.json`、`closed-process-index.json`。封存索引记录两个候选和已结束 wrapper 共 3299 个文件，原始素材不删除。

新修改必须建立新的 run/workdir、冻结新配置和脚本字节，保留旧素材、failed attempts、partial、TTS、音轨、字幕和日志。现有 helper 的路径、输入、计数以及只创建文件的约束是针对本次 attempt；不能不改参数直接复跑，更不能覆盖旧目录。复用素材应核对原来的 bytes/SHA。

## 接手后的优先事项

1. 对精确 a09 文件完成正常速度的全片观看和听审，检查 BGM 可听度及循环接缝、长公式段节奏、字幕和真实 UI 可读性。只有实际完成后，才能用正式工具链记录人工 signoff，绑定上述最终 bytes/SHA；修改任何媒体字节都需要新的审阅记录。
2. 如果发现具体问题，在新 run 最小修正，继续沿用棕金风格和系列 BGM，再做与改动相称的媒体检查和单个 MP4 的 OneDrive 交付。无需重跑无关的已通过研究，也不要将当前供审阅片写成正式外部发布。
3. 优先补非零败方掩护的两类原版跨日样本；如果要把非空成长当成实机展示，再分别取得勇武 +1 和剑术大师添加/经验写回的前后原图、trace 与保存端点。静态说明可以继续使用，但证据层次要保持明确。
4. 继续回答用户关于下一期 20–40 分钟的选题问题。下面只是接手者可呈给用户的建议，未得到选题确认，不承诺已启动制作或交付日期。

## 下一期的待定建议

建议主题为 **围城怎样把一场胜仗变成战争胜利**，目标约 33 分钟。第二期已经讲到单场战斗写入战争账本、战争仍未结束，第三期可以接续一个真实战争和同一个战争理由，从战争面板出发，跟踪围城与结束条件，最后回到玩家如何判断下一步行动。

| 预计时间 | 章节和待取得证据 |
| --- | --- |
| 0–3 分钟 | 承接第二期，展示战斗结束后仍在进行的战争和完整战争面板 |
| 3–10 分钟 | 分解该案例的战斗、占领、战争目标和俘虏贡献；先核对原版规则、上限与取数口径 |
| 10–20 分钟 | 一段完整围城案例，解释城防、守军、进度、阶段结果或攻城选择，以实际前后读数为准 |
| 20–25 分钟 | 围城结束如何改变占领、俘虏和战争分数，用同一保存链复算 |
| 25–30 分钟 | 原版强制要求、议和可用性与战争结束后的真实变化；其他战争理由明确留出边界 |
| 30–33 分钟 | 汇总本次可用的判断流程、已验证结论和下一组待验条件 |

这是叙事提案，不是已有研究成果。先确认可采的战争理由和围城案例，列出每句拟讲机制的原版定义、原生读数、UI 与保存端点，再做文案和视频。若关键案例取不到，应缩小范围或重新提议主题，不能用重复第二期骑士解释凑时长。

整个系列后续继续保持棕金配色、Quiet Courtly Tension BGM、中文主旁白和双语字幕，以及独立分支、先证据后文案的流程。时间节点应在接手者确认现场、案例和依赖后给出，本轮没有作出新的日期承诺。
