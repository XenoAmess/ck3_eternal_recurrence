# 同一 canonical head 的只读恢复与已提交 Life 决定重放

新 Life 的 resume 已有真实成功 ACK，但 fresh READ 不可用，原 ID 只读重试后父 UNKNOWN 的序号恰好等于当前 canonical head。完整历史校验已通过，旧 DATA 分支却只允许父序号严格小于 head；另一个普通事件的只读历史也已通过，公共 DATA 构造器遗漏了同一事件分支。

本单元补齐这两处 DATA 接线。current-head Life 仍须匹配唯一真实 ARM／末尾 ACKed UNKNOWN resume 前缀、已保存 CurrentMap 历史、当前周期和最新观察的日期／角色／episode、原 source 与 body。历史小于 head 和全子动作已结算的 operator 分支保持原样。事件只复用原有严格判据，不伪造 restart capture 或把当前 date143 改述为 C19 SEM 的 date137。

连续的单 Life operator 决定可显式保留更早同 owner／Game／episode／原 source 的 Life 决定及完整祖先引用。旧授权按真实 archive materialReference 重开；原 source 再验证已提交事件、前驱快照、原 UNKNOWN 与 reservation。旧 Sway 分支及普通验证保留；更早决定的过期期限不会变成新签发权限。

实际 Source15 在37通过 DATA 并将原 resume487只读确认；38的新489独立退役、490零信用恢复与491 batch10／LOOP通过，旧 Sway24和 Life27事实保留。Source21在40通过事件 DATA，原495只读成为497 APPLIED，498发布 Driver 材料。后续 RETAIN 的另一个路由缺口由独立 Source24 修复，499 RETAIN／500 SETTLE为 C20 VISIBLE_GAMEPLAY，0新增推进信用。41曾因 following-turn 原证据 verifier 安装范围而结束；42的既有全结算标准恢复实际进入 batch11，未重做497或C20。

正式变体保留原 Saved 差异，仅必要单 Journal TU 验型；另一 source 与实际已编字节相同，复用其完整家族资格。必要正式 Journal 单 TU 于00:14:10.609063Z开始、00:14:25.632529Z以 exit0／accepted／完整21类结束，CLOSE释放；原 Source17 字节相同的完整1类直接复用。主回执为 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/formal-journal22-compile01/actual/prod/ACTUAL.json`（1590B／`f592b40d57c5e9fac8aa041ccf31a0e4467fdfaf7f5b7a1ad49b065334f401a7`），OUTPUTS为162222B／`35840533987401595b90e496e044033375229b8ec8991c7a87f534fb1bbafe5a`。没有重复编译旧绿色家族或运行 Runtime 正式变体。本单元不包含未来 after-publication 修复、独立维护SDK或性能候选，也不将它们的编测状态混入。

上述切点 saved 仍为8日、pending=null。没有新增确认保存日，不报告有限秒／新增保存日；普通年度保存政策不变。私有原件位于 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/life-postcondition-p0-20261112-01` 的 source15／17／21、formal22与对应 Runtime37／38／40／41／42目录，机器为 `xenoamess-full-tower-eb9d2c1186`。正式发表不代表 Runtime 装载正式 Saved 变体。
