# R87：原版儒家基线与准备合格，制度议案进入推举阶段，尚未建立宗主

2026-10-14（北京时间）。R87 从 R79 的真实资格存档重新启动，使用 0.1.2 正式 83 文件候选；manifest SHA-256 为 `c3c8a398ff97c9b1af360b642bf235a973020be6613bceb7de196eae616cb1bc`。A57 有限准入、全新 Steam 离线画面、独占屏幕和 1500 秒冷启动门槛均成立。CK3 1.20.0.4 装入源存档 SHA-256 `f91795ad026e42ca5c958a5c50af949bb103381073d1ccb34fc51d05dab24e9d`，原生回读玩家31254、日期原值53144328、原版 `confucian_faith` Faith31、儒教宗教9、原主礼仪33、本人白沙礼仪174。当前信仰有4677名在世成员、38个礼仪，其中2派活跃；原生宗教头衔读口确认 `legal_head_title_absent=true`。ROOT 直接查看了当前玩家身份、原版道学信仰面板和“无信仰领袖”。基线与准备阶段均按原固定期限提交 `complete/qualified=true`。

准备阶段把 R79 存档中的真实入门、T35、T08 来源与本场当前身份绑定，确认发起者学识16、两个活跃礼仪各有实际合格的可提名学者。这只证明**候选池存在**，不是代表已经接受提名。ROOT 使用正式“议建共同体宗主制度”决议，出现 `lyd.430`“完整名单与制度条款”事件。此时原生事件选项仅列出“本轮制度实施条件尚未齐备”、“待诸方答复”和“撤回本轮”，没有“按已重核授权实施”选项；事件保存阶段值1。界面进度提示显示原版主礼仪道学尚无已接受代表、279名合格学者中本轮授权0人；白沙礼仪也尚无已接受代表。源码 `lyd_i3b_ready_trigger` 要求阶段2、各活跃派代表/三分之二授权/签署及玩家同意；因此当前未出现实施选项符合门槛设计，不能据此说宗主创建失败或成功。R87 未提交代表接受、封定、投票、签署或实施选项，也未证明 NPC 行为。宗教头衔仍不存在。

制度阶段固定期限 `2026-10-13T23:29:09Z` 到达时尚未完成上述步骤，公共 case 原始错误为 `TimeoutError: Original normal Quit reserve reached; pending Root phase remains GAP`。`business_pass=false`；不把基线/准备两个合格 cell 外推为完整 I3b、C3、B4/B5 或 36 信条功能验收。原始 `case-error-preserved.json` 保留 RED；public run 返回2。

正常退出独立合格：ROOT 在新鲜原始1920×1080截图中确认“保存游戏作为 autosave_exit”复选框未勾选，经 `desktop_coordinate_map.py --click --receipt` 点击“退出到桌面”；映射 sidecar 证明前后焦点同属 PID15464。保留进程返回 CK3 OS0，native 报告 `GREEN/cleanup_ok=true`，host 原始退出0，`normal_close_qualified=true`。显示器恢复1024×768，keeper 完成，屏幕租约序号5703→5704以精确 CAS 释放；Steam 保持离线。

本次四根清理前实际逻辑量913,583,468 B，超过 A57 的512 MiB 预约，不能把初始超限略去。闭场后按[通用存储策略](../../../storage-retention-policy.md)逐文件回收：三个91,609,185 B的游戏自动存档 SHA 完全相同，保留 `xar_checkpoint.ck3`、删去 `autosave.ck3` 与 `last_save.ck3`；本场 `restored_campaign.ck3` 与 R79 原源存档 SHA 完全相同，源件仍在且可读，删去本场副本。三份原始 native wire/call 线流分别无损压缩为单成员 ZIP，逐份解压回读 SHA 与原件一致后才删原文件。六个精确文件共释放原始逻辑量454,495,955 B，新建压缩包4,067,539 B；保留本场可继续分析的唯一91 MB检查点（写于正式议案发起前）、R79源存档及本场着色器缓存。历史原路径仍记在原报告中，现时可用性以 `R87-EXACT-RECLAIM.actual.json` 为准。闭场四根实际逻辑量463,169,417 B，加32 MiB保守余量后 carry 141,235,903,505 B，低于固定上限141,327,031,211 B，预约未用余额归零；物理空闲变化不独占归因本次清理。容量协调任务序号5705结束。

下一场须重新申请有限容量和新鲜桌面/离线证据。从 R79 原源或已核身份的 R87 后置存档择一作为新的不可变输入，先核其具体阶段、身份与原版信仰。按正式路径逐个取得道学与白沙礼仪的**实际接受代表**，随后封定、逐派投票、玩家同意、代表签署，才尝试实施；原政治头衔/继承保护及宗主头衔保存冷载仍是独立门槛。不得使用不存在的 `C:/workspace/ck3-upgrade-20261008` 目录。0.1.2 未上传；Steam 公开仍为0.1.1 Alpha内部测试。

外置证据根：`A57=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-r79-resume-admission-20261014-057`，`R87=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0087`，`CASE038=C:/workspace/ck3-common-runtime/cases/lyd-release012-headship-resume-20261014-038`。这些原件按存储策略分级复核，不能把整场当成永久保留对象。

| 关键回执 | SHA-256 |
| --- | --- |
| `R87/case-output/baseline-cell-result.json` | `8ebaf01e1a455edb3881c518abfa2e230f5bbed0d5add20f6ba694e31702f29a` |
| `R87/case-output/preparation-cell-result.json` | `4aa9e01ef4a3c7c7cfeb1d78842f5b460a5ea055f5b567862dbdb671b492f15a` |
| `R87/case-output/case-error-preserved.json` | `d4f7e7bcc4ef5b6f3c437969d16d23ba68bbccbab1d434b2c9c82df2ddc65c84` |
| `R87/case-output/normal-close-result.json` | `371f7520a87b9a32cb33b068cc9eb51c647a1137f89418ec634ab76aaaaa8ec8` |
| `A57/R87-SCREEN-RELEASE.actual.json` | `390ae8cb39ee92175b6b627a5cb85ce7d37342b1c54020c279000d0515e5e6da` |
| `A57/R87-EXACT-RECLAIM.actual.json` | `349c067d42067009d51a5c3d24e5dc728d3583a476a0fbd7cb30400de0ed9320` |
| `A57/CLOSED-RESERVATION.actual.json` | `8df2b128124e237442a1828d3e835557057ecfeee64fdfe106608c28e3e6f6e2` |
