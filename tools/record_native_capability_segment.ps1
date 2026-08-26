[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')]
    [string]$SegmentId,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$EnglishTitle,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ChineseTitle,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$StatusBadge,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$BoundaryText,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Runner,

    [Parameter(Mandatory = $true)]
    [AllowEmptyCollection()]
    [string[]]$RunnerArguments,

    [System.Collections.IDictionary]$Environment = @{},

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$titleMilliseconds = 5000
$resultMilliseconds = 10000
$cleanupTimeoutSeconds = 25
$captureWidth = 2560
$captureHeight = 1440
$captureFrameRate = 30

if ($env:OS -ne "Windows_NT") {
    throw "Native capability recording requires Windows."
}

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Web.Extensions
if (-not ("XarNativeSegmentWindowApi" -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class XarNativeSegmentWindowApi {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool BringWindowToTop(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool SetWindowPos(
        IntPtr hWnd,
        IntPtr hWndInsertAfter,
        int X,
        int Y,
        int cx,
        int cy,
        uint uFlags
    );
}
"@
}

function ConvertTo-WindowsCommandLineArgument {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Value
    )

    if ($Value.IndexOf([char]0) -ge 0) {
        throw "A native argument contains a NUL character."
    }
    if ($Value.Length -eq 0) {
        return '""'
    }
    if ($Value -notmatch '[\s"]') {
        return $Value
    }

    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $backslashCount = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq [char]92) {
            $backslashCount += 1
            continue
        }
        if ($character -eq [char]34) {
            if ($backslashCount -gt 0) {
                [void]$builder.Append(('\' * ($backslashCount * 2)))
            }
            [void]$builder.Append('\')
            [void]$builder.Append('"')
            $backslashCount = 0
            continue
        }
        if ($backslashCount -gt 0) {
            [void]$builder.Append(('\' * $backslashCount))
            $backslashCount = 0
        }
        [void]$builder.Append($character)
    }
    if ($backslashCount -gt 0) {
        [void]$builder.Append(('\' * ($backslashCount * 2)))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Join-NativeArgumentArray {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [string[]]$Values
    )

    return ((@($Values) | ForEach-Object {
        ConvertTo-WindowsCommandLineArgument -Value $_
    }) -join ' ')
}

function Start-ArrayProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FileName,
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [switch]$RedirectInput,
        [switch]$CaptureOutput,
        [System.Collections.IDictionary]$ChildEnvironment
    )

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FileName
    $startInfo.Arguments = Join-NativeArgumentArray -Values $Arguments
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $startInfo.RedirectStandardInput = [bool]$RedirectInput
    $startInfo.RedirectStandardOutput = [bool]$CaptureOutput
    $startInfo.RedirectStandardError = [bool]$CaptureOutput
    if ($ChildEnvironment) {
        foreach ($keyObject in $ChildEnvironment.Keys) {
            $key = [string]$keyObject
            $value = [string]$ChildEnvironment[$keyObject]
            $startInfo.EnvironmentVariables[$key] = $value
        }
    }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        throw "Failed to start native executable: $FileName"
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

function Write-Utf8FileNew {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [AllowEmptyString()]
        [string]$Content
    )

    $encoding = New-Object System.Text.UTF8Encoding($false)
    $bytes = $encoding.GetBytes($Content)
    $stream = New-Object System.IO.FileStream(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally {
        $stream.Dispose()
    }
}

function Read-JsonDictionary {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $serializer = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    $serializer.MaxJsonLength = [int]::MaxValue
    $serializer.RecursionLimit = 4096
    $text = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    $value = $serializer.DeserializeObject($text)
    if (-not ($value -is [System.Collections.IDictionary])) {
        throw "JSON root is not an object: $Path"
    }
    return ,$value
}

function Get-DictionaryItem {
    param(
        [System.Collections.IDictionary]$Dictionary,
        [string]$Key
    )

    if ($null -ne $Dictionary -and @($Dictionary.Keys) -contains $Key) {
        return $Dictionary[$Key]
    }
    return $null
}

function Get-FileIdentity {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $item = Get-Item -LiteralPath $Path
    return [ordered]@{
        path = $item.FullName
        bytes = [long]$item.Length
        sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
    }
}

function Resolve-RunnerExecutable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value,
        [Parameter(Mandatory = $true)]
        [string]$RepositoryRoot
    )

    $containsSeparator = (
        $Value.IndexOf([System.IO.Path]::DirectorySeparatorChar) -ge 0 -or
        $Value.IndexOf([System.IO.Path]::AltDirectorySeparatorChar) -ge 0
    )
    if ([System.IO.Path]::IsPathRooted($Value)) {
        $candidate = [System.IO.Path]::GetFullPath($Value)
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "Runner executable is missing: $candidate"
        }
        return $candidate
    }
    if ($containsSeparator -or (Test-Path -LiteralPath (Join-Path $RepositoryRoot $Value) -PathType Leaf)) {
        $candidate = [System.IO.Path]::GetFullPath((Join-Path $RepositoryRoot $Value))
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "Runner executable is missing: $candidate"
        }
        return $candidate
    }

    $command = Get-Command -Name $Value -CommandType Application -ErrorAction Stop | Select-Object -First 1
    return $command.Source
}

function Wait-ForCk3Cleanup {
    param([int]$TimeoutSeconds)

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $absenceStreak = 0
    $lastPids = @()
    while ([DateTime]::UtcNow -lt $deadline) {
        $rows = @(Get-Process -Name ck3 -ErrorAction SilentlyContinue)
        $lastPids = @($rows | ForEach-Object { [int]$_.Id })
        if ($rows.Count -eq 0) {
            $absenceStreak += 1
            if ($absenceStreak -ge 8) {
                return [pscustomobject]@{
                    ok = $true
                    stable_absence_samples = $absenceStreak
                    remaining_pids = @()
                }
            }
        }
        else {
            $absenceStreak = 0
        }
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 250
    }
    return [pscustomobject]@{
        ok = $false
        stable_absence_samples = $absenceStreak
        remaining_pids = $lastPids
    }
}

function New-SegmentCard {
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
    $form.Controls.Add($accent)

    $eyebrow = New-Object System.Windows.Forms.Label
    $eyebrow.Location = New-Object System.Drawing.Point(176, 112)
    $eyebrow.Size = New-Object System.Drawing.Size(1500, 52)
    $eyebrow.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 22)
    $eyebrow.ForeColor = [System.Drawing.Color]::FromArgb(218, 170, 74)
    $eyebrow.Text = "XAR / CK3 EXACT-BUILD NATIVE CAPABILITY"
    $form.Controls.Add($eyebrow)

    $badge = New-Object System.Windows.Forms.Label
    $badge.Location = New-Object System.Drawing.Point(($screen.Width - 790), 105)
    $badge.Size = New-Object System.Drawing.Size(610, 60)
    $badge.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 18)
    $badge.BackColor = [System.Drawing.Color]::FromArgb(38, 48, 68)
    $badge.ForeColor = [System.Drawing.Color]::White
    $badge.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
    $form.Controls.Add($badge)

    $title = New-Object System.Windows.Forms.Label
    $title.Location = New-Object System.Drawing.Point(170, 225)
    $title.Size = New-Object System.Drawing.Size(($screen.Width - 340), 110)
    $title.Font = New-Object System.Drawing.Font("Segoe UI", 46, [System.Drawing.FontStyle]::Bold)
    $title.ForeColor = [System.Drawing.Color]::White
    $form.Controls.Add($title)

    $chineseTitle = New-Object System.Windows.Forms.Label
    $chineseTitle.Location = New-Object System.Drawing.Point(178, 342)
    $chineseTitle.Size = New-Object System.Drawing.Size(($screen.Width - 356), 64)
    $chineseTitle.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 27)
    $chineseTitle.ForeColor = [System.Drawing.Color]::FromArgb(202, 210, 224)
    $form.Controls.Add($chineseTitle)

    $subtitle = New-Object System.Windows.Forms.Label
    $subtitle.Location = New-Object System.Drawing.Point(178, 438)
    $subtitle.Size = New-Object System.Drawing.Size(($screen.Width - 356), 62)
    $subtitle.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 27)
    $subtitle.ForeColor = [System.Drawing.Color]::FromArgb(156, 201, 255)
    $form.Controls.Add($subtitle)

    $body = New-Object System.Windows.Forms.Label
    $body.Location = New-Object System.Drawing.Point(182, 560)
    $body.Size = New-Object System.Drawing.Size(1040, 430)
    $body.Font = New-Object System.Drawing.Font("Consolas", 21)
    $body.ForeColor = [System.Drawing.Color]::FromArgb(222, 228, 239)
    $form.Controls.Add($body)

    $divider = New-Object System.Windows.Forms.Panel
    $divider.Location = New-Object System.Drawing.Point(1268, 560)
    $divider.Size = New-Object System.Drawing.Size(2, 430)
    $divider.BackColor = [System.Drawing.Color]::FromArgb(65, 78, 104)
    $form.Controls.Add($divider)

    $chineseBody = New-Object System.Windows.Forms.Label
    $chineseBody.Location = New-Object System.Drawing.Point(1330, 560)
    $chineseBody.Size = New-Object System.Drawing.Size(1040, 430)
    $chineseBody.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 21)
    $chineseBody.ForeColor = [System.Drawing.Color]::FromArgb(188, 204, 229)
    $form.Controls.Add($chineseBody)

    $boundary = New-Object System.Windows.Forms.Label
    $boundary.Location = New-Object System.Drawing.Point(182, 1040)
    $boundary.Size = New-Object System.Drawing.Size(($screen.Width - 364), 120)
    $boundary.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 18)
    $boundary.ForeColor = [System.Drawing.Color]::FromArgb(218, 170, 74)
    $boundary.TextAlign = [System.Drawing.ContentAlignment]::MiddleLeft
    $form.Controls.Add($boundary)

    $footer = New-Object System.Windows.Forms.Label
    $footer.Location = New-Object System.Drawing.Point(182, ($screen.Height - 145))
    $footer.Size = New-Object System.Drawing.Size(($screen.Width - 364), 52)
    $footer.Font = New-Object System.Drawing.Font("Segoe UI", 17)
    $footer.ForeColor = [System.Drawing.Color]::FromArgb(132, 144, 166)
    $footer.Text = "English primary narration / Simplified Chinese subtitles  |  英语主叙事 / 简体中文字幕"
    $form.Controls.Add($footer)

    return [pscustomobject]@{
        Form = $form
        Accent = $accent
        Badge = $badge
        Title = $title
        ChineseTitle = $chineseTitle
        Subtitle = $subtitle
        Body = $body
        ChineseBody = $chineseBody
        Boundary = $boundary
    }
}

