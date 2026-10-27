# 融合后只读状态帧竞态：R0032

`machine_id: 4-8e1c2f1861`，观察日期2026-10-27。源码基线`502f922c26c76f0a749aaf582522d60d08cb295d`；CK3 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。

本场未通过。公开下载仍为0.1.0-alpha；本记录不授0.2发布资格。

## 实际失败

场次`4-8e1c2f1861--religious-ritual-fusion--R0032`在1066年9月第二自然日暂停。新草案通过真实父级`button_group`选择，最终将律法主义移除、补回秘传，目标为秘传、占星术、天主子民与允许离婚。透明checkbox只负责显示，先前对其调用没有改变选择；后续使用实际拥有onclick的父控件，没有重放该未知动作。

13:15:49Z，generation19的`rrf_commit`控件27仅派发一次。回执为handled/verification_pending，after_snapshot仍为native10/public11、虔诚6000。下一只读宗教查询携native10，被原生以`player_religion_published_frame_changed`拒绝。随后原生发布native11，日期和暂停状态未变，虔诚为5500。后一个发布不能倒推前一个查询成功，也不能证明完整新礼仪、来源、费用及保存图已经验收。

拒绝位于`ck3_12002_religion_mailbox.cpp`进入查询mailbox的完整帧一致性校验，早于宗教字段读取。这里没有证据支持放宽whole-frame守卫，也不应重放融合。

## 资源关闭

原CaseClient执行一次typed正常退出、禁用退出保存，独立保留handle与原生均观察到进程退出0。失败shutdown消费实际后态后finish_hold，host原wait1、public run2；业务和normal_close资格均保持false。

Root调用共享`validate_preserved_failure_native_os0`校验后停止原keeper，消费原allocator0、keeper0及Root外层session77404的终态1（tool chunk `bf94e8`）。显示恢复1024×768，按新鲜sequence释放SCREEN，release事件14249。

后续调用真实`previous_failed_live_resource_closure`，并在既有machine writer锁内重验；账本和计数器未写入。行政资源接续通过，不把失败改为正常关闭或业务通过。

实际根：`C:/workspace/rrf-development-20261024/review-fixes-a01/fresh-no-mts-review-a04`。

| 原件 | bytes / SHA-256 |
| --- | --- |
| `metadata/normal-close-a01/R0032-mechanical-close-a01/SCREEN-RELEASE.stdout.json` | 1336 / `6f2f586a3b58d87769a35d6b04f6430ec44c70967bd53eaae7192a5d751c12b2` |
| `metadata/normal-close-a01/R0032-resource-recovery-a01/EXECUTION.actual.json` | 6579 / `cac8d61076eb08daa601660e898bd41269c2e95e4dbb200b28b3de8d0e6c7ecb` |
| `metadata/normal-close-a01/R0032-resource-recovery-a01/FAILED-LIVE-CLOSURE.actual.json` | 10488 / `e9c4c832911208f56079a711d45b99adcf11b4096a8c818412e0df41f429db8a` |

恢复producer原session89126由Root消费为0（`d5045c`）。机械关闭候选a02曾在STOP前拒绝：通用runtime inventory包含尚待停止的当前keeper。a03只允许与原记录PID、出生时间、argv匹配的keeper及其相同argv子进程，其余blocker继续拒绝；原失败保留。

## 修复和验证边界

共享SDK修复仅允许当前玩家宗教的无参数只读查询，在精确匹配上述失败回执后，等待Condition收到真实新publication。在同一总timeout内，要求更大的native/public revision及相同构建、进程连接、运行、玩家、日期、暂停与事件边界，再独立读取一次。

成功结果绑定实际新帧，并明确记录初始授权revision、被拒请求及完整错误回执、新revision与新请求ID。第二次读取继续使用原先完整帧校验，失败不再重取。所有写操作、Confirm及UNKNOWN动作的提交规则不变。

