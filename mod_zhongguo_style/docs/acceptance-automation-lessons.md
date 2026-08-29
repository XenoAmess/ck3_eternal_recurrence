# CK3 桌面自动化经验与教训账本

本文记录 `mod_zhongguo_style` 实机验收、GUI 阻塞审计和宣传片采集过程中已经被真实运行证据确认的经验。它是后续同类 CK3 任务的操作记忆；新发现必须当场追加，不能只留在聊天、日志或某次失败 runner 里。

最后更新：2026-08-30（Asia/Shanghai）。

## 1. 永久工作规则

1. 自动化期间保持系统当前前台应用和 CK3 使用 **US English** 键盘布局；目标 HKL 必须精确等于 `0x04090409`。不要在任务结束时切回微软拼音，也不要删除系统中已有的中文输入法。
2. “发出了按键/点击”只是意图，不是游戏收到动作的证据。每个关键动作必须有 OCR、窗口状态、日期、日志 marker 或地图像素差等独立 ACK。
3. 局部 UI 探针失败先在同一 CK3 进程内走有界兜底；只有入口全部耗尽或无法恢复干净 HUD 才结束本轮。不要为十秒级相机/菜单问题反复重启完整 361 链。
4. 玩法验收、GUI 审计、真实角色 provenance、宣传片片场分别记账。后者 RED 不抹掉前者已经签过的产品证据，前者 GREEN 也不能冒充宣传片就绪。
5. FFmpeg 只能在史实角色、宋境镜头、原生右窗已关、测试 UI 为零、系统通知为零的全部录制前门禁通过之后启动。
6. 失败 artifact、完整一次性 `_userdir`、日志、截图、sidecar 和失败录像全部保留；不得为了“目录干净”删除可复盘证据。

## 2. 输入法事故：Shift 不是键盘布局切换

### 已观察现象

- `runs/zga_camera_retry_20260829_2048_5bc23c9`：裸 `V` 没有打开 CK3 的“查找头衔”，右下角出现微软拼音“V模式输入”候选层。CK3 没收到 `find_title_shortcut`。
- `runs/zga_camera_ime_20260829_2100_3b8c7d5`：`Escape → Shift → V` 清掉了候选层，但仍未打开“查找头衔”。这只能证明微软拼音内部状态变化，不能证明 CK3 的窗口线程已经改用英文布局，也不能证明第二个 `V` 送达游戏。
- 本机枚举出的已安装布局为 US English `0x04090409` 和 Microsoft Pinyin `0x08040804`。2026-08-29 21 时后的前台窗口已从 `0x08040804` 精确切换到 `0x04090409`，并按项目所有者要求保持英文。
- Windows 会按窗口/线程保留输入状态：把 Chrome 切成 `0x04090409` 后，切回另一个前台应用仍实测为 `0x08040804`。所以“系统刚才已经切过英文”不能替代对每个新 CK3 窗口线程重新签 HKL；当前实际前台应用也已再次切到并保持 `0x04090409`。
- 当时 `Get-WinDefaultInputMethodOverride` 返回空值。依项目所有者“始终保持英文、不切回”的明确要求，已执行 `Set-WinDefaultInputMethodOverride -InputTip '0409:00000409'`；复读结果为 `English (United States) - US`，当前前台线程也再次精确验证为 `0x04090409`。中文输入法仍在已安装列表中，没有被删除。系统默认覆盖只减少新窗口回到拼音的概率，CK3 runner 仍必须逐窗口做线程级 gate。

该系统状态的外部过程证据保存在 `Z:\ck3_mod_rewrite_process_assets\zg361\input-method-policy-20260829.json`，SHA-256 为 `109524BAC6435AEEE370B2C6218C73B2C2E786DE88E67D5EAD7AE9FF7AC53E05`。

