# H2743 全战争槽只读候选 v5（2026-09-29）

## 证据边界

H2743 attempt-12 的暂停帧已证明 WarID `16777231` 守方投降按钮合法且会被接受；具体终战条款仍 `terms_observable=false`。本候选只读取 WarManager 的完整槽状态，寻找 Landolf `30097` 主攻、Robert `29829` 主守且 CB key 为 `fp2_border_raid` 的在役战争。它不调用 CB evaluator、setup/resolve effect、终战提交或日期推进。

原版 `00_war_values.txt:54–65` 使用 `any_character_war`。完整 WarManager 槽扫描与该脚本迭代器的等价性尚未证明，所以新增 `border_raid_storage_candidate_v1` 只可标为 `structural_candidate_only`。正式 `truce_inputs_v1.border_raid_pair` 继续 `unavailable`；休战天数、到期日、title/封臣和资源 delta、续战风险、推荐结果与动作均为 null/不可用。即使槽扫描得到 `false`，也不能据此推断原版条件为 false。

## 原生读口与失败门

新读口复用 CK3 1.19.0.6 已有的 `game_data + war_manager_offset`，遍历 `storage.capacity` 个槽，记录每个槽的空／已结束／在役状态和对象指针。每个在役 War 均要求完整 WarID 的低 24 位与槽位一致、`ResolveWar` 往返回查相同、主攻和主守完整 CharacterID 合法且出现在各自参与者集合、active CB index/key 可读。目标 WarID 必须恰有一行，且对象指针、双方、CB index/key 与 V1 当前帧相同。

读口在同一暂停查询中扫描两次，逐槽比较 capacity、完整 ID、对象指针、双方、CB 指针与 key；任何缺槽、漂移、异常、无法读出的在役战争均给 typed unavailable。前后原生 snapshot、资源余额、目标 Title holder 和现有 V1 身份门仍需一致。C++ 纯函数 admission 和 CTest 覆盖正例、无匹配的完整负例、已结束的 raid 不计数、缺槽、错槽、同槽不同 generation、CB 指针/key 漂移与缺少参与者。Python normalizer 独立拒绝把结构候选升级为原版条件或实际条款。

## 固定输入与下一次外置 attempt

七件必须重新核对的精确字节是：source save `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9`、driver `F31460BAA126BAED289CBA20A6FEFF59AAF6EF87BA3B29943C892236B6D15069`、family sidecar `12D7B2B006E409DB69F7F442107B01B5D38D8C589A7F494B24519094024B5724`、source DLL `8C3A9523D14DEDB6C44AC04F748BFC9D086E983B2A973A956CBADD21F07A8A5C`、v5 candidate DLL `19C53611AEA499A37CF222A48A5395EC7B5BBA306ABC6065AB73C097CC85FB2B`、injector `C89F1A919514A7E664AEE8FAF165B78C693ABA4EA2105289BDA2DB4BAC6A84FF`、CK3 EXE `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。原版 `00_war_values.txt` 另须 SHA `ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B`。前四件在 `D:/ck3-research-artifacts/war31-h2743-20260928/source-verified-01/`；v5 DLL 在同根 `build-war-storage-candidate-002/xar_ck3_bridge.dll`。旧 v3/v4 DLL 和所有旧 attempt 不改。

无屏幕静态核验必须用已验证的 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 执行当前工作树的 `run_h2743_dejure_readonly_v3.py --candidate war-storage-candidate-v5 --check-static`。裸 `python` 首试因缺少 `mcp` 依赖停止，环境 RED 保留于外置 `war-storage-v5-static-001/`；指定解释器重试 GREEN，`war-storage-v5-static-002/check-static.json` SHA-256 `CDC83573D8631EF51246394D231220644F2A8F59C957A82CA371CCDD5D51F663`。新 DLL 的 MSVC/Ninja Release 构建与 CTest 1/1 GREEN 回执在外置 `build-war-storage-candidate-002/receipt.json`。新的 `attempt-13-dejure-baseline-no-launch` 只能在上一个屏幕任务完成受管清理并实际释放后创建：先领取 `ck3-screen:acquired`，确认 CK3／FFmpeg／OBS 均无进程，再取得当次新鲜 Steam 离线原图并人工审阅；随后以同一 `--candidate`、新 task ID、`--prepare-no-launch --attempt-name attempt-13-dejure-baseline-no-launch --task-id <已领取任务>` 执行 profile prepare、精确原件放置、rebind 和官方 preflight。所有步骤追加新文件与回执；任一门 RED 则保留该 attempt 并清场，不修改旧证据。

只有上述门全部 GREEN 且屏幕仍独占时才可用同一候选的 `--run --prepared-attempt <新 attempt> --steam-gate <新鲜门回执> --task-id <同一任务>` 读取双次 V1 baseline 与同帧 `query-war-termination-options-16777231`。受管退出、PID 清空、loaded module 路径及磁盘 SHA、七件原件/放置件后置哈希必须通过，才生成成功结果。只读查询不会提交投降；本页不能作为正式退出授权。
