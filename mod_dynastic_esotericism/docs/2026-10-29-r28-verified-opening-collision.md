# R0028：前四阶段通过与开窗记录碰撞

- `machine_id: desktop-3fevhd2-1c74096080`
- 观察区间：2026-10-28 14:08–16:29 UTC（本地跨至 2026-10-29）。
- Source：`066fdf0ea1b9502f21eaeac90ebfa5ddc1c6e907`；CK3 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
- 场次：`desktop-3fevhd2-1c74096080--dynastic-esotericism--R0028`。
- 实际根：`C:/ck3-dynastic-esotericism-20261024/resume-product-a20`；下文 `LIVE` 为其 `runtime-a20/retest-066f-a01/runs/<场次>`，`Admin` 为其 `core-a30-administration`。

## 已取得的实机结果

控制器实际接受前四个阶段，完整 Core、产品发布资格及 0.2 更新仍未通过。

1. 创建/编辑 GUI 的宗族化组实际可见，默认 None、两项已知可选、取消后资源及身份不变；原生最终价 3705 虔诚，单次确认创建 Rite152。保存的 `native_dynast_reuse` 成功分支复用玩家31254、D174/H174，没有走产品新创始 NPC 后备分支。纯 D0 的四名新增议会成员与产品创始人分别分析，未声称全局零新增 NPC。
2. D0 的50名及 D1/D2 的63名原生完整礼仪成员均逐一与独立 Save 对上；未改信继承人65843仍 Rite6/H174。三个旧家族的归属、旁支完整 AST 及 CoA1783完整设计保持；H174/D174仅有预期名称及绑定变化。Stock factory 的 Rite153/154 于 H0 创建，H1 才发生接纳回调，H2 即回调次日完成绑定；deferredDate 等于实际回调日期而非创建日。最终 D/H 领袖为 A65857、C65859，旧 A 家族由 B65858接任。NPC65861仍活着且非最终领袖；不把它混称为 Rite154 的创始人65859，也不把两个 Rite 的空 head 槽当 D/H 领袖。
3. Root/peer→target 各唯一产品好感修正 −100，outsider 无污染。实际囚犯65840由31254羁押；执行及放逐 mask4 只读预览可用，没有提交处罚。执行交互的 declared-options dispatch 仍不具备资格。
4. 跨信仰后 target 为 Faith14/Rite6/H174，产品修正完整 AST、起始日及期限不刷新。首次悔罪后 target 返回 Rite152/H174，三个方向产品修正消失，成员绑定保留，独立囚犯对照不变。这不能替代第五阶段独立原版犯罪保留测试。

前四阶段的 `*-accepted.json` 均在 `LIVE/case-output/`；成员及刑罚分析在 `LIVE/operator-evidence/retrospective-members-readonly-a01/`、`head-cells-readonly-a01/`、`phase3-4-save-readonly-a01/`。创建和编辑的完整实机原图为 `storefront/raw-png/07-r28-phase1-dynastic-editor-proof.png` 与 `08-r28-phase1-dynastic-edit-proof.png`。

## 第五阶段的真实失败

`des_acceptance_extended_start_decision` 已单次确认。随后 `r28-second-rite-available-a01` 的 Open 在 SDK 创建 claim 时失败：`Decisions opener already claimed for this episode; no action retry`。第二礼仪决议的确认未提交。

旧成功 Open 与这次调用处于同一暂停帧 public revision52/native51。旧 Native 回执实际为 `before_visible=true`、`dispatch_invoked=false`，并已有独立 `verified_visible` 证据；SDK 却把这个成功观察占成同 revision 的开窗身份。此处是已验证 claim 键碰撞，失败调用没有新 Native dispatch。没有新鲜 Hidden 证据，不能描述为已证实的关闭后重开，更不能把 UNKNOWN 改为可重放。

修复须落共享 SDK，区分当前只读可见观察与实际开窗 ACK；军事开窗复用的 Native ACK normalizer 保持原义。真正再次开窗须依严格旧成功、完整新鲜 Hidden 及有父关系的确定性新 claim。全部消费者、持久化和跨进程回归同步；冻结的 R0028 Source/claims 不热改。

## 资源闭合及后续边界

实际保留 OS handle 读得 CK3 退出0，Native Job最终0；public run原始 wait 为2，失败如实保留，不能改成验收成功。keeper/allocator 原始 wait 均0，SCREEN 经精确 CAS 释放。`normal_close_qualified=false`，这里只证明失败场次资源已闭合。

汇总：`Admin/R28-FAILED-OPEN-RESOURCE-CLOSURE-a01.actual.json`，3751 B，SHA-256 `acb64a2c8297219a5f198e4dd21b56b7b5cfe34fd2fdf4f3b7c802b8977779d2`。最新独立保全 Save `r28-repent-return.ck3` 在已完成的 extended_start 之前，不能追认为该输入的后态。

后续须完成共享开窗修复与完整 CI、新 Source/SDK 闭包和实机复验，再完成生命周期、冷载、旧档 bootstrap、两个教廷及原生付费/继承/恢复全部业务。仍更新同一 Workshop `3826991345`；当前未发布 0.2。全程没有 UAC，不延长任何既有 HOLD，也不重置存储计数或已计回收。
