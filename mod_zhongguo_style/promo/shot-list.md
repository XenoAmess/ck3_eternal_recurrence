# 361 宣传片：一次集中实录镜头清单

本清单替代早期的 14 段“每个互联网热词各拍一个子系统”的分镜要求。旧的原始录像、验收静帧、导入副本、失败 take 和原清单所指向的目录都保留，不移动、不删除；只是正式成片不再把尚未实现的独立 OKR、PIP、HC 或项目管理器拍出来。

正式片的事实核心是：逐级考核、KPI 与强制分布、校准、免费京察、冻结考核榜、3.25 的国库/金币/贤能/俸禄四重处分、申诉、PIP/末位，以及 **361 个逐项政策卡 + 持久选择状态 + 17 类后果 profile + 14 本组织账**。

## 已保留的夹具实机静帧

导入 run：`zga_20260829_061314_ea5f04ad`。导入副本与哈希仍在
`promo/imported/fixture-live-zga-20260829-061314-ea5f04ad/`。它们是最终 GREEN 验收夹具画面，不是干净宣传录屏：可作为事实插帧，不能假装成完整正常玩法闭环。

| 已有画面 | 诚实用途 | 不得借此声称 |
|---|---|---|
| 历史 23 人考核榜 `7/16/0` | 仅作初始化缺陷的 RED 过程证据 | 正式 361 分布、发布截图或宣传片素材 |
| 校准会 | 直接公示、抬 3.75 边界、压 3.25 边界三个真实选项 | 命名人物、理由档案、受益者档案 |
| 京察弹窗/规划器 | 半强制、免费、拒办入口 | 300 日逾期的连续录屏 |
| 上司 3.25 告身 | 上司、KPI、名次、国库/金币/贤能/俸禄四重后果与申诉入口 | 画面直接显示贤能 -60 或退款前后数值 |

## 自动集中实录的实际覆盖

`tools/run_zhongguo_acceptance.py --promo-capture` 在真实 gameplay HUD 出现后才启动一个连续 FFmpeg 录制，
同一 run 同时保存屏幕、timeline mark、验收报告、evidence index 与静帧。正式 manifest 只认下面这些实际产物：

| 实际 mark / 静帧 | 正式章节 | 可以声称 | 不能借此声称 |
|---|---|---|---|
| `calibration_event_visible` | 04 | 真实校准会三选项 | 命名人物档案、任意点名器 |
| `managed_scoreboard_visible` → `policy_cockpit_visible` | 03 | 当前候选严格 `7/14/2` 榜、唯一名次、真实 3.25 边界与驾驶舱 | 单轮画面外推多年绩效循环 |
| `jingcha_mandate_visible` → `free_jingcha_planner_visible` | 06、14 | 半强制弹窗与免费规划器 | 300 日逾期连续录像 |
| `superior_assigned_325_visible` | 08、12、14 | 上司 3.25 告身、国库/金币/贤能/俸禄四重后果、申诉入口 | 画面直接展示退款前后或一年 PIP |
| `received_scoreboard_with_325_visible` | 07、14 | 本人所属考核单元、KPI/位次/3.25 | 独立三年长期闭环 |
| `12_policy_001_event.png` | 02 | 实际 #001 KPI 分项证据单政策卡 | 独立 OKR 目标管理器 |
| `12_policy_007_event.png` | 05 | 实际 #007 背靠背 360 邀评政策卡 | 举荐/攻讦互动已单独录屏 |
| `12_policy_020_event.png` | 10 | 实际 #020 晋升包政策卡 | 晋升通道 modifier 已单独录屏 |
| `12_policy_022_event.png` | 10b | 实际 #022 软 HC / 编制预算政策卡 | 招聘、岗位空缺或增编模拟器 |
| `12_policy_026_event.png` | 11 | 实际 #026 贡献/可见度政策卡 | 项目 ID、双账仲裁 UI |
| `12_policy_361_event.png` | 13 | 实际 #361 绩效宪章政策卡 | 361 张都逐张录过 |

