# 物理存档审计

金融工具复用共享`ck3-save-core`的plain/ZIP/显式decoder读取，命名Quarkus入口为`save-audit`。默认validate/build入口保持原用途。审计只读指定物理文件，不连接Game或修改游戏状态。

命令为`audit --inputs request.json --output unused-external-report.json`。请求须显式给机器、仓库、源SAVE的真实路径/bytes/SHA、实际编码布局、零或一个冷载SAVE与decoder。输出使用外部已有父目录下的新文件，拒绝覆盖。实际加载的审计和parser源码资源、POM及代码来源在处理前后核对；旧同版本jar不能冒充本轮实现。

请求路径与规范物理路径分别保留，前后核samefile、属性及SHA。所选故事单条最多512KiB、总计64MiB、记录最多200000；共享旧schema与原4MiB保留限制不扩大。大市场可能触发限制，必须记录真实拒绝并根据实际需要调整，不能截断后假称完整。

先从真实1.21物理SAVE核版本/格式、数值scale、story与character引用类型、故事表和global exchange。缺变量、未知type与省略identity不得默认为零。币/账户/仓位/债务按永久ID、原生story引用及法律holder核对；技术story_owner不等于产权人。金额分别核现金、冻结、费用和基金，债权不当现金。

布局的可选第六字段为`numberIdentityEncoding`，枚举`identityRequired`、`omittedZero`或`unsigned64OmittedZero`。旧五字段JSON与旧Java构造/位置CLI仍默认`identityRequired`，不隐式改变历史报告语义；显式null、错类型、未知值和未知字段拒绝。后两种模式只允许明确声明`1.21.0`／格式`19`／scale`100000`，且共享parser第一遍完整、有界metadata投影的版本与格式实际吻合；同名块与标量重复也拒绝。在这两种模式中，仅真实存在的变量中恰好为`data={type=value}`的编码可解释为数值零。缺变量、缺data、缺/错type、含额外不明数据、重复或畸形identity仍不完整；story/character/global引用身份缺失始终不推零。所选模式会写入输出`layoutHypothesis`，候选仍不授金融认证。

`unsigned64OmittedZero`另将恰好为`type=value`加一个identity的数值包按64位补码解码：identity必须是规范无符号十进制，范围`0..18446744073709551615`；先验证范围，达到`9223372036854775808`时减`18446744073709551616`，再按`100000`精确整除。负数字面值、越界、前导零、小数、额外不明data字段均不容错，不截断或取模。`identityRequired`与`omittedZero`的有符号十进制原语义保留；story/character/global的原生ID完全沿原引用路径，不按数值scale或补码转换。R0013完成提现后的发现原件`6435749508278093a3e726801b388ecc14dda89c9225216adaee2c0c04707dcb`在native合同75、96的`xfm_last_daily_day`均记录raw`18446744073709451616`，对应原生产`xfm_futures_orders.txt`明确初始化的`-1`哨兵。新软件测试保留此57640字节发现原件及两条记录；重建文本是软件投影，不替代原物理SAVE、实际审计或冷载。

该显式选项依据R0013实际钱包归档：`140063587`字节／SHA256`409b15a5d8598d2a6e77f118bf025762dbd2da35013d7ede2e0c287ceec91df6`，其只读发现原件`2147b527455eb3b9eee2d83b4eb78cc3506c69d54de97e6e8610a5b85819bc15`同时观察到真实正值与省略零。全局exchange指向story52；主账户story54的account_id raw200000对应永久ID2、free raw100000000对应真实预存1000分，holder为char31254；基金story53的account_id/system1均raw100000，而free/reserved及exchange.day等`type=value`省略identity。实际原件与独立本金255→245金币共同支持该确切布局，不把缺变量补成值。软件回归所用JSON是发现原件的逐字副本；从其变量包重建的测试文本明确是软件投影，不冒充原物理SAVE、共享实际审计或冷载。

冷比较需要另一个真实进程载入后、同暂停日期的物理SAVE及独立装载证据。同文件复制或对象总数相同不能证明冷载。候选报告始终`financialCertified=false`；exit0只代表已选择字段约束成立，exit2为不完整/冷比较不同，exit3为约束冲突，exit1为输入或处理失败。真正业务认证由实际动作、完整财务读回和运行证据共同判断。

