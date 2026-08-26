[CmdletBinding()]
param(
    [string]$OutputDirectory,
    [int]$TitleSeconds = 6,
    [int]$ResultSeconds = 12
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class XarDemoWindowApi {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

function Join-NativeArguments {
    param([string[]]$Values)

    return (($Values | ForEach-Object {
        '"' + $_.Replace('"', '\"') + '"'
    }) -join ' ')
}

function Start-HiddenProcess {
    param(
        [string]$FileName,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [switch]$RedirectInput,
        [switch]$RedirectOutput,
        [hashtable]$Environment
    )

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FileName
    $startInfo.Arguments = Join-NativeArguments $Arguments
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardInput = [bool]$RedirectInput
    $startInfo.RedirectStandardOutput = [bool]$RedirectOutput
    $startInfo.RedirectStandardError = [bool]$RedirectOutput
    if ($Environment) {
        foreach ($key in $Environment.Keys) {
            $startInfo.EnvironmentVariables[[string]$key] = [string]$Environment[$key]
        }
    }
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        throw "Failed to start $FileName"
    }
    return $process
}

function Pump-Ui {
    param([int]$Milliseconds)

    $deadline = [DateTime]::UtcNow.AddMilliseconds($Milliseconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 40
    }
}

function New-DemoCard {
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $form = New-Object System.Windows.Forms.Form
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
    $form.Bounds = $screen
    $form.BackColor = [System.Drawing.Color]::FromArgb(12, 16, 28)
    $form.ShowInTaskbar = $false
    $form.TopMost = $true

    $accent = New-Object System.Windows.Forms.Panel
    $accent.Location = New-Object System.Drawing.Point(176, 182)
    $accent.Size = New-Object System.Drawing.Size(($screen.Width - 352), 12)
    $accent.BackColor = [System.Drawing.Color]::FromArgb(218, 170, 74)
    $form.Controls.Add($accent)

    $eyebrow = New-Object System.Windows.Forms.Label
    $eyebrow.Location = New-Object System.Drawing.Point(176, 115)
    $eyebrow.Size = New-Object System.Drawing.Size(($screen.Width - 352), 50)
    $eyebrow.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 22)
    $eyebrow.ForeColor = [System.Drawing.Color]::FromArgb(218, 170, 74)
    $eyebrow.Text = "XAR / EXACT-BUILD NATIVE BRIDGE"
    $form.Controls.Add($eyebrow)

    $title = New-Object System.Windows.Forms.Label
    $title.Location = New-Object System.Drawing.Point(170, 225)
    $title.Size = New-Object System.Drawing.Size(($screen.Width - 340), 115)
    $title.Font = New-Object System.Drawing.Font("Segoe UI", 50, [System.Drawing.FontStyle]::Bold)
    $title.ForeColor = [System.Drawing.Color]::White
    $form.Controls.Add($title)

    $chineseTitle = New-Object System.Windows.Forms.Label
    $chineseTitle.Location = New-Object System.Drawing.Point(178, 345)
    $chineseTitle.Size = New-Object System.Drawing.Size(($screen.Width - 356), 62)
    $chineseTitle.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 27)
    $chineseTitle.ForeColor = [System.Drawing.Color]::FromArgb(202, 210, 224)
    $form.Controls.Add($chineseTitle)

    $subtitle = New-Object System.Windows.Forms.Label
    $subtitle.Location = New-Object System.Drawing.Point(178, 435)
    $subtitle.Size = New-Object System.Drawing.Size(($screen.Width - 356), 66)
    $subtitle.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 27)
    $subtitle.ForeColor = [System.Drawing.Color]::FromArgb(156, 201, 255)
    $form.Controls.Add($subtitle)

    $body = New-Object System.Windows.Forms.Label
    $body.Location = New-Object System.Drawing.Point(182, 555)
    $body.Size = New-Object System.Drawing.Size(1040, 500)
    $body.Font = New-Object System.Drawing.Font("Consolas", 22)
    $body.ForeColor = [System.Drawing.Color]::FromArgb(222, 228, 239)
    $form.Controls.Add($body)

    $divider = New-Object System.Windows.Forms.Panel
    $divider.Location = New-Object System.Drawing.Point(1268, 555)
    $divider.Size = New-Object System.Drawing.Size(2, 500)
    $divider.BackColor = [System.Drawing.Color]::FromArgb(65, 78, 104)
    $form.Controls.Add($divider)

    $chineseBody = New-Object System.Windows.Forms.Label
    $chineseBody.Location = New-Object System.Drawing.Point(1330, 555)
    $chineseBody.Size = New-Object System.Drawing.Size(1040, 500)
    $chineseBody.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 22)
    $chineseBody.ForeColor = [System.Drawing.Color]::FromArgb(188, 204, 229)
    $form.Controls.Add($chineseBody)

    $footer = New-Object System.Windows.Forms.Label
    $footer.Location = New-Object System.Drawing.Point(182, ($screen.Height - 150))
    $footer.Size = New-Object System.Drawing.Size(($screen.Width - 364), 55)
    $footer.Font = New-Object System.Drawing.Font("Segoe UI", 18)
    $footer.ForeColor = [System.Drawing.Color]::FromArgb(132, 144, 166)
    $footer.Text = "CK3 1.19.0.6 | no OCR | no mouse | no foreground-window dependency  /  无 OCR、无鼠标、无前台窗口依赖"
    $form.Controls.Add($footer)

    return [pscustomobject]@{
        Form = $form
        Accent = $accent
        Title = $title
        ChineseTitle = $chineseTitle
        Subtitle = $subtitle
        Body = $body
        ChineseBody = $chineseBody
    }
}

