# 宗教试拍的规划与证据接线

**后续生产先读[系列研究与讲解方法](../docs/production-lessons.md)。** 先明确要支持的玩家决策、所需观测和因果验证，再编排声画；研究同时演进现有MCP与智能体。下述初始试拍／authoring状态保留各自历史身份，当前成果见[一期v4交付](../../../docs/ck3-native-ai/faith-and-power-episode01-value-v4-delivery.md)；技术检查与讲解效果、实际听审分别记录。

本轮按[第五轮整体重排](../docs/episode01-revision-v5.md)实现缺失教改MCP并制作双向案例；配音与新take前应用[制作经验](../docs/production-experience.md)。源码候选、构建、实测、配音和最终媒体各自保留实际状态，不从已有run继承新版资格。

采用／圣物两条因果试拍仍是 `CAPTURE_PENDING`，系列 ProjectConfig 三章均为 `planned`。第一期已有独立的158条逐句文稿和准备场景有声样段；[第一期输入与机器索引](../episode01/README.md)保存其边界。上下文原片不补齐原生业务链，也不让两条因果试拍获得采用／圣物结果信用。

2026-10-17T05:42:56.604633Z，`machine_id: 4-8e1c2f1861` 已创建并验证一个[authoring-only run](../build-records/authoring-20261017-a01.json)：12份小型输入、270,034 B，固定源码提交`bf5d4d871f4a974339279a110693074df3aef406`和再次查询的最新0.3.0 wheel。其phase明确跳过实际试拍，不能作为capture或render资格；下文命令是此能力的可复用入口，新attempt须另选目录。

`pilot-plan.json` 把 P01 采用对应到 H01-01／07，把 P02 圣物对应到 H02-04／09；四项 claim 保留固定来源、行号和来源锁中的 SHA。原来源机器只提供历史来源事实；新拍仍须重新核当前机器、EXE／build、加载内容、存档、现场与容量。智能体可消费 `required_before_and_after_fields` 和 `agent_decision_outputs`，用同一数据链产出候选拒绝理由、资源预算、单次提交记录和独立后态比较。

从仓库根目录执行只读作者检查：

```text
tools/.venv/Scripts/python.exe -B promo/ck3_faith_and_power/integration/verify_authoring.py
tools/.venv/Scripts/python.exe -B promo/ck3_faith_and_power/integration/source_plan.py
tools/.venv/Scripts/python.exe -B -m xar_promo validate promo/ck3_faith_and_power/promo-project.json --profile authoring --json
```

第一条检查配置、四项来源 claim、两条未绑定试拍、安装 wheel 的 direct_url、真实 CLI help 与 `PipelineComposer` 签名；也验证缺素材时 `handle_plan` 拒绝，并验证生产 build 守卫。它不会调用 provider、录制、FFmpeg、游戏或创建 run/workdir。`--receipt <new-file>` 仅新写一份小型机器／UTC／来源完整的作者检查回执，拒绝覆盖。第二条默认输出仍为 pending 的索引；`--intake <existing-json>` 可重复传入未来实录步骤。未实录的正向 intake、正向媒体 plan 和渲染尚未验收。

## 未来真实 capture 的入口

实际 Python API 是 `faith_power_promo.evidence.build_evidence_index(plan_path, intake_paths, observer=...)`。`observer` 必须带本次机器 ID、UTC 和来源；脚本用 `tools/ck3_live_run_id.py machine` 新取身份。输入 intake 为 `ck3-faith-power-capture-intake-v1` JSON，其根字段如下；这是一份未来生产者需填写的合同，当前没有宣称存在这样的宗教 capture 文件。

| 字段 | 要求 |
| --- | --- |
| `pilot_id`／`step_id` | P01-adoption 或 P02-relic；不同供奉／取出步骤分别标识，不冒充一次动作。 |
| `identity` | 逐项满足 pilot-plan 的 required_identity_fields；本期只接受已锁定 1.20.0.4，其他 patch 先建立自己的来源绑定。确实不适用的 rite 等字段写有理由的对象，不能用 null 冒充身份。 |
| `native_chain` | 恰含 before、legality、decision、action、acknowledgement、after。每项为 `{"file":{"path":...,"bytes":...,"sha256":...},"json_pointer":...}`，指向保留的原生 JSON，不从 OCR 补造状态。 |
| `capture_root`／`clean_span_ids` | 现有 CK3 capture report、timeline、evidence index、raw 与 clean gates；经实际安装的 `xar_promo.adapters.ck3.capture.load_capture_bundle` 只读核验。接口不会制造或修补 GREEN report。 |
| `raw_start_seconds`／`raw_end_seconds` | 原片中一个 1× 连续区间，必须完整落在一段已核 clean span 内。 |
| `phase_raw_seconds` | 六个 native phase 在同一原片中的时码，顺序一致并位于区间内；最终成片时码继续为空。 |

