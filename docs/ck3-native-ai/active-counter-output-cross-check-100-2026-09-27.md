# 100：相邻日原生反制输出与模型对拍

本次用 [099 冻结的第 12 日暂停存档](active-counter-output-day12-checkpoint-attempt-099-2026-09-27.md) 独立启动 CK3 **1.19.0.6**，观察同一 CombatID `16777218` 从日期 `53146512`、主战阶段日 `8` 到 `53146536`、阶段日 `9` 的一次日界。EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，DLL SHA-256 为 `ABEE0A5AD16347A9EA2F10454D111A769CEDB84E343010792619CBB27A4CD858`。输入存档 SHA-256 为 `E6155C9C127EC3D1D758468653E8ABC3458A96B50EA053E303FDCCAD18C0B731`，其配对保存回执 SHA-256 为 `A68C4D38CC14B11FCB4078E8D9074C9EE5793B0EF20674199327E6D0A983B415`。

| 侧 | 主参与者 owner | 原生反制兵团数：本侧 / 对方 | context（Q100000） | 原生非满额类别 | 暂停帧兵团重算 |
| --- | ---: | ---: | ---: | --- | --- |
| side 0，对方 | `31549` | `24 / 14` | `125000` | class `8` = `10000`；其余 12 类 `100000` | **13/13 相同** |
| side 1，玩家 | `29829` | `14 / 24` | `100000` | class `0、1` = `10000`；其余 11 类 `100000` | **13/13 相同** |

这次原生 hook `hook_calls=12`、`target_calls=2`、`first_failure_gate=0`、`pair_complete=true`，七个原生日界边界均齐，trace `failure_flags=0`。第 12 日暂停帧与第 13 日后读帧的两侧 regiment ID 及 class/stack/targets 元数据各自保持相同，原生 hook 所见 `24/14` 条目数和暂停帧一致。[只读投影器](../../tools/project_active_counter_output_100.py) 先核对源存档、保存回执、DLL 实际字节和三份原始响应的 SHA，再用 `combat_input` 同一定点反制公式、暂停帧当前兵力与本次原生 context 计算。其[逐兵团机器夹具](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_counter_output_100_projection.json)保留 owner、兵团 ID、class、stack、target 和前后当前兵力。`--check` 对原始响应与入库夹具逐字节复核通过。

本次 `post_counter_attack` 两侧原始值为 `7086468150 / 1367059376`，`outgoing_damage` 为 `116572401 / 63568260`（均 Q100000）；这说明 098 和 100 的**反制向量相同，不代表两日的攻击与实际出伤相同**。098 是增援日，100 是其下一日；两次向量都处在若干类别达到 `10000` 下限的状态。这是两个相邻日的同一战斗，不是独立战局分布，也无法单凭相同向量唯一反推出引擎每项当前兵力的读取瞬间。100 没有请求 runtime join 全条目，因此不能从该回执宣称当天绝无瞬时增援/撤离。

原始 attempt 在 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-100`。`c100-before-control.json`、`c100-trace-finish.json`、`c100-after-control.json` 的 SHA-256 分别为 `428B64DEA74202B5C5A2835E3079964C2227EC83946B3BB7A666E6D3CAB364EF`、`644580703FE18769B081CCEBCC96B473BF459E4489835777117D6B070014FBFC`、`14055050DBA2548FFEB71B14CF4D32CFC1C55F7170D345C1EA5D1C8415EEC089`。`cleanup-check.json` 证明退出码 `0`、`cleanup_ok=true`、最终 CK3 进程数为 `0`，绑定的 session/report SHA-256 为 `D2A7D6AE1D45E7BA0B93BD1F0EA359CDCA3594BB450FDB93CA908FB9EC9A2AC1` / `3B2E2BF73CFB82F30BFC9D50FAD903A03C31BDF4F907EAFB5E2AB93081E916CA`。

这只验证两次主战日的**实际反制输出向量与条件模型**。回执仍明示 `full_mutable_transition_bundle_complete=false`、`original_trace_ready=false`；下一日非骰子优势、骑士动态参与以及其他可变输入尚未接进生产现役续算。不能据此报告整场胜率或称终局校准完成。