function Show-DemoCard {
    param(
        [pscustomobject]$Card,
        [string]$Title,
        [string]$ChineseTitle,
        [string]$Subtitle,
        [string]$Body,
        [string]$ChineseBody,
        [System.Drawing.Color]$Accent
    )

    $Card.Title.Text = $Title
    $Card.ChineseTitle.Text = $ChineseTitle
    $Card.Subtitle.Text = $Subtitle
    $Card.Body.Text = $Body
    $Card.ChineseBody.Text = $ChineseBody
    $Card.Accent.BackColor = $Accent
    $Card.Form.TopMost = $true
    if (-not $Card.Form.Visible) {
        $Card.Form.Show()
    }
    $Card.Form.Bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $Card.Form.BringToFront()
    $Card.Form.Activate()
    [System.Windows.Forms.Application]::DoEvents()
}

function New-GameplayCaption {
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $form = New-Object System.Windows.Forms.Form
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
    $form.Bounds = New-Object System.Drawing.Rectangle(260, ($screen.Height - 220), ($screen.Width - 520), 165)
    $form.BackColor = [System.Drawing.Color]::FromArgb(12, 16, 28)
    $form.Opacity = 0.88
    $form.ShowInTaskbar = $false
    $form.TopMost = $true

    $english = New-Object System.Windows.Forms.Label
    $english.Location = New-Object System.Drawing.Point(30, 18)
    $english.Size = New-Object System.Drawing.Size(($form.Width - 60), 52)
    $english.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 22)
    $english.ForeColor = [System.Drawing.Color]::White
    $english.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
    $form.Controls.Add($english)

    $chinese = New-Object System.Windows.Forms.Label
    $chinese.Location = New-Object System.Drawing.Point(30, 72)
    $chinese.Size = New-Object System.Drawing.Size(($form.Width - 60), 48)
    $chinese.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 19)
    $chinese.ForeColor = [System.Drawing.Color]::FromArgb(156, 201, 255)
    $chinese.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
    $form.Controls.Add($chinese)

    $boundary = New-Object System.Windows.Forms.Label
    $boundary.Location = New-Object System.Drawing.Point(30, 126)
    $boundary.Size = New-Object System.Drawing.Size(($form.Width - 60), 28)
    $boundary.Font = New-Object System.Drawing.Font("Segoe UI", 12)
    $boundary.ForeColor = [System.Drawing.Color]::FromArgb(218, 170, 74)
    $boundary.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
    $boundary.Text = "READ-ONLY NATIVE QUERY / NO EVENT OPTION IS SELECTED  |  只读原生查询 / 不选择任何事件选项"
    $form.Controls.Add($boundary)

    return [pscustomobject]@{
        Form = $form
        English = $english
        Chinese = $chinese
    }
}

