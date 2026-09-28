# H2743 守方 de-jure 终战只读 v3 实机运行单

状态：**静态就绪，未执行 v3 no-launch、未启动 CK3、未取得 H2743 v3 live 结果**。R0271/R0266 屏幕任务优先。此运行单只采集当前帧原生基线；没有投降或白和平提交路径。

## 冷启动与时限

R0271 R0004 本机外置报告 `D:/ck3-research-artifacts/war-r0271-replay-20260928/attempt-03/formal-run-12-01/formal-report.txt`，SHA-256 `B41F23BFD789D7D3E7D68893CEDBBFCA8B46425025BAC382B86E1F233F3B2D83`。该 run 07:10:46Z 启动，约 07:34:23Z 才执行首个原生命令，耗时 **23 分 37 秒（1417 秒）**。旧 1500 秒就绪预算只余约 83 秒。v3 设原生会话就绪等待 **1800 秒**、会话自身超时 **3000 秒**、就绪后 MCP 帧等待 **300 秒**、单次工具调用 **120 秒**、清理等待 **180 秒**。R0004 是另一个 run 的本机耗时证据，不是 H2743 v3 读数。

## 精确输入与只读界限

固定源目录 `D:/ck3-research-artifacts/war31-h2743-20260928/source-verified-01` 恰有下列四件；它们与新候选 DLL 是不同角色。`--check-static` 逐字节校验源、候选、注入器和 EXE，且不建 profile、不启动 CK3。

| 文件 | SHA-256 |
| --- | --- |
| `xar_checkpoint.ck3` | `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9` |
| `driver-state.json` | `F31460BAA126BAED289CBA20A6FEFF59AAF6EF87BA3B29943C892236B6D15069` |
| `first-heir-marriage-formal-v1.json` | `12D7B2B006E409DB69F7F442107B01B5D38D8C589A7F494B24519094024B5724` |
| 源 `xar_ck3_bridge.dll` | `8C3A9523D14DEDB6C44AC04F748BFC9D086E983B2A973A956CBADD21F07A8A5C` |
| 候选 `build-read-port-v1/Release/xar_ck3_bridge.dll` | `FD8B5C7873C22BE32ACF2E421D2A9F625AE8FF3FB4D5408DB7F6E6AF15321470` |
| `R0221-original-bridge/native/xar_ck3_bridge_injector.exe` | `C89F1A919514A7E664AEE8FAF165B78C693ABA4EA2105289BDA2DB4BAC6A84FF` |
| CK3 1.19.0.6 `binaries/ck3.exe` | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |

冻结帧：WarID `16777231`，Robert `29829` 为主守方，Landolf `30097` 为主攻方，episode `native-29829-2bc2d599f7f9`，date_raw `53217264`，战分 `-12`，目标 Title `2128`，CB `individual_county_de_jure_cb` / index `17`。仅允许 `query-defender-de-jure-exit-terms-v1-16777231` 双读与其间一次 `query-war-termination-options-16777231`；两者都是只读 `ck3_execute_step`。前后 `ck3_take_snapshot` 验证 paused 帧、WarID、双方；六字段中 `snapshot_id`、`revision`、`native_revision`、`date_raw`、`episode_run_id` 从顶层读取，`connection_generation` 严格从 `diagnostics` 读取。终战选项回执的 `active_war_signature` 必须与前态快照中的**全部**进行中战争排序签名一致，目标 WarID 恰好出现一次；后态快照也必须保持相同完整战局签名。驱动比较两次基线，在查询前回读运行中 CK3 EXE 和已装载 DLL 的实际路径与文件 SHA，不能证实时 RED。保存三次查询各自的精确 request、MCP envelope、原始 payload 与 SHA，以及进程 stdout/stderr、失败与清理收据；既有 attempt 不覆盖。

## 屏幕释放后的操作顺序

1. 本任务在任务总线上独占 `ck3-screen:acquired`；先确认别的 CK3、录制和屏幕任务已退出。R0271/R0266 占屏时连 profile 预检也不要启动。用仓库相对脚本的 `--help` / `--check-static` 只做静态检查：

   ```text
   D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_h2743_dejure_readonly_v3.py --help
   D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_h2743_dejure_readonly_v3.py --check-static
   ```

