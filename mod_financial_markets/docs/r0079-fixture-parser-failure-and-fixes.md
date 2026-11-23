# R0079：fixture日期解析失败与后继源码修复

2026-11-23，机器 `4-8e1c2f1861`，CK3 **1.21.0／26622941／2F2B**。Core53已实际build返回0，manifest属于静态候选范围；较早“Core53未build”保留其历史切点。

R79实际engine拒绝了四处fixture日期RHS内联`value／add`：`xfmr_guards.txt:68`及`xfmr_observe.txt:275／281／305`。原WITNESS保留前16行及完整日志身份。Root操作记录证实**0 setup／交易控制请求、0日期推进请求、0原生SAVE**；该口径不证明Game_load初始化等世界内金融效果为零，未观测部分保持未知。

原公共run返回 **2／647.8133634秒**，verify返回 **2／0.4723545秒**，状态`NOT_RUN`、`normal_close=null`；case及normal-close两个“Original held session is no longer active”错误均保留。原typed退出另有Game0、Host0、retained OS0、Job0、keeper0及allocator0证据，CAS16382→16383／done／资源空。因此`normal_close_qualified=false`和`normal_resource_exit_proven=true`同时成立，资源正常退出不能改写成公共case通过。

闭场后正常FF到19447d7a，合并12个金融文件的风险日期修复、两处SYN同类日期修复及只读角色discovery接线；C++改动是在关闭分支用`(void)family`处理未使用参数。它们尚无新engine通过信用。

后继受影响金融组实际 **99个distinct全部P／0FES**，产品来源before／after不变；外层原wait **0／85.1141458秒**，内层Maven原wait **0／83.5224397秒**。五模块Python组197项原0／141.3809026秒，框架内报138.102秒；其内15项optimized另有原0／13.0497049秒，内部unittest报7.189秒。三源typing原0／4.0981249秒，原notes保持。

随后默认完整金融verify实际 **709个distinct全部P／0FES**，无测试过滤或skip，产品before／after来源不变，实际保留56份Surefire XML。外层原wait **0／247.2504184秒**，内层Maven原wait **0／246.0227761秒**，两层分开记录。709包含99，15项属于197范围，均不与前序701或其他增量组相加。

完整verify的`head_at_start`为19447d7a，按原SOURCE-WINDOW限定金融产品及相关工具来源。金融12＋CPP1工作改动不构成Native资格；3叶Native profile未列入该金融来源清单，也不由709项授予资格，不据此推断采用先后。原初稿“新完整verify未BEGIN”保留其当时切点，本段只补随后真实结果，不能回填R79实机失败。

Core54未build，Q56及后继Game未RUN；20剧情实机场、SYN4096、完整产品及Workshop首发继续待验。前序701和[R78有限35日窗口](r0078-e8-continuous35.md)各保原来源。原wait、WITNESS、Core53 manifest、源码采用及闭场pin见[本轮紧凑索引](../../docs/maintenance/evidence/2026-11-23-financial-markets-r0079-fixture-parser-failure-and-fixes.json)。