function Show-GameplayCaption {
    param(
        [pscustomobject]$Caption,
        [string]$English,
        [string]$Chinese
    )

    $Caption.English.Text = $English
    $Caption.Chinese.Text = $Chinese
    $Caption.Form.TopMost = $true
    if (-not $Caption.Form.Visible) {
        $Caption.Form.Show()
    }
    $Caption.Form.BringToFront()
    [System.Windows.Forms.Application]::DoEvents()
}

function Hide-GameplayCaption {
    param([pscustomobject]$Caption)

    if ($Caption.Form.Visible) {
        $Caption.Form.Hide()
        [System.Windows.Forms.Application]::DoEvents()
    }
}

function Hide-DemoCard {
    param([pscustomobject]$Card)

    if ($Card.Form.Visible) {
        $Card.Form.TopMost = $false
        $Card.Form.Hide()
        [System.Windows.Forms.Application]::DoEvents()
    }
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$today = Get-Date -Format "yyyy-MM-dd"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $repositoryRoot "artifacts\demos\$today"
}
$outputRoot = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($outputRoot) | Out-Null

$rawVideo = Join-Path $outputRoot "ck3-autonomous-agent-event-window-bilingual-$stamp.raw.mkv"
$finalVideo = Join-Path $outputRoot "ck3-autonomous-agent-event-window-bilingual-$stamp.mp4"
$artifactPath = Join-Path $outputRoot "ck3-event-window-live-$stamp.json"
$runnerStdoutPath = Join-Path $outputRoot "ck3-event-window-live-$stamp.stdout.txt"
$runnerStderrPath = Join-Path $outputRoot "ck3-event-window-live-$stamp.stderr.txt"
$metadataPath = Join-Path $outputRoot "ck3-autonomous-agent-event-window-bilingual-$stamp.video.json"

$ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
$ffprobe = Join-Path (Split-Path $ffmpeg -Parent) "ffprobe.exe"
$python = Join-Path $repositoryRoot "tools\.venv\Scripts\python.exe"
$runner = Join-Path $repositoryRoot "ck3_autonomous_player\native_bridge\research\run_current_event_window_context_live_acceptance.py"
$gameDirectory = Join-Path $repositoryRoot "Crusader Kings III"
$bridgeDirectory = Join-Path $repositoryRoot "ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2"
$bridgeDll = Join-Path $bridgeDirectory "xar_ck3_bridge.dll"
$bridgeInjector = Join-Path $bridgeDirectory "xar_ck3_bridge_injector.exe"
$isolatedSource = Join-Path $env:TEMP "xar-event-window-cea30a0-source"
$expectedDllSha256 = "52398435F8AA5177D6D507BFAA38CD2578EB988F0629F1C5E13360CC91FB3BB0"
$pipeName = "\\.\pipe\xar-event-window-video-$stamp"

foreach ($required in @($ffmpeg, $ffprobe, $python, $runner, $bridgeDll, $bridgeInjector, $isolatedSource)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required demo input is missing: $required"
    }
}
if (Get-Process -Name ck3 -ErrorAction SilentlyContinue) {
    throw "Refusing to record while ck3.exe is already running"
}

$obsWindows = @(
    Get-Process -Name obs64 -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } |
        ForEach-Object { $_.MainWindowHandle }
)
foreach ($handle in $obsWindows) {
    [XarDemoWindowApi]::ShowWindow($handle, 6) | Out-Null
}

$gold = [System.Drawing.Color]::FromArgb(218, 170, 74)
$green = [System.Drawing.Color]::FromArgb(55, 205, 126)
$red = [System.Drawing.Color]::FromArgb(235, 84, 92)
$card = New-DemoCard
$caption = New-GameplayCaption
$capture = $null
$runnerProcess = $null
$exitCode = 1

