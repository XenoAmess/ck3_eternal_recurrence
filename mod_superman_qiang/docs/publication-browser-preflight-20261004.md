# 发布前原生probe与匿名DOM路径

状态：2026-10-04发布准备；本产品仍待最终实机GREEN、正式tagged staging和干净玩法图。以下是只读预检，不是创建、上传或发布成功事实。新原始收据统一保存在C盘外置目录，避免占用实机attempt所在D盘。

## 实际离线DLL probe

根任务授权后，用现有`workshop_native_probe`通过official in-memory MCP client做了一次隔离调用。AppID为1158310，DLL为本机Steam管理的`C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/steam_api64.dll`。调用时间为`2026-10-03T21:49:08.499248Z`至`21:49:13.128992Z`，结果明确为`Steam user interface reports BLoggedOn=false`，MCP `ok=false`。没有自动重试、切在线、启动游戏或操作桌面。

完整参数快照、argv、开始/结束时间和stdio位于`C:/ck3-superman-qiang-publication-20261004/publication-native-probe-offline-01/`。stdout SHA为`168cfaca227df6a07eb07dd9aa9a3f0f69ff0062df453f19e20edbee3cbe6493`，stderr SHA为`2d979cdbfe9eed3ec4e84c0893899b0a437a6adb721095807ec5097c20804101`。stderr中的缓存SteamID不是在线owner的成功业务读回，正式窗口仍须重新probe并绑定`logged_on/app_id/steam_id64`。

此失败只证明原生客户端当时没有在线登录业务状态，不代替需要直接看图确认的Steam离线模式。既有纯PE symbols预检与44项静态回归仍是独立证据，未因本次离线预检外推为实际订阅成功。

## 已执行的匿名浏览器正例

本机Python未安装Playwright。复用了家徽项目已安装的Node `@playwright/test 1.63.0`、Node `v24.20.0`和已安装Chrome；实际浏览器版本`154.0.8037.93`。没有下载浏览器、安装依赖或使用当前浏览器登录profile。每次使用headless Chrome的全新context，初始cookies为0，主请求没有Cookie或Authorization。浏览器页面截图不属于桌面输入或桌面租约占用。

外置最小观察脚本为`C:/ck3-superman-qiang-publication-20261004/anonymous_workshop_dom.cjs`，只执行一次显式导航，保全观察时自身源码、输入、HTTP原文、实际`page.content()`、完整浏览器页截图和观察JSON，不登录、不订阅、不修改任何页面。使用CLI：

```text
node C:\ck3-superman-qiang-publication-20261004\anonymous_workshop_dom.cjs --repo D:\workspace\ck3_eternal_recurrence --item-id <精确item ID> --output <C盘新的外置目录>
node C:\ck3-superman-qiang-publication-20261004\anonymous_workshop_dom.cjs --repo D:\workspace\ck3_eternal_recurrence --item-id <精确item ID> --page-kind changelog --output <C盘新的changelog目录>
```

