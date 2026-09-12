# 自动升级建筑（XenoAmess维护版）

本目录是 Steam Workshop 条目“自动升级建筑”（上游 item `3596580780`，原作者白绮）的仓库内维护源码。
当前基线来自 2026-09-11 下载的上游 7 文件版本；原始字节与逐文件哈希记录在
[`../docs/auto-upgrade-buildings-upstream.md`](../docs/auto-upgrade-buildings-upstream.md)。仓库内
`descriptor.mod` 只移除了只能存在于用户目录外层 `.mod` 的 `remote_file_id`，其余运行时文件在首个导入基线中保持上游字节。

## 玩家合同

- 入口：玩家决议“启用自动建造”与“禁用自动建造”。
- 启用后：由唯一全局循环每 15 个游戏日检查玩家直接持有的地产；每条已有下一等级、符合原版资格条件的建筑链每轮最多即时升级一级。
- 覆盖：CK3 1.19.0.6 的 605 条普通建筑流程升级边，包括城堡、城市、神殿、部落和曼荼罗神殿城塞地产中的主建筑、普通建筑、公国建筑与特殊建筑。
- 费用：使用对应建筑的原版基础费用和金币／威望／虔诚／scripted cost 资源形状；启用时可选择“只用国库”“只用个人金钱”或“优先国库”，同一笔金币费用不拆分，资源不足时不升级、不扣款。
- 排除：所有住所系统、游牧／牧民地产、曼荼罗都城的 4 条 Great Project 升级边、正在施工或出租的地产、空槽与没有下一等级的终级建筑。
- 资格：生成器逐条投影当前 CK3 1.19.0.6 的建筑资格门槛，不兑现原版定义之外的提前升级。
- 玩家/AI：只允许真人玩家启用，AI 永不触发。
- 旧存档：保留上游 `auto_build` 事件命名空间和 `enable_auto_build` 角色 flag；已有启用状态且没有三期资金 flag 的旧存档继续按“优先国库”运行。

## 维护目标

目标运行时为本机冻结的 CK3 `1.19.0.6 (Scribe)`、Steam build `23530548`。兼容性修复、静态门与隔离核心实机矩阵均已完成；
维护基线证据见 `../docs/auto-upgrade-buildings-maintenance.md`，三期资金策略与 R0025 证据见 `../docs/auto-upgrade-buildings-phase-3-plan.md`。正式版提供简体中文、英文、法文、德文、日文、韩文、波兰文、俄文和西班牙文；Workshop 文案维护在
`../workshop/auto_upgrade_buildings_description.bbcode`。

本维护版保留上游署名和来源，并已获得原 Mod 作者授权进行二次开发与发布。

## 生成与校验

`common/scripted_effects/build_scripted_effect.txt` 与 `common/scripted_triggers/aub_building_triggers.txt` 是生成文件。建筑图谱来自
`../tools/auto_upgrade_buildings_1_19_0_6.json`；刷新 exact 原版定义时先运行提取器，再运行生成器：

```powershell
py tools/extract_auto_upgrade_buildings.py --check
py tools/gen_auto_upgrade_buildings.py
py tools/validate_auto_upgrade_buildings_static.py
py tools/test_build_auto_upgrade_buildings_release.py
py tools/build_auto_upgrade_buildings_release.py --check
```
