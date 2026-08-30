# 天朝特色 361 制发布签核表

本表是 `mod_zhongguo_style` 的正式发布门禁与上传记录。任何未勾选项都表示尚未完成；设计完成、静态 GREEN、
fixture GREEN 和 CK3 实机 GREEN 必须分开记录，不能互相代替。0.3.0 已创建并公开新的 Workshop 物品
`3792585972`；它不是、也未复用 `3784706360`、`3787304042` 或 `3790635143`。八图 media strip 已按
`01 → 08` 上传；物品于 2026-08-30 约 14:48（Asia/Shanghai）从隐藏切换为公开，并于 14:50:21 通过匿名远端复核。

0.3.0 的发布范围已经冻结为现有考核核心链、361 项参考政策配置和 14 本共享组织账。38 个领域对象/状态机属于
下一版本预研；它们可以诚实保留 `not-implemented` / `partial` 状态，但不得反过来阻断 0.3.0，也不得在本版文案中
冒充已经实现。

## 1. 候选身份

- [x] `descriptor.mod` 的版本、名称、`supported_version` 与本次文案一致。
- [x] `descriptor.mod` 恰好含一行 `picture="thumbnail.png"`，无 BOM、无 `remote_file_id`。
- [x] `thumbnail.png` 为可解码的 640×640 PNG，低于 1,000,000 字节；在 Steam 小卡片尺寸下人工确认标题可读。
- [x] 简中与英文逐条人工审阅完成；法、德、日、韩、波、俄、西七种发布译文依照根目录 `docs/localization-workflow.md` 完成，并通过自动化检查与独立分层抽检；README/BBCode 明确说明这不等同于完整母语审校签字。
- [x] `docs/release-localization-audit.json` 为当前 4 个源文件与 14 个发布目标文件的 GREEN 哈希快照；任一文案改动后已重跑审计。
- [x] 所有运行时 `.txt` / `.gui` / `.yml` 带 UTF-8 BOM；README、BBCode 和 JSON 可读且无意外 BOM。
- [x] 当前候选已提交；正式 clean worktree 无 tracked dirty，HEAD `393253276481916f026c4c28e9bbab6da2877275` 带 annotated tag `zhongguo-361-v0.3.0`。
- [x] 发布 commit、tag、CK3 build、EXE SHA-256 和生成器输入 checksum 已写入最终报告与本表发布记录。

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

- [x] 生成器重跑后 `git diff --exit-code`，证明产物未陈旧。
- [x] 361 manifest 的编号恰为 001–361，无缺失、重复或额外编号。
- [x] 每号都有玩家入口、AI 入口、选择状态、组织账变化、静态断言和 361 整批参考路线映射。
- [x] 发布本地化审计命令 GREEN；报告严格为 4 个源文件 + 14 个目标文件，且报告生成后 `git diff --exit-code`。
- [x] release builder 单元测试 GREEN；双构建 manifest 与 ZIP 逐字节可复现。
- [x] `--check` 的 file count、manifest SHA-256 与 ZIP SHA-256 已抄入本表末尾记录。

## 3. CK3 合批实机验收

只使用一次性 `-userdir` 与外部 fixture。正式发布总共只安排**两次 CK3 启动**：上传前一次 `--promo-capture`
在同一 PID 中跑完 361 条参考路线、共享核心链、MCP 头衔导航矩阵和宣传录制；上传后从 fresh Workshop cache
再跑一次 production smoke。仅在日志、截图或断言出现明确 RED 时定向重跑失败场景，不人为追加独立相机启动。
失败 attempt、日志、存档和截图必须原样保留，不能被 GREEN 覆盖。

桌面输入、OCR、GUI scale 与片场清理的可复用规则见 `docs/acceptance-automation-lessons.md`。现有产品 GUI 自动化期间
CK3 输入线程仍必须精确签为 US English HKL `0x04090409` 并保持英文；该 HKL 不参与头衔导航，也不得把 Shift、
候选层消失或已发送快捷键当成相机 ACK。

