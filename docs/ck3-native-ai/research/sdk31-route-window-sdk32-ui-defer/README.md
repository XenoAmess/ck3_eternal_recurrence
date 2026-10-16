# 已有路线窗口分类与可选战争 UI 读取

本目录保留两份完整窄patch及来源pin；正式小提取为
`tools/g2_saved_campaign/route_window_advance_outcome.py`，SDK正式修改为Service和两类普通UI优先级模块。
不会复制整份场次分类器或启动运行进程。

路线分类器由宿主显式注入已审核的帧绑定、规范step解析及sentinel后验验证函数，无SDK import。
保留原生日期／tick／暂停／generation／完整敌军scope全部守卫；只排除明确 `retreating is True`，
None／缺字段仍算敌军。原生监测集合为全部我方军加本次合格敌军；自然战争结束或新战争只作为日数观察，
不授胜利／业务信用。已有相同速度可以是严格绑定源帧的 `already_observed`，不能伪造一次提交。

实际 query12／AUTO14 字段投影保留原件SHA，13KB；原完整回执、投影和新portable函数经原帧绑定及公共SDK
真实pure parser／sentinel validator比较，输出完全一致：72raw／3日，业务false。
见 `PUBLIC-FULL-PROJECTION-EQUIVALENCE.json`。这不是再次执行原clock。

UI三叶修复释放两类同帧失败读取缓存，unknown仍unknown，有可见窗口或close-pending仍严守。
overview首次精确 `state_changed` 可重新规划一次，原请求不重试并保留failed attempt/request ID。
**本批尚未修复war-results首次query失败的非致命消费**，只有其已有失败缓存后的普通规划释放；
不得据此声称所有UI错误都不中断、窗口已隐藏或关闭成功。后续候选独立验收。

新16项与已有overview/results优先级回归共25项GREEN，包括真实Service规划→NativeHeadless query→fake endpoint，
公共revision2／Native40分别绑定。world snapshot facade仅提供合成世界输入；没有预计算欲验证的query DTO，
没有游戏、窗口、MCP或原动作调用。公共宿主的全部运行接线不在本次提取的验收内。

正式CI沿用现有相关focused入口；不扩大全repo强制矩阵。Runtime原件仍外置，未把视频、SAVE或Driver全态入Git。
