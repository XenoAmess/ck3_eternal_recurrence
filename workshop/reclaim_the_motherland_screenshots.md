# 重整河山 0.2.0：Steam 实机截图清单

状态：四张候选图均来自同一次 **GREEN 的 CK3 1.19.0.6 源码树 MCP-first 验收**，已完成确定性裁切和逐张视觉检查；等待 0.2.0 上传后作为公开页面素材复核。

## 权威来源

- Workshop item ID：`3798404599`
- 页面：`https://steamcommunity.com/sharedfiles/filedetails/?id=3798404599`
- Run ID：`desktop-3fevhd2-1c74096080--reclaim-the-motherland--R0004`
- Run：`D:\workspace\ck3_reclaim_phase2_20260913_process_assets\reclaim\runs\desktop-3fevhd2-1c74096080--reclaim-the-motherland--R0004-source`
- Wrapper report：`report.json`，SHA-256 `962c679a10ae669201eff32cb62f2cb442ab5189cffd0037ee9af4f03071f85a`
- Cell report：`cell/report.json`，SHA-256 `53ed9ecf85166c4f3e0335777c641b64f5043ffe7b7ec0fe56db1fd6b9bb83e9`
- 结果：wrapper/cell 均为 `GREEN`；20 个顺序标记全部出现；项目 diagnostics 为 0；source/runtime 和保护存储未改写；CK3 进程树已受控回收。
- 游戏：CK3 `1.19.0.6`
- EXE SHA-256：`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`
- 投影脚本：`tools/compose_reclaim_the_motherland_workshop_media.py`

## 大宋首都镜头门禁

素材不使用快捷键猜测，也不从错误地图区域后期伪造。runner 通过原生 MCP `ck3_center_map_on_landed_title_v1` 将镜头定位到 `b_kaifeng`，并保存机器可读证据：

- `cell/08_song_capital_navigation.json`：SHA-256 `a94386f1750e3f40a071ac8e2493e4f96e7d1bff0af52b3e934e6b5ae79a67b5`。
- `cell/08_song_capital_map.png`：SHA-256 `a3da7a1f379d9b18ebc544f571ff53fce9d28e29f81005c626a40d5cef5d6d3e`。
- MCP 回执证明 target/current 已收敛且 `settled=true`、`postcondition_verified=true`、`target_write_blocked=false`。
- composer 会重新读取 GREEN wrapper 和镜头证据；门禁失败即拒绝生成 JPG。

## BBCode 与 media strip 顺序

| 顺序 | 仓库文件 | 原始实机画面 | 裁切框 | 尺寸 | JPEG bytes | SHA-256 | 中英文说明 |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| 1 | `workshop/reclaim_the_motherland_media/00_divided_hearts_live.jpg` | `cell/07_loyalty_summary.png`（SHA-256 `981150fa0f62f43c19cbb8c5b5157cb890b72b6e50f8e8f2fb01062472c1a1a9`） | `(300,180,1690,920)` | 1390×740 | 228,473 | `bdf2d4b38c6daa66ffe81b1dc881d7d017da137cbd5048d37427d09dd8944888` | Divided Hearts / 人心向背 |
| 2 | `workshop/reclaim_the_motherland_media/01_later_dynasty_live.jpg` | `cell/08_later_dynasty_character.png`（SHA-256 `f915eb1492c4c64934a2ba04e029730f1b207167331a6eabb248a653749a1897`） | `(0,0,1500,1050)` | 1500×1050 | 512,586 | `3be1a698e51a96c4064311e04216784f676c31388888da13f639e23810597743` | Later Song at Kaifeng / 后宋立于开封 |
| 3 | `workshop/reclaim_the_motherland_media/02_restoration_decision_live.jpg` | `cell/09_decision_visibility.png`（SHA-256 `b10f2c4dcdd358482833e6ebfa1e5eb57ae20900a6462f0eb563c86544f6b656`） | `(1400,275,2540,650)` | 1140×375 | 114,128 | `b443e478e90acf29608fe87b19cb5ce0b1d1c17d2bd78a9eb966a6a898bfc309` | Proclaim the Restoration is ready / 宣称复辟已就绪 |
| 4 | `workshop/reclaim_the_motherland_media/03_restoration_confirm_live.jpg` | `cell/10_restore_confirm.png`（SHA-256 `3f98010160a33f17b7b8f1c0bcd18a6c9f3a3ed21b4a7f4beb5123d8bf48ec85`） | `(380,275,1800,1130)` | 1420×855 | 286,425 | `07dfd518e43762918e4681deb3218656e761a20fa85af60a795ceef413021ba2` | Restoration proclamation and effect / 复辟诏告与效果 |

## 真实性与使用边界

四张 JPEG 只做裁切和有损编码，没有生成或改写游戏内容。首图显示正式产品事件【人心向背】，且裁掉验收抽屉与测试通知；第二张同时显示后宋人物和开封地图；第三、四张只保留普通玩家可见的决议 UI。生成式主视觉只用于 `thumbnail.png`，不冒充实机截图。

Workshop BBCode 必须使用 commit-pinned GitHub raw URL；Steam media strip 按本表顺序上传或复核。所有中英文文案统一使用《溥天之下 / All Under Heaven》。

## 发布证据

0.2.0 尚未上传。正式发布后在此补充：上传回执、公开页面/API 复核、四张素材公开可见证据、必需 DLC 复核，以及 fresh-cache L3 run。
