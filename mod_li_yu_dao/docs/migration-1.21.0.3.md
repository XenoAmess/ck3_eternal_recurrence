# 0.1.3 / Florin 1.21.0.3 兼容候选

本轮实际目标：`desktop-3fevhd2-1c74096080`，CK3 `1.21.0.3` / Steam `26785313`，EXE SHA-256 `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`。这是离线源码迁移，新的加载、业务效果、保存重载、Native资格与Workshop更新另记实际回执。

公开基线为 `li-yu-dao-v0.1.2-alpha.1` / `1619030d839b721109c21286ab9d7cce01886f38`。其[发布记录](../../docs/release-changelogs/li-yu-dao/0.1.2.md)包含实际上传、匿名完整Notes、83文件正式清单、真实缓存下载及当时机器1.20.1加载和正常退出。迁移前当前整个产品对该tag的diff为空。README原来把0.1.2称为未发布候选的文字已纠正；0.1.1和0.1.2的原版本、机器及失败不改写。

## 实际接口变化

新版原版tenet正文、modifier格式、活动效果与数值源存在以下变化。修改权威`content_data.py`、`tenet_playstyle_data.py`和既有生成器，再从真实生成链产生运行文件；没有新增Python生产模块。

| 原字段 | Florin字段 | 本轮行为 |
| --- | --- | --- |
| `county_opinion_add` | `popular_opinion_add` | 保留好感点数与正负取舍 |
| `tax_mult` | `all_tax_mult` | 保留全部税种意图与原倍率，未窄化为宗教税 |
| `development_growth_factor` | `prosperity_growth_factor` | 接入新版繁荣增长，更新中英文说明，保留原倍率 |
| `monthly_county_control_growth_factor` | `monthly_control_change_when_below_baseline_mult` | 对应低于基准时恢复，保留原倍率 |
| `monthly_county_control_decline_at_war_factor` | `monthly_control_change_at_war_mult` | 对应战时控制力变化，保留原取舍 |
| `change_development_progress` | `change_prosperity_progress` | 四处主动进度效果改用真实新版原语，保留50/75进度的数量意图 |

发展与繁荣是不同机制，不能把本轮表述为原效果完全相同。原版当前普通/较大繁荣进度数值为40/80；本轮效果的实际传播、上限与平衡须在新实机确认。费用、冷却、分支数量、状态ID、知行相资的一年等待及玩家入口守卫不重设。

`monthly_income_mult`和`domain_limit`仍出现在当前格式及真实Character消费者，保留原玩法。当前82条modifier源引用中79条有实际同容器tenet例子；总收入个人效果、普通角色直辖上限、个人全部税种三项明确记为通用格式连续性，不能冒充同容器实机证明。源行号与旗标消费者均按本机实际文件更新；`validate_static.py --game-dir <game>`可读取当前原版并检查这些源引用，输出仍为`runtime=NOT_RUN`。

## 保留的功能与后继验收

- 保留36礼仪、36信条、36专属行动、52选择分支，以及个人信条须由本人在原版窗口实际选取的条件。知识或允许不自动授予个人效果。
- 保留原版`confucian_faith`、经学、道学和实际主礼仪，不新增faith覆盖或整信仰自动迁移。新版原版仍以faith及rite类型、原版个人信念窗口的数据模型与实际选取入口承接；源匹配不替代GUI与效果传播。
- 保留完整派别名单、各派三分之二学者、所有实际玩家同意、代表签署、过期与失效重验。M3资产守卫、C2授权、C3/I3b工厂及继承保护相关运行字节相对公开版保持；不以本轮迁移静默取消这些约束。
- 原版宗主工厂仍使用动态头衔、`temporal_head_of_faith_succession_law`、`same_faith_succession_law`和真实绑定/授予事务；原`on_death`及新faith回调的scope约定已查正文。没有把原版完整工厂直接覆盖到本产品，也没有据此修复或清绿B4。
- 历史R90制度链未完、B4政治继承与玩家继承保护失败、冷重载/NPC授予/C3完整争统/I4自然到期等原状态保留。本轮不把全部未来研究扩成新发布硬门，也不把软件通过换成这些场景通过。

本轮先验证实际生成链、完整现行产品软件测试、受影响共享消费者及双构建。后继实机应先确认新EXE确实加载本次staging与无相关引擎错误，再覆盖这次字段变化的普通/个人/县域效果、主动繁荣进度及原版入口；既有场景继续按[验收矩阵](acceptance-matrix.md)判断。

`run_acceptance.py`、旧factory诊断与历史Native proof继续保留原1.20绑定。生成器读取的R0002入库原件只是原构建的历史出处；没有改其版本/哈希、旧地址或profile来取得1.21 ABI资格，没有触碰旧savedPair。新版实机必须另有真实通道资格；不能只给旧工具换版本字符串。工坊canonical仍为`3817934804`，0.1.3尚未发布。