2026-10-27T13:48:17Z核对时，四个修改文件仅完成语法和diff检查；完整CI命令组、SDK独立进程和新实机尚未执行。实际后续结果须另行追加，不能把本段设计算作修复验收。

## 2026-10-27 实际本地验证

`machine_id: 4-8e1c2f1861`。正式准入为storage revision268，验证根`C:/workspace/rrf-development-20261024/review-fixes-a01/review-validation-a18`，累计上限576MiB。执行身份始终为上述`502f922c…`基线加实际工作树修改（`SCOPED_WORKING_TREE`），没有追认为后继clean提交执行。

原生构建命令于14:18:45.753851Z开始、14:33:45.907348Z原wait0；仅构建现有pilgrimage traits独立fixture目标及其依赖，不是新DLL或实机资格。随后原CTest精确单项测试为原wait0。后继SDK修改不消费于这两条纯原生命令；a05复核整个native源码/CMake与实际Python生产依赖字节相同，保留原始混合来源表及原执行身份，没有重编译或将旧SDK字节改称当前输入。

最终a05在14:59:37.795983Z启动，重新完整执行命令3–18，16条原wait均0、跳过均0，原外层session28740亦已消费退出0。完整宗教wire/SDK模块13项（包含真实Condition及独立`-I` Python进程）、traits模块6项、三filming/acceptance模块27项、Rite持久化模块26项均通过。原CI五模块strict与两个完整修改leaf的strict均通过；后者使用`--follow-imports=silent`加载真实依赖模型，不授导入driver函数体完整strict信用。

分类修复同步Python builder与Java六链producer：仅精确的通用宗教transport归`shared_sdk_delta`，其余HOF分类不变。对应完整五条CI命令实际为36、78、28、28项测试及原strict检查，全部通过。默认Maven实测3.10.0（该机Maven home为`C:/apache-maven-3.9.16`，Java25.0.4.1）；RRF完整offline `verify`于15:04:19.401842Z结束，100项测试、失败0、错误0、跳过0。完整分类函数与既有分类测试类的AST strict，以及完整builder/entry/launcher非strict也均为原wait0；这不是全仓静态或云端CI通过声明。

先前原件完整保留：a02在原生构建成功后因CTest不在子进程搜索路径而尚未启动CTest；a03额外strict采用skip导入时将真实`BridgeUnavailableError`视为Any而失败；a04采用真实导入模型后暴露`dict[str, object].get()`丢失`activity_terms`类型的1项错误。最终仅保留normalizer实际返回值的typed局部变量，未用cast、ignore或放宽运行时合同；a05对消费该leaf的命令3–8全部重新执行。旧失败没有改写为成功。

| 最终原件（相对验证根） | bytes / SHA-256 |
| --- | --- |
| `metadata/all-step-a05/EXECUTION.actual.json` | 14179 / `0cc374a721b82b79b3625b666785dfea3ef5fe133b39a92be7749d8ca24ce6cf` |
| `metadata/outer-a05/ORIGINAL-WAIT.actual.json` | 1194 / `fd6540d6420a95d688594ed26bdb10ac6082b36f208de64b7c956df3406b5d42` |
| `metadata/all-step-a05/SOURCE.before.actual.json` | 2608800 / `fd0e0803d6992b7bfe64e9130bd7ab3771b5a1023d4ee7aa02450f906bafd02a` |
| `metadata/all-step-a05/SOURCE.after.actual.json` | 2608800 / `0ff0b049038b2693542e6daa43c92960a78e44a98dce02170950960f251ff792` |

两份来源表的`source_pins`与operator来源逐项完全相同；原JSON观察时间不同，不以整文件hash相等冒充源表比较。a05收尾时目录计入的实际占用为359391232B，采样峰值356765696B，后者不是连续峰值。以上仅证明声明的本地构建、测试、静态和来源范围，R0032业务仍失败，修复后新实机尚未执行，既有hosted Quarkus TEST仓库故障仍保留。
