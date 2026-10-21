# 活武器 / Living Artifacts

让 CK3 的个人装备有概率苏醒，成为自行成长、产生随机异能与诅咒，并随家族传承的活武器。范围包括武器、甲胄、冠冕、礼器、胸针、个人饰品与日志。

**当前状态：0.1.0 开发中，已有游戏脚本、生成器与构建门禁，尚未完成实机验收或发布，暂无 Workshop item ID。** 目录沿用 `mod_<english_name>/` 惯例。首次实现目标为12个异能、8种重诅咒及4组代表联动；图鉴其余内容不进入当前随机池。

## 文档

- [Elona 活武器设定研究](docs/elona-living-weapons-research.md)：检索来源、原版与衍生版差别，以及可借鉴的核心玩法。
- [CK3 详细设计](docs/design.md)：AI/NPC完整参与、自动升级、卸下停级、付费限时镇压、四档无CD喂养、共鸣与传承。
- [异能图鉴](docs/affix-catalog.md)：36个机制异能与10组联动。
- [诅咒图鉴](docs/curse-catalog.md)：8类共32种诅咒，每种三阶，包含重度生存、财务、统治、人际与失控后果。
- [实现与验收方案](docs/implementation-plan.md)：脚本落点、持久化字段合同、兼容性、待验证接口与开发顺序。
- [测试验收总方案](docs/test-plan.md)：分层流程、夹具、核心机制/AI/冷载用例、运行安排和通过标准。
- [内容验收矩阵](docs/content-acceptance-matrix.md)：12异能、8重诅咒、4代表联动逐条前置、真实触发、数字后验与负例，全部NOT_RUN。
- [验收执行与结果合同](docs/acceptance-execution-contract.md)：连续核心 v1 已实际运行并保留失败；当前 v2 使用当次角色身份与保存状态后验，待重新实测。
- [R2 运行记录](docs/runtime-r2-issues.md)：真实装备、两天推进、第三天读回失败、修复及资源清理；附[真实库存截图](docs/evidence/r2-inventory.png)。
- [实现调整](docs/implementation-adjustments.md)：90日镇压、每件饥渴叠加和真实原版触发的最终期望。
- [图片来源](docs/media-provenance.md)：原创宣传封面；实机截图与公开上传单独记录。
- 工作记录：[v0.1](docs/evidence/design-session-2026-10-22.json)、[v0.2](docs/evidence/design-revision-2026-10-22.json)、[v0.3诅咒修订](docs/evidence/curse-revision-2026-10-22.json)。旧回执只对应各自当时的内容。

每件合格装备默认 **5%** 觉醒且只判定一次。玩家与AI使用相同规则；实际装备时持续成长，经验足够便**自动升级并随机演化**，11级起出现基础饥渴，没有15级硬上限。卸下免费停级且失去加成；仍装备时只能付费暂缓成长。喂养按原版普通/大师级/名作级/卓越级四档给经验，**无冷却**。

异能采用最多六个显性槽与两个诅咒槽，包含特殊触发、风险交易、突变与装备联动；不再按六条属性路线加点。数值均为本项目设计，不代表Elona各版本通则。

诅咒一阶就应显著影响取舍，三阶可威胁角色生存或统治；减益不受每件基础饥渴5点上限保护。诅咒替换保留原槽阶数，不能把三阶负担免费洗回一阶。卸下仍然免费停止成长并移除持续加成/减益，已经发生的损失与承诺照常保留。

独立运行是预期目标，不要求主模组、MCP或外部后台。AI/NPC完整参与依据用户2026-10-22的本产品明确授权；不外推到其他模组。

开发工具使用Python；实际玩家模组只包含原生CK3脚本与图片。`tools/generate.py --game <CK3安装目录/game>`生成，`tools/validate_static.py --game <同目录>`检查；`python -m unittest discover -s mod_living_artifacts/tools -p test_*.py`执行工具目录的离线回归。正式包只用`tools/build_release.py --game <同目录> --output <全新外置目录>`；启用内容未完成或发布本地化不齐时拒绝构建，不把离线通过称为游戏验收。
