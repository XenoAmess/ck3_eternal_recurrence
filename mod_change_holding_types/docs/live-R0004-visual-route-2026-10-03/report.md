# R0004 英文视觉与语言切换路线报告

本次 `bf-202609141645-5434332d4d--change-holding-types--R0004` 使用固定 CK3 `1.20.0.3`／build `25652598`，以 `-debug_mode` 重载存档。生产运行文件的 inventory／size／SHA 与 R0003 相同，本次没有改 runtime，也没有新增生产玩法矩阵结果。

只读原图确认 `en-holding-list-01.png` 的六个英文决议名称、`en-city-full-01.png` 的城市名称、说明、Trani／特拉尼目标与 400 费用。建筑损失及政府／继承警告已经渲染，但右半行仍被悬浮提示遮挡。末帧名为 `en-warning-unobscured-01.png`，实际仍然被遮挡；父任务报告移开指针的操作被拒绝。文件名不能作为无遮挡验收依据，全文警告视觉门仍 pending。

官方 debug Language 窗口的 French 按钮与控制台 `switchlanguage french` 都进行了尝试，后续截图的原版 HUD／决议文字仍为英文。因此分类是语言切换测试路线 FAIL；没有进入可核验的法语渲染，不足以判定本产品法语文件 PASS 或 FAIL，也没有七种新增语言的视觉完成事实。下一步由新的独立 run 在启动前设置每种语言，并核对实际 HUD 和产品文本。

debug 详情还出现 `is_ai` 的 trigger 本地化诊断：原版 `common/trigger_localization/00_debug_triggers.txt:5` 缺少 `first_not`，采用 `NOT_is_ai_trigger` fallback，调用上下文指向本产品 `00_convert_holdings_decisions.txt:116` 的城市决议 `is_valid`。完整引用链保留；没有据此修改产品或把它断言为玩法故障。error.log 也含原版 court scene 和 debug GUI 诊断，本轮不标为日志无错误。

`session-final.json` 保存 `cleanup_proven=true`、`tree_gone=true`、最终 job 活动进程数0、`ok=true`；`bus-release.json` 保存资源空列表与任务 done，证明进程清理和屏幕释放。CK3 exit code 为1，本文记录的是受管终止完成，不声称游戏自然退出码0。

R0003 的旧 `screen-register.json` 在父任务的一次注册重试中被误覆盖为 CAS_CONFLICT。原1256字节回执曾直接读取并记录SHA；当前678字节错误回执另行保留，未恢复原 bytes。更正与边界见 [追加勘误](../corrections-2026-10-03.md)。R0002／R0003 的冻结玩法报告没有改写。

逐文件证据及 SHA 见 [JSON 报告](report.json)。本轮英语部分视觉已确认，完整警告、七语视觉与正式发布仍待证据；语言路线失败不替代产品语言结论。结果不外推全部 `1.20.*`。
