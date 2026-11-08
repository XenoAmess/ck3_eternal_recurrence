# P117：同一quote精确结果复用以减少intent分配，墙钟未改善

本单元确认主线程分配下降，未确认延迟或端到端提速。同一DATA消费者的whole分配均值945644044→892130767B，约少53.5MB／call（-5.66%）；墙钟均值仅639.4407875→637.99885ms（-0.23%），中位636.862→640.4039ms（+0.56%），actor均值10.67553535→10.937727秒（+2.46%）。全部反向指标和慢样本保留，不复跑挑选更快结果，不把功能资格当成速度通过。基线为[P116](2026-11-08-construction-financing-header-performance.md)真实成功B，不相加百分比；P116原基线也独立保存。

源码仅ConstructionDomainLifecycle的既有private五参数intent计算，9add／1del。原DriverJson.encode(query)继续执行；只有同一ObservedRequest的NativeQuote已有P114 exact cache，且queryBytes与该quote.original()逐byte相等时，才复用防御clone所得结果。cache absent或原件表示不同就lazy调用原ConstructionOriginalSource.finalizeQuery；旧small／inline保持原fallback。未使用会经经济codec重编码的selected().original()。该处只复用纯计算DATA，完整same-session CAS／cold reload、header／frame／candidate／expected／diagnostics／income和目标body规范输出核验原样保留，未缓存跨READ或实际权限。

真实模型任务在2026-11-08T01:02:53.796378Z开始，单POST200／stop，总6.5775491秒、TTFT2.9545723秒、22282prompt／564output，cached tokens=null。采用完整literal单hunk，已有Arrays import；其中无害的冗余局部初始化也未为风格改变。模型没有运行测试或业务动作，输入为五份完整当前源码快照。正式仅Lifecycle一TU／8class实际编译通过，5.546034秒；Native第一次准备器旧helper文件名误配发生在claim／JVM／BEGIN前，独立留证，不计源码编译RED。

## 新回归与作用域

owner新Test首编因quote(true)声明throws Exception却放在仅允许IOException的writer lambda内而javac RED，1error／0class／0JUnit。原件保留；最小修正只是把同一份pure full DATA构造移到进入writer之前，不改输入、断言、生产源码或Guard。Test02必要增编后，三个新方法同一JUnit JVM真实3P／0F／0E／0skip，actor12.0246114秒、XMLsuite10.104秒；未重跑旧P113／P114／P115／P116绿套件。

新验证通过真实独立SOFTWARE same-writer Windows归档端口保全full source，cold resolveCommand得到真实Loaded，再直接调用包内intent三参数入口，断言完整canonical pending body与旧finalizer参考逐byte一致。高精度opaque world／negativezero／exponent用于对照既有fixed输出，调用前变异getter返回数组仍不影响结果；不同实例的proof1缓存不会串到proof2请求。旧public small cacheempty的原intent字节保持，新的当前header改动仍被物理full loader拒绝。

独立fallback oracle只反射既有private纯五参数计算：同一命令和完整request配等价oldsmall typed参考使cacheempty，从而强制原finalizer。另一反例故意传入proof1的ObservedRequest和proof2的request／命令，仅作为该纯函数DATA测试；exact mismatch必须fallback并输出与真实fresh Loaded proof2相同的完整body，误用proof1缓存会被原proof guard拒绝。未构造新公有raw／typed pair、假Loaded、私有权限issuer或RootGuard。该验证不授真实动作执行、Native verifier正向、owning publication、Root／Runtime许可。

## 完整同DATA对照

沿用P114 Main03原binary（26020B／6660ee3c3ecf375b620eaeb63b5355c1b8cb3763dbe8e9cffbeaa0111ddd1da0）、原6831978B input／Q2、同绝对warm-existing CAS、source／ref和DATA／EXPECTED；无Main重编、新PREP或dataset刷新。Main真实调用loaded→intent三参数入口，覆盖此次改动，不用手写算法冒充Policy。查询原编码、cache clone／原件clone／memcmp、fallback、所有构造、compose、preserve／读回、cold resolve、Q2、canonical body、writer获取释放和marker验证均保留在原完整DATA窗口。

A0／B0／B1／A1四独立JVM，各2warm＋4measure，CPU1／384MiB／90秒。全部8warm＋16measure、全部错误和慢样本保留，无forceGC或速度断言。raw内部label仍B0／B0／B1／B1，实验逻辑标签另映射，真实variant由Lifecycle完整8class族SHA、first-origin与ordered CP识别。P116 targets5和P114 cache16等共同依赖保持，原source／CAS／head／anchor／lock／store身份不变，每进程新allocation card单列，不称整个文件系统相同。全部24call cached=true／warm=true／marker=原EXPECTED，whole等于disjoint阶段wall／CPU／allocation之和；cached marker属于共同P114路径，不伪装成新增intent marker。

| 指标 | P116基线A | P117 B |
| --- | ---: | ---: |
| whole墙钟均值 | 639.4407875ms | 637.99885ms |
| whole墙钟中位数 | 636.862ms | 640.4039ms |
| whole主线程CPU均值 | 304.6875ms | 300.78125ms |
| whole allocated均值 | 945,644,044B | 892,130,767B |
| whole allocated中位数 | 945,644,092B | 892,132,124B |
| intent墙钟均值 | 103.7320625ms | 102.18815ms |
| intent墙钟中位数 | 77.18775ms | 85.6513ms |
| intent allocated均值 | 114,648,223B | 61,135,660B |
| process actor均值 | 10.67553535s | 10.937727s |

intent分配约减46.68%，whole约减5.66%；intent中位墙钟变慢约10.97%，不能称缓存命中就已提速。未改resolve均耗226.110675→240.6128875ms、preserve78.50255→63.5974625ms等波动也全部保留，不把差额选择性归因给本叶。完整四actor合计43.226524699945秒；ABBA含阶段间隔47.452576秒，从首生产至末close396.433924秒还包含源码错误、准备机械纠正、编测、审阅及等待。主指标没有用只含timed样本的分母替换完整窗口。

业务证据根D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-intent-result117。Native最终QUALIFIED-P117-INTENT-AND-CONSUMER-DATA01.json43237B／33eb979f6a093c4b13e527f9c3fbbf3cca5174e2ce03ffe16b9190f1e5fdcb1b；全样本399381B／35202ce5a5bc6f599e58ad383cbfaa83ac51bcb53be459aac62f1a74d11a136e；identity6593B／d36ab293afbda415f32cca92604436be74ac6659a39386b3c4da50888f82c867。Root逐件核全部24call、原EXPECTED、phase sum及实际close，独立proof112138B／fff2a4fe9ee441673d965dd75850e94fed83ea1c685cf437a8652723d8f935c0另存。

本轮保留为窄分配优化；若后续真实墙钟证明受损，使用正常新提交撤回，不重写历史。它未Runtime采用、没有新增SAVE，10秒／已保存游戏日目标仍未通过。下一项只研究SDK内部第三遍多MB解析的同owned节点复用，旧byte入口及外层完整custody／header／Guard保持，不引入公有任意raw／typed pair或通用JSON平台；持续目标继续。
