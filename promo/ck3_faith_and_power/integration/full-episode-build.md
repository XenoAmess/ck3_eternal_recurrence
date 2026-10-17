# 有界整期与采用审阅段

`episode01_full.py` 复用独立 `xar_promo_toolchain` 正式 Release 的 ProjectConfig、原生 run、字幕、render/concat planner 和审计命令。它只读取已经存在的实测配音、原片、机制图与原生查询原件；不访问游戏，不发起 TTS。`plan` 允许明确缺口，`build` 在任何输出前拒绝缺口。

两种 scope 分别为 `episode01-full-review`（20–31分钟）和 `episode01-adoption-review-segment`（3–5分钟）。后一种独立审阅段不代表整期完成。整期必须完整覆盖冻结的158句原声清单，或逐句说明删除原因；结果槽 `E01-L01/L02/L03` 始终保留，L01/L03在build时须绑定真实结果，L02可为null。

```text
<toolchain-python> -B promo/ck3_faith_and_power/integration/episode01_full.py plan --repo <checkout> --input <edit.json> --runtime <runtime.json> --reservation <active-ledger.json> --package-root <production-root> --output <new-plan-dir>
<toolchain-python> -B promo/ck3_faith_and_power/integration/episode01_full.py build --repo <checkout> --input <edit.json> --runtime <runtime.json> --reservation <active-ledger.json> --package-root <production-root> --output <new-build-dir> --workers 2
```

这些输入由目标机器重新生成，不将某台机器的媒体、路径、解释器或预算pin作为跨机资格。`runtime`声明实际FFmpeg、FFprobe和字体的path/bytes/SHA及字体家族；edit与存储账本均须标明当前机器ID。每次实际build重新核官方最新Release及安装wheel来源/SHA、解释器、工具help与字体。已有音频不复制、不重新配音。

`ck3-faith-power-full-edit-v1` 的 `cues` 包含原句ID、zh/en、claim_ids、shot_ids、audio、speech_duration_seconds、duration_seconds和visual_parts；原句文字、音频、provider request及实测时长须与assembly输入一致。结果槽包含独立before/action/after三份原件、具体JSON-pointer等值检查和逐句新实测音频。`sequence`恰好包含每个选中句子一次。

每个visual part有duration_seconds和disclosure；总时长严格覆盖实际配音对齐后的句子，不靠循环原片延长：

- `diagram`：image精确pin、live_result_depicted=false；单个图解focus最多6.4秒，标签说明版本及非实测动作。
- `native-readback`：image及native_card_receipt精确pin；图的每行由绑定原生原件的JSON指针直接生成，验值后才接入。图内明确说明“原生读回”“不是游戏UI”。`full_diagrams.render_native_card`保留全部原值与显示转换。
- `raw`：raw、raw_audit、source_index、source_frame_pts四份精确pin及raw_start_seconds。校验原片完整解码与机器ID，绑定全部真实帧PTS，保存实际选中帧索引/首尾PTS。中断原片必须明确RED；不同句子不能重复或重叠同一原片区间。VFR以显式最近帧规则转30fps，保留帧不冒充额外游戏时间。

编码固定2560×1440/30fps、x264 veryfast/CRF21、maxrate/bufsize各3,000,000、AAC192kbps/48kHz/stereo；每个输出有独立文件大小上限，最多2个segment并发、每encoder 2线程。31分钟/168段的保守新增峰值2,783,466,160字节，包含prepared visual、带声段、最终串联、侧车及包超量余量；这是上界估算，不是已发生占用。active v2账本将既有占用与未来3GiB承诺分别核算；build前重新检查机器、期限、增长、卷余量与项目quota，拒绝过期或不足准入。31分钟以上、168段以上须先修改并审查预算合同。

为避免成片重复四份，媒体直接写到原生run下的`derived/direct`并登记原文件；不会再制造媒体CAS副本或hardlink。仅小型输入目录、producer和实际环境/容量回执使用标准preserve。此处保留一个显式版本耦合接点：`direct_register`使用已核版本的`xar_promo.operations._replace_run`更新原生RunManifest并由load_document(check_files=True)验回，升级工具链时必须复核该接点。

一次build不自动重试。失败保留实际failure、部分输出与命令审计，修复后新attempt须重新准入。成功完成严格全音视频decode、实际声轨/尺寸/时长、全部最终视频帧PTS与CFR核对；raw-to-final-map记录每句及每part的最终帧区间、原片实际PTS、claim/shot/audio及来源。`ENCODED_REVIEW_PENDING`仍待完整播放、听审和人工签核，不自动授予业务或干净镜头资格。
