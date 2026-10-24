# 二期 0.4.0：CK3 1.20.0.4 兼容更新

本次按用户 2026-10-25 指令发布仓库二期实现；验收范围为游戏启动、人物入场、自然运行一年及项目错误检查。原版 0.3.0 和二期历史专题保留各自当时的覆盖边界，本次不追加完整 361 项业务回归、宣传视频或多语言实机。

## 原版源码核对

`machine_id: pc-20260924rtuf-f11af23c08`；2026-10-24 UTC 读取 Steam 本机 build 25734779，实际 `ck3.exe` SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。游戏根为 `C:/SteamLibrary/steamapps/common/Crusader Kings III`；该安装位置不作为其他机器前提。构建、隔离 profile、日志与存档输出均在 D 盘。

核对范围：`game/common/governments/00_government_types.txt` 中 `celestial_government`、`government_is_celestial`、贤能资格和 `character_max_merit_level_add`；`common/on_action/_on_actions.info`、`yearly_on_actions.txt` 的年度 playable/everyone pulse；`common/modifiers/10_tgp_modifiers.txt` 的贤能及 `monthly_treasury_from_salary_budget_mult`；原版活动类型与本产品京察的参与者 scope、host 限定、取消及 treasury 成本接口。现存接口继续用于二期生产路径，不另建平行实现。

描述文件原先已标记 1.20.0.4，但仍使用 0.3.1 版本号。此次将完整仓库二期投影正式标记为 0.4.0，并同步当前说明；不把旧版加载或历史场次当作本次实测。首次实际加载发现京察缺少 `header_background`，已按原版 `feast.txt:1182` 补入实际存在的宴会顶部背景。

## 简短实测合同

公共入口选择 `zhongguo-361 / migration-one-year`，沿用本机共同 runtime 与原生 MCP。1066 罗贝尔正常入场，启用年度严格 361；天朝 AI 仍走真实生产年度链。独立观察夹具仅在入场和 365 个自然日后记录日志，不改日期、角色、资源或产品状态，不进入发布包。验收同时读取原生日期、玩家身份和游戏错误日志。

静态校验、本地化发布格式审计和构建回归已通过；下面记录本次实际简短实测，Workshop 发布事实在永久 changelog 中另记。

首场 `pc-20260924rtuf-f11af23c08--zhongguo-style--R0001` 在人物入场前因共同 DLL 不提供 `query-frontend-game-rules-window-v1` 而失败。三项规则本来就是产品默认值，后继直接消费默认值，不增加 native 施工。首场同时保留大量二期未使用变量的加载分析诊断，不能称为零诊断。

执行者在首场运行时修改 lease anchor 工作树，导致 keeper 因 checkout dirty 退出；这是执行流程失误。游戏经实际主菜单 Exit to Desktop 退出，原生 session 证明 Game OS0、Job0、完整 tree/control/watchdog 清理。原 host 因旧队列要求已结束 keeper 仍持有新鲜租约而停在无游戏的 hold，已在共享队列补入显式 `--terminal-cleanup`：只接受单个 `failure_shutdown=true` 的 `finish_hold`，复用原 host 的实际 native-zero 谓词，核原 keeper 线程已结束及当前无 CK3，返回 `lease=null`，保留失败且不授业务/正常退出信用。未热改冻结 runtime；新队列消费原 frozen helper，原 host 自己执行尾部 finally 并写出 RED/cleanup true。42 项队列回归通过，完整 `ck3_mod_acceptance_queue.py` 的 mypy 检查通过；回归已在现有 static CI step 持续执行。

后继 `R0002` 使用独立、干净的本机 `c23` lease anchor、修正版 staging 和新 profile；主仓后续文档与发布准备不修改该冻结 anchor。

`R0002` 于 2026-10-24 18:35–19:40 UTC 实际运行。玩家 31254（1066 罗贝尔）正常入场，从原生 `date_raw=53144328` 推进到 `53154048`，即 405 个自然日；365 日只读观察事件已触发，末帧玩家仍存活、地图正常。游戏经原版 Exit to Desktop 正常退出，原 session 回执为 OS exit 0、Job0、tree/control/watchdog 清理成功。未发现该模组新的运行时脚本错误；日志仍含二期未使用变量分析、六条孤立事件诊断及原版事件错误，故不称零错误日志。

共同逐日 case 的原始结果保持 RED：执行者切换为原生连续加速后超出该 case 的 366 日上限，恢复逐日驱动时其旧 revision 请求被原生守卫拒绝（expected 74/current 326）；另有错误加入的旧年度 debug marker 未满足。这些是本次测试编排问题，不将共同 case 冒充 GREEN。用户要求的有界启动／入场／一年事实由独立的 365 日观察、真实原生日期与存活人物读回支撑；二期完整业务、多年、旧存档、中文界面语义和多语言实机均没有据此授予通过。

原始有界结果为外置 `one-year-smoke-result.json`；当场弹窗的源码及选项离线分析见[来源绑定知识记录](../../../docs/ck3-native-ai/zhongguo-migration-20261025-event-analysis.json)。发布包不含观察夹具。

过程证据：`D:/workspace/ck3-zhongguo-12004-20261025`，原始日志按通用策略保留 30 天，运行 profile/存档 14 天，当前必要恢复输入最长七天复核。未删除旧证据。
