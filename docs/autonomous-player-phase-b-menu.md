# 自主玩家 Phase B：主菜单到书签页

## 范围与成功声明

Phase B 的第一个实机竖切只允许一次玩家可见输入：在 CK3 主菜单点击【新游戏】，随后确认连续两帧稳定的
书签选择页并退出。成功报告只能声明：

```text
acceptance_claim = visible_main_menu_to_bookmark_lobby_only
valid_score_episode = false
growth100_lobby_adoption_proven = false
```

它不选择角色、不打开规则页、不点击大厅【开始】，也不证明 Growth+100 已被大厅采用。任何未知窗口、遮罩、
OCR 歧义、焦点变化、进程身份变化或后置状态超时都会终止尝试；已经进入可能输入窗口后不得重试。

## 固定信任边界

- 仍使用 Phase A 的仓库外隔离 `-userdir`、production-only 投影、non-debug CK3、精确单 mod inventory、
  suspended-create → Job → record → resume 和按句柄回收链。
- UI 合约只能从仓库固定路径
  `ck3_autonomous_player/configs/ui/ck3-1.19.0.6.zh-hans.2560x1440.json` 加载。文件必须由 prepared
  environment 的 agent-runtime 指纹覆盖，运行时还要把原件复制进本次 run 并校验 SHA-256；CLI、策略层和
  episode 数据均不能传入坐标、控件文字、后置状态或替代合约。
- 本竖切注册能力必须精确等于 `{main_menu.new_game}`，禁用能力必须包含
  `bookmark_lobby.start_game`。同名 control ID 的文字、区域、前后屏幕或风险语义发生漂移也要拒绝，而不是只
  检查 ID。
- 策略层只能看到截图、OCR、可见锚点与不透明控件 token。启动日志只由 supervisor 压缩成单 mod / mount
  attestation，原始日志不得进入观察或决策层。

## 可见状态合约

`main_menu` 和 `bookmark_lobby` 均要求连续两帧。两帧证据必须保留，而不是只返回最后一帧；其采集序号和
monotonic 时间严格递增，并绑定同一 PID、创建时间、进程句柄映像、HWND 与 client rect。所有锚点中心在两帧间
最多漂移 15 像素。

主菜单以限定区域内的【继续游戏】【新游戏】【载入游戏】作为正向 OCR 锚。仅有正向文字不足以排除同一 CK3
窗口内的模态遮罩，因此还需要：

- 已知阻塞文案反证，例如【确认退出游戏】【取消】【欢迎来到】【开始教程】；
- 从本机 1.19.0.6、简中、2560×1440、non-debug 的 15 份历史主菜单截图冻结的像素探针。探针覆盖左侧菜单、
  按钮边框与背景；模态变暗或页面替换必须令分类变为 `unknown`。

书签页使用限定区域内的【选择初始日期和角色】、中央【公爵弗拉季斯拉夫】与下方【公爵罗贝尔】三枚锚。
历史转场淡化帧可能同时残留主菜单文字和书签内容，应保持 `unknown`，直到两帧稳定；教程欢迎框或暗色空白模态也
不能仅凭背景里的【公爵罗贝尔】判成大厅。

书签页还冻结了三枚 `20×20` 羊皮纸/界面像素探针，RGB 每通道容差为 ±9。其来源是本机验收 artifact 中被合约生成时
选取为稳定大厅的 377 张历史截图（`03_start_enabled.png` 187 张、`03_ruler_selected.png` 190 张），覆盖 190 个 artifact
父目录。去重父目录清单的 SHA-256 为
`48936aa1d19a50e7b8c3d26a8d86ea25f7ad023c42f205711766f0114acfaf0b`，377 个相对 artifact 路径清单的 SHA-256 为
`56f09a76539e0e5f2642eeaab11c519d6d5e1c6866364cbf76b8feb345a1d66e`。两份清单都以
`%LOCALAPPDATA%\Temp\opencode` 为根，把 POSIX 相对路径按 Python Unicode 顺序排序，使用 UTF-8、每行一个条目并保留末尾 LF；
父目录清单先去重，artifact 清单不去重。
三个矩形分别是 `(1050,350)-(1070,370)`、`(950,1000)-(970,1020)` 与 `(1200,850)-(1220,870)`。它们在 190 张
`02_bookmark.png` 转场/遮挡候选中只放过 4 张，人工与 OCR 复核均为真实稳定大厅。源截图集合没有入库，当前仓库不能独立
重建“377 张均稳定”的筛选过程；配置只冻结计数、摘要、阈值和来源规则，因此这仍不是本轮真实 `menu-smoke` 证据。

