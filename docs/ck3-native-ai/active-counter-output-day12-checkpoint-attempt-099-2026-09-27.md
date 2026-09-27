# 099：第 12 日冻结存档，用于独立复核下一次反制输出

这是 CK3 **1.19.0.6** 原版战斗的续接取样准备，不是新的反制输出证明。099 从 098 使用的同一份第 11 日冻结存档独立加载，只推进一天，把第 12 日暂停帧保存为下一次实验的输入。Steam 离线视觉回执在启动前取得，未切换模式；结束时进程树清场通过。

| 项目 | 冻结值 |
| --- | --- |
| EXE SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| bridge DLL SHA-256 | `ABEE0A5AD16347A9EA2F10454D111A769CEDB84E343010792619CBB27A4CD858` |
| 输入存档 SHA-256 | `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953` |
| 原生 CombatID | `16777218`，玩家侧 `side 1`、Army `18` |
| 日期 / 主战阶段日 | `53146488 → 53146512`；`7 → 8` |
| 新冻结存档 SHA-256 | `E6155C9C127EC3D1D758468653E8ABC3458A96B50EA053E303FDCCAD18C0B731`，`52,389,793` 字节 |

独立 attempt 在 `D:\workspace\ck3_native_war_ai_promo_work\episode01-day12-checkpoint-attempt-099`。`c099-before-snapshot.json`、`c099-before-control.json`、`c099-life-advance.json`、`c099-after-snapshot.json`、`c099-after-control.json`、`c099-save-day12.json` 的 SHA-256 依次是 `815B3B553E101D0BB204A027E5800BF2FF7A030E2FBC1991E97E20027A81ABC4`、`FD2D25BD1773D01EB34736051900F47D3D5F46004DAFF3467A87162296288B5C`、`FACA04FEE2949FC30B74CC0225152D8FD067705E2E167DE182B59FE25402F74B`、`6C9AD9B7964A0A7BBBEF6645E33EE0E362F5627423378F12B572F2A23C04C13B`、`FFE286DC1422A54A330A53F29BD4541512F9E75A4C0DE112584CFC934F2022B6`、`A68C4D38CC14B11FCB4078E8D9074C9EE5793B0EF20674199327E6D0A983B415`。保存回执声明 `status=saved`、`date_raw=53146512`，其路径为该 attempt 的 `ck3-state/profile/save games/xar_checkpoint.ck3`；随后对文件字节重算 SHA 与回执一致。

`cleanup-check.json` 报告 capture exit `0`、`cleanup_ok=true`、final job active processes `0`、最终 CK3 PID 清单为空；其绑定的 `session-result.json` 和 `capture-report.json` SHA-256 分别为 `3FD84B7899F0CFF2FC76FE129ACA3ECCD383E1815CC6FA1DA9D1859C5876D870`、`F0441E491FBC6C2E18B4BB291CB2B41EC0BB596B0CCBBFC4BAA056FBCDE5A390`。本次没有打开 runtime counter hook。后续独立 attempt 必须以此存档和 `c099-save-day12.json` 精确配对，才能把下一天观察与 098 的增援日样本分开比较；这份存档本身不提高整场胜率模型的完成状态。
