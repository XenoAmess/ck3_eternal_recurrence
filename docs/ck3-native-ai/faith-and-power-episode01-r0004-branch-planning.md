# 第一期R0004：B准备后的个人、核心与采用许可

`machine_id: 4-8e1c2f1861`；CK3 1.20.0.4，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。实际编写2026-10-17T11:32:04.393876+00:00；本稿B详情a02截止11:11:33.713711Z，圣物接口可用性截止11:11:34.905000Z；闭场截止11:28:49.082549Z。R4为新PID19004/gen1、玩家15893、date_raw51394920；before native:2/public3/native2，选择后native:3/public4/native3，保存及详情native:4/public5/native4。

[小型规划记录](evidence/faith-and-power-episode01-r0004/branch-planning.json)绑定19份来源回执、与当次native-report的14项结果相等核对及最新详情小投影。原件根为 `C:/workspace/ck3-faith-and-power-20261017/episode01/`。最终native-report SHA为 `d911fa2adbdbc547e3a21bc6072ee4d18c25b6ba5bc527bbb4089eac2d5feeab`，记录其相应steps位置；这里只保留必要小投影，不宣称整包永久保留。本lane没有游戏操作。

## 一次B选择与保存边界

11:08:36.211066–11:08:36.664879Z，一次 `event_instance_id=1/option_number=2` 对应实际native index1，独立后验 `event_instance_advanced/postcondition_verified=true`、active_event=null。piety前后均225000000/100000=2250、日期不变。三个明确准备marker的本场匹配数由 `[0,0,0]` 变 `[0,0,1]`，只新增B分支marker；初始化加虔诚marker未增加。这是明示准备步骤，没有再次注资证据，不计普通Robert成绩。

11:10:30.819601Z实际保存B，50,209,815 B，SHA `1419b3ed54bdf294a81047f62e8bb1e17ebc205b490f632dcb20997d6832bbf6`，已冻结 `scenario/saves/B-maliki-prepared.ck3`；copy收据SHA一致。driver仍 `unconfirmed/save_binding_mismatch`、save_binding_verified=false。保存和冻结不等于完整恢复资格，B冷载尚未完成；下一进程必须重新绑定身份、Rite/Faith、日期、事件及资源。

## 个人与核心不能合成一个信条集合

| 同帧原生输入 | before | B之后 | 规划含义 |
| --- | --- | --- | --- |
| 当前角色Rite / Faith / Faith main Rite | 13 / 50 Sunni / 13 | 15 / 50 Sunni / 13 | 当前Rite改变，Faith及其main Rite未改变；不按界面标题填身份。 |
| `source=character_personal_tenets` | `struggle_submission`；190条personal parameters | 同一个personal tenet；190条列表完全相等 | 个人参数不是当前Rite的核心参数。完整性仅限该接口支持集合；唯一value=true的已支持参数键为`unlock_voluntary_laampdom_faith`。 |
| current Rite核心tenets | legalism、religious_legal_pronouncements、struggle_submission，均status4 | adaptive、legalism、religious_legal_pronouncements，均status4 | 当前核心集合新增adaptive、移除核心struggle_submission；后者仍作为个人tenet保留。 |
| Faith main Rite核心tenets | Rite13的上述三项 | 完全不变 | Faith main Rite不能被当前个人所属Rite15覆盖。 |
| effective tenet state | adaptive=status1/known | adaptive=status4/core；个人struggle_submission仍status4 | `known`不等于`permitted`或`core`；状态registry为unknown0/known1/prohibited2/permitted3/core4。 |
| numeric-special `heresy_threshold` | current Rite调整0 | current Rite调整+5；main调整仍0 | 独立native final getter仍给Faith阈值65，不将current的+5直接加到Faith最终值。 |

personal/core/tenets三个工具前后都实际ok/available/status=observed、read_only=true、advertised=false；没有把schema存在当作实读。文件名`before/after-b-core`实际调用的是 **numeric-special五键接口**，不是完整Rite布尔参数目录。`allow_adopt_any_holy_site`没有由190条个人键或该五键numeric口独立读取；不能把未覆盖键当false。numeric中minimum_fervor仍是unset，raw=-1/value=null；authored_presence_provenance_observed=false，已读零值也不能当成原始定义显式填写零的证明。

原版[第一期静态合同](faith-and-power-episode01-planning.md)已区分actor.rite参数与个人参数；本场把这个分层落到实际存档数据。当前Rite core membership、独立布尔parameter、Faith主礼仪最终数值仍是不同观察，不能互相顶替，也不能宣称B只改变一个权限开关。

## B的当前原版采用许可已经为true

11:10:33.217842Z的a01及11:11:33.713711Z的最新a02实际读到：actor15893、requested/parameter/selected HolySite32一致，selected index14/count21/token361；bypass已读为0，普通条件CanConfirm=true，native_detail_context_verified=true。21仍是当前selector候选数，不是21个合法动作。

R3缺失的正文和报价在本次原生接口已取得：`native_requirements_description_available=true`，完整native Requirements字符串保存在小投影；`native_cost_description_available=true`，结构化费用piety raw100000000/scale100000=1000、其余已投影资源0，`native_affordable=true`。`native_decision_cooldown_observed=true`、adopt决议present=false/active=false，expiry=null；不猜其native counter为日历时间。原生Requirements携带当前Rite15与目标32等scope文本，但这不是单独参数getter或完整逐条件结构树；保留其原字符串，不用中文标题猜权限。

此只读结果的 `action_ready=false` 仍原样保留，与已观察的原版最终许可true分别记账；执行资格依确认专口的新鲜actor/目标/bypass/帧守卫，不能互相覆盖字段。**截至本稿查询上限，没有Confirm，也没有采用。** 1000是当前报价，不是已付款；冷却缺席不是采用后仍缺席。下一步若在owner执行合同中确认一次，须独立查Faith关联/等级、完整实例、库存与其他Faith、钱包/free/冷却及真实收益，再判断达成，未知结果不可重放。

native-report另有nadjaf和baghdad两次 `ck3_query_player_holy_site_relic_context_v1`，实际ok/available=true，本记录只冻结其可用状态，不把它当供奉、认可、Active、受益者或业务效果通过。正常闭场见下节；媒体QA由producer另行结算；R1–R3历史结果保留，不能借给本场。

## 独立正常闭场

R4 `case-output/normal-close-result.json` 为11,515 B，SHA `3414233c7b5fe6da6d91b9af8793a54eae39e2c1e8080db26bcc6063c297411b`。实际正常GUI退出、原HANDLE PID19004/create_time1792234509.150048 exit0，native process_exit0/cleanup_proven、normal_close_qualified=true；原public Popen等待0、keeper原父等待0。`root-screen-release-a01.json` 于2026-10-17T11:28:49.082549Z记录CAS11323、task done/resources[]。原business_pass仍false，完整最终报告没有采用Confirm工具调用。闭场不完成B冷载、不代表采用已付款或完成；R1历史退出RED和R2/R3各自结果保留。

统一存储策略1.0.0下仅保留小型文档、来源pin和规划投影，不复制存档或大wire。记录2027-04-15复核，应用核验后的patch按48小时派生期限复核。
