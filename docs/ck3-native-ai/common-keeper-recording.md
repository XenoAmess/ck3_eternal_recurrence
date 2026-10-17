# 共用 screen keeper 的有界录制

公共 allocate 可选择在原有 keeper 进程中挂载录制请求线程。录制器直接使用该 keeper 实例的 `process_create_gate()`，并接入同一个 `on_abort`；请求方不新建 keeper、租约或游戏进程。省略 `allocation.recording` 时沿用原有启动参数。

运行时清单增加 `allocation.recording`，仅含 `config` 和 `service` 两个精确文件 pin（`path`、`bytes`、`sha256`）。`service` 必须是选中 keeper 同目录的 `ck3_mod_acceptance_recorder.py`。配置文件 schema 为 `ck3-mod-acceptance-recording-config-v1`，完整字段为：

```json
{
  "schema": "ck3-mod-acceptance-recording-config-v1",
  "machine_id": "<当前执行机器 ID>",
  "capture_root": "<本任务获准的外置原片根目录>",
  "ffmpeg": {"path": "<编码器>", "bytes": 0, "sha256": "<实际摘要>"},
  "ffprobe": {"path": "<探测器>", "bytes": 0, "sha256": "<实际摘要>"},
  "recorder_job": {"path": "<repo>/promo/ck3_native_war_ai/integration/recorder_job.py", "bytes": 0, "sha256": "<实际摘要>"},
  "storage_reservation": {"path": "<本任务统一容量准入回执>", "bytes": 0, "sha256": "<实际摘要>"},
  "reservation_task": "<回执中唯一的录制任务名>",
  "max_seconds": 120,
  "peak_bytes": 536870912,
  "required_size": [2560, 1440]
}
```

示例 pin 中的零和占位符不能直接执行，必须由当前机器实际文件生成。将 RecorderJob、请求 CLI、FFmpeg、FFprobe、容量回执的精确 pin 加入已有 `allocator_overlay`；config/service 由 allocate 自动加入冻结输入。所有原有运行时 pin 同步更新后，再从正常 public prepare/allocate/run 流程开始，不能向已冻结的运行临时注入模块。

keeper 就绪后只启动被动请求线程；common host 实际进入 `hold` 且仍存活后，才接受以下显式调用。每次调用使用全新 `--id`，`--keeper-root` 和 `--live` 必须来自同一次真实分配。

```text
python tools/ck3_mod_acceptance_recorder_request.py --keeper-root <keeper目录> --live <live目录> --id take01-start --operation start --capture-name take01
python tools/ck3_mod_acceptance_recorder_request.py --keeper-root <keeper目录> --live <live目录> --id take01-status --operation status
python tools/ck3_mod_acceptance_recorder_request.py --keeper-root <keeper目录> --live <live目录> --id take01-prestate --operation mark --label prestate --native-receipt <本live内的原生回执>
python tools/ck3_mod_acceptance_recorder_request.py --keeper-root <keeper目录> --live <live目录> --id take01-finish --operation finish --timeout 120
python tools/ck3_mod_acceptance_recorder_request.py --keeper-root <keeper目录> --live <live目录> --id take02-start --operation start --capture-name take02
python tools/ck3_mod_acceptance_recorder_request.py --keeper-root <keeper目录> --live <live目录> --id take02-abort --operation abort --timeout 120
```

增加 `--plan-only` 只输出请求，不写 mailbox、不录屏。生产请求按文件名最多消费一次；调用超时为结果未知，应读取既有响应及终态，不能重发同一动作。响应的 `CALL_COMPLETED_ACK_NOT_CLEAN` 只表示请求已完成，不能作为 clean 或业务通过。

原片为桌面 GDI、30 fps、H.264、无游戏声音。开始前要求 GDI 与 pyautogui 的真实屏幕尺寸都等于配置值；FFmpeg 通过已有 RecorderJob 挂入 kill-on-close Job。每条有时长和字节上限。上一条实际 finish/abort 且 `job_active_processes == 0` 后，同一 keeper 可用全新 `capture_name` 继续拍摄；活动重叠、已消费名称和既有目录均拒绝。所有留存 take 的实际字节加新条预留不得超出配置指向的统一 root reservation。

每条目录保留启动意图、Job 原始终态、FFmpeg 日志、原片、mark 和终态回执。mark 绑定 UTC、monotonic 与原生回执 SHA，其相对时间从进程创建意图起算，不能直接冒称精确首帧 PTS。lease abort 和正常 keeper 停止都先停止录制并证明 Job 树为空；未证明的原片保留 RED。有效剪辑仍需原片时码、逐段画面核验和业务的前态、合法性、单次提交、ACK、独立后态证据。

```text
python -B -X utf8 tests/test_mod_acceptance_recorder.py
```

该测试使用临时目录、假的 keeper/recorder，不创建屏幕 owner、FFmpeg 或游戏。它验证同实例绑定、活动拒重叠、finish/abort 后顺序拍摄、目录不覆盖、请求不重放、未证明 Job 拒绝、root reservation 上限，以及默认/可选启动参数。它不构成本机实录验收；实录回执另记当前 machine_id、UTC 和来源。
