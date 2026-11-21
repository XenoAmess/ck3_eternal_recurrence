# 自动升级建筑（XenoAmess维护版）

本目录是 Steam Workshop 条目“自动升级建筑”（上游 item `3596580780`，原作者白绮）的仓库内维护源码。
当前基线来自 2026-09-11 下载的上游 7 文件版本；原始字节与逐文件哈希记录在
[`../docs/auto-upgrade-buildings-upstream.md`](../docs/auto-upgrade-buildings-upstream.md)。仓库内
`descriptor.mod` 只移除了只能存在于用户目录外层 `.mod` 的 `remote_file_id`，其余运行时文件在首个导入基线中保持上游字节。

## 玩家合同

- 入口：玩家决议“启用自动建造”与“禁用自动建造”。
- 启用后：由唯一全局循环每 15 个游戏日检查玩家直接持有的地产；每名人物每次扫描最多成功升级 15 栋建筑，每条已有下一等级、符合原版资格条件的建筑链每轮最多即时升级一级。
- 覆盖：CK3 1.21.0.3 的677条建筑链、2,583条非伟大工程升级边；只在玩家直接持有的城堡、城市、神殿、部落和神殿城塞地产内处理已有建筑。
- 费用：使用对应建筑的原版基础费用和金币／威望／虔诚／scripted cost 资源形状；启用时可选择“只用国库”“只用个人金钱”或“优先国库”，同一笔金币费用不拆分，资源不足时不升级、不扣款。
- 超直辖策略：启用时同时选择“超直辖暂停”或“超直辖继续”。暂停只跳过超直辖期间的整轮修建，不关闭 15 日循环；回到直辖上限内后自动恢复。
- 继承：玩家角色死亡并继续扮演继承人时，启用状态、资金策略和超直辖策略会原样迁移，唯一 15 日循环继续生效。
- 排除：所有住所系统、游牧／牧民地产、16条伟大工程链的61条升级边、其他领主持有或所有权未知的贸易站、正在施工或出租的地产、空槽与没有下一等级的终级建筑。
- 资格：在建筑所在区域调用原版完整建造资格检查，包含区域等级、革新、文化、礼仪及其他门槛；资金单独按所选策略检查，不兑现原版定义之外的提前升级。
- 玩家/AI：只允许真人玩家启用，AI 永不触发。
- 旧存档：保留上游 `auto_build` 事件命名空间和 `enable_auto_build` 角色 flag；没有三期资金 flag 时继续按“优先国库”运行，没有四期暂停 flag 时继续在超直辖状态修建；4.0.1 起，已经启用的玩家会从下一次死亡继承开始自动迁移这些状态。4.0.2 的每轮计数在扫描开始时自动清零，无需存档迁移。

## 维护目标

当前发布候选为4.0.4，目标 CK3 `1.21.0.3 (Florin)`；本段已记录下述实际业务范围，正式tag、Workshop提交与下载核验仍须按发布回执分别记录。

本机 `desktop-3fevhd2-1c74096080`／build26785313／EXE859f 的当前验收按实际范围分层：九项区域探针另列；原十九项矩阵中普通六项、holding四项、特殊一项与曼荼罗四项已有当前构建观察。公国一项沿用266构建真实施工及8/8业务证据，并以军区建筑／区域定义逐字节不变、热修升级规则图一致作兼容判断；原公国整体INCOMPLETE、渲染诊断与日志超限保留，不标为267新施工通过。原三项继承已在本轮派生场实证：原角色36423真实死亡，官方默认Continue一次后独立确认实际继承人46669与窗口关闭，两次自然日推进至1066-09-17，原启用、策略与循环存在判据各一次通过。该场只观察到引擎已在Close前分配继承人的关系；不声称Close完成角色分配、播放鼠标动画或覆盖另两种关系，也不授严格十七日回调或队列基数。至此原十九项代表性业务按18项当前构建实测加1项历史公国业务复用记录，不称19项全fresh。

原R24六标签／六悬停／三个预览及R26两轮启停本来即是当前267/859构建；三组345文件载荷逐SHA相同，直接复用各自实机证据，不提升R24原PARTIAL或抹去原版诊断。原资金17项保留其真实历史构建与结果，无相关语义变化时不无差异重复89天全场。完整软件资格及原件索引见 `../docs/maintenance/2026-11-20-ck3-121003-followup.md`；旧结果不自动变为当前全矩阵PASS。
历史维护基线证据见 `../docs/auto-upgrade-buildings-maintenance.md`，三期资金策略与 R0025 证据见 `../docs/auto-upgrade-buildings-phase-3-plan.md`，四期超直辖策略见 `../docs/auto-upgrade-buildings-phase-4-plan.md`。正式版提供简体中文、英文、法文、德文、日文、韩文、波兰文、俄文和西班牙文；Workshop 文案维护在
`../workshop/auto_upgrade_buildings_description.bbcode`。

本维护版保留上游署名和来源，并已获得原 Mod 作者授权进行二次开发与发布。

## 历史迁移记录（2026-10-01，当时状态）

2026-10-01 开发树已迁移到 CK3 `1.20.0.2 (Crozier)`、Steam build `25588574` 的建筑快照，保留原有 605 条升级边，
同步 45 处原版资格条件变化。新版提取、生成、14 项合同／构建测试、静态检查与可复现构建已通过；
新版实机验收尚未执行，descriptor 仍保持原公开兼容声明。完整差异和证据见
[`1.20.0.2 兼容专题`](../docs/ck3-1.20.0.2-auto-upgrade-buildings-compatibility-2026-10-01.md)。

## 生成与校验

`common/scripted_effects/build_scripted_effect.txt`、`common/scripted_triggers/aub_building_triggers.txt`及各自的分片是生成文件，每文件最多10个顶层定义。建筑图谱来自
`../tools/auto_upgrade_buildings_1_21_0_3.json`；旧 `1_19_0_6`、`1_20_0_2` 快照保留为历史政策对照。
刷新 exact 原版定义时先运行提取器、审阅全部图谱／费用／资格差异，再更新独立冻结合同并运行生成器。
普通提取器与生成器不会更新 `auto_upgrade_buildings_data.py` 的政策和资格 SHA-256。当前快照的只读检查与构建命令为：

```text
tools\.venv\Scripts\python.exe tools\extract_auto_upgrade_buildings.py --game-version 1.21.0.3 --output tools/auto_upgrade_buildings_1_21_0_3.json --check
tools\.venv\Scripts\python.exe tools\gen_auto_upgrade_buildings.py --check
tools\.venv\Scripts\python.exe tools\validate_auto_upgrade_buildings_static.py
tools\.venv\Scripts\python.exe tools\test_build_auto_upgrade_buildings_release.py
tools\.venv\Scripts\python.exe tools\build_auto_upgrade_buildings_release.py --check
```

原三项闭场原件：`../docs/maintenance/2026-11-20-ck3-121003-followup.md`关联a180；原GSV/creator/Game正常0、Job0和cleanup已取得，零新SAVE、输入f488保存不变。该场无AUB匹配错误，但原版地图、去DES缺键与继承界面is_diarch／文化／头像诊断完整保留，不宣称原始日志全零。
