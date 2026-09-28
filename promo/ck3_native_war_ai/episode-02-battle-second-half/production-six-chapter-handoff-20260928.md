# 第 2 集：录制后六章组装交接清单

2026-09-28，屏幕外静态排期。此表按当前正式六章中文稿、已保全的五组 Edge TTS 和正式九卡计算；它不是取用镜头的审片记录，也不是生产 declaration。当前没有一条已经过人工原速审片并封成 CK3 adapter GREEN 的 clean span，没有六章正式 reel 或成片。

## 时长与 7:19.616 画面桥接

工作目标沿用原六章 **29:50.000** 时间格。六章现有语音总长 **22:30.384**；每章目标减去实测语音，是需要在剪辑中以原速游戏画面、可读计算卡、来源标签和转场实际填入的**非旁白时长**。它们不是已经取得的 clean span 秒数，旁白期间也仍需足量画面。最终人审可调整目标，但改动后须重算逐章 reel、字幕与章节元数据。

| 章节 / 暂定时码 | 目标 | 本次语音 | 待填画面桥接 | 其中计算卡独读预留 | 其余原速画面/来源过渡预留 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `opening` 开场 00:00–01:30 | 1:30.000 | 1:17.808 | **0:12.192** | E2-01 身份图 0:08 | 0:04.192 |
| `pursuit` 追击 01:30–07:10 | 5:40.000 | 4:13.824 | **1:26.176** | E2-02/03 0:36 | 0:50.176 |
| `knights` 骑士 07:10–13:50 | 6:40.000 | 5:28.752 | **1:11.248** | E2-04/05 0:40 | 0:31.248 |
| `reinforcement` 增援 13:50–22:25 | 8:35.000 | 5:32.712 | **3:02.288** | E2-06/07 0:54 | 2:08.288 |
| `terminal` 终局 22:25–28:15 | 5:50.000 | 4:29.232 | **1:20.768** | E2-08/09 0:44 | 0:36.768 |
| `closing` 收束 28:15–29:50 | 1:35.000 | 1:28.056 | **0:06.944** | 无 | 0:06.944 |
| **合计** | **29:50.000** | **22:30.384** | **7:19.616** | **3:02** | **4:17.616** |

卡片独读秒数承接旧[编辑预案](editorial-timeline-26-to-28-min-20260928.md)的最低阅读排期，属于**新目标中的占位**，尚未通过本次卡片 1× 可读审看；E2-01/E2-08 是身份或结果画面，并非另两张正式计算卡。不得为满足上表延长静止游戏帧、循环同一镜头或跨 PTS 缺帧处补插帧。录制与成片实际取舍优先由真实可见性、原速端点与人工审片决定。

## 已有的静态输入与共同缺口

- 已有来源：`project/promo-project.json`、`narration-script-draft.md`、六章 `english-subtitles.json`、正式九卡 `cards/calculation-cards.json` 与 SVG；当前三份 A05 追击、A01 增援、A05 终局事实回执均有精确来源门。正式卡是 E2-02/03 **A05**、E2-06/07 **A01**、E2-09 **A05**。旧 004/085/024 卡留在历史侧栏，不进入正式九卡。脚本 SHA-256 `8979B3E72B4C1D58C36428D8A7AE390666E479CBCEF53D22DFB59A5C66F1A699`；正式卡索引 SHA-256 `AF6B27757423E81355DBA965BD867AE43AF12844BC61C22277C9CFCD58429690`。
- 五组原生语音已按各自 source run 保全。外置冻结 `D:/workspace/ck3_native_war_ai_promo_work/episode02-final-narration-20260928-a01/five-group-freeze-root-a01/source-groups.json` SHA-256 `1DFF5D58E874F55673E0963384B45827902C63A81BFD35F5CE0CEF2BB42E80CA`；六章字幕预检 `.../subtitle-preflight-root-a01/subtitle-input-fragments.json` SHA-256 `E37CE884E9BE4D82094133E0D79B3E7306F3044E63037E15EB1919C4C8399AA3`，同目录 `preserve-plan.json` SHA-256 `5F4D6556720453F0BB46193DBAE962780B27309608889E31C3EADF77B38BA253`，共 **82** 条待保全 TTS/Edge/来源原件。中文、英文字幕机器排版审核只证明来源/时间约束，不是人工听审或观片。
- 系列主题曲可从既有本地原 WAV 取用：`D:/workspace/ck3_native_war_ai_promo_work/v5-theme-film-attempt-001/run/artifacts/raw/sha256/FD/FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F.wav`。既有记录为 30,726,160 bytes、SHA-256 `FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F`；正式 declaration 仍要在新 attempt 重新核原件。不要从 OneDrive 重新下载。
- **六章共同尚缺**：每章独立成片 `reel.<id>` 和 `reel-receipt.<id>` 原件的路径/bytes/SHA；每个取用镜头的具体 `attempt_id`、冷载存档、control、raw、完整 ffprobe 与 `recorder-final.json` 精确身份；人工原速审片后的首末真实 PTS、抽帧、`human-review.json`，以及由 `prepare_existing_capture_bundle.py package` 真正产生的 adapter `report.json`、`capture-timeline.json`、`evidence-index.json` 与 GREEN clean-span receipt；每个 span 在最终 reel 中**可见**的来源标签帧及其 audit。正式 `reel-receipt` 要绑定实际 reel SHA、2560×1440/30fps 输出、原 raw 分辨率和上采样/重采样真值，跨 attempt 与跨 raw 的切口要在片中清楚标示。现有 raw 均 1920×1080，不得称作原生 2560×1440 拍摄。
- 每张进入 reel 的正式 A05/A01 卡另需 `ck3-war-ai.episode02.recomputed-card.v1` 回执，精确绑定卡 SVG SHA、正式索引的 primary receipt、该镜头 attempt 与冷载 save；已有卡片事实回执不能直接冒充这个逐 reel 合同。骑士旧研究卡若仍沿用历史 039/040、020、070、036/038，须在**各自 reel** 留下 `历史研究`、`非当前录制`、具体 replay ID 的可见卡标签及 `card-label-audit.v1`。若改拍新同源数字，则先重算卡与稿，再另起 TTS/字幕 run。

