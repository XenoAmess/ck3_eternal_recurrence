# R466/R467 Stage 10 近边界来源淘汰与 Operator 启动修复

## 结论

R467 从距 `zg361cl.390` 仅 2 游戏日的真实 production 存档启动并在固定 10 游戏日上限内停止。该帧再次证明 Central stage 9，但没有符合 Stage 10 的直属 AI celestial manager；同帧 Workforce owner 查询也明确缺少 Stage 11 所需的 owner/portfolio/case 绑定。该存档不具备 Stage 10 或 Stage 11 来源资格，不能计入 P1，今后不得再次重放。

这次运行没有暴露新的 mod 产品 bug。Stage 10 返回结构化 `INELIGIBLE`，Stage 11 的 runner RED 是来源资格在动作前没有被完整筛掉；产品 Stage 10/11 均为 `NOT_EVALUATED`。P1 仍为 `6/9 = 66.7%`，P2 最终宣传视频继续硬锁定。

## 启动前 Operator RED 与最小修复

首次提交作业后超过三分钟仍没有 CK3 进程、live state 或 artifact。只读线程栈显示 worker 卡在后台线程首次导入 `run_zhongguo_acceptance` 的依赖链：

`run_zhongguo_acceptance -> run_acceptance -> pyautogui -> pyscreeze -> cv2 -> numpy._core.multiarray -> create_module`

线程转储位于 `Z:\ck3_mod_rewrite\_runtime\p1-stage10-near-source-r466-r467-20260912\prelaunch-hang-thread-dump.txt`，SHA-256 为 `70957B4B3582968929F2C686BE6072248FF24853A7EB3312A3C1D6C0A3A3C675`。该尝试没有启动 CK3，因此没有消耗轮次。精确停止作业和 MCP 进程后，CK3 与端口清单均为空。

最小修复让 Operator 的 `start()` 在进程主线程先完成路径装载和 acceptance 模块导入，再创建 worker。四个直接相关模块的测试为 `27/27` GREEN；主线程首次导入约 `0.931 s`，worker 复用缓存导入约 `4 us`。未扩大到完整 L0，也未为这项 Python 小改动单独启动 CK3。提交 `c9937ca8466ab7354cdac7cbb8b4fc5043b06fc8` 已推送并与上游分支同步。

公共 MCP capability/schema、Java/profile、DLL、游戏文件、启动配置和加载顺序均未变化，因此 open_kaishek 不需要代码同步。这个修复更新的是可复用 Operator 生命周期资产，避免其他机器或操作者在 worker 首次导入重型原生模块时无响应。

## 运行绑定

