# 天朝制允许经商&贪腐框架（XenoAmess维护版）

面向 CK3 1.19.0.6 的独立维护版，基于 Steam Workshop 物品 `3596263413`
（`Corruption & Trading under the Celestial government`）的玩法与素材继续开发。

核心内容：

- 为原版 `celestial_government` 增加 `barter = yes`，使天朝制角色进入原版易货与商旅系统；
- 为天朝属官提供四档贪腐策略，分别少缴 5%、10%、15%、25% 的天朝税赋；
- 贪腐特质提供易货产出，并同步施加功绩、民望、压力与治理代价；
- AI 按性格权重选择策略，角色也可暂时收手或永久退出该框架。

维护版不会覆盖原版 `feast.txt` 或 `window_county_view.gui`。CK3 1.19 已原生支持宴会的
易货货物成本；旧 GUI 整文件覆盖会回退 1.19 的快捷键与特殊建筑界面。

上游出处、精确提交、兼容性差分和授权确认记录见
[`docs/compatibility-audit.md`](docs/compatibility-audit.md)。

## 验收与发布状态

- `1.0.0` 已发布到维护版 Workshop 物品 [`3804807463`](https://steamcommunity.com/sharedfiles/filedetails/?id=3804807463)；上游物品 `3596263413` 未被修改。
- CK3 `1.19.0.6` 简体中文隔离实机验收及全新订阅缓存复验均 GREEN：正式决议与事件完成 UI 往返，天朝易货规则、第四档特质和 `0.75 - 0.25 = 0.50` 税率计算均由引擎确认。实机验收只使用简体中文。
- 正式 staging 由 `py tools/build_celestial_commerce_corruption_release.py` 生成，共 22 个运行文件；不要直接上传源码目录。
- 简中、英语及法、德、日、韩、波、俄、西九语已纳入正式 staging；英语及其他非简中语言只走键集、保护 token、数字、术语、文字系统与格式静态审计，不启动 CK3 实机，也不冒充母语玩家的游戏内截断签核。
- 工坊标题、主描述（含 `1.0.0` 更新日志段）和完整 Steam Change Notes 已匿名精确回读；正式发布记录见 [`docs/release-changelogs/celestial-commerce-corruption/1.0.0.md`](../docs/release-changelogs/celestial-commerce-corruption/1.0.0.md)。
- 上游下载未附许可证；仓库所有者已于 2026-09-20 明确确认取得原作者对维护版再分发与发布的许可，并指示据此执行。授权原件仍待所有者方便时补档。