## 逐章待取得的声明原件

下面每行最终都应落实到一个单独的 `chapters[]` 条目：`id`、ProjectConfig 标题、实际时长、`reel` 与 `reel_receipt` 的 `{source,bytes,sha256}`。所有 `capture_spans`、卡标签和重算回执所引的 ID 应恰好组成顶层 `source_artifacts`；少一件或塞无关件都由预检拒绝。`opening`、`closing` 虽无正式计算卡，也仍必须含至少一个真正合格的原生 capture span。

每章在**新外置组装 attempt** 至少新增 `reel-<id>.mp4`、`reel-<id>-receipt.json`、取用镜头的 `source-label-audit-<span-id>.json` 及其可见帧原件；这些是建议命名，**目前均不存在**。每条实际 raw 则在其独立 adapter attempt 生成 `source-manifest.json`、首末 `extract-frame` PNG/回执、真实 `human-review.json`、`bundle-receipt.json` 和 `report.json`/`capture-timeline.json`/`evidence-index.json`。封装验证后，再为每个入剪区间单独写与 adapter 三件套及原始 raw 精确绑定的 GREEN `clean-span-receipt-<span-id>.json`；封装器本身不会代写这个审计。卡另有 `recomputed-card-<card-id>.json` 或骑士历史 `card-label-audit-<card-id>.json`；每件最终都要填绝对路径、实际 bytes、SHA-256，不能根据建议文件名猜测身份。

