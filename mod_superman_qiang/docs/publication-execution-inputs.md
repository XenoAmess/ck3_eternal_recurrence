# 《超人强》1.0.0 发布窗口输入与收据方案

状态：2026-10-04只读准备，未执行发布、Steam模式切换或桌面操作。根任务尚未交付实机GREEN、正式tagged staging及干净玩法图；本页的命令与JSON是待绑定输入，不是执行记录。完整产品发布门禁见[发布准备](publication-preparation.md)。

## 可用的模式控制路径

源码核对结果：`ck3_workshop_mcp/providers.py`的真实Launcher与Steamworks provider都声明`online_control=false`；`go_online`和`restore_offline`不能执行真实模式切换。具备这两个动作的是Fake provider。`workshop_begin_online_window`或`workshop_restore_offline`的Fake回执不能证明真实Steam状态。

`workshop_native_*`直接工具要求已有授权会话，由执行者负责模式与占用。`operator_query_steam_workshop_status_v1`仅只读本机配置、进程与安装信息，`WantsOfflineMode`不能代替新鲜离线画面，也不能证明其他机器没有游戏会话。`launcher_uia.py`的操作白名单要求`paradox launcher.exe`，不能把它当作Steam菜单控制器。

因此模式控制复用Steam客户端官方菜单，在发布屏幕租约内先取得当前Steam窗口的UIA树。若菜单及模式确认控件提供实际Invoke/ExpandCollapse等语义pattern，按当次HWND、进程身份、Name和pattern操作并保存前后树。历史窗口ID、旧坐标或只有Text而无pattern的控件不可复用。若当次真实控件无可用pattern，保全该缺口，使用已有[坐标换算工具](../../tools/desktop_coordinate_map.py)和新鲜原图；不新增平台模式控制层。

模式动作前后的收据应包含：任务总线租约及续约、UTC时间、Steam PID/HWND/映像、操作前后菜单文本、实际控件pattern或坐标回执、原始PNG尺寸与SHA、当前`pyautogui.size()`、动作结果及直接看图结论。键盘动作另需焦点和`LANGID=0x0409`。语义Invoke或按键ACK不能代替状态读回。

发布接管后先结束本任务CK3并复核进程归属，再取得新的离线证据：

```text
tools\.venv\Scripts\python.exe tools\desktop_steam_offline_recovery.py inspect
tools\.venv\Scripts\python.exe tools\desktop_steam_offline_recovery.py recover --task-id <当次发布屏幕租约任务ID> --output-dir <新的外置离线取证目录> --bring-steam-forward
```

`inspect`只读；`recover`会在租约下做窗口新鲜度取证，不切换模式。必须直接审阅它生成的新像素中的“离线模式”。正常在线切换选Steam菜单当次实际的“上线/Go Online”并读回确认后的状态；恢复选择当次“进入离线模式/Go Offline”及其真实确认控件。若需鼠标，精确CLI为：

```text
tools\.venv\Scripts\python.exe tools\desktop_coordinate_map.py --source-image <当次原始PNG> --preview-left <实际预览内容左边界> --preview-top <实际预览内容上边界> --preview-width <实际内容宽> --preview-height <实际内容高> --observed-x <预览中目标X> --observed-y <预览中目标Y> --click --button left --receipt <新的操作后截图.png>
```

以上占位值只能由动作当时的真实图像与UIA提供。`--receipt` 是操作后截图路径，应使用 `.png`；命令标准输出中的坐标 JSON 另行保全。此前误把此参数当作 JSON 路径会在动作已执行后导致截图编码失败，不能据此重发点击。模式切换后保存新图、菜单/窗口状态及实际业务结果；不由本机配置标志自动推断成功。菜单异常时先保全异常；只有没有CK3/录制/别人的屏幕占用，才按既有恢复指南处理。不能登出账号、强行启动游戏或终止别人的会话。

## 待根任务交付的绑定输入

