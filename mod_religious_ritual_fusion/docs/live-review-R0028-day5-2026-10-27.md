# R0028：冷载五日与新版界面实拍

`machine_id: 4-8e1c2f1861`；实际观察2026-10-27T03:55–04:31Z；冻结源码`7b671baf21af26a096dd86a34a67503c49b65426`。CK3实际1.20.0.4，EXE SHA`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本轮零日安全前置10/10，第五日6/7，业务未完整通过。

公共入口分配R0028／keeper a35，独立state冷载R0024真实保存，不运行seed、onStart或修复脚本。实际PID5920，原始Win32出生FILETIME字符串`134375469088985698`。来源保存68,524,252B／`170232f0b6f2060504fa8f1863584bc61b74a8a4ac6620366d0f67b770a0a0d1`，日期1066.9.18、玩家31254、Rite155、Faith13、Religion8。

外置根：`S=C:/workspace/rrf-development-20261024/review-fixes-a01/cold-day5-R0024-a01`；`L=S/live/4-8e1c2f1861--religious-ritual-fusion--R0028`；`B=S/metadata/normal-close-a01/root-business-oracles-a01`。

原generic adapter连续完成五个单自然日，原生日期53144400→53144520（1066.9.23），逐日精确增加24且暂停读回。未重复邀请、未再次原生定制、未超过五日。

- 原邀请对象45464、45458和预览拒绝对象33946仍存活，完整保存记录的当前Rite均为0。实际Faith13完整记录`main_rite=0`、`religion=8`提供归属关系；未选取Rite0完整记录。
- 玩家保存中`rrf_vassal_invited`与`rrf_vassal_pending`仍为45464、45458；`rrf_vassal_declines`仍为33946。待确认不证明原版消息已发送，预览拒绝不证明实际拒绝；原生发出／回复证据未观察。第三项要求明确false。
- 新礼仪155与来源152／153／154的完整规范token SHA均未改变，Religion8亦未改变。Faith13及部分角色存在自然变化，保留完整AST，不要求整条角色或Faith相等。
- ACTOR实际35,538条，相对零日新增4、移除10；RITE156、FAITH106、RELIGION49有序ID均未变。DYNASTY、HOUSE、COAT_OF_ARMS为`UNKNOWN_LAYOUT`，空集合不计通过。
- 第五日在原版信仰页重新取得当前155完整美德7／罪恶7，没有复用零日清单。名称、三项核心、31项教义及归属均有新读回，玩家虔诚仍5500。

零日原Java V4工具退出0，`B/zero/ORIGINAL-WAIT.actual.json`为4881B／`a370990640823af3ea10bb96c34154fea33e909c603bb3af5f71dedd87a6433a`；第五日亦0，`B/five/ORIGINAL-WAIT.actual.json`为4635B／`bc07cd38f79cfdd736323766461ec490c2daae99b17ba85a826d7ccbf5de3e55`。两次均持有拒绝写入／删除的原文件句柄读取18份完整选定记录，没有复制完整保存。第五日保存68,814,030B／`d31f43b990db39f48c521c5cb8681cd1e2b6ca4f79da07668e7eeb47e294ca50`。

普通SDK回执仍为`unconfirmed/save_binding_mismatch`，原生文件与V4不抵扣SDK continuation。零日玩家六个landed数值字段与R0024不同，完整差异保留，原因未证明。Root第五日审核`L/operator-plans/FIVE-REVIEW.actual.json`为66,045B／`1643e6ed26b093389880a219039d7498da8e09167fe90055bf65d82ce4f404bf`，原七要求6 true、1 false。

[两张实机素材](media/screenshots-R0028-2026-10-27.json)包括融合结果页与原版信仰页。原图2560×1440，绑定当前进程、日期及控件代数；JPEG仅Java格式编码，Root已逐图查看。公开下载仍0.1.0-alpha，图片拟标为未发布0.2开发预览。04:44Z，目标owner页面实际出现“登录”，已打开浏览器登录页等待账号持有者登录，未提交图片，Steam客户端模式未改变。

原CaseClient因业务不完整进入正常typed退出。原生进程、保留OS句柄、host、keeper、allocator原wait均0；公共run／verify／Root原wait均2。原Root工具session13527、终态chunk`3f8502`已消费一次；显示恢复1024×768，SCREEN14186→14187精确释放。`S/metadata/normal-close-a01/ROOT-OUTER-WAIT-AND-CLOSE.actual.json`为2627B／`4ffb7f006ac1eb1692fe708c2109554fe483761697d63ac0f617b0cc2f0d566c`。

Root零日审核误复制完整GUI树和after_snapshot，产生8,300,297B原件并超过case8MiB预测，原件及已消费结果保留。闭场normal_close owner17,653,760B超过16MiB、public_preparation owner16,859,136B超过14MiB，均保留历史RED。总scene及全局容量通过不能追认owner预算通过。

存储闭场a01在CAS前因9个exact guards超过工具上限8而原退出1，245未变；a02仅去掉已校验BASE的冗余短锁guard并换新输出，实际245→246。全局owned6GiB／gross8GiB／quota84GB／物理容量检查通过，本scene未来写入归零，未删除或改大原场预算。实际报告为`C:/workspace/rrf-development-20261024/review-fixes-a01/finalized-cold-R0024-a01/metadata/normal-close-a01/store-ui-media-a02/cold5-close-actual-a02/CLOSED-COLD5.CAPACITY.actual.json`，24,733B／`0cf1fe10f8f4b51035d5a6f7d6eeec88397ec93034321b71fdb28feeb8ea7b91`。

下一步修共享邀请发送阈值并验证原版实际回复，不对本场不明结果重试。长名换行、独立MTS四项／无MTS三项及RRF＋DES联合维护仍需各自实机，八项审核尚未完成。
