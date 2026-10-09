# 2026-10-10：当前机器自行重建公共运行时

用户确认 `C:/workspace/ck3-upgrade-20261008` 不存在，并要求不依赖它。本次从本机已跟踪源码构建、固定一份供全部产品共用的 manifest，没有等待该目录，也没有回退产品专属 host/native。历史缺件和失败报告保留。

本机 CK3 为 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。正式入口仍为 `tools/ck3_mod_acceptance.py` 的六种模式。

28项实际输入、输出、索引和生产器已逐字节归档：[INDEX](acceptance/2026-10-10-local-common-runtime-rebuild/INDEX.actual.json)、[归档复验](acceptance/2026-10-10-local-common-runtime-rebuild/ARCHIVE-VALIDATION.actual.json)。完整源码 ZIP 和二进制保留外置，仓库保存它们的字节/SHA。

## 实际构建与共享源码

第一次冻结 Source01 `5e2f65740a28dd5df34ffa59862a47030048a1b3` 的构建失败于 MSVC C2712；[共享修复](2026-10-10-religious-title-seh-compile.md)将纯 SEH 调用与含 RAII 的逻辑分开。Source01、失败日志和输入保留。

Source02 `af20455212ed75000ba6136b3be308a9288cb06e` 在 `C:/csr2`，实际 build 在 `C:/cbr2`，公共 DLL/injector 编译链接返回0。特性开关从本机已知真实基线取得并加入公共 frontend rules；完整定义、编译工具和索引位于外置证据，不据此宣称所有产品能力已通过。

| 产物 | 字节 | SHA-256 |
| --- | ---: | --- |
| `xar_ck3_bridge.dll` | 9459712 | `390506e486f5b19e298070523360d420de255a7811b5e79a5b279d5f9331dbbe` |
| `xar_ck3_bridge_injector.exe` | 39936 | `2e22a985ba3166ce50ca1732901f0bac0629e8ff0f068de73330fdd5d09c86a8` |

Source03 `13d063c81ff706d8bc3f9a8bf81f60c283338042` 在 `C:/csr3`，增加[固定保存中已有事件的只读启动检查](2026-10-10-saved-startup-event-admission.md)。与 Source02 全文件比较共有6项变化；native_bridge 下只有 host `.py` 改变，所有其他 native 目录文件逐字节相同。因此沿用已编译 Source02 产物，保留两份完整 source/native 索引和实际比较，不宣称重新编译 Source03。共同运行时固定这些显式输入，不随其他 master 工作包自动改版。

`C:/workspace/ck3-common-runtime/20261010-002/manifest.json` 的 SHA 为 `275bd7bdb8b44e72340e4fb77cc238f43a50dabd532d64f93916d3d0380be51c`；本机映射 `runtime.local.json` 的 SHA 为 `36e880a0784458fd54c3740c0cf69fcccb66cc3e1ca87a82571dba852482660f`。公共 host、source、DLL/injector、Python imports、launcher、队列、keeper 和已安装 task-bus 均绑定精确字节。能力表只授 source/build-ready，`actual_live_qualified=false`。

## 首次本机准入与事务对照输入

[首次本机 bootstrap](../ck3-mod-acceptance-first-machine-bootstrap.md)实际 bundle 已固定。真实只读检查通过：绑定当前 OS MachineGuid 派生 machine ID、canonical ID 历史、八份 R38 原始闭场证据、归档 INDEX、当前实际 bus list 和 durable 4188→4189 释放链。没有借此将 R38 追认为公共运行时或完整事务对照。该检查未分配 ID、创建 ledger 或领取屏幕。

《礼与道》新增 `transaction-only-control` 产品 case，只有 fixture/data/adapter；host/native 选择仍在全局 manifest。正式71文件与原固定 `06159b964d859d30f2f07f4b183284df7d6dac47` 的正式 staging 逐字节相同，诊断覆盖6文件单独挂载。外置 seed 是原 R34 D2a，91711686字节、SHA `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`。actor/root31254、date_raw53144712、原事件121均固定；真实 typed saved scope 名是 `new_title`，title18373。

