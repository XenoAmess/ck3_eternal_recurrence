# 战争影片窗口采集：2026-09-23 实测与复用方式

本机优先使用 **FFmpeg 9.0.1 `gfxcapture` 指定实际 CK3 HWND → hwdownload → libx264 ultrafast**，
配合 `-fps_mode passthrough -enc_time_base filter` 保留真实变帧率时间戳。
本轮只是加载画面的环境测试：抽帧可见 CK3“启动游戏中……”，并与录制开始时的桌面截图一致。
没有 HUD/gameplay clean span、自然 AI 行为证据或人工 1× 签核。

## 本轮两个有界配置

全部证据在 `D:/workspace/ck3_war_film_research_20260923/`，不覆盖旧 attempt。
两次均指定采集 12 秒、墙钟最多 35 秒，实际各约 13 秒正常结束；没有并行 recorder，没有启动或控制游戏窗口。

| 目录 | 实际输出 | PTS/内容 | 结论 |
| --- | --- | --- | --- |
| `gfxcapture-monitor-probe-r1` | 2560×1440，11.966 秒，323 帧，28,785 bytes | 相邻间隔 0–67 ms；5 秒抽帧全黑；当时正在启动游戏，不能单凭一帧区分窗口状态与后端原因 | 不继续复用这一显示器配置 |
| `gfxcapture-window-probe-r1` | 2560×1440，12.018 秒，448 帧，6,123,465 bytes | 实际 PTS 严格递增，间隔 15–63 ms；5.022 秒抽帧显示真实 CK3 加载画面 | 可复用的窗口采集候选，保留 VFR；仍需正式 HUD 取材 |

窗口原片 SHA256：`cba01adcce763ec1c09fc4e383c56907afc0dd4c0c526828259cfaa64d7012d8`。
对应 `command.json`、`result.json`、`probe.json`、`timing-analysis.json`、`sample-selection.json`、
`sample-5s.png`、`desktop-at-start.png`、stdio、抽帧审计与 `probe-source.py` 均保留。
总摘要为 `gfxcapture-probe-summary-20260923-r1/summary.json`。

本次实际窗口绑定于 `2026-09-22T21:48:23.490954Z`：HWND `462536`、PID `32356`，
标题 `Crusader Kings III`，窗口矩形 `[0,0,2560,1440]`。
这是该次录制的绑定，**不能跨进程重启或前端预热复用**；每次重新读取真实 HWND/PID。

## 可复用 argv 模板

使用 Python `subprocess.Popen(argv, ...)` 传列表，不经 shell 拼接。`hwnd`、`output` 与时长来自本次明确录制任务，
`output` 必须是新文件。下面保留本次实测参数；正式采集须先确认目标进程已进入所需画面。

```python
argv = [
    ffmpeg_executable,
    "-n", "-hide_banner", "-loglevel", "info",
    "-f", "lavfi", "-i",
    f"gfxcapture=hwnd={hwnd}:max_framerate=30:capture_cursor=0:display_border=0:output_fmt=bgra,"
    "hwdownload,format=bgra,format=yuv420p",
    "-t", "12", "-an", "-fps_mode", "passthrough", "-enc_time_base", "filter",
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p",
    str(output),
]
```

实测系统可执行文件为 WinGet 的 `ffmpeg-9.0.1-full_build/bin/ffmpeg.exe`，
SHA256 `57c56e369d5b4873b4d93fc1a1d833cb7cd8bc9325c14b05c34ce60b22842d8a`。
完整绝对路径见实测 `command.json`。

当前系统报告 `Setting minimum update interval unavailable, framerate may be limited`；
因此 `max_framerate=30` **不能被宣称已限制成 30 fps**。
本次窗口约 37.3 个实际解码帧/秒，但间隔可变，不是原生 CFR30。`r_frame_rate`/`avg_frame_rate` 都写 30 也不改变这个结论。
首个配置使用默认编码时基时出现重复 PTS；窗口配置的 `-enc_time_base filter` 保存输入时基，实测没有重复或倒退 PTS。

不要为满足旧导入器的 CFR 条件添加 `fps`、`-r`、`tpad`、循环或重定时去伪造原片采样。
后续成片可在单独导出阶段明确采样为 30 fps，原始证据仍保留 VFR 与实际 PTS，不能补出未发生的运动。
桌面没有变化时，捕获 API 自然返回相同图像不等于后期剪辑定格；图像内容相同本身不能判定取材失败。

## 已失败路径与当前边界

- `gpu-desktop-capture-probe-r1/r5`：DDA 捕获在约 35 秒墙钟预算内没有输出，按失败保留。
- `gpu-desktop-capture-probe-r2`：系统 FFmpeg 9 的 NVENC 要求 API 13.1，当前驱动支持 12.1，不能直接使用。
- `gpu-desktop-capture-probe-r3`：独立 FFmpeg 6.1.1 的 gdigrab + NVENC 能编码，但 12 秒仅 138 帧，约 11.5 fps。
- `gpu-desktop-capture-probe-r4`：该旧 FFmpeg 不接受尝试使用的 `dup_frames` 选项。
- `robert-input-case-r1`：旧 gdigrab 原片 120 秒仅 1,077 实际帧，元数据 30 fps 不能证明连续采集；
  对该原片的 PTS 修正和旧失败图边界见 [gameplay bundle 用法](../../promo/ck3_native_war_ai/integration/README.gameplay-bundle.md)。

这些失败不改写为成功。当前窗口方案已证明本机能取得非黑 CK3 窗口帧和完整有界 VFR 输出，
尚未证明长时间 HUD 录制、游戏运动的每帧覆盖或任何原生 AI 决策因果。
默认保持 [会话管理器](../../promo/ck3_native_war_ai/integration/README.capture-session.md) 的后台调试录像关闭，
同一时间仅运行一个正式取材 recorder。
