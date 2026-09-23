# V3 口播输入交接

后续执行状态：45 段口播已配音并进入[33:53.8 完整审阅片](../../build-records/v3-fullfilm-20260923-r1.json)；本页其余“尚待”“形成全片前”表述保留为输入准备时的步骤说明。成功生产 run 为 `v3-film-attempt-003`，失败 attempt 001/002 与所有原始素材仍分别保留。人工完整审片未签核。

`narration-spoken.json` 是 [导演旁白稿 v3](../narration-v3-review.md)中 45 个 **朗读** 段落的逐字提取；`timeline.json` 给每段独立 `S3-*` 镜头编号和标题。来源、制作备注、待拍标记、字数表均不进入 `zh` 配音字段。`build_inputs.py --check` 会重新提取并逐字节核对两个生成输入，检查 45 段顺序与 7516 个汉字的审阅合同。

`english-captions-draft.json` 是简写的英文字幕适配稿，尚待逐段编辑审阅；它不参与中文 TTS。最初的独立配音输入保留 `unbound-v3-shot`，不追改已生成的音频 attempt；[V3 逐段证据表](evidence-ledger-notes.md)现将 45 段分别绑定到有限实机读回、静态规则或明确算例。`integration/bind_v3_production_inputs.py` 从实测配音输入生成新的来源绑定文件，逐项核对音频、口播请求与 ledger。现有 `S30-*` 镜头属于旧稿，不能用编号相同这一点替换 `S3-*`。

已用本隔离工作区 `tools/.venv/Scripts/python.exe` 核对 `xar-promo 0.2.1`、`xar_promo --help`、`xar_promo plan --help`、当前 `war_ai_promo.prepare_narration --help` 与 `war_ai_promo.produce --help`。每个新的 xar-promo run 仍应按项目指南查询当时最新正式 release；本页的版本只是本次核验记录。

从仓库根目录运行文本和逐段证据合同检查：

```text
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\longform\v3\build_inputs.py --check
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\longform\v3\build_evidence_ledger.py --check
```

在确定英文字幕已审阅或明确作为内部配音素材试制时，可以把这份独立输入交给当前 EdgeTTS 准备器。输出必须是**不存在的新目录**，例如：

```text
tools\.venv\Scripts\python.exe -m war_ai_promo.prepare_narration --script promo/ck3_native_war_ai/longform/v3/narration-spoken.json --timeline promo/ck3_native_war_ai/longform/v3/timeline.json --provider edge --voice zh-CN-XiaoxiaoNeural --rate -12% --output D:/workspace/ck3_native_war_ai_promo_work/v3-speech-attempt-001
```

该命令保全每段 TTS 请求、返回、失败 attempt、边界事件与媒体探测，并写出实测 `production-inputs.json`。当前 45 段 EdgeTTS 实测总长 `2033.90` 秒。形成可审的新版全片前，先用 `integration/bind_v3_production_inputs.py` 核对并绑定这次实测输入；用 `integration/bind_v3_context_frames.py` 冻结 CASE-R/W 原始抽帧；再用 `integration/plan_v3_capture_selection.py` 从已审窗口生成 `--capture-spec`。V3 composer 按证据表调用独立画面模块，原始录像进入片中时常驻 CASE-W/C 情境标签；未绑定段会直接失败，不会回退到旧教学画面。英文字幕仍需逐段审阅，自动包、自动审计与抽帧均不能替代人工 1× 全片观看。

完成上述逐段绑定以后，新 run 的 producer 命令形状如下；`NEW_RUN_ID` 必须替换为不存在的新目录/ID，不得重用既有 attempt。`v3-capture-spec-r1.json` 与 `v3-context-frames-r1.json` 必须是实际生成、经审阅的素材选择和来源清单。跨 run 复用本次已保全的五段 capture 时，可显式添加 `--reuse-captures-from D:/workspace/ck3_native_war_ai_promo_work/v3-film-attempt-003`，由 producer 核对源资产精确字节：

```text
tools\.venv\Scripts\python.exe -m war_ai_promo.produce --project promo/ck3_native_war_ai --inputs D:/workspace/ck3_native_war_ai_promo_work/v3-production-inputs-bound-r1.json --run-root D:/workspace/ck3_native_war_ai_promo_work/NEW_RUN_ID --run-id NEW_RUN_ID --full-film --capture-spec D:/workspace/ck3_native_war_ai_promo_work/v3-capture-spec-r1.json --v3-assets D:/workspace/ck3_native_war_ai_promo_work/v3-context-frames-r1.json
```
