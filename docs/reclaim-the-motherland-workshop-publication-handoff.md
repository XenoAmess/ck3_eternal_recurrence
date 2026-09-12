# 重整河山：Steam Workshop 发布交接

状态：**0.2.0 发布闭环完成。正式上传、公开描述、Change Notes、全新订阅缓存与 MCP-first L3 均已复核。**

## 公开产品

- 产品：`mod_reclaim_the_motherland`
- 版本：`0.2.0`
- Workshop item：[`3798404599`](https://steamcommunity.com/sharedfiles/filedetails/?id=3798404599)
- 应用：Crusader Kings III（App ID `1158310`）
- 依赖：`Crusader Kings III: All Under Heaven`；中文统一写作《溥天之下》
- 可见性：Public；Steam 匿名接口返回 `result=1`、`visibility=0`
- 标题：`Reclaim the Motherland — 重整河山`
- 公共文件大小：949,064 bytes；`time_updated=1789251577`
- BBCode 权威源：`workshop/reclaim_the_motherland_description.bbcode`
- Change Notes 权威源：`workshop/reclaim_the_motherland_change_notes_0.2.0.txt`
- 截图来源与顺序：`workshop/reclaim_the_motherland_screenshots.md`

## 正式构建与上传身份

- tag：`reclaim-motherland-v0.2.0`
- tag target：`6486a0c72dda61c3b4e4466bc9db1193e83c74bc`
- 精确 tag worktree：`D:\workspace\ck3_reclaim_v020_tagbuild`
- 上传及重建 staging：`D:\workspace\reclaim-motherland-v0.2.0-publication\release\mod_reclaim_the_motherland`
- 文件数：32
- manifest SHA-256：`2d63b2c6d72db677a06644d61ee6b909e639c30d99f2ce9fc153f12f16ccce73`
- deterministic ZIP SHA-256：`5981535815e61dd92c5f681a2fea9f9804cd58ffb545f5fe6f1310d9af6c8550`
- thumbnail：803,154 bytes；SHA-256 `564a558d5dc280e9049fb6907db36418a9a29085802da2ce8bed0f1dff6e1c38`
- native publish plan SHA-256：`3c60a0e3f079cf1e4cf2f7de1fa751d686f3b19faecb627bd01519bf604cab4e`
- payload SHA-256：`1659038e01959d01404f97a9b9e6ca0b346437b8fd0194a741db99a1fd5d4083`
- native receipt SHA-256：`d33334e040b59c21fc7757f78445ee70596c8a4b3f80d7b10788caadeaffbc11`
- Steam result：`1`；提交时间：2026-09-13 06:19:29（Asia/Shanghai）

上传后已从 exact tag 再建一次 staging；两次 manifest/ZIP 哈希相同，内层 `descriptor.mod` 不含 `remote_file_id`。Workshop item ID 只保存在外层 launcher descriptor、ID-bearing manifest 与发布证据中。

## 公开回读

- 匿名 `GetPublishedFileDetails` 的标题、可见性、标签和 5,446 字规范化描述与入库 BBCode 精确一致。
- 公开 item 回读：`D:\workspace\reclaim-motherland-v0.2.0-publication\steam\public_item_readback.json`；SHA-256 `ade3b8fe6423c800edfd7d14ec05f687103acf6d319bf97821ad8ed0d41f669b`。
- BBCode bytes：7,479；SHA-256 `267c6c0b03e00d599ca2ed971aaaa641a1a1067e4ca1e96f256ea8514eb8b6d2`。
- 新 Change Notes entry：`1789251577`。
- 公开正文与权威源逐字符相同：508 字、14 行、保留末尾换行；UTF-8 SHA-256 均为 `368a357002ec6e9bdb3fb181881257926e5a8184c8d8ee86aa29d9f7dc06cad2`。
- 匿名 changelog HTML SHA-256：`80221726c46f240331615a9b4c6e18c10b934e14b12b6402b82f4e064d4ad8e6`。
- 精确 Change Notes 回读：`D:\workspace\reclaim-motherland-v0.2.0-publication\steam\public_changelog_readback.json`；SHA-256 `7840809031cc91794c30dbc3fc576c93b757ee12287766ab97b7294696dcbad5`。
- 四个 commit-pinned GitHub raw 素材 URL 均返回 HTTP 200，Content-Length 分别为 228,473 / 512,586 / 114,128 / 286,425 bytes。

## 全新订阅缓存与 L3

- 旧 0.1.1 缓存已可恢复地移动到 `D:\workspace\reclaim-motherland-v0.2.0-publication\steam\3798404599.before-v0.2.0-20260913-0620`，共 28 文件；没有删除。
- Steam 控制台重新下载到 `C:\SteamLibrary\steamapps\workshop\content\1158310\3798404599`。
- 新缓存 32/32 文件按正式 ID-bearing manifest 严格匹配。
- 缓存核对记录：`D:\workspace\reclaim-motherland-v0.2.0-publication\steam\fresh_cache_verification.json`；SHA-256 `d03e70fb410b22a01b548883a086b851b5bf784c3769124191b2c5c296a9471c`。
- Steam 原生上传保留 canonical 无 ID inner descriptor；验证器已在 commit `52456f9f` 修正为同时接受这种精确形式和 Launcher 唯一末行 ID 形式，10/10 focused tests GREEN。
- 最终 run：`desktop-3fevhd2-1c74096080--reclaim-the-motherland--R0007`
- execution ID：`dee5e47a-6108-4720-86e9-c8370e5f8cf7`
- 路径：`D:\workspace\ck3_reclaim_phase2_20260913_process_assets\reclaim\runs\desktop-3fevhd2-1c74096080--reclaim-the-motherland--R0007-workshop`
- wrapper/cell：GREEN / GREEN；20 个顺序标记；项目 diagnostics 为 0。
- wrapper SHA-256：`fc77bbff14ef2be971f727d0875c52e181aac35bce52d7a2808e56d283286512`
- cell SHA-256：`8cc4cfbfc57b3bb7e1a6eac3385052bf58d364a5caa95501ae505b0193eebfb2`
- live identity receipt SHA-256：`39f62d4eeb16a6df8c9226f2ef42ccb37c779ce8c640fda9297e3e779a97b58d`
- open_kaishek preflight SHA-256：`cff13f7d2be8ed65610a22886195536b569458b12daac8906a1464c4664189cf`
- runtime product/fixture SHA-256：`b849da37bcb8901aa27b9a06d53b4bb4a247025ac9f2c775e54588d40933e119` / `8aea8e4e2df5eec325ff8d3315c184064f00fc798633228a0ee2098205c5ab99`
- 时长：764.041 秒；CK3 槽位等待 0.125 秒。
- source/runtime、保护存储均未改写；隔离 userdir 已删除；CK3 进程树回收已证明。

`R0005` 是保留的 environment RED：detached worktree 未显式设置迁移后的 `XAR_CK3_EXE`，在 preflight 即停止，没有启动 CK3。`R0006` 是单独的 GREEN preflight-only 记录，没有启动 CK3；完整 L3 使用新的 `R0007`，没有覆盖前两次记录。

## 本机收尾

Steam 已在发布和下载后恢复 Offline Mode：`WantsOfflineMode=1`，connection log 记录用户发起的 LogOff，带 AppID 1158310 的本地 Steamworks probe 返回 `STEAM_USER_OFFLINE / BLoggedOn=false`。Steam 客户端仍运行，CK3 进程数为 0。最终记录为 `D:\workspace\reclaim-motherland-v0.2.0-publication\steam\final_offline_attestation.json`，SHA-256 `a48c09d45e2f2c57b5bd0d056af91b055723d67c510292b73dceb72d9cd34561`。

## 后续更新规则

1. 修改源码后先做与风险相称的 L0/L1，并从新 tag 生成唯一正式 staging。
2. 只能上传 staging；内层 descriptor 不得预置 `remote_file_id`。
3. 更新同一 Workshop item `3798404599`；必须独立精确回读公开 Change Notes，不能只信 submit 回执。
4. 上传后从全新订阅缓存做 manifest 核对和 MCP-first L3，并再次重建无 ID 的正式 staging。
5. 页面素材必须来自真实 GREEN run；中国地图镜头继续以原生 MCP 定位 `b_kaifeng`。