原生 JSON pointer 选中的观察对象须有共同的 machine_id、episode_id、actor_id、faith_id、holy_site_instance_id，以及各自 observed_at_utc、evidence_source、frame、scene_revision。before／after 需有 query_id、state；after 另有 independent_readback=true，query_id 与前态和动作不同。legality 需保留 legal=true 和完整 requirements；decision／action／acknowledgement 共享 operation_id；action 的 submission_count 必须为 1。ACK status 如实为 accepted／rejected／unknown。来源 raw 不能直接满足该规范时，需实现有来源绑定的原生适配器，保留原回包；不能只手填一个“成功”规范化对象。

本接口只核绑定、身份与顺序，输出 `business_result_verified=false`。它没有宗教效果计算器，不凭 producer 的 legal/ACK 字段证明业务结论；实际增量、无效圣物边界和拒绝原因须由研究／智能体决策层对独立观察评估。缺任何一环就保留诊断。未知动作结果先查询当前状态，不重复提交。

## Composer 与原生 run

`faith_power_promo.composer:compose` 符合已安装 v0.3.0 的 `PipelineComposer` API；`components.registry()` 提供局部 adapter/preset 注入，不依赖另行安装本项目包，也没有虚构 xar-promo 子命令。可以使用实际 API：

```python
from xar_promo.pipeline_commands import handle_plan
from faith_power_promo.components import registry
from faith_power_promo.composer import compose

outcome = handle_plan(document_path, workdir=fresh_path, registry=registry(), composer=compose)
```

调用方需明确把本 integration 的 `src` 加入其 Python import 路径。未绑定的 ProjectConfig 返回 `No native run`；只保存作者输入的 run 缺少 `faith-production-inputs-v1` 时也拒绝。此诊断是预期的因果拍摄待完成边界。这个 `composer.py` 的 `validate_only=False` 继续一律拒绝；下节的上下文 renderer 使用独立合同，不能放宽其完整原生链门槛。

将来供只读媒体规划的 `faith-production-inputs-v1` artifact 须包含 schema=`ck3-faith-power-production-inputs-v1`、`evidence_index_artifact_id` 和非空 `cues`。每 cue 含 id／chain_id／claim_ids／shot_ids、zh／en、实测 speech_duration_seconds／duration_seconds，以及 audio_artifact_id、subtitle_ass_artifact_id、prepared_clip_artifact_id、clip_receipt_artifact_id。所有证据、源锁、索引、原片和引用原生回包必须先保全到同一 run；composer 按 bytes／SHA 解析已保全部件，不能直接读取 mutable 原路径充数。prepared clip receipt schema 为 `ck3-faith-power-prepared-capture-clip-v1`，需实际绑定 chain_id、raw_sha256、prepared_media、duration_seconds、fps=30、playback_speed=1，interpolation／looping／tail_padding 均为 false。该未来 positive path 尚无实录输入验证，不能称已生产可用。

当项目存储门禁允许小型作者存档时，可使用已核 CLI 创建 **authoring-only** run。以下 `<new-authoring-run>` 是操作者实际选择的新外置目录，不是当前已存在的生产 run：

```text
tools/.venv/Scripts/python.exe -B -m xar_promo start-run promo/ck3_faith_and_power/promo-project.json --run-id faith-source-authoring-a01 --run-directory <new-authoring-run>
tools/.venv/Scripts/python.exe -B -m xar_promo preserve promo/ck3_faith_and_power/pilot-plan.json --run-manifest <new-authoring-run>/run-manifest.json --artifact-id faith-pilot-plan-v1 --collection derived --role authoring-plan --media-type application/json
tools/.venv/Scripts/python.exe -B -m xar_promo preserve promo/ck3_faith_and_power/source-lock.json --run-manifest <new-authoring-run>/run-manifest.json --artifact-id faith-source-lock-v1 --collection derived --role source-provenance --media-type application/json
tools/.venv/Scripts/python.exe -B -m xar_promo validate <new-authoring-run>/run-manifest.json --profile authoring --json
```

额外保全作者检查回执／索引同样使用 `preserve`，每件唯一 artifact ID。冻结时把本次真实 toolchain version／wheel SHA、machine_id、UTC 和来源回执一并保全。不要执行 `build`；作者 run 与 schema 通过均不提供拍摄、宗教业务、clean、音频、视频或人工审阅信用。

## 第一期开篇的可复用生产入口

`episode01_production.py` 是本仓库脚本，直接调用工具链公开 Python API；它没有添加 xar-promo CLI 子命令。`context_composer.py` 从真实49.6秒试拍的 composer 提取，仍限于30–60秒准备／观察上下文。媒体工具、字体和原片路径全部由当次输入提供；库不查固定盘符、不取屏、不启动游戏，也不领取或绕开 screen keeper。

可在仓库根目录只读检查文稿、缓存指纹、未绑定守卫、源区间拒重叠和公共 render-planner 接口：

```text
tools/.venv/Scripts/python.exe -B promo/ck3_faith_and_power/integration/verify_episode01.py
tools/.venv/Scripts/python.exe -B promo/ck3_faith_and_power/integration/episode01_production.py --help
```

