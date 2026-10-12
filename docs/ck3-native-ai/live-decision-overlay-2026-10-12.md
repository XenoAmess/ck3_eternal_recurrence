# 罗贝尔实机演示：实时决策悬浮窗（2026-10-12）

用户要求在游戏窗口上展示自动游玩如何决定开战，而不是只展示地图变化。当前演示已启动真实 Windows 悬浮窗，使用本局 SDK 文件队列的请求、规划和返回结果，每 350 ms 更新。源代码是 [实时数据展示](../../tools/g2_saved_campaign/live_decision_overlay.py) 与 [原生窗口](../../tools/g2_saved_campaign/decision_overlay_window.py)。它不创建另一个 Driver、不查询游戏管道，也不执行游戏输入。

显示内容包括当前计划、实际步骤结果、宣战决策及独立读回的战争身份、决策理由、最近三条记录、尚未解决的军力查询失败。计划与提交不会显示为战斗胜利；存档只有返回文件回执 `checkpoint.status=saved` 才显示已确认。宣战战争 ID 要同时关联对手、攻击方与目标头衔，并且只有唯一匹配且动作已接受才显示已读回。

战前综合军力比较与简化推演直接来自实际宣战规划。本局向锡拉库萨宣战前，综合军力约为目标的 2.53 倍，256 次简化推演中 252 次占优；窗中标明这是战前估计、不代表战果。它没有将这组模型数据解释为士兵数量或经过校准的获胜概率。角色与地名标签是启动时显式提供的演示说明，原生目标 ID 与战争回执仍来自真实规划。

2026-10-12 更正：Root 早期将目标角色 `33026` 错标为那不勒斯。实际当前安装文件、原生居中回执和像素现场确定战争目标省份 `2638` 为 `b_syracusa` / `c_siracusa`，当前游戏简中名为锡拉库萨。旧截图与启动参数原件仍保留，不能将其中地名作为已核验事实。回执 `073-actual-hotspot-camera.json` 与新截图 `11-actual-hotspot-camera.png` 提供更正证据。

## 本次实际显示

外置现场目录：

```text
D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/fresh-robert-demo-20261012/attempt04-full-capability
```

第一段游戏 PID `141860`，创建身份 `20261012104318.530236+000`，FILETIME `134362753985302361`。新鲜 1066 罗贝尔开局已向目标角色 `33026` 宣战，读回战争 `4`，已召集部队。实际请求 `041-ck3_auto_turn.json` 的军力查询失败：原生帧 `70,335,967` 字节超过原有 `67,108,864` 字节上限。失败没有被悬浮窗掩盖；后续 `043-next-real-plan.json` 虽已给出下一项规划，未解决失败仍持续显示。本记录不宣布战争能力验收或战斗胜利。

后续从同局 9 月 22 日存档正常恢复到 PID `191588`。`048-resumed-full-auto.json` 的真实军力查询返回 `accepted=true/status=available`，三支军队 `18/16777230/24` 各读回 `1204/799/1623` 人，原超限提示只在该成功结果出现后清除。不是把读文件时的半写入 JSON 错误当成新的游戏失败；当前控制器等待完整结果解析后才继续。窗口当前继续追踪本局请求，不将恢复后的 episode ID 变化解释为自然继承。

`042-preserve-full-day7.json` 实际保存了 1066 年 9 月 22 日局面：`68,704,884` 字节，SHA-256 `a5bcc588bf7a3058e9c3757a1162bd66f815b6955713e7526eee927cabbb7526`。这仍是本次从头开始的完整规划局；历史 nonwar-only 的 990 天不计入此局。

Root 亲自审阅原始截图 `05-native-decision-overlay-complete.png`，原始桌面与截图均为 `2560×1440`：左上窗、中文完整换行、规划与结果、宣战依据和阻点均可见。新原生窗口启动回执 `ROOT-DECISION-OVERLAY-90048-STARTED.json` 的前台 HWND 在启动前后均为 `14877498`，悬浮窗 HWND `6762690`，扩展样式实际读回 `134742184`。早期 Tk 实例曾抢焦点，已实际退出并改为原生窗口；旧回执原样保存。

原生窗口创建前即设置 `WS_EX_NOACTIVATE`、分层透明与鼠标穿透样式，并用 `SW_SHOWNOACTIVATE` 显示。没有为验证穿透而合成鼠标或键盘输入；本记录的现场验收范围为真实显示、真实来源与启动前台身份保持。字体宽度由 GDI 实际测量，按 UTF-16 单元计数，避免长中文在右侧被截断。

