# 天朝二期双版本制作合同

状态：**两版均为 authoring draft / 非 live / 未生成媒体**。

用户要求保留并制作两种不同导演思路。本合同让它们共享同一组八段真实 CK3 原始证据，同时拥有各自独立的剪辑、旁白、运行目录、
候选交付物和最终审阅链。共享素材不等于共享叙事结论；任何跨人物、跨案件或跨周期关系仍须由画面明示，不得靠剪辑补出因果。

## 两个版本

| 剪辑 ID | 导演主角 | 项目配置 | 声明/旁白账本 | 默认运行 ID | 候选交付物 |
|---|---|---|---|---|---|
| `character-led` | 一名官员走过完整考核季 | `phase2-promo-character-project.json` | `phase2-authoring-character-claims.json` | `phase2-character-led-candidate` | `zhongguo-361-phase2-character-led-video` → `deliverable/zhongguo-361-phase2-character-led.mp4` |
| `institution-led` | 制造、批准并延续一个 C 的制度 | `phase2-promo-institution-project.json` | `phase2-authoring-institution-claims.json` | `phase2-institution-led-candidate` | `zhongguo-361-phase2-institution-led-video` → `deliverable/zhongguo-361-phase2-institution-led.mp4` |

两份权威导演处理稿分别为 `phase2-character-director-treatment.md` 与
`phase2-institution-director-treatment.md`；它们与本文件分工：处理稿决定戏剧结构，本文件决定两条可复现的制作与证据边界。

外部 `zhongguo_361_phase2` preset 的底层 `project.id` 仍必须是 `zhongguo-361-phase2-promo`。两版的项目级身份由不同配置路径、标题、
cue ID 前缀和配置文件 SHA 共同确定；剪辑级身份由上表的 cut/run/artifact/output 四组互不相同的 ID 确定。不得为了让底层 ID 看起来不同而
修改已发布 preset 或绕过其验证。

## 共享八段，独立成片

两版都严格消费以下 canonical spans，顺序和 provider postcondition 不变：

1. `phase2_fact_quota_calibration`
2. `phase2_receipt_appeal_pip`
3. `phase2_manager_governance`
4. `phase2_promotion_compensation`
5. `phase2_hc_workforce`
6. `phase2_projects_metrics`
7. `phase2_incidents_operations`
8. `phase2_cross_cycle_endgame`

允许共享的是已经通过 intake 的原始录像、timeline、evidence index、clean frames 和其字节哈希。两版必须分别完成以下内容：

- 根据各自处理稿做第一次 1× 素材审阅，并只提升画面真正支持的 cue；
- 使用各自配置 SHA 生成/绑定媒体环境 receipt；
- 使用不同 `work-dir` 与 `run-id`；
- 分别做 claims audit、最终 1× 审阅、signoff、export 和 publication receipt；
- 任一版本失败或被驳回，不得借用另一版本的审阅结果给自己开绿灯。

内容寻址的 Xiaoxiao TTS cache 可以共用，但两个版本不同的 cue 文本会自然得到不同缓存键。相同句子复用相同音频字节是缓存命中，不是
审阅复用。

## 当前 authoring 边界

两个 cut ledger 都是覆盖层：它们只替换旁白、双语字幕和开场/尾卡标题。八段 footage binding、required postcondition、可见观测清单、
evidence path 与 cannot-claim 规则全部从 `phase2-authoring-claims.json` 按 SHA-256 继承。validator 会先展开覆盖层再跑原有完整校验，
因此某个版本不能通过删掉 claim 字段来放宽证据要求。

当前两份项目仍保持全部章节 `planned`、`cues=[]`、`artifact_ids=[]`；两份 cut ledger 的所有 cue 仍为
`release_usable=false`。这表示剧本已经落盘，但真实镜头尚未到齐，不能称作 candidate、live、release-ready、exported 或 published。

## 无媒体校验

```powershell
py mod_zhongguo_style/tools/validate_phase2_authoring_claims.py `
  --ledger mod_zhongguo_style/promo/phase2-authoring-character-claims.json `
  --validate-only

py mod_zhongguo_style/tools/validate_phase2_authoring_claims.py `
  --ledger mod_zhongguo_style/promo/phase2-authoring-institution-claims.json `
  --validate-only
```

两份 no-media runbook 使用同一个 `<GREEN_EIGHT_SPAN_CAPTURE>`，但必须指定不同的新目录：

```powershell
py tools/plan_zhongguo_phase2_final_promo.py `
  --project-config mod_zhongguo_style/promo/phase2-promo-character-project.json `
  --authoring-ledger mod_zhongguo_style/promo/phase2-authoring-character-claims.json `
  --capture-root <GREEN_EIGHT_SPAN_CAPTURE> `
  --tts-cache <SHARED_CONTENT_ADDRESSED_CACHE> `
  --work-dir <NEW_CHARACTER_WORK_DIR> `
  --output <NEW_CHARACTER_RUNBOOK_JSON>

py tools/plan_zhongguo_phase2_final_promo.py `
  --project-config mod_zhongguo_style/promo/phase2-promo-institution-project.json `
  --authoring-ledger mod_zhongguo_style/promo/phase2-authoring-institution-claims.json `
  --capture-root <GREEN_EIGHT_SPAN_CAPTURE> `
  --tts-cache <SHARED_CONTENT_ADDRESSED_CACHE> `
  --work-dir <NEW_INSTITUTION_WORK_DIR> `
  --output <NEW_INSTITUTION_RUNBOOK_JSON>
```

runbook 会把正确的 `--cut`、配置、默认 run ID、artifact ID 与输出路径写入后续命令。正式制作前仍须先 fresh fetch/fast-forward
宣传工具并证明 clean 且 `HEAD == origin/main`；本文和 validate-only 结果都不能替代该前置条件。

## 旧入口兼容

`phase2-promo-project.json`、`phase2-authoring-claims.json`、`phase2-candidate`、`zhongguo-361-phase2-video` 和
`deliverable/zhongguo-361-phase2.mp4` 暂时保留为 legacy single-cut 合同，供旧 receipt、测试和命令复核。新的双成片生产不得继续使用
legacy 名称，以免审阅者无法判断正在签哪一个版本。
