# 宗教试拍的规划与证据接线

当前只交付可审阅的作者输入与只读接口。两条试拍仍是 `CAPTURE_PENDING`，未绑定原片、原生动作、音频、实际时长或最终时码。没有通过生成静态卡补足动态镜头。ProjectConfig 三章均为 `planned`，旁白 cue 留空，等待同场实验结果及实测音频。

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

调用方需明确把本 integration 的 `src` 加入其 Python import 路径。未绑定的 ProjectConfig 返回 `No native run`；只保存作者输入的 run 缺少 `faith-production-inputs-v1` 时也拒绝。此诊断是预期的拍摄待完成边界，不能改写为成片通过。现在 `validate_only=False` 一律拒绝；render、字幕布局、声画、PTS 和人工 1× 审片未取得资格。

将来供只读媒体规划的 `faith-production-inputs-v1` artifact 须包含 schema=`ck3-faith-power-production-inputs-v1`、`evidence_index_artifact_id` 和非空 `cues`。每 cue 含 id／chain_id／claim_ids／shot_ids、zh／en、实测 speech_duration_seconds／duration_seconds，以及 audio_artifact_id、subtitle_ass_artifact_id、prepared_clip_artifact_id、clip_receipt_artifact_id。所有证据、源锁、索引、原片和引用原生回包必须先保全到同一 run；composer 按 bytes／SHA 解析已保全部件，不能直接读取 mutable 原路径充数。prepared clip receipt schema 为 `ck3-faith-power-prepared-capture-clip-v1`，需实际绑定 chain_id、raw_sha256、prepared_media、duration_seconds、fps=30、playback_speed=1，interpolation／looping／tail_padding 均为 false。该未来 positive path 尚无实录输入验证，不能称已生产可用。

当项目存储门禁允许小型作者存档时，可使用已核 CLI 创建 **authoring-only** run。以下 `<new-authoring-run>` 是操作者实际选择的新外置目录，不是当前已存在的生产 run：

```text
tools/.venv/Scripts/python.exe -B -m xar_promo start-run promo/ck3_faith_and_power/promo-project.json --run-id faith-source-authoring-a01 --run-directory <new-authoring-run>
tools/.venv/Scripts/python.exe -B -m xar_promo preserve promo/ck3_faith_and_power/pilot-plan.json --run-manifest <new-authoring-run>/run-manifest.json --artifact-id faith-pilot-plan-v1 --collection derived --role authoring-plan --media-type application/json
tools/.venv/Scripts/python.exe -B -m xar_promo preserve promo/ck3_faith_and_power/source-lock.json --run-manifest <new-authoring-run>/run-manifest.json --artifact-id faith-source-lock-v1 --collection derived --role source-provenance --media-type application/json
tools/.venv/Scripts/python.exe -B -m xar_promo validate <new-authoring-run>/run-manifest.json --profile authoring --json
```

额外保全作者检查回执／索引同样使用 `preserve`，每件唯一 artifact ID。冻结时把本次真实 toolchain version／wheel SHA、machine_id、UTC 和来源回执一并保全。不要执行 `build`；作者 run 与 schema 通过均不提供拍摄、宗教业务、clean、音频、视频或人工审阅信用。