## 后续复用与边界

传入本局目录与显示标签即可启动。目录须有真实 `ROOT-ACTUAL-GAME-LAUNCH.json`、`requests/` 与 `responses/`；标签不能代替原生身份验证。窗口用查询权限持有游戏进程句柄并核对创建时间，避免 PID 复用；游戏退出或创建 `STOP-DECISION-OVERLAY` 时关闭。每个窗口进程保存独立启动/关闭回执。

```text
tools/.venv/Scripts/python.exe -X utf8 tools/g2_saved_campaign/live_decision_overlay.py --session <actual-session> --campaign-label 1066罗贝尔·完整规划 --target-label 33026=锡拉库萨
```

控制器应先提交 `ck3_plan_turn` 显示真实前瞻规划，再提交普通 `ck3_auto_turn`。后者仍独立重规划，实际动作以它的返回为准，不能假定预览与动作一定一致。悬浮窗从不为演示制造规划或虚构结果，也不绕过普通动作的原生前置门槛。

源审阅与真实窗口运行属于本次交付验证；没有运行单测、模拟游戏或新增业务验收夹具。现场及原始请求仍按父 `STORAGE-ADMISSION.json` 的有限保护期限管理，当前复核期限 `2026-10-12T16:47:28.264315+00:00`；不以此文档无限期保留原始视频或截图。

## 2026-10-12：镜头主体接入、窗口边界与虚拟桌面

主体 `GameplayBridgeService.auto_turn` 现在在普通规划之前调用已有战争热点选择器，返回单独的 `camera_follow`；原 CLI runner 复用这个入口，避免 MCP 游玩绕过视频工具已有的镜头能力。热点按实际战斗、围城、己方行军及战争目标排序，地名从当前安装的 landed titles 建立映射。本轮 `077-ck3_auto_turn.json` 实际读回 `b_syracusa`、`already_centered` 和原生 `postcondition_verified=true`。这是每回合按新局面重新居中，不是永久禁止用户拖动镜头。

窗口工具 [fit_owned_game_window.py](../../tools/g2_saved_campaign/fit_owned_game_window.py) 只对启动回执绑定的 PID 与创建时间操作。实际 `ROOT-GAME-WINDOW-FITTED.json` 将超界窗口 `[-8,-31,2568,1448]` 收到本机实际显示器 `[0,0,2560,1440]`，客户区也读回 `2560×1440`。没有键鼠输入、桌面切换或前台激活。该记录证明窗口几何；失败第一次调用后取得的 `12-game-window-fitted.png` 是另一个桌面的画面，不能当成修复后 CK3 像素验收。

本机只读清点确认 Windows build `22631.6199` / 23H2（[微软版本信息](https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information)）、16 个物理核 / 32 个逻辑处理器、约 128 GB RAM 和 RTX 3080 10 GB。首次显存样本为 `9155/10240 MiB`；后续样本为 `9434/10240 MiB`。这是当时占用，不能证明两个游戏长期同时流畅。两个虚拟桌面是同一交互会话内的窗口分组，资源和输入设备没有由此分成两台机器；Windows 支持窗口桌面身份查询和移动自身窗口，不应自动切换用户桌面（[公共接口](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nn-shobjidl_core-ivirtualdesktopmanager)）。

`ROOT-VIRTUAL-DESKTOP-ASSESSMENT.json` 发现 CK3 PID `191588` 在非当前桌面、非最小化、DWM shell cloak=2，旧 TOOLWINDOW 悬浮窗却仍出现在用户当前桌面。新悬浮窗改为独立 APPWINDOW，保留 NOACTIVATE、分层和透明输入样式；先保持零透明度，公共接口只移动本进程 HWND，桌面 GUID 读回相等才恢复可见内容。失败时隐藏自身，不移动 Game，不创建跨进程 owner，也不抢前台。APPWINDOW 会增加一个任务栏入口，此副作用不隐藏。

实际 `ROOT-DECISION-OVERLAY-18304-STARTED.json` 和 `ROOT-VIRTUAL-DESKTOP-BOUND-OVERLAY-OBSERVED.json` 确认新窗 `11605986` 与 Game `12331766` 同属 `964b3ff9-3cf7-4ba9-881b-47444f31cfbe`，二者均非当前桌面且 DWM cloak=2；用户前台仍属于另一桌面。启动前后前台 HWND 都是 `1121666`。没有为此切换用户桌面或采集用户当前桌面的新截图。

