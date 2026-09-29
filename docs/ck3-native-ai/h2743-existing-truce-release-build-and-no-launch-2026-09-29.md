# H2743 投降前既有休战槽：Release 构建与无启动配对

状态：**原生构建与无启动准入 GREEN；CK3 live 尚未执行。** 这只为 Draft PR #448 的默认关闭候选 `preaction-existing-truce-v1` 准备精确 DLL、Python 路由和原始 H2743 输入，不构成休战旧槽实测、投降效果预测或正式退出动作。

## 精确构建

独立源码工作树 `D:/w/h2743_exit_build_01` 从 PR #448 的原生源码 HEAD `3841f830a0511c65f99043571f779c953f32ecae` 建立。新外置构建 `D:/ck3-research-artifacts/h2743-existing-truce-release-20260929-attempt03/` 的 `candidate-manifest.json` SHA-256 为 `0E98B9E1FD13A6CCD550E582ADEEA82D161B063DD7AF97B6D75DC0FB9260D04C`，`build-receipt.json` SHA-256 为 `E6991CD2A46ED6A30FBE0995D1F6F8494F6FF9548FA6E77E8A8E744073AEE67B`。前两轮 attempt 只在 MSVC 环境初始化停止，未配置或编译；各自保留，不覆盖。

Release CMake 明确设置 `XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1=ON`，Ninja 207/207；精确 CK3 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。冻结源码/ABI 校验通过，native source fingerprint 前后一致且 tracked 工作树干净；普通与 `-O` 的原有源码测试各 6/6，原生 CTest/JUnit 1/1。DLL SHA-256 `DAE3E3F5DBA5AD936EC85A22584E33D58379E2ACE107D6E044AD7F8CEF7C4C02`，配对 injector SHA-256 `2261CCF9FD919E329014720A4AD797B988C53FB46DCA234B48A50A8C03FEF931`。构建没有启动 CK3。

Python driver 新增这一条精确只读命令的能力门、暂停帧 claim 以及 C++ 所要求的日期、snapshot、episode、checkpoint 和 EXE 字段；协议校验拒绝错方向、帧漂移、伪造未来期限、效果完成或动作字面量。runner 仅在显式选择新候选时切换到上述 DLL/injector，并计划同一暂停帧读两次旧槽，其间复核一次终战选项；它仍没有投降、白和平、日期或行军提交路径。新协议测试普通与 `-O` 各 7/7，runner 测试各 14/14。

## 无屏幕、无启动输入配对

最终外置 `D:/ck3-research-artifacts/h2743-existing-truce-readonly-20260929/attempt-4-dejure-baseline-no-launch/` 的 source pair SHA-256 `E98BDB41522B4B37A670B5EFE3F750F376841DE6D0B5A6BB038F57D99FB3B42C`，READY SHA-256 `2069B3BD94F1489D709FBFFC317895DCDF1CC71A41D0C9A239277E83241B5162`。独立 `attempt-4-postcheck.json` SHA-256 `71D9298069AE3731DAC7C58E5963C0BB8024431EACF2F75AD99C439EB08107E4`，状态 `EXACT_SOURCE_PAIR_NO_LAUNCH_READY`。它重新核对源 save、driver、family sidecar、源 DLL、新 DLL/injector、EXE、war values、构建 manifest 及 runner/driver/contract 的精确 Python 字节；生成独立 profile，放置存档原件，ordinary seed rebind 后由 one-generation preflight 返回 `ready`。派生 driver SHA-256 `A2D84254A148BF58B4439053A6E4D2E9CB8DC5831309B8E23D8525BC11844A7E`；preflight report SHA-256 `135153B363D9A41A043FB4B3E85130B4F1111BE45439CA211159F58BC38E4CD6`，进程清单空、`desktop_interaction=false`、`ck3_launch_attempted=false`。

attempt-1、attempt-2 的旧 runner 准入保留为历史。attempt-3 在准备过程中因协议文件字节改变，被 preflight 的 `agent runtime fingerprint differs` 门拒绝，故为 RED 并原样保留；代码冻结后才创建上面的 attempt-4。此处的 `open_kaishek` 确定性预验判定为 `not-applicable`：步骤只验证精确文件身份、Python profile 和 CK3 进程内 `HasTruce` / `GetTruceEndDate` 的 native 指针读口，没有可由其 parser、validator、IR、finite runtime 或 replay 复现的脚本执行子集。

## 后续 live 门

H3937/R0271 的屏幕队列优先；本轮未领取 `ck3-screen:acquired`，未启动 CK3。下一次若取得屏幕，先重判 `open_kaishek` 子集并按 `tools/ck3_live_run_id.py` 生成实机 run ID，再取得独占屏幕租约和**当次**人工审阅的新鲜 Steam“离线模式”原图。live 启动前应再次核 `attempt-4` 的 READY、source pair、Python 字节、配对二进制和原始输入；如任一变化，另建 attempt，不修改旧回执。只能运行 `--candidate preaction-existing-truce-v1 --run` 的只读双读与同帧终战选项复核，保存 raw payload、revision、date、模块路径/磁盘 SHA、受管清场和源文件后哈希。H3937 等待期间不启动此 live。

即使未来读到 `existing_truce` 和投降前旧 expiry，也不能推断本次投降后的实际期限、FP2 付款、Title/封臣或其他完整效果。当前 `effect_projection_complete=false`、`material_complete=false`、`action_literal=null`；正式第 36 turn 退出选择及终战动作门未解除。
