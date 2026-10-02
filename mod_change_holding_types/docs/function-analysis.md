# 地产类型转换：功能分析

日期：2026-10-03。证据层次：公开页面＋上游冻结源码＋已安装原版脚本；未启动 CK3。

## 页面承诺

[上游公开页面](https://steamcommunity.com/sharedfiles/filedetails/?id=3337428403) 显示标题 `Change the holding types`，作者白绮，最后更新日期 2025-11-13。它提供城堡、城市、神殿、部落、游牧聚落及神殿城塞之间的转换，并提示转换可能损失不兼容建筑。页面评论于 2026-10-01 报告新版游戏不可用；这只是故障线索，没有给出日志和重现场景，不能直接判定根因。

## 已安装原版的相关合同

研究安装：`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`，父任务冻结 CK3 `1.20.0.3`、Steam build `25652598`，EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

本分析使用的五份原版来源文件大小和 SHA-256 已保存在 [vanilla-source-2026-10-03.json](vanilla-source-2026-10-03.json)。这里只存来源摘要，不把整个原版文件复制进 mod。

`game/common/holdings/00_holdings.txt` 当前定义七种地产：

| 定义 ID | 含义 | 主建筑 |
| --- | --- | --- |
| `castle_holding` | 城堡 | `castle_01` |
| `city_holding` | 城市 | `city_01` |
| `church_holding` | 神殿 | `temple_01` |
| `tribal_holding` | 部落 | `tribe_01` |
| `nomad_holding` | 游牧聚落 | `nomadic_camp_01` |
| `herder_holding` | 牧民聚落 | `herder_camp_01` |
| `temple_citadel_holding` | 神殿城塞 | `temple_citadel_01` |

原始源码已核定只有六个目标类型，不新增 `herder_holding` 目标；它作为已有地产可以进入既有转换路径。

原版 `common/scripted_effects/00_holding_effects.txt` 及多个政府／决议 effect 在 province scope 调用 `set_holding_type`。原版部分部落／游牧转化还调用 `holding_pre_feudalize_effect`，包含县修正、文化关系、丝绸之路状态等附加语义。因此“修改一个地产类型 ID”不能被当作已经完成全部原版政府、继承或经济迁移。

`common/holdings/_holdings.info` 说明 `primary_building`、可建建筑列表、继承政府约束等定义字段。当前游牧／牧民聚落携带 `no_buildings`、`no_levies` 与 `county_fertility` 参数。转换后正常的政府兼容性、继承与建筑变化属于关键实机观察对象。

## 上游实际功能与维护差异

上游通过六个 `ch_convert_holding_to_<type>_decision` 决议，使用 `create_holy_order` 控制器选一个男爵领，再在 `scope:barony.title_province` 调用 `set_holding_type`。每个决议消耗个人金币 `main_building_tier_1_cost`；城堡需要文化的 `innovation_motte`，城市／神殿需要 `innovation_city_planning`。原版成人、可行动与和平门槛保留。

上游 target predicates 要求男爵领 holder 是人物、无在建、当前类型不是目标；没有独立事件、on_action、存档 flag 或变量。本版保留六个 public decision IDs、六个 public `ch_barony_is_valid_for_*_trigger` 和决议组 `ch`。请替换原作使用，不能同时加载两份相同 public IDs 的产品。

确定的 CK3 1.20 API 差异：widget 的 `barony_valid` 变为 `title_valid`；GUI 数据模型 `DecisionViewWidgetCreateHolyOrder` 变为 `DecisionViewWidgetSelectBarony`；`HasCurrentCapital`、`GetCurrentCapital`、`HasValidBaronies` 分别变为 `HasCurrentTitle`、`GetCurrentTitle`、`HasValidTitles`。控制器 ID `create_holy_order` 和输出 `scope:barony` 仍保留。当前原版 holy-order decision 与 GUI 是直接比较来源，SHA 见 L0 报告。

维护同时把决议总体 eligibility 的人物引用从 controller 局部 `scope:ruler` 改为原版决议根 `root`；widget 内仍用 `scope:ruler`。移除三处在 `is_valid` 裸层的 `subject=root.culture`（原版仅在自定义说明内使用此字段），不改变革新条件。

当前六个生产 effect 放在 `cht_conversion_effects.txt`，共同调用相应保留 trigger；决议和 effect 都有玩家闸门。共享 `cht_barony_is_convertible_trigger` 明确要求 `tier_barony`、已有 holding、人物直接持有、未出租和无在建，避免 county／duchy 的层级遍历项或空地被当成转换目标。所有实际转换仍走原版 `set_holding_type`，不编造建筑保留机制。

## 维护版验收要求

保持上游核心用途，以真正的玩家可见转换为完成标准。每次执行只影响文案明确指定的玩家地产，AI 没有入口；费用、建筑损失与政府兼容性必须可理解且可验证。禁止在没有原版与实机依据时承诺“建筑全部保留”或“所有政府下功能一致”。