四份配置中 `pdx_settings.txt`、`tutorial.txt` 使用 R38 原字节；旧现场和当前 Windows Documents CK3 目录均没有两份 presets。新 fixture 明确创建两份零字节“无自定义预设”输入并保存来源说明，不伪称历史复制，不改变存档及其中的游戏规则。seed 留在外置输入路径，准备 profile 的 saves/logs/run 保持空。

新 case 仍使用既有公共预算 command300/readiness400/timeout2100/hold900/poll0.5；没有延长旧 held 会话。只选择原 D2b 选项一次，以真实终点事件、完整有序45人缓存、resolve 后持久化数值标记、未授封18373和七个政治头衔完整 AST 为证。此对照不授正式 I3b/C3/I4 或整体验收通过。

## 已知边界

构建原始回执的 Defender hook 为 `disabled`：冻结源码没有主仓 Git-local opt-in。随后从已成功构建的真实 CMake codemodel 仅登记新增 injector 精确路径；实际管理员 WMI Add 返回常规故障，读回仍缺该路径，终态 `settings_failed`。未重新 build，DLL/injector 字节保持固定。原 disabled、dry-run仅需CMake glob regeneration的保守停止和实际失败回执分别保留；不能外推旧238路径或称新路径已永久排除。

`af2045521` 的 Official CI 失败于新增无害子进程测试缺少可选 `psutil`；[原失败及修复证据](acceptance/2026-10-10-shared-local-launch-static-dependency/REPORT.md)保留。修复只隔离可选创建时间查询，真实 Popen/wait/退出码7检查仍执行。Linear 通过，LiYu 未触发；不把未触发写为通过。

公共 `prepare` 实际 exit0，完整 profile 为84文件（79项 mod/outer 加四配置、dlc_load），seed未写进 profile。公共 `preflight` 实际 exit0，状态 `READY_FOR_EXISTING_REVIEWED_LAUNCH`；包括安装游戏 SHA、共同 host CLI、固定保存、startup handler/data、adapter 和 native pins。[12项准备和预检原件](acceptance/2026-10-10-local-common-runtime-rebuild/PREPARE-PREFLIGHT.actual.json)另行归档，前28项历史归档不覆盖。原未准备 `plan` 的6项 unbound 阻点及 exit2 也保留，不改写旧结果。

截至此版记录，公共运行时为 **BUILD_READY / LIVE_NOT_RUN**。新实机仍需当次实际无占用检查、唯一 ID/屏幕租约及新鲜 Steam 离线原图亲审；不能由 manifest、bootstrap 或 preflight 推导 live GREEN。事务对照和正式 I3b/C3/I4/整体验收未通过。

## 04:07 CST 后续：R39 已实际启动，启动检查 RED，现场已释放

上节 `LIVE_NOT_RUN` 保留为启动前记录。本次公共入口已实际分配并启动 `bf-202609141645-5434332d4d--li-yu-dao--R0039`；owner checkout 固定为 `00b88fc4df0b8b4cea8b15ff85de8f244825a329`，仍消费上述同一全局 manifest 和 Source03。首次本机 bootstrap 已消耗，后继不得重复 bootstrap 或清理 machine admission ledger。

公共 `run` 实际 exit2；host 的固定存档检查在原400秒 readiness 预算内超时，最终原生报告 RED。146份观察均未取得就绪地图、玩家角色和当前事件；日期53144712及暂停状态存在，query mailbox 在工作，但 `map_ready=false`、`played_character=null`、`local_player_id=0`、`active_event=null`。原守卫逐件只读重放与保存的 `frame=null` 一致，尚未进入 campaign-root 查询或产品启动 handler。`steps=[]`，事务选项、业务保存及天数推进均为0；不能据此判断事务或继承缓存的业务结果，底层未提供完整快照的原因继续排查。公共 `verify` 实际 exit2，保持原失败，未制造成功 case 记录。

host 原 Popen wait 返回1，CK3 受管退出码为1；native job active0、进程树消失、三路最终清点均空、控制文件清空，managed session/thread/cleanup 已结束。这证明失败现场清理，不授正常退出0。最终新鲜1920×1080原图亲审 Steam“离线模式”，原桌面1024×768×32@60实际恢复；keeper 原父句柄退出0、线程已结束，CAS4221→4222实际 done/resources=[]。首次释放因缺少 CLI SHA pin 被拒，补全精确 pin 后释放成功；两份原始回执均保留。[R39 原始证据及诊断](2026-10-10-r39-shared-runtime-startup-red.md)另包归档。

