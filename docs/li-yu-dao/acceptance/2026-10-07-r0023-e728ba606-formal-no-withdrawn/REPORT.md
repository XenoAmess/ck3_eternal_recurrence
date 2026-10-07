# R0023 正式首轮反对、撤回与正常 UI 退出

本轮完成正式提案、代表委派、封存和两项玩家确认；NPC65865 实际反对，票数为 2 人中 1 人赞成，未达到三分之二。因此没有最终签署、factory 或新宗教 Title。整体仍为 NOT_GREEN；一期工作量暂估约 75%，不是验收通过率。

运行编号 `bf-202609141645-5434332d4d--li-yu-dao--R0023`，加载源码 `e728ba6067ea7b8e2438b71d46f54718071c9ca5`，CK3 1.20.0.4/build25734779。原0240基线、本轮 B2、待签署窗口和撤回后的独立保存均取得原生读回；四次保存的保护校验各 87 项通过。待签署窗口没有签署信用。

正式撤回清除了 active、authority、owner、delegate、vote 和 consent 状态，保留 serial1/nonce2 历史。续跑存档为外置 `live-attempt-023/checkpoints/R1-withdrawn/checkpoint.ck3`，91,670,781 字节，SHA-256 `5501caf084a7cc6058c63d5b540e54dd2770596a51184f340a36aa0e593205fe`。七个政治头衔、HoR169、人物身份和钱包均保持；新冷载应从这里继续 serial2，不重新加载原0240重复首轮。

执行者最初把 begin/seal 的预期事件误填为410/411，而实际前台为430；两次业务效果只执行一次，原失败回执保留。该未核验 claim 拒绝本进程的新一轮确认，拒绝发生在 dispatch 前，没有删除 claim 或伪造通过。未来 begin/seal/review 预期为 `lyd.430`，代表事件为 `lyd.410`。

本轮 DLL 的正常退出 inventory 校验仍硬编码旧1.20.0.3 EXE SHA，实际1.20.0.4查询因此不可用；未消耗退出 claim。隔离修复已通过一次 focused production 编译与七项身份案例，但不授本轮 DLL 退出资格。随后实际通过游戏菜单“退出到桌面”正常退出，Steam保持离线。外部原 game HANDLE 观察遇到 wait258/exit0 竞态，原结果为 UNKNOWN、wrapper exit1；不能写成原HANDLE wait0，也不能写成 typed退出或autosave验证通过。新的现场进程清场、原Client/keeper句柄和原执行退出码、CAS释放单独构成 operational closure。

构建目标和 focused tests 编译/运行成功与 Defender 登记失败分列；没有把调用ACK当设置读回。本轮及隔离 focused 的环境RED、错误预期事件、schema拒绝、未执行确认、材料化首轮失败和原observer UNKNOWN全部保留。

`INDEX.json` 与 `raw-evidence.zip` 保全本轮小型原始回执、原生/SDK查询、请求、读回STATE、保护校验、菜单截图及退出边界。CK3大存档与原构建输入继续永久保留在外置目录，没有重新解析或归档其正文。下一步整合版本绑定修复，按新clean HEAD/build/profile从真实撤回存档冷载，继续正式宗主成立，再进行新Title的NPC授予、争统与I4代表高风险/自然到期/冷载。