头衔定位不再使用 OCR、快捷键、剪贴板或鼠标驱动瞬态“查找头衔”窗口。冻结构建必须先由 exact-build MCP
`ck3_center_map_on_landed_title_v1(title_key="c_bianzhou", expected_revision=<revision>)` 解析稳定 title key，并在
游戏拥有线程上回读真实相机终态。成功证据必须包含 `postcondition_verified=true`、
`anchor_kind=title_bounds_center`、`settled=true`、`target_write_blocked=false`，且 current/target state 与期望中心、
zoom 和冻结的 paused/date/player/episode binding 一致；命令 dispatch 或菜单消失都不算 ACK。

正式门直接嵌入同一次 `--promo-capture` 会话：runner 以唯一 pipe 执行 suspended → inject → resume，复用同一个
`NativeHeadlessGameplayDriver` / `GameplayBridgeService` 与受管 CK3 PID；在 `recorder.start()` 之前运行
`c_guangzhou → c_bianzhou → c_guangzhou → b_kaifeng → b_kaifeng → unknown → b_kaifeng → final c_bianzhou`
typed 矩阵。报告必须保存完整 binding、每次 typed payload/error 的 SHA-256、DLL/injector/EXE 身份、同 PID/connection
generation、全部成功调用的 `target_write_blocked=false` 和 OCR/像素判断/窗口激活/键盘/鼠标/剪贴板六类零 fallback 计数。
生产没有安全可逆的 inhibit 控制时，正例必须明确写 `skipped`、`executed=false`、`live_claim=false`，不得改进程内存伪造。

上传前正式命令（`--bridge-pipe` 默认自动生成本次运行唯一 nonce，不应复用固定 pipe）：

```powershell
& "tools\.venv\Scripts\python.exe" tools/run_zhongguo_acceptance.py `
  --promo-capture `
  --bridge-dll <exact-build-production-bridge.dll> `
  --bridge-injector <exact-build-injector.exe>
