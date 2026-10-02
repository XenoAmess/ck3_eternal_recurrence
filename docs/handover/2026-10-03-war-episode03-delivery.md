# 2026-10-03 战争第3期制作与主线交付

本次用户授权继续研究、制作战争系列，并把全部有价值的研究、视频和必要补丁整合回master。此前Steam升级、本期实机及草稿PR清理的范围分别见[游戏升级与主线整合](2026-10-02-war-master-integration-and-steam-upgrade.md)、[草稿PR逐项处理](2026-10-02-open-draft-pr-review.md)、[刘易斯实机专题](../ck3-native-ai/episode03-william-lewes-live-2026-10-03.md)。45个草稿PR已逐项处理：21项缺失成果整合、16项已有、8项被后续方案取代；原始来源与失败证据保留。

## 最终成片

标题《一座城究竟是怎样被攻下的？》，9章、129段中文旁白及中英字幕，1920×1080、30fps、H.264/AAC，1407.721354秒。最终a09 MP4为155322628字节，SHA-256 `166E6C53FA6C9359F2BBD826A4E9E6A8A49B4A6AFAEC6218B32A7335BDD89B0B`。文件位于 `D:/ck3-war-episode03-20261002-a01/episode03-nativebuild-a09/CK3-War-AI-Episode03-Siege-BrownGold.mp4`。

实际完整解码、编码音频峰值−3.2dB、20个音乐窗口、129段旁白时序及415帧/19份ASS/258个双语字幕事件均已通过其对应机器检查。129段原始PCM逐字节保留，实际AAC相对字幕逐段延迟为0，最小相关系数约0.999910；最后一句结束在1407.483333秒，音频尾部余量0.216667秒。独立复核保留方法RED和原a08生产RED，未借后续修正删除失败。

初次入库截点的415帧归档与最终审计仍在进行，当时OneDrive传输尚未开始。后续已完成全部机器审计与OneDrive客户端同步，精确回执见下方带时间的完成记录；完整人工1×观看/听音与签核尚未提供。

## 实机与研究边界

真实原版run `desktop-3fevhd2-1c74096080--vanilla--R0156`、William33388、ownSiege6、province1506，1067-01-10至04-22共102个正常游戏日。围城总量/进度/器械、正常合军、强攻一天与停止、城破占领与同战争分数读回均有原片、原图或typed收据；最终存档SHA `fb0336fe3d570031fa640dc7b0b6d311b09fd62c9dec7b8b18aa47861453d8b0`。普通强攻一天的16.38净工作含普通推进；净减168人不单独证明死亡原因。城破后整数13、native占领13与tooltip13.2分开记录，其他世界变化存在，不能将全部13点隔离归因于一城。

4月22日城破前一原始帧的日期也已变为4月22日；原raw审阅把其记为4月21日的错误以外置 `review-captures12-16-a01/15/fall-date-erratum-a01.json` 追加更正，旧报告不覆盖。各规则研究与未查明分支回链[本期证据索引](../ck3-native-ai/episode03-william-lewes-evidence-index.json)。历史1.19证据不外推为1.20；这项战争任务不增加Robert/G2信用。

## 源码整合与过程保全

公开CUnit军队ID0、CArmy0强度读回、路由producer/DTO、完整OEM严格CSV进程清单与Toolhelp互证，以及有实际故障证据的回收修复一并整合。普通renderer也使用帧对齐PCM master，防止多段AAC拼接再次累积偏移；415帧FFmpeg选择式改为平衡加法，编号、顺序、理由及PTS保持。详细测试及合回身份以随后实际回执追加。

全部原片、截图、TTS请求/返回、音频、板卡、字幕、concat输入、中间编码、partial、失败attempt、命令输出、manifest、审阅及成片永久保留于 `D:/ck3-war-episode03-20261002-a01/`。2026-10-03 02:20左右，源包已rebase至当时最新origin/master `2f0bb9dc85e1983cd7de3c7623431aa323aac9d3`，新HEAD `238bbc13d9b6fca9bdc2718e093d52eeafcf5432`；9份编辑输入已在外置保全后恢复精确原字节。新组合源码的native/Python验证、push和exact官方CI仍待其实际结果。

02:30追加：合回后normal/`-O`各87测试及384 subtests通过，1项未启用桌面集成skip；native117开关全OFF、4个production产物及11个fixture EXE构建成功、12/12 CTest通过，隔离MSVC army fixture成功。详细精确pins见[补丁验证专题](../ck3-native-ai/episode03-public-unit-zero-recovery-2026-10-03.md)。Git rebase实际会将两份冻结CRLF JSON规范化为LF，因此为这两条精确路径追加 `-text` 属性，保留编辑输入原SHA并避免下一次checkout改变来源；9个历史输入内容保持，两个文件在index中保存原字节。push/最终CI和视频交付仍待实际结果。