实际捕获编号固定为 **#001/#007/#020/#022/#026/#361**；旧计划中的 **#002/#015/#035 没有被本次
runner 捕获，不得继续写进正式 manifest 或旁白角标**。六张图共同证明编号、A/B/C 卡面与题材跨度；361/361、
17 profiles、14 ledgers 的覆盖结论由同一 GREEN 报告绑定，不把六张样卡冒充 361 张逐张真人操作。

## 没有独立实录的章节

下列内容不阻止生成零占位正式候选，但必须显示 `GENERATED EVIDENCE/BOUNDARY`，不能标 `CLEAN CAPTURE`、
`FIXTURE-LIVE` 或 `captured`：

- 公爵—伯爵—男爵同框的层级镜头；报告只绑定公爵及以上考核入口合同。
- 举荐/攻讦互动本身；#007 只是一张真实政策卡。
- 一年 PIP 与连续两次 3.25 的末位处置过程；当前连续录像只到首次 3.25。
- 申诉改判的退款前后连续画面；可展示真实申诉入口，并明确说精确退款由同 run 报告验证。

## 录制动作与口径

1. 原始录像必须在 gameplay HUD 后启动；timeline 须写 `exclude_ck3_loading=true`，正式 clip 的起点不得早于 `recording_started_after_gameplay_hud`。
2. 正式画面中的玩家与受评者必须是书签/世界里的真实历史角色；素材 notes 记录 bookmark、character id 与画面角色，不用测试临时角色冒充。
3. 连续镜头只描述真实链：校准、发榜、驾驶舱、京察、告身和本人榜。政策卡可以作旁支蒙太奇，但不能拼成不存在的目标—项目—互评流水线。
4. 最终时间线逐段排除“361制实机验收”、`ZGA`、验收规划器、演示触发器等 fixture/test-only 决议与控件；含污染的验收片段只能留作过程证据，不得裁字、打码或遮罩后入片。
5. 制度驾驶舱只展示已配置的组织账；不把账本字段称为独立 HC/项目/人才系统。
6. 每张政策卡静帧必须来自同一 GREEN run，露出真实编号、题目与 A/B/C；正式 manifest 对原图、报告、timeline 和原始 MKV 全部锁 bytes/SHA-256。
7. 失败 take、随机事件遮挡、OCR 与 recorder 日志都保留；只有根报告、cell 报告和 evidence index 同时 GREEN 的 run 才能投影正式 manifest。

## 目录、保留与 notes

每次集中录制都新建目录。正式 manifest 与 provenance 也保存在这个外部 run 下，不回写仓库内作者版 manifest：

```text
Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\<run-name>\
├─ report.json
├─ evidence-index.json
├─ cell\
│  ├─ promo\
│  │  ├─ capture-timeline.json
│  │  └─ raw\                         # 原始长录像与 FFmpeg 日志；永不覆盖
│  ├─ 10_superior_result.png
│  └─ 12_policy_<001...361>_event.png # 六张实际政策卡无损静帧
└─ release\                            # 外部 manifest、provenance、成片、QA 与 sidecar
```

每个 `notes/CAP-*.json` 至少记录：CK3 版本、mod commit、游戏日期、review serial、角色 id、原始文件 SHA-256、select 的起止时间、是否排除 loading、与哪个报告绑定、已知瑕疵。原始素材、旧 take 与失败 attempt 始终保留。

## 入片门槛

- 视觉素材有原始录像、timeline marks、hash 与报告；任何 clip 不含 CK3 loading。
- 旁白声称的数值、角色与后果在画面或绑定的同一 run 报告中可核验。
- 对政策卡只声称：独立编号、A/B/C、持久选择、共享 profile/账本与 KPI 回流；不声称独立 HC、项目、OKR 或 PIP 子系统。
- 核心连续片段不跨 run 拼成假闭环；同一原始 MKV 的 marks 明确写进 provenance。
- 每个入片实机段都记录真实历史角色 provenance，并通过 test-only UI 污染扫描与人工抽帧复核；验收 GREEN 不自动等于宣传画面 GREEN。
- 正式 build 前 placeholder 必须全部消失：有实录的变成带证据的 `video_clip`/`still`，没有独立实录的变成明确生成边界卡；然后才运行 `--stage release`。
