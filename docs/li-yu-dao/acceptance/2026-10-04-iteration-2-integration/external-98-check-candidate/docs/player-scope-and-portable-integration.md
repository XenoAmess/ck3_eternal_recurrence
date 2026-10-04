# I2 candidate002：全部受影响玩家与可复现原生 admission

本目录是当前交付候选；复制来源 candidate001 的 85 项源码、报告、index 均已冻结原样保存于原目录。这里保留的旧 `candidate-report.json` / `candidate-index.json` 及旧 nonce review 属于历史输入。当前状态和文件清单以新增 `candidate-report-v2.json` / `candidate-index-v2.json` 为准。

同意集合现在包含来源移动 Rite 及接收 Faith 每个 Rite 中**所有活着的人类玩家**，包含无地者/冒险者，不要求学识、爵位、成年或囚禁状态。来源和接收集合、首次计数、逐人变量、最终快照刷新和 callback eligibility 一致；发起者仍需成年、有地、合格玩家，NPC 学者投票资格保持原来的存活、成年、未囚禁、非无能、学识至少15。低学识无地玩家不会制造额外学者票，但不回复或拒绝会阻止迁移。玩家事件的实际多人送达仍需 R4，离线模型不能代替多人实机。

事件与共享 I3 export 的 ID/参数不变，R4 夹具不需要改接口。nonce、vote_nonce/player_nonce 和历史序号规则沿用 candidate001；旧85 proof保持有效的历史字节，没有改写为新结果。

## 可移植 admission 的边界

保留原 `native_admission_v2.py` 作为严格外置审计验证器；它在原 proof 条件下可以重哈希大存档、原生源文件和完整外置日志。构建/CI使用新的 `native_admission_portable.py` 和小型 SOURCE 输入 `tools/reference/native-primitive-tracked-admission.json`。后者绑定仓库已保存的 R0002 原始 attestation、保存对象摘要、原始 marker 摘录、当时实际加载的两份 probe 源码、错误分类及4份对象摘录，共10个 checkout-relative 路径，逐文件精确SHA验证；同时检查三轮计数、保存图关系、原生版本与载入源码绑定。

receipt 保留原存档SHA `ed90dbe3374e44881fd6bb6f075acde4363fc79ebbae50e82a4fdfdf392482ca` 与原 projection SHA，并明确 `raw_save_rehashed_this_run=false`。CI不会追随 JSON 内历史绝对路径、重读100MB原片或访问本机游戏文件。这是已观察且已严格验证的原生接口证明的可移植 SOURCE 投影，不能扩张成新同意流程或新领袖 factory 实机通过；新流程 `NOT_RUN`，零 error.log GREEN `NOT_CLAIMED`。

## 根集成步骤

1. 集成当前 `source/` 模板、生成器/数据/模型/test及 portable helper；SOURCE receipt放正式 `mod_li_yu_dao/tools/reference/`。保留严格 helper作为显式审计能力，不在正式check默认选择外置 binding。
2. 根既有 runtime 生成器可以调用 `build_outputs(native_evidence=<正式receipt路径>)` 并合入生成图；它仍由根负责实际写 tracked 输出。本候选 `generate` 默认拒绝写 checkout，`--check` 可只读比较正式树。不要把外置 audit/finalize/report helper 作为正式工具。
3. `resolve_checkout()` 从 `__file__.parents` 找当前 checkout；外置调用才显式传 `--checkout-root` 或 `LYD_C2_CHECKOUT_ROOT`。正式工具无固定账户或 `C:/workspace` 根。只有原生日志的历史 provenance 字段保留原路径，validator不跟随它们。
4. I2生成图共15文件，其中两份 C3 factory/migration hooks 与 I3 authored共享源不变；根只加载一份共享定义。更新正式构建 allowlist/静态门禁，并将新增默认关闭 gate 的生成调用显式绑定正式 receipt，避免 default closed 与 admitted 输出混用。
5. 原 tracked R2 proof 文件现有 `text=unset` 保持不变。新的 SOURCE receipt也应使用 `-text` 保全精确字节；不要为 CI 重写或归一化历史 proof。模板/生成文件按既有 BOM 合同处理。

根集成后，正式 checkout 中的只读命令可以是：

```text
python -B -X utf8 mod_li_yu_dao/tools/gen_school_consent.py --native-evidence mod_li_yu_dao/tools/reference/native-primitive-tracked-admission.json --output-root mod_li_yu_dao --check
python -B -X utf8 mod_li_yu_dao/tools/test_school_consent.py
```

这些命令需模板和 tools 按上述相对结构集成，且15份输出均已由根生成。source目录、receipt路径或 orchestrator如果采用别的位置，根应保持显式路径传递；不自动猜未知 receipt，不降级到历史外置 binding。正式 CI 不需要 CK3/Steam/桌面、原生 DLL或历史大存档。

外置候选的对应只读重现命令：

```text
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe -B -X utf8 C:/workspace/ck3_lyd_runtime_20261004/iteration2-nonce-candidate-002/tools/gen_school_consent.py --checkout-root C:/workspace/ck3_eternal_recurrence --native-evidence C:/workspace/ck3_lyd_runtime_20261004/iteration2-nonce-candidate-002/tools/reference/native-primitive-tracked-admission.json --output-root C:/workspace/ck3_lyd_runtime_20261004/iteration2-nonce-candidate-002/generated/mod_li_yu_dao --check
```

当次新离线报告为 `evidence/offline-20261004T081242776689Z/offline-report.json`；包含来源/接收无地玩家拒绝与不响应、分立无地玩家、发起者限制与NPC资格、真实生成集合检查，以及 relocated checkout 只复制10份小proof即可验证、缺文件/换哈希/绝对路径或越界路径拒绝。旧85 attempt 与更早83项 clean门禁失败均保留。原生教义 iterator、same-core trigger、跨 Faith divergence、多人事件及新头衔生命周期仍需冷载验证；没有把原生接口 credit 当作完整玩法验收。
