# R758 无 PowerShell 策略的正式预览入口

状态：**本机同候选实机通过，可作为现有冻结 ZIP 的附加启动入口；尚未重新打包 ZIP。**

候选目录为 `C:\g2feudal-r751-entry\candidate-python-operator-02`。交付 seal SHA-256 为 `B7FBAE2A2595515471889307DFA6D2745EE3B4ABCE74478A21CC7823B5597FBB`，operator manifest SHA-256 为 `8DE2915F720472431F3CD4E66373C9E4A09BF8AC21DC2AD0F52061F55B420367`。它不需要 `.ps1`，也不要求修改 Windows ExecutionPolicy。

在 `cmd.exe` 或 PowerShell 中使用同一条 Python 命令启动：

```text
"Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "C:\g2feudal-r751-entry\source-master-d7e6ef36\tools\g2_preview_operator.py" run --manifest "C:\g2feudal-r751-entry\candidate-python-operator-02\operator-manifest.json" --output "C:\g2feudal-r751-entry\candidate-python-operator-02\attempt-user-02" --turns 20 --timeout 390 --readiness-timeout 300
```

每次运行必须使用新的 `--output` 目录。入口启动后会打印 stop 文件位置。受控停止在另一个终端执行：

```text
"Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "C:\g2feudal-r751-entry\source-master-d7e6ef36\tools\g2_preview_operator.py" request-stop --manifest "C:\g2feudal-r751-entry\candidate-python-operator-02\operator-manifest.json"
```

读取退出状态：

```text
"Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "C:\g2feudal-r751-entry\source-master-d7e6ef36\tools\g2_preview_operator.py" status --report "<本次 output>\formal-report.txt"
```

冷恢复时重复启动命令并换用新的 output 目录。持久化文件位于：

- checkpoint：`C:\g2feudal-r751-entry\candidate-python-operator-02\state\profile\save games\xar_checkpoint.ck3`
- agent 状态：`C:\g2feudal-r751-entry\candidate-python-operator-02\state\native-session\driver-state.json`
- CK3 日志：`C:\g2feudal-r751-entry\candidate-python-operator-02\state\profile\logs`
- 每次完整证据：`<本次 output>\formal-report.txt` 与 `operator-receipt.json`

冻结组合为 CK3 `1.19.0.6`，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，Python source/operator commit `d7e6ef368b1a57a3810a538fce4de5f6edd058f6`，native DLL source commit `320efe63b57959e6b314072acbe8043476cc56cf`，只加载 `mod/xar_autoplayer.mod`，manifest 声明 `disabled_dlcs=[]`，支持政府仅为 `feudal_government`。

R758 从先前 checkpoint 真实冷恢复，通过该入口完成 20/20 turns、14 次查询、6 次 gameplay 和 2 次 checkpoint，日期 `53146272 -> 53150880`（192 游戏日），随后回收 CK3 进程树。正式报告 SHA-256 `D94A2C27CD2EDD93F257D057584250E7AFA6DFD712B3F34DC51209FD6E2214B4`，operator receipt SHA-256 `1EA8341462ECBC8DA85363FA6BB068EAE74B86BDB88BBCC29F29AA10B286C467`，最终 checkpoint SHA-256 `14B8151351AE0FD139C09672DB65542FE56D19C703FC4F63653AC1C8FD041497`，最终 driver state SHA-256 `D9871B332BCFDFDE63BBF219D2446F29012E5FC398F2C0DD5DAD746BF377842C`。

已验证范围是该普通标准封建 campaign 的有界 production 循环、战争声明查询与保守不宣战、日期推进、checkpoint、退出回收和随后冷恢复入口。议会四类完整门、战争终局、自然指定事件、自然继承、完整治理/婚姻外交、1066→1453 整局和第二独立种子仍未通过，不得据此广告。G2 权威状态仍为 1/8。

现有冻结 ZIP `g2-preview-candidate-d11268f1-eefc88e4.zip` 仍是可迁移的正式包；本页记录的是本机可直接运行、已实机验证的后续入口候选，尚未把它描述成新的冻结 ZIP。
