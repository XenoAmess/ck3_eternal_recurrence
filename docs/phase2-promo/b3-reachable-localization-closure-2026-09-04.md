# B3 reachable localization closure（2026-09-04）

状态：**static-ready / no-launch**。本工作包没有启动 CK3，不能据此声称 loader、Frontend、业务路径或素材 GREEN。

## 缺口与优先级

B3 r5 已证明 product 的 event/effect/trigger fixed point 会引入七个事件用途族，但旧的
`tools/expand_zg361_phase2_b3_projection_closure.py` 只同步
`zg361pp.9004.{t,desc,a}` 三个 key。结果是代码调用闭包虽为 GREEN，投影仍缺少 63 个真实 localization provider；
r5 实机日志因此保留 952 行、816 个唯一 key 的 localization 噪声。false-stub 单变量诊断已经完成后，这个缺口成为不依赖当前
seed freshness blocker、且能独立施工的最高优先静态产品包。

## 实现

closure expander 的 schema 提升到 3，并执行以下顺序：

1. 先递归物化 effect、event、trigger provider，直到 custom-call fixed point；
2. 再按最终 candidate 中实际存在的事件 owner，选择七个已取证用途族；
3. 对每个用途族同步 9 个语言 provider 的 canonical 完整文件，而不是抽取或拼装个别 key；
4. 检查每个文件有 UTF-8 BOM、九语言 key 集与英文一致；法、德、日、韩、波、俄、西七种非创作语言的值必须逐 key 与英文占位一致；
5. 最终 candidate provider 必须与 canonical source 逐字节相等，并写入文件数、字节数和
   `relative-path<TAB>bytes<TAB>sha256` 清单摘要。

用途族固定为：

- `zg361_career_hc`
- `zg361_career_learning`
- `zg361_compensation_runtime`
- `zg361_credit_project`
- `zg361_feedback_promotion_pip`
- `zg361_phase2_central`
- `zg361_phase3_metrics_delivery`

formal B3 no-launch verifier 同步收紧：schema 2 的旧三-key evidence 不再能通过；必须看见完整七族、63 个 provider、exact-byte
标记、无最终缺 key、非创作语言英文占位一致，以及合法的 provider inventory SHA-256。这里没有新增或修改翻译正文，日常语言策略仍是
只创作中英，其余语言保留英文占位。

## 真实静态重放

以 canonical commit `06940744807b5096343c47ed275c551263a477d4` 和既有 565-file B3g product 为输入，复制到独立目录后执行
新 expander：

```text
artifact: Z:\ck3_mod_rewrite_process_assets\zg361\b3-localization-closure-static-0694074-20260904T120500Z
closure-expansion.json SHA-256: 115AC7FFAFF8B663214EACC24D8053211F9603CD26A25AAF5154358DB46753F9
schema_version: 3
green: true
code providers added: 0
final missing effects/events/triggers: 0/0/0
required localization families: 7
required provider keys: 936
provider files: 63
provider bytes: 685315
provider inventory SHA-256: 541a3e0e2f580f1811b81fb186d11ece335a1c76daaa0328733b0af8351b6226
final_missing_by_language: {}
placeholder_values_match_english: true
provider_files_exact: true
formal closure_expansion_evidence: GREEN
```

`936` 是七个完整 provider 的 key 总数；历史日志中的 `816` 是当次 candidate 实际引用并报错的唯一 key 数，两者不是同一口径。
完整 provider 同步有意包含该用途族内尚未在该日志出现的 key，避免下一条已可达分支再次产生同类缺口。

## 测试与文件边界

- closure expander：普通与 `-O` 各 `4/4` GREEN；覆盖七族 63-file fan-out、递归新增 event 后再补 loc、BOM/精确复制，以及非创作语言擅自翻译时 fail-closed。
- B3 formal no-launch verifier：普通与 `-O` 各 `15/15` GREEN；包含旧 schema 2 / 三-key evidence 必须被拒绝的回归测试。
- effect boundary：普通与 `-O` 各 `4/4` GREEN；当前 427 个 effect 文件、3,719 个 definitions，B2+ 非 legacy 单文件最大 10，目标 miss 0、超过 20 的违规 0。

本工作包没有改任何 effect 文件，所以没有产生新的文件体量假设或加载性能 A/B。现有经验边界保持：遇到实机加载性能 RED 才按用途继续拆分并做
单变量实机取证；本次修复针对的是已复现的 localization provider 缺失，不把它包装成文件过大根因。

## 剩余 live 边界

新 evidence 只证明投影生成与 formal no-launch 合同闭合。必须在后续独占 CK3 轮次使用新生成的 exact product，才可验证
`error.log` 的 952 行 localization 噪声是否归零；在此之前不得把本页写成 loader/live GREEN。当前 seed inventory freshness blocker 也未由本工作包处理或绕过。
