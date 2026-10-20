# Steam 离线模式的无截图只读查询调研

machine_id: `xenoamess-full-tower-eb9d2c1186`  
观察窗口：2026-10-20 14:42–14:47 UTC；资料核对：2026-10-20。  
范围：网络研究、现有文件/进程/注册表只读、现有 Steam HWND 的 UI Automation 只读。未切换模式、重启 Steam、启动游戏、激活窗口、取屏或安装依赖。

**可以不截图查询 Steam 的主动离线模式。可实施的首选是客户端自身的 `App.GetCurrentUser().bIsOfflineMode`；本轮尚未取得这台机器该布尔值的实际运行时读回。** 公开 Steamworks 的 `BLoggedOn()` 不是等价接口；不能以它返回 false、网络断开或缓存偏好代替。

本机 Steam 正在运行，steam.exe PID 165096；Steam 主窗口 HWND 52505028 属于 steamwebhelper PID 142952。steam.exe、steamclient64.dll、steamwebhelper.exe 的实际文件版本均为 **10.96.30.42**。身份由 `tools/ck3_live_run_id.py machine` 实读，安装根由 HKCU SteamPath 实读；这些事实仅适用于上述机器和观察时间。

安装目录 `steamui/chunk~2dcc5aaf7.js` 实读 14,382,868 B，SHA-256 `f9606b111203c9140dcdd6fc016a0ee00e4c8406aeb786187c42873f08d071fb`，FileID `1407374883818107`，mtime_ns `1788653822000000000`，读取前后身份相同。该文件的原始字节偏移证明：

| 偏移 | 实际关系 |
|---:|---|
| 10722655 | SteamApp 注册 `SteamClient.User.RegisterForCurrentUserChanges(this.OnCurrentUserChanges)` |
| 10728126 | `OnCurrentUserChanges(e)` 将原生回调对象保存到 `m_CurrentUser`；`GetCurrentUser()` 返回它 |
| 10728958 | SteamApp 的 `BIsOfflineMode()` 返回 `this.m_CurrentUser?.bIsOfflineMode` |
| 10729000 后的同一模块 89748 | 初始化实例并赋给 `window.App` |
| 10915522 / 10915602 | 主菜单据上述值选择显示 GoOnline / GoOffline |
| 836210 | **另一个** FriendStore 的同名方法比较 PersonaState；它表示好友状态，不能使用 |

