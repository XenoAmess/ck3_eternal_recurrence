# GEN-034 下一次有界 live 输入冻结

冻结日期：2026-09-12（Asia/Shanghai）。本页只冻结下一次 G2 live 的可复用输入与动作预算，不启动 CK3。T0 占用 CK3 时，
G2 必须继续让位；实际启动前由主线程分配“新轮次 R{new}”，并重新执行最终 source/runtime no-launch admission。

## 输入

| 项目 | 冻结值 |
|---|---|
| exact build | CK3 `1.19.0.6`，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| checkpoint | `Z:\ck3_mod_rewrite\_runtime\g2-r459-normal-lifecycle-20260911\live-state\profile\save games\xar_checkpoint.ck3` |
| checkpoint identity | `68,603,154` bytes，SHA-256 `FAA32578602EF546D991C364D196292C70C2D491FBCC6D4558FAB31444E14E78` |
| driver state | R459 native-session `driver-state.json`，SHA-256 `A5DB3F1E5FEDCD019B60FDAB0380E072D9D8465E330DD6D080AA3D0208994B5E` |
| paused identity | CharacterID `29829`，opponent `28551`，WarID `33554473`，date_raw `53183856` |
| strategic-power evidence | R471 reclassification `D8F43EABC2A38F451FCAB1FE8DAEEB157EF8C62439B904DF96E8AFA301E924C9` |
| strategy profile | `ck3_autonomous_player/strategies/raiktor_exit_budget_v1.json`，profile `raiktor-exit-balanced-v1 / 1.0.0`，SHA-256 `4206D725EC702701725221EB274E1F248E607F3127B720D033779FD71154FD11` |
| profile provider receipt | `Z:\ck3_mod_rewrite\_runtime\g2-gen034-strategy-profile-20260912\repository-default-profile.json`，SHA-256 `BB20D87233DF6C854DD668FD1641AE590DFFA3BD87CF82099A1A97EBF20C7981` |

R459 已证明 source-specific `3000→0`、persisted truce expiry `53227656`、唯一 surrender 与 postwar cleanup。R471 已证明同一
paused frame 上两次 strategic-power payload 一致：玩家 `13075500000`，对手 `16770900000`，ratio `128262/100000`。下一轮不得
重跑 source capture、loss、truce reader、旧 index `9/10` shape 或 active-war strategic-power 专项。

## 唯一 live 目标与预算

第一目标是在上述 paused identity 上取得 **same-frame white-peace terms + utility comparison**。所有读必须绑定同一 PID、connection、
episode、snapshot/native revision、date、WarID 和 candidate/profile SHA。允许两次相同只读查询用于稳定性检查；不得推进时间，
不得在 comparison 未齐时提交任何 action。

若 campaign dominance、strategy profile 和 white-peace comparison 在同一受管会话内全部 ready，则允许继续完成 GEN-034-D：

1. 运行一次三路 recommendation；
2. 只提交 recommendation 选定的一个 semantic action；
3. 下一 paused frame 独立查询 WarID、source loss、truce、资源与结果；
4. 保存 checkpoint，执行 cold restore 和 identity/postwar rebind；
5. 规范清理当前轮次。

任何缺字段、frame mismatch、underdetermined recommendation、submit ambiguity 或 postcondition mismatch 都保持 RED，停止本次动作，
归档已有输入后再做最小修复。单个合同修复只回归对应 provider/consumer 和这一有界场景，不扩大为整局长跑。

## 启动前必须重新确认

- 没有其它 CK3 实例，T0 没有占用交互桌面或验收环境；
- final root commit、runtime manifest、DLL/injector 和两个输入文件的 path/size/SHA 全部匹配；
- profile 使用仓库默认，或显式 operator override 的 base profile ID/version 精确匹配；
- 启动记录写明旧轮次处置、新轮次、原因、前后版本、参数、RED 与 DLL/游戏文件变化。
