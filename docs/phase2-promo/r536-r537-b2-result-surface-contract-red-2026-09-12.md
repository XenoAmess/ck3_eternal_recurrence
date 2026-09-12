# R536/R537：B2 动作后展示面合同 RED（2026-09-12）

## 轮次与结论

- 旧轮次 R535 已终止后，R536 以 CK3 `1.19.0.6`、EXE SHA-256 `2D00FF31…3DB86` 完成前端热身并终止；新轮次 R537（PID `157628`）作为唯一 gameplay 实例运行。
- 捕获绑定 harness commit `1e2485314da8a9434f358a89b149b5d8f071b018`，产品投影 tree SHA-256 `C428C42B…CB5DC`。沿用 R533 已验收的 DLL `3D41E88A…3CF48` 与 injector `6A4E7A04…61E2C`；没有 DLL、游戏文件、加载顺序或启动配置变化。
- R537 通过 loader、native、paused seed、八项 feature、FFmpeg、第一段榜单开关和第一段 clean begin/end。随后 exact `zg361b2.40` 的身份、三项文本、option 1 提交以及同 owner/subject/cycle/case 的 `state 1 → 2` provider 后置条件全部 GREEN。
- 整体仍为 RED，错误为 `scenario_surface_not_visible`。失败发生在 B2 动作已完成之后、第二段 clean hold 之前；不回退 B2 动作 GREEN，也不把第一段单独提升为可用素材。P2 继续为 `0/8`。

## 根因

`zg361b2.40` 的三个产品选项只写入 PIP 回应和业务状态，然后关闭当前窗口。实机 action ACK 明确记录 `new_event_instance_id=null`，同一暂停帧也没有 active event。产品定义同样证明该选项不会触发 `zg361.4`。

旧捕获计划却把 B2 clean surface 写成 `zg361.4`。`zg361.4` 实际由考绩结果送达 effect 提前排期，是 PIP 前面的送达事件，不是 PIP 选择的后继。runner 因此在正确完成 B2 动作后立即寻找一个不会出现的旧事件，构成捕获编排 RED，不是 mod 业务 bug。

## 最小修复

- B2 span 保持以真实 `zg361b2.40` 为 source，动作及 provider 后置条件不变。
- B2 动作 GREEN 后复用已经通过实机验证的 scoreboard open primitive，打开 `named_widget:zg361_scoreboard_modal` 作为 clean result surface；该榜单能呈现执行中的 PIP，连续原始录像仍保留 PIP 窗口、选择动作和动作后榜单。
- 第二次榜单调用使用独立 nonce 和 `07d_phase2_b2_pip_scoreboard_visual_action_cell.json`，不覆盖第一段的 `07c` 证据。
- 榜单必须自身返回 capture visual GREEN；否则以 `b2_postcondition_scoreboard_not_green` 保持 RED。clean hold 后继续走同一 provider-owned close 与独立 hidden-modal 查询。
- 同步修订 `docs/phase2-promo/phase2-live-event-choreography.md`，删除 `zg361b2.40 → zg361.4` 的错误后继关系。

## 有界验证

- `test_zhongguo_phase2_event_choreography.py`：`4/4 GREEN`
- `test_zhongguo_phase2_event_choreography_runner.py`：`17/17 GREEN`
- `test_zhongguo_phase2_promo_runner_plumbing.py`：`20/20 GREEN`
- 受影响 Python 文件 `py_compile` 与 `git diff --check`：GREEN

没有运行全仓测试，也没有为这一 Python 编排修复重复执行长跑。下一轮仅验证 B2 postcondition 榜单能进入 clean hold，然后继续后续 span。

## R537 证据

| artifact | bytes | SHA-256 |
|---|---:|---|
| `capture-plan.json` | 11,284 | `C0BFDFD26B546448069F4F5F8B9363CC35FC3CE1C75D92DF958DA2059EFF7B2C` |
| outer `capture/report.json` | 4,372,791 | `561B6FD02AEBB0281F8BBE40D90A80CCE03489CD9F40F7C24690AC9989DB483F` |
| inner `capture/cell/report.json` | 4,317,864 | `2E6B0614F83B2AD56974237CC08DB1424AE95557EA7772E4F58757F2DBFABACA` |
| B2 action cell | 5,497 | `5565A6B98FFD3D271FB7F55CF459FE758C9A64E28C3390F683F6A2C5A9914B45` |
| first-span scoreboard visual | 141,425 | `A3E215A91044B5DEF9E3EAF29820DB09C2D9A1FA014E28C2F8BEE2834B996610` |
| cleanup | 31,756 | `3D8E8DF38B1AF86E61BE78EF414BC5FE145C5A724118209400FC7EB9E3191240` |
| timeline | 14,596 | `19AC1E7E6786F49A965AD5CE81EFC243DBCCDA43FD9E3DADB6BDA1B50CCA290B` |
| evidence index | 11,413 | `E01CC57358B63C142FAB47992C96172BF20ABCEEB2C1346CABA651A7C231A247` |
| failed raw MKV | 25,793,759 | `2948F7A2DC41066CBC669A9308F55216D7FF3F7A6B4A72C87BF8F48D03E0FFF2` |

artifact 根目录：`Z:\ck3_mod_rewrite\_runtime\p2-capture-r536-r543-1e24853b-20260912`。cleanup 后 CK3、FFmpeg、injector 均为 0。此次只改内部宣传捕获编排，没有公共 MCP/schema/ABI/版本/依赖变化，不触发 open_kaishek 兼容层修改。