摄像光标处理只有在唯一 CK3 进程、唯一实际窗口、非最小化、DWM shell cloak=2 且公共接口明确返回非当前虚拟桌面时，才返回 `skipped_other_virtual_desktop` 并继续原生镜头控制，`mouse_input=false`。一般“CK3 不在前台”、未知桌面身份和接口失败仍不移动鼠标，也不放行未经确认的摄像条件。当前桌面的前台 CK3 光标停车仍在写入前复核同一个前台 HWND。

`074-ck3_take_snapshot.json` 在约 1.7 秒内取得非当前桌面的实际地图状态，前台窗口保持；`077` 又取得后台原生镜头与战争结束条件的真实回执。随后 `079-ck3_auto_turn.json` 军力查询再次失败：原生返回 `113,153,654` 字节仍超过原有 `67,108,864` 上限。`ROOT-ACTUAL-BACKGROUND-NATIVE-PLAY-FAILURE.json` 保存实际中止原因；这轮没有取得新的日期推进、战斗获胜或持续后台渲染证明。以前 `048/056/064` 的成功不能外推为所有后续帧已经修好。

该 Game 使用 `army-wire-build01/native.dll`（SHA-256 `273caee1ef5f79e19aeac8dea670b385a5bd20d8c1af8733babfaeb91cf444bd`）：只重编 Bridge TU 并重新链接，保留前次罗贝尔相关对象，不能称为全部 TU 同源重编。两份 Army header 让已满足原六字段共享门槛的多行组，进一步共享四个“所有行都存在且完整值相同”的字段；缺失或不同的值仍逐行保留，SDK91 的已有十字段展开负责还原。没有扩大帧上限，也没有改变军力数据语义。新失败说明这一优化不够覆盖当前完整返回，需要继续修复；未以重启后的短帧夸称获得了原 70 MB 帧的精确压缩量。

当前 Python 控制器采用冻结 SDK91 commit `50a1a5451227d1b30f42394dd02ddfbaea26a1ff` 加 `camera-sdk-overlay02/ROOT-SOURCE-VARIANT.json` 的五模块有限源码变体。变体仅接入公共镜头入口、严格虚拟桌面光标保护、桌面接口和移除 MCP 对外 nonwar-only 路由，其余模块继续来自冻结 SDK。旧 SDK 实际退出后才接入同一 Game / pipe，不运行第二个 Driver 或新游戏。

后续两路纯源码审阅修正 COM ABI 清理：使用 `WinDLL` 与显式 HRESULT 返回类型，`CoUninitialize` 明确为 void，只有本次成功初始化才调用清理；保留已初始化为其他 apartment 的调用方环境。前景鼠标分支补核唯一 CK3 PID、非最小化与写入前同一前台 HWND；这两个读检查并非系统级原子输入隔离。新悬浮窗只有 Game 在当前桌面、cloak=0 且非最小化时才恢复内容透明度，隐藏调用失败则关闭自身。该审阅修正已在 `camera-sdk-overlay03/ROOT-SOURCE-VARIANT.json` 与 `camera-sdk-session02` 部署；先前 SDK 和悬浮窗实际退出后才替换，Game 始终 PID `191588`。`ROOT-VIRTUAL-DESKTOP-REVIEWED-OVERLAY-OBSERVED.json` 读回新窗 PID `136876` / HWND `4852812`，与 Game 仍同 GUID 且非当前桌面。早先 02/077 的运行证明原样保留，新修正没有获得新的日期推进或军力成功信用。

容量限制的权威定义在 [protocol.hpp](../../ck3_autonomous_player/native_bridge/include/xar_bridge/protocol.hpp) 的 `kMaximumFrameBytes = 64U * 1024U * 1024U`，Python `native_driver.MAXIMUM_FRAME_BYTES` 与读端长度准入保持配对。传输是一段 4 字节小端长度头加紧凑 UTF-8 JSON；日志 `payload_bytes` 是 JSON 本体长度，不包含这个长度头。它限制单条原生桥消息，并非 Windows、显存、模型 token 或 MCP 服务套餐限额。

三个本轮 ffmpeg 段已经实际关闭，录制因共用 6 GiB 预算到顶而停止，Game 没有被录制停止动作终止。当前未继续全桌面采集。若要后台持续录像，应另行采用只捕获 CK3 窗口的采集方案；[Windows 窗口采集 API](https://learn.microsoft.com/en-us/windows/apps/develop/media-authoring-processing/screen-capture) 的存在不能代替本机隐藏桌面 CK3 连续新帧的验证。现有演示仍无战斗胜利、自然继承或新 M6/M7 完成证据。