```

`--promo-camera-probe` 只是在上述正式会话 RED 后用于定向诊断的可选模式；它不启动 FFmpeg、不冒充 361 全链、
不构成正式发布前置，也不计入正常两次启动预算。旧 OCR 相机 attempt 只保留为历史过程素材，不再构成本版本的
可接受路径或验收前置。

- [x] 兼容 smoke 一次整批运行完成 361/361 配置投影：每个编号的 BEGIN/PASS 遥测恰好出现一次，0 duplicate，0 missing；14 本组织账与选择状态均通过。该项本身不代表领域机制完成。
- [x] 最终报告与公开文案把 `361/361` 严格限定为参考政策配置、唯一选择状态、14 本共享账、校验和与幂等 smoke；38 个下一版本领域状态机可以继续标为 `not-implemented` / `partial`，且不计入 0.3.0 缺陷或发布阻点。
- [x] 同次运行覆盖严格分布、小 cohort、新人保护、互评、校准、告身、考核榜、申诉/PIP、免费京察与拒办后果；一名来宾门槛与零来宾豁免由静态合同覆盖，不用监禁/释放角色伪造实机前置。
- [x] 非独立 AI 天朝制公爵完成后台考核；代码/静态审计证明公爵及以上可考核直属官员，伯爵和男爵只有受评入口；发布文案明确这是第二个所有者授权 AI 例外，不外推到其他系统。
- [x] 报告不把配置 smoke 冒充 361 个领域玩法、1,083 个 A/B/C 分支逐一人工点选，或下一版本已经落地；未跑的自然期限、跨三年存读档或角色截图矩阵不得写成已实测。
- [x] 同一领主同一年重复结算无二次奖惩；换上司不消费旧上司的拒办理由；旧榜单不读取新一轮实时值。
- [x] 3.25 精确核对地方国库 `-50`、个人金币 `-25`、贤能 `-60` 与一年俸禄 `-25%`；申诉只退同一 reviewer / serial 的本轮固定金额，并立即停止尚未结算的未来扣薪。
- [x] `error.log`、`debug.log`、GUI warning 和 database conflict 中 0 个阻塞性 `zg361` 诊断。
- [x] 真实 profile、Steam userdata、现有 Workshop 缓存和仓库源树的前后基线符合验收报告声明。
- [x] 整批报告、截图、日志、存档、覆盖 JSON、JUnit、哈希索引均有唯一 artifact 路径；所有 RED 定向重跑另建不可变目录，历史或失败报告未被覆盖。

上传前完整同局 GREEN 位于
`Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0930_clean_2fa2ac8_mcp`；根报告
SHA-256 为 `786B451B305FC5FCCDE3FA2650ED2969D6EF51941761D045CBD26249B8C493B1`。上传后 fresh-cache
production smoke 位于 `Z:\ck3_mod_rewrite_process_assets\zg361\release\fresh-cache-3792585972\acceptance-03`，运行
`503.022` 秒；顶层和 cell 均为 GREEN，`fixture_cases_passed = 361`、项目诊断数为 0，且
`verified_workshop_cache=true`、`runtime_source_kind=verified_workshop_cache`、缓存/运行源/仓库源树前后均未变化。
顶层报告 SHA-256 为 `4FE660637964EF908EF5D0DB4F0F63D412AE319D12502C4EC61737419006F418`，证据索引 SHA-256 为
`64EA0E135CB2AA9D3BA351DB6C4B862ECCE6C23CA05A486966D83946F6F0FCC6`。

## 4. README、缩略图和工坊媒体

- [x] README 的适用范围明确为“天朝制公爵及以上考核直属官员；伯爵/男爵只受评”。
- [x] README 与 `workshop/description.bbcode` 的版本、兼容性、九语言口径、AI 第二例外和 361/361 证据边界一致。
- [x] BBCode 在 HTML form 的 CRLF 换行投影后仍少于 8,000 UTF-8 字节；没有 Markdown 图片语法、可变 branch raw URL 或未替换占位符。
- [x] BBCode 顶部加入一张干净主视觉或实机 hero 图；所有外链图片使用 40 字符 commit-pinned GitHub raw URL，或使用已核验 Steam CDN URL。
- [x] 保留 8 张无调试/fixture 控件的实机图：严格分布与校准、考核榜、京察、3.25/PIP 和 `#001/#361` 政策卡；其来源、诚实边界及推荐上传顺序记录于 `workshop/media.md`。
- [x] 原始 2560×1440 PNG 永久保留；Workshop 上传副本另存为单张低于 2 MB 的 JPEG，并记录裁切、质量、尺寸与 SHA-256。
- [x] 第 7/8 张只采用同一正式 promo GREEN run 的 `#001/#361` 政策卡；`media-policy-lock.json` 已绑定根/cell 报告、evidence index、timeline、原始 MKV 与源/成品 SHA-256，capture 前不得以 fixture 或生成图占位。
- [x] 工坊 media strip 已按 `01 → 08` 上传并保存；匿名公开 HTML 恰含 8 个 `highlight_strip_item`，实际数量和顺序复核通过。
- [x] 八图与最终 BBCode 采用同一个 image-bearing commit，并通过独立严格门：

```powershell
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/test_validate_workshop_description.py
& "tools\.venv\Scripts\python.exe" mod_zhongguo_style/tools/validate_workshop_description.py
```