- exact build：CK3 `1.19.0.6`；`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- production tree SHA-256：`84443728419E390024936809778C98D4BF4B529747FF776DE0F2FD4DC97E58CE`。
- 输入存档：`Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource_state\profile\save games\autosave.ck3`，`101,827,548` bytes，SHA-256 `F7A3AC56E1CEC7B6CA7CC449B9160E087779BCD503A8A6A647241AF9931CB3B6`，header `date_raw=53313360`。
- activation：`409E1F96D62DB8C3A4C65913959045E8192A9F0EFB60F53FE4D2C92DCB37E194`；checkpoint provenance：`1C57C7B2956A228E1BA5C5DB096CC0782EE4EFD3CB6D14BCC787C54808CD92AF`；direct preflight：`6414F4A614E77D024BCA2C4048945C1E7DB0D71912B2DFEAE0AD835EC6ECDA93`。
- Operator target：`local-interactive-operator-r466-r467-p1-stage10-near-c9937ca`，作业 `eee13112-d4b6-45b4-8c10-a9711ca2402f`；bootstrap SHA-256 `C3D43580A57D2F73549104A9A2B19C45217B972B82DFCE7E65F98404E103204E`。
- 当前轮次 R466：frontend warmup，PID `75336`，在约 `12.046 s` 后到达已认证 Frontend，随后正常结束。
- 新轮次 R467：唯一 gameplay PID `59536`，connection generation `1`。R466 结束后才启动 R467，全程满足 CK3 单实例串行。
- 实际运行目录：`Z:\ck3_mod_rewrite\_runtime\p1-stage10-near-source-r466-r467-c9937ca-20260912`。

## Stage 10 来源判定

R467 在 `date_raw=53313408`、instance `418` 观察到真实 `zg361cl.390`；从输入日期到目标仅 48 raw hours，即 2 游戏日。玩家与事件 owner 均为角色 `32904`，Central stage 9 再次观察为 GREEN，但该门已在 R433 签收，本轮不重复计数。

同帧通用 selector 返回：

- `status=unavailable`；
- `unavailable_reason=no_bounded_ai_direct_manager`；
- `manager_eligibility_ready=false`、`direct_subordinate_ready=false`；
- `selection_attempted=false`；
- action cell 结论 `INELIGIBLE / eligible_stage10_manager_unavailable`。

因此没有生成 `zg361_stage10_player_subject_source_v1` checkpoint receipt，也没有切换玩家或尝试 Stage 10 `.120`。这不是 `.120` 产品失败，而是该世界状态没有可用的 owner → AI celestial manager 路线。

## Stage 11 来源判定

同一暂停帧的 Workforce owner provider 找到 Central subject `30317`、cycle `4`、case `3`，但 Stage 11 身份链没有建立：

- `stage11_status` 不存在；
- source status 为 `0`，source owner/subject 与 P2C/AL serial 均不存在；
- AL case、`.360` receipt 和 portfolio 字段均不存在；
- `player_owner_binding_ready=false`；
- `portfolio_subject_binding_ready=false`；
- `case_identity_ready=false`；
- `unavailable_reason=workforce_owner_identity_not_bound`。

runner 保留 `TerminalStagesError: native gameplay step failed: ZhongGuo workforce owner snapshot changed or is not ready`，`current_stage=11`。这个 RED 暴露的是 source qualification 未在 Stage 11 动作前短路，而不是 Stage 11 产品状态被执行后破坏。后续必须在启动前或首个只读暂停帧淘汰缺少上述身份链的存档，禁止把它扩成实机长跑。

canonical RED 为 `terminal-stages-red.json`，`913,108` bytes，SHA-256 `C6658E23F2492D597670C7695FF73AE825DBABDFF0C1B8EE884C64380E86BC32`；attempt-01 内容相同。完整 loader error scan 为 `02_loader_error_scan.json`，`11,076` bytes，SHA-256 `2345F5896D84430301BA7CB1BBF59772A073C0F02F311DE0D6230F43262F15DA`。

## 有界停止、清理与下一步

R467 在目标出现后的同帧完成两项只读资格判断，失败快照最晚只到 `date_raw=53313480/53313504`，仍在配置的 10 游戏日上限内。没有为了单个缺口继续长跑。

- canonical cleanup：`09_phase2_native_session_cleanup.json`，`32,497` bytes，SHA-256 `9B9046809D0F5ED9CAA6E07586987D591A482942ABCFF33BCA39C84DA8A11261`，GREEN。
- managed cleanup：`terminal-stages-managed-cleanup.json`，`34,110` bytes，SHA-256 `D765BFADF45256BB9FFE433F32E85A3821A34E0E7CDFCD0D385DF306315D6207`，GREEN。
- 当前轮次 R467 已结束；旧轮次 R466 已结束；CK3=0，Operator MCP=0，端口 `12432` 已释放。
- 该输入以及此前所有返回 `no_bounded_ai_direct_manager` 的 `.390` 帧均加入不重放集合。下一步先离线核对真实 Stage 10 manager 条件与 Stage 11 owner/portfolio/case 条件，只在候选能新增信息时启动新轮次 R468。

本轮没有触碰 T0 视频锁，没有改变 T1 G2，也没有改变 open_kaishek 对外接口或兼容行为。
