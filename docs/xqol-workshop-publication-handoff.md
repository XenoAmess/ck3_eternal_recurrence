# XenoAmess的体验优化：Steam Workshop 发布记录

收口时间：2026-09-09（Asia/Shanghai）
状态：**COMPLETE**

## 发布身份

- 产品：`mod_xenoamess_quality_of_life` 1.0.2
- Steam Workshop item：[`3798133925`](https://steamcommunity.com/sharedfiles/filedetails/?id=3798133925)
- Git tag：`xqol-v1.0.2`
- Git commit：`a8acdc19c36a94e807c11f047f3d4bc85f7ff941`
- GitHub Release：<https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/xqol-v1.0.2>
- 目标游戏：Crusader Kings III 1.19.0.6

`xqol-v1.0.0` 与 `xqol-v1.0.1` 是未公开候选；1.0.2 是该 Workshop item 的 initial public baseline。

## Steam 发布事实

- Launcher 上传成功时间：2026-09-09 01:20:02（Asia/Shanghai）。
- 证据：`C:\Users\1\AppData\Local\Paradox Interactive\launcher-v2\logs\launcher-2026-09-09.log` 第 1784 行 `Publishing mod succeeded`。
- 上传过程没有出现或接受新的 Workshop Legal Agreement。
- 匿名 API 与公开页面均确认：item ID `3798133925`、`visibility=0`、标题 `XenoAmess的体验优化`、标签 `Gameplay`。
- 远端描述仅规范化 CR/LF 与末尾换行后，逐字符等于 `workshop/xenoamess_quality_of_life_description.bbcode`。
- 远端 preview 为 640×640 PNG、768,568 字节，SHA-256 `832e36c9394e6ed74aa8669507d55486ceacc0403f49daa8b456fc3cb1067fe3`。
- 描述中的 commit-pinned GitHub raw 主图返回 HTTP 200，大小 768,568 字节。

## 冻结物料与 fresh-cache

| 物料 | SHA-256 |
|---|---|
| 正式 manifest | `d1618abc1ffe6b3f2e611799001b72793ac99676f8fd5b28061f724d07538ce3` |
| deterministic ZIP | `edf50efd2d64044c1ea62f9c9177759d375324dabf2e08aea56d1acb124e95c7` |
| ID-bearing sidecar manifest | `a896600926a79d31ff3bc53e9d162c47666547d1965be407d2269734d916ed7b` |
| thumbnail / remote preview | `832e36c9394e6ed74aa8669507d55486ceacc0403f49daa8b456fc3cb1067fe3` |

- 正式 staging：`D:\workspace\xqol-v1.0.2-publication\release\mod_xenoamess_quality_of_life`
- fresh cache：`D:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\3798133925`
- fresh-cache strict verify：19/19 GREEN。
- 最终从精确 tag 重建正式 staging 后，内层 descriptor 已恢复为无 `remote_file_id`，manifest/ZIP 哈希保持不变。
- 用户目录外层 `mod_xenoamess_quality_of_life.mod` 保留 `remote_file_id="3798133925"` 并指向正式 staging；仓库内层 descriptor 无 ID。

## 实机验收

最终 artifact：`D:\workspace\ck3_xqol_publication_process_assets\xqol\runs\zqa_20260909_043524_3fe57500`

- L1/L2/L3：GREEN；耗时 623.051 秒。
- MCP readiness：GREEN；fresh-cache/source unchanged；进程树清理证明 GREEN；受保护存储 unchanged。
- 死亡、卸任、启用/关闭、原版继任恢复、禁转 flag 所有权与既有 flag 保留全部 PASS。
- `report.json` SHA-256：`b01a7ee987ca591aee4e2abffcbf9b81f2c833743490830cd123ed8730a5b19a`
- `cell/report.json` SHA-256：`2d01847d7dfeb913806376f56010627260da6ea855fea132188319d0d8454264`
- `04_mcp_readiness.json` SHA-256：`679e5406bb6a0a17eedb5695f83846bad293c281daaed5a328239597cb8cb938`
- `09_death_settlement_tick.json` SHA-256：`dfeb9eb738461ad11bf86cc40c20629eb723d6105bc26b65c6da16657fecd746`

完整测试边界、open_kaishek tool-coverage RED 与保留失败尝试见 `mod_xenoamess_quality_of_life/docs/acceptance-report.md`。发布本地化审阅见 `docs/xqol-release-localization-review-2026-09-08.md`。

## 后续更新规则

更新此 item 时继续使用 `3798133925`，但 canonical `remote_file_id` 只能存在于用户目录外层 `.mod`；不得预存到仓库或正式 staging 的内层 `descriptor.mod`。每次更新仍须完成 staging、上传、fresh-cache 核验、实机验收和相对上一公开版本的 changelog。
