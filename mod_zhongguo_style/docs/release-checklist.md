# 天朝特色 361 制发布签核表

本表是 `mod_zhongguo_style` 的正式发布门禁与上传记录。任何未勾选项都表示尚未完成；设计完成、静态 GREEN、
fixture GREEN 和 CK3 实机 GREEN 必须分开记录，不能互相代替。首次发布目前没有已知 Workshop item ID，禁止复用
`3784706360`、`3787304042` 或 `3790635143`。

## 1. 候选身份

- [ ] `descriptor.mod` 的版本、名称、`supported_version` 与本次文案一致。
- [ ] `descriptor.mod` 恰好含一行 `picture="thumbnail.png"`，无 BOM、无 `remote_file_id`。
- [ ] `thumbnail.png` 为可解码的 640×640 PNG，低于 1,000,000 字节；在 Steam 小卡片尺寸下人工确认标题可读。
- [ ] 简中与英文逐条人工审阅完成；法、德、日、韩、波、俄、西七种发布译文依照根目录 `docs/localization-workflow.md` 完成，并通过自动化检查与独立分层抽检；README/BBCode 明确说明这不等同于完整母语审校签字。
- [ ] `docs/release-localization-audit.json` 为当前 4 个源文件与 14 个发布目标文件的 GREEN 哈希快照；任一文案改动后已重跑审计。
- [ ] 所有运行时 `.txt` / `.gui` / `.yml` 带 UTF-8 BOM；README、BBCode 和 JSON 可读且无意外 BOM。
- [ ] 当前候选已提交，工作树干净，HEAD 带 annotated tag `zhongguo-361-v<descriptor version>`。
- [ ] 发布 commit、tag、CK3 build、EXE SHA-256 和生成器输入 checksum 已写入最终报告。

## 2. 静态与生成验证

在同一候选上执行并记录退出码与输出：

```powershell
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/gen_361_mechanisms.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/gen_scoreboard_snapshot.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/test_gen_361_mechanisms.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/test_scoreboard_snapshot.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/test_prepare_release_localization.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/validate_local.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/prepare_release_localization.py audit `
  --write-report mod_zhongguo_style/docs/release-localization-audit.json
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/compose_thumbnail.py --check
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/test_compose_workshop_media.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/compose_workshop_media.py --check-tracked
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/test_promo_video.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/test_prepare_promo_release_manifest.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/test_prepare_promo_visual_audit.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/test_audit_promo_visuals.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/validate_promo_video.py `
  --manifest mod_zhongguo_style/promo/promo-manifest.json --stage draft
& "tools\.venv\Scripts\python.exe" tools/test_gen_zhongguo_acceptance_cases.py
& "tools\.venv\Scripts\python.exe" tools/test_run_zhongguo_promo_capture.py
& "tools\.venv\Scripts\python.exe" tools/test_run_zhongguo_workshop_acceptance.py
& "tools\.venv\Scripts\python.exe" tools/test_build_mod_zhongguo_style_release.py
& "tools\.venv\Scripts\python.exe" tools/test_verify_zhongguo_workshop_cache.py
& "tools\.venv\Scripts\python.exe" tools/build_mod_zhongguo_style_release.py --check
```

- [ ] 生成器重跑后 `git diff --exit-code`，证明产物未陈旧。
- [ ] 361 manifest 的编号恰为 001–361，无缺失、重复或额外编号。
- [ ] 每号都有玩家入口、AI 入口、选择状态、组织账变化、静态断言和 361 整批参考路线映射。
- [ ] 发布本地化审计命令 GREEN；报告严格为 4 个源文件 + 14 个目标文件，且报告生成后 `git diff --exit-code`。
- [ ] release builder 单元测试 GREEN；双构建 manifest 与 ZIP 逐字节可复现。
- [ ] `--check` 的 file count、manifest SHA-256 与 ZIP SHA-256 已抄入本表末尾记录。

## 3. CK3 合批实机验收

只使用一次性 `-userdir` 与外部 fixture。正式基线采用**一次 CK3 启动跑完 361 条参考路线与共享核心链**；仅在日志、截图或
断言出现明确 RED 时定向重跑失败场景，不再人为拆成四次启动。失败 attempt、日志、存档和截图必须原样保留，不能被 GREEN
覆盖。