try {
    Show-DemoCard -Card $card `
        -Title "CK3 AUTONOMOUS AGENT" `
        -ChineseTitle "CK3 自动游玩智能体" `
        -Subtitle "LIVE EVENT OBSERVATION / CHECKPOINT RECOVERY" `
        -Body ("OBSERVE current native event window`r`n" +
               "-> read materialized options and authored indices`r`n" +
               "-> save an exact checkpoint without selecting`r`n" +
               "-> launch a fresh CK3 process`r`n" +
               "-> recover and verify the same event again") `
        -ChineseBody ("观察当前原生事件窗口`r`n" +
                      "→ 读取真实物化选项与 authored index`r`n" +
                      "→ 不选择任何选项，保存精确检查点`r`n" +
                      "→ 启动全新的 CK3 进程`r`n" +
                      "→ 冷恢复后再次验证同一事件") `
        -Accent $gold

    $capture = Start-HiddenProcess -FileName $ffmpeg -WorkingDirectory $repositoryRoot -RedirectInput -Arguments @(
        "-hide_banner", "-loglevel", "warning",
        "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "0",
        "-video_size", "2560x1440", "-i", "desktop",
        "-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq",
        "-rc", "vbr", "-cq", "22", "-b:v", "0",
        "-pix_fmt", "yuv420p", "-y", $rawVideo
    )
    Pump-Ui 1200
    Pump-Ui ($TitleSeconds * 1000)

    Show-DemoCard -Card $card `
        -Title "STAGE 1 / 2" `
        -ChineseTitle "阶段 1 / 2：种子进程原生观察" `
        -Subtitle "SEED PROCESS: OBSERVE -> QUERY -> SAVE" `
        -Body ("Launching exact CK3 executable...`r`n`r`n" +
               "The agent will materialize a deterministic nonreligious event,`r`n" +
               "read it through the production native bridge while paused,`r`n" +
               "and save without selecting any option.") `
        -ChineseBody ("正在启动 exact-build CK3……`r`n`r`n" +
                      "智能体会物化一个确定性的非宗教事件，`r`n" +
                      "在暂停状态通过生产原生桥读取，`r`n" +
                      "随后保存，但绝不选择任何选项。") `
        -Accent $gold

    $runnerProcess = Start-HiddenProcess -FileName $python -WorkingDirectory $repositoryRoot -RedirectOutput -Environment @{
        XAR_EVENT_WINDOW_ISOLATED_SOURCE_ROOT = $isolatedSource
    } -Arguments @(
        $runner,
        "--game-dir", $gameDirectory,
        "--bridge-pipe", $pipeName,
        "--bridge-dll", $bridgeDll,
        "--expected-bridge-dll-sha256", $expectedDllSha256,
        "--bridge-injector", $bridgeInjector,
        "--output", $artifactPath
    )

    $seenCk3Pids = New-Object 'System.Collections.Generic.HashSet[int]'
    $visualState = "stage-1-card"
    while (-not $runnerProcess.HasExited) {
        $ck3Rows = @(Get-Process -Name ck3 -ErrorAction SilentlyContinue)
        foreach ($row in $ck3Rows) {
            $seenCk3Pids.Add([int]$row.Id) | Out-Null
        }
        if ($ck3Rows.Count -gt 0) {
            if ($visualState -ne "game") {
                Hide-DemoCard $card
                if ($seenCk3Pids.Count -eq 1) {
                    Show-GameplayCaption -Caption $caption `
                        -English "SEED PROCESS: native event observation and checkpoint save" `
                        -Chinese "种子进程：原生事件观察并保存检查点"
                }
                else {
                    Show-GameplayCaption -Caption $caption `
                        -English "FRESH PROCESS: cold recovery and repeat native verification" `
                        -Chinese "全新进程：冷恢复并重复进行原生验证"
                }
                $visualState = "game"
            }
        }
        elseif ($seenCk3Pids.Count -eq 1 -and $visualState -ne "checkpoint") {
            Hide-GameplayCaption $caption
            Show-DemoCard -Card $card `
                -Title "CHECKPOINT SAVED" `
                -ChineseTitle "检查点已保存：第一 CK3 进程已干净关闭" `
                -Subtitle "FIRST CK3 PROCESS CLEANLY CLOSED" `
                -Body ("The event window was read through native memory.`r`n" +
                       "No OCR. No mouse. No option selection.`r`n`r`n" +
                       "Now cloning the saved checkpoint and launching`r`n" +
                       "a distinct, fresh CK3 process for cold recovery...") `
                -ChineseBody ("事件窗口已直接从 CK3 原生内存读取。`r`n" +
                              "无 OCR、无鼠标、无选项选择。`r`n`r`n" +
                              "现在复制检查点并启动另一个全新 CK3 进程，`r`n" +
                              "执行真正的冷恢复验证……") `
                -Accent $gold
            $visualState = "checkpoint"
        }
        elseif ($seenCk3Pids.Count -ge 2 -and $visualState -ne "finalizing") {
            Hide-GameplayCaption $caption
            Show-DemoCard -Card $card `
                -Title "VERIFYING NATIVE EVIDENCE" `
                -ChineseTitle "正在核验原生证据" `
                -Subtitle "FRESH-COLD PROCESS COMPLETED" `
                -Body "Binding event identity, options, checkpoint bytes, process IDs and cleanup..." `
                -ChineseBody "正在绑定事件身份、选项、检查点字节、进程 ID 与清理结果……" `
                -Accent $gold
            $visualState = "finalizing"
        }
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 100
    }

    $runnerStdout = $runnerProcess.StandardOutput.ReadToEnd()
    $runnerStderr = $runnerProcess.StandardError.ReadToEnd()
    [System.IO.File]::WriteAllText($runnerStdoutPath, $runnerStdout, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText($runnerStderrPath, $runnerStderr, [System.Text.UTF8Encoding]::new($false))

    if (-not (Test-Path -LiteralPath $artifactPath)) {
        throw "Live acceptance did not write its artifact (exit $($runnerProcess.ExitCode))"
    }
    $result = Get-Content -LiteralPath $artifactPath -Raw | ConvertFrom-Json
    $cross = $result.cross_stage_proof
    $frame = $result.cold_stage.sequence.first_query.current_event_window_context
    $indices = (@($frame.options | ForEach-Object { $_.native_option_index }) -join ", ")
    $cancelIndices = (@($frame.options | Where-Object { $_.cancel } | ForEach-Object { $_.native_option_index }) -join ", ")
    $doubleQuery = [bool]$result.cold_stage.sequence.checks.adjacent_context_frames_strictly_equal
    $cleanupGreen = [bool]$result.disposable_cleanup.ok -and [bool]$result.no_ck3_processes_after

    if ([bool]$result.ok -and $runnerProcess.ExitCode -eq 0) {
        $exitCode = 0
        Show-DemoCard -Card $card `
            -Title "LIVE ACCEPTANCE: GREEN" `
            -ChineseTitle "实机验收：GREEN / 通过" `
            -Subtitle "OBSERVE -> CHECKPOINT -> FRESH PROCESS -> VERIFY" `
            -Body ("event instance     : $($cross.current_event_instance_id)`r`n" +
                   "definition key     : $($cross.event_definition_key)`r`n" +
                   "native option index: [$indices]  (cancel: [$cancelIndices])`r`n" +
                   "process IDs        : $($cross.seed_bridge_pid) -> $($cross.cold_bridge_pid)`r`n" +
                   "cold double query  : identical = $doubleQuery`r`n" +
                   "source unchanged   : $($result.source_save_invariant.unchanged)`r`n" +
                   "managed cleanup    : $cleanupGreen") `
            -ChineseBody ("事件实例          ：$($cross.current_event_instance_id)`r`n" +
                          "定义 key           ：$($cross.event_definition_key)`r`n" +
                          "原生选项索引       ：[$indices]（取消：[$cancelIndices]）`r`n" +
                          "种子/冷启动 PID    ：$($cross.seed_bridge_pid) → $($cross.cold_bridge_pid)`r`n" +
                          "冷启动双查询一致   ：$doubleQuery`r`n" +
                          "源存档保持不变     ：$($result.source_save_invariant.unchanged)`r`n" +
                          "托管清理完成       ：$cleanupGreen") `
            -Accent $green
    }
    else {
        Show-DemoCard -Card $card `
            -Title "LIVE ACCEPTANCE: RED" `
            -ChineseTitle "实机验收：RED / 未通过" `
            -Subtitle "EVIDENCE DID NOT QUALIFY" `
            -Body ("runner exit: $($runnerProcess.ExitCode)`r`nerror: $($result.error)") `
            -ChineseBody ("runner 退出码：$($runnerProcess.ExitCode)`r`n错误：$($result.error)") `
            -Accent $red
    }
    Pump-Ui ($ResultSeconds * 1000)
}
catch {
    Show-DemoCard -Card $card `
        -Title "DEMO RECORDING FAILED" `
        -ChineseTitle "演示录制失败" `
        -Subtitle "THE VIDEO IS NOT QUALIFIED" `
        -Body $_.Exception.Message `
        -ChineseBody "该视频不能作为日报演示交付。" `
        -Accent $red
    Pump-Ui 8000
    throw
}
finally {
    if ($runnerProcess -and -not $runnerProcess.HasExited) {
        $runnerProcess.Kill()
        $runnerProcess.WaitForExit()
    }
    if ($capture -and -not $capture.HasExited) {
        try {
            $capture.StandardInput.WriteLine("q")
            $capture.StandardInput.Flush()
            $capture.StandardInput.Close()
            if (-not $capture.WaitForExit(20000)) {
                $capture.Kill()
                $capture.WaitForExit()
            }
        }
        catch {
            if (-not $capture.HasExited) {
                $capture.Kill()
                $capture.WaitForExit()
            }
        }
    }
    if ($card -and $card.Form) {
        $card.Form.Close()
        $card.Form.Dispose()
    }
    if ($caption -and $caption.Form) {
        $caption.Form.Close()
        $caption.Form.Dispose()
    }
    foreach ($handle in $obsWindows) {
        [XarDemoWindowApi]::ShowWindow($handle, 9) | Out-Null
    }
}

if ($exitCode -ne 0) {
    throw "Live acceptance was RED; raw recording retained at $rawVideo"
}
if (-not (Test-Path -LiteralPath $rawVideo)) {
    throw "FFmpeg did not produce the raw recording"
}

$mux = Start-HiddenProcess -FileName $ffmpeg -WorkingDirectory $repositoryRoot -RedirectOutput -Arguments @(
    "-hide_banner", "-loglevel", "warning",
    "-i", $rawVideo,
    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
    "-map", "0:v:0", "-map", "1:a:0", "-shortest",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "96k",
    "-movflags", "+faststart",
    "-metadata", "title=CK3 Autonomous Agent - Bilingual Native Event Window Live Demo",
    "-y", $finalVideo
)
$muxStdout = $mux.StandardOutput.ReadToEnd()
$muxStderr = $mux.StandardError.ReadToEnd()
$mux.WaitForExit()
if ($mux.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $finalVideo)) {
    throw "MP4 mux failed (exit $($mux.ExitCode)): $muxStderr"
}