生成一份新的、未绑定媒体的作者 ProjectConfig（不调用TTS）：

```text
tools/.venv/Scripts/python.exe -B promo/ck3_faith_and_power/integration/episode01_production.py project --script promo/ck3_faith_and_power/episode01/script.json --output <new-external-project.json>
```

实际生产先在外置输入中填好 `runtime-input-template.json`，以当前机器 `tools/ck3_live_run_id.py machine` 身份绑定 FFmpeg／ffprobe／字体的路径、bytes和SHA。按通用存储策略取得当前机器、未来复核时间、并发预留和系统增长完整的共享容量回执；本脚本消费 `machine-storage-coordination-episode01-v1` 回执，不另造预留。`--package-root` 是当前获准工作包，`--reservation-task` 必须命中该回执的一条任务，`--peak-bytes` 是这次实际峰值估算，产物须位于工作包内。每次重型写入都重新读容量和本包占用，产出闭场读回；不够时拒绝。完整全片尚无获准编码预算，不能拿样段额度启动全片。

按冻结语音配方重新配音的实际入口如下。`synthesize` 会联网调用provider；复用现有音频直接进入下一条媒体入口。可选 `edge_tts_module_root` 选择外置provider安装，`tts_runtime_receipt` 保留其实际来源／版本／wheel SHA。当前配方的身份是 EdgeTTS7.3.1；更换版本或声音先冻结新指纹，不静默使用机器默认值。每句保存实际请求、音频SHA、ffprobe时长和失败记录；失败不自动重发，结果槽从不转为配音文本。

```text
tools/.venv/Scripts/python.exe -B promo/ck3_faith_and_power/integration/episode01_production.py synthesize --repo <repo-root> --script promo/ck3_faith_and_power/episode01/script.json --recipe promo/ck3_faith_and_power/episode01/tts-recipe.json --runtime <current-runtime.json> --reservation <current-reservations.json> --reservation-task <admitted-task> --package-root <approved-package> --peak-bytes <estimated-peak-bytes> --output <new-narration-attempt>
```

媒体复用入口接收 `ck3-faith-power-measured-narration-v1`（`cues[].id/audio/request/speech_duration_seconds`）与显式源选择。`audio`／`request`／原测量脚本均为path、bytes、SHA绑定。允许作者文档合并章节，但每句中文必须逐字匹配原provider请求，原测量脚本另行保全。跨机搬迁时显式更新当前位置的路径绑定，保留原始回执，不能把旧索引里的路径当目标机默认值。

```text
tools/.venv/Scripts/python.exe -B promo/ck3_faith_and_power/integration/episode01_production.py context-sample --repo <repo-root> --script promo/ck3_faith_and_power/episode01/script.json --measured <existing-measured-narration.json> --selection <bound-context-selection.json> --runtime <current-runtime.json> --reservation <current-reservations.json> --reservation-task <admitted-task> --package-root <approved-package> --peak-bytes <estimated-peak-bytes> --output <new-context-attempt>
```

`context-selection-template.json` 的每段绑定实际raw、只读raw审计、原Job终态和获准区间。审计 schema 是 `ck3-faith-power-raw-media-read-audit-v1`，必须匹配源机器、raw SHA及原始tree-empty终态；`ABORT_TREE_EMPTY` 原样保留，画面常显“中断RED”。调用会重新读取全部源帧PTS，以可解码末帧限制素材长度，不信容器声明的120秒或头部30fps。不同cue不能重复同一源区间，不循环、不变速、不补动态帧。VFR到CFR用原时钟持有／重复现有帧，字幕始终明示该派生关系。准备画面不冒充旁白中计划已完成。

公开 API 链为 `start_run → preserve_artifact(Path) → handle_plan → handle_build`。它保全作者输入、实际请求、音频、源审计、原终态、显式字体和生产源码；raw留在原证据位置，保留其精确绑定及FFmpeg argv。`context_composer` 仅从run解析已保全部件。字幕按实际字体测量中英各最多两行，游戏画面放在上方1120像素区域。通过工具链公开 `render_planner` 注入 `fontsdir`，不依赖 Windows 字体路径；随后输出全解码、实际容器时长、逐帧CFR PTS及cue/claim/source/raw到final区间映射。该路径不调用TTS。

每次 `synthesize`／`context-sample` 都重新查询官方 `releases/latest`，核对最新正式wheel的精确URL／SHA与当前解释器已安装的 `direct_url.json`，运行真实version/help/build-help，并核本次媒体工具SHA及version。发现新Release先升级并核API；生产入口不会用历史回执替本次检查。源码依赖下限不是“永远使用0.3.0”的生产许可。

2026-10-17真实样段的媒体通过范围与签核缺口以带machine_id的样段索引为准。当前提取后的可移植源码只做了离线合同／ProjectConfig检查；显式字体目录等变化尚未重新渲染，不把原机器样段的端到端通过自动移给这版入口。全片render、听审、完整1×和人工签核继续未完成。所有输出的业务／clean／人工审阅信用均为false，失败产物留在原attempt，新尝试必须另选目录。