| 输入 | 要求 |
| --- | --- |
| `staging`、`manifest` | 正式`superman-qiang-v1.0.0`对应的clean commit/tag；builder生成；实际库存数量来自manifest；内层descriptor无`remote_file_id` |
| `acceptance_report` | 根任务已审阅的本产品1.20.0.3实机GREEN及九语格式报告；不能用历史产品或旧游戏证据代替 |
| `thumbnail.png` | 正式staging封面，严格小于1MiB |
| `media[]` | 至少一张与封面不同的干净真实CK3玩法图；原片、裁切源、用途、SHA已入清单；native上传每图严格小于1MiB |
| 主描述与notes A/B | 最终产品边界已与验收一致；A为完整首发说明，B为完整首发说明加实际媒体变化；逐次冻结字符数、行数和SHA |
| 外层`.mod` | 首次指向正式staging且没有ID；创建成功后仅此canonical副本保存新ID |
| 屏幕租约 | 验收任务释放，发布任务领取并续约；本次offline/online/offline三组新鲜证据 |

已准备的外置单调用收据wrapper为`D:/ck3-experience-drain-feasibility-20261004/publication_native_call.py`。它只运行指定的现有MCP工具，通过official in-memory SDK调用，给子进程设置AppID上下文，保全精确参数、argv、时间、stdout/stderr及SHA；不切Steam模式、不启动游戏、不自动重试。这里只验证了`--help`，真实工具业务能力仍须在发布窗口记录。

## 在线窗口与原生输入

先从Steam当前账号/资料或好友状态与实际窗口取得“正在游戏中/其他设备会话”观察，记录观察来源和状态。若另一机器正在游戏中，停止任何游戏启动流程，报告根任务，不能接管或挤下线。本发布路径不需要启动CK3。进入必要在线窗口后，原生probe只证明当前授权AppID和owner，不能证明账号空闲。

当次`probe-arguments.json`：

```json
{
  "dll_path": "C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/steam_api64.dll",
  "app_id": 1158310
}
```

```text
tools\.venv\Scripts\python.exe D:\ck3-experience-drain-feasibility-20261004\publication_native_call.py --repo D:\workspace\ck3_eternal_recurrence --tool workshop_native_probe --arguments-file <probe-arguments.json> --output <新的probe收据目录>
```

读取业务结果`logged_on`、`steam_id64`及AppID，绑定当次owner；历史owner值不能代替此观察。DLL路径须与当次本机安装核对，准备时的symbols审计SHA为`1db3fd414039d3e5815a5721925dd2e0a3a9f2549603c6cab7c49b84966a1af3`。

先冻结Create输入（该命令本身仅本地校验）：

```text
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\prepare_publication.py --staging <tagged-staging> --manifest <tagged-manifest.json> --output <新的create冻结目录> --operation-id superman-qiang-1.0.0-create-<当次唯一值> --operation create --dll "C:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\steam_api64.dll" --description workshop\superman_qiang_description.bbcode --change-notes <已审阅notes-A.txt> --acceptance-report <GREEN-report.json>
tools\.venv\Scripts\python.exe D:\ck3-experience-drain-feasibility-20261004\publication_native_call.py --repo D:\workspace\ck3_eternal_recurrence --tool workshop_native_publish --arguments-file <create冻结目录/native-arguments.json> --output <新的create调用收据目录>
```

冻结目录内plan持有唯一耐久`receipt_file`，Create无item ID、无media字段、`legal_agreement_accepted=false`。新ID一旦出现立即保全；未知Create/Submit结果不能另建receipt或盲目再Create。遇Workshop Legal Agreement需要由所有者亲自处理，交根任务，保存同一耐久receipt；不要自动勾选或自行承诺接受。MCP transport `ok=true`及`EResult=1`都不证明公开notes和媒体。

创建成功后对精确新ID查询实际媒体库存，`previews-arguments.json`：

```json
{
  "dll_path": "C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/steam_api64.dll",
  "item_id": "<真实新ID>",
  "app_id": 1158310
}
```

