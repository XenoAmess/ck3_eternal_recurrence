# XenoAmess的体验优化：Steam Workshop 发布记录

收口时间：2026-09-11（Asia/Shanghai）
状态：**COMPLETE**

## 发布身份

- 产品：`mod_xenoamess_quality_of_life` 1.1.0
- 上一公开版本：1.0.2
- Steam Workshop item：[`3798133925`](https://steamcommunity.com/sharedfiles/filedetails/?id=3798133925)
- Git tag：`xqol-v1.1.0`
- Git commit：`a608d7d2082dfbb7206046eb0303f493433811db`
- GitHub Release：<https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/xqol-v1.1.0>
- 目标游戏：Crusader Kings III 1.19.0.6

## Steam 发布事实

- 通过本机 Steam 启动 PDX Launcher 2026.11.1 并更新同一 item；没有使用 Remote Play，也没有出现或接受新的 Workshop Legal Agreement。
- Launcher 日志 `C:\Users\1\AppData\Local\Paradox Interactive\launcher-v2\logs\launcher-2026-09-11.log` 于 `2026-09-11T09:23:42.499Z` 记录 `Publishing mod started`。本版 Launcher 没有写旧版的 terminal `succeeded` 行；成功页截图保存在 `D:\workspace\xqol-v1.1.0-publication\uploader-progress-latest.png`。
- 匿名 API 于 `time_updated=1789118637`（2026-09-11 17:23:57 +08:00）返回 content manifest `5269885934487179164`、`file_size=1054793`、`visibility=0`、标签 `Gameplay`。
- 标题精确为 `XenoAmess的体验优化`；远端描述仅去掉末尾 LF 后逐字符等于 `workshop/xenoamess_quality_of_life_description.bbcode`。
- 公开页面 `<title>` 与 Open Graph title 均为 `Steam Workshop::XenoAmess的体验优化`。
- 远端 preview 为 640×640 PNG、768,568 字节，SHA-256 `832e36c9394e6ed74aa8669507d55486ceacc0403f49daa8b456fc3cb1067fe3`，与 tag 产物逐字节一致。

## 冻结物料与 fresh-cache

| 物料 | SHA-256 |
|---|---|
| 正式 manifest | `ce17682bb5a26aeb61d81aee61959c0002db750e0076401662fc707b24c31bf6` |
| deterministic ZIP | `58f79aa467615d11d1473898b5b9e08f63b08d609a0ef0c68c575bffc5bbe9b8` |
| ID-bound sidecar manifest | `2b817bee6eec6b9813264fbaf7ba4f70c244412e9816a1fca997611fbf6a9abd` |
| thumbnail / remote preview | `832e36c9394e6ed74aa8669507d55486ceacc0403f49daa8b456fc3cb1067fe3` |

- 正式 staging：`D:\workspace\xqol-v1.1.0-publication\release\mod_xenoamess_quality_of_life`
- fresh cache：`D:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\3798133925`
- 旧缓存完整备份：`D:\workspace\xqol-v1.1.0-publication\pre-upload-cache-3798133925-20260911-174816`
- fresh-cache strict verify：24/24 GREEN；ACF 的 size/time/manifest 与匿名 API 一致。
- 上传后已从精确 tag 重建正式 staging；其内层 descriptor 无 `remote_file_id`，manifest/ZIP 哈希保持不变。
- 用户目录外层 `mod_xenoamess_quality_of_life.mod` 保留 `remote_file_id="3798133925"` 并指向正式 staging；仓库内层 descriptor 无 ID。
- GitHub Release 两个资产的服务端 SHA-256 digest 与上述正式 manifest/ZIP 完全一致。

## 实机验收

发布前完整 artifact：`D:\workspace\ck3_xqol_phase2_release_live1`

- L1/L2：GREEN；耗时 1069.261 秒；七项二期功能与一期回归在同一完整本机 CK3 会话全部 PASS。
- `report.json` SHA-256：`47a6fa24213e600b3c9fd8498273efe0efc5ae3ea27037f789be7ee554643e2f`。

发布后 fresh-cache artifacts：

- `D:\workspace\ck3_xqol_phase2_workshop_live1`：同一 fresh cache 上完整运行，一期回归与牵制索款、改信、两档赎囚、释放优先级全部 PASS；最后防御阶段因验收驱动的事件选择暂停后置条件保留为 harness RED。`report.json` SHA-256：`a878a183e599f58a079e009536f8f6bbe020796f2314291922fd11239340954e`。
- `D:\workspace\ck3_xqol_phase2_workshop_defense_recovery1`：只重跑未收口的防御矩阵，最终 GREEN，耗时 896.046 秒；`report.json` SHA-256：`08f847f98cc276d29a8eef80365134df0c87064f09221c663fb860875b5f91e8`。
- 两次运行使用同一 fresh-cache product tree SHA-256 `40416967e1da3e17a1439a14df97c81b5cd5567f48287cbd545e93ad064beac5`；source/runtime unchanged、MCP readiness、受保护存储与进程树清理均 GREEN。组合后的 L3 覆盖为 GREEN，且中间 RED 未被覆盖或删除。

完整测试边界与逐项哈希见 `mod_xenoamess_quality_of_life/docs/acceptance-report.md`。发布本地化审阅见 `docs/xqol-release-localization-review-2026-09-11.md`。

## CI 与发布记录

- exact tag CI：[`34581117770`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/34581117770)，GREEN。
- release-candidate master CI：[`34580639616`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/34580639616)，GREEN。
- 验收驱动恢复修复 CI：[`34591857017`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/34591857017)，GREEN。
- 相对 1.0.2 的永久 changelog：`docs/release-changelogs/xqol/1.1.0.md`。

## 后续更新规则

更新此 item 时继续使用 `3798133925`，但 canonical `remote_file_id` 只能存在于用户目录外层 `.mod`；不得预存到仓库或正式 staging 的内层 `descriptor.mod`。每次更新仍须完成 staging、上传、fresh-cache 核验、实机验收和相对上一公开版本的 changelog。