## 首次真实运行证据（2026-08-22）

提交 `226d80e` 先在环境 SHA-256
`219c77d9d5e8b7e50e32314f2f8fcb57130fedc3c853880677e4149c425556ba` 下取得普通 smoke
`20260822T005515Z-03f296c7` 与 post-resume crash-smoke
`20260822T005727Z-crash-38023ffc` 两项 GREEN，随后才运行第一次真实菜单竖切
`20260822T010001Z-menu-193c8062`。该次运行在识别或输入前发现 CK3 已失去前台，以
`bound CK3 client lost foreground; refusing input` 安全 RED 结束：主链中没有任何 `ui_*` 事件，artifact 中没有 action
receipt，也没有鼠标移动、`SendInput` 或游戏点击。tracked shutdown、全局 CK3 空清点、protected postflight 与 production
tree 复核均完成。这证明前台门禁确实阻止了误点，但不证明菜单导航成功，也不允许用同一候选直接重试。

该不可变 RED 还暴露了两种跨 Windows API 的证据编码差异：COM WMI 把创建时间写成带本地偏移的 DMTF
`20260822090033.870978+480`，PowerShell CIM 清点把同一时刻写成 UTC ISO
`2026-08-22T01:00:33.8709780Z`；`runtime_dlc_mounts` 则保持 debug log 的引擎出现顺序，并非字典序集合。当前 validator
严格解析两种时间后比较同一 UTC 时刻，并对 DLC mount 保留原顺序、要求绝对路径、白名单成员和不重复。修订后旧 RED
可以原样公开回放；它没有被改写成 GREEN。由于这些修订改变 runtime 指纹，旧 ordinary/crash 资格也不能用于下一次尝试。

## 一次性前台与输入协议

唯一窗口出现后，前台获取本身也是一次性事务。场景先向主 `events.jsonl` 持久写入
`foreground_activation_planned -> foreground_activation_armed`，再只允许一次直接 `SetForegroundWindow(exact_hwnd)`；
若 Windows 前台锁仍拒绝，只允许一次把 caller thread attach 到两次稳定采样到的当前 foreground thread，重新认证目标
PID/TID/HWND 后再调用一次 `SetForegroundWindow`，并在 `finally` 中强制验证同一线程对 detach 成功。成功时写入
`foreground_activation_finished`，绑定前后 HWND/PID/TID、模式、detach 结果和采样 tick；不使用 Alt、PyAutoGUI、鼠标或
`SendInput`。attach、detach、身份、前台后置条件或采样 tick 任一未知都直接结束本局，绝不循环抢焦或再次 attach。
`GetLastInputInfo` 的 tick 相等只记录“两个采样值未变”，不证明期间没有人类输入。

每个 run 只有一个不可恢复的输入预算。成功签发 token 后，一旦动作被接受，无论之后是在鼠标移动前拒绝、
SendInput 部分失败，还是后置状态超时，都不得再签发或执行第二个动作。

输入顺序为：

1. 复核冻结环境、单 mod attestation、pinned CK3 进程、唯一窗口、固定 client rect、已完成且可回放的前台事务和无遮挡。
2. 保存两帧 `main_menu` 及 OCR/观察证据，生成只对该 session、frame、bbox 和 control 语义有效的短期 token。
3. 重新采集 fresh frame、重放分类并重新定位目标；此阶段仍未移动鼠标。若屏幕、控件唯一性或无遮挡条件变化，立即以
   零输入 RED 结束。
4. 在任何合成焦点键、鼠标移动或点击前，向主 run `events.jsonl` 追加并 `fsync` 一次 `ui_input_armed`；这才是
   输入 write-ahead log，JSON receipt 只是派生视图。随后才移动到目标、等待 hover，再采集并复核。禁止用 Alt 等额外合成键抢焦点；
   若 CK3 已失去前台则直接 RED。
