# 共享串行启动前恢复：原始回执与实际 Prepared 阶段

machine_id: `4-8e1c2f1861`。记录开始于 2026-10-29T04:37Z。此项维护属于现有共享 Python 接续工具，不新增业务实现、runner 或构建系统。

RRF R0047 在容量绑定时因 `native_slot_model` 缺少 canonical 字段而退出；公共 run、host 和 CK3 均未启动。原 Root wait1、allocator0、一个 guard1、keeper0 和 SCREEN release14553保留。恢复工具原先只接受 `ROOT-SERIAL.*` 回执并硬编码两个 guard，与该场实际 `INNER/SERIAL` 原始回执及单阶段 Prepared 不符。

`ck3_mod_acceptance_unrun.py` 现在只接受两种明确的原始 recorder 格式，逐一绑定原始 start、wait、stdout 和 stderr，不生成别名。INNER 格式要求规范 uint64 十进制 FILETIME、相同 PID/argv/出生时间、真实原 wait1 和一致的开始、结束、耗时；旧 ROOT 格式保留其没有 native birth 的事实。阶段数量及顺序来自实际 READY → Prepared → contract，全部实际 guard 必须恰好对应；缺失、额外、重复或错序均拒绝。生产者调用真实 reducer，下一 allocator 仍在原 writer 锁内重验。

这是跨 mod 的共享恢复合同改进；它不授予正常退出、业务完成或下一场启动资格。原 R0047 容量失败也不会被改为通过。Native a09、Java v5 与冻结 SDK 没有因此重编译。

局部验证已实际完成：66 项回归通过；修改涉及的18个 serial 定义采用提取范围 strict 检查，整个测试模块 strict 通过。不是整个历史 unrun 模块 strict 全绿。证据在外置 `cold-R0046-final-a01/metadata/runtime-preparation-a01/unrun-shared-fix-a01/LOCAL-VALIDATION.actual.json`，12003 B，SHA `6156b28c6462c0abc3e8c201c042194cedfb7b832eca660ec2f3a4b885bfd79c`。

完整对应 CI step 的92条命令正在执行，完成前不计为通过。前四次中止都保留了原始失败：第一次观察器碰到正常删除中的临时路径；第二、四次触发整个 public preparation 容量上限；第三次触发所选测试峰值上限。没有把中止前通过的断言外推为完整测试通过。

闭写的 synthetic Git 测试临时副本依统一存储策略的可重建提前到期规则精确回收，每批不超过1000文件，保存原生文件身份、内容摘要、删除清单、原始日志与 wait。三次实际回收合计7498224 B native allocation，已分别只加回 gross retirement 一次，不退款历史高水或重置旧失败。Root CAS326将同场保存预算420→384 MiB、metadata192→228 MiB、public preparation28→64 MiB；总额936 MiB保持，cache160、PNG28、wire64、real input72、keeper132、normal close32 MiB保持。零天推进、一次检查点的 canonical 三个70 MiB保存临时槽合计210 MiB，低于新的384 MiB保存栏。原07Z期限与全局容量、配额未改，Game仍 withheld。

完整 step 第20条还发现 HoF 组件测试缺环境而 skip1；该次 wait0仍记 FAIL。已从本机原 `production-b21-a01/qualifications/native-a04/hof-stock-default-wire-a01` 找到两份真实 C++ fixture 字节，1450 B／`9a1b96bfce89797e0224f69969ecc485d97a9bf9ff2fc3a57654a43c3c0c2066`、974 B／`6837f869ee3a1deebee57ae21032024b8fefaa00cd527f109d16822aa8f8e708`；补精确路径后六项实际通过，无需重编译或重生成。它们是 DTO reader/serializer fixture，不能外推为实机资格。

续行在第36条遇到 prepare v5 演进遗漏的真实 XQOL compatibility 失败：24项中的1 fail、9 errors，旧 reviewed source仍为31816 B／`e53b0fca36fc9714cd730187583c9efa14e4c78439ccb48374991c2f0bb265b3`，当前为37844 B／`092f87430af32d2125143e45d63e1c54709ec2f368aa3bb7f431949dd7f6dbda`。Root CAS327允许在现有预算内修复新增 v5严格逆投影、对应类型化测试及七份 case的唯一 prepare support Pin；不改 prepare、common、SDK、Java或Native。整份原 case恢复及此前v4→v3→v2→原前缀/唯一附加定义的校验必须保留，不能只更新摘要绕过守卫。新增兼容输入闭写后重新完整执行92条，早前失败继续保留。

Root另于04:38Z明确审查新 G2有限期08Z，因为原READY最迟04:40无法容纳剩余完整CI、commit、真实恢复、fresh scan与五步准备。该审查不修改原G1／Native期限，当前HEAD仍07Z；新G2只有取得全部真实验证与容量结果后才可发布，原8400／8220秒及keeper完整预测守卫保持。

