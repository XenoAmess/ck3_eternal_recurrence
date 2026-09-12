# 自动升级建筑（XenoAmess维护版）

本目录是 Steam Workshop 条目“自动升级建筑”（上游 item `3596580780`，原作者白绮）的仓库内维护源码。
当前基线来自 2026-09-11 下载的上游 7 文件版本；原始字节与逐文件哈希记录在
[`../docs/auto-upgrade-buildings-upstream.md`](../docs/auto-upgrade-buildings-upstream.md)。仓库内
`descriptor.mod` 只移除了只能存在于用户目录外层 `.mod` 的 `remote_file_id`，其余运行时文件在首个导入基线中保持上游字节。

## 玩家合同

- 入口：玩家决议“启用自动建造”与“禁用自动建造”。
- 启用后：由唯一全局循环每 15 个游戏日检查玩家直接持有的地产；每条已有、符合条件的普通建筑链每轮最多即时升级一级。
- 费用：使用 CK3 1.19.0.6 对应建筑等级的原版基础费用；优先使用国库，国库不足时使用个人金钱，两者都不足时不升级、不扣款。
- 排除：主建筑、公国建筑、特殊建筑、部落、游牧、曼荼罗及其他非普通建筑体系。
- 革新：只按当前时代革新与地产等级判断，不兑现文化传统提供的提前升级。
- 玩家/AI：只允许真人玩家启用，AI 永不触发。
- 旧存档：保留上游 `auto_build` 事件命名空间和 `enable_auto_build` 角色 flag；兼容性修复不得无迁移地改名。

## 维护目标

目标运行时为本机冻结的 CK3 `1.19.0.6 (Scribe)`、Steam build `23530548`。兼容性修复、静态门与隔离核心实机矩阵均已完成；
实机证据见 `../docs/auto-upgrade-buildings-maintenance.md`。正式版提供简体中文、英文、法文、德文、日文、韩文、波兰文、俄文和西班牙文；Workshop 文案维护在
`../workshop/auto_upgrade_buildings_description.bbcode`。

本维护版保留上游署名和来源，并已获得原 Mod 作者授权进行二次开发与发布。

## 生成与校验

`common/scripted_effects/build_scripted_effect.txt` 是生成文件。建筑链、费用档、标准革新路线和地产等级门槛只改
`../tools/auto_upgrade_buildings_data.py`，然后运行：

```powershell
py tools/gen_auto_upgrade_buildings.py
py tools/validate_auto_upgrade_buildings_static.py
py tools/test_build_auto_upgrade_buildings_release.py
py tools/build_auto_upgrade_buildings_release.py --check
```