精确 `00b88fc4d` 的 Official CI 已到失败终态，原因是既有 allocation 测试的模拟 `ids` 缺少新机器绑定接口 `MACHINE_ENV`；Linear 通过，Li Yu Dao 未触发。该 CI 夹具修复与原生快照只读诊断并行，生产 allocator 的机器绑定、原现场闭场和唯一 ID 守卫保持。正式 I3b/C3/I4 与一期仍 **NOT_GREEN**，上一工作量估计不因构建、闭场或 CI 修复上调。

## 下一场启动预算与已完成 CI 夹具修复

实际日志精度为1秒。R38启动后185.147秒记录Load Save、228.147秒 powerful vassals、331.147秒 In Game、417.147秒 Setup completion。R39原进程创建后对应前两阶段为240.764及299.764秒，在401.928秒结束前没有后两项。R38是历史独立launch再attach，没有保存同类startup budget字段，不能追认为旧400秒通过。R39的400来自新case复制通用LiYu配置，不是业务谓词。两轮日志及精确来源行已纳入R39原件归档。

仅未来新场的 `transaction-only-control` startup readiness 改为600秒：以实际R38完成417.147秒、R39前半段额外71.617秒为依据，约489秒历史参考加约110秒余量。command300、timeout2100、hold900、poll0.5、终点60秒及正常退出reserve90均保持，host/native、seed、正式71文件、六项overlay与业务谓词不变。这不保证加载成功，也不延长已结束R39或追改其RED；未来必须全新profile和ID，常规前驱闭场准入。

[CI窄修](2026-10-10-common-allocator-ci-fixture.md)已完成，34项相关回归通过：adapters9、bootstrap10、entry15；生产allocator/ID工具逐字节不变。旧00b88fc4d失败保留，后继精确CI需另取实际终态。

## 05:00 CST：R40 仍启动 RED，600秒没有解决加载问题

普通fetch/rebase后的 `598d4855b1a5e7678fa2253e5664acb991c0c825` 已实际推送，接入远端失败启动清理更新后54项相关回归通过。该精确提交 Official Runner CI 37988052013 和 Linear 37988052148 均实际success；Li Yu Dao未触发，单独保留。[原始CI及本地回归证据](acceptance/2026-10-10-exact-598d4855b-ci-and-rebase-tests/REPORT.md)含190项原件；本地旧回执没有独立HEAD字段，不补造其绑定。

新profile公共prepare/preflight均exit0，常规R39闭场准入实际分配 `bf-202609141645-5434332d4d--li-yu-dao--R0040`，未重复bootstrap。固定原seed、正式71文件和六项overlay、同一公共host/native，readiness600。run/verify实际exit2，host再次在原始本轮预算内超时，steps=[]。413份观察中前363份map_ready=false，后50份已map_ready=true/local_player1/actor31254/date53144712/event121，但后50份准入帧的pump_epoch均27770，未通过第二独立owner帧推进守卫，campaign-root查询和产品handler仍未进入。日志进入InitPostRead和缓存重算，04:51:05到powerful vassals，至04:56:15结束无In Game/setup completion，error.log仍0字节；日志缺完成行不能覆盖原生已map_ready的事实。此结果证明本次600秒预算没有完成准入，不增加或重跑业务动作。[R40永久记录](2026-10-10-r40-shared-runtime-startup-red.md)保留全部实际输入和失败。

原host/CK3退出码均1，managed session/thread/job/tree/最终空清点及控制文件清理完成，normal0未取得。新鲜Steam原图亲审离线、原1024×768桌面恢复；keeper原父句柄退出0/thread joined，CAS4234→4235实际done/resources=[]。当前无游戏和屏幕占用。下一步核两帧绑定、采样/更新链及实际启动路径，不再次仅增加预算；尚无已验证的底层修复。正式I3b/C3/I4与一期仍NOT_GREEN，工作量估计75%保持。