- [x] 宣传视频所用原始录屏、TTS 输入、`zh-CN-XiaoxiaoNeural` 音轨、双语字幕源、剪辑工程、中间导出和失败版本均保留，不进入 mod staging。
- [x] 宣传成片以中文为主叙事、简中/英文同屏字幕，使用 `zh-CN-XiaoxiaoNeural`，时长严格短于 20 分钟；开场直接进入主题，不含 Launcher、CK3 启动或存档 loading。
- [x] 所有入片实机镜头使用 CK3 书签/世界中的真实历史角色，素材 notes 记录 bookmark 与 character ID；不使用测试临时角色，考核榜可见区域也不得出现两名世界生成坊正的姓名。
- [x] 最终时间线与 QA 抽帧中 0 个 fixture/test-only 决议、按钮或文字（包括“361制实机验收”、`ZGA`、验收规划器、演示触发器）；含污染的验收素材只保留为过程证据，不以裁字、打码或遮罩方式入片。
- [x] 对最终 manifest 运行 `tools/prepare_promo_visual_audit.py`，输出到新的外部 artifact 目录；全部 captured video 章节均含精确起点/终点且采样间隔不超过 1 秒，重叠章节的同源同时间戳证据已合并，角色与 role 映射来自 manifest provenance。
- [x] producer 原始 `promo-visual-audit-spec.PENDING.json` 仍保留且明确未签核（空 reviewed chapter、五项 false）；人工完整审阅后另存 SIGNED spec，未通过脚本或批量替换伪造 GREEN。
- [x] 对最终零占位 manifest 运行 `tools/audit_promo_visuals.py audit`：每个实机章节都有间隔不超过 1 秒的全屏 PNG/OCR 覆盖，still 使用原图，全部证据与源素材按 bytes/SHA-256 绑定；报告为 GREEN。
- [x] 角色 provenance 为每名主角/考核者/受评者记录书签、原版 history ID、显示名、职责及 exact-build history 文件 SHA；工具已确认 history key 存在且 `temporary_or_generated=false`。
- [x] 人工以 1× 完整播放每个入片实机段并检查所有 still，签核 `historical_characters_only`、`no_generated_official_name_visible`、`fixture_test_ui_absent`、`full_clip_reviewed` 与 `no_crop_mask_or_redaction` 五项；五张均匀 QA 抽帧不替代完整签核。
- [x] 合成后再以 1× 完整播放最终 MP4，确认公开角色角标、中文主字幕和英文副字幕没有重新引入 `FIXTURE-LIVE`、`ZGA`、测试决议/事件/按钮或世界生成官员姓名；记录成片 SHA-256 与签核人。构建器同时静态扫描所有会渲染的标题、状态、正文和 cue，人工复核不能被五帧抽样替代。
- [x] 使用最终记录的报告 SHA 执行 `tools/audit_promo_visuals.py verify --expected-report-sha256 <sha>` 再现 GREEN；audit spec、GREEN/RED 报告、全屏 PNG、OCR JSON、旧 take 与人工签核全部保留在外部 artifact。

宣传证据摘要：源素材单文件审阅卷 `97.033333` 秒，审阅人 `XenoAmess` 以 1× 完整播放并签核五项；SIGNED spec SHA-256 为 `22EB7E10DA8A2ACB18BB58F3CDB2CF75E02BC990164F45D1B6047A9B8D243C5D`。14 个实机章节/108 帧视觉审计为 GREEN，报告 SHA-256 为 `B27F0EA426A78DB25B21DE56AD092AA08A23F419275EB5F3E4BAFFC3EE9779B6`。retry03 技术门虽 GREEN，但 450 px 定宽角标裁切导致人工 visual RED；`1230ad9` 改为测量后的动态宽度并提升视觉缓存版本，定向测试 `27/27` GREEN。最终 retry04 自动媒体门 GREEN，审阅人又以 1× 完整播放 `449.286068` 秒成片并确认五项；签核记录 SHA-256 为 `57E96541B8B74960F4CBA6E487CA4F0B4AF1845BE67FC497A8BA0C38FAFF8A43`。

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

- [x] 构建器已拒绝 lightweight tag，并确认 HEAD 上的匹配 tag 是 annotated tag。
- [x] 构建器已重新核对发布本地化审计报告的精确 schema、4+14 文件清单与当前 SHA-256。
- [x] 正式输出仅为 `dist/mod_zhongguo_style/`、旁置 manifest 与 deterministic ZIP。
- [x] staging 只包含 `descriptor.mod`、`thumbnail.png` 与 `common/events/gfx/gui/localization` 中的允许类型。
- [x] staging 中不存在 README、docs、tools、workshop、images、artifacts、fixture/test 路径或 `remote_file_id`。
- [x] 对 staging 运行 canonical manifest 验证 GREEN：

```powershell
py tools/build_mod_zhongguo_style_release.py `
  --verify dist/mod_zhongguo_style `
  --manifest dist/mod_zhongguo_style-v<version>.manifest.json
```

- [x] ZIP 根目录恰为 `mod_zhongguo_style/`；ZIP 内容与 staging manifest 完全一致。
- [x] Steam 上传源只指向 formal staging，绝不直接指向开发目录。

## 6. Steam 首次上传