5. 在内存中保存 hover target patch。最终临界区只允许：快速重截同一 patch、逐字节哈希比较、foreground /
   client / cursor / `WindowFromPoint` 复核、monotonic TTL 复核、一次 Win32 `SendInput` 批次提交
   `LEFTDOWN+LEFTUP`。其间不得 OCR、sleep 或写盘。
6. 输入后不发送任何恢复键，只等待两帧 `bookmark_lobby`。未知或超时记录
   `failed_after_possible_input`，随后进入受控清理。

进程路径信任根是启动时保留的精确进程句柄及其 `image_path()`。WMI 必须继续精确匹配 PID、创建时间、名称与
父进程；`ExecutablePath` 非空时还必须匹配，空值只表示该 WMI 字段不可用，不能把整体身份退化为 PID-only。

2026-08-22 的无 CK3 Win32 helper 实测还发现，桌面 `EnumWindows` 可能返回多个 `IsWindowVisible`、位于
`(0,0)` 且尺寸恰为 `1×1` 的 ghost HWND。若把它们一概当作相交遮挡，正常的全屏前台窗口会被误判为 RED。
实现只忽略宽、高均不超过 1 像素的这种对象；同轮创建的 `180×120` topmost 遮挡仍被拒绝，最终目标点还必须由
`WindowFromPoint` 精确命中绑定的 PID/HWND。这个结论只来自无害 helper 的本机桌面实测，不冒充 CK3 实机结论。
同一 helper 还实测到 Windows foreground-lock 会偶发拒绝新建 overlay 的 `SetForegroundWindow`。夹具因此记录实际
foreground 结果而不把抢焦点当作就绪条件；无论 overlay 是否成为前台，独立 Z-order 遮挡反证都必须拒绝目标像素。

## 生命周期与证据

`menu-smoke` 使用 sealed lifecycle，场景回调没有启动、终止、postflight 或报告定稿权限：

```text
state lock + game launch lock
  -> verify frozen environment / production / rules / UI contract
  -> replay and archive same-environment ordinary + crash qualification
  -> protected-before + provisional RED report
  -> tracked launch + singleton-mod runtime attestation
  -> ui_bound
  -> durable foreground planned / armed
  -> one direct activation + at most one exact attach/detach fallback
  -> foreground finished attestation
  -> two-frame main_menu
  -> ui_action_planned
  -> durable ui_input_armed
  -> exactly one SendInput batch
  -> two-frame bookmark_lobby
  -> tracked stop + Job/watchdog/control/global-empty conjunction
  -> protected / production postflight only when cleanup_proven=true
  -> report-body-bound final event and atomic final report
```

GREEN 报告至少绑定：固定 UI 合约的来源、environment 记录哈希与归档哈希；前后各两帧 PNG、OCR、观察 JSON
及递增采集序号；PID / creation / exe / HWND / rect；唯一 confirmed action receipt；目标 bbox、client/screen
中心、hover/final patch、SendInput 接受数；主 `events.jsonl` 的 WAL 与 tail；load、shutdown、全局清点、protected 与 production
证据。专用公开 validator 必须逐项复算；普通 `validate_smoke_report()` 的无密钥事件链/定稿检查不能替代它。

所有哈希链均是无密钥的一致性链，只证明当前归档在同一 validator、仓库与 OCR runtime 下满足 schema 与内部关系，
不证明历史执行真实性，也不是跨机数字签名。

## 首次真实点击前门禁

1. 合约漂移、模态/遮罩、两帧丢失/换序、重复动作、部分 SendInput、超时、异步中断、cleanup 未证明与 artifact
   篡改的离线负例全部 GREEN（即正确 fail closed）。
2. 无害 Win32 helper-window 实测 96 DPI 下 client→screen 换算、foreground / Z-order / overlay 抢占反证、
   WMI 空 `ExecutablePath` 的句柄信任，以及唯一一次两记录 SendInput 只抵达认证目标。
3. 提交代码，重新 `prepare-profile`；由于 runtime 指纹变化，旧 ordinary/crash GREEN 不资格化新候选。
4. 同一新 environment 下重新通过 ordinary smoke 与 post-resume crash-smoke。
5. 才允许执行一次真实 `menu-smoke`。首次如果出现教程或未知模态，应保存 RED 证据并停止，不得盲点【取消】、
   【继续】或【开始】。
