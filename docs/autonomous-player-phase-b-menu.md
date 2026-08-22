# 自主玩家 Phase B：主菜单到书签页

## 范围与成功声明

Phase B 的第一个实机竖切只允许一次玩家可见输入：在 CK3 主菜单点击【新游戏】，随后确认连续两帧稳定的
书签选择页并退出。成功报告只能声明：

```text
acceptance_claim = visible_main_menu_to_bookmark_lobby_only
valid_score_episode = false
growth100_lobby_adoption_proven = false
```

`menu-smoke` 本身不选择角色、不打开规则页、不点击大厅【开始】，也不证明 Growth+100 已被大厅采用。任何未知窗口、遮罩、
OCR 歧义、焦点变化、进程身份变化或后置状态超时都会终止尝试；已经进入可能输入窗口后不得重试。

功能性 `opening-smoke` 已在该底座之上扩展为七动作开局。2026-08-22 的 GREEN
`20260822T102802Z-opening-4cc459ce` 已真实完成【新游戏】→1066 罗贝尔→【开始】→接受契约→开始此生→
首轮祝福→首轮咒痕；七份收据的 `SendInput.accepted` 均为 2，最终双帧确认 `map_hud`，退出后 CK3 inventory 为空。
本轮选择【兵棋的余局（+500军事经验）】与【千面的哑剧（-1000谋略经验）】，形成首个可计分开局基线。

随后提交 `106278f`、环境 `f11b248ccc09bb80b5a9d92f0b9e3bc19646af333d21ccd0961183d583c09cbe` 的 GREEN
`20260822T111130Z-opening-a27391b9` 在相同七动作后，从地图 HUD 点击玩家头像并双帧确认 `player_character`。
第八份收据同样为 `SendInput.accepted=2`；可见 OCR 读出罗贝尔本人、配偶、玩家继承人与 7 名臣属，随后完整清理 CK3。
该结果把 Phase B 从“进入地图”推进到第一条真实地图内状态读取；下一步根据状态执行角色发展或宫廷治理动作。

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

## 真实运行证据（2026-08-22）

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

加固提交 `af3df58` 重新准备的环境为
`31e68f6d8e439643a7ff8fcb6029d72f93a85ead2d74bb58d24042c382753f72`。同环境 ordinary
`20260822T020912Z-7dc8269d` 与 post-resume crash `20260822T021144Z-crash-b010d18c` 均 GREEN；随后且仅随后执行的
`20260822T021436Z-menu-c9b3d667` 在主菜单观察前检测到 HWND `45219986` 以矩形
`(2130,1095)-(2560,1392)` 覆盖 CK3 客户区，按协议 RED 并停止。公开 validator 原样接受该 RED：事件链没有
`visible_main_menu_attested` 或任何 `ui_*`，外层本 run 自身的 `artifacts/` 没有 observation/action/patch/receipt；foreground 为
`already_foreground`、`attached_fallback=false`、`synthetic_input=false`，所以本次连 `SetForegroundWindow`/attach 都未执行，更没有
鼠标或 `SendInput`。tracked Job、watchdog、control、双源 inventory、protected storage 与 production tree 均完成退出后证明。

运行结束后的只读活体查询发现该窗口仍存在，title=`AlertWindow`、class=`HwndWrapper[...]`、`WS_EX_TOPMOST=true`，进程为
Kaspersky `avpui.exe`，句柄查询到路径 `C:\Program Files (x86)\Kaspersky Lab\Kaspersky Internet Security 21.3\avpui.exe`。
这些产品身份没有被不可变 run 归档；原报告只绑定 HWND 与矩形，因此它们只能作为高置信事故诊断，不能冒充历史验签字段。
自主玩家仍不得自动操作任意安全软件对话框；但用户已持续授权自动关闭右下角 Windows/Chrome/其他 Toast，且不得点击通知正文。
`opening-smoke` 实机期间应直接保持 Chrome 退出，避免浏览器通知或窗口抢占 CK3 前台。

