# XQOL：CK3 1.20.0.2 兼容候选与静态证据

日期：2026-10-01。产品：`mod_xenoamess_quality_of_life`，Workshop item `3798133925`。

当前结论：代码兼容迁移和本产品 L0 已完成；新版实机验收尚未执行，不能据此宣称新版兼容或正式发布。源 descriptor 仍为 `version="1.1.0"`、`supported_version="1.19.0.6"`；旧 native ABI、真实 Workshop 缓存和发布历史未修改。

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

1. 三类政府的五种继任候选、开关与转封 guard 所有权清理。
2. 免费防御关系矩阵、同人多关系去重及资源不扣减。
3. 改信 slider 七个边界、直接玩家 scope、rite/state_rite 场景、拒绝与接受后果、最后一次汇总。
4. 牵制足额/现有款与赎金自付/领主共享余额、普通/劫掠金钱报价。
5. 七种条件释放、不可改信标记、head_of_rite、招募奖励与原版后果对照。

以上应在当次新鲜 Steam 离线证据、独立一次性 userdir 和已准入新版工具基础上串行执行。历史 1.19.0.6 GREEN、静态检查、parser 或构建成功均不能替代这些结果。