兼容修复的完整followups26项、完整compatibility11项均实际通过，新增v5涉及的完整类型/函数/方法提取范围 strict通过；整个旧compatibility模块strict实际37 errors，独立保留，不写成全模块绿色。局部完整执行原退出码为 `[0,0,1,0]`。薄PASS证明只含三条真实通过的命令，完整执行记录保留那条失败；没有改写失败。

新一轮a07实际执行完92条、累计968项测试，最后一条9项中的1 error：旧pre-ready测试的`SimpleNamespace`未同步真实分配器必填的`prepared_path`。生产守卫不改，测试改为使用setUp已经创建的`self.prepared`；该模块九项实际原Popen9500／wait0通过。随后a08再次用最后闭写的12份源码和workflow完整执行全部92条，a07整体FAIL及其前91条实际通过均保留。

最终a08已完整通过92条原始命令、968项测试，零跳过；原Popen均0，12份本轮源码与workflow前后摘要不变，真实外部fixture输入也前后一致。完整证明 `cold-R0046-final-a01/metadata/runtime-preparation-a01/shared-CI-complete-a08/COMMAND-VALIDATION.actual.json` 为37696 B，SHA `1e6257f60ff9c13ad15dcaf9b756911582d17721ef81dce68b25f60d992c4f1e`。此前各轮FAIL仍是原始失败，不被该次结果改写；全模块strict37ERROR也继续保留。

本次执行发生在基于3079d09b的工作树，后续提交只封存这些同字节输入；没有将其声称为未来提交重新执行。Native CL、link及Maven重新编译数均为0。实际R0047恢复、来源绑定和新的CK3业务仍须另取真实结果，不能由软件验证推断CK3已启动。

提交7b926后的实际共享恢复a02原Popen13324退出1：冻结输入表含七份未选中的XQOL case，它们此前唯一的prepare support摘要修复仍触发了原始输入不变守卫。完整原失败保留；没有修改冻结表、原件或SDK通用守卫。

CAS328限定继续修复现有unrun及其stages测试。新增v2资源恢复分支逐一保留原Git blob、当前文件与内层ContentPin；完整JSON仅允许该一个prepare support摘要变化，当前prepare仍须与冻结原件raw一致。实际READY→Prepared→contract/adapter/runtime/product/case/run身份必须完整吻合，拒绝选中XQOL或活动launch/native/control/Save。消费者在原始终态、无Game、SCREEN释放、进程检查之后验证，下一allocator继续在原writer锁内重验。原v1两reader分支保留；没有给其他输入漂移增加例外。

局部完整stages原Popen18280／wait0，73项、零跳过；其中新增七项执行真实producer→reducer→writer锁，并检查序列化往返、当前及旧字节变化、错误字段/类型和越界语义。新增16个class/def及一个union的完整提取范围strict通过，原serial提取范围strict通过；整个stages测试模块原Popen17904／wait0、strict通过。整个旧unrun模块没有据此宣称strict全绿。新源码冻结后正在完整重跑92条CI命令，不能沿用a08代替新源码验证。

Root于05:31:45Z重新明确审查G2有限期08:30Z，替代未采用的08Z候选；当时HEAD仍07Z，没有自动延长原G1、Native或旧失败。新G2仍须实际完整CI、clean commit、共享恢复0、完整fresh scan和容量CAS，原8400／8220秒及keeper完整预测守卫保持。

a09现已完整通过全部92条原始命令、975项测试，零跳过，Root持有的原工具session2364实际退出0。证明 `shared-CI-complete-a09/COMMAND-VALIDATION.actual.json` 为37695 B，SHA `44e69f76ad856cc9781b7bf756fbeebeb5e8e96d58a821ac6241047fc00a3c09`；12份源码与workflow前后相同。执行基于7b926工作树，后续提交封存同字节输入。局部闭写证明 `recovery-registry-support-fix-a01/LOCAL-VALIDATION.actual.json` 为6664 B，SHA `a030ffa09df48795973e5e5c9fd764cb52ffb88366ca68c8a7d4a07d2da6f104`。该次PASS不覆盖前述37项历史全模块strict错误，也不代表游戏或业务已经通过。

R47实际恢复a03原Popen5164／wait1：Root额外传入同一stdout作为可选`--admin-release`，与单次completed事件的既有canonical-reconstruction要求不符；原失败保留。a04只移除此可选参数，沿现有生产者从实际journal重建同一事件并保留原始stdout，原Popen18028／wait0、真实reducer通过，无新管理事件或源码修改。`recovery-R47-a04/ALLOCATED-UNRUN.actual.json` 为22019 B／`cb1f1a0c2b3d5c85a4d84513dd85e43dd23c3757f729e7926db68a44741b60bc`，完整reducer stdout为15788 B／`fedf6849f50019a4bb6efb486a4bca69f33d27158bf9cdfbad19d962e61d76c2`。模式为`previous-shared-allocated-unrun-prelaunch-orchestrator-failed`，`SDK_or_launch=false`；原R47仍无游戏、正常关闭或业务PASS。