桌面输入、OCR、GUI scale、相机与片场清理的可复用规则见 `docs/acceptance-automation-lessons.md`。自动化期间 CK3 输入线程必须精确签为 US English HKL `0x04090409` 并保持英文；不得把 Shift、候选层消失或已发送快捷键当成 ACK。

宣传合批不得承担相机调试。正式 `--promo-capture` 前，先在同一提交上运行一次只到史实赵曙、汴州定位、查找窗关闭与零测试 UI 门的短探针；它不启动 FFmpeg，也不冒充 361 全链：

```powershell
& "tools\.venv\Scripts\python.exe" tools/run_zhongguo_acceptance.py `
  --promo-camera-probe
```

只有短探针报告为 GREEN，才允许启动完整宣传合批。

- [ ] 兼容 smoke 一次整批运行完成 361/361 配置投影：每个编号的 BEGIN/PASS 遥测恰好出现一次，0 duplicate，0 missing；14 本组织账与选择状态均通过。该项本身不代表领域机制完成。
- [ ] 语义验收覆盖 361/361：每个编号都在所属的 38 个领域状态机中建立真实对象，执行合法迁移，并验证期限、资源/容量恒等式、幂等/stale 负例和可见反馈；manifest 中不再存在 `domain_runtime=not-implemented` 或未解释的 `partial`。
- [ ] 同次运行覆盖严格分布、小 cohort、新人保护、互评、校准、告身、考核榜、申诉/PIP、免费京察与拒办后果；一名来宾门槛与零来宾豁免由静态合同覆盖，不用监禁/释放角色伪造实机前置。
- [ ] 非独立 AI 天朝制公爵完成后台考核；代码/静态审计证明公爵及以上可考核直属官员，伯爵和男爵只有受评入口；发布文案明确这是第二个所有者授权 AI 例外，不外推到其他系统。
- [ ] 报告分别声明两种覆盖：旧 `361/361` 是配置与共享账本 smoke；新的语义 `361/361` 才是领域运行时完成。二者都不冒充 1,083 个 A/B/C 分支逐一人工点选；未跑的自然期限、跨三年存读档或角色截图矩阵不得写成已实测。
- [ ] 同一领主同一年重复结算无二次奖惩；换上司不消费旧上司的拒办理由；旧榜单不读取新一轮实时值。
- [ ] 3.25 精确核对地方国库 `-50`、个人金币 `-25`、贤能 `-60` 与一年俸禄 `-25%`；申诉只退同一 reviewer / serial 的本轮固定金额，并立即停止尚未结算的未来扣薪。
- [ ] `error.log`、`debug.log`、GUI warning 和 database conflict 中 0 个阻塞性 `zg361` 诊断。
- [ ] 真实 profile、Steam userdata、现有 Workshop 缓存和仓库源树的前后基线符合验收报告声明。
- [ ] 整批报告、截图、日志、存档、覆盖 JSON、JUnit、哈希索引均有唯一 artifact 路径；所有 RED 定向重跑另建不可变目录，历史或失败报告未被覆盖。

## 4. README、缩略图和工坊媒体

- [ ] README 的适用范围明确为“天朝制公爵及以上考核直属官员；伯爵/男爵只受评”。
- [ ] README 与 `workshop/description.bbcode` 的版本、兼容性、九语言口径、AI 第二例外和 361/361 证据边界一致。
- [ ] BBCode 以 UTF-8 计少于 8,000 字节；没有 Markdown 图片语法、可变 branch raw URL 或未替换占位符。
- [ ] BBCode 顶部加入一张干净主视觉或实机 hero 图；所有外链图片使用 40 字符 commit-pinned GitHub raw URL，或使用已核验 Steam CDN URL。
- [ ] 保留 6–8 张无调试/fixture 控件的实机图：京察入口、考核榜管理视角、本人受评视角、3.25/PIP、申诉改判、361 政策卡、制度驾驶舱、AI 领主结果。
- [ ] 原始 2560×1440 PNG 永久保留；Workshop 上传副本另存为单张低于 2 MB 的 JPEG，并记录裁切、质量、尺寸与 SHA-256。
- [ ] 第 7/8 张只采用同一正式 promo GREEN run 的 `#001/#361` 政策卡；`media-policy-lock.json` 已绑定根/cell 报告、evidence index、timeline、原始 MKV 与源/成品 SHA-256，capture 前不得以 fixture 或生成图占位。
- [ ] 工坊 media strip 的实际数量、顺序和放大图人工复核；删除重传后的顺序变化已校正。
- [ ] 宣传视频所用原始录屏、TTS 输入、`zh-CN-XiaoxiaoNeural` 音轨、双语字幕源、剪辑工程、中间导出和失败版本均保留，不进入 mod staging。
- [ ] 宣传成片以中文为主叙事、简中/英文同屏字幕，使用 `zh-CN-XiaoxiaoNeural`，时长严格短于 20 分钟；开场直接进入主题，不含 Launcher、CK3 启动或存档 loading。
- [ ] 所有入片实机镜头使用 CK3 书签/世界中的真实历史角色，素材 notes 记录 bookmark 与 character ID；不使用测试临时角色，考核榜可见区域也不得出现两名世界生成坊正的姓名。
- [ ] 最终时间线与 QA 抽帧中 0 个 fixture/test-only 决议、按钮或文字（包括“361制实机验收”、`ZGA`、验收规划器、演示触发器）；含污染的验收素材只保留为过程证据，不以裁字、打码或遮罩方式入片。
- [ ] 对最终 manifest 运行 `tools/prepare_promo_visual_audit.py`，输出到新的外部 artifact 目录；全部 captured video 章节均含精确起点/终点且采样间隔不超过 1 秒，重叠章节的同源同时间戳证据已合并，角色与 role 映射来自 manifest provenance。
- [ ] producer 原始 `promo-visual-audit-spec.PENDING.json` 仍保留且明确未签核（空 reviewed chapter、五项 false）；人工完整审阅后另存 SIGNED spec，未通过脚本或批量替换伪造 GREEN。
- [ ] 对最终零占位 manifest 运行 `tools/audit_promo_visuals.py audit`：每个实机章节都有间隔不超过 1 秒的全屏 PNG/OCR 覆盖，still 使用原图，全部证据与源素材按 bytes/SHA-256 绑定；报告为 GREEN。
- [ ] 角色 provenance 为每名主角/考核者/受评者记录书签、原版 history ID、显示名、职责及 exact-build history 文件 SHA；工具已确认 history key 存在且 `temporary_or_generated=false`。
- [ ] 人工以 1× 完整播放每个入片实机段并检查所有 still，签核 `historical_characters_only`、`no_generated_official_name_visible`、`fixture_test_ui_absent`、`full_clip_reviewed` 与 `no_crop_mask_or_redaction` 五项；五张均匀 QA 抽帧不替代完整签核。
- [ ] 合成后再以 1× 完整播放最终 MP4，确认公开角色角标、中文主字幕和英文副字幕没有重新引入 `FIXTURE-LIVE`、`ZGA`、测试决议/事件/按钮或世界生成官员姓名；记录成片 SHA-256 与签核人。构建器同时静态扫描所有会渲染的标题、状态、正文和 cue，人工复核不能被五帧抽样替代。
- [ ] 使用最终记录的报告 SHA 执行 `tools/audit_promo_visuals.py verify --expected-report-sha256 <sha>` 再现 GREEN；audit spec、GREEN/RED 报告、全屏 PNG、OCR JSON、旧 take 与人工签核全部保留在外部 artifact。

