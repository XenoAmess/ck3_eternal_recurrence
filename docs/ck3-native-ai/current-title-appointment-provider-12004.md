# CK3 1.20.0.4 当前任命窗口只读 provider

2026-10-10：本页记录共同 bridge 的实现与离线证据。当前状态是 **实现已构建，尚未取得新 provider 实机资格，也没有据此通过 QOL UI25 或 government 任命业务**。R39 从 `d_zhexi` 点“查看继承”实际打开 `k_liangzhe` 的旧 GAP 原样保留。

唯一公开入口是 `ck3_query_current_title_appointment_v1(expected_revision, requested_title_id=None, candidate_offset=0, candidate_limit=32, breakdown_character_id=None)`，capability 为 `game.command.query-current-title-appointment-v1`。它复用既有 `query-ingame-ui-window-v1` 主线程 mailbox，以 `window_kind=title_appointment` 读取当前已显示窗口；不打开或切换窗口，不任命人物，不修改游戏状态。指定 breakdown 人物时只调用原生 GUI 分数 getter 刷新该窗口自己的显示缓存。

目前仅支持 Steam CK3 1.20.0.4，EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。不同 EXE 拒绝复用这些 ABI，历史证据不外推。

## 请求头衔与实际窗口头衔

原版 `game/gui/window_title.gui:2486` 将 `Title.GetID` 交给 `ToggleGameViewData('title_appointment', ...)`。真实处理函数 RVA `171C790..171C8C8` 先验证完整 title ID，再从 Title+128 解析并验证完整 holder character ID。holder+1C0 非空时从 group+1E0/1EC 取第一完整 title ID；否则走 holder+1D0 的 group+68/74。`171C8AE` 读第一 ID，`171C8B0` 写入 window+C8。因此传入 d 级头衔并不保证打开 d 级任命窗。

返回值分别保留 `requested_title_id`、`requested_holder_character_id`、`native_group_branch`、`group_first_title_id`、`resolved_title_id`、`current_window_title_id`、`requested_resolves_to_current`、实际/解析 title key 和 `effective_succession_law_key`。不把原始分支 1C0/1D0 猜成未经证明的业务名称。有效继承法来自窗口实际 law getter `171B8D0` 所读 window+BC0；title-own-laws 的 own_count=0 不能代表没有有效继承法。

验收 adapter 必须从本场独立 typed title-map 导航取得请求 key/full ID，再核对 requested holder、group-first、resolved 与 current-window 的一致关系以及有效 law。它修正的是旧 harness 固定 d 窗口的错误预期，不能手改 label 或把旧 d GAP 改为 PASS。

## 完整候选池、资格与分数

原版 `game/gui/window_title_appointment.gui:43-62` 明确把这份列表定义为能够被任命到该头衔的候选人。原生 population `171BCD0..171BF9F` 调用 `273A390` 构造 source pool，并逐个把完整 character ID 写入 base list。source pool 并不是“所有人再交给 UI 判资格”：

- `273A741..273A790` 对每个实际 character 指针调用 `273AA40`；返回 true 时 swap-remove，最终减小 pool count。只有通过当前任命规则的指针留下。
- `273AA40` 的剔除路径含现任 holder 的完整 ID 比较、年龄、死亡字段、性别与任命规则字段等；其他子函数保留原始 RVA 与分支，不给缺少符号证据的检查杜撰业务名字。
- population 随后逐个将保留指针变为 base+18 的 item（full ID 在 item+8、index 在 +C）。实际 vtable sort `171BFA0` 和通用 `DA8A30` 只修改显示 list+48/count+54，不过滤或重排 base+18。完整 base 与 source pool 逐 full ID join 后才能把其成员解释为引擎的 eligible 候选集合。
- `candidate_pool_member` 只是原始事实；adapter 的 `eligible=true` 需要上面的精确 EXE、原生剔除定义和完整 source/base join 三者。`score_present` 仅表示 cache rank>0，绝不是资格判定。

