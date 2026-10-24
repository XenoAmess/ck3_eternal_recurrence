# 二期 0.4.0：CK3 1.20.0.4 兼容更新

本次按用户 2026-10-25 指令发布仓库二期实现；验收范围为游戏启动、人物入场、自然运行一年及项目错误检查。原版 0.3.0 和二期历史专题保留各自当时的覆盖边界，本次不追加完整 361 项业务回归、宣传视频或多语言实机。

## 原版源码核对

`machine_id: pc-20260924rtuf-f11af23c08`；2026-10-24 UTC 读取 Steam 本机 build 25734779，实际 `ck3.exe` SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。游戏根为 `C:/SteamLibrary/steamapps/common/Crusader Kings III`；该安装位置不作为其他机器前提。构建、隔离 profile、日志与存档输出均在 D 盘。

核对范围：`game/common/governments/00_government_types.txt` 中 `celestial_government`、`government_is_celestial`、贤能资格和 `character_max_merit_level_add`；`common/on_action/_on_actions.info`、`yearly_on_actions.txt` 的年度 playable/everyone pulse；`common/modifiers/10_tgp_modifiers.txt` 的贤能及 `monthly_treasury_from_salary_budget_mult`；原版活动类型与本产品京察的参与者 scope、host 限定、取消及 treasury 成本接口。现存接口继续用于二期生产路径，不另建平行实现。

描述文件原先已标记 1.20.0.4，但仍使用 0.3.1 版本号。此次将完整仓库二期投影正式标记为 0.4.0，并同步当前说明；不把旧版加载或历史场次当作本次实测。

## 简短实测合同

公共入口选择 `zhongguo-361 / migration-one-year`，沿用本机共同 runtime 与原生 MCP。1066 罗贝尔正常入场，启用年度严格 361；天朝 AI 仍走真实生产年度链。独立观察夹具仅在入场和 365 个自然日后记录日志，不改日期、角色、资源或产品状态，不进入发布包。验收同时读取原生日期、玩家身份和游戏错误日志。

当前：静态校验通过；实机与 Workshop 更新待本次实际执行后追加。

过程证据：`D:/workspace/ck3-zhongguo-12004-20261025`，原始日志按通用策略保留 30 天，运行 profile/存档 14 天，当前必要恢复输入最长七天复核。未删除旧证据。
