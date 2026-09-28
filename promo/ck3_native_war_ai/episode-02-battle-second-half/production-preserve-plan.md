# 第二期六章生产输入预检

`prepare_production_inputs.py` 只读取原件并校验显式 `bytes` / SHA-256；可选地在一个**新建的仓库外目录**写出 `production-inputs.json`、`preserve-plan.json`、`source-audit.json`。它不启动游戏、不探测或编码媒体、不创建 `xar-promo` run，也不制造人工审片结论。`source-audit.json` 的成功状态只代表这次机器来源预检。

先按仓库 `AGENTS.md` 查询最新正式 `xar-promo` Release，验证所用解释器与 wheel。相对 `.venv` 缺失的工作树须显式使用已验证的主工作树解释器。真实素材齐备后，调用：

```text
<verified-python> promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_production_inputs.py --declaration <absolute-declaration.json>
<verified-python> promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_production_inputs.py --declaration <absolute-declaration.json> --output-directory <new-absolute-external-attempt>
```

第一条纯只读；第二条只新增一个外置 attempt。任一来源不存在、哈希/长度变化、六章不足、TTS 原始请求/事件与字幕边界不符、缺少 GREEN clean span、来源标签帧不匹配、旧研究卡被冒充为新数值，均拒绝生成可用清单。E2-02/03 a01/a02 稀疏索引和未审原片不能充当 GREEN clean span；未到齐的 E2-09 原片也不能借旧 024 卡补位。

声明 JSON 的顶层字段：

| 字段 | 内容 |
| --- | --- |
| `schema` | `ck3-war-ai.episode02.production-declaration.v1` |
| `human_signoff` | `not-provided` |
| `project_config`, `narration_script`, `card_index`, `subtitle_fragments`, `subtitle_preserve_plan` | 各自 `{source, bytes, sha256}`，`source` 为绝对路径 |
| `subtitle_source_root` | 覆盖 70 件原始 TTS run、manifest、MP3、请求与 Edge 事件的绝对目录 |
| `cards` | 9 个卡 ID 对应的 SVG `{source, bytes, sha256}`；须是卡索引旁的原件 |
| `music` | `{artifact_id: "episode02-series-theme", source, bytes, sha256}` |
| `source_artifacts` | 六章 reel receipt 引用的 save、raw、control、clean span、label、label frame、完整逐帧 ffprobe JSON、`recorder-final.json`、历史卡可见标签或当次重算回执的 `{artifact_id, source, bytes, sha256, role}`；集合必须恰好匹配 receipt 所引用的 ID |
| `chapters` | 按 `opening,pursuit,knights,reinforcement,terminal,closing` 排列的 6 条 `{id,title,en,duration_seconds,reel,reel_receipt}`，其中 `reel` 和 `reel_receipt` 均为 `{source,bytes,sha256}` |

所有声明文件须先由实际原件产生，绝不能把样片、静态计划、命令 ACK、稀疏帧索引填进真实 reel 或 GREEN clean span 字段。`title` 与 run 配置快照逐章相同；`en` 是实际采用的英语字幕文案；时长不短于来源 TTS。

每条真实 `capture_spans` 还须给 `raw_video_pts_probe_artifact_id/sha256/bytes` 和 `raw_video_recorder_final_artifact_id/sha256/bytes`。预检与正式 composer 均核对 recorder-final 对 raw 与完整 ffprobe 的精确身份，按 CK3 adapter clean span 的 begin/end 在完整 frame PTS 表中逐帧检查：首尾各有 200 ms 内的实际帧、内部 PTS 严格递增、相邻帧间隔不超过 200 ms。整条 raw 可在别处断档，但任何跨越断档的 clean span 必须 RED。`ENCODED_UNREVIEWED` 或稀疏 mark 的最近帧仅供定位，不能代替该检验。

通过预检后，另用最新正式 `xar-promo start-run` 从同一 `ProjectConfig` 建新原生 run；检查 run 快照字节与清单一致。随后按 `preserve-plan.json` 每项的 `artifact_id`、`collection`、`role` 和 `source`，用 `xar-promo preserve` 在该 run 中保全，逐项回读 artifact ID / SHA / bytes。`preserve-plan.json` 最后一项是生成的 `episode02-production-inputs-v1`。只有完成原生 run 保全并再次运行 `validate` / `plan` 后，才能在新的外置 build attempt 调正式六章组装。任何失败 attempt 保留原样，重做使用新的 run/workdir。
