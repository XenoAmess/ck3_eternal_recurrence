# 天朝二期双成片交付闸门

## 交付定义

项目所有者要求保留并制作两种互不替代的导演版本。两条成片都是天朝二期最终交付物，不是“主版本 + 可选花絮”：

| 角色 | 叙事中心 | 最终文件名 |
|---|---|---|
| `character-led` | 跟随单个官员经历考核、校准、申诉与后果，承接一期的人物线 | `zhongguo-361-phase2-character-led.mp4` |
| `institution-led` | 以生产、批准并消化评级的制度为主角，展示跨人物、部门和周期的连锁作用 | `zhongguo-361-phase2-institution-led.mp4` |

总状态只有在两条视频分别完成候选检查、事实审计、两轮 1 倍速人工审看、导出和真实发布后才允许写
`COMPLETE`。任一条缺失或 RED 时，总状态固定为 `pending`；不得把其中一条、改名副本或同一候选文件冒充双片交付。

## 可以共享和必须分离的部分

两版允许使用同一份已验真的八段 Phase 2 CK3 实机源素材。这样不会为了不同剪辑重复触发 CK3，也不会把一期或
fixture 画面混入二期。双片 attestation 必须为每版列出相同顺序的八个 `span_id` 和逐字节 SHA-256；任一源段发生变化，
闸门会返回 RED。

以下边界必须分离：

- run / attempt ID；
- 工作目录；
- 最终候选 MP4 的 SHA-256；
- 候选与导出的文件名；
- 各自的单片 completion report，或各自完整的 candidate/export/review/publication receipts。

也就是说，源画面可以相同，导演结构、旁白、字幕、剪辑、成片审看和发布证据不能共用一个结果冒充两个版本。

## 工具

只读验收逻辑位于 `tools/zhongguo_phase2_dual_cut_completion.py`。它不会启动 CK3、TTS 或 FFmpeg，也不会生成、导出或发布
媒体。它接受两种单片证据输入：

1. `completion.mode = "report"`：引用已由单片闸门生成的 hash-bound completion report；
2. `completion.mode = "receipts"`：引用 hash-bound completion attestation、footage intake report 与 publish-target report，
   由工具重新调用既有单片 completion validator。双版自定义 artifact ID 可放在 `completion.deliverable_id`；未提供时兼容
   旧的 `zhongguo-361-phase2-video`。

输入的最小外形如下。`path` 必须是绝对路径，每个记录还必须带实际 `bytes` 与 `sha256`：

```json
{
  "schema_version": 1,
  "kind": "zg361_phase2_dual_cut_completion_attestation",
  "cuts": [
    {
      "role": "character-led",
      "output_name": "zhongguo-361-phase2-character-led.mp4",
      "work_dir": "Z:\\...\\phase2-character-led-run",
      "completion": {
        "mode": "report",
        "report": {"path": "Z:\\...\\completion-report.json", "bytes": 1, "sha256": "..."}
      },
      "source_spans": [
        {"span_id": "...", "media": {"path": "Z:\\...\\span.mkv", "bytes": 1, "sha256": "..."}}
      ]
    },
    {
      "role": "institution-led",
      "output_name": "zhongguo-361-phase2-institution-led.mp4",
      "work_dir": "Z:\\...\\phase2-institution-led-run",
      "completion": {
        "mode": "report",
        "report": {"path": "Z:\\...\\completion-report.json", "bytes": 1, "sha256": "..."}
      },
      "source_spans": [
        {"span_id": "...", "media": {"path": "Z:\\...\\span.mkv", "bytes": 1, "sha256": "..."}}
      ]
    }
  ]
}
```

运行：

```powershell
py tools/zhongguo_phase2_dual_cut_completion.py `
  --input <dual-completion-attestation.json> `
  --output <dual-completion-report.json>
```

输出路径已存在时工具直接拒绝覆盖。GREEN 报告中的七项 checks 必须全部为 `true`，且 `status` 才会是
`COMPLETE`。RED 报告会保留每版的具体错误，并只声明 `both_cuts_pending`，不会伪造成片、审看或发布 receipt。

## 测试

```powershell
py tools/test_zhongguo_phase2_dual_cut_completion.py
py -O tools/test_zhongguo_phase2_dual_cut_completion.py
py tools/test_zhongguo_phase2_final_promo_completion.py
py -O tools/test_zhongguo_phase2_final_promo_completion.py
```

fixture 中的所谓 MP4/MKV 只是少量非媒体字节，用于验证哈希、隔离和聚合逻辑；不得作为成片或实机素材证据。
