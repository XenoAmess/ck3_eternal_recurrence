# 礼与道 R0006：代表流程通过，资格与日志 RED，生命周期已闭合

R0006 已正常退出并完成资源释放，**整体 NOT_GREEN**。基础入学、选派取消、朱子择师与祭修 A 的限定保存回读通过；I2 资格后置仍 RED，错误日志已达 100000 条上限。退出成功不改变功能与日志结论。

来源固定为 `3d3305e75cf642a7a82bef5f9aee03dc76b3c10e`，产品树 `2e290b9b7fca02c38a33e4c73f5c46e7060dc9fa`，CK3 1.20.0.3 / Steam build25652598。实际执行 `a29d24c0-d479-4989-bf90-16d4e1de0ea0`、PID12500，挂载59件产品、7件入口夹具、7件I2夹具。后续master整合不改变此轮实际装载来源，也不授予新源码实机信用。

| 场景 | 实际结果与边界 |
| --- | --- |
| 正式入学、取消选派、朱子择师、取消祭修、朱子祭修A | 限定保存场景PASS；朱子A费用、资源、经验和冷却已读回，不外推36派全选项 |
| I2资格夹具 | RED_QUALIFICATION_POSTCONDITION；同effect缓存8/7/8，保存baseLearning14，没有当前exacttotal15观测 |
| 35+1礼仪图夹具 | PASS_SAVED_SETUP_GRAPH_ONLY；不是正式合分、表决或签署 |
| 时间推进 | 请求D+1实际D+2，1066.9.15→1066.9.17；没有精确一天或D+30验收 |
| 0036→0040资源夹具 | PASS_RESOURCE_FIXTURE_ONLY，29项检查；金币229→2229、虔诚185→9185，七项夹具记录，其他世界角色原记录、全部Faith/Rite及整段头衔不变 |
| 0042→0044正式提案与事件对应 | 提案存在，源派2/4赞成、quorum−2；玩家未投源派票、未给个人同意；0043只选择lyd.200 wait |
| 正式签署、提交及native迁移 | 未执行／未证明；不以原文件名source-yes或SDK ACK写成同意成功 |

源派实际选民是31254、65856、65860、65861。后两人是成年外庭祭司，生日1034.8.11及1017.8.25，在0036已出现，早于资源准备和提案；不是新生儿，也不是夹具创建的两名age40代表65856/65857。外庭君主34973/34232的ownrite由0变169，宗教关系任务1359/506将owner59621/59758换为65860/65861。当前build脚本的auto_fill/fill_from_pool/pool_court_chaplain与此相符，但缺少原native创建和任命调用，只作来源支持的推断，不声称唯一原因。

资源读取001/002因真实重复记录、非唯一或缺失rite字段失败，失败过程永久保留。003按完整角色occurrence的原顺序比较，保存重复项和字段缺失，不去重、不造身份；这些读取器失败不写成游戏effect失败。完整238MB世界账留在外置原包；本投影保留完整报告无损gzip、源摘录、最终索引以及未导入项的bytes/SHA与理由。

实际保存instance10=lyd.210源派授权、11=lyd.212个人同意、12=lyd.200提案。0043选择12的option1=wait，12消失，10和11保持。native active11不能等同于PNG前景；先前独立回读代理按原PNG中文内容对应到源派授权10，GUI数字instance本身没有显示。玩家没有新票或个人同意；65860票据identity省略保持原貌，不补赞成1或数值0。

最终退出前后各复制16份日志，error均为40866397字节、SHA `fd8b659ef333ffe7e1a1dad1a20e7a8f892071bbcc41d36ec4866f229cd9827b`，与旧分类原件完全相同，共100000[E]，主要位置全部I2夹具。早期正式入学阶段0error的快照保持原事实。cap之后覆盖仍 **UNKNOWN**；缺新行不能证明正式提案、退出或后续阶段零错误。最终日志receipt中旧PENDING字段是复制工具当时标签，本报告另据实际退出回执闭合，不改写原receipt。

| 生命周期 | 真实终态 |
| --- | --- |
| CK3 PID12500 | 正常GUI退出，独立watcher观测exit0、CK3/reporter全部消失；watcher未发终止请求 |
| 旧SDK/client/stdio | 会话lost，独立psutil确认进程消失；**未观察到orderlyclose回执**，不能写旧SDK正常关闭 |
| 旧keeper | interruption后进程消失，旧FINAL未见；不补造正常STOP/FINAL |
| 新恢复keeper | 新任务独占后STOP→FINAL，failure及entry_error为null，thread_exited=true；FINAL本身screen_released=false |
| 屏幕lease | 旧expiredowner释放2808→2809；旧task重新注册被拒的001保留；新task注册2810→2811；最终freshCAS2813→2814、resources=[] |
| 源冻结 | 据CK3/reporter/SDK/keeper实际全部消失及freshCAS释放解除；不是因SDK正常close才允许保存报告 |

退出autosave为真实GUI退出产生，90506624字节、SHA `23b0c18b59cd59bbbe55f94e4bc47333de339a1076bd64a43cea102562f41bd7`，永久外置保留。本报告只核对其bytes/SHA和真实来源，没有重新解析该存档或外推投票状态，不把90MB存档导入Git。

C3领袖完整生命周期、36派全部祭修、正式C2全部授权与签署/迁移、重复join/detach、D+30和reload仍未执行或未证明。任何R7冷载均须新attempt、新来源与新证据，本报告不预填R7成功；旧68old人工证据不外推本轮。

旧795件草稿、7件D+2、19件进度补充、110件续稿均保持原字节，其PENDING是历史快照。此最终包追加真实终态；旧严格导入候选已被本包新候选取代，旧文件保留。新导入脚本接受有真实终态证据的RED/lost报告，仍要求运行进程消失、lease和源冻结实际释放，拒绝覆盖旧报告与复制raw.ck3，不调用Git、游戏、native或CI。本准备代理只写外置新文件，永久tracked导入由根代理另执行。