2. 选全新、未存在的 `attempt-N-dejure-baseline-no-launch`。在独占屏幕任务内运行 `--prepare-no-launch --attempt-name attempt-N-dejure-baseline-no-launch --task-id <当前独占屏幕任务ID>`。该命令再次检查独占、调用分支内 `prepare-profile`、放置精确 save/driver/family sidecar、做 ordinary seed rebind 和 native one-generation preflight；`ready-summary.json` 必须为 `no_launch_preflight_ready`。已有 RED attempt-08/09 保留，不改写也不复用。预检失败时保留新 attempt，换下一编号。
3. 取当次真实 Steam 桌面位移画面和 `steam-frame-freshness.json`，人工审阅**新图**可见“离线模式”，记录审阅人、UTC 时间与图像 SHA。旧截图、文件时间或只看服务状态均不足。将下面的 `steam-gate.json` 作为新 attempt 的人工回执，填入真实值；不得把模板当观察事实：

   ```json
   {
     "schema": "xar.ck3.h2743.steam-offline-human-gate.v3",
     "task_id": "<当前独占屏幕任务ID>",
     "reviewer": "<实际审阅人>",
     "reviewed_at_utc": "<新图人工审阅 UTC ISO 时间>",
     "screenshot_path": "<本次 steam-moved.png 绝对路径>",
     "screenshot_sha256": "<本次图像大写 SHA-256>",
     "fresh_frame_receipt_path": "<本次 steam-frame-freshness.json 绝对路径>",
     "steam_offline_visible": true
   }
   ```

   驱动验证审阅不超过 10 分钟、位移收据与图像 bytes 相同，并实时查询任务总线确认本任务是唯一 `ck3-screen:acquired` owner；人工仍须亲眼判断离线文字。若屏幕冻结或远程采集不可证，按 `desktop-steam-offline-recovery-2026-09-27.md` 获取新的恢复收据后再审阅。

4. 在同一屏幕任务内，用新 attempt 与真实 gate 运行：

   ```text
   D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_h2743_dejure_readonly_v3.py --run --prepared-attempt D:\ck3-research-artifacts\war31-h2743-20260928\attempt-N-dejure-baseline-no-launch --steam-gate D:\ck3-research-artifacts\war31-h2743-20260928\attempt-N-dejure-baseline-no-launch\steam-gate.json --task-id <当前独占屏幕任务ID>
   ```

   若任何哈希、READY、屏幕占用、新鲜画面或当前已有 CK3 进程不符，驱动在启动前拒绝。冷启动可能超过任务总线默认 15 分钟 stale 门限，驱动在等待 ready 时每 60 秒校验独占 owner 并续租；预检命令长时间运行时亦续租。live 输出固定为该 attempt 下全新的 `live-dejure-readonly-v3/`；失败保留，不重试同一输出目录。会话退出后检查 `session-exit.json`、CK3 PID 清空与原件后哈希，再释放任务总线资源。

## 读数与缺项判定

v1 native reader 预计只给双方身份、同帧目标 Title ID、**14 行当前资源余额**（双方各 7 种：gold、prestige、prestige_experience、piety、piety_experience、legitimacy、stress）和双方每月 gold income 2 行。余额与收入不是终战 signed delta；Title `2128` 的前态或目标列表也不是转移结果。两次查询必须保持 `material_complete=false`，`title_vassal_delta=null`、`signed_resource_delta=null`、`directed_truce=null`。若原生读口意外宣称 material complete，脚本拒绝该 run，不据此提交动作。

`read-only-result.json` 是**退出后**回执：只有受管 session 返回码为 0、stdout 读取线程结束、CK3 PID 清空，源四件／候选 DLL／注入器／CK3 EXE／已放置 save 与 sidecar 的后哈希均匹配，且运行中 module-map 路径与当前磁盘 SHA audit 已生成时才创建，并绑定 `session-exit.json` SHA。该 audit 不读取或证明进程内存映像 bytes。查询成功但清理失败会留下原始查询和 `cleanup-red.json`，不会生成最终结果；运维需处理遗留进程，不能把查询 payload 单独升级为本轮 GREEN。普通查询失败留下 `failure.json`；每次失败仍保留该 attempt 全部已写文件。

终战选项的直接只读查询仅补合法性观察，不含正式规划器的 `selected_step` 与 typed `priced_command`；不能据此向 R0266 填即时费用 0。完整比较仍需同一 native revision 绑定的：运行时 `scope:target` referent；`setup_de_jure_cb` 的 F 原始数值与倍率；`resolve_title_and_vassal_change` 的 Title holder、title liege、character liege、claim 完整 before→after 操作；双方 7 种资源的 **14 行有符号终战 delta** 与条件效果覆盖；单向停战 owner/toward、期限和结束日期；候选 surrender 按钮当前合法且对方接受；以及给定时域内战分、资源、领土与 R0271 围城参与者的续战风险界。任何一项缺失、同帧身份漂移或不同 WarID 均由比较合同返回 `unavailable` / `action_literal=null`。即使将来可逐项比较，效用排序、风险阈值和精确 checkpoint 退出授权仍需单独合同与新鲜原生重验。本 v3 不调用已发生崩溃的广义 loaded-effect preview，也不调用 `surrender-war-*` 或 `offer-white-peace-*`。
