# v20261019：真实T0的离线领土与宗族基线

**本场1066.9.15基线已独立取得：玩家realm为10县，个人直接地理county为2县，宗族持有8县；创始house和dynasty均为174。** 这些值全部从新场次受保护T0保存重新读取，不继承旧局174或旧县集。新钱包为**257金**，不能沿用旧局239金。当前结果只补T0输入，不是新局终局分、完整月史或S30，也不增加G2信用。

机器为`machine_id: xenoamess-full-tower-eb9d2c1186`；实际唯一SAVE流式读取区间为`2026-10-19T03:14:57.081491+00:00`—`03:15:11.221756+00:00`，结果时间`03:15:11.299965+00:00`。原生SAVE发生于Root保存回执的`03:05:37.203431`—`03:05:39.439035 UTC`；不要混淆游戏保存、保护副本与离线读取时间。新场次Robert31254、episode `native-31254-6271ac8cd441`，日期raw53144328。

小型[精确摘要](evidence/g2-m1-robert-v20261019-T0-summary.json)为12,442 B、SHA-256 `bb5cb5593e6a4e1156dfbacf2d94aa13f10eb41735a5f215dbaad2eb2d89ada8`；[来源与闭场](evidence/g2-m1-robert-v20261019-T0-sourcepins.json)保留decoder、静态定义、锁内身份与失败边界。完整262,848 B派生投影留在已准入外置子目录，未复制SAVE或完整melt进仓库。

## 三种领土口径

| 当前T0事实 | 值 | 口径 |
| --- | ---: | --- |
| 玩家realm县 | 10 | 沿保存中的实际de-facto title链归属于Robert的county，包含所有层级附庸；按县ID去重 |
| 个人直接地理county | 2 | `2231 c_apulia`、`2262 c_rossano`，county实际holder为Robert且有地理映射 |
| 个人直接地理holding | 4 | 明确barony holder与实际省份记录；不是原生GetDomainSize的替代值 |
| 固定创始宗族县 | 8 | 实际县holder→house→dynasty/家族分支关系；同县只计一次 |
| Native domain大小/上限 | unknown | 此离线包没有同T0的GetDomainSize/GetDomainLimit原生观测，不能用2县或4holding冒充 |

因此“直接持有2县”和“统治10县”可以同时为真。不能把本T0个人county清单误写成已经发生8县失地。具体10县与每县holder、发展、控制、已完工地产和结构品质已在摘要逐项保存：Messina、Foggia、Apulia、Bari、Lecce、Camarda、Reggio Calabria、Cosenza、Rossano、Lanciano。

## 已闭合品质与仍未知的部分

| 输入 | 本T0观测 |
| --- | --- |
| `Q_realm` | 15.975品质县当量 |
| `K_dynasty` | 12.675品质县当量 |
| `control_average` | 1.0；10县控制均100，以q加权 |
| `legacy_ranks` / 已建立家族分支 | 0 / 0 |
| 钱包 | 257金；SAVE中的个人金币字段，不是净资产 |
| `rebel_share` | unknown；本保存未给可消费的`landed_data.wars`明确列表，未把缺列表当作无战争 |
| E/M/H的费用、承诺、质量军力及合法继承 | 仍unknown；不拿保存缓存income/power或主头衔successor补值 |

每县q沿既定v1公式使用实际发展与已完工holding；当前控制满值，相关已完工省份记录没有occupant，原有适配器因此给确定`Q_realm`。没有修改公式、权重或开局分母。当前摘要没有给确定治理U或总分；`rebel_share`缺口不能被满控制掩盖。

可把此包作为当前campaign_id的**离线T0锚补充证据**。原普通月度anchor中house/dynasty为null是当时真实观测边界，不应悄悄覆盖历史文件或在继承时重建分母；本包没有改运行anchor、SDK、COW或任何月份文件。运行owner可通过同campaign/T0/SAVE身份关联这份补证，不需要重开游戏或重复扫描SAVE。

## 一次读取、静态适配失败与闭场

使用已有Rakaly0.8.19，先新鲜核EXE SHA `e154af990aaed2c2f44284946772188c9749ad3f6b641b41f6c23456a6f1633d`；来源是此前带machine_id的decoder receipt及官方ZIP，不下载、不安装。实际复用`campaign_score_save_reader.py::melt_projection`和原评分函数；Rakaly只向stdout输出，内存保紧凑标量，SAVE只流读一次。后续两次`project_metrics`均复用同一内存map，第二次只补本T0自身的固定锚和境外资产上限分母，没有二次读保存。

首次runner在静态定义阶段因原`landed_title_map`继承SAVE的256 root-name帽退出1，耗时0.3533077秒；**该次尚未调用decoder，SAVE扫描0**。外置runner随后沿相同lexer和county/barony/province规则提取静态映射，略去无用途的static root-name收集，保留128层深度、8MiB单文件帽和映射冲突拒绝；生产SAVE parser及冻结SDK未改。失败小记录保留，未把它算作第二次SAVE扫描。后继实际流式读取退出0，未知token0、锁内前后卷/文件ID/大小/mtime完全一致。保存SHA沿Root真实SAVE和保护副本回执复用，**未再做整份保存SHA扫描**。

输入是68936116 B的已保护独立副本，SHA `381e832bb3122b1c544d5bcd505eb86b4d40456a4d37969bcf208714d0aa88f4`；未读活Driver、未访问后续可变checkpoint。Root实际无mod回执绑定Game214568/出生134368503807325674及environment `dbcb5ea688435677d945cef9fc9c73c31d01d229ec060c3a951e53701bf33b57`；本包仅读取当时回执与指定原版landed_titles小定义，不操作现场或宣称新的部署/实时资格。

外置根`D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/m1-t0-projection01`累计293,165 B，低于storage child硬4MiB，已由storage实际读核CLOSE01：producer_closed=true、未来未消费输出0、allocated未知为null。0重型预留增量、0删除、0Native/RPC、0游戏推进；derived在2026-10-21T03:10:04.107622Z复核，仓库小记录180日复核，不自动续SAVE或父预算保护。本包没有重跑旧M1/cadence矩阵，只核新产物JSON与格式；M1历史complete、G2仍6/8。
