# H3937 a11 旧 one-shot 入口退役（2026-09-30）

`ck3_autonomous_player/src/xar_autoplayer/h3937_combined_once_enable.py` 只保留 a11 历史实现供审阅。其屏幕租约逻辑按旧任务总线快照过滤，并使用未绑定序列的 heartbeat；它不能用于当前受管实机。

模块的公开操作入口 `issue_screen_challenge`、`run_exact_once`、`main` 和 `supervise_exact_once` 均在读取任务总线、检查 Steam/CK3、创建输出目录、写回执或启动子进程前直接抛出 `RED` 退役错误。旧的屏幕租约读取、裸 heartbeat 和 GO 校验辅助入口也直接拒绝。命令行执行同样以非零退出。旧 a11 attempt 的源码和证据保持原样；旧测试仅在测试进程内临时绕过退役门，用于验证归档逻辑，不构成操作授权。

任何新的 H3937 六项暂停帧只读查询都必须使用独立、经复审的当前 one-shot，完成新 HEAD、二进制、任务总线 CAS、屏幕租约、当次 Steam 离线画面和 GO 的全部准入。此变更仅是代码及夹具验证；没有触碰权威任务总线、屏幕、Steam 或 CK3，也没有获得 live 准入。
