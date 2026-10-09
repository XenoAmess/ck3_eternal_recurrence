# 共享冷载延后单次注入与 Source04 冻结证据（2026-10-10）

本次共享 Python 修正增加默认关闭的 `--saved-campaign-inject-after-load`。显式启用时，原 CK3 进程 resume 后等待当前已清空日志 epoch 的正式 `Setup completion (history loaded)` 标记，再向原 PID 注入一次。原进程 HANDLE、Job、watchdog、命令行及清理路径继续使用；日志标记只决定注入时点，不授予地图、角色、根、事件或业务身份。

只有本机公共 runtime 的全局 manifest 显式启用 `host_features.saved_campaign_inject_after_load=true`；产品不能据此选择另一份运行时。整个加载、native 连接与 saved-startup 准入共用原 600 秒绝对 readiness deadline，不在注入后重置预算。原同 owner 的两个相等 native 帧、pump 严格推进、paused、actor/date、根身份和显式事件 contract 门禁保留；R40 的重复 pump 27770 不会因此获准。

作者提交为 `1d4468fc35361be5126acd84402ef27b87d71254`，parent `4c874cfaf45007c1b4d043011b90e9724a4aeb46`。Root 对主线 rebase 后普通 push，精确 master 为 `6a3affdb87f03f01bdc9f4dc43aeff15960200db`，原 rebase/push 退出均为 0。独立复核结果为 `STATIC_REVIEW_PASS_LIVE_UNPROVEN`，保存作者最终五文件、原 baseline、守卫 AST 对比及 599→600 秒剩余预算探针；没有把早注入与 R40 故障的因果假说写成已证实。

Source04 固定提交 `919bae0f42def04e6398eb2de4b4afe20dcfc106` 的唯一父提交为 Source03 `13d063c81ff706d8bc3f9a8bf81f60c283338042`，tag `archive/common-runtime-source04-20261010` 已实际普通 push。Root 仅把作者 delta 应用到该固定父提交，避免混入主线其他研究改动；完整作者文件和重建的 Source04 文件分别保全，不混用整文件 SHA。实际来源索引只有以下五处改变：

- `ck3_autonomous_player/src/xar_autoplayer/runtime.py`
- `ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py`
- `ck3_autonomous_player/tests/unit/test_saved_campaign_delayed_injection.py`
- `tools/ck3_mod_acceptance.py`
- `tools/test_ck3_mod_acceptance.py`

Source04 位于 `C:/csr4`，metadata 位于 `C:/workspace/ck3-common-runtime/20261010-003`。整个 native 目录只有 host Python 改变，其余文件逐字节相等，编译输入保持原样，直接复用 `C:/cbr2/xar_ck3_bridge.dll`（9459712 字节，SHA `390506e486f5b19e298070523360d420de255a7811b5e79a5b279d5f9331dbbe`）和 injector（39936 字节，SHA `2e22a985ba3166ce50ca1732901f0bac0629e8ff0f068de73330fdd5d09c86a8`）。没有新 native build 或新实机资格。manifest 原 qualification 为 `PYTHON_FIX_NATIVE_INPUTS_EQUAL_NOT_LIVE_NOT_PRODUCT_PASS`。

| 验证范围 | 实际结果 |
| --- | --- |
| 作者 validation 002 | lifecycle 与 runtime 相关测试退出 0；当时 entry 退出 1，原件保留 |
| 作者 entry 003 | 修正新 feature 后的 fixture pin，实际退出 0；旧失败不覆写 |
| 独立 review | 源码/守卫复核及剩余预算探针通过；LIVE_UNPROVEN |
| rebase 后主线相关测试 | entry 16、delayed 8、failure-shutdown 4、normal-close 4、operator-quit 16，共 48 项通过 |
| Source04 lifecycle | 原 8 项通过 |
| Source04 完整 entry suite | 运行 15 项，1 ERROR：冻结导出未包含测试读取的 `workshop/products.json`；完整 suite 未通过，原错误保留 |
| Source04 定向 global flag / host help | 新 flag 1 项通过；help 退出 0 |
| 新 case 准备 / 预检 | `lyd-transaction-control-20261010-003` 的 prepare / preflight 实际分别退出 0 |

exact `6a3affdb8` 的 [Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37995375811) 实际 completed/failure，失败 step 是 `Test shared CK3 acceptance without installed CK3`；[Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37995375808) 为 success，Li Yu Dao static checks 为 NOT_TRIGGERED，不计成功。原 API/失败日志/完整 workflow 日志由独立 owner 保全于 `C:/workspace/ck3_lyd_runtime_20261004/r41-exact-6a3affdb8-ci-20261010-001`，本包仅纳两份终态边界回执。另有 `r41-poll-reporting-fixture-candidate-20261010-001` 的外置六项复现/修正候选；其 PASS 不追认原 CI 成功，不属于此 Source04 五文件修正。

本候选在 R41 keeper 冻结现场期间只于外置目录准备，封存前后仓库均为 `6a3affdb8`、dirty 0；没有 tracked 修改、commit、fetch、rebase、push、游戏或屏幕动作，也不跟踪变化中的 R41 run 文件。本包不评估 R41 最终实机结果，不授予 case、业务、产品或共享 runtime live PASS；最终现场由独立包记录。R39 / R40 原失败与完整证据包继续保留。

[EVIDENCE.zip](acceptance/2026-10-10-shared-delayed-injection-source04/EVIDENCE.zip) 固定 133 项新证据，共 3097076 字节，SHA-256 `fc5e5deb84a3c2dcbaea8902f59fe9dd3846b09d94e9f6e75af761ecab31f35a`。包含作者 handoff/validation 原件、独立 review、48 项主线测试、rebase/push 回执、Source04 全部小文件、source/native 索引、freeze/bind/check producers、Source04 五文件及准备/预检回执；不重复 R39 / R40 整包。完整 Source04 ZIP 53555249 字节仅 pin SHA `afb56a009310205372c11e1b467862823bc10e15a37d8848c13d48c8d83a672c`；R34 D2a seed 91711686 字节仅 pin SHA `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`。

[INDEX](acceptance/2026-10-10-shared-delayed-injection-source04/INDEX.json)、[FACTS](acceptance/2026-10-10-shared-delayed-injection-source04/FACTS.actual.json) 与 [VALIDATION](acceptance/2026-10-10-shared-delayed-injection-source04/VALIDATION.actual.json) 记录每项来源及复验。作者 handoff 中历史仓库路径按精确作者 Git blob 和已保存的 `author-final-source` 复验，不把 rebase 后的当前文件外推成历史字节。[producer](acceptance/2026-10-10-shared-delayed-injection-source04/package_evidence.py) 仅封存既有静态文件；证据一致不等于完整 CI 或实机通过。