建议截图顺序：

1. 免费半强制京察弹窗；
2. “我考核的官员”完整榜单；
3. “我所在的受评队列”与本人 KPI/名次；
4. 3.25 国库、金币、贤能、俸禄四重处罚与 PIP；
5. 申诉改判、退款和榜头修正；
6. 背靠背互评 / 校准 / 抢功中的一张代表政策卡；
7. 14 本组织账制度驾驶舱；
8. 非独立 AI 公爵后台考核的玩家可见结果。

## 5. 正式构建

```powershell
py tools/build_mod_zhongguo_style_release.py --release
```

- [ ] 构建器已拒绝 lightweight tag，并确认 HEAD 上的匹配 tag 是 annotated tag。
- [ ] 构建器已重新核对发布本地化审计报告的精确 schema、4+14 文件清单与当前 SHA-256。
- [ ] 正式输出仅为 `dist/mod_zhongguo_style/`、旁置 manifest 与 deterministic ZIP。
- [ ] staging 只包含 `descriptor.mod`、`thumbnail.png` 与 `common/events/gfx/gui/localization` 中的允许类型。
- [ ] staging 中不存在 README、docs、tools、workshop、images、artifacts、fixture/test 路径或 `remote_file_id`。
- [ ] 对 staging 运行 canonical manifest 验证 GREEN：

