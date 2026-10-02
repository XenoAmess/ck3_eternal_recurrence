# 2026-10-03 战争第3期制作与主线交付

本次用户授权继续研究、制作战争系列，并把全部有价值的研究、视频和必要补丁整合回master。此前Steam升级、本期实机及草稿PR清理的范围分别见[游戏升级与主线整合](2026-10-02-war-master-integration-and-steam-upgrade.md)、[草稿PR逐项处理](2026-10-02-open-draft-pr-review.md)、[刘易斯实机专题](../ck3-native-ai/episode03-william-lewes-live-2026-10-03.md)。45个草稿PR已逐项处理：21项缺失成果整合、16项已有、8项被后续方案取代；原始来源与失败证据保留。

## 最终成片

标题《一座城究竟是怎样被攻下的？》，9章、129段中文旁白及中英字幕，1920×1080、30fps、H.264/AAC，1407.721354秒。最终a09 MP4为155322628字节，SHA-256 `166E6C53FA6C9359F2BBD826A4E9E6A8A49B4A6AFAEC6218B32A7335BDD89B0B`。文件位于 `D:/ck3-war-episode03-20261002-a01/episode03-nativebuild-a09/CK3-War-AI-Episode03-Siege-BrownGold.mp4`。

实际完整解码、编码音频峰值−3.2dB、20个音乐窗口、129段旁白时序及415帧/19份ASS/258个双语字幕事件均已通过其对应机器检查。129段原始PCM逐字节保留，实际AAC相对字幕逐段延迟为0，最小相关系数约0.999910；最后一句结束在1407.483333秒，音频尾部余量0.216667秒。独立复核保留方法RED和原a08生产RED，未借后续修正删除失败。

公开工具链原生manifest的415帧保全和最终完整integrity audit仍在进行；此截点不声明最终media-report完成。OneDrive传输尚未开始。完整人工1×观看/听音与签核尚未提供。

## 实机与研究边界

真实原版run `desktop-3fevhd2-1c74096080--vanilla--R0156`、William33388、ownSiege6、province1506，1067-01-10至04-22共102个正常游戏日。围城总量/进度/器械、正常合军、强攻一天与停止、城破占领与同战争分数读回均有原片、原图或typed收据；最终存档SHA `fb0336fe3d570031fa640dc7b0b6d311b09fd62c9dec7b8b18aa47861453d8b0`。普通强攻一天的16.38净工作含普通推进；净减168人不单独证明死亡原因。城破后整数13、native占领13与tooltip13.2分开记录，其他世界变化存在，不能将全部13点隔离归因于一城。

4月22日城破前一原始帧的日期也已变为4月22日；原raw审阅把其记为4月21日的错误以外置 `review-captures12-16-a01/15/fall-date-erratum-a01.json` 追加更正，旧报告不覆盖。各规则研究与未查明分支回链[本期证据索引](../ck3-native-ai/episode03-william-lewes-evidence-index.json)。历史1.19证据不外推为1.20；这项战争任务不增加Robert/G2信用。

## 源码整合与过程保全

公开CUnit军队ID0、CArmy0强度读回、路由producer/DTO、完整OEM严格CSV进程清单与Toolhelp互证，以及有实际故障证据的回收修复一并整合。普通renderer也使用帧对齐PCM master，防止多段AAC拼接再次累积偏移；415帧FFmpeg选择式改为平衡加法，编号、顺序、理由及PTS保持。详细测试及合回身份以随后实际回执追加。

全部原片、截图、TTS请求/返回、音频、板卡、字幕、concat输入、中间编码、partial、失败attempt、命令输出、manifest、审阅及成片永久保留于 `D:/ck3-war-episode03-20261002-a01/`。2026-10-03 02:20左右，源包已rebase至当时最新origin/master `2f0bb9dc85e1983cd7de3c7623431aa323aac9d3`，新HEAD `238bbc13d9b6fca9bdc2718e093d52eeafcf5432`；9份编辑输入已在外置保全后恢复精确原字节。新组合源码的native/Python验证、push和exact官方CI仍待其实际结果。

02:30追加：合回后normal/`-O`各87测试及384 subtests通过，1项未启用桌面集成skip；native117开关全OFF、4个production产物及11个fixture EXE构建成功、12/12 CTest通过，隔离MSVC army fixture成功。详细精确pins见[补丁验证专题](../ck3-native-ai/episode03-public-unit-zero-recovery-2026-10-03.md)。Git rebase实际会将两份冻结CRLF JSON规范化为LF，因此为这两条精确路径追加 `-text` 属性，保留编辑输入原SHA并避免下一次checkout改变来源；9个历史输入内容保持，两个文件在index中保存原字节。push/最终CI和视频交付仍待实际结果。