| 章 | 首选取材及当前状态 | 该章的下一项实证 / reel 工作 |
| --- | --- | --- |
| `opening` | A05 a01 的 WarID 4 前态、墨西拿和战斗身份；若使用 E2-02/03 的 A01 a01，需标成**另一独立 attempt**。两者都仅有 `ENCODED_UNREVIEWED` raw。 | 逐帧核地图/身份与 HUD、确定无加载的原速 span；封 adapter bundle；剪 E2-01 身份图、可见来源标签和开场 reel。旧 attempt-005 上下文拼接只可另标历史候选，不能替代原 raw clean span。 |
| `pursuit` | A05 a01/a02 同一冷载会话的第 28–31 日 control 与两段 raw；正式 E2-02/03 卡已绑 A05，A01 追击 raw 不可剪成 A05 同轨。A05 a02 有 271.267–278.833 秒 7.566 秒 PTS 断档，另有较小断档。 | 对 A05 两条 raw 各自选真实 PTS、不跨任何 >0.2 秒 gap；1× 看每日人物/逐团变化，按实际可见画面做 clean spans 和 A05 标签；出 E2-02/03 两份同 attempt 卡重算回执，再剪本章 reel。75203000 是模型复算，不写成原生单独 scalar。 |
| `knights` | E2-04 新 a01 因首次同帧 helper 误判且实际 1.3 倍界面裁切，未取得正式 raw；E2-05 新 a01 虽有同帧身份 GREEN，原始 1920×1080 面板下半仍裁切，未录 raw 或推进日期。039→040、020、070、036→038 仅为多条历史研究轨。 | 先在新 attempt 取得封口且可审的 E2-04/05 原生录像与事件前后同轨证据；分别包装 clean spans。若用旧研究镜头/卡，对 E2-04 和 E2-05A/B/C 四卡分别做历史可见标签 audit，不把 070 的成长 draw 接作 020 的击杀抽签次帧；若换当前 run 数值，先完成卡、中文、英文、TTS 重生。 |
| `reinforcement` | A01 第 11→12 日新独立冷载，`recording-e2-06-d11-a01/raw/e2-06-d11.mkv` 1920×1080、600 秒，已有原生 private trace 和正式 E2-06/07 A01 卡；媒体仍 `ENCODED_UNREVIEWED`。现有 1.3 倍 GUI 下战斗面板底部逐团/战宽 UI 被裁。 | 把这条 raw 加入 adapter `prepare`/原速审片队列；仅把确实可见的上半 UI 作实机镜头。若要呈现下半逐团/战宽可见证据，先以合格 GUI scale 补拍并同轨对证；否则在画面明确使用来源绑定的原生 trace/计算板，不能称为 UI 直接可见。剪 E2-06/07 时给两张 A01 卡各一份 same-attempt 重算回执。 |
| `terminal` | A05 a01 战争前态 + a02 第 32 日 writer/原生暂停后态，正式 E2-09 A05 卡；同一 CK3 会话两段**非连续** raw。a02 后态候选处有事件弹窗遮挡，媒体未审。 | a01/a02 各自独立 clean spans、可见切口标签；a02 的 writer 与后态仅用真正无遮挡且不跨 PTS gap 的段。若战争面板始终被遮，补拍清楚面板，口播仍严格区分 writer 战斗 row −50 与原生暂停后态战争总分 −50。E2-08 结果图和 E2-09 卡需人工可读；E2-09 的 same-attempt 重算回执另建。 |
| `closing` | 可复用前五章**已准入**的同 run 原速片段作回顾，额外新拍预算为零；不可从尚未审阅的旧 004/085/024 素材暗中补镜头。 | 单独剪 1:35 reel，并以至少一条已 GREEN 的原生 span、可见来源标签和真实重复使用范围绑定 receipt；若回顾镜头来自不同 attempt，逐段显式标明。末段 0:06.944 的桥接仍需真实画面或有来源的片尾卡。 |

## 屏幕释放后的执行次序

1. 先核 CK3/recorder 进程清零和屏幕租约释放；每个新媒体 attempt 只用新的外置目录，原 raw、失败 attempt 与旧回执原样保全。每次新工具链 run 先重新查询最新正式 `xar-promo` Release 并记录 wheel/解释器身份。
2. 依[三 raw adapter 队列](three-raw-adapter-queue-20260928.md)逐条 `prepare`、审片、精确首末抽帧、`package`；**A01 增援 raw 另加一条队列**，骑士后续封口 raw 再加队列。A05 a02 的机器 PTS 候选仅用于找窗，[当前镜头账](shot-list.md)与三 raw 队列均明确 7.566/0.767/0.467 秒 gap。任何 PTS 候选、mark、截图、`ENCODED_UNREVIEWED` 不得填 GREEN。
3. 将每个取用 clean span 连同原 raw 1920×1080 身份、字幕/卡、来源分轨逐章剪成六个独立 reel；每个候选 reel 生成实际字节 SHA 与 `chapter-reel.v1` 回执，再在该 reel 的真实帧上作 `source-label-audit.v1`/历史卡 `card-label-audit.v1`。失败重剪创建新 attempt/新 receipt，不能改写旧媒体。正式画幅 2560×1440 需明确记为上采样。
4. 从真实原件逐项填 `production-declaration.v1`，`human_signoff=not-provided`，并补 `project_config`、`narration_script`、`card_index`、`english_subtitles`、`subtitle_fragments`、`subtitle_preserve_plan`、`subtitle_source_root`、九 SVG、单首本地主题曲、精确 `source_artifacts` 与六章 reel/receipt。先以 [`prepare_production_inputs.py`](prepare_production_inputs.py) 只读预检；通过后在新外置目录写 `production-inputs.json`、`preserve-plan.json`、`source-audit.json`。不可用样片或占位 JSON 过生产门。
5. 新建正式 `xar-promo` run，核 config snapshot，再依 preserve plan 保全全套原件；运行 `validate`/`plan` 后另开 build attempt，做六章字幕、音频混合、章节/帧率/流时长审计。技术 GREEN 之后，实际按 1× 完整观看成片并对精确最终 bytes/SHA 记录人工 signoff；更换任何字节需重审。外部交付仅按用户既有 OneDrive 授权处理最终指定视频，未形成或未上传不能写作已交付。
