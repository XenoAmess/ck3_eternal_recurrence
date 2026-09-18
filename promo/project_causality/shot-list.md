# 镜头清单与素材状态

状态词：`READY` 可直接进入粗剪；`REVIEW` 需检查 clean span；`CAPTURE` 必须补拍；`MATRIX` 只进入诚实产品矩阵。

| ID | 内容 | 当前素材 | 状态 | 正式候选条件 |
|---|---|---|---|---|
| P0-01 | 终末之契 | `screenshots/gallery/01_pact.jpg` | READY-STILL | 若无新录像，按已审计实机静帧使用 |
| P0-02 | 祝福三选一 | `screenshots/gallery/03_blessing_choice.jpg` | READY-STILL | 不声称自然随机序列 |
| P0-03 | 诅咒二选一 | `screenshots/gallery/04_curse_choice.jpg` | READY-STILL | 同上 |
| P0-04 | 琉焰账簿 | `screenshots/gallery/05_glassfire_ledger.jpg` | READY-STILL | 保留当前分数与阈值可读性 |
| P0-05 | 死亡结算 | `screenshots/gallery/10_death_settlement.jpg` | READY-STILL | 开场优先；不得拼成虚构完整人生 |
| P0-06 | 下一世当铺 | `screenshots/gallery/02_reincarnation_shop.jpg` | READY-STILL | 显示真实商品，不使用测试教程位 |
| P1-01 | 白绮廷臣 | `images/vivhite_courtier_key_art.png` + 主产品廷臣实机图 | MATRIX | 正式版最好补独立版干净 gameplay |
| P1-02 | 361 公开版 | `mod_zhongguo_style/workshop/media/*.jpg` | READY-STILL | 只用公开能力，二期完全排除 |
| P1-03 | 牛来 | `workshop/ox_here_media/*.jpg` | READY-STILL | 到庭事件和人物状态均为公开实机图 |
| P1-04 | 体验优化 | 产品 thumbnail | MATRIX | 无干净 gameplay 时只进入产品矩阵 |
| P1-05 | 自动升级建筑 | `workshop/auto_upgrade_buildings_media/*.jpg` | READY-STILL | 政策与确认画面不外推完整长期循环 |
| P1-06 | 重整河山 | `workshop/reclaim_the_motherland_media/*.jpg` | READY-STILL | 使用 0.4.0 合同内画面 |
| P1-07 | 肃清曼荼罗 | `workshop/remove_mandala_media/*.jpg` | READY-STILL | 明确是制度环境规则 |
| P1-08 | 驱策朝贡国 | `workshop/tributary_expansion_directives_media/01_directed_war_live.jpg` | READY-STILL | 不外推所有接受/拒绝分支 |
| P2-01 | 家徽编辑器 | `artifacts/project-causality/2026-09-19-r1/coa-production-capture/` | REVIEW-WEB | 生产页 GET-only 录屏已覆盖载入实机样例→解析→预览→复制；图片拟合动态可在精剪时补拍 |
| P2-02 | 自动玩家 OODA | 2026-08 月报与 source clips | REVIEW | 只取 artifact 绑定的有界 loop，不使用宗教泛化 |
| P2-03 | checkpoint 恢复 | 月报 segment 与 sidecar | REVIEW | 恢复前后身份必须同一证据链 |
| P2-04 | open_kaishek | 文档与 CLI 可用 | CAPTURE | 冻结独立仓 commit/profile/verdict |
| P2-05 | Workshop MCP | 文档与历史 receipt | CAPTURE | WAL、UIA、native readiness 分开显示 |
| P3-01 | 权威文档 | 仓库 Markdown | READY | 只突出一条规则，不滚动整屏 |
| P3-02 | 生成器 | 仓库脚本与生成物 | READY | 同一 schema 到多类输出的真实 match cut |
| P3-03 | 离线 GREEN | 静态命令可运行 | CAPTURE | 使用本次冻结 commit 的真实输出 |
| P3-04 | typed MCP state | 历史 agent 录像 | REVIEW | 与同帧 CK3 UI 对照，说明证据等级 |
| P3-05 | OCR | 历史 acceptance 流程 | CAPTURE | 只核对可见文字，不宣称隐藏状态 |
| P3-06 | ACK 与后置状态 | 历史 notification/war clips | REVIEW | ACK 先出现、独立后置状态后出现 |
| P3-07 | staging/manifest/ZIP | release builder | READY | 哈希完整值进入 sidecar |
| P3-08 | fresh-cache/readback | 产品发布记录 | REVIEW | 只使用已有真实回读，不触发新上传 |
| P4-01 | 四 Loop 动画 | `images/project_causality/promo/chapter_vision.png` | READY-VISION | 常驻 `VISION / TARGET SYSTEM`，实虚线重绘 |

## 一日制作的补拍优先级

1. 家徽编辑器生产网页；
2. `open_kaishek` 冻结 CLI verdict；
3. release builder 的 staging/manifest/ZIP；
4. 从现有自动玩家素材中选择无重复字幕、能读清 OODA 的 clean span；
5. 只有时间允许时再补白绮独立版和 QoL gameplay。

任何补拍失败都保留 RED；优先缩小声明或退回产品矩阵，不延展为功能开发。