完整 pool、base list 与 score cache 读取前后独立核对，分数按 full ID join。AI 来自既有引擎 getter `2BAA6F0` 对本场 human-player roster 的完整 ID 查找；不会把“不是当前玩家”一律算成 AI。分数固定比例为 100000；原百万惩罚在 wire 上的精确差值是 **100000000000**。原生 breakdown getter `171CD50` 与 score cache total 必须精确一致。

原始有限函数证据保存于 `C:/workspace/ck3-upgrade-20261010/qol-candidate-gui-source-01/native-provider-01/` 的 `rva-273A390.json`、`rva-273AA40-273BC60-273B780.json`、`rva-2C61AB0.json` 与 `candidate-list-order-14.json`；完整 ABI 冻结为同目录上层 `abi-freeze12/APPOINTMENT-EXACT-ABI-FREEZE-12.json`，SHA-256 `ed71d2fe91e0e427c5eb11611b755818ba12ef6dbb41adac13578d7858671378`。

## 公共验收接线

`tools/ck3_mod_acceptance_appointment.py` 负责完整逐页 join；`CaseClient.query_appointment_pool` 使用原 once-only control queue，逐页保存实际回执，并登记本客户端生成的不可变 proof pin。至少核对同 PID/保留 process identity、connection generation、pipe、paused actor、date、native revision、实际 title/law、count 与 pool token。分页必须从 0 连续覆盖全池，不能只读取前 32/64 人。请求不导航，也不补造缺失 ID。

仅 `ui_tail`、`administrative_appointments`、`meritocratic_appointments` 三 case 声明该 read-only opt-in。UI controller 增加 typed action `appointment-full-pool`；government checkpoint 增加逐序只读 request/response 文件，仍由既有 client/host 执行，不创建第二 host。每次需 `requested_title_id`、`requested_title_key`、`expected_law`、本场已完成的 `navigation_step_id`，可另给 `breakdown_character_id`。政府场每 slot 分别保存 `appointment_pool_off/on/restored` 三 pin。

typed query 是数据和资格证据，不是业务 signoff。原 direct original PNG review、完整候选/tooltip review、独立人类自然在池、百万 off/on/off、开关恢复、eligible AI、实际 successor/appointment 和 UI25 原顺序全部保留。两 government 场的原计划、天数和每项业务断言不变，七个非 GUI case 不增加该工具要求。

## 已完成的离线验证与共同构建边界

原 reader 的 11 项 native fixture、8 项 Python contract/真实 driver 方法 AST mock 已通过；测试源码和 synthetic wire 随本实现保存，不能把 synthetic wire 当实机人物。公共接线一批 12 项定向 checks 通过，覆盖跨场分页、重复/遗漏候选、伪造资格/AI、d 请求到 k 实际窗、精确百万分数、只读 checkpoint、三 case opt-in 和 UI25 保持。后续 canonical main 的两处受影响 TU 只做额外 `/WX /utf-8 /Zs`，没有重跑原 provider 测试或重链相同 DLL。

唯一未来共同 DLL 为 `C:/workspace/ck3-upgrade-20261010/qa12/frozen11/xar_ck3_bridge.dll`，9072128 字节，SHA-256 `fd1f33ed63c452ba2fef3313a490db53fd8bfcfc567909c94b4966e1f4f7c5aa`。它从完整 Native08 后继构建源窄增量产生，继承 title-key/truce 能力；572 个生产 TU 中实际重编 20 个、复用 552 个，唯一 link exit0。完整构建收据为 `qa12/actual11/result.json`，SHA-256 `0b4b5e1f6207b1aea572ec170ad919062272aeb6c8ba83481dc2555d7ba63003`。共同 Python Source12 另继承 PAM 与失败生命周期收尾，manifest 分别 pin Python source 和 native build input。

canonical main 合回使用函数级窄补丁，保留其后新增的其他 G2 能力；这不声称 main 整棵代码就是上述 DLL 的构建输入。正式实机仍使用精确冻结的单一 shared runtime，先取得新 provider 资格，再继续原未完成业务。