当前公开的 [CurrentUser 类型](https://jsr.io/@steamclienthomebrew/millennium/doc/~/CurrentUser) 和 [User 接口实现方声明](https://jsr.io/@steamclienthomebrew/millennium/doc/~/User)也分别包含 `bIsOfflineMode: boolean` 与该回调。它们是客户端接口的独立开源声明，并非 Valve 对外稳定 API。公开追踪的[客户端源码](https://github.com/SteamTracking/SteamTracking/blob/6b7154d1abaf484f6ef181fb4ecd2bb3cc7d3c82/ClientExtracted/steamui/sp.js)来自另一构建；本机结论以以上实际安装字节为准，不能跨版本硬套偏移。

| 路径 | 能证明什么 | 限制 |
|---|---|---|
| SteamApp 当前用户布尔值 | 客户端主动 Offline Mode 的语义状态，与主菜单同源 | 内部接口；须有可用、来源绑定的当前 CEF 执行上下文 |
| 官方 `ISteamUser::BLoggedOn()` | 此用户客户端与 Steam 服务的实时连接 | false 也可能是网络/服务器故障；不能推出主动离线 |
| UI Automation 当前 Name/菜单语义 | 若客户端暴露“离线模式”或“进入在线模式”，可无需像素读取语义 | 本机这次只暴露根窗口和四个 pane，没有该语义 |
| `loginusers.vdf: WantsOfflineMode` | 保存的启动/账户偏好 | 本机值 1；不是当前运行时证明，修改/切换/崩溃可能使缓存滞后 |
| 连接日志、注册表、TCP | 发生过的连接/退出、现有进程与监听 | 历史/配置/连通性旁证；不等于当前模式；缺少日志也不证明离线 |

Valve 对 [BLoggedOn](https://partner.steamgames.com/doc/api/ISteamUser#BLoggedOn)明确按服务连接定义，并列出本机网络问题及服务器不可用的 false 情形。[官方离线说明](https://help.steampowered.com/en/faqs/view/0E18-319B-E34B-B2C8)把 Offline Mode 作为用户选择的客户端功能。好友“离线/隐身”、未登录与此分别处理。

本机只读结果：未发现 Steam/所查 webhelper 的 CEF 调试启动参数；所查 Steam 监听为 27036、1110、1104，没有观察到 CDP 监听。此结果仅说明此次受检入口不可用，不宣称全机所有端口已扫描。14:46:58 UTC 经原生 UIAutomation COM RawViewWalker 读取当前属性，访问 5 节点、0 个离线语义；前台 HWND 前后都为 52505028，耗时约 0.202 秒。未运行 Invoke、Expand、SetFocus、点击或截图。现有 Python 环境缺少 pywinauto/comtypes，已用系统 COM 只读，不新增依赖。Microsoft 的 [ElementFromHandle](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomation-elementfromhandle) 与 [GetCurrentPropertyValue](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationelement-getcurrentpropertyvalue)分别支持 HWND 定位和当前属性读取。

建议实现一个独立只读探针，通过**已启用且绑定到该 Steam 实例**的 CEF/CDP SharedJSContext 查询，不调用 SteamAPI_Init、不注册游戏 AppID。最小 getter 如下；生产版须在外层校验对象形状、两个返回值为严格 boolean 且相等，并把异常归入 unavailable：

```javascript
(() => {
  const app = globalThis.App;
  if (!app || typeof app.GetCurrentUser !== "function" ||
      typeof app.BIsOfflineMode !== "function")
    return { status: "unavailable", reason: "no_current_context" };
  const user = app.GetCurrentUser();
  if (!user || typeof user.bIsOfflineMode !== "boolean")
    return { status: "unavailable", reason: "no_valid_current_user" };
  const value = app.BIsOfflineMode();
  if (typeof value !== "boolean" || value !== user.bIsOfflineMode)
    return { status: "unavailable", reason: "inconsistent_state" };
  return { status: "observed", offline_mode: value };
})()
```

Python 消费者用共享 TypedDict 的判别联合：`status: Literal["observed"]` 分支必须有 `offline_mode: bool`；`status: Literal["unavailable"]` 分支必须有有限 reason，**不得默认 false**。JSON 入口拒绝缺字段、null、0/1、字符串真假值及矛盾字段。回执同时绑定 machine_id、UTC、查询 nonce、Steam PID/出生时间、EXE 版本、源码 SHA、CDP target/context 身份及前后实例一致性；64 位身份/时间用十进制字符串。不把 `offline_mode=false` 写成“服务已连接”。

资格步骤：先只读核对已有 CDP 的监听所有者、执行上下文和固定 getter；通过 [CDP Runtime.evaluate](https://chromedevtools.github.io/devtools-protocol/tot/Runtime/#method-evaluate) 返回 JSON，限定超时，允许时设置 throwOnSideEffect；响应不完整、换进程、上下文消失或未确认原生状态来源时返回 unavailable。首次资格在获准维护窗口中与当前规定的离线画面交叉核对，并覆盖在线模式但断网、好友离线、未登录、过渡期、错误类型与 JSON 往返等负例。需要启用 CEF 调试时属于后续客户端启动配置工作；本轮没有启用、安装框架或重启。另行保存实际接口版本与失败语义，不能只因源码存在就声称探针已通过。

现行 AGENTS.md 仍要求实机前的新鲜离线画面。本研究没有替换该门禁；当前可交付状态是**接口已定位、版本源码已核、UIA 当前不可用、CDP 运行时读回待资格**。