`audit-retired-xfma --inputs request.json --output unused-external-report.json`是显式兼容入口。R0016真实存档中的旧观察story51缺少`story_cycle`，只留下owner、seed和数值`xfma_complete`；原`audit`拒绝此记录的失败保留。新入口仅接收完整、唯一的owner/seed/variables封套，且变量非空、名称唯一、全为规范`xfma_`数值观察量；任何`xfm_`金融字段、引用值、未知结构或其它缺类型故事仍拒绝。报告逐条列出原生ID、owner、seed、规范token哈希／字节与变量编码，并要求两遍ID及哈希完全一致。旧`audit`、原reader及共享七参数流式合同仍默认严格拒绝。

兼容入口仍读完整两遍，不按故事批次重复读取整个SAVE。普通非选中故事读到类型后即释放暂存前缀；真正缺类型记录才保留完整512KiB有界AST，总流式工作64MiB及原投影限制不变。它不会补写存档、恢复已丢失的类型或把未知金融记录当零。后续观察包同时保留已发表core及epoch1的无回调类型声明，以免正常续载时再遗漏这些已知类型；任意其它旧epoch须先按真实来源扩展兼容目录。

2026-11-18，machine_id`4-8e1c2f1861`：共享原10项回归及金融完整160项通过，其中两项SAVE JUnit复用52个合成断言；这不是1.21实际编码、命名入口实用或冷载通过。对应原件位于`C:/workspace/ck3-market-live-20261118/operations/MVN-save-core-audit01`与`MVN-financial-ai-save-full01`。

14:21Z后命名入口已单独实际打包至`target/save-audit-app/quarkus-run.jar`，原wait0/20.194778秒；随后公共CLI对明确标记的合成物理文件实际wait0/1.198547秒，得到来源绑定报告且`financialCertified=false`。原件分别在`operations/MVN-financial-save-audit-package01`、`operations/CHECK-save-audit-named-cli01`及外部`save-audit-cli-software01`。这只验证命名入口和合成输入消费，真实1.21金融SAVE、编码scale及冷载仍未通过。

16:41Z完整金融246项通过，其中回兑新增7项与原SAVE两项共同通过。审计显式识别`xfm_finance_redemption_window`及`xfm_finance_redemption_receipt`：逐窗核initial=paid+reclaimed+remaining、每张实付/整手/固定价及预算after、逐币永久收据顺序链/累计与ID高水位、当前窗专用free=remaining且reserved=0、发行及做市账户防冒用、旧窗到期后七日发布限制。历史窗可复用同一专用账户，不能拿其旧余额覆盖当前窗；收据的历史holder/controller不强制等于继承后的当前holder。未知故事、缺失数值或断链保持INCOMPLETE，不推断空集合或零金额。字段与生产者见[回兑身份表](coin-redemption.md)。

16:43:44Z命名入口已按本轮源码重新打包（`MVN-financial-save-audit-package02`，原wait0/25.422001秒），随后`CHECK-save-audit-named-cli02`实际wait0/1.172256秒消费合成物理文件。当前419628字节app JAR、嵌入源码资源及实际loaded-code pins逐项与当前审计／共享parser相同，包括回兑审计；无需再次打包。两轮合成CLI均不授真实SAVE信用。

R0011于20:47:12Z首次实际保存并于20:49:41Z完成独立外置物理归档：132739080字节／SHA256 `d58e7f82bf607ff1cb2957f19e8d0263dd1f1e852e63de3801e502800a2e4a66`，源与归档身份不同且复制前后大小、属性和SHA一致。真实文本头为1.21.0／格式19／1066.9.15；有界完整字节词法核验仅发现51个原版故事，尚无金融exchange或账户。这是初始化前missing/incomplete基线，不是共享parser失败或金融认证。数值scale及金融引用类型仍未确定，没有套用合成值或制造可执行审计请求；下一次经正常GUI初始化后SAVE，才继续现有named审计。[实际证据](../../docs/maintenance/evidence/2026-11-19-financial-markets-machine4-r0011.json)。
