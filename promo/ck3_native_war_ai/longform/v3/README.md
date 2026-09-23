# V3 口播输入交接

`narration-spoken.json` 是 [导演旁白稿 v3](../narration-v3-review.md)中 45 个 **朗读** 段落的逐字提取；`timeline.json` 给每段独立 `S3-*` 镜头编号和标题。来源、制作备注、待拍标记、字数表均不进入 `zh` 配音字段。`build_inputs.py --check` 会重新提取并逐字节核对两个生成输入，检查 45 段顺序与 7516 个汉字的审阅合同。

`english-captions-draft.json` 是简写的英文字幕适配稿，尚待逐段编辑审阅；它不参与中文 TTS。新镜头目前全部标为 `unbound-v3-shot`，未与实机、图解或原生面板逐段绑定。`claim_ids` 为空，待新版逐条台账与可用实机证据定稿后再绑定。现有 `S30-*` 镜头属于旧稿，不能用编号相同这一点替换 `S3-*`，否则会出现叙事和画面错位。

已用本隔离工作区 `tools/.venv/Scripts/python.exe` 核对 `xar-promo 0.2.1`、`xar_promo --help`、`xar_promo plan --help`、当前 `war_ai_promo.prepare_narration --help` 与 `war_ai_promo.produce --help`。每个新的 xar-promo run 仍应按项目指南查询当时最新正式 release；本页的版本只是本次核验记录。

从仓库根目录运行文本合同检查：

```text
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\longform\v3\build_inputs.py --check
```

在确定英文字幕已审阅或明确作为内部配音素材试制时，可以把这份独立输入交给当前 EdgeTTS 准备器。输出必须是**不存在的新目录**，例如：

```text
tools\.venv\Scripts\python.exe -m war_ai_promo.prepare_narration --script promo/ck3_native_war_ai/longform/v3/narration-spoken.json --timeline promo/ck3_native_war_ai/longform/v3/timeline.json --provider edge --voice zh-CN-XiaoxiaoNeural --rate -12% --output D:/workspace/ck3_native_war_ai_promo_work/v3-speech-attempt-001
```

该命令保全每段 TTS 请求、返回、失败 attempt、边界事件与媒体探测，并写出实测 `production-inputs.json`。它只完成配音准备。形成可审的新版全片前，还须把每个 `S3-*` 接到真实镜头或与该段相符的图解，复核英文字幕和逐条主张，按实测音频选择无循环、无伪同步的片段，然后以新的 run 调用现有 `war_ai_promo.produce --full-film --capture-spec ...`。当前 composer 的未绑定段会进入旧程序化画面分派；在完成逐段绑定前，直接调用 produce 会生成错位画面，因此不得作为 v3 成片交付。

完成上述逐段绑定以后，现有 producer 的真实命令形状如下；其中 `v3-capture-selection-reviewed.json` 必须是届时实际生成、经审阅且能通过导入器的素材选择文件，不能创建空文件充数：

```text
tools\.venv\Scripts\python.exe -m war_ai_promo.produce --project promo/ck3_native_war_ai --inputs D:/workspace/ck3_native_war_ai_promo_work/v3-speech-attempt-001/production-inputs.json --run-root D:/workspace/ck3_native_war_ai_promo_work/v3-film-attempt-001 --run-id v3-film-attempt-001 --full-film --capture-spec D:/workspace/ck3_native_war_ai_promo_work/v3-capture-selection-reviewed.json
```