首次发布没有 item ID 时，外层 `.mod` 必须复制 staging 内层 `descriptor.mod` 的全部字段并追加 staging 的绝对
`path=`；不要预填任何 `remote_file_id`。只写一行 `path=` 的残缺 descriptor 不能作为 Launcher 枚举合同。

- [x] 通过 Steam 客户端启动 CK3/PDX Launcher，确认 Steam API 已初始化。
- [x] Launcher → Mods → 上传 Mod → 创建新物品；上传时保持隐藏可见性。
- [x] 上传成功日志保存到 `Z:\ck3_mod_rewrite_process_assets\zg361\release\steam-upload-3932532`，记录时间、content manifest 和新 item ID。
- [x] 新 item ID 只保存在用户目录外层 `.mod`；仓库内层 descriptor 不保存 ID。
- [x] 上传后立即重建 canonical staging，清除 Launcher 临时注入的内层 `remote_file_id`；重建结果仍为 51 文件及本表记录的正式哈希。
- [x] 用新 ID 从同一 clean tag 生成一份仅用于核验的 ID-bearing sidecar：

```powershell
py tools/build_mod_zhongguo_style_release.py --release `
  --workshop-item-id <new-item-id> `
  --output <temporary-output>
```

- [x] 新 ID 的缓存叶目录在下载前确认为不存在；从该空路径强制下载新 item，得到 51 文件、6,931,940 bytes 的 fresh cache。
- [x] 新鲜缓存只允许 Launcher 的 descriptor 换行规范化与末行唯一正确 ID 注入，其余文件逐字节匹配：

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

- [x] 从新鲜 Workshop 缓存运行一次 production smoke；报告明确写 `verified_workshop_cache`，不借用开发树结论。

```powershell
& "tools\.venv\Scripts\python.exe" tools/run_zhongguo_acceptance.py `
  --artifacts-dir <new-immutable-artifact-root> `
  --workshop-cache-source <fresh-workshop-cache> `
  --workshop-manifest <id-bearing-manifest> `
  --bridge-dll <exact-build-production-bridge.dll> `
  --bridge-injector <exact-build-injector.exe>