```text
tools\.venv\Scripts\python.exe D:\ck3-experience-drain-feasibility-20261004\publication_native_call.py --repo D:\workspace\ck3_eternal_recurrence --tool workshop_native_previews --arguments-file <previews-arguments.json> --output <新的previews查询目录>
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\prepare_publication.py --staging <tagged-staging> --manifest <tagged-manifest.json> --output <新的media冻结目录> --operation-id superman-qiang-1.0.0-media-<当次唯一值> --operation update --item-id <真实新ID> --dll "C:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\steam_api64.dll" --description workshop\superman_qiang_description.bbcode --change-notes <已审阅notes-B.txt> --preview-snapshot <实际previews查询目录/stdout.json> --media <干净玩法图1> --acceptance-report <GREEN-report.json>
tools\.venv\Scripts\python.exe D:\ck3-experience-drain-feasibility-20261004\publication_native_call.py --repo D:\workspace\ck3_eternal_recurrence --tool workshop_native_publish --arguments-file <media冻结目录/native-arguments.json> --output <新的media调用收据目录>
```

更多图逐个增加`--media`，顺序须与冻结清单一致。再查询实际post-update媒体库存用于公开URL核对。完整notes B的匿名entry核对失败时，保全失败，再从owner页面编辑该条目的全文；最终以匿名entry ID及HTML解码、换行归一化后全文的字符数、行数和SHA为准。

## 订阅、fresh cache与立即恢复离线

`subscribe-arguments.json`：

```json
{
  "dll_path": "C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/steam_api64.dll",
  "item_id": "<真实新ID>",
  "app_id": 1158310,
  "timeout_seconds": 180
}
```

```text
tools\.venv\Scripts\python.exe D:\ck3-experience-drain-feasibility-20261004\publication_native_call.py --repo D:\workspace\ck3_eternal_recurrence --tool workshop_native_subscribe --arguments-file <subscribe-arguments.json> --output <新的subscribe收据目录>
```

必须观察callback1313精确ID、EResult1及同item Subscribed bit。Steam可能已自动下载；如精确cache已存在，先将它永久保全到当次外置目录，再证明预期cache不存在。路径解析须限定本机Steam安装下`steamapps/workshop/content/1158310/<真实新ID>`；不能复制仓库文件冒充订阅下载。

`download-arguments.json`：

```json
{
  "dll_path": "C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/steam_api64.dll",
  "item_id": "<真实新ID>",
  "app_id": 1158310,
  "timeout_seconds": 300,
  "expected_cache_path": "C:/SteamLibrary/steamapps/workshop/content/1158310/<真实新ID>"
}
```

```text
tools\.venv\Scripts\python.exe D:\ck3-experience-drain-feasibility-20261004\publication_native_call.py --repo D:\workspace\ck3_eternal_recurrence --tool workshop_native_download --arguments-file <download-arguments.json> --output <新的download收据目录>
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\build_release.py --verify <Steam实际返回的cache目录> --manifest <正式manifest.json>
```

下载必须为exact callback3406、AppID1158310、真实新ID、EResult1，随后安装路径与flags符合合同。正式文件库存、字节长度和SHA必须精确匹配manifest。ID绑定后的manifest重建由根任务处理，必须证明同tag/runtime等价；不移动源码tag。

原生联网工作结束或失败时第一时间使用官方菜单恢复离线，并运行前述新的offline `recover`、直接审阅“离线模式”。网络公开页读取可以在Steam已离线时继续；不能为了匿名HTTP等待或429让客户端一直在线。最终离线收据与失败attempt永久保全。

## 匿名页面依赖核对规则

只读一手正例确认Steam页面有两个独立栏目：

