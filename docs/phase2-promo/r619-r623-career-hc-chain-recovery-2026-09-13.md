# R619–R623 Career HC 连贯链恢复（2026-09-13）

## 验收状态

- T0 P1 保持 `9/9 GREEN`。
- T0 P2 保持 `0/8`。本次连续 take 完成前四个 clean spans，进入 HC/Workforce span 5 后在真实产品事件 `zg361ch.950` 上保留 RED；失败 take 不拆分计数。
- 最终宣传片硬锁继续生效；本轮没有制作、更新、发布或预热最终成片。
- RED 没有被吞掉或降级。R623 的事件现场、暂停门、时间线、报告和原始 MKV 均保留。

## 连续 take 与清理

artifact 根：

`Z:\ck3_mod_rewrite\_runtime\p2-capture-r619-plus-a73e50e-20260913`

| 轮次 | PID | 用途与处置 |
|---|---:|---|
| R619 | `111088` | frontend warmup；frontend ready 后终止 |
| R620 | `202516` | gameplay spans 1–2；clean end 后终止 |
| R621 | `176188` | manager governance span 3；clean end 后终止 |
| R622 | `194932` | promotion compensation span 4；clean end 后终止 |
| R623 | `62232` | HC/Workforce source；`zg361ch.950` RED 后终止 |

连续 FFmpeg PID `25384` 已停止。cleanup 为 GREEN，gameplay PID lineage 为
`[202516, 176188, 194932, 62232]`，CK3 与 FFmpeg 最终存活数均为零，protected storage 为 `UNCHANGED`。
报告耗时 `754.625 s`，原始 MKV 为 `355,773,513` bytes。

前四段的录像时间锚点为：span 1 `9.720–30.021 s`、span 2 `37.429–55.913 s`、span 3
`189.293–209.048 s`、span 4 `329.895–349.445 s`；录制于 `486.488 s` 停止。这些片段只作为失败 take 的调查证据，
不计入 P2 的八段交付。

| 文件 | SHA-256 |
|---|---|
| `capture-plan.json` | `8BBDD7DB577BEE460775C46256626D2A4D64F55B6D39312D071405AD26A3146F` |
| `capture/report.json` | `0B4AA93C9D183689D3ABAE5CC399910489E8ED37B0DE82E9F24FBD7516858844` |
| HC native event wait gate | `6EC7F4525E6A4D8486A007A67B7BF1151C5D4264DE46D17B54FE8D839ACA2B0` |
| identity 07 pause gate | `9B6B1DF16C14B434D1432F4D684EF9652CAB2B8CFB6772E604F9B43FAB01FFA4` |
| `capture-timeline.json` | `AF64F56F3A5AEB6BEAA2F419E438452FB3109977F09B68CF718D1D0D6DE0717C` |
| raw MKV | `8946915057154A5E049DC275B074E7FFA75F7006DC45E395AD20C28C38D87424` |

## RED 根因

R623 依次识别并安全处理：

1. `ep3_story_cycle_admin_eunuch.8030`
2. `zg361p2c.2`
3. `zg361.40`
4. `epidemic_events.5007`
5. `zg361.1`
6. `zg361.5`

随后第七个现场为 `zg361ch.950`：event instance `628`、date raw `53375664`、root/player `32904`、
共 `104` 个 saved scopes、native options `0/1/2/3`。必需作用域均存在且类型正确：

- `zg361_ch_d_event_owner = character:32904`
- `zg361_ch_d_event_subject = character:31450`，与 owner 不同
- `zg361_ch_d_event_cycle = value`
- `zg361_ch_d_event_case = value`

现有 `CAREER_HC_TIMELINE_CONTRACTS` 对该现场完成 `17/17` 检查，选择 authored `1` / native `0`。
事件来源是生成文件 `mod_zhongguo_style/events/zg361_career_hc_runtime_events.txt`，生成器为
`mod_zhongguo_style/tools/gen_361_career_hc_runtime.py`，调用点在
`common/scripted_effects/zg361_career_hc_003_d_lifecycle_effects.txt`。三者 SHA-256 分别为：

- event file：`5AA9A5B29DE6F2CFC628773D5C51389616241F6E5957C22F3FC307CB25F81FEC`
- generator：`494570E44C140FDDAF18C933386BCD2B05A828015E7A44054CBAABF2E8C9E04C`
- caller：`6AF5C7156609782770449399D99A24AC0323AB7C25EB2315275ED3317FF23097`

这是 P2 runner 的受审产品路由缺口，不是 Career HC 产品语义缺陷。A/B/C 路线会批量展示 22 个低风险机制，D 路线会进入完整
44 项逐项链；项目规范分别形成 29 张与 51 张可见卡。已有严格合同覆盖整个 51-key 连贯链，但 capture runner 先前只允许较小的
产品事件白名单，因此在第一个未注册 key 上按设计停止。

## 最小修复与验证

提交 `bfc19480e2844174fc1322761433a25632f6d663` 复用现有 `CAREER_HC_TIMELINE_CONTRACTS`，并将其完整 key 集加入
`PHASE2_CHOREOGRAPHY_PRODUCT_EVENT_KEYS`。只有这个命名注册表内且通过对应严格合同的产品事件可以继续；注册表外事件仍为 RED，
通用单选自动清理仍然禁用。

聚焦测试新增 `.950` 现场并断言整个 Career HC 合同集合已纳入 P2 路由。普通与 `-O` 模式的
`test_zhongguo_phase2_reviewed_vanilla_wait.py` 均为 `8/8 GREEN`，`py_compile` 与 `git diff --check` 通过。
没有再次扩大为逐事件重启矩阵或完整 51 卡长跑。

R623 的 identity 07 暂停门走的是普通 `submitted` 路径。它证明 R618 旧失败位置没有再次阻断，但没有实机重现
`already_paused` 分支；该幂等修复的直接运行证据仍是 R618 原生 ACK，辅以聚焦测试。

## 接口、通用资产与下一步

本包没有 MCP schema/version、DLL、游戏文件、启动配置、加载顺序或公共接口变化，故不需要修改 open_kaishek。
Career HC 严格合同是已有通用产品资产，本次只复用它，没有新增 MCP 通用资产。

下一次 CK3 启动从新轮次 R624 warmup 开始，只执行一次新的连续八段 P2 source capture。若再次出现新的真实 RED，仍在首个阻点
停止并做最小审查，不把单个事件扩成永久长跑。
