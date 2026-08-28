# 天朝特色 361 制发布签核表

本表是 `mod_zhongguo_style` 的正式发布门禁与上传记录。任何未勾选项都表示尚未完成；设计完成、静态 GREEN、
fixture GREEN 和 CK3 实机 GREEN 必须分开记录，不能互相代替。首次发布目前没有已知 Workshop item ID，禁止复用
`3784706360`、`3787304042` 或 `3790635143`。

## 1. 候选身份

- [ ] `descriptor.mod` 的版本、名称、`supported_version` 与本次文案一致。
- [ ] `descriptor.mod` 恰好含一行 `picture="thumbnail.png"`，无 BOM、无 `remote_file_id`。
- [ ] `thumbnail.png` 为可解码的 640×640 PNG，低于 1,000,000 字节；在 Steam 小卡片尺寸下人工确认标题可读。
- [ ] 简中与英文逐条人工审阅完成；发布级七语言翻译依照根目录 `docs/localization-workflow.md` 完成并抽检，不能把英文占位称为翻译完成。
- [ ] 所有运行时 `.txt` / `.gui` / `.yml` 带 UTF-8 BOM；README、BBCode 和 JSON 可读且无意外 BOM。
- [ ] 当前候选已提交，工作树干净，HEAD 带 annotated tag `zhongguo-361-v<descriptor version>`。
- [ ] 发布 commit、tag、CK3 build、EXE SHA-256 和生成器输入 checksum 已写入最终报告。

## 2. 静态与生成验证

在同一候选上执行并记录退出码与输出：

```powershell
py mod_zhongguo_style/tools/gen_361_mechanisms.py
py mod_zhongguo_style/tools/gen_scoreboard_snapshot.py
py mod_zhongguo_style/tools/test_gen_361_mechanisms.py
py mod_zhongguo_style/tools/test_scoreboard_snapshot.py
py mod_zhongguo_style/tools/validate_local.py
py tools/test_gen_zhongguo_acceptance_cases.py
py tools/test_build_mod_zhongguo_style_release.py
py tools/build_mod_zhongguo_style_release.py --check
```

- [ ] 生成器重跑后 `git diff --exit-code`，证明产物未陈旧。
- [ ] 361 manifest 的编号恰为 001–361，无缺失、重复或额外编号。
- [ ] 每号都有玩家入口、AI 入口、选择状态、组织账变化、静态断言和实机波次映射。
- [ ] release builder 单元测试 GREEN；双构建 manifest 与 ZIP 逐字节可复现。
- [ ] `--check` 的 file count、manifest SHA-256 与 ZIP SHA-256 已抄入本表末尾记录。

## 3. CK3 合批实机验收

只使用一次性 `-userdir` 与外部 fixture。每波同时覆盖玩家公爵、玩家皇帝、非独立 AI 公爵，以及只受评的伯爵/男爵；
失败 attempt、日志、存档和截图必须原样保留。四波全部结束后再汇总 361/361，不因某个共享 effect 成功就替其余编号签字。

- [ ] 波次 1：绩效核心与程序。覆盖严格分布、小 cohort、互评、校准、告身、申诉、PIP、事故责任、AI 公爵后台考核。
- [ ] 波次 2：职业与资源兑现。覆盖晋升、薪酬、国库/个人金币/俸禄、HC、招聘、继任、内转、外包、重组与账本守恒。
- [ ] 波次 3：项目、技术与办公室政治。覆盖抢功、向上管理、矩阵汇报、技术债、平台、实验、加班、需求与制度审计。
- [ ] 波次 4：跨周期政策与终局。跨至少三轮并存读档，覆盖目标棘轮、旧案冻结、翻案守恒、十年报告与绩效宪章。
- [ ] 每个编号的 BEGIN/PASS 遥测恰好出现一次；机器覆盖为 361/361，0 duplicate，0 missing。
- [ ] 同一领主同一年重复结算无二次奖惩；换上司不消费旧上司的拒办理由；旧榜单不读取新一轮实时值。
- [ ] 3.25 精确核对国库、个人金币、merit 与一年俸禄；申诉只退同一 reviewer / serial 的本轮固定金额。
- [ ] `error.log`、`debug.log`、GUI warning 和 database conflict 中 0 个阻塞性 `zg361` 诊断。
- [ ] 真实 profile、Steam userdata、现有 Workshop 缓存和仓库源树的前后基线符合验收报告声明。
- [ ] 每波报告、截图、日志、存档、覆盖 JSON、JUnit、哈希索引均有唯一 artifact 路径；历史或失败报告未被覆盖。

## 4. README、缩略图和工坊媒体

- [ ] README 的适用范围明确为“天朝制公爵及以上考核直属官员；伯爵/男爵只受评”。
- [ ] README 与 `workshop/description.bbcode` 的版本、兼容性、语言和已知限制一致。
- [ ] BBCode 以 UTF-8 计少于 8,000 字节；没有 Markdown 图片语法、可变 branch raw URL 或未替换占位符。
- [ ] BBCode 顶部加入一张干净主视觉或实机 hero 图；所有外链图片使用 40 字符 commit-pinned GitHub raw URL，或使用已核验 Steam CDN URL。
- [ ] 保留 6–8 张无调试/fixture 控件的实机图：京察入口、考核榜管理视角、本人受评视角、3.25/PIP、申诉改判、361 政策卡、制度驾驶舱、AI 领主结果。
- [ ] 原始 2560×1440 PNG 永久保留；Workshop 上传副本另存为单张低于 2 MB 的 JPEG，并记录裁切、质量、尺寸与 SHA-256。
- [ ] 工坊 media strip 的实际数量、顺序和放大图人工复核；删除重传后的顺序变化已校正。
- [ ] 宣传视频所用原始录屏、TTS 输入、`zh-CN-XiaoxiaoNeural` 音轨、双语字幕源、剪辑工程、中间导出和失败版本均保留，不进入 mod staging。

建议截图顺序：

1. 免费半强制京察弹窗；
2. “我考核的官员”完整榜单；
3. “我所在的受评队列”与本人 KPI/名次；
4. 3.25 三账本处罚与 PIP；
5. 申诉改判、退款和榜头修正；
6. 背靠背互评 / 校准 / 抢功中的一张代表政策卡；
7. 14 本组织账制度驾驶舱；
8. 非独立 AI 公爵后台考核的玩家可见结果。

## 5. 正式构建

```powershell
py tools/build_mod_zhongguo_style_release.py --release
```

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

首次发布没有 item ID 时，外层 `.mod` 只含 staging 的绝对 `path=`，不要预填任何 `remote_file_id`。

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
```

- [ ] 从新鲜 Workshop 缓存运行一次 production smoke；报告明确写 `verified_workshop_cache`，不借用开发树结论。
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
| Thumbnail SHA-256 | |
| BBCode SHA-256 / UTF-8 bytes | |
| Media-strip index | |
| Promo master / duration / SHA-256 | |
| Raw/process artifact root | |

签核后仍不得删除任何过程素材。大体积文件不进 Git，但必须在 artifact 索引中留下绝对路径、大小、SHA-256、
生成命令与对应发布版本。
