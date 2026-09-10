# 《重整河山》宣传片制作与验收报告（2026-09-10）

## 结论

正式成片已完成制作，技术、素材血缘、术语、抽帧语义与自动证据审计均为 **GREEN**。仓库所有者随后回复
“通过”，其 approval 已按精确成片字节写入 native run，并生成离线正式交付包。未向外部视频平台发布。

候选片：

- 路径：`D:\workspace\ck3_reclaim_promo_work\renders\reclaim-promo-candidate-20260910-a03\deliverables\reclaim-the-motherland-promo-a01.mp4`
- SHA-256：`3E30299AAB75944D2A1C54E7044576816CEE5B61ED5032C5A1A7A917C577BE0B`
- 大小：37,258,304 bytes
- 规格：H.264 High，1920×1080，30 fps，yuv420p；AAC LC，48 kHz，双声道
- 时长：画面 96.000 秒；封装 96.021354 秒

## 已锁定创作合同

- 音乐采用 A03，源 SHA-256 为
  `0E4ED8EE2AA86BD676862B080707796430C2F8C2B2EF7934BDA053CF68EB92FB`。
- 权利说明按用户原话记录：A03 是本人付费方案期间生成并由 Suno 官方下载，不是 Remix。
- 旁白为 Edge TTS `zh-CN-XiaoxiaoNeural`。
- 结构为 88 秒主体加 8 秒自然尾音，总交付约 96 秒。
- 片尾保留“重整河山——一朝失鹿，尚可再兴。”
- DLC 术语全程使用“溥天之下 / All Under Heaven”，没有把“天下归心”呈现给观众。
- “保留领地”的叙述严格落在已验事实：旧天子继续持有割据前由其本人直属持有的伯爵领；没有宣称整个版图不变。

## 实机素材验收

素材来自 `reclaim-promo-capture-20260910-a02` 的可控实机存档拍摄。录制前按 MCP-first 流程将镜头锚定
`b_kaifeng`（province `9822`，county `c_bianzhou`），验收报告为 GREEN，11/11 个稀疏抽样帧均非黑屏且互异。
选片裁切只呈现正常玩家界面，不展示验收控制面板。

最终 visual master 为：

- SHA-256：`44F2A395C1A4C88289BD4FE9A512250285AD05C1E57A9E9486E82487343798E2`
- 时长：96 秒
- 关键修正：群雄割据段改用“后朝尚存”之后的开封/后宋镜头；废弃了曾出现印度地图的 a02 候选。

## 成片检查结果

准确定位抽检了 4、12、20、23、27、30、33、45、57、63、69、79、85、92 秒：

- 12 秒为大宋—开封地图，并显示 `大宋・开封 / Song・Kaifeng`。
- 20–30 秒依次呈现“后朝尚存”、后宋角色与开封中心地图；没有意大利或印度镜头。
- 57 秒为“宣称复辟”决议，69 秒为复辟诏告，79 秒为中华霸权恢复后的状态。
- 85 秒片尾卡包含中英标题、Steam Workshop、`溥天之下 / All Under Heaven` 与保留口号。
- 抽检画面没有验收专用控制面板。

音频机器检查：综合响度 `-21.9 LUFS`，响度范围 `17.6 LU`，True Peak `-6.2 dBFS`，无削波。
以 `-50 dB / 0.5 s` 检查只发现 0–0.556187 秒和 95.215229–96.021333 秒两段近静音，主体没有意外断音，片尾自然落至近静音。

## 证据与审片包

- native run：`D:\workspace\ck3_reclaim_promo_work\runs\reclaim-promo-render-20260910-a03\run-manifest.json`
- 自动审计：`automated-audit-a02/audit-report.json`，状态 `passed`，18/18 个计划样本具备完整 SHA-256 绑定证据。
- 项目语义审计：`project-semantic-audit-a03.json`，状态 `passed-pending-human-review`。
- 人工审片包：`D:\workspace\ck3_reclaim_promo_work\renders\reclaim-promo-candidate-20260910-a03\review-package-a01`
  ，含 34 张首尾、章节边界与关键内边界帧；该不可变预审包仍忠实保留生成时的
  `pending-human-review`、`approval_granted=false` 状态，后续 approval 记录在 run 的独立 signoff 中。
- 人工签核：`signoff-000001`，reviewer `repository-owner`，decision `approved`，时间
  `2026-09-10T00:51:13Z`，绑定上述精确 SHA-256。
- 离线正式交付：`D:\workspace\ck3_reclaim_promo_work\exports\reclaim-promo-release-20260910-a01\reclaim-the-motherland-promo.mp4`；
  export 为 GREEN，成片 SHA-256 不变，`release-bundle-manifest.json` SHA-256 为
  `D7C1BE5DD997C4D88386B8923CE86590D90AEB8A9A311170CABA7A23CA1E530B`。

以下 RED 尝试均保留且未覆盖：a01（GOP 解码后章节乱序）、a02（割据段误用印度地图）、首个自动审计尝试
（evidence bundle 根目录与 native run 不一致）。它们都不构成最终候选。

## 人工签核与发布边界

仓库所有者已在连续 1× 审片请求后明确回复“通过”，`xar-promo signoff` 与离线 export 均已完成。
任何重新编码仍会改变字节并使本次签核失效。签核只批准该成片，不等于指定或授权外部视频平台上传；本轮没有执行网络发布。
