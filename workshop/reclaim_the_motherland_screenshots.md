# 重整河山：Steam 实机截图清单

状态：三张候选图均来自同一次 **GREEN 的 CK3 1.19.0.6 Workshop fresh-cache MCP-first 验收**，已完成确定性裁切与人工逐张视觉检查；Steam media strip 上传、排序和公开页面复核待执行。

## 权威来源

- Workshop item ID：`3798404599`
- 页面：`https://steamcommunity.com/sharedfiles/filedetails/?id=3798404599`
- Run：`D:\workspace\ck3_reclaim_the_motherland_design_process_assets\reclaim\runs\rqa_workshop_20260909_1952_capital_3798404599_v011`
- Wrapper report：`report.json`，SHA-256 `6d5ad36cd296f61a83573b501a566c90ec918e9d811ab5b38eb41ade3513c6ab`
- Cell report：`cell/report.json`，SHA-256 `5859e13cdf06f8287cb2a28aa1f3d72669d4d33ff2cb50fb4ab691dee4938e30`
- 结果：wrapper/cell 均为 `GREEN`；19/19 fixture markers；项目 diagnostics 为 0；source/runtime 和保护存储未改写；CK3 进程树已受控回收。
- 游戏：CK3 `1.19.0.6`
- EXE SHA-256：`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`
- 投影脚本：`tools/compose_reclaim_the_motherland_workshop_media.py`

## 大宋首都镜头门禁

商店素材不使用快捷键猜测，也不从错误地图后期裁切。进入群雄割据、关闭验收窗口后，runner 通过原生 MCP `ck3_center_map_on_landed_title_v1` 把镜头定位到 `b_kaifeng`：

- MCP 返回 `accepted=true`、`title.key=b_kaifeng`、`anchor_kind=title_bounds_center`、`capital_province_id=9822`。
- 相机目标为 `[6836.0, 0.0, 2619.0]`；`current_state == target_state`、`settled=true`、`postcondition_verified=true`、`target_write_blocked=false`。
- 无面板截图 `cell/08_song_capital_map.png`，SHA-256 `772defc92ca9846758a5e42da554d5b5ec021b1e290c747d9736491a4cdc150a`。
- 镜头证据 `cell/08_song_capital_navigation.json`，SHA-256 `cc280aaadd48a2ab4fc3d8f193f3edcfe6e0afbb92042c1a832077e1e92acdde`。
- 视觉辅证命中开封周边“管城县”，且“教宗 / 教宗国 / 意大利 / 罗马 / 那波利 / 萨莱诺”均未出现；“验收”字样也未出现。
- composer 会重新读取 wrapper GREEN 与上述 MCP/视觉证据；任一条件失败即拒绝生成三张 JPG。

保留的 RED attempt `rqa_workshop_20260909_1940_capital_3798404599_v011` 已证明 MCP 实际成功定位开封，但首版只接受“开封/汴州”文字；详细地图层级渲染“管城县”导致它按设计失败。该 run 不用于商店素材，也未被覆盖或删除。

## 上传顺序

| 顺序 | 仓库文件 | 原始实机画面 | 裁切框 | 尺寸 | JPEG bytes | SHA-256 | 中英文说明 |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| 1 | `workshop/reclaim_the_motherland_media/01_later_dynasty_live.jpg` | `cell/08_later_dynasty_character.png`（SHA-256 `4c3c7e5df7ba67f51d01609ae40dd1a5ad2e8b04fc22def22910d43a53806595`） | `(0,0,1500,1050)` | 1500×1050 | 515,634 | `603071742f6d450fb9867f0d40b60108886769be2f67802640b9e726dea91f51` | Later Song at Kaifeng / 后宋立于开封 |
| 2 | `workshop/reclaim_the_motherland_media/02_restoration_decision_live.jpg` | `cell/09_decision_visibility.png`（SHA-256 `b2c3f08b75cd37261147931b99af1033de65c69e3e855d0102b490654900dcb9`） | `(1400,275,2540,650)` | 1140×375 | 115,500 | `00e307d670ebe8b2f73eb05c2b49c92adc14c901a1b97342a35713ebe06dea14` | Proclaim the Restoration is ready / 宣称复辟已就绪 |
| 3 | `workshop/reclaim_the_motherland_media/03_restoration_confirm_live.jpg` | `cell/10_restore_confirm.png`（SHA-256 `262de0eb4603b5990ebd279de045103f71da061a51552f639b650150d0e5471d`） | `(380,275,1800,1130)` | 1420×855 | 277,263 | `e3886bf3b385bbacf7d4b5b413c0e5e4ccf1c87de4735eeb05de14b459d08bca` | Restoration proclamation and effect / 复辟诏告与效果 |

## 真实性与使用边界

三张 JPEG 只做裁切和有损编码，没有生成或改写游戏内容。第一张同时显示“后宋”主头衔和开封地图；第二、三张裁掉验收专用决议组，只保留普通玩家能见到的产品决议 UI。生成的主视觉只用于 `thumbnail.png`，不冒充实机截图。

Workshop BBCode 使用 commit-pinned GitHub raw URL；Steam 页面还必须把本表三张 JPEG 作为独立 media strip 按顺序上传。正式公开后回填页面可见性、媒体数量与顺序复核结果。

## 发布证据（待回填）

- 页面公开可见性：待执行
- media strip：待上传并复核为 3 张
- 页面顺序与标题：待公开页面复核
