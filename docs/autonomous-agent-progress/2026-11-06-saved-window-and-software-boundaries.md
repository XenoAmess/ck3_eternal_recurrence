# Saved 窗口、恢复结果与软件验证边界

本切点为 2026-11-06T21:42:25.765332Z。功能恢复、模型响应、软件验证与新增保存日分别记账；10 秒／新增确认保存游戏日的目标尚未达到。

## 完整保存窗口

以原 1323 窗口起点 `2026-11-06T10:54:22.3482445Z` 为起点，最后一次确认保存仍是 1475，时间为 `15:49:08.1922044Z`，累计新增确认保存 38 个游戏日。

| 窗口 | 墙钟秒数 | 新增确认保存日 | 秒／保存日 |
| --- | ---: | ---: | ---: |
| 起点至 1475 确认保存 | 17685.8439599 | 38 | 465.4169463 |
| 1475 后至本切点 | 21197.5731276 | 0 | 无有限值 |
| 同一起点至本切点 | 38883.4170875 | 38 | 1023.2478181 |

完整窗口包含恢复、失败、软件准备与等待。旧的 465.4169463 秒／日只描述截至 1475 的闭合窗口，不能覆盖后续零新增保存日的耗时。当前整体结果没有达到性能目标，也不能凭局部解析命中声称改善。

机器原件：`D:/ck3-state/resume91-runtime/resume-after-user-play-20261105/m7-retained-repair99/action-unknown100/COMPLETE-WALL-ACCOUNTING101.json`，1279 B，SHA-256 `379f52fe` 前缀；其来源为独立核验的 `SAVE1323-1475-WINDOW01.json`，3711 B，SHA-256 `563d72b762e13266389693006910cc3310f556ee29eed4091fc0b3d9851f1c88`。本次计时汇总没有新增 Game 查询或 Runtime 启动。

## 已实际越过的功能边界

同一 Game102152、keeper35300 的 retained 恢复在 `20:36:53.1764628Z` 返回已有 SavedEntry/head36，随后 `20:36:53.1774429Z` 进入普通 LOOP，next1。START 至 LOOP 共 275.0576809 秒；这是保留原 B0 消费记录后的恢复，不新增 SavedEntry、游戏日或保存信用。

专属 Sway 模型输入投影随后取得真实 HTTP200：请求 955689 B，服务报告 prompt 387158 tokens、completion 134 tokens，总耗时 51.438 秒。该结果证明本次请求越过先前的上下文长度拒绝；它不证明动作执行、游戏推进或保存。

随后 B1 于 `20:42:08.792192Z` 进入 ACTION_UNKNOWN。父动作保留为 COMPOSITE_UNKNOWN，实际 attempted1／applied0／positiveACK0／saved0，Java24536 退出 4。原父子命令期限 `21:06:53.1953352Z` 自然到期，未刷新期限、重放动作或清除原账本。Game 与 keeper 的最近运行岗回执仍为保留，本文没有新增现场核验。

相关原件分别为 `m7-retained-repair99/frozen-loop99/ACTUAL-RETAINED-LOOP99.json`（6393 B，SHA-256 `2aee96951776da559fa9aa23b6ec05ef48a7e64ae9d75ee12d8403d5bb8ecfce`）与 `first-http20099/FIRST-HTTP200-AND-PLANNING99.json`（12251 B，SHA-256 `3645fd577dfe9c0b97becf26194b2d9abfe760c81345c5cc294cc0caff8d1096`），路径前缀均为上述 Runtime 数据根。

## 软件通过与当前限制

P097 的同调用 Driver 重复解码优化已正式发表为提交 `5b18edbcec6ff40eabbdbab7b301bcf453095a77`。实际两生产源 12 个 class、真实保存 Driver 的独立 DATA 测试，以及保留正式 IO scope 的最小两 TU／既有测试二进制组合分别验证通过。该测试没有覆盖旧 `verify(pair)` 的 IO scope 行为，也没有提供实际保存日吞吐改善的证据。

P101 仅实现独立的原 SavedEntry／原 episode 与新 transport session 身份路由及严格 schema 软件。当前 head47 含 reserved child1，既有空 child 与无玩法写入门保持；该候选不能据身份与 schema 测试取得运行准入。原 UNKNOWN 的首个异常原因仍未定位；P100 后续诊断因 provider 的 `possiblecybersecurityrisk` 拒绝停止，没有重投、改写或换岗继续该链。