function Show-SegmentCard {
    param(
        [pscustomobject]$Card,
        [string]$Title,
        [string]$ChineseTitle,
        [string]$Subtitle,
        [string]$Body,
        [string]$ChineseBody,
        [string]$Badge,
        [string]$Boundary,
        [System.Drawing.Color]$Accent
    )

    $Card.Title.Text = $Title
    $Card.ChineseTitle.Text = $ChineseTitle
    $Card.Subtitle.Text = $Subtitle
    $Card.Body.Text = $Body
    $Card.ChineseBody.Text = $ChineseBody
    $Card.Badge.Text = $Badge
    $Card.Boundary.Text = $Boundary
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

function Hide-SegmentCard {
    param([pscustomobject]$Card)

    if ($Card.Form.Visible) {
        $Card.Form.TopMost = $false
        $Card.Form.Hide()
        [System.Windows.Forms.Application]::DoEvents()
    }
}

function New-GameplayLowerThird {
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $form = New-Object System.Windows.Forms.Form
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
    $form.Bounds = New-Object System.Drawing.Rectangle(
        220,
        ($screen.Height - 250),
        ($screen.Width - 440),
        190
    )
    $form.BackColor = [System.Drawing.Color]::FromArgb(12, 16, 28)
    $form.Opacity = 0.90
    $form.ShowInTaskbar = $false
    $form.TopMost = $true

    $badge = New-Object System.Windows.Forms.Label
    $badge.Location = New-Object System.Drawing.Point(24, 18)
    $badge.Size = New-Object System.Drawing.Size(410, 48)
    $badge.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 15)
    $badge.BackColor = [System.Drawing.Color]::FromArgb(55, 75, 105)
    $badge.ForeColor = [System.Drawing.Color]::White
    $badge.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
    $form.Controls.Add($badge)

    $english = New-Object System.Windows.Forms.Label
    $english.Location = New-Object System.Drawing.Point(465, 10)
    $english.Size = New-Object System.Drawing.Size(($form.Width - 495), 62)
    $english.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 23)
    $english.ForeColor = [System.Drawing.Color]::White
    $english.TextAlign = [System.Drawing.ContentAlignment]::MiddleLeft
    $form.Controls.Add($english)

    $chinese = New-Object System.Windows.Forms.Label
    $chinese.Location = New-Object System.Drawing.Point(28, 78)
    $chinese.Size = New-Object System.Drawing.Size(($form.Width - 56), 50)
    $chinese.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 20)
    $chinese.ForeColor = [System.Drawing.Color]::FromArgb(156, 201, 255)
    $chinese.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
    $form.Controls.Add($chinese)

    $boundary = New-Object System.Windows.Forms.Label
    $boundary.Location = New-Object System.Drawing.Point(28, 136)
    $boundary.Size = New-Object System.Drawing.Size(($form.Width - 56), 38)
    $boundary.Font = New-Object System.Drawing.Font("Segoe UI", 13)
    $boundary.ForeColor = [System.Drawing.Color]::FromArgb(218, 170, 74)
    $boundary.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
    $form.Controls.Add($boundary)

    return [pscustomobject]@{
        Form = $form
        Badge = $badge
        English = $english
        Chinese = $chinese
        Boundary = $boundary
    }
}

