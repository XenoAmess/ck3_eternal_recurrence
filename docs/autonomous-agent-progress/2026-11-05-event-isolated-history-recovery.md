# EVENT 原件进入独立只读历史恢复路径

Runtime29正常loader已启动，但在legacy incident回调前以 `historical cycle requires the actual interrupted batch` 停出。实际原件证明：最后capture147之后，B4 START148中的正常RETAIN170发生于phase2；旧fallback专门处理FOCUS中断后的phase3，不能接纳这段普通多cycle历史。B10的517START→518至521事件→522INTERRUPTED合法，原521为正ACK后UNKNOWN。问题是EVENT未被isolated选择器接住，不是坏账或v1 callback失败。

本次只改ContinuityBatchJournal。新增纯DATA EVENT判定限定Gameplay原点／期望、BodyDerived协议、既有select-event-option有界operation和native-event-instance schema，核完整bodySHA、原expected before/source、原Attempt、正ACK、原结果token／outbound／custody、requestId／prepared step及完整guard，执行原custody.verify。全部canonical actions中仅一个未结算且满足该判定才选择它。

入口picker、完整readSameGameHistory unresolved门和最后isolated角色三处同步。返回只能是未结算DATA，不能发行saved-settled／settled-sameGame权限。已有CurrentMap保存态的EVENT retention核完整cycleSemantic／savedPair、原canonical成员、source／machine／Game／session／body，仍先通过整个历史replay、周期原件、Driver、owner及head fence。原FOCUS fallback、1858 guard和历史主体原字节保留；不改B4／B10、不重发旧动作或刷新deadline。

actual新单TU20类首编0，9.9391552秒；所有类名与原20族相同，仅BatchJournal方法集合及synthetic变，其余19族、字段和结构属性不变，使用正常loader。新Hosted Test单TU2类首编0，4.3897485秒；精确两方法2P，4.3576775秒，XML7d915132。正例解原521、完整ACK、prepared及实际Chronology／conn19，再调用真实公开DATA选择器；八类native flag、token、custody、outbound、hash、step、guard及schema错误被拒。全phase强终态／fence／close释放，没有重编或重跑旧绿。

测试仅证明真实已记录DTO的分类和拒绝，不冒private Session／Root发行、完整历史reader或事件效果。原ledger／dispatch路径只D Hosted使用，源及原payload不进入通用Maven或公开Git。完整历史恢复、Root v1和原521结算仍由唯一Runtime在实际受控readonly scope首验。

模型完整stop26.5336036秒、TTFT10.3280988秒。两个DATA选择／保存shape helper原文采用；classifier漏expected绑定、裸类型缺import、catch语法及补丁hunk／位置问题由owner修正，未应用整份patch。独立测试模型length6000整份未读未hash、0采用、无R2；owner接管两个必要用例，最初compound var源审拆分为02，未记为编译失败。

formal只投影七个owned span，其余原字节完全逆还原；actual与formal变体不同，actual2P不授wholeformal组合绿。源码／编测／正常loader／完整历史／Root／SETTLE／SAVE逐层验收。本文切点原521仍UNKNOWN、head522、C22，169eligible／8saved，任务继续RUNNING；不为发表新增GET。

后到Runtime30实际越1858且完整历史验证finish1／failed0，随后因Driver私有资格角色漏EVENT停出，未进v1。已另形成[Driver角色补接](2026-11-05-event-driver-history-role.md)的单TU18类首0／全结构同；不将本页原DTO2P改称Driver或Root行为通过。