提交 `38fd5fa` 引入 ordinary format v2 后，环境
`75f8c6b0271d82183ba2d345a48e4a191e36ea2fd85d98b9a8d30327ce6c7367` 下的 ordinary
`20260822T033531Z-9a595275` 与 crash `20260822T033759Z-crash-f289e776` 均公开回放 GREEN。唯一菜单 run
`20260822T034104Z-menu-49f9b8bd` 仍在输入前安全 RED，但时序与前一次不同：foreground activation 在
`2026-08-22T03:41:39.675959Z` 以 `already_foreground` 完成；随后两次 observation capture 的前后 foreground/unobscured guard
均通过，归档画面却是逐像素全黑且 OCR 为空；第三次 capture 的前或后 guard 才发现丢焦。主链没有
`visible_main_menu_attested`、任何 `ui_*`、bookmark、navigation、action/receipt 或 SendInput；Job、watchdog、control、双源 inventory、
protected 与 production postflight 均通过。当前归档只证明“绑定 HWND 仍有效但已不是 foreground”，没有保存实际 raw/root foreground
HWND、PID、TID 或检测 checkpoint，故不能从停机后的当前桌面反推历史抢焦者。原 run 永不重试；先增加 RED-only、只读、主链绑定的
foreground-loss snapshot，再依据新证据选择方法。

提交 `c8531be` 实现了这条 snapshot 链，并由上述 `20260822T050447Z-menu-0eae4606` 真实 RED 固定证据。loss 判定冻结同一次
raw/root foreground 样本、
`capture.pre_grab|capture.post_grab|foreground_guard|capture_patch.pre_grab|capture_patch.post_grab`、capture sequence、
UTC/monotonic、input tick、target HWND/PID/TID，以及 actual raw/root HWND、root HWND 对应的 PID/TID、class、rect、topmost；
外部进程 image/creation 只有持柄和 HWND 复核都成功才是 proven，否则为 unknown。判定前保留既有的只读 WMI/唯一窗口
认证；判定样本后的 enrichment 明确不读窗口标题、不再做 WMI/全桌面枚举，也不激活、关闭、输入、sleep 或重试。canonical snapshot artifact 先 fsync，再发布唯一 `foreground_lost` 主 WAL；
report/event/manifest/public validator 三向绑定，写入失败或孤儿证据会让 preseal 保持 provisional。旧 run 继续无回填兼容。

## 一次性前台与输入协议

唯一窗口出现后，前台获取本身也是一次性事务。场景先向主 `events.jsonl` 持久写入
`foreground_activation_planned -> foreground_activation_armed`，再只允许一次直接 `SetForegroundWindow(exact_hwnd)`；
若 Windows 前台锁仍拒绝，只允许一次把 caller thread attach 到两次稳定采样到的当前 foreground thread，重新认证目标
PID/TID/HWND 后再调用一次 `SetForegroundWindow`，并在 `finally` 中强制验证同一线程对 detach 成功。成功时写入
`foreground_activation_finished`，绑定前后 HWND/PID/TID、模式、detach 结果和采样 tick；不使用 Alt、PyAutoGUI、鼠标或
`SendInput`。attach、detach、身份、前台后置条件或采样 tick 任一未知都直接结束本局，绝不循环抢焦或再次 attach。
`GetLastInputInfo` 的 tick 相等只记录“两个采样值未变”，不证明期间没有人类输入。

真实 RED `20260822T050447Z-menu-0eae4606` 在 `capture.pre_grab` 保存到一个与目标同为全屏矩形、不同 PID、
class 精确为 `Ghost` 的前台快照；该 owner 的 `OpenProcess` 被拒，因此归档只能把进程身份记为 `unknown`，不能把它追认成
`dwm.exe`。本次还表明，activation finished 到 Ghost loss 约有 3.39 秒，短暂的 500 ms 就绪采样不足以吸收启动期
ghosting。提交 `39860a0` 因此在任何 `SetForegroundWindow` / `AttachThreadInput` 前增加纯读响应稳定门：总等待不超过 30 秒且
不得超过场景剩余 deadline；门内不做 WMI、全桌面枚举、激活、关闭或输入，只用保留的精确进程句柄、目标 HWND/PID/TID/
client rect、`GetLastInputInfo`、`SendMessageTimeoutW(WM_NULL, SMTO_BLOCK|SMTO_ABORTIFHUNG|SMTO_ERRORONEXIT)` 和
`IsHungAppWindow` 采样。`WM_NULL` 成功是主要响应证明，`IsHungAppWindow=true` 只作 veto；250 ms cadence 下必须取得一段
连续至少 5 秒的 responsive streak，任何 hung/nonresponsive 样本都会把 streak 清零。进程退出、身份/几何未知或变化、
输入 tick 变化、deadline 到期都在零窗口 mutation 下 RED。门前做一次既有完整 WMI/唯一窗口验证；门内每帧及门后只做
保留句柄与 exact HWND 的本地复核，避免无界 WMI/EnumWindows 把 5 秒证明拖成陈旧授权。confirmed streak 的相邻样本必须在
250–500 ms 内且至少 21 帧；last sample→gate finish、gate finish→每次窗口 mutation/activation completion 也都不得超过
500 ms，调度空洞会清零 streak 或在 mutation 前 fail closed。成功证据内嵌现有
`foreground_activation_finished.attestation` 并由 public validator exact replay，不增加事件种类。GREEN 必须带该证据；
新 producer 写入 `foreground_protocol_version=2`，因此新 GREEN/RED 一旦有 finished 都必须带该证据；缺少版本字段的兼容口
只钉住四份既有 finalized 零输入 RED 的 run ID 与 final-event digest，不能通过删除字段把任意新 RED 降级成 legacy。

