# XQOL：CK3 1.20.0.2 兼容候选与静态证据

日期：2026-10-01。产品：`mod_xenoamess_quality_of_life`，Workshop item `3798133925`。

当前结论：代码兼容迁移和本产品 L0 已完成。新版天朝场景已有严格继任、转封、死亡、关闭开关、改信门槛实际 UI、赎金和七组合释放证据；实机发现的足额牵制款报价与 recipient 上下文问题已修复，并由独立 R0004 付款场景验证。行政场景及下述未覆盖范围仍待验，不能据此宣称整个产品或正式发布完成。源 descriptor 仍为 `version="1.1.0"`、`supported_version="1.19.0.6"`；旧 native ABI、真实 Workshop 缓存和发布历史未修改。

## 精确输入

- 新版：CK3 `1.20.0.2`，Steam build `25588574`；EXE SHA-256 `ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d`。
- 原版安装：`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`。
- 旧原版文本快照：`C:/workspace/ck3-upgrade-20261001/baseline/vanilla-text/game`，对应 `1.19.0.6`。
- 新旧完整差异审计：`C:/workspace/ck3-upgrade-20261001/audits/standalones.json`，本产品条目冻结改动前覆盖与依赖的差异。
- 新原版依赖字节合同：[18 文件 SHA-256 清单](../tools/xqol_vanilla_1_20_0_2.json)。本次冻结在审阅真实原版差异后建立；生成器与静态校验均拒绝原版文件漂移，不自动刷新合同。

## 兼容修复

| 问题 | 当前处理 |
|---|---|
| 三份旧 governor 整文件保留已删除的犯罪 trigger，并遗漏新版公共计分、候选等级及冷却 | 从冻结的新原版重建，只在五个 `appointment_score_final_factors` 后保留原有百万分扣分。新增 `gen_xqol_appointments.py`；剥离五块后与原版逐字节相同，保留 BOM 与 CRLF。 |
| `government_allows = administrative` 已被政府 mechanic 替代 | 使用原版 `government_has_mechanic = administrative`。校验行政、贤能、天朝三类均声明此 mechanic，不误用只覆盖行政制的政府 flag。 |
| 隐藏改信互动接受分遗漏新版修正 | 从当前原版投影天朝等级、基础 50、默认宗教修正和 Christian situation 修正。保留廷臣/统治者两类回复延迟，不选择 hook、影响力或金钱让步。 |
| 原版改信、unity、state faith 后果开始依赖 `puppet_or_actor` 与 rite/state_rite | 批处理开始与接受/拒绝后果入口显式将 `puppet_or_actor` 绑定玩家。仍调用原版改信、unity 和 state_rite 奖励，补齐当前原版共有的斗争虔诚及 Acts of the Apostles / Mendicant Preachers 后果。只迁移本产品所需依赖。 |
| 条件释放缺少新版接受度与宗教门禁 | 七个组合补天朝等级及 head_of_rite 扣分；四个改信组合补原版拒绝改信标记的扣分，改信有效性也拒绝该标记。招募共产财产奖励迁移为 `rite_has_tenet`。原版此接受分仍使用 faith hostility，因此保留 faith 条款。 |
| 金钱足额赎金门禁引用旧通用报价 | 普通金钱报价改为 `normal_ransom_cost_value`，劫掠报价仍为 `increased_ransom_cost_value`；实际付款、redirect 与释放继续由原版互动执行。当前原版的该互动优先提供可用金钱选项，未新增 herd 选择逻辑。 |
| 原 effect 文件超过项目规定的 20 个顶层定义 | 按用途拆为转封/免费防御 6、改信 9、付款/监狱 8 个定义，ID 不变；更新正式 allowlist、静态校验及构建测试，staging 由 24 变为 26 文件。 |

相关机制及流程合同已同步至 [mechanics](../mod_xenoamess_quality_of_life/docs/mechanics.md)、[原版依赖合同](../mod_xenoamess_quality_of_life/docs/phase-two-vanilla-contract.md) 与 [新版验收计划](../mod_xenoamess_quality_of_life/docs/acceptance-plan.md)。未修改其他产品源码、九语文案、受管桌面或任何游戏启动配置。

## L0 与离线预验

