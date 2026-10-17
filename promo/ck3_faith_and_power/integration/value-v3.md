# Value v3：实际语音、证据与剪辑输入

此入口把已实测的中文语音、英文副字幕、来源与原片时码汇合成正式剪辑输入。它不把目录里存在的文件自动认定为已审阅素材，也不把调用回执认定为游戏结果。播放器正文使用玩家语言；机器、场次、来源、未知项及实机观察保存在旁注和索引。

## 作者输入

`faith_power_promo.formal_episode` 接受 `schema: "ck3-faith-power-value-v3-formal-edit-v1"`。输入至少包含：

```json
{
  "schema": "ck3-faith-power-value-v3-formal-edit-v1",
  "machine_id": "<实际目标机器 ID>",
  "scope": "episode01-formal-review",
  "voice_authoring_catalog": {"path": "<语音目录>", "bytes": 0, "sha256": "<实际 SHA>"},
  "cue_evidence_catalog": {"path": "<逐句证据目录>", "bytes": 0, "sha256": "<实际 SHA>"},
  "result_voice_batches": [],
  "project_config": {"path": "<原生 ProjectConfig>", "bytes": 0, "sha256": "<实际 SHA>"},
  "storage_reservation": {"path": "<当前已激活的预算>", "bytes": 0, "sha256": "<实际 SHA>"},
  "pending_result_slots": {
    "after_V3-N018": null,
    "after_V3-N068": null,
    "after_V3-N083": null
  },
  "excluded_cues": [],
  "sequence": ["<实际选择顺序>"],
  "cues": []
}
```

这只是字段示意，零字节与占位 SHA 不是可运行输入。所有文件引用都要用真实绝对路径、字节数和 SHA。跨机器可以复用代码与研究知识；媒体、解释器、工具链、容量与游戏结果必须核对机器及当次实际证据。

`voice_authoring_catalog` 读取 `faith-power-value-v3-voice-authoring-catalog-v2`，其中 `cues` 给出 `id / zh / en / audio / provider_request / speech_duration_seconds / duration_seconds`。它是实际语音的作者投影，不取代原始 TTS 文本及请求冻结。选择的旧句必须逐字段保持这些值。不能把旧音频套到改写后的中文。

`cue_evidence_catalog` 读取 `ck3-faith-power-value-v3-cue-evidence-v1`，其句子集合应恰好覆盖旧语音目录。每句的 `claim_ids`、`shot_ids` 由证据目录提供；来源引用使用文件精确 pin 加 `first_line / last_line` 或 `json_pointer`。静态规则、历史实测和本次实测须分清，未知项与每项结论的限制会带入计划。

实际 `ProjectConfig` 使用 `kind: "xar_promo_project_config"`，由工具链的 `ProjectConfig.from_mapping` 验证。把所有章节的 `cues` 展平后，顺序必须与 `sequence` 完全相同；中文 `narration["zh-CN"]`、中英 `subtitles` 必须逐字等于所选实际语音文本。新增结果句也必须进入此配置。

## 新结果批次

每个 `result_voice_batches` 元素引用 `text_freeze / measured_voices / result_evidence` 三个精确文件。三者必须属于目标机器；实际测量文件须指向同一文本冻结且 `failures` 为空。新批次的文本与音频句子集合必须一致，不得与旧语音或另一新批次重复。

结果证据包含 `claims / native_checks`，可以含 `cues: [{id, claim_ids, shot_ids}]`。每个结果 claim 必须引用非空、实际核对的 native check：

```json
{"id":"<check-id>","file":{"path":"<原生回执>","bytes":0,"sha256":"<实际 SHA>"},"json_pointer":"/result/field","equals":false}
```

`equals` 是实际值，可以是 `false`、空数组或明确读出的 `null`；缺少观测不能伪装成这些值。一次提交、正常合法性、独立后态与原片像素分别记录。规则判断还要绑定其源码；例如行动者恰好也是当地领主的个案，不能独立证明两种角色的接收者规则。

实际结果及新声都已绑定后，相关槽才改成 `{"status":"observed-bound","cue_ids":["<实际新句 ID>"]}`。`null` 继续表示缺口；此格式下把槽标为 omitted 仍是缺口。完整选择集合与有理由的 `excluded_cues` 必须恰好划分全部旧、新语音。

## 只生成元数据计划

在仓库根、已验证工具链解释器中，把 `promo/ck3_faith_and_power/integration/src` 加入 Python 模块路径，然后运行：

```text
python -B -m faith_power_promo.formal_episode plan --metadata-only --repo <仓库根> --input <实际剪辑输入.json> --output <新的计划目录>
```

或者用现有包装入口 `python -B promo/ck3_faith_and_power/integration/episode01_formal.py plan --metadata-only ...`，由入口配置模块路径。

此分支校验有界文本元数据、来源片段、素材索引及原片逐帧 PTS；媒体只核路径、大小与 mtime，继承声明的 SHA，不重新读取媒体字节、不解码、不编码。输出明确区分 `content_ready` 与 `ready_to_build`：元数据计划始终 `ready_to_build: false`、`fullrender_admitted: false`，且不扫描生产目录、不调用容量准入 helper。不要拿它替代原片 QA、当次正式工具链资格或完整制作准入。

每句的 `visual_parts` 可使用现有 `raw / mechanism-motion / diagram / native-readback`。raw 必须绑定原片审计、素材索引及逐帧 PTS；选中的真实时间区间不重叠，不循环或慢放来补片长。机制动画须有实际完成的素材、生成输入与来源片段；未制作素材或空视觉列表是明确缺口。原生读回图与实机画面应分别标注，不用读回图冒充录到的动作。

## 分组字幕

句子可给 `subtitle_groups`，每组包含 `start_seconds / end_seconds / zh / en`。范围须有限、正长度、有序、无重叠，且在未修改的实测语音范围内；同一语言按顺序直接拼接，必须逐字等于整句，包括空格和标点。`subtitle_start_seconds` 默认为零。

同一个分组函数生成画面 ASS 与最终时码 SRT。无分组时保留旧入口行为。分组合同通过仅证明时序和文本自洽；并不证明真实词边界或声画因果已经人工审阅。结果字幕要另绑实际原片后态的可见门槛，不能在提交之前先显示成功或扣款。

## 正式制作

普通 `plan / build` 仍需要原入口的 runtime、当前预算、package-root、存储 helper 与 allocation-reader 等参数，详见该入口 `--help`。正式制作前重新核官方最新正式 Release、实际解释器、wheel 来源与安装 RECORD、相关帮助及当次容量；不能将历史资格外推为本次资格。只有最终主源冻结后才固定 producer/source snapshots。

制作保持最多31分钟、168个语音段、2560×1440 / 30fps、视频 maxrate/bufsize 3Mbps，直接产物模式，不无意义复制大媒体或另入 CAS。一个语音段可含多个视觉部分，视觉部分数不是语音段数。具体准入用实际新音频时长、段数与既有已用增长加剩余写入峰值；已完成的语音、图解和 QA 不再整额重复计入未来，也不重置原点或补满额度。

完成后交付实际 MP4、中英字幕、最终逐句稿、章节、claims 与 raw/final PTS 索引，以及解码、声轨、字幕和来源 QA。完整人耳听审及1倍速签核未完成时应继续标 pending。第一期最终稿入口为同目录上级的 `../episode01/narration-v3-final.zh.md`，英文为 `narration-v3-final.en.md`，原始 `narration-v3.zh.md` 保留其既有字节与语音来源身份。
