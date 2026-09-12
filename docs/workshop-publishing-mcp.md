# CK3 Workshop 发布 MCP：Paradox Launcher 真实调用链预研

> 状态：针对本机 Paradox Launcher `2026.11.1` 的只读静态逆向结论。本文没有上传物品、接受法律协议、读取凭据或操作 Steam/Launcher/CK3 进程。

> 2026-09-12 实施补记：下文保留原始预研及失败分析。主线程最终通过 `ck3_workshop_mcp` 的 `steam-native` 工具真实发布了 [3800124956](https://steamcommunity.com/sharedfiles/filedetails/?id=3800124956)，Create/Submit 均为 `EResult=1`；公开文案与 14 文件下载缓存一致，Steam 随后恢复离线。完整事实见 [1.19.0 changelog](release-changelogs/auto-upgrade-buildings/1.19.0.md)。原生更新分支有离线测试，尚未实机更新验证；CDP 未通过实机验证，未使用。

> 2026-09-13 实施补记：原生 update 已由 1.19.0 文案修正和 2.0.0 正式更新两次真实验证。另有一个必须保留的边界：只改变 `SubmitItemUpdate` 的 `pchChangeNote` 时，Steam 可返回 `EResult=1` 却不创建或替换公开 Change Notes；描述 metadata 更新也不替换既有条目。现有条目最终通过登录态 owner page 直接编辑，并以匿名公开 HTML 精确读回。后续发布必须单独核对 Change Notes 正文，不能从 Submit 回执或主描述更新推断成功。完整事实见 [2.0.0 changelog](release-changelogs/auto-upgrade-buildings/2.0.0.md)。

## 1. 结论

Paradox Launcher 上传 Steam Workshop Mod 的真实路径不是 HTTP API，而是：

```text
Launcher renderer
  -> Electron preload: ipcRenderer.send("message", action)
  -> Launcher main: PublishModHandler
  -> Launcher Steam publish service
  -> greenworks 0.29.0
  -> steam_api64.dll / Steam Client IPC
  -> ISteamUGC
```

鉴权来自当前 Steam Client 的登录会话。这里没有可复用的 Paradox token 或 Steam Web API key，也不应由 MCP 读取、保存或回传用户凭据。

截至本文落盘时，仓库中的 `ck3_workshop_mcp/src/ck3_workshop_mcp/providers.py` 仍把 `pdx-readonly` 和 `steamworks-readonly` 定义为无写能力 provider（`create_item=false`、`update_item=false`）；`transport.py` 已有 CDP transport，但这不等于真实发布 provider 已接通。在完成下述 bridge 和一次 live probe 前，不能把当前包描述成已经能够真上传。

最短的无 OCR 接入方式，是在**第一个** Launcher Electron 进程启动时开启 Node main-process inspector，再通过 main process 的 `webContents.executeJavaScript()` 调用 Launcher 已有的 preload IPC。这样复用官方 Launcher 的 Mod 数据库、发布处理器和 Greenworks，不需要重写 Steam 登录，也不依赖图像识别。

## 2. 冻结的 Launcher 身份

本次分析对象：

```text
C:\Users\1\AppData\Local\Programs\Paradox Interactive\launcher\launcher-v2.2026.11.1
```

| 对象 | 版本/大小 | SHA-256 |
| --- | ---: | --- |
| `Paradox Launcher.exe` | file/product `0.1.0.4774` | `0EF0882AB975DED0A08E849CC7660C43B44BEC731F9978109E4A123F96D36449` |
| `resources/app.asar` | 28,508,052 bytes | `92AD205C01A6730ED2A0D66434348682096F38E712A451289F91ECF0592ED918` |
| `resources/app.asar.unpacked/node_modules/greenworks/package.json` | 630 bytes | `AD46FE739EDBD694F62FB4E87F9621C6742FC62F2C64A4E78ADCC34A753E1274` |
| `resources/app.asar.unpacked/node_modules/greenworks/greenworks.js` | 11,702 bytes | `155797EE660A77F36B2A9E7C7C03064B994D318CC6497CB9236D8B6D9200662C` |
| `resources/app.asar.unpacked/node_modules/greenworks/lib/greenworks-win64.node` | 634,880 bytes | `E2766469FB8A3F8EAECB4932D65E4ED5267B76B614B74B1EDEAFD34323726E8F` |
| `resources/app.asar.unpacked/node_modules/greenworks/lib/steam_api64.dll` | 295,336 bytes | `4DF999C0C8CB12589F0864D52BE5D4C775577AEB27FEE28B49B188F9BA083EEA` |

Launcher 内置 Electron `42.7.0`、Node `24.18.0`；Greenworks 包版本为 `0.29.0`。原生插件包含 `STEAMUGC_INTERFACE_VERSION016`。

### ASAR 内精确模块

| ASAR member | 大小 | content offset | SHA-256 |
| --- | ---: | ---: | --- |
| `/package.json` | 1,384 | 26,719,312 | `5c714c027788e9c5882c5e075a136ac4de858916eaaf99b8ecdbff8fecc681ca` |
| `/dist/main/index.mjs` | 3,522,896 | 14,870,901 | `575c80c28444e5b2b9716dee6433e2289035000fbc213bdabd3e6b5301f25168` |
| `/dist/preload/index.mjs` | 188,676 | 18,432,390 | `92b8375edb85c253d5cb4c433cbffb505e4086d4a425cb818c4b9b2fa7141363` |
| `/dist/renderer/assets/mods-upload-0bs69VFp.js` | 1,192,069 | 22,712,286 | `3d11c3fef1ac76079c1e8d1db81784640c6125e4723348b34f0165a4dcad0a33` |
| `/dist/renderer/mods-upload.html` | 1,705 | 26,715,939 | `53310c9817070219159f7aaac61d6eefcc4eea977a1ff4a09e65c2a4234e9b41` |

`content offset` 是 ASAR header 中的相对 offset，用来定位和复核证据；不是普通文件系统偏移。

### 可复现提取命令

先校验输入，再完整提取到一次性目录：

```powershell
$launcherRoot = Join-Path $env:LOCALAPPDATA 'Programs\Paradox Interactive\launcher\launcher-v2.2026.11.1'
$asarPath = Join-Path $launcherRoot 'resources\app.asar'
$extractRoot = Join-Path $env:TEMP 'pdx-launcher-2026.11.1-asar'

Get-FileHash -Algorithm SHA256 -LiteralPath $asarPath
npx.cmd --yes @electron/asar extract $asarPath $extractRoot

Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $extractRoot 'dist\main\index.mjs')
Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $extractRoot 'dist\preload\index.mjs')
Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $extractRoot 'dist\renderer\assets\mods-upload-0bs69VFp.js')
```

用于定位本结论的只读检索：

```powershell
rg -n --fixed-strings 'PublishModHandler' (Join-Path $extractRoot 'dist\main\index.mjs')
rg -n --fixed-strings '@IPC_MODS_UPLOAD/UPLOAD_MOD' $extractRoot
rg -n 'remote-debugging|openDevTools|toggleDevTools|globalShortcut|before-input-event' (Join-Path $extractRoot 'dist\main\index.mjs')
```

提取物只用于逆向核验，不应提交进仓库。升级 Launcher 后必须重新记录版本、ASAR SHA、内部文件名和哈希，不能把上述 bundle 名视为稳定 ABI。

## 3. Launcher IPC 与发布语义

preload 暴露的关键调用是：

```js
window.electron.ipcSend(action);       // ipcRenderer.send("message", action)
window.electron.ipcRendererOn(handler); // 接收 main 发回的 action
```

上传请求：

```js
{
  type: "@IPC_MODS_UPLOAD/UPLOAD_MOD",
  gameId: "ck3",
  platform: "steam",
  mod: uploadMod
}
```

Launcher 的执行器从 `mod` 读取：

```js
{
  id,
  remotePdxId,
  remoteSteamId,
  descriptionSteam,
  descriptionPdx,
  shortDescriptionPdx,
  tags,
  thumbnailPath,
  requiredVersion,
  patchNote
}
```

其中 `id` 是 Launcher installed-mod 数据库 ID。实际上传目录由 Launcher 按这个 ID 查到的本地 Mod 记录决定，不能只在请求里随意塞一个路径。

返回 action：

```text
@IPC_MODS_UPLOAD/UPLOAD_MOD_PROGRESS
@IPC_MODS_UPLOAD/UPLOAD_MOD_SUCCESS
@IPC_MODS_UPLOAD/UPLOAD_MOD_ERROR
```

### 首次创建

当 `remoteSteamId` 为空时，Launcher 调用 `ensureWorkshopItemExists()`，继而调用 Greenworks `_ugcCreateItem()`。成功后获得新的 `PublishedFileId`，更新 Launcher 的本地 Mod 记录，再继续提交内容。

这一步对应 Steamworks 的 `ISteamUGC::CreateItem`。创建成功不等于公开发布完成；仍需随后上传内容，并可能需要用户处理 Workshop 法律协议。

### 更新既有物品

当 `remoteSteamId` 已存在时，不创建新物品。Launcher 构造的 Steam payload 为：

```js
{
  title: installedMod.displayName,
  tags: requestedTags || installedMod.tags,
  path: resolvedStagingDirectory,
  description: descriptionSteam.trim(),
  icon: "<staging>/thumbnail.png" // 仅文件存在且小于 1 MiB
}
```

随后 `steamService.updateWorkshopMod()` 调用 `greenworks.updateMod()`；Greenworks 注入当前 `app_id` 和字符串形式的 `published_file_id`，最终进入 `_ugcUpdateModFull`。其语义相当于 Steamworks 的 `StartItemUpdate`、各项 setter 和 `SubmitItemUpdate`。

Launcher 这条路径没有暴露 visibility、update language 或 changenote；需要这些能力时不能假装已有 IPC 支持。

### Steam 上传前的 PDX social-profile gate（2026-09-12 live 故障）

这个用户名提示不是 Steam Workshop 或 Steam 账号的要求，而是 Launcher 上传窗口自己的 **Paradox `social` game profile** 前置门槛。冻结 bundle 中的确切分支位于：

- `app.asar:/dist/renderer/assets/mods-upload-0bs69VFp.js`：上传请求先保存完整的 `{ gameId, mod, platform }`；随后 saga 读取上传窗口 Redux store 的 `gameProfile.username`。值为空时，无论 `platform` 是 `steam` 还是 `pdx`，都会跳到 `#/username`，尚未向 main 发送 `@IPC_MODS_UPLOAD/UPLOAD_MOD`。
- 同一模块的初始化只异步发送 `@IPC_MODS_UPLOAD/GET_GAME_PROFILE`，默认 namespace 为 `social`；用户名页提交的是 `@IPC_MODS_UPLOAD/POST_GAME_PROFILE { username, namespace: "social" }`。该分支不检查所选发布平台。
- `app.asar:/dist/main/index.mjs`：GET handler 调用 `authService.apiClient.getGameProfile("social")`；POST handler 调用 `postGameProfile(...)` 后再次 GET，并把成功结果广播给上传窗口和主窗口。真正的 `PublishModHandler` 本身不检查 username。
- `app.asar:/dist/renderer/assets/primary-BhXEZjYt.js`：主窗口账号显示名优先读取 `account.gameProfiles.social.username`，缺失时才回退为掩码邮箱。现场主窗口已经显示 `XenoAmess`，所以主窗口的账号 store 已经持有 social username；上传窗口却仍跳转 `#/username`，证明这是两个窗口的 profile 状态不一致，而不是用户尚未设置用户名。

现场在重新打开上传窗口、等待、选择 Steam、填写 1,024 字描述并提交后仍进入 `#/username`；填写现有用户名后得到通用“无法更新你的个人资料，请重试”。后者与 main 的错误映射一致：它只专门映射 `username-exists`、`invalid-username` 和本地长度错误，其余后端错误都落入通用提示。`profile-exists` 是否为本次确切后端错误没有请求级日志，不能仅凭 UI 断言。

相关日志为 `C:\Users\1\AppData\Local\Paradox Interactive\launcher-v2\logs\launcher-2026-09-12.log`：`09:06:51.558Z` 打开 Mods upload window，`09:06:51.705Z` 紧接着出现 `Livecheck API request failed read ECONNRESET`；同日日志还在 `08:56:48.374Z` 记录 `connect ECONNREFUSED 127.0.0.1:10808`，并在 `09:16:55.373Z` 记录 playset API sync 的 `read ECONNRESET`。这些是 PDX API/代理链不稳定的关联证据，但日志没有标出 `/profiles` 请求，不能冒充该请求的直接 trace。

冻结 main bundle 中 profile API 的精确地址是：

```text
GET  https://api.paradox-interactive.com/profiles?namespace=social
POST https://api.paradox-interactive.com/profiles
```

只做 DNS/TLS/HTTP 可达性检查、不读取或发送 Launcher token/cookie，可运行：

```powershell
$uri = 'https://api.paradox-interactive.com/profiles?namespace=social'
try {
  $r = Invoke-WebRequest -Uri $uri -Method Get -MaximumRedirection 0 -TimeoutSec 15 -UseBasicParsing
  [pscustomobject]@{ Reachable = $true; Status = [int]$r.StatusCode; Host = ([uri]$uri).Host }
} catch {
  $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { $null }
  [pscustomobject]@{
    Reachable = $null -ne $status
    Status = $status
    Error = if ($status) { $null } else { $_.Exception.Message }
    Host = ([uri]$uri).Host
  }
}
```

其中 `401`/`403` 仍表示 DNS、TLS 和 HTTP 路由已通；没有 HTTP 状态码的 DNS、连接或 TLS 错误才表示链路未通。该命令不得添加 `Authorization`、Cookie 或 `-UseDefaultCredentials`。当前发布处置是不再重复 POST 用户名，也不通过退出/重登 PDX 账号修复；主线程改走直接 Steamworks 调用链。

## 4. Debug/CDP 与外部桥审计

当前生产 bundle 的结论如下：

| 候选入口 | 静态结论 |
| --- | --- |
| Launcher 自带 renderer CDP | 未开放；main bundle 没有 `remote-debugging` 配置。 |
| DevTools / 开发者快捷键 | 生产常量 `mp=false`，`BrowserWindow.webPreferences.devTools=mp`；未发现 `openDevTools`、`toggleDevTools`、`globalShortcut`、`before-input-event` 或 F12 注册。 |
| BrowserWindow 参数 | `webSecurity: !mp`、`contextIsolation: false`、`nodeIntegration: false`、`devTools: mp`、`sandbox: false`、`additionalArguments: []`。 |
| Launcher 自有 CLI | 未声明 remote-debugging/pdxl 选项；未知选项被 yargs 当作给游戏的参数，不是可靠的 Launcher 调试入口。 |
| Electron 原生参数 | Electron 支持首进程的 `--inspect=<host:port>` 和 `--remote-debugging-port=<port>`，但本机 Steam 启动参数能否原样送到 Launcher 尚需一次只读 loopback probe 确认。 |
| 第二实例注入参数 | 不可依赖。Launcher 使用 `requestSingleInstanceLock()`，且未发现可消费新参数的 `second-instance` handler。调试参数必须进入第一个 Launcher 进程。 |
| Launcher localhost socket | 存在随机本地端口，但静态调用链属于 `cpatch` 更新/提权/关停协议，不是 Mod 发布 IPC。 |
| preload IPC | 可直接发布，但只存在于 Electron 进程内部；没有发现对应的外部 named pipe、HTTP 或 WebSocket 服务。 |

因此，不应把 `cpatch` socket 当发布桥，也不应依赖生产 renderer 的 DevTools。更短且边界更清楚的候选是 Electron main-process `--inspect`：它不要求 BrowserWindow 开启 DevTools，main inspector 内可以取得 `electron.webContents`，再进入已有 renderer/preload IPC。

## 5. 最短无 OCR 真实调用方案

以下方案仍走 Paradox Launcher 自己的真实发布器；唯一需要先实测确认的是 Steam 是否把 inspector 参数交给第一个 Launcher 进程。

1. MCP 在既有发布门禁通过后，请 Steam 以 AppID `1158310` 的正常上下文启动第一个 Launcher，并附加只监听 loopback 的随机 main inspector 端口。候选 Steam URI 形态为：

   ```text
   steam://run/1158310//--inspect=127.0.0.1:<random-port>/
   ```

   不能通过直接运行 `dowser.exe` 代替：本机证据表明脱离 Steam 启动上下文会导致 Steam API 初始化失败。不要创建 `steam_appid.txt`。

2. 只读探测 `http://127.0.0.1:<port>/json/list`。若没有 main inspector target，则本版本的 inspector adapter 判定不可用；不要改用猜测性的本地端口。

3. 连接 main target 的 WebSocket，在 `Runtime.evaluate` 中取得 Electron：

   ```js
   const require_ = process.getBuiltinModule("module").createRequire(process.execPath);
   const { webContents } = require_("electron");
   ```

4. 找到 primary renderer，并用 `executeJavaScript()` 请求 Launcher 打开上传窗口：

   ```js
   window.electron.ipcSend({
     type: "@IPC_PRIMARY/OPEN_MODS_UPLOAD_WINDOW",
     gameId: "ck3"
   });
   ```

5. 从 `webContents.getAllWebContents()` 找 URL 含 `mods-upload.html` 的 renderer。在其中先注册消息队列，再拉取 Launcher 认识的 local mods：

   ```js
   window.__ck3WorkshopMcpMessages = [];
   window.electron.ipcRendererOn(message => {
     window.__ck3WorkshopMcpMessages.push(message);
   });

   window.electron.ipcSend({
     type: "@IPC_COMMON/FETCH_INSTALLED_MODS",
     gameId: "ck3",
     source: "local"
   });
   ```

6. 等待 `@IPC_MAIN/FETCH_INSTALLED_MODS_SUCCESS`。用准备阶段冻结的 staging 绝对路径精确匹配返回的本地 Mod，取得 Launcher 数据库 `id`；不要按显示名称模糊匹配。

7. 克隆返回的 serialized mod，只覆盖已冻结发布计划中的字段，然后发出 `@IPC_MODS_UPLOAD/UPLOAD_MOD`。首次发布保持 `remoteSteamId` 为空；更新必须精确等于目标 Workshop ID。

8. 轮询队列中的 progress/success/error，并保存 Launcher 发布日志、请求摘要、staging manifest SHA、目标 ID 和最终回读结果。调用成功后按仓库流程进行订阅缓存复核、重建无内层 ID 的 staging、写入 changelog，最后立即恢复 Steam 离线模式。

若步骤 2 证明 Steam 没有把 `--inspect` 送入 Launcher，当前版本可用于本次发布的最短替代是 Windows UI Automation 按可访问性控件驱动现有上传表单；它仍不需要 OCR，但不是 Launcher 内部协议。不要把未经实测的 CDP 参数转发写成已完成能力。

## 6. MCP tool/API 草案

真实 provider 应保持预检与副作用分离：

```text
inspect_environment()             # 只读：Steam/Launcher/账号占用/版本/bridge 状态
prepare_release(product, target)  # 只读：解析 outer descriptor，构建并冻结 staging 证据
probe_launcher_bridge()           # 只读：首进程 inspector target 与 Launcher IPC ABI
publish_new(prepared_id, fields)  # 写：remoteSteamId 为空，允许 CreateItem + 首次 update
publish_update(prepared_id, workshop_id, fields) # 写：禁止 CreateItem，只更新精确 ID
observe_publish(operation_id)     # 只读：progress/success/error/log evidence
verify_public_item(operation_id)  # 只读：Workshop 元数据及新鲜订阅缓存复核
restore_offline(operation_id)     # 写：恢复 Steam 离线状态并复核
```

建议状态机：

```text
DISCOVERED
  -> PREPARED
  -> BRIDGE_READY
  -> USER_AUTHORIZED
  -> SUBMITTING
  -> SUBMITTED
  -> PUBLIC_READBACK_VERIFIED
  -> FRESH_CACHE_VERIFIED
  -> OFFLINE_RESTORED
  -> COMPLETE
```

任何 `UPLOAD_MOD_ERROR`、进程桥断开、目标 ID 漂移或回读不一致进入 `FAILED_WITH_EVIDENCE`；不能从不确定状态自动重试首次创建，否则可能产生重复 Workshop item。

## 7. 当前必须保留的实际边界

- 正式上传只能使用对应 builder 生成且已冻结 manifest/SHA 的 staging，不上传源码目录。
- Steam 在线时，若账号显示正在其他机器游戏或占用状态无法确认，不启动 CK3/AppID，不接管会话。
- 上游 `3596580780` 只表示来源，绝不能作为维护版更新目标。
- canonical `remote_file_id` 只保留在用户目录外层 `.mod`。上传前 staging 内层 `descriptor.mod` 必须无该字段；Launcher 会在上传过程中临时注入，上传结束后必须重建 staging 恢复无 ID 正式树。
- Greenworks 0.29.0 的 JS callback 只暴露创建出的 item ID 和数值结果，没有暴露 `bUserNeedsToAcceptWorkshopLegalAgreement` / EULA status。`steam_api64.dll` 虽含 `GetWorkshopEULAStatus` 和 `ShowWorkshopEULA`，Launcher JS surface 没接出这两项。因此 MCP 不得宣称已自动确认或接受法律协议；需要时由用户在 Steam 页面人工处理。
- `SubmitItemUpdate` 发出后没有可靠取消。超时应记录为 unknown，并先回读，不能自动再次 CreateItem。
- 上传成功、公开页回读、全新订阅缓存复核、release changelog 入库、Steam 恢复离线缺一不可；前面的 success IPC 只证明 Launcher 调用成功。

### 7.1 Change Notes 事故复盘与强制门禁

2026-09-12 的 Auto Upgrade Buildings 2.0.0 发布把完整 changelog 只留在仓库，Steam Change Notes 则只写入 51 字摘要。根因不是
内容缺失，而是把三个不同交付物错误地合并理解：仓库 release changelog、Workshop 主描述、Steam Change Notes。验收又只检查了
`SubmitItemUpdate` 的 `EResult=1`，没有读取公开 changelog 页面，因而漏过了玩家实际只能看到摘要的问题。

2026-09-13 的纠正进一步证明：只更换 `pchChangeNote` 的 metadata-only submit 可以返回 `EResult=1`，但不新建、也不替换公开
Change Notes；成功更新 Workshop 主描述同样不会连带修改既有 Change Notes。最终必须在登录态 owner page 编辑既有条目，再用匿名
公开页面读回，才能证明玩家实际看到的正文已经改变。

以后每次正式发布必须执行以下门禁：

1. **分别准备三份交付物。** 仓库 release changelog、Workshop 主描述和 Steam Change Notes 各自有明确目标；Steam 条目必须是
   完整的玩家可见更新说明，不能只给一句摘要。
2. **提交前冻结正文。** 在发布证据中保存待发布 Change Notes 的精确 UTF-8 文本、字符数、行数和 SHA-256；禁止事后凭印象判断。
3. **回执只算传输证据。** `EResult=1`、进度 100% 或主描述更新成功都不能把 Change Notes 标为 GREEN。
4. **匿名公开回读。** 读取 `https://steamcommunity.com/sharedfiles/filedetails/changelog/<item-id>`，锁定本次目标 entry ID；HTML 解码并
   归一化 CRLF/LF 后，与冻结正文逐字比较，同时记录 entry ID、字符数、行数、正文哈希及公开 HTML 哈希。
5. **既有条目必须验证替换。** 若本次是纠正或更新已有版本条目，不能仅证明页面上“有一条新记录”；必须证明预期 entry 的正文
   已经替换。原生 submit 无效时，使用 owner page 编辑该条目，再重复匿名回读；不要为了改文案无意义地重传未变化的 mod 内容。
6. **失败就保持未完成。** 公开正文缺失、被截断、仍是旧摘要、目标 entry 不明或无法匿名回读时，release 状态保持 RED/未完成，
   不能用仓库文档、截图、登录态页面或 API 回执替代。
7. **证据与收尾。** 将精确回读结果写入该版本永久 changelog/发布证据；随后完成订阅缓存复核、提交推送和 Steam 离线恢复。

本次事故的永久事实与哈希见 [Auto Upgrade Buildings 2.0.0 changelog](release-changelogs/auto-upgrade-buildings/2.0.0.md)。

## 8. 自动化边界与最小测试路线

可自动化：staging 构建与哈希、descriptor 检查、Launcher local-mod 精确匹配、IPC 请求、进度/错误采集、公开元数据回读、订阅缓存哈希复核和离线恢复。

必须人工处理：Steam 登录/Steam Guard、Workshop 法律协议、账号冲突的决策，以及首次对新工具授予真实发布权限。

最小实现顺序：

1. 用固定 ASAR SHA 做只读 ABI fixture 测试，断言 action 名、请求字段和 Greenworks 调用仍存在。
2. 实现 main inspector transport；只做 `/json/list`、`Runtime.evaluate` 和 `webContents` 枚举，不上传。
3. 实机只读拉取 local mods，证明 exact staging path 能解析到唯一 Launcher `id`。
4. 对已授权测试 item 做一次 update，保存完整 progress/success/error 与公开回读。
5. 最后才验证 new-item 分支；断线/超时后只回读，不自动重建。

建议代码继续放在 `ck3_workshop_mcp/`，协议冻结 fixture 放在 `ck3_workshop_mcp/tests/fixtures/pdx-launcher-2026.11.1/`；运行证据放 `_runtime/ck3-workshop-mcp/<operation-id>/`，不要把解包后的 Launcher bundle 或用户态日志原文提交进 Git。

## 9. 一手资料

- Electron command-line switches: <https://www.electronjs.org/docs/latest/api/command-line-switches>
- Electron main-process debugging: <https://www.electronjs.org/docs/latest/tutorial/debugging-main-process>
- Electron `webPreferences`: <https://www.electronjs.org/docs/latest/api/structures/web-preferences>
- Steamworks `ISteamUGC`: <https://partner.steamgames.com/doc/api/ISteamUGC>
- Steam Workshop implementation guide: <https://partner.steamgames.com/doc/features/workshop/implementation>
- Steam browser protocol: <https://developer.valvesoftware.com/wiki/Steam_browser_protocol>

本机历史运行证据位于 `C:\Users\1\AppData\Local\Paradox Interactive\launcher-v2\logs\launcher-2026-09-11.log`：该日志记录 Steam API 初始化成功，以及一次 `Publishing mod started` / `Publishing mod succeeded`。它能证明 Launcher + Steam 上下文的真实发布链工作过，但不替代本次目标 item 的新发布证据。