```powershell
py tools/build_mod_zhongguo_style_release.py `
  --verify dist/mod_zhongguo_style `
  --manifest dist/mod_zhongguo_style-v<version>.manifest.json
```

- [ ] ZIP 根目录恰为 `mod_zhongguo_style/`；ZIP 内容与 staging manifest 完全一致。
- [ ] Steam 上传源只指向 formal staging，绝不直接指向开发目录。

## 6. Steam 首次上传

首次发布没有 item ID 时，外层 `.mod` 必须复制 staging 内层 `descriptor.mod` 的全部字段并追加 staging 的绝对
`path=`；不要预填任何 `remote_file_id`。只写一行 `path=` 的残缺 descriptor 不能作为 Launcher 枚举合同。

- [ ] 通过 Steam 客户端启动 CK3/PDX Launcher，确认 Steam API 已初始化。
- [ ] Launcher → Mods → 上传 Mod → 创建新物品；先保持隐藏可见性。
- [ ] 上传成功日志保存到 artifact，记录时间、content manifest 和新 item ID。
- [ ] 新 item ID 只保存在用户目录外层 `.mod`；仓库内层 descriptor 不保存 ID。
- [ ] 上传后立即重建 canonical staging，清除 Launcher 临时注入的内层 `remote_file_id`。
- [ ] 用新 ID 从同一 clean tag 生成一份仅用于核验的 ID-bearing sidecar：

```powershell
py tools/build_mod_zhongguo_style_release.py --release `
  --workshop-item-id <new-item-id> `
  --output <temporary-output>
```

- [ ] 将旧缓存完整移出 `steamapps/workshop/content/1158310/` 后，从空路径强制下载新 item。
- [ ] 新鲜缓存只允许 Launcher 的 descriptor 换行规范化与末行唯一正确 ID 注入，其余文件逐字节匹配：

```powershell
py tools/build_mod_zhongguo_style_release.py `
  --verify <fresh-workshop-cache> `
  --manifest <id-bearing-manifest> `
  --workshop-cache

py tools/verify_zhongguo_workshop_cache.py `
  --cache-leaf <fresh-workshop-cache> `
  --manifest <id-bearing-manifest> `
  --zip <id-bearing-formal-zip> `
  --descriptor-policy launcher-injected `
  --report <external-fresh-cache-report.json>
```

- [ ] 从新鲜 Workshop 缓存运行一次 production smoke；报告明确写 `verified_workshop_cache`，不借用开发树结论。

```powershell
& "tools\.venv\Scripts\python.exe" tools/run_zhongguo_acceptance.py `
  --artifacts-dir <new-immutable-artifact-root> `
  --workshop-cache-source <fresh-workshop-cache> `
  --workshop-manifest <id-bearing-manifest>
```

该模式会在启动 CK3 前再次执行逐文件 Workshop manifest 核验，并要求缓存叶目录名等于新 item ID、sidecar
绑定当前 formal tag / HEAD；运行报告记录 `verified_workshop_cache=true`、manifest SHA-256、item ID、运行源路径及
缓存源树前后不变性。
- [ ] 工坊标题、缩略图、BBCode、media strip、可见性、订阅下载和游戏内版本均核验后再公开。
- [ ] 最终再次重建无 ID staging，并把外层 `.mod` 的 `path=` 恢复到开发目录。

## 7. 发布记录

| 字段 | 最终值 |
|---|---|
| Mod version | |
| Git commit | |
| Git tag | |
| CK3 version / EXE SHA-256 | |
| Workshop item ID | |
| Steam content manifest | |
| 上传成功时间（Asia/Shanghai） | |
| Formal file count | |
| Formal manifest SHA-256 | |
| Formal ZIP SHA-256 | |
| ID-bearing verification manifest SHA-256 | |
| Fresh Workshop cache report / SHA-256 | |
| 361/361 coverage report / SHA-256 | |
| Release-localization audit SHA-256 | |
| Thumbnail SHA-256 | |
| BBCode SHA-256 / UTF-8 bytes | |
| Media-strip index | |
| Promo master / duration / SHA-256 | |
| Promo visual audit report / SHA-256 | |
| Raw/process artifact root | |

签核后仍不得删除任何过程素材。大体积文件不进 Git，但必须在 artifact 索引中留下绝对路径、大小、SHA-256、
生成命令与对应发布版本。