| 官方正例 | 实际结果与正文身份 | 取证目录 |
| --- | --- | --- |
| [Royal Court Event Pack](https://steamcommunity.com/sharedfiles/filedetails/?id=3360676953) | HTTP200；HTTP SHA `a64758171db28aec5b1fff0ba555d2a6835bb20eb806a2b329f2c1075890d936`；DOM SHA `4705af8656a8ddbed2891c54a2fae0afeca047e14d0782c6370bb0d494607fbd` | `C:/ck3-superman-qiang-publication-20261004/anonymous-dom-positive-dlc-01/` |
| [CFP/EPE韩语补丁](https://steamcommunity.com/sharedfiles/filedetails/?id=3538192508) | HTTP200；HTTP SHA `69a0a20df60f88aa579b4a7d380885ef349115ffa1135b4788870a8ed8fe6e65`；DOM SHA `5f1675865c670239e90ecd03cb331c22e5acb1cd23144a49d227e4068f61ec94` | `C:/ck3-superman-qiang-publication-20261004/anonymous-dom-positive-items-01/` |

两张实际页面截图已直接审阅，正例分别显示Required DLC和Required items，不从之前urllib的429正文推断依赖。两次浏览器取证都是新的输入/目录，没有循环429或反复刷新。

还对同一3538192508的changelog页面执行了一次独立新匿名context导航，HTTP200。原文SHA为`28fbb85aca0dad63e4a1f9d479568a1fadf8e640937a1037f607a601803a58e2`、DOM SHA为`b033342c6cbc79e9c0364d4a0cae5670cdc0c53947ef99e10f46bd3d8dd3a311`，保存在`C:/ck3-superman-qiang-publication-20261004/anonymous-changelog-positive-01/`。共享全文解码器读出实际entry ID；这只证明已有页面的回读路径，不证明本产品notes已公开。

`verify_publication.py`现提供可选`--item-page-observation`和`--changelog-observation`。它读取对应观察目录中`http-response.html`的精确字节，并核对item ID、HTTP200、请求/最终URL一致及正确目标路径/query、fresh context初始零cookies、无storage_state/Authorization、主请求无Cookie/Authorization、原HTTP与DOM SHA。原文、DOM和观察JSON复制进新的核对目录并记录来源身份。API、完整notes、封面和CDN比较仍执行原有合同；Required DLC/items保持独立未观察门，不把API缺字段当空。

相称拒绝边界检查保存在`C:/ck3-superman-qiang-publication-20261004/browser-input-contract-checks-02/`，最终helper源码SHA为`9dbf0bfac753f8a1877a6a5c94da9b7d16b714d791ab1d2a250fc1c8313b57ad`，9项通过：实际匿名输入成功；错item、错请求URL、错最终URL、429、认证请求、HTTP字节SHA错、DOM SHA错和非fresh context均拒绝。另一次缺少匿名证明的拒绝及实际changelog输入/解码检查保存在`browser-input-missing-proof-01/`与`browser-changelog-input-check-01/`，各自报告记录当时helper SHA；没有HTTP、Steam或桌面调用。早期attempt不覆盖。

## 实际可复用DOM规则

两个实际DOM都将依赖放在`#rightContents > .sidebar`的独立`.panel`中，栏目标题为`.rightSectionTopTitle`，说明为`.rightSectionMinorText`。`Created by`位于另一个独立panel。文件大小及Posted/Updated位于上面的`.workshop_item_header`区域，因此不能要求它们与Created by处在同一个最小sidebar祖先中。

Royal Court正例实际使用`.requiredDLCContainer > .requiredDLCItem`，店铺href为`https://store.steampowered.com/app/1303182`，图片链接和文本链接指向同一DLC，按首次DOM顺序去重后为`["1303182"]`。另一正例实际使用`#RequiredItems.requiredItemsContainer > .requiredItem`，栏目链接顺序为`["2220098919", "2507209632", "2996881191", "3538041942"]`。正文也重复这些链接，解析只能限定该panel。

Steam CSS把栏目标题渲染为大写，实际`innerText`可能是`REQUIRED DLC`。第一次通用观察器以大小写敏感的innerText寻找标题，漏列了标题；原始DOM和实际截图仍完整保全，没有把漏列当成无依赖。后续观察改为先检查实际CSS可见性，再以规范化`textContent`匹配`Required DLC`或`Required items`，并保存实际panel的outerHTML与链接。此修正不是重新解释或覆盖旧取证。

正式新物品依赖核对须绑定实际HTTP200、正确title/item/AppID、同一次DOM及新匿名context。只有唯一、已加载且可见的`#rightContents > .sidebar`、独立Created by panel，以及本页File Size/Posted元数据均观察成功，才可以把两个Required栏目确实缺席记录为空数组。Updated若实际存在则记录；刚创建物品没有该字段不能单凭此判失败。未知布局、不可见、无匹配href、HTTP错误或登录页继续记`not_observed/unknown`和`null`。

栏目存在时分别限定store app href和Workshop item href提取ID，不把API缺字段当空，不扫描全部正文，不把隐藏的removed/incompatible/login模板当成可见状态。最终记录应保全HTTP正文SHA、DOM SHA、实际sidebar outerHTML/SHA、具体选择器、栏目标题/说明/可见性、完整href和两个实际ID数组；与公开元数据、完整notes及CDN核对结果合并后才能关闭发布门。

## 屏幕与游戏停机边界

匿名headless页面读取和纯本地冻结可以与验收任务并行；新attempt只写C盘。正式发布的Steam菜单操作必须等验收方保存全部结果、退出其拥有的CK3/启动器、交接屏幕租约，并由发布方复核当前进程归属及新鲜离线画面。发布原生流程无需启动CK3。

发布窗口顺序：当次租约和offline新帧 → 官方菜单online状态读回 → 当前账号/其他设备游戏占用观察及在线owner probe → 单一耐久Create receipt → 新ID媒体库存与独立media update → exact订阅1313与fresh下载3406/manifest → 立即官方菜单恢复offline并直接审阅新帧 → 匿名完整notes、元数据、CDN和依赖DOM回读。owner notes修正优先使用既有登录网页会话并保持Steam离线，只有实际原生动作才另开短在线窗口。EULA或未知Create结果交根任务保全同一receipt，不能盲目再Create或虚构同意。

正式staging、manifest、GREEN、纯production图和notes A/B字节绑定仍待交付；[发布执行输入](publication-execution-inputs.md)给出了对应原生JSON和命令。[永久changelog草稿](../../../docs/release-changelogs/superman-qiang/1.0.0.md)全部发布事实保持待补齐；草稿不关闭任何发布门。