该提交在环境 `d343278a3e2d046c7aadc2ad90d75640aadca483b3192801234f4e8a096befa2` 下取得 ordinary v2
`20260822T060233Z-be4794fb` 与 crash `20260822T060508Z-crash-123c80f3` 两项 GREEN，随后只运行一次
`20260822T060758Z-menu-fc73b5c5`。这次响应稳定门、稳定主菜单、fresh frame 与 `ui_input_armed` 均通过，鼠标移动到
`(600,558)`，hover OCR 与 patch 也匹配；但最终输入提交前 caller token 已约 5.85 秒，越过当时单一 5 秒 TTL，故以
`visible control token expired at input submission` 安全 RED。receipt 为
`pointer_input_may_have_occurred=true`、`button_click_may_have_occurred=false`、`send_input.accepted=null`；没有调用
`SendInput`，没有 LEFTDOWN/LEFTUP 或点击。Job 1→0、进程树、watchdog、四类 control 和双源 CK3 inventory 均排空，
protected baseline 与 production tree 后置复核通过。原 run/候选不可重试，它也不是书签页 GREEN。

### 分阶段输入授权

上述 RED 的根因不是画面或身份漂移，而是 caller 的 5 秒 token 错误覆盖了 fresh capture、WAL、鼠标移动与较慢的 hover OCR。
不能用扩大全局 TTL 来模糊 freshness 边界。新协议保持 caller token 的 5 秒有效期，但只在动作 admission 时消费；随后签发两份
短期内部 lease：

- `fresh_move`（执行器 purpose 为 `fresh_target_pointer_move`）从 fresh observation 的保守采集时刻起有效 5 秒，绑定
  action/control、contract、进程/窗口 binding、fresh frame、target、caller token hash 与绝对 action deadline；父授权是 caller。
- `hover_click`（执行器 purpose 为 `hover_verified_left_click_batch`）从 hover observation 的保守采集时刻起有效 5 秒，绑定
  同一 action/control、contract、binding、hover frame、target 与绝对 deadline；父授权是 fresh lease。

两份 lease 都是 HMAC 签发、一次性消费；receipt 只保存可公开复算的 claims/token SHA-256、签发/到期/消费时刻与父链。
fresh lease 在已持久化 WAL 后、移动鼠标前重新验证并消费；hover lease 在全部最终 guard 通过后、`SendInput` 前紧邻验证并消费，
两者之间不得偷渡第二次授权。动作 admission 同时固定绝对 deadline；任何截图在返回时已经越界都拒绝，后置观察只使用该 deadline
剩余时间，不能从输入完成点重新获得完整 timeout。

新 menu report 写入 `visible_action_protocol_version=2`。公开 validator 必须复算两份 claims hash、source observation/token、
target、父授权、时间关系、绝对 deadline 和 WAL 交叉绑定；新报告缺失版本化 authorization 即 RED。旧
`20260822T060758Z-menu-fc73b5c5` 仅按 run ID 与 final-event digest
`aef3dc4d0dc6bbcaf117dfaabc1d27b263309ec2f58cab5b9a14aa4ffb46396d` 固定只读兼容，不能靠删版本字段让新报告走 legacy。
这套协议尚未用于新的真实 CK3 `menu-smoke`，不得宣称实机 GREEN 或已经重试。

每个 run 只有一个不可恢复的输入预算。caller token 完成 admission 后，一旦动作被接受，无论之后是在鼠标移动前拒绝、
SendInput 部分失败，还是后置状态超时，都不得再签发或执行第二个动作。

输入顺序为：

