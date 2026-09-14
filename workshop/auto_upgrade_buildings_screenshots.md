# 自动升级建筑：Steam 实机截图清单

状态：**已发布并通过匿名公开回读**。三张图片均来自 CK3 `1.19.0.6` 的 **R0033 GREEN 实机验收**，使用 4.0.0 最终决议插图与正式中文本地化。图片只做确定性的 JPEG 压缩，不裁切、不生成、不改写游戏画面，也不进入 Mod staging。

## 权威来源

- Workshop item ID：`3800124956`
- 页面：`https://steamcommunity.com/sharedfiles/filedetails/?id=3800124956`
- Run ID：`desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0033`
- Run：`D:\workspace\ck3_auto_upgrade_runtime\phase4-art-live-20260914`
- Wrapper report：`report.json`，结果 `GREEN`，SHA-256 `0c0c380f8c953180ea63eb0d525369fb5cfd3c2e2c577869cb0c5bc2b7952663`
- Cell report：`cell/report.json`，结果 `GREEN`，SHA-256 `e0b16fa0845450dd2ed0290e31a4ab8b78b3425604bb2d3409f04ffa963fd8a9`
- 游戏版本：CK3 `1.19.0.6`
- EXE SHA-256：`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`
- 产品树 SHA-256：`e85b0581ecfd8ea9fc50e63883999fd3150e96c2986f35e74b2b7f69690e6408`
- 投影脚本：`tools/compose_auto_upgrade_buildings_workshop_media.py`
- 编码：Pillow quality 90、optimized progressive JPEG、4:4:4；Steam 实测限制为单图小于 2 MB

## 上传顺序

| 顺序 | 玩法内容 | 原始实机画面 | 原图 SHA-256 | 仓库文件 | 尺寸 | JPEG bytes | SHA-256 |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 1 | 六种资金来源与超直辖策略完整选择器 | `cell/05_policy_selector_clean_surface.png` | `ca1687baced2205882c27192e8546705079e03358c213454cee57041cc38da9d` | `workshop/auto_upgrade_buildings_media/01_policy_selector.jpg` | 2560×1440 | 948,159 | `9dff96128f77c9226b993d0f5f9d20483f142e2621533351421969bac0f43f88` |
| 2 | “优先国库、超直辖暂停”的完整本地化 hover | `cell/05_policy_selector_hover_treasury_first_pause.png` | `4d3ec4f56dab7b7a015a07c522cb6f59b9929d736c668de0159f37271facded4` | `workshop/auto_upgrade_buildings_media/02_policy_hover_treasury_first_pause.jpg` | 2560×1440 | 948,779 | `a899c3528e75b434ab75ba36a3ba5685b577bda4dbefc1985a7c86f8b51bfa41` |
| 3 | 选定“优先国库、超直辖继续”后的自然确认文案 | `cell/05_policy_selector_natural_confirmation.png` | `344227287c91db6eafa305edd4afc77da8202d9c1732d7c4d515ca6857233703` | `workshop/auto_upgrade_buildings_media/03_policy_confirmation.jpg` | 2560×1440 | 902,352 | `f2ac53f23b944bcabd621c9c13b1c222a5269dc8cf30ba46464a2f38efa94200` |

推荐标题：

1. `六种资金与超直辖策略 / Six funding and domain-limit policies`
2. `优先国库，超直辖暂停 / Treasury first; pause over domain limit`
3. `选择前明确确认完整效果 / Confirm the complete policy before enabling`

## 取舍说明

- 不使用 R0032 图片：该轮发生在最终决议插图替换之前。
- 不使用 `08_acceptance_summary_event.png`：它属于验收夹具，不是普通玩家会看到的产品界面。
- 不使用 `05_policy_selector_executed.png`：截图处于窗口淡出中，视觉信息不完整。
- 三张图分别展示入口、解释与确认，能直接对应 4.0.0 的玩家可见玩法，不用普通地图画面凑数量。

## 发布证据

2026-09-14 通过目标物品的所有者页面逐张上传并保存。匿名公开页返回恰好三个 `highlight_strip_screenshot`，顺序与本清单一致；三个无参数 CDN 原图均为 2560×1440，下载字节与仓库 JPEG 逐张完全一致：

| 顺序 | Steam thumb ID | 公开 CDN 原图 | 匿名下载 SHA-256 | 结果 |
| ---: | --- | --- | --- | --- |
| 1 | `thumb_screenshot_47666524` | `https://images.steamusercontent.com/ugc/15692328034495717492/CEBFEBFC2249D1800C04A9C4076908AC720F2218/` | `9dff96128f77c9226b993d0f5f9d20483f142e2621533351421969bac0f43f88` | byte-exact |
| 2 | `thumb_screenshot_47666555` | `https://images.steamusercontent.com/ugc/13707642752009220109/25DFA79FC6A3CCBEF19881D2A89BA0079F7DC481/` | `a899c3528e75b434ab75ba36a3ba5685b577bda4dbefc1985a7c86f8b51bfa41` | byte-exact |
| 3 | `thumb_screenshot_47666593` | `https://images.steamusercontent.com/ugc/16725795040312459112/C3CC6D84E3445BB338171B9BF8FFDEABC4FCB7F0/` | `f2ac53f23b944bcabd621c9c13b1c222a5269dc8cf30ba46464a2f38efa94200` | byte-exact |

过程证据根目录：`D:\workspace\auto-upgrade-buildings-v4.0.0-publication\steam\workshop-media-20260914`。

- `public_media_readback.json` 冻结公开数量、顺序、尺寸、字节数、URL 与哈希，SHA-256 `353838b5f7a75e0fe94deef6be24ff4eb941a18862bd4d60963379fc138a4f16`。
- `public_page_after_media.html` 是匿名公开页原文，SHA-256 `4989f73bf27f44afb6f0f35a4f736834b0d8a8a0f1f3a1b79398a50323296b2b`。
- `media_offline_attestation.json` 记录 2026-09-14 20:21 Asia/Shanghai 的终态：Steam 客户端仍运行但已显示“离线模式”，CK3 与启动器进程均为 0；SHA-256 `5a4fea929284e73ac831dc24f7d0e4fc33848d68ad25d8d4b1bf09a9dd972a45`。