```

该模式会在启动 CK3 前再次执行逐文件 Workshop manifest 核验，并要求缓存叶目录名等于新 item ID、sidecar
绑定当前 formal tag / HEAD；运行报告记录 `verified_workshop_cache=true`、manifest SHA-256、item ID、运行源路径及
缓存源树前后不变性。
- [x] 工坊标题、缩略图、BBCode、media strip、可见性、订阅下载和游戏内版本均已核验；物品已切为公开。
- [x] 最终再次重建无 ID staging，并把外层 `.mod` 的 `path=` 恢复到开发目录。

八张 media strip 已按 `01 → 08` 上传保存，物品于 2026-08-30 约 14:48（Asia/Shanghai）从隐藏切换为公开；过程中
没有协议确认、重新登录或 Steam Guard 挑战。14:50:21 的匿名远端验证为 GREEN：API `result=1`、`visibility=0`、
标题精确匹配、`hcontent_file=2542810955685536611`，公开 HTML 恰含 8 个 `highlight_strip_item`；远端描述在仅规范化
CRLF 与尾换行后和本地 BBCode 一致，且无 probe 残留。证据目录为
`Z:\ck3_mod_rewrite_process_assets\zg361\release\steam-upload-3932532\remote-public-verify`，验证报告 SHA-256 为
`195DE867F93AD84D14FF669CE69B908064AEC54200D8E30E0A25A2DE9E5A6DA9`。最终外层描述符已在 Launcher 与 CK3 均未运行时
恢复到开发树：`path="Z:/ck3_mod_rewrite/mod_zhongguo_style"`，并保留正确的
`remote_file_id="3792585972"`；仓库与 formal staging 的内层 `descriptor.mod` 均继续不含 `remote_file_id`。

## 7. 发布记录

| 字段 | 最终值 |
|---|---|
| Mod version | `0.3.0` |
| Git commit | `393253276481916f026c4c28e9bbab6da2877275` |
| Git tag | `zhongguo-361-v0.3.0`（annotated，精确指向上述 commit） |
| CK3 version / EXE SHA-256 | `1.19.0.6` / `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| Workshop item ID | `3792585972`（公开，`visibility=0`） |
| Steam content manifest | `2542810955685536611` |
| 上传成功时间（Asia/Shanghai） | `2026-08-30 13:43:25`（Launcher `Publishing mod succeeded`） |
| 切换公开时间（Asia/Shanghai） | `2026-08-30` 约 `14:48`；无协议确认、登录或 Steam Guard 挑战 |
| 匿名远端验证 / SHA-256 | `2026-08-30 14:50:21` GREEN；`remote-public-verify\verify-publication.json` / `195DE867F93AD84D14FF669CE69B908064AEC54200D8E30E0A25A2DE9E5A6DA9` |
| 最终外层 descriptor / SHA-256 | `C:\Users\xenoa\Documents\Paradox Interactive\Crusader Kings III\mod\mod_zhongguo_style.mod`；206 bytes、LF、无 BOM、无末尾 LF，开发路径 + `remote_file_id="3792585972"` / `1C79AFDA987A7D10612473F4CEBAAAADAECAF3F3A49DDB522AB78526328E7889` |
| Formal file count | `51` |
| Formal manifest SHA-256 | `F61219ADFBA8E31B52836DD5251E505F0714262A74703409068101345540AD14` |
| Formal ZIP SHA-256 | `7ECF185749A6DEB10C7B260EEC70040299EDBD0BE96F49D5418000221BC32BA2` |
| ID-bearing verification manifest SHA-256 | `BD6DE37D590BB573D8B3E95833EA0F6D0BF32D5A3939BE1C9E97705A173EA54E` |
| Fresh Workshop cache report / SHA-256 | `Z:\ck3_mod_rewrite_process_assets\zg361\release\fresh-cache-3792585972\verify-workshop-cache.json` / `CD5097837D66988968975B343F4E245FFB7783A85549DBB1AE9AA9DB6FDEDC8B`; production smoke `acceptance-03\report.json` / `4FE660637964EF908EF5D0DB4F0F63D412AE319D12502C4EC61737419006F418`（GREEN） |
| 361/361 coverage report / SHA-256 | `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0930_clean_2fa2ac8_mcp\report.json` / `786B451B305FC5FCCDE3FA2650ED2969D6EF51941761D045CBD26249B8C493B1`（GREEN） |
| Release-localization audit SHA-256 | `DC8430A5A79813856BEAF733B122BE0CA1C7CA40F837C4D527D65BB346E986FC`（GREEN，4+14 文件） |
| Thumbnail SHA-256 | `B4E92139A227B55E8D52CCC58CFBE2C9CAC11A5F40E1B75EFDFA5D2D512DA5CE` |
| BBCode SHA-256 / UTF-8 bytes | `E7DF894B36F3F29B45C28CE294B0DE58E7E8875F16DD826265638AD605152B10` / 本地 LF `7,804` bytes；Steam CRLF 投影 `7,918` bytes |
| Media-strip index | `mod_zhongguo_style/workshop/media.md` / `2914CAC1B736A8D5FDD0AFE355C36694E0B3A9C7B2CDA8E447BEB04F40502BBE`；8 个 JPEG 已按 `01 → 08` 上传，公开 HTML 复核为 8 项 |
| Promo master / duration / SHA-256 | `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0930_clean_2fa2ac8_mcp\release\video-20260830-104354-retry04\zg361-promo-release.mp4` / `449.286068 s` / `A2647D2B88B1E243E9CD46A3EF6B7F0B6DF94A76FC22B048A847A0E31249B763`; sidecar `6084E1BDC362A72FAE1844202BF0C134E8EB2BF70DA89BE078D29E652C0550BC` |
| Promo visual audit report / SHA-256 | `release\promo-visual-audit-report-20260830-104354.json` / `B27F0EA426A78DB25B21DE56AD092AA08A23F419275EB5F3E4BAFFC3EE9779B6` (GREEN, 14 chapters / 108 frames) |
| Raw/process artifact root | `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0930_clean_2fa2ac8_mcp` |

签核后仍不得删除任何过程素材。大体积文件不进 Git，但必须在 artifact 索引中留下绝对路径、大小、SHA-256、
生成命令与对应发布版本。
