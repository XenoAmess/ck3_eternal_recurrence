param(
    [Parameter(Mandatory=$true)][ValidateSet('inspect','invoke','set_text','keys')][string]$Operation,
    [long]$Hwnd=0,
    [string]$Name='',
    [string]$ControlType='',
    [string]$AutomationId='',
    [string]$TextFile='',
    [string]$Keys=''
)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class WorkshopInput {
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint pid);
 [DllImport("user32.dll")] public static extern IntPtr GetKeyboardLayout(uint tid);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr LoadKeyboardLayout(string id,uint flags);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
}
'@
function Describe($e) {
 $c=$e.Current
 $patterns=@($e.GetSupportedPatterns() | ForEach-Object {$_.ProgrammaticName})
 $value=$null
 $selected=$null
 if($patterns -contains 'SelectionItemPatternIdentifiers.Pattern'){
   $selected=([System.Windows.Automation.SelectionItemPattern]$e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Current.IsSelected
 }
 if(-not $c.IsPassword -and $patterns -contains 'ValuePatternIdentifiers.Pattern') {
   $value=([System.Windows.Automation.ValuePattern]$e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)).Current.Value
 }
 return [ordered]@{name=$c.Name;type=$c.ControlType.ProgrammaticName.Replace('ControlType.','');automation_id=$c.AutomationId;pid=$c.ProcessId;hwnd=$c.NativeWindowHandle;enabled=$c.IsEnabled;offscreen=$c.IsOffscreen;rect=$c.BoundingRectangle.ToString();patterns=$patterns;value=$value;selected=$selected}
}
try {
 if($Hwnd -eq 0) {
  if($Operation -ne 'inspect'){throw 'An exact window handle is required'}
  $ws=[System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
  $rows=@(foreach($w in $ws){if($w.Current.Name -match 'Crusader Kings|Paradox|Steam'){Describe $w}})
  [ordered]@{ok=$true;windows=$rows} | ConvertTo-Json -Depth 6 -Compress
  exit 0
 }
 $root=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Hwnd)
 $process=Get-Process -Id $root.Current.ProcessId
 if($process.ProcessName -ne 'Paradox Launcher'){throw 'Target is not a Paradox Launcher window'}
 $all=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
 if($Operation -eq 'inspect'){
   $rows=@(foreach($e in $all){Describe $e})
   [ordered]@{ok=$true;window=(Describe $root);controls=$rows} | ConvertTo-Json -Depth 6 -Compress
   exit 0
 }
 $matches=@(foreach($e in $all){
   if(($Name -eq '' -or $e.Current.Name -ceq $Name) -and
      (($AutomationId -eq '' -and $Operation -ne 'set_text') -or $e.Current.AutomationId -ceq $AutomationId) -and
      ($ControlType -eq '' -or $e.Current.ControlType.ProgrammaticName -eq "ControlType.$ControlType")){$e}
 })
 if($matches.Count -ne 1){throw "Expected one control, found $($matches.Count)"}
 $target=$matches[0]
 if(-not $target.Current.IsEnabled){throw 'Target control is disabled'}
 if($Operation -eq 'invoke'){
   if($ControlType -ne 'ListItem'){
     [void][WorkshopInput]::SetForegroundWindow([IntPtr]$Hwnd)
     $target.SetFocus()
   }
   $before=Describe $target
   $patterns=@($target.GetSupportedPatterns() | ForEach-Object {$_.ProgrammaticName})
   if($ControlType -eq 'ListItem' -and $patterns -contains 'SelectionItemPatternIdentifiers.Pattern') {
     ([System.Windows.Automation.SelectionItemPattern]$target.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
   } elseif($patterns -contains 'InvokePatternIdentifiers.Pattern') {
     ([System.Windows.Automation.InvokePattern]$target.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)).Invoke()
   } elseif($patterns -contains 'ExpandCollapsePatternIdentifiers.Pattern') {
     ([System.Windows.Automation.ExpandCollapsePattern]$target.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)).Expand()
   } elseif($patterns -contains 'SelectionItemPatternIdentifiers.Pattern') {
     ([System.Windows.Automation.SelectionItemPattern]$target.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
   } else {throw 'Control has no semantic invocation pattern'}
   Start-Sleep -Milliseconds 600
   [ordered]@{ok=$true;action='invoke';target=$before} | ConvertTo-Json -Depth 6 -Compress
 } else {
   [void][WorkshopInput]::SetForegroundWindow([IntPtr]$Hwnd)
   $target.SetFocus()
   $english=[WorkshopInput]::LoadKeyboardLayout('00000409',1)
   [void][WorkshopInput]::PostMessage([IntPtr]$Hwnd,0x50,[IntPtr]::Zero,$english)
   Start-Sleep -Milliseconds 150
   [uint32]$windowPid=0
   $thread=[WorkshopInput]::GetWindowThreadProcessId([IntPtr]$Hwnd,[ref]$windowPid)
   $layout=[WorkshopInput]::GetKeyboardLayout($thread).ToInt64() -band 65535
   if($layout -ne 1033){throw 'English keyboard layout was not confirmed'}
   if([WorkshopInput]::GetForegroundWindow().ToInt64() -ne $Hwnd){throw 'Foreground window was not confirmed'}
   if($Operation -eq 'keys'){
     if($Keys -notmatch '^(\{(ENTER|HOME|END|UP|DOWN|TAB|ESC)\})+$'){throw 'Unsupported navigation key sequence'}
     [System.Windows.Forms.SendKeys]::SendWait($Keys)
     Start-Sleep -Milliseconds 600
     [ordered]@{ok=$true;action='keys';keys=$Keys;langid=$layout} | ConvertTo-Json -Compress
     exit 0
   }
   $text=[IO.File]::ReadAllText((Resolve-Path -LiteralPath $TextFile),[Text.Encoding]::UTF8)
   Set-Clipboard -Value $text
   [System.Windows.Forms.SendKeys]::SendWait('^a')
   [System.Windows.Forms.SendKeys]::SendWait('^v')
   Start-Sleep -Milliseconds 200
   $pattern=[System.Windows.Automation.ValuePattern]$target.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
   $method='clipboard'
   $got=$pattern.Current.Value
   if($got.Replace("`r`n","`n") -cne $text.Replace("`r`n","`n")){
      $pattern.SetValue($text)
      $method='ValuePattern after clipboard mismatch'
      Start-Sleep -Milliseconds 150
      $got=$pattern.Current.Value
   }
   if($got.Replace("`r`n","`n") -cne $text.Replace("`r`n","`n")){throw 'Control text readback mismatch'}
   [ordered]@{ok=$true;action='set_text';method=$method;langid=$layout;characters=$got.Length;readback=$got;target=(Describe $target)} | ConvertTo-Json -Depth 6 -Compress
 }
} catch {
 [ordered]@{ok=$false;error=$_.Exception.Message} | ConvertTo-Json -Compress
 exit 1
}
