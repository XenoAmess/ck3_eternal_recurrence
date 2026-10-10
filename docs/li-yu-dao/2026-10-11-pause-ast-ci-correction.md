# 暂停诊断的旧 AST 测试装配修正

`9e2fad7de47a0c26cb242e988dcba54bd19c8316` 的 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38090919254) 于2026-10-10T22:24:51Z实际失败；Linear成功。暂停测试5个方法产生16个子测试错误，首个异常为 `_campaign_pause_frame_rejection_detail` 未定义。生产host已有该函数，但旧测试只提取部分host函数，漏提取其新增依赖。

修正四个直接消费者：pause、day-result、campaign-event与preaction的AST选择集合各增加这个既有helper名称，其他断言和生产源码不变。有限搜索确认这四处是旧提取器的全部直接消费者。只运行3个原失败方法及另外3个直接受影响的拒绝检查；22:27:49.695738Z—22:27:51.220197Z实际exit0、6 PASS，没有重跑已通过的正常路径。

首次本机定向命令因记录器固定cwd与工具模块搜索路径不一致，产生4个loader错误，未进入测试场景。改用显式工具目录的6方法选择器后才形成上列实际PASS；原命令、失败stderr和后继结果分别保留。[完整小证据索引](acceptance/2026-10-11-pause-ast-ci-correction/INDEX.json)含官方原始失败步骤的无损ZIP。

Source14/O14尚未物化。旧009准入不能暗改为新来源；先关闭未消费预约，再由新published exact、包含这四项修复的16路径计划与新准入生成后继。原2f与9e失败、旧计划及容量回执原样保留。此修正没有新的游戏日、SAVE、自然到期或冷重载信用，一期仍75% / NOT_GREEN。