function Show-GameplayLowerThird {
    param(
        [pscustomobject]$LowerThird,
        [string]$Badge,
        [string]$English,
        [string]$Chinese,
        [string]$Boundary
    )

    $LowerThird.Badge.Text = $Badge
    $LowerThird.English.Text = $English
    $LowerThird.Chinese.Text = $Chinese
    $LowerThird.Boundary.Text = $Boundary
    $LowerThird.Form.TopMost = $true
    if (-not $LowerThird.Form.Visible) {
        $LowerThird.Form.Show()
    }
    $LowerThird.Form.BringToFront()
    [System.Windows.Forms.Application]::DoEvents()
}

function Hide-GameplayLowerThird {
    param([pscustomobject]$LowerThird)

    if ($LowerThird.Form.Visible) {
        $LowerThird.Form.Hide()
        [System.Windows.Forms.Application]::DoEvents()
    }
}

function Bring-Ck3WindowForward {
    param([System.Diagnostics.Process]$Process)

    $Process.Refresh()
    $handle = $Process.MainWindowHandle
    if ($null -eq $handle -or $handle -eq [IntPtr]::Zero) {
        return $false
    }
    $swRestore = 9
    $swpNoSize = 0x0001
    $swpNoMove = 0x0002
    $swpShowWindow = 0x0040
    [XarNativeSegmentWindowApi]::ShowWindow($handle, $swRestore) | Out-Null
    [XarNativeSegmentWindowApi]::SetWindowPos(
        $handle,
        [IntPtr]::Zero,
        0,
        0,
        0,
        0,
        ($swpNoSize -bor $swpNoMove -bor $swpShowWindow)
    ) | Out-Null
    [XarNativeSegmentWindowApi]::BringWindowToTop($handle) | Out-Null
    [XarNativeSegmentWindowApi]::SetForegroundWindow($handle) | Out-Null
    return $true
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runnerExecutable = Resolve-RunnerExecutable -Value $Runner -RepositoryRoot $repositoryRoot

foreach ($argument in @($RunnerArguments)) {
    if ($null -eq $argument) {
        throw "RunnerArguments cannot contain null elements."
    }
    if ($argument.IndexOf([char]0) -ge 0) {
        throw "RunnerArguments cannot contain NUL characters."
    }
    if ($argument -ieq "--output" -or $argument.StartsWith("--output=", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "RunnerArguments must not contain --output; this recorder injects a unique artifact path."
    }
}

$childEnvironment = @{}
if ($Environment) {
    foreach ($keyObject in $Environment.Keys) {
        $key = [string]$keyObject
        $value = [string]$Environment[$keyObject]
        if ($key -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
            throw "Invalid child environment variable name: $key"
        }
        if ($value.IndexOf([char]0) -ge 0) {
            throw "Child environment variable $key contains a NUL character."
        }
        $childEnvironment[$key] = $value
    }
}

$outputRoot = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$today = Get-Date -Format "yyyy-MM-dd"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
$normalizedSegmentId = $SegmentId.ToLowerInvariant()
$fileStem = "ck3-native-$normalizedSegmentId-$stamp"
$rawVideo = Join-Path $outputRoot "$fileStem.raw.mkv"
$finalVideo = Join-Path $outputRoot "$fileStem.mp4"
$artifactPath = Join-Path $outputRoot "$fileStem.live.json"
$runnerStdoutPath = Join-Path $outputRoot "$fileStem.stdout.txt"
$runnerStderrPath = Join-Path $outputRoot "$fileStem.stderr.txt"
$sidecarPath = Join-Path $outputRoot "$fileStem.video.json"

foreach ($candidate in @(
    $rawVideo,
    $finalVideo,
    $artifactPath,
    $runnerStdoutPath,
    $runnerStderrPath,
    $sidecarPath
)) {
    if (Test-Path -LiteralPath $candidate) {
        throw "Refusing to overwrite existing recording output: $candidate"
    }
}

$effectiveRunnerArguments = @($RunnerArguments) + @("--output", $artifactPath)
$ffmpeg = (Get-Command ffmpeg -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$ffprobeCandidate = Join-Path (Split-Path $ffmpeg -Parent) "ffprobe.exe"
$ffprobe = if (Test-Path -LiteralPath $ffprobeCandidate -PathType Leaf) {
    $ffprobeCandidate
}
else {
    (Get-Command ffprobe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
}

$encoderInventory = (& $ffmpeg -hide_banner -encoders 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0 -or $encoderInventory -notmatch '(?m)^\s*V\S*\s+h264_nvenc\s') {
    throw "FFmpeg does not advertise the required h264_nvenc encoder."
}

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
if ($screen.Width -ne $captureWidth -or $screen.Height -ne $captureHeight) {
    throw "Primary display must be exactly ${captureWidth}x${captureHeight}; observed $($screen.Width)x$($screen.Height)."
}
if (Get-Process -Name ck3 -ErrorAction SilentlyContinue) {
    throw "Refusing to record while ck3.exe is already running."
}

$obsWindows = @(
    Get-Process -Name obs64 -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } |
        ForEach-Object { $_.MainWindowHandle }
)
foreach ($handle in $obsWindows) {
    [XarNativeSegmentWindowApi]::ShowWindow($handle, 6) | Out-Null
}

$gold = [System.Drawing.Color]::FromArgb(218, 170, 74)
$green = [System.Drawing.Color]::FromArgb(55, 205, 126)
$red = [System.Drawing.Color]::FromArgb(235, 84, 92)
$card = New-SegmentCard
$lowerThird = New-GameplayLowerThird
$captureProcess = $null
$runnerProcess = $null
$runnerStdoutTask = $null
$runnerStderrTask = $null
$runnerStdout = ""
$runnerStderr = ""
$streamsPersisted = $false
$qualified = $false
$caughtError = $null
$qualificationFailure = $null
$artifact = $null
$artifactIdentity = $null
$runnerExitCode = $null
$cleanupProof = $null
$foregroundAttemptCount = 0
$seenCk3Pids = New-Object 'System.Collections.Generic.HashSet[int]'
$seenWindowPids = New-Object 'System.Collections.Generic.HashSet[int]'
$orderedCk3Pids = New-Object 'System.Collections.Generic.List[int]'

try {
    Show-SegmentCard -Card $card `
        -Title $EnglishTitle `
        -ChineseTitle $ChineseTitle `
        -Subtitle "LIVE CK3 NATIVE CAPABILITY SEGMENT" `
        -Body ("OBSERVE exact-build CK3 state`r`n" +
               "-> run one bounded native acceptance scenario`r`n" +
               "-> expose the managed CK3 process on screen`r`n" +
               "-> verify the runner artifact and process cleanup") `
        -ChineseBody ("观察 exact-build CK3 状态`r`n" +
                      "→ 执行一条有边界的原生实机验收场景`r`n" +
                      "→ 将受管 CK3 进程真实展示在画面中`r`n" +
                      "→ 核验 runner artifact 与进程清理") `
        -Badge $StatusBadge `
        -Boundary $BoundaryText `
        -Accent $gold

    $captureProcess = Start-ArrayProcess `
        -FileName $ffmpeg `
        -WorkingDirectory $repositoryRoot `
        -RedirectInput `
        -Arguments @(
            "-hide_banner", "-loglevel", "error",
            "-f", "gdigrab",
            "-framerate", [string]$captureFrameRate,
            "-draw_mouse", "0",
            "-video_size", "${captureWidth}x${captureHeight}",
            "-i", "desktop",
            "-c:v", "h264_nvenc",
            "-preset", "p5",
            "-tune", "hq",
            "-rc", "vbr",
            "-cq", "22",
            "-b:v", "0",
            "-pix_fmt", "yuv420p",
            "-n", $rawVideo
        )
    Pump-Ui -Milliseconds 1200
    if ($captureProcess.HasExited) {
        throw "FFmpeg capture exited before the title card completed (exit $($captureProcess.ExitCode))."
    }
    Pump-Ui -Milliseconds $titleMilliseconds

    $runnerProcess = Start-ArrayProcess `
        -FileName $runnerExecutable `
        -Arguments $effectiveRunnerArguments `
        -WorkingDirectory $repositoryRoot `
        -CaptureOutput `
        -ChildEnvironment $childEnvironment
    $runnerStdoutTask = $runnerProcess.StandardOutput.ReadToEndAsync()
    $runnerStderrTask = $runnerProcess.StandardError.ReadToEndAsync()

    $currentDisplayedPid = $null
    $visualMode = "start-card"
    $lastWindowRaiseAt = [DateTime]::MinValue
    while (-not $runnerProcess.HasExited) {
        $ck3Rows = @(Get-Process -Name ck3 -ErrorAction SilentlyContinue)
        foreach ($row in $ck3Rows) {
            $ck3Pid = [int]$row.Id
            if ($seenCk3Pids.Add($ck3Pid)) {
                $orderedCk3Pids.Add($ck3Pid)
            }
        }

        if ($ck3Rows.Count -gt 0) {
            Hide-SegmentCard -Card $card
            $latest = $ck3Rows |
                Sort-Object -Property StartTime -Descending |
                Select-Object -First 1
            if ($null -eq $currentDisplayedPid -or $currentDisplayedPid -ne [int]$latest.Id) {
                $currentDisplayedPid = [int]$latest.Id
                $ordinal = $orderedCk3Pids.IndexOf($currentDisplayedPid) + 1
                Show-GameplayLowerThird -LowerThird $lowerThird `
                    -Badge $StatusBadge `
                    -English "LIVE PROCESS #${ordinal}: $EnglishTitle" `
                    -Chinese "实机进程 #$ordinal：$ChineseTitle" `
                    -Boundary $BoundaryText
                $visualMode = "game"
            }

            if (([DateTime]::UtcNow - $lastWindowRaiseAt).TotalMilliseconds -ge 500) {
                foreach ($row in $ck3Rows) {
                    if (Bring-Ck3WindowForward -Process $row) {
                        $foregroundAttemptCount += 1
                        $seenWindowPids.Add([int]$row.Id) | Out-Null
                    }
                }
                $lowerThird.Form.BringToFront()
                [System.Windows.Forms.Application]::DoEvents()
                $lastWindowRaiseAt = [DateTime]::UtcNow
            }
        }
        elseif ($seenCk3Pids.Count -gt 0 -and $visualMode -ne "handoff") {
            Hide-GameplayLowerThird -LowerThird $lowerThird
            Show-SegmentCard -Card $card `
                -Title "PROCESS HANDOFF / EVIDENCE BINDING" `
                -ChineseTitle "进程交接 / 正在绑定证据" `
                -Subtitle $EnglishTitle `
                -Body ("A managed CK3 process has closed.`r`n`r`n" +
                       "The runner is validating its checkpoint, preparing the next`r`n" +
                       "isolated stage, or finalizing typed native evidence.") `
                -ChineseBody ("一个受管 CK3 进程已经关闭。`r`n`r`n" +
                              "runner 正在核验检查点、准备下一隔离阶段，`r`n" +
                              "或收束 typed native evidence。") `
                -Badge $StatusBadge `
                -Boundary $BoundaryText `
                -Accent $gold
            $currentDisplayedPid = $null
            $visualMode = "handoff"
        }

        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 120
    }

    $runnerProcess.WaitForExit()
    $runnerExitCode = [int]$runnerProcess.ExitCode
    $runnerStdout = $runnerStdoutTask.GetAwaiter().GetResult()
    $runnerStderr = $runnerStderrTask.GetAwaiter().GetResult()
    Write-Utf8FileNew -Path $runnerStdoutPath -Content $runnerStdout
    Write-Utf8FileNew -Path $runnerStderrPath -Content $runnerStderr
    $streamsPersisted = $true

    Hide-GameplayLowerThird -LowerThird $lowerThird
    Show-SegmentCard -Card $card `
        -Title "VERIFYING NATIVE EVIDENCE" `
        -ChineseTitle "正在核验原生证据" `
        -Subtitle $EnglishTitle `
        -Body "Parsing the runner artifact, hashing evidence, and proving that no managed CK3 process remains..." `
        -ChineseBody "正在解析 runner artifact、计算证据哈希，并证明没有任何受管 CK3 进程残留……" `
        -Badge $StatusBadge `
        -Boundary $BoundaryText `
        -Accent $gold
    Pump-Ui -Milliseconds 500

    if (-not (Test-Path -LiteralPath $artifactPath -PathType Leaf)) {
        $qualificationFailure = "Runner did not write the injected output artifact."
    }
    else {
        $artifact = Read-JsonDictionary -Path $artifactPath
        $artifactIdentity = Get-FileIdentity -Path $artifactPath
        $artifactOk = Get-DictionaryItem -Dictionary $artifact -Key "ok"
        if (-not ($artifactOk -is [bool]) -or -not [bool]$artifactOk) {
            $qualificationFailure = "Runner artifact does not contain top-level ok=true."
        }
    }

    $cleanupProof = Wait-ForCk3Cleanup -TimeoutSeconds $cleanupTimeoutSeconds
    if (-not $cleanupProof.ok) {
        $qualificationFailure = "CK3 cleanup failed; remaining PIDs: $(@($cleanupProof.remaining_pids) -join ', ')."
    }
    if ($runnerExitCode -ne 0) {
        $qualificationFailure = "Runner exited with code $runnerExitCode."
    }

    $pidText = if ($orderedCk3Pids.Count -gt 0) {
        @($orderedCk3Pids) -join " -> "
    }
    else {
        "none observed"
    }
    $artifactKind = if ($null -ne $artifact) {
        [string](Get-DictionaryItem -Dictionary $artifact -Key "kind")
    }
    else {
        "unavailable"
    }
    $artifactHashShort = if ($null -ne $artifactIdentity) {
        ([string]$artifactIdentity.sha256).Substring(0, 16)
    }
    else {
        "unavailable"
    }

    if ($null -eq $qualificationFailure) {
        $qualified = $true
        Show-SegmentCard -Card $card `
            -Title "LIVE CAPABILITY: GREEN" `
            -ChineseTitle "实机能力验收：GREEN / 通过" `
            -Subtitle $EnglishTitle `
            -Body ("runner exit       : 0`r`n" +
                   "artifact kind     : $artifactKind`r`n" +
                   "artifact SHA-256  : $artifactHashShort...`r`n" +
                   "managed CK3 PIDs  : $pidText`r`n" +
                   "foreground windows: $($seenWindowPids.Count)`r`n" +
                   "cleanup           : no ck3.exe remains") `
            -ChineseBody ("runner 退出码      ：0`r`n" +
                          "artifact 类型      ：$artifactKind`r`n" +
                          "artifact SHA-256   ：$artifactHashShort...`r`n" +
                          "受管 CK3 进程      ：$pidText`r`n" +
                          "前置展示窗口       ：$($seenWindowPids.Count)`r`n" +
                          "清理结果           ：没有 ck3.exe 残留") `
            -Badge "$StatusBadge / GREEN" `
            -Boundary $BoundaryText `
            -Accent $green
    }
    else {
        $artifactError = if ($null -ne $artifact) {
            [string](Get-DictionaryItem -Dictionary $artifact -Key "error")
        }
        else {
            "artifact unavailable"
        }
        Show-SegmentCard -Card $card `
            -Title "LIVE CAPABILITY: RED" `
            -ChineseTitle "实机能力验收：RED / 未通过" `
            -Subtitle "THIS SEGMENT IS NOT QUALIFIED" `
            -Body ("failure     : $qualificationFailure`r`n" +
                   "artifact    : $artifactError`r`n" +
                   "CK3 PIDs    : $pidText") `
            -ChineseBody ("失败原因：$qualificationFailure`r`n" +
                          "artifact：$artifactError`r`n" +
                          "CK3 进程：$pidText") `
            -Badge "$StatusBadge / RED" `
            -Boundary $BoundaryText `
            -Accent $red
    }
    Pump-Ui -Milliseconds $resultMilliseconds
}
catch {
    $caughtError = $_
    try {
        Hide-GameplayLowerThird -LowerThird $lowerThird
        Show-SegmentCard -Card $card `
            -Title "SEGMENT RECORDING FAILED" `
            -ChineseTitle "能力片段录制失败" `
            -Subtitle "RAW CAPTURE WILL BE RETAINED" `
            -Body $_.Exception.Message `
            -ChineseBody "该片段不能作为 GREEN 实机证据；原始录制会保留以供诊断。" `
            -Badge "$StatusBadge / RED" `
            -Boundary $BoundaryText `
            -Accent $red
        Pump-Ui -Milliseconds 8000
    }
    catch {
        # Preserve the original failure if the emergency card cannot render.
    }
}
finally {
    if ($runnerProcess -and -not $runnerProcess.HasExited) {
        try {
            $runnerProcess.Kill()
            $runnerProcess.WaitForExit()
        }
        catch {
            # The final cleanup proof below remains authoritative.
        }
    }

    if ($runnerProcess -and -not $streamsPersisted) {
        try {
            if ($runnerStdoutTask) {
                $runnerStdout = $runnerStdoutTask.GetAwaiter().GetResult()
            }
            if ($runnerStderrTask) {
                $runnerStderr = $runnerStderrTask.GetAwaiter().GetResult()
            }
            if (-not (Test-Path -LiteralPath $runnerStdoutPath)) {
                Write-Utf8FileNew -Path $runnerStdoutPath -Content $runnerStdout
            }
            if (-not (Test-Path -LiteralPath $runnerStderrPath)) {
                Write-Utf8FileNew -Path $runnerStderrPath -Content $runnerStderr
            }
            $streamsPersisted = $true
        }
        catch {
            if ($null -eq $caughtError) {
                $caughtError = $_
            }
        }
    }

    if ($null -eq $cleanupProof -or -not $cleanupProof.ok) {
        $cleanupProof = Wait-ForCk3Cleanup -TimeoutSeconds $cleanupTimeoutSeconds
        if (-not $cleanupProof.ok -and $null -eq $caughtError) {
            $caughtError = New-Object System.Management.Automation.ErrorRecord(
                (New-Object System.InvalidOperationException(
                    "Managed cleanup left ck3.exe running: $(@($cleanupProof.remaining_pids) -join ', ')"
                )),
                "Ck3CleanupFailed",
                [System.Management.Automation.ErrorCategory]::CloseError,
                $null
            )
        }
    }

    if ($captureProcess -and -not $captureProcess.HasExited) {
        try {
            $captureProcess.StandardInput.WriteLine("q")
            $captureProcess.StandardInput.Flush()
            $captureProcess.StandardInput.Close()
            if (-not $captureProcess.WaitForExit(20000)) {
                $captureProcess.Kill()
                $captureProcess.WaitForExit()
            }
        }
        catch {
            if (-not $captureProcess.HasExited) {
                $captureProcess.Kill()
                $captureProcess.WaitForExit()
            }
        }
    }

    if ($card -and $card.Form) {
        $card.Form.Close()
        $card.Form.Dispose()
    }
    if ($lowerThird -and $lowerThird.Form) {
        $lowerThird.Form.Close()
        $lowerThird.Form.Dispose()
    }
    foreach ($handle in $obsWindows) {
        [XarNativeSegmentWindowApi]::ShowWindow($handle, 9) | Out-Null
    }
}

if ($null -ne $caughtError) {
    throw $caughtError
}
if (-not $qualified) {
    throw "Native capability segment was RED; raw recording retained at $rawVideo"
}
if (-not (Test-Path -LiteralPath $rawVideo -PathType Leaf)) {
    throw "FFmpeg did not produce the raw recording."
}
if (Test-Path -LiteralPath $finalVideo) {
    throw "Refusing to overwrite final video: $finalVideo"
}

$muxProcess = Start-ArrayProcess `
    -FileName $ffmpeg `
    -WorkingDirectory $repositoryRoot `
    -CaptureOutput `
    -Arguments @(
        "-hide_banner", "-loglevel", "error",
        "-i", $rawVideo,
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "96k",
        "-movflags", "+faststart",
        "-metadata", "title=$EnglishTitle / $ChineseTitle",
        "-n", $finalVideo
    )
$muxStdoutTask = $muxProcess.StandardOutput.ReadToEndAsync()
$muxStderrTask = $muxProcess.StandardError.ReadToEndAsync()
$muxProcess.WaitForExit()
$muxStdout = $muxStdoutTask.GetAwaiter().GetResult()
$muxStderr = $muxStderrTask.GetAwaiter().GetResult()
if ($muxProcess.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $finalVideo -PathType Leaf)) {
    throw "MP4 mux failed (exit $($muxProcess.ExitCode)): $muxStderr"
}

$probeProcess = Start-ArrayProcess `
    -FileName $ffprobe `
    -WorkingDirectory $repositoryRoot `
    -CaptureOutput `
    -Arguments @(
        "-v", "error",
        "-show_streams",
        "-show_format",
        "-of", "json",
        $finalVideo
    )
$probeStdoutTask = $probeProcess.StandardOutput.ReadToEndAsync()
$probeStderrTask = $probeProcess.StandardError.ReadToEndAsync()
$probeProcess.WaitForExit()
$probeStdout = $probeStdoutTask.GetAwaiter().GetResult()
$probeStderr = $probeStderrTask.GetAwaiter().GetResult()
if ($probeProcess.ExitCode -ne 0) {
    throw "ffprobe failed (exit $($probeProcess.ExitCode)): $probeStderr"
}

$probeSerializer = New-Object System.Web.Script.Serialization.JavaScriptSerializer
$probeSerializer.MaxJsonLength = [int]::MaxValue
$probeSerializer.RecursionLimit = 64
$probe = $probeSerializer.DeserializeObject($probeStdout)
$streams = @($probe["streams"])
$videoStream = $streams |
    Where-Object { $_ -is [System.Collections.IDictionary] -and $_["codec_type"] -eq "video" } |
    Select-Object -First 1
$audioStream = $streams |
    Where-Object { $_ -is [System.Collections.IDictionary] -and $_["codec_type"] -eq "audio" } |
    Select-Object -First 1
if ($null -eq $videoStream -or $videoStream["codec_name"] -ne "h264") {
    throw "Final MP4 lacks an H.264 video stream."
}
if ([int]$videoStream["width"] -ne $captureWidth -or [int]$videoStream["height"] -ne $captureHeight) {
    throw "Final MP4 geometry differs from ${captureWidth}x${captureHeight}."
}
if ($null -eq $audioStream -or $audioStream["codec_name"] -ne "aac") {
    throw "Final MP4 lacks an AAC audio stream."
}

$frameRateParts = ([string]$videoStream["avg_frame_rate"]).Split('/')
if ($frameRateParts.Count -ne 2 -or [double]$frameRateParts[1] -eq 0) {
    throw "Final MP4 has an invalid average frame rate."
}
$observedFrameRate = [double]$frameRateParts[0] / [double]$frameRateParts[1]
if ($observedFrameRate -lt 28.0 -or $observedFrameRate -gt 31.0) {
    throw "Final MP4 frame rate is $observedFrameRate, expected the 28-31 fps desktop-capture band."
}

$duration = [double]::Parse(
    [string]$probe["format"]["duration"],
    [System.Globalization.CultureInfo]::InvariantCulture
)
$videoIdentity = Get-FileIdentity -Path $finalVideo
if ([long]$videoIdentity.bytes -lt 100KB -or $duration -lt 10.0) {
    throw "Final MP4 sanity check failed: bytes=$($videoIdentity.bytes), duration=$duration"
}

$stdoutIdentity = Get-FileIdentity -Path $runnerStdoutPath
$stderrIdentity = Get-FileIdentity -Path $runnerStderrPath
$artifactKind = [string](Get-DictionaryItem -Dictionary $artifact -Key "kind")
$evidenceClassification = [string](
    Get-DictionaryItem -Dictionary $artifact -Key "evidence_classification"
)
$artifactElapsedSeconds = Get-DictionaryItem -Dictionary $artifact -Key "elapsed_seconds"
$sidecar = [ordered]@{
    format_version = 1
    kind = "ck3_native_capability_segment_video"
    created_at = [DateTime]::UtcNow.ToString("o")
    date = $today
    segment = [ordered]@{
        id = $SegmentId
        english_title = $EnglishTitle
        chinese_title = $ChineseTitle
        status_badge = $StatusBadge
        boundary_text = $BoundaryText
    }
    language = [ordered]@{
        primary = "English"
        secondary = "Simplified Chinese subtitles"
        title_cards_bilingual = $true
        gameplay_lower_third_bilingual = $true
        evidence_card_bilingual = $true
    }
    runner = [ordered]@{
        executable = $runnerExecutable
        arguments = @($effectiveRunnerArguments)
        environment_keys = @($childEnvironment.Keys | Sort-Object)
        exit_code = $runnerExitCode
        stdout = $stdoutIdentity
        stderr = $stderrIdentity
    }
    live_artifact = [ordered]@{
        path = $artifactIdentity.path
        bytes = $artifactIdentity.bytes
        sha256 = $artifactIdentity.sha256
        ok = [bool](Get-DictionaryItem -Dictionary $artifact -Key "ok")
        kind = $artifactKind
        evidence_classification = $evidenceClassification
        elapsed_seconds = $artifactElapsedSeconds
    }
    process_evidence = [ordered]@{
        ck3_pids_in_observed_order = @($orderedCk3Pids)
        ck3_process_count = $orderedCk3Pids.Count
        ck3_window_pids = @($seenWindowPids | Sort-Object)
        foreground_attempt_count = $foregroundAttemptCount
        no_ck3_processes_before = $true
        no_ck3_processes_after = [bool]$cleanupProof.ok
        stable_absence_samples = $cleanupProof.stable_absence_samples
    }
    video = [ordered]@{
        path = $videoIdentity.path
        bytes = $videoIdentity.bytes
        sha256 = $videoIdentity.sha256
        duration_seconds = [Math]::Round($duration, 3)
        width = $captureWidth
        height = $captureHeight
        frame_rate = [Math]::Round($observedFrameRate, 3)
        video_codec = "H.264"
        video_encoder = "h264_nvenc"
        pixel_format = [string]$videoStream["pix_fmt"]
        audio_codec = "AAC"
        audio_description = "silent AAC stereo"
    }
}
Write-Utf8FileNew `
    -Path $sidecarPath `
    -Content (($sidecar | ConvertTo-Json -Depth 10) + "`n")
$sidecarIdentity = Get-FileIdentity -Path $sidecarPath

$rawItem = Get-Item -LiteralPath $rawVideo
$resolvedRaw = $rawItem.FullName
$resolvedOutputRoot = [System.IO.Path]::GetFullPath($outputRoot).TrimEnd('\') + '\'
if (-not $resolvedRaw.StartsWith($resolvedOutputRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove raw capture outside the requested output directory: $resolvedRaw"
}
Remove-Item -LiteralPath $resolvedRaw -Force

[pscustomobject]@{
    ok = $true
    segment_id = $SegmentId
    video = $finalVideo
    video_sha256 = $videoIdentity.sha256
    sidecar = $sidecarPath
    sidecar_sha256 = $sidecarIdentity.sha256
    live_artifact = $artifactPath
    live_artifact_sha256 = $artifactIdentity.sha256
    stdout = $runnerStdoutPath
    stderr = $runnerStderrPath
    ck3_pids = @($orderedCk3Pids)
    duration_seconds = [Math]::Round($duration, 3)
    bytes = $videoIdentity.bytes
}