| 页面 | 正例中的栏目与ID |
| --- | --- |
| [Royal Court Event Pack](https://steamcommunity.com/sharedfiles/filedetails/?id=3360676953) | `Required DLC`栏目链接Royal Court，实际store app ID为[1303182](https://store.steampowered.com/app/1303182) |
| [CFP/EPE韩语补丁](https://steamcommunity.com/sharedfiles/filedetails/?id=3538192508) | `Required items`按栏目顺序链接2220098919、2507209632、2996881191、3538041942 |

这些正例证明栏目标题、说明句及实际目标href，不证明本机浏览器的具体CSS class。正文也可能重复提到同样的mod链接，因此禁止全页扫描链接来推断Required items。页面提取器还可能输出隐藏的removed/incompatible/login模版，不能把这种文本当作可见状态。

实际发布窗口使用全新匿名浏览器context（没有cookies、storage_state或Authorization），读取`https://steamcommunity.com/sharedfiles/filedetails/?id=<真实新ID>&l=english`。保存HTTP返回正文和浏览器`page.content()`各自的SHA、最终URL、HTTP状态、item标题及ID；二者不是同一字节串。

可复用的解析规则如下，但具体DOM选择器须由当次真实页绑定并记录：

1. 在实际已加载的sidebar内找可见且规范化文本精确等于`Required DLC`或`Required items`的标题，检查对应说明句。获取只包含该栏目标题、说明及目标链接的最小祖先；若祖先同时包含`Created by`、其他栏目或正文，则继续缩小。保存实际DOM path、class/id、matched outerHTML及SHA；不要预设未经真实DOM证明的CSS class。
2. 只在该栏目中提取href：DLC限定`store.steampowered.com`的`/app/<ASCII数字>`；mod限定`steamcommunity.com`的`/sharedfiles/filedetails/`或`/workshop/filedetails/`路径及`id=<ASCII数字>`query。记录DOM顺序、去重ID、链接文字及完整href。
3. 返回空数组需要真实完整sidebar已观察：同一已验证物品的File Size、Posted/Updated及Created by区域实际加载，保存完整sidebar outerHTML和所有可见标题，并证明其中缺少上述两个Required栏目。429、登录页、错误页、尚未加载、无法界定sidebar或标题歧义时保持`not_observed`与`null`，不能从API缺字段得到空数组。
4. 栏目存在但没有可解析的href时记`unknown`并直接检查DOM；不能当成无依赖。布局变更只调整针对真实页面的最小规则，不新增无关平台API。

本机先前三个直接匿名HTML请求均429，已经保全，未反复请求；正例核对来自官方Steam页面读取。本准备阶段未取得成功的本机匿名原始DOM，以上布局绑定留待实际窗口。

实际观察记录最少应包含以下字段（占位/未观察不可标为通过）：

```json
{
  "state": "observed",
  "item_id": "<真实新ID>",
  "anonymous": true,
  "url": "<实际最终URL>",
  "http_status": 200,
  "http_body_sha256": "<HTTP原始正文SHA>",
  "dom_sha256": "<实际page.content()SHA>",
  "sidebar_sha256": "<实际完整sidebar outerHTML SHA>",
  "actual_rule_and_locators": "<当次已观察DOM规则，包含可见性与栏目边界>",
  "required_dlc_app_ids": [],
  "required_mod_item_ids": [],
  "observed_links": [],
  "required_sections_absent_in_complete_sidebar": true
}
```

数组和absence字段须填写实际结果，不复制模板。只允许本产品预期的两个空数组；观察到任何真实依赖须先解决并重新公开读回。再将这份实际DOM观察与[公开核对helper](../tools/verify_publication.py)的`metadata_notes_cover_media_ok`合并到最终报告。helper单独运行仍会明确给出`pending_dependency_observation`，不能独自作为完整发布GREEN。

最终匿名公开核对命令：

```text
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\verify_publication.py --item-id <真实新ID> --owner-steam-id <当次probe的steam_id64> --description <最终media冻结目录/description.bbcode> --change-notes <最终media冻结目录/change-notes.txt> --thumbnail <tagged-staging/thumbnail.png> --native-previews <post-update预览查询/stdout.json> --media <干净玩法图1> --output <新的anonymous公开回读目录>
```

公开CDN字节与解码像素核对、实际图片审阅、完整notes精确entry、DOM依赖观察、fresh cache和最后offline均须真实通过。之后才可写实际发布changelog与发布报告；永久changelog的master commit/push及GitHub Release附件校验由根任务收口。
