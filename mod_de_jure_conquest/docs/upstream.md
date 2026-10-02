# 来源与环境冻结

日期：2026-10-03。状态：**公开来源与上游 bytes 已冻结；维护源码已导入。**

## 来源身份

- 上游名称：公国/王国/帝国法理征服。
- 原作者：白绮。
- 上游 Workshop item：`3600021457`。
- [公开页面](https://steamcommunity.com/sharedfiles/filedetails/?id=3600021457)。
- 页面读取日期：2026-10-03；匿名网页可读取描述与评论。
- 页面显示发布时间：2025-11-04；更新时间显示为 `29 Apr @ 4:22pm`，页面未显式给出更新年份，本记录不推断年份。
- 页面文件大小：138.655 KB；不是下载文件总字节，也不是源码文件清单。
- 维护版 Workshop item：**尚未创建**。上游 ID 只标识来源，永不作为维护版发布目标。

## 原始字节

主执行者经原生 MCP `DownloadItem` 取得，callback `3406`、`EResult=1`、`Subscribed=false`；不证明维护版已发布。

- 缓存：`C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/3600021457`。
- 不可变原始快照：`C:/workspace/two-mod-maintenance-20261003/upstream-3600021457-original/`。
- manifest：`C:/workspace/two-mod-maintenance-20261003/3600021457-upstream-manifest.json`。
- 下载回执：同目录 `3600021457-download-stdout.json`。
- 冻结时间：`2026-10-02T22:54:47.976206+00:00`。
- 文件数 `8`，总字节 `138655`，tree SHA-256 `6A8FABF7200130185850280E71AF3CA9C741FD3959D03C45E4119A8BA83203E1`。
- 原始 descriptor：`version="1.18"`、`supported_version="1.19"`、上游 remote ID；维护副本已删除 remote ID。原图原样保留，SHA `7b9d9de50b9a8a9fdf83bc89996330ea12f28a4a2396006d733043a8840c0465`。

原始文件为三份 `common/casus_belli_types/*_de_jure_greatwar.txt`、`common/on_action/greatwar.txt`、descriptor、两语 yml 和 thumbnail；逐文件 bytes／SHA 以冻结 manifest 为准。原始快照未被适配脚本修改。

取得后应保存一次性外置原始快照及每文件 path/size/SHA-256 清单，禁止在原始树内删除 `remote_file_id` 或修脚本。规范化 tree hash 按相对路径排序，UTF-8 每行 `<path>\0<size>\0<SHA256>\n`；路径分隔符 `/`。可维护副本内才可删除上游 remote ID、规范化文本编码并实施适配。

## 授权状态

用户已明确要求本产品独立第三方维护并分别发布，是当前工作授权链。8 个原始文件未携带 LICENSE，也未附作者单独许可记录；不据此制造额外审批。仍须如实记录来源状态，不套用自动升级建筑的许可，不在 Workshop 文案中声称本产品已取得原作者单独授权。

## 本机目标构建

- CK3：`1.20.0.3 (Crozier)`，从本机 `launcher/launcher-settings.json` 的 `rawVersion`／`version` 读回。
- Steam build：`25652598`，由主执行者提供；本工作包尚未独立读取 appmanifest。
- 安装目录：`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`。
- EXE SHA-256：`94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。
- `game/common/casus_belli_types/_casus_belli.info` SHA-256：`270343ebae0f8ebd2e4d24f9f839a7c77cb663836d9b36af6d5138a58755bb05`。
- `game/common/casus_belli_types/00_religious_war.txt` SHA-256：`5c4b6af8742f65a720529434a2997e83ec93b6cfa8d594204ca914ae6c359d33`。
- `game/common/casus_belli_types/00_dejure_war.txt` SHA-256：`18c0d3647fd936b37e3d26e28980ec45657841414d6397667891ad2e73ac1f85`。
- 实体 Python：`C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe`。本机 PATH 的 `python` 为 WindowsApps 占位入口，`py` 不存在；未用缺依赖的默认解释器判定产品 RED。
- 本工作包未启动 CK3，未改变 Steam 联机状态，未操作账号；实机前离线新鲜画面由主执行者取证。