使用 `C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，Python `3.14.7`。正式本轮检查各执行一次：

```text
tools/.venv/Scripts/python.exe tools/gen_xqol_appointments.py --check
tools/.venv/Scripts/python.exe tools/gen_xqol_phase2.py --check
tools/.venv/Scripts/python.exe tools/validate_xenoamess_quality_of_life.py
tools/.venv/Scripts/python.exe tools/test_build_xenoamess_quality_of_life_release.py
tools/.venv/Scripts/python.exe tools/build_xenoamess_quality_of_life_release.py --check
tools/.venv/Scripts/python.exe tools/build_xenoamess_quality_of_life_release.py --output C:/workspace/ck3-upgrade-20261001/audits/xqol-l0-001/build
```

结果：两套生成投影 current、静态 GREEN、8 个构建测试通过，26 文件双构建可复现。七语发布翻译审计未请求。

构建 staging：`C:/workspace/ck3-upgrade-20261001/audits/xqol-l0-001/build`。

- manifest SHA-256：`ba05ae8576d50519d1e6c3d3f2de8fb866841d0cbc8aecef6d72936c11c7af9c`。
- ZIP SHA-256：`045664a1afd011f9b3aa8e228a4dfeb52d97091d192fa704a2b192c8e821b8ab`。
- 完整 argv、stdout/stderr 与精确身份保存在 `audits/xqol-l0-001/report.json`。

先对源码、再对同一 staging 执行 `open_kaishek corpus --require-corpus`。工具 checkout 为 `C:/workspace/open_kaishek`，commit `522ac2d93bd6c534a6a242a227057de40a8977c1`，CLI `0.1.0-cli`；JAR SHA-256 `6ac143ebf03f3e1a041dff01b2d808e60de8e289d18cebf9855682f0a80b6d82`。两次均解析 15 个 `.txt/.gui` 文件、137550 bytes、0 diagnostics，corpus SHA-256 `9f420d44117cc7d9b4c7e77e8b77f48125f7958550fbfd4933c96051c6ba7327`。

第一次 staging 解析误给 `build/mod` 路径，返回 `corpus-root-absent`；此失败回执保持原样。新 attempt `audits/xqol-l0-002/report.json` 改为实际 `build` 路径后通过；没有重写失败，也没有因此重跑已通过的代码或构建检查。最终外置汇总状态为 `GREEN_L0_ONLY`。

目前 `open_kaishek` 没有 CK3 1.20 semantic profile；本轮仅使用无版本语义的 parser，不用旧 1.19 profile 证明新版语义。互动引擎、GUI、异步 scope 生命周期、实际金钱/囚犯/改信/战争后果与 native ABI 均未由该离线结果证明。

## 待新版实机验证

### 2026-10-01 实机增量与边界

R0003（`4-8e1c2f1861--xenoamess-quality-of-life--R0003`）严格原版 baseline、最高合格非玩家候选、移除/死亡继任及关闭后原版候选/guard 清理均通过。后续原始 `payment_full_only` 失败保持原样；回调覆盖旧预期值后无法重建其具体失败条件，没有将其归为已证明的自然死亡、缓存或日收入问题。

该场继续实际操作了门槛 50% 的改信事件、足额/有钱即赎回按钮和条件释放决议；新日志中的 `conversion_threshold_50_filtered`、`ransom_full_only`、`ransom_any_one_gold`、`release_priority_matrix`、`release_conversion_rite_matched` 均通过。角色搜索实际输入并全文读回 `ZQA`，应用名称筛选后显示两个控制样本；高接受度角色完整面板主行显示“禅宗”，低接受度角色主行仍为“罗马礼”，并非仅凭图标判断 Rite。对应原图为 live R0003 根目录的 `20261001T112130480976Z-actual-high-portrait-001-after.png` 与 `20261001T112222485164Z-actual-low-portrait-001-after.png`。这些证据证明该实际路径及矩阵后果，不能代替尚未执行的 head_of_rite、拒绝改信标记或其他 slider 边界样本。

R0003 closeout：`C:/workspace/ck3-upgrade-20261001/audits/xqol-R0003-ui-closeout-02/report.json`，SHA-256 `62b160a22ab231350b6d1ca409323ce6acd6996227f4ddf9ddb1a3ea0b5fbd4d`。最终 error.log 50209 字节、136 条错误记录（其中 57 条明确处于 tooltip 构建）；不得称零错误。冻结投影中的 governor、改信和已通过的监狱 effect 块与当前修复后生产字节相同；仅足额牵制款块变化，故 R0004 只补受影响付款范围，没有机械重跑这些已通过块。

R0004 在同一真实引擎事务完成弱牵制足额/现有款/一金币边界和强牵制钱包 74/76 的原版报价边界。钱包 74 的 uncapped 价为 75、原版 capped 价为 74，足额筛选拒绝并保留可用牵制；钱包 76 重新报价 75，原版实付 75。八个金额、计数、钱包与牵制条件全部通过。细节、原失败保全、27 文件修复投影及精确 error 归因见 [付款上下文实机证据](xqol-native-payment-context-2026-10-01.md)。该场最终 error.log 111712 字节、385 条记录，303 条为付款完成后的夹具错误调用改信 dispatcher 所产生的真实 runtime error；没有将其说成 tooltip 或改信通过。

两场均使用 fresh Steam 离线画面、一次性 userdir、冻结 d19 新版候选与官方 1.20 harness，并在正常结束后证明进程树清理及实际 CK3 零进程。开局人物为 1066 罗贝尔·德·欧特维尔／阿普利亚；旧 operator 中“Robert of Normandy”的称呼是历史错误。d19 event normalization 默认补出的 `enabled=true` 不是原生选项门禁实证；实际选择另依可见按钮/业务文字、fresh instance/revision 和真实后果确认。

下列原完整验收清单继续作为范围要求。其中天朝上述已执行部分已有有界证据，行政主场景、复杂免费防御关系/战争后果、其余 slider 边界及独立宗教负门禁仍未执行。旧 runner 的游戏版本、EXE 与旧 Kaishek/native 准入锁保持冻结；新版实机入口是 checked 1.20 准备器与精确冻结的官方 harness，不能仅换旧 runner 常量声称迁移完成。

1. 三类政府的五种继任候选、开关与转封 guard 所有权清理。
2. 免费防御关系矩阵、同人多关系去重及资源不扣减。
3. 改信 slider 七个边界、直接玩家 scope、rite/state_rite 场景、拒绝与接受后果、最后一次汇总。
4. 牵制足额/现有款与赎金自付/领主共享余额、普通/劫掠金钱报价。
5. 七种条件释放、不可改信标记、head_of_rite、招募奖励与原版后果对照。

以上应在当次新鲜 Steam 离线证据、独立一次性 userdir 和已准入新版工具基础上串行执行。历史 1.19.0.6 GREEN、静态检查、parser 或构建成功均不能替代这些结果。
