# H604 派生建设：下一次定时读回入口

状态：**配对来源已只读核对；候选尚未准备，未做本次 no-launch 或实机运行**。本页只为 R0372 后的 h90 派生施工提供下一次有界验收入口；不计入正式 Robert 持久日期。原生建设决策与现有材料收据合同见 [domain-construction-ai.md](domain-construction-ai.md)。

## 原始四文件配对

R0372 [正式报告](<Z:/ck3_mod_rewrite_process_assets/nw-econ-r0370-coldwatch-715279f-20260929/run-coldwatch-32/formal-report.txt>) SHA-256 `6B1CBAB1CD7108CB72794ED7F828A7C635F1521CA44D7139B81FFA2096AC51D4` 已验收 32/32 turn、h536/raw53156640 → h604/raw53156784，末存档是派生来源。未在本次接手中启动 CK3。

四个来源文件均在 `Z:\ck3_mod_rewrite_process_assets\nw-econ-r0370-coldwatch-715279f-20260929\state`；下一候选须复制到新目录，经官方 `tools/g2_preview_operator.py prepare-state` 的普通 `xar_off` rebind 与 no-launch 检查，不能改写原目录：

| 用途 | 相对路径 | SHA-256 |
| --- | --- | --- |
| 存档 | `profile/save games/xar_checkpoint.ck3` | `5E43DEA244C3869E09EC4C8B15FF7646680C4A2670267C1040B0E6ED8144CAF8` |
| Driver | `native-session/driver-state.json` | `B38745C4EBBBDAF4ABD89539CCD234CAB3E8CEBA16D14E55A333B41D61BC261A` |
| 建设账本 | `construction-formal-pending-v1.json` | `04781D873564E5B809BB476B4A41A5A27A2AA22A4A3ADE96B898B50C9606B3B7` |
| 家庭账本 | `first-heir-marriage-formal-v1.json` | `880205B7A2FE30E20B69243F1E249A8607A3BF312F702726D8C856E90DDF8659` |

Driver 的 `last_checkpoint` 指向该存档 SHA、`date_raw=53156784`、`history_index=604`、角色 29829、episode `native-29829-2bc2d599f7f9`；命令历史有 609 行，尾部须由官方恢复器处理，不能物理截断。建设账本 `pending=null`，原动作已核 `applied/in_progress`，目标是 `hill_farms_01`、barony 2174 / province 2629 / slot 1 / building type 628。最近读回 raw53156688：剩余工作 raw95,944,458、省月收入 raw87,000、`completion_last_check_date_raw=53156688`；`completion_observed_date_raw` 与实际省收入增量仍为 null。

## 下一有界观察与实际边界

既定 30 游戏日检查间隔是 `720 date_raw`；下一到期门为 **raw53157408**，比 h604 存档晚 `624 date_raw = 26 游戏日`。R0370 的 112 turn 推进 28 派生日，R0372 的 32 turn 推进 6 派生日；因此约 128–160 turn 的单次有界运行有机会到达该门，具体推进受战争与事件阻塞影响，不能保证。候选应固定 turn/wall 边界，并在到期后读取同一槽的 active/已建状态、剩余工作及省月收入；如果仍施工，保存新的合法配对供后续定时复查。不能为了到期手改日期、存档或建设账本。

R0372 在两游戏日内观察到剩余工作 raw96,166,680→95,944,458。若速度不变，完成还需约 864 游戏日；这是**粗略推算，不是原生完工日期**。本次单场的目标只是下一次到期读回。只有同槽从 active 转为已建、独立读到完成及实际收入/建筑效果，才分别记录完工与收益；原已建收据、脚本预计月收益或总收入差值本身均不能冒充独占建筑收益。不得重复建设扣款或提交。

本机 2026-09-29 晚间（Asia/Shanghai）接手核查时有 CK3 PID 187764，任务总线登记由 NW-TAKEOVER-LIFE 占用。官方普通 rebind 与 `native-one-generation-preflight` 均明确要求 **零 CK3 进程**。因此本包没有运行 `prepare-state`，没有冻结新候选，也没有触碰当前窗口。待唯一实例负责人释放后，先核新 master/源码、四文件与进程状态，再完成独立候选的配对/no-launch；这一步不能沿用 R0372 旧候选资格。
