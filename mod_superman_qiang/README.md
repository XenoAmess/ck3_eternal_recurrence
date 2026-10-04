# 超人强：越超人越强

1.0.0 已发布：[Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3812991990) · [GitHub 下载](https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/superman-qiang-v1.0.0)。

独立 CK3 模组。每次游戏明确结算两位成年角色之间的性行为时，经验较多的一方可以从经验较少的一方吸取随机属性。

性经验记录在角色变量中，双方每次各增加 1；结算前经验相同则不吸取。经验不受特质经验条的 100 点限制。通过角色交互和特质说明查看角色自己的累计经验。

吸取以六项“净转移点数”账本记录：同一技能接收者 +1、来源者 -1，再投影为永久属性修正，原生基础属性保持原样。每项账本范围为 -1,000,000 至 +1,000,000。来源者当前有效技能为 0 或本次转移会越过账本边界时，跳过该技能；接收者有效技能为 0 仍可接收。剩余候选等权抽取，没有候选仍累计经验。原版百分比修正和取整继续生效，因此面板变化可能为 0 或 2，不保证有效技能每次正好变化 1。

只统计启用模组之后的明确事件，不推算日常夫妻生活或既往经历。适用角色必须年满 18 岁，玩家和 AI 使用相同规则。明确的匿名对象事件仅给已知角色增加经验，不创造属性来源。

首发实机验证版本为 CK3 1.20.0.3，独立加载，不需要其他模组。覆盖两个原版结算效果，因此与同样覆盖这些效果的模组可能冲突。

开发和验收入口：

- [产品规则](docs/product-contract.md)
- [测试与验收方案](docs/test-plan.md)
- [首发实机验收汇总](docs/acceptance-1.0.0-20261004.md)
- [正式发布与完整回读证据](docs/release-1.0.0-20261004/README.md)
- [永久首发 changelog](../docs/release-changelogs/superman-qiang/1.0.0.md)
- [技能边界及原版缩放依据](docs/skill-boundaries-reference.md)
- [发布方案与完成门槛](docs/release-plan.md)
- [前期可行性研究](../docs/sex-experience-attribute-drain-feasibility-1.20.0.3.md)

正式包由 `tools/build_release.py` 的明确文件清单构建，22 个运行文件与实机候选逐字节一致。中文机制、正常查看、百万经验与安全极值、真实保存重载、原版旧存档启用及双向属性边界验证通过；真实订阅下载、公开媒体和完整 Steam Change Notes 均已核验。Steam 已恢复离线。旧试扣方案 R0006 RED、R0007 失败断言及历史候选按原事实保留。
