# 公开用例失败后的资源接续与 CoA 字段语义

本次来源机器为 `desktop-3fevhd2-1c74096080`，观察日期为 2026-10-26。R0020 的历史事实见 [原记录](acceptance/R0020-2026-10-26.json)，不补签其任何阶段。

R0020 的公开 case 原进程返回 2，托管 host 原进程返回 0；host 的 `GREEN/error=null` 仅表示 host 完成。原 retained wait 为 `signaled=false/exit_code=null`，随后 native Job 清理报告 CK3 退出 1、tree gone、cleanup proven、Job final 0。Keeper 原 wait 0 与真实 CAS 释放另行完成。这些来源不能混成正常 Quit、原 retained OS0 或业务通过。

`tools/ck3_mod_acceptance_allocate.py` 在既有 failed-live 合同内新增 `case-client-failure-retained-wait-expired-native-cleanup` 分支。共享 `case_client_cleanup_bundle` 只编码原始 FilePin；序列化后仍须由原 `previous_failed_live_resource_closure` 消费。新 validator 以 `CaseClientNativeCleanupFacts` 固定十个返回字段，明确 false、null、整数退出码和文本错误／出生身份。公开 `allocate --previous-failure-close` 沿原分派消费该合同。Prepared、runtime/state、原 public wait、host、case error、retained identity、native cleanup、Keeper STOP/wait、CAS、当前进程与控制文件全部检查，资源资格没有业务或正常退出资格。旧 host 非零分支不因此放宽。

共享回归使用 `tools/fixtures/ck3_R0020_case_client_failure_native_cleanup.json` 的真实字段摘录。完整原件 pins 与摘录分开保留；frozen argv、prepared case、native report 明确是字段投影。临时重定位文件和进程缺席是测试输入，不冒充又一次实机观察。回归覆盖共享 producer→JSON 往返→完整 consumer、错误类型/原 wait 缺失、错 pin/错 run、未清理/仍存活/屏幕仍占用、原未知 wait 被升级等拒绝路径；新增 producer/validator/实际分派 AST 范围执行严格类型检查。

需求要求保留原 Dynasty 与实际 House 的原纹章，没有要求两者必有两个独立 CoA 对象。下一新场的 core 第 7 标签改为 `preserve_original_coa_fields_objects_and_designs`，其余阶段、七断言、13 fixture 文件与 25 markers 不变。原字段缺失必须仍缺失；原字段存在则保留其实际值，实际对象存在则保持对象 ID 与完整设计 AST。House 缺失 ownCoA 不能借 Dynasty 图案声称存在第二对象。这是断言措辞纠正，不修改产品纹章行为；Java emitter→公共 prepare→冻结合同回归检查新标签完整传递。R0020 冻结合同及原断言不改。

本机 2026-10-26 完整 `tools/test_preserved_failure_native_os0.py` 实际运行 12 项、零失败／错误／跳过，包含新增 producer／validator／实际分派的严格类型范围。首次执行因原解释器缺 mypy 而退出 1；仅向 `PYTHONPATH` 加入既有 `typecheck-packages` 后完整重跑退出 0，没有安装或修改全局依赖。退出码范围严格为 `0 < code < 2**32`；时序用 UTC epoch 的整数纳秒比较，回归包含上界、错误类型和前后一纳秒。完整受影响 CI、Maven 与后继实机仍须独立实际执行，当前不追认通过。需要新的源固定点与后继运行图，不热改 runtime19，不复用其未知提交。

同机随后将真实R0020的23个必需角色原件交给该producer及完整consumer预验，原进程退出0，未mock进程、mtime或bus，未分配编号或启动游戏。新鲜bus列出1123个任务且无SCREEN owner，实际293进程扫描无blocker。原public2／allocator0／host0／native Game1及原retained未知全部保留；资源接续通过不授予正常、typed或业务资格。输出根为 `C:/ck3-dynastic-esotericism-20261024/resume-builder-a20/attempt-a10/captures/r20-actual-resource-consumer-a01/`：bundle 7192B，SHA-256 `bb96c8d51364f429f3f85fc56861dd562021e22d73b739b7b44543094e45d35e`；完整consumer结果16526B，SHA-256 `d5667611e637b3330647f5b2089de810fc3ccbcc96ed27d99eed99c925ad1e9d`。预验绑定当时dirty源的实际pins；下一次公共allocate仍须消费原bundle并在原writer锁内重验，不能把此预验当新场准入。

2026-10-26T06:51Z，同机后继发现原资源预验在机器writer锁之外。新共享 `revalidate_failed_live_resource_admission` 在 `claim_machine_admission` 的原 `chain.lock` 内重取完整bus、重跑真实reducer，并复核原bundle／release／23项证据及当前源索引和实际consumer；任何漂移在intent前拒绝。外置完整叶17项均通过，包含真实Selection、OS锁、原reducer及前后漂移负例；原失败回执保留。该结果尚不是canonical完整91命令或新场准入。原Game1／retained未知／正常与业务false语义保持。