$durationText = & $ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $finalVideo
$duration = [double]::Parse(($durationText | Select-Object -First 1), [System.Globalization.CultureInfo]::InvariantCulture)
$videoFile = Get-Item -LiteralPath $finalVideo
if ($videoFile.Length -lt 1MB -or $duration -lt 60.0) {
    throw "Final video sanity check failed: bytes=$($videoFile.Length), duration=$duration"
}
$videoHash = (Get-FileHash -LiteralPath $finalVideo -Algorithm SHA256).Hash
$artifactHash = (Get-FileHash -LiteralPath $artifactPath -Algorithm SHA256).Hash
$artifact = Get-Content -LiteralPath $artifactPath -Raw | ConvertFrom-Json
$metadata = [ordered]@{
    format_version = 1
    kind = "ck3_autonomous_agent_daily_showoff_video"
    language = [ordered]@{
        primary = "English"
        secondary = "Simplified Chinese subtitles"
        gameplay_lower_thirds_bilingual = $true
        evidence_card_bilingual = $true
    }
    date = $today
    video = [ordered]@{
        path = $finalVideo
        bytes = $videoFile.Length
        sha256 = $videoHash
        duration_seconds = [Math]::Round($duration, 3)
        width = 2560
        height = 1440
        frame_rate = 30
        codec = "H.264"
        audio = "silent AAC stereo"
    }
    live_acceptance = [ordered]@{
        path = $artifactPath
        sha256 = $artifactHash
        ok = [bool]$artifact.ok
        evidence_classification = $artifact.evidence_classification
        event_instance_id = $artifact.cross_stage_proof.current_event_instance_id
        event_definition_key = $artifact.cross_stage_proof.event_definition_key
        seed_pid = $artifact.cross_stage_proof.seed_bridge_pid
        cold_pid = $artifact.cross_stage_proof.cold_bridge_pid
        no_ck3_processes_after = [bool]$artifact.no_ck3_processes_after
    }
}
[System.IO.File]::WriteAllText(
    $metadataPath,
    (($metadata | ConvertTo-Json -Depth 8) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
)

Remove-Item -LiteralPath $rawVideo -Force

[pscustomobject]@{
    ok = $true
    video = $finalVideo
    metadata = $metadataPath
    live_artifact = $artifactPath
    duration_seconds = [Math]::Round($duration, 3)
    bytes = $videoFile.Length
    sha256 = $videoHash
}