微软文档也把 Shift 描述为微软拼音内部“中文/英文输入模式”的切换；这和把目标窗口线程从中文 HKL 切到 US English HKL 不是同一层状态。参考：[Simplified Chinese IME](https://learn.microsoft.com/en-us/globalization/input/simplified-chinese-ime)、[WM_INPUTLANGCHANGEREQUEST](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-inputlangchangerequest)、[GetKeyboardLayout](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getkeyboardlayout)。

### 三层状态必须分开

| 层 | 正确观测 | 不能接受的替代证据 |
|---|---|---|
| Windows 输入布局 | 对目标输入线程调用 `GetKeyboardLayout(thread_id)`，完整 HKL 等于 `0x04090409` | 任务栏图标、候选框消失、按过 Shift |
| CK3 是否收到快捷键 | 右侧原生窗口标题稳定 OCR 到“查找头衔” | `pyautogui.press("v")` 已返回、窗口像素有轻微变化 |
| 目标动作是否执行 | 右键前后在相同 finder 状态下，中央地图变化率至少 `0.18` | 菜单关闭、鼠标落在了结果行、调用了 click handler 名称 |

### 固化实现

`tools/run_zhongguo_acceptance.py` 的输入布局 gate 必须执行以下完整过程：

1. `focus_ck3()` 后读取前台顶层 HWND，并核对窗口标题、PID 与 runner 跟踪的 CK3 PID。
2. 由顶层窗口线程调用 `GetGUIThreadInfo`；若 `hwndFocus` 属于同一 CK3 PID，就把它作为输入窗口和输入线程，否则使用顶层 HWND。
3. 用 `GetKeyboardLayoutList` 证明精确 US English HKL `0x04090409` 已安装。
4. 若目标线程不是该 HKL，向焦点窗口 `PostMessageW(WM_INPUTLANGCHANGEREQUEST, 0, 0x04090409)`。Windows 文档明确该消息应投递给有焦点的窗口；post 返回值只说明消息已入队，不是状态成功证明。
5. 轮询目标输入线程的 `GetKeyboardLayout`，必须看到完整值 `0x04090409`；同时再次确认 CK3 仍是前台窗口。
6. sidecar 记录顶层/焦点 HWND、PID、线程 ID、安装列表、切换前后 HKL、轮询样本和 `restore_requested=false` / `restore_performed=false`。
7. 不恢复中文布局。若无法得到精确 HKL ACK，跳过字母快捷键并把输入 gate 判 RED。

不要使用 Shift、Win+Space、托盘图标颜色或 IME overlay 消失来替代以上 gate。也不要用 `ActivateKeyboardLayout` 只改 runner 自己的线程，然后声称 CK3 已切换。

## 3. 标题查找与相机定位

### 已证伪路径

- Home 和原生“转到首都”在切换到赵曙后的当前角色上下文中连续多次没有显著移动地图。它们的无效不代表产品玩法失败。
- 原生“更多”菜单带 `_mouse_hierarchy_leave` 行为；菜单文字被 OCR 到不代表随后较慢的鼠标移动仍点中了该行。
- OCR/键鼠只获项目所有者授权用于当前宣传片临时兼容路径。正规终态是 MCP 夹具按 stable landed-title key 解析并定位地图；能力合同见根知识库 `docs/ck3-native-title-map-navigation-contract.md`。该合同当前仅为 `research`，不得把本轮 OCR GREEN 冒充 MCP 已实现。
- 菜单消失不构成 handler ACK。必须观察目标窗口或地图的后置状态。
- “查找头衔”在同一面板里既可能是标题，也可能是空搜索框的 placeholder。实机 OCR 返回的是输入框中心 `(2164,226)`；再机械加 65 像素会点到空白面板、把自动获得的输入焦点夺走，随后 `Ctrl+V` 看似执行但搜索框仍为空。任何输入框定位都必须保存粘贴后的文字 ACK，不能从窗口标题坐标盲推。
- 实机 runner 会校验源码树前后哈希。运行期间即使是另一个合法子线程新增设计 JSON，也会让整局报告出现 `source_tree_unchanged=false`；因此每次 CK3 启动前必须冻结待测字节，并暂停所有会写同一源码树的并行任务。并发只留给只读研究或外部独立 worktree。

### 当前有界状态机

1. 保存 Home 前后帧并计算中央地图差；差值达标则结束。
2. 在 CK3 输入线程已经精确签为 US English 后只发一次 `V`，要求右上角“查找头衔”标题出现。
3. 若没有标题，清场后在同一进程走鼠标兜底：hover 原生“更多”并 OCR tooltip；打开菜单，在下方菜单区 OCR“查找头衔”，点击 OCR 中心，再次要求右上角标题出现。
4. 2560×1440、1.30 UI scale 的实机参考：更多按钮约 `(1807,1417)`；菜单中“查找头衔”约 `(1820,1176)`。坐标只是候选，tooltip/文字 ACK 才是语义定位。
5. 搜索“汴州”，两帧稳定解析结果后右键；若结果缺失或动作没有地图 ACK，在同一个 finder 中尝试史实首府“开封”。
6. 每个右键动作保存 action-before / action-after；只有中央地图差至少 `0.18` 才接受。
7. 关闭 finder，并反证标题消失；再确认 CK3 仍保持 `0x04090409`。整个过程的 `attempts[]` 无论 GREEN/RED 都写入 `05_promo_camera_recenter.json`。

2026-08-29 末，项目所有者将正规路径优先级提升到 MCP。上述 OCR 状态机继续保留为历史兼容与故障取证，不再作为正式宣传片导航的首选施工方向；下一次实机优先验收合同中的 typed title-key 原生动作。

## 4. GUI 自动化经验

- CK3 GUI unit 会被 UI scale 放大。源码坐标不能直接当屏幕像素；候选点必须先用 tooltip 或唯一文字反证。
- 原生右侧栏的按钮位置会随玩家角色和已存在入口数量变化。固定坐标曾把“决议”误点成“派系”；能用原生快捷键或 OCR 扫描时，不依赖旧角色截图坐标。
- `Escape` 可能先关闭 tooltip、组合输入或子层，而不是目标窗口。关闭动作要连续观察目标标题缺失；必要时再点原生标题栏 X。
- 反过来也不能把 Escape 当通用“清场键”：当 `V` 没有打开 finder、OCR 又确认没有 IME 候选层时，干净地图上的 Escape 会打开暂停菜单，反而遮住底部“更多”兜底。现在只有 `ime_v_mode_visible=true` 才用 Escape 清组合输入；More 重试之间仅把鼠标移出瞬态 flyout。
- 新增 GUI 按钮必须做阻塞审计：正常 HUD 可点、原生右窗打开时隐藏/抑制、模态叠层不穿透、标题 X 与 backdrop 行为正确、人物链接打开原生人物页后能关闭并重开。
- 同构生成行只实点一条时，只能声称“1 条 L3 实点 + 其余静态同构”，不能把 160 条同构行都写成实机点击通过。
- 数字字段不能用全屏字符串集合判唯一。`zga_20260830_0156_current_fa2f684_mcp` 的上司告身正确显示“你的绩效：3.25”，但顶栏资源增量同时出现 `+3.5`，旧门禁遂误报两个档位。现在档位断言只读取告身正文的归一化小区域，要求同帧出现“你的绩效 + 3.25”并排除另外两档；全屏 OCR 仍用于标题、KPI、位次和 raw-key 检查。界面上合法重复同一值也不应被当作重复结果。

## 5. 时间推进与事件转场

- 事件选项 click 后可能发生异步 activity-detail 转场；紧跟 mouse-up 的 Space 可能被吞。
- 暂停是否成功只能用 HUD 日期冻结和相关 marker 尚未到期共同证明。后续自动暂停事件出现时，不能倒推之前的 Space 生效。
- 降速按键、暂停按键、原生时间轴点击都要各自有后置日期 ACK。慢 OCR 本身会消耗游戏时间，不能放在关键截止日之前无限等待。
- carrier 到期日必须为失败兜底留足同年缓冲；这属于验收夹具编排，不得修改产品的 D+300 京察期限或其他正式规则来迁就 harness。
- classic character event 的模态停表不能等同于 native snapshot 的普通 `paused=true`。2026-08-30 04:15 attempt 直接证明 `set-speed-1` 已获 `accepted/submitted` 且 `dedicated_server.log` 执行了原生零基速度 `0`，但旧 runner 等待 `speed=1 && paused=true` 仍超时；该次失败循环没有落盘 snapshot，因此 `paused=false` 只能作为强推断，不能写成直接观测。正确交接是：点击前用同一 native event instance、`date_raw`、played character 和命令 ACK 绑定上下文，速度/暂停字段只记录；点击后先看到 event instance 在同日发生变化，只有 changed-event 帧为 running 时才提交 `pause-map`，若已经暂停则禁止反向 toggle，最后以连续三帧 `paused=true` 且日期仍等于点击前日期收口。任何 RED 都应先写 observations sidecar 再抛异常。

## 6. 宣传片片场纪律

- 唯一测试决议只允许出现在 FFmpeg 启动前的验收截图；原生决议抽屉必须被关闭并有连续缺失 ACK。
- 连续主角只能来自史实赵曙和冻结白名单中的史实公爵及以上天朝制领主；史实伯爵只作为被考核对象，生成坊正不能进入宣传身份。
- 每个 clean span 都要做全屏 OCR 禁词检查，并保留 begin/end 帧。系统 Toast 遮挡也会使素材作废。
- 冷启动/loading、测试标签、fixture 文案、测试决议、生成角色和 RED 轮次录像不得进入正式 release manifest。
- 片场 gate 通过前不启动 FFmpeg；这样一次十秒探针失败不会制造可误用的长录像。

## 7. 批量验收组织

- **交付优先，禁止重复审计**：同一候选、同一问题如果已经有权威清单和证据结论，不得再派生同类审计或重写第二份矩阵。代码没有变化时不重复跑同一静态门；只有新的明确 RED 证据才能触发针对性复盘。默认顺序是最小修复 → 当前候选合批实机 → 发布物料 → 上传后新鲜缓存复验，而不是继续扩展审计范围。
- 先用短探针闭合输入、镜头和干净 HUD，再启动一次完整的 361/361 + GUI + 宣传采集链。
- 完整链中把静态 L0、361 唯一 marker/幂等性、GUI 阻塞、京察时间线、本人受评、政策卡和素材 capture marks 合批验收，避免为每个机制单独启动 CK3。
- 每轮报告要区分 `product GREEN / harness RED / promo not started`。相机脚本 RED 不能写成“361 机制失败”。
- 同一小状态的失败最多做有界回退；每条回退都必须有独立 ACK 和 `attempts[]` 记录，不能用无限重试掩盖不确定性。

## 8. 新经验的落盘模板

后续每次新增条目至少记录：

- 日期、提交、run 路径；
- 观察到的现象与稳定复现条件；
- 能证明事实的截图/日志/JSON SHA-256；
- 已排除什么，哪些仍未查明；
- 最小修复及其可执行回归测试；
- 产品 readiness 是否变化，还是仅 harness/片场变化；
- 是否需要在下一次完整 CK3 启动前先闭合。

只记录证据支持的事实。推测若仍有必要保留，必须明确标为“未查明”，并给出下一项可执行的观测入口。