1. 复核冻结环境、单 mod attestation、pinned CK3 进程、唯一窗口、固定 client rect、已完成且可回放的前台事务和无遮挡。
2. 保存两帧 `main_menu` 及 OCR/观察证据，生成只对该 session、frame、bbox 和 control 语义有效的 5 秒 caller token；它只
   负责 admission，不授权后续整段流水线。
3. 重新采集 fresh frame、重放分类并重新定位目标；此阶段仍未移动鼠标。若屏幕、控件唯一性或无遮挡条件变化，立即以
   零输入 RED 结束；成功则从该 fresh frame 签发绑定 target、caller 父授权和绝对 deadline 的 5 秒 fresh lease。
4. 在任何合成焦点键、鼠标移动或点击前，向主 run `events.jsonl` 追加并 `fsync` 一次 `ui_input_armed`；这才是
   输入 write-ahead log，JSON receipt 只是派生视图。随后紧邻移动前消费 fresh lease，才移动到目标、等待 hover，再采集并复核。
   禁止用 Alt 等额外合成键抢焦点；若 CK3 已失去前台则直接 RED。
5. 从 hover frame 签发以 fresh lease 为父授权的 5 秒 hover lease，并在内存中保存 hover target patch。最终临界区只允许：
   快速重截同一 patch、逐字节哈希比较、foreground / client / cursor / `WindowFromPoint` 复核、absolute deadline 与 hover lease
   复核、紧邻消费 lease、一次 Win32 `SendInput` 批次提交 `LEFTDOWN+LEFTUP`。其间不得 OCR、sleep 或写盘。
6. 输入后不发送任何恢复键，只用动作绝对 deadline 的剩余时间等待两帧 `bookmark_lobby`。未知或超时记录
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
  -> pre-mutation WM_NULL responsive stability (continuous >=5s, deadline-bounded)
  -> one direct activation + at most one exact attach/detach fallback
  -> foreground finished attestation
  -> two-frame main_menu
  -> ui_action_planned
  -> caller-token admission + absolute action deadline
  -> fresh frame + fresh_move lease
  -> durable ui_input_armed
  -> consume fresh_move lease + pointer move
  -> hover frame + hover_click lease
  -> consume hover_click lease + exactly one SendInput batch
  -> two-frame bookmark_lobby within remaining deadline
  -> tracked stop + Job/watchdog/control/global-empty conjunction
  -> protected / production postflight only when cleanup_proven=true
  -> report-body-bound final event and atomic final report
```

GREEN 报告至少绑定：固定 UI 合约的来源、environment 记录哈希与归档哈希；前后各两帧 PNG、OCR、观察 JSON
及递增采集序号；PID / creation / exe / HWND / rect；唯一 confirmed action receipt；版本化 caller/fresh/hover authorization、
父链与绝对 deadline；目标 bbox、client/screen 中心、hover/final patch、SendInput 接受数；主 `events.jsonl` 的 WAL 与 tail；
load、shutdown、全局清点、protected 与 production
证据。专用公开 validator 必须逐项复算；历史 format v1 `validate_smoke_report()` 只有无密钥事件链/定稿检查，不能替代它。
format v2 ordinary validator 虽已能自包含重放可见主菜单、加载、诊断、进程清理、protected 与 production 证明，但仍不验证本场景的
foreground、UI WAL、像素 patch、单次 SendInput 和书签页后置条件，因此也不能替代 menu validator。

所有哈希链均是无密钥的一致性链，只证明当前归档在同一 validator、仓库与 OCR runtime 下满足 schema 与内部关系，
不证明历史执行真实性，也不是跨机数字签名。

## 下一次真实点击提交前门禁

1. 合约漂移、模态/遮罩、两帧丢失/换序、重复动作、部分 SendInput、超时、异步中断、cleanup 未证明与 artifact
   篡改的离线负例全部 GREEN（即正确 fail closed）。
2. 无害 Win32 helper-window 实测 96 DPI 下 client→screen 换算、foreground / Z-order / overlay 抢占反证、
   WMI 空 `ExecutablePath` 的句柄信任，以及唯一一次两记录 SendInput 只抵达认证目标。
3. 提交分阶段授权代码，重新 `prepare-profile`；由于 runtime 指纹变化，旧 ordinary/crash GREEN 不资格化新候选。
4. 同一新 environment 下重新通过 ordinary smoke 与 post-resume crash-smoke。
5. 才允许执行一次新的真实 `menu-smoke`。如果出现教程、未知模态或授权过期，应保存 RED 证据并停止，不得盲点【取消】、
   【继续】或【开始】。