## 2026-10-03T03:27:52+08:00 最终媒体审计与客户端交付完成

最终a09全媒体报告实际 **machine_condition_status=PASS**，415个实际帧已全部通过公开API保全，原生完整integrity audit通过；完整解码、音频峰值、音乐窗口、129段旁白时序、258字幕事件及像素安全区均完成。报告 `D:\ck3-war-episode03-20261002-a01\episode03-media-audit-a09-completion-a02\media-report.json`（424966字节/SHA `68D991C7890F6DB6EA113341F98281222EBAC29DD32F21F86C9F3EE71A276F3B`）绑定唯一成片SHA `166E6C53FA6C9359F2BBD826A4E9E6A8A49B4A6AFAEC6218B32A7335BDD89B0B`。AI内容/画面抽检和独立PCM/AAC复核通过；人工完整1×观看及签核仍 **not-provided**，没有制造approval。

只传输了这一份MP4至 `C:\Users\1\OneDrive\CK3-War-AI-20260923\CK3-War-AI-Episode03-Siege-BrownGold.mp4`。实际本地copy stream SHA匹配，OneDrive客户端精确该文件的in_sync_state=1、validated=155322628、modified=0；结果 **CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED**，10次metadata采样。未独立下载或回读远端bytes，不把客户端状态扩大为远端SHA证明；未修改同步设置或传入源码/过程资产。实际回执 `D:\ck3-war-episode03-20261002-a01\onedrive-delivery-a09-a01\delivery-result.json`（1815字节/SHA `78BB5E453BC4325A687880D4722A4EE62872C4E23E1CA886EC38274003F4CFFA`）。这是可观看的交付审阅副本，外部平台发布没有执行。

源码与研究已普通fast-forward推送master **551a88e91f70767359db7e5545a9536de0d29fed**，exact官方[CI37048183916 SUCCESS](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37048183916)，root18:40:20UTC观察；实际normal/`-O`各87测试+384 subtests、1桌面skip，fresh native117 OFF/12CTest通过。9份编辑输入已与Git index逐字节一致。本次最终文档追加按随后实际push/CI记录在外置 `final-integration-receipt-a09.json`；不预填本文自身未来commit/CI。

本片时长23:27.721、9章/129段；前期战分衔接保守并集66.567秒。原始取材102个正常游戏日、全部failed attempts/partial/raw/TTS/音频/编码/审阅资料继续永久保留。War任务的可见里程碑已交付，未给Robert保存日、G2或非战争里程碑增加信用。

本次记录了工具链0.2.1的实际性能成本：415帧逐项preserve会反复完整校验已有manifest；随后v2 bundle构建两次加载415条source binding，每条重新hash同一155MB成片，约129GB重复读取。PID13716在18:57:19至18:58:07UTC实测增加约15.5GB读取/48秒CPU，吞吐约323MB/s。CLI audit已经产出 passed integrity report 后，又逐项重复登记原先已保全的415帧，造成额外数十分钟归档。只终止该CLI子进程，外层的真实 nonzero、failure.json 和全部52项已通过媒体条件永久保留；新的 completion-a02 使用正式 wheel 的公开 verify_audit_report 完整复核原报告，再公开 preserve plan/bundle/report 与 append_automated_audit_record 登记，复用已保全的415帧。第一份completion候选因使用assert判定而停止，保留partial及真实退出记录；a02等价改用显式异常。新完成报告没有改写旧RED、没有重解码或调用provider、没有降低阈值或制造人工签核，也没有热改正式wheel。项目审计入口按同一公共API路线作最小修复，以避免未来重复登记；批量首次保全优化仍归独立工具链。
### 审计入口修复验收

未来项目审计入口已改用正式工具链的公共 `write_audit_report`、`preserve_artifact` 和 `append_automated_audit_record`，避免对已保全帧再次逐项登记。唯一修改函数为 `native_frame_audit`；一次离线路由检查实际通过，原415帧报告和6个拒绝分支均符合合同，没有新增解码或provider调用。工作树工具SHA从 `5B1DAC07AEB508A99DC09B557CE99C2C80E4977103B3343766C89E7DD7A4FF1A` 变为 `2FFD3248B9BC8987F93C5D1E39121BB585E2EC7B3F25D6673C90FCEEFD74FA40`。验证回执 `D:/ck3-war-episode03-20261002-a01/final-production-a09-plan/future-media-audit-public-api-candidate-a02/bounded-validation-a01.json` SHA `D483198B9E21848E14DF32E1067CD8F381A66584CDC8C4FCB5D5D30206117360`；旧source与精确采用记录单独保全。此补丁只服务后续调用，既有A09检查和全部失败attempt仍按各自原始source与bytes解释。
