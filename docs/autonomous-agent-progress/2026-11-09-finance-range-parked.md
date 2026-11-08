# P155：区间比较减少分配，默认生产仍 PARK

候选只将 `FinanceReadContracts.decode` 中“复制 framed body 后比较”替换为 JDK 数组区间比较；所有先行长度／LE／request 判断、错误消息、完整 frame 解析和独立 result-token 校验保持。正常输入域的逐字逆向证明与必要软件验证通过，但本次不采用到生产：pretty 延迟出现反向，compact 均值与中位数方向不一致，自然输入频率未知。current350 仍为 P150，正式生产与 Test 源码不变，不把同一 primitive 换到别处绕过此取舍。

## 两次执行分别保留

首次必要 production 1TU／9类、Test02 1TU／4类及 sole JUnit 都 exit0，case3.262秒／1P；但裸 `@TempDir` 在成功后默认清理，所需报告已经不存在。这是报告保留契约失败，首次64原数与性能为UNKNOWN，不能从1P重建、回填或拼接。

随后经明确授权，Test03仅将同一注解改为 `cleanup=CleanupMode.NEVER`，其余输入、64顺序、oracle、计时与堆预算逐字不变。原 production9与A9不重编，仅必要Test1TU4＋新的独立sole JUnit，case3.531秒／1P。新报告43,352B／SHA256 `da142898e490ca28b9c74039a332a606def3ca685a3de9e75a7f4ea556c84950` 真正保留；global_completed、全部64行后置条件、14个功能case／28次decode、3个构造期拒收、原件SHA均通过。构造期拒收不是进入decode的负例。

新测量为同进程隔离的actual A9与candidate B9，共享parent DTO／parser／writer；whole old compiled-source仍UNPROVEN，source307与formal的decode源码块相同不等于整族编译谱系相同。其它Gift准备差异单列，该prepare分支未在本测量调用，不归为P155收益。两组真实public请求／回执的frame分别为3,398,245B与3,398,297B，未知UTF8字段保留，不授Game／archive／collector整体行为。每种输入固定8轮ABBA、16A16B；compact先于pretty，0setup target-decode／0额外warmup。每行完整typed result、originalResult、receipt、成员顺序、canonical bytes与原frame／token／packet SHA核验后才合格；功能检查在64之后，不将后续暖态调用算入64。

## 新独立64行结果

| 输入／指标 | A | B | 限定观察 |
|---|---:|---:|---|
| compact allocation mean B/call | 94,972,696.5 | 91,568,095.5 | 8/8配对下降；首轮冷差保留 |
| pretty allocation mean B/call | 94,965,872 | 91,567,540 | 8/8配对下降 |
| compact wall mean ms | 27.77746875 | 25.56649375 | 均值约−7.96%，配对5负3正 |
| compact wall median ms | 18.91555 | 20.6223 | 反向约＋9.02% |
| pretty wall mean ms | 18.4334375 | 21.1652375 | 反向约＋14.82%，配对3负5正 |
| pretty wall median ms | 18.4262 | 17.9693 | 不能代替反向均值与尾部 |
| compact current-thread CPU total ms | 281.25 | 234.375 | 两侧median均15.625ms且含零量化 |
| pretty current-thread CPU total ms | 234.375 | 218.75 | 两侧median均15.625ms且含零量化 |

pretty最慢B35.2818ms高于A最大22.7666ms；compact首A85.671ms与B最大45.2657ms完整保留，不删冷首或事后增样本。分配下降约3.58%并不自动通过CPU／latency门槛；P154 inclusive caller次数不作CPU秒。两输入不按未知自然频率合成headline，原P149拒绝与P150限定软件采用不改写。

setup0.7129885秒、后置功能0.0168683秒、before-report3.087348秒，均不等于完整进程或交付费用。新JUnit recorder actor7.0424952秒／outer8.0867371秒；原JUnit actor6.9257885秒与失败报告保留成本不删除。新child stdout481B／stderr296B（保留目录INFO）与原481B／0B分开记；不是outer空输出。报告写出／JUnit返回／VM退出、编译、两次冷启动、等待、审阅、修复和后处理另按最终资格的完整窗口保留，不凭短测量窗授整体提速。

最终Native资格45,920B／`7516b55aa36796b2075adad396f79c40988622f057468f1c9e2aa0c050cccd94`与Root136个唯一原件重hash核验闭合，决定DEFAULT_PARK。Native三个owned目录写资格前1,488,244B，写前reserve及4MiB元数据预算通过；真实报告43,352B小于256KiB限额。这不修复首次报告缺失，也不改P141历史预算失败。

实际共production1TU9、必要Test2TU各4类、2次JUnit／2次case执行／1个unique方法；不是首次全交付通过，也不是生产重编两次。5阶段recorder actor合计29.9725743秒／outer资源子窗合计35.4065102秒，不能代替完整交付窗。最早本件已知SourceReady `2026-11-08T18:43:24.643825Z`→新末CLOSE1754.494645秒／→最终资格2216.504767秒，包含准备、审阅、原报告丢失、注解修复、必要重编、新冷启动、等待及后处理；此锚之前仍UNKNOWN，不记0。0新增SAVE，不报有限秒／保存日。

本次正常只发表unit／daily11-09／weeklyW46三份事实文档，P155生产候选与需本机props的Test均只保D，P156也维持D／PARK，不捆P157。current350不变，无业务／Test／AGENTS／CI改动，也无追加采样／重录／补测或Runtime／SAVE／10秒目标信用。

最终原件：[Native资格](D:/ck3-state/resume91-native-integration/p155-finance-range-retained02/QUALIFIED-P155-RETAINED02-COMPONENT64-FUNCTIONAL-PASS-DEFAULT-PARK01.json)；[Root默认PARK决定](D:/ck3-state/resume91-root/post-vacation-20261107/P155-RETAINED64-ACTUAL-MEASUREMENTS-DEFAULT-PARK01.json)；[Root最终136原件核验](D:/ck3-state/resume91-root/post-vacation-20261107/P155-FINAL-QUALIFIED-136REFS-DEFAULT-PARK-REVIEW01.json)（1,295B／`5d0b542e56393e258360c33565920e43bf6512a0afaa910bd372335825b23129`）。


原件：[首次1P但报告缺失](D:/ck3-state/resume91-native-integration/p155-finance-range-prod01/QUALIFIED-P155-ORIGINAL1P-BUT-RAW64-RETENTION-FAILURE01.json)；[新独立64行](D:/ck3-state/resume91-native-integration/p155-finance-range-retained02/tmp-junit/junit-12281326235103487882/p155-finance-frame-range-fixed64.json)；[Test03唯一保留修复](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-next155/test-draft03/TEST-SOURCE-READY03.json)。
