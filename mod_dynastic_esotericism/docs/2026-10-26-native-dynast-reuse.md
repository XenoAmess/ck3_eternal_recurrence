# 真实创建／改革时复用原宗族

日期：2026-10-26；machine_id：`desktop-3fevhd2-1c74096080`。本记录说明当前源码合同与静态验证，不表示新分支已实机通过。R0017 失败原件继续保留，不追认为本修复通过。

用户要求：真实创建／改革操作前已经是 Dynast 的操作者，直接复用其原 Dynasty 与实际 House，不生成 Dynasty、House 或 NPC；按新 Rite 改名，两者各自原 CoA 保留，其他旁支与未入教原成员身份不变。原宗族若已有另一 Rite 绑定，则把绑定转给新 Rite，旧 Rite 实际改为 None 并解除本产品来源。普通采用预置 Rite 不属于创建／改革，不获得此复用政策。

## 先保身份，再分支

R0017 表明：真实创建者进入礼仪创建回调时，另一信徒已经能通过普通同步完成建族。仅在创建完成时重绑已生成的 NPC 宗族不能满足新要求。因此全部普通首建入口共用 `des_ensure_own_rite_binding_effect`，并检查全局 `des_ordinary_binding_rites` 中的实际 Rite 对象。

- 初始世界只为已经宗族化的现存 Rite 登记普通即时首建资格，保留繁育／白绮普通首次采用路径。初始 None Rite 不预先登记。
- 未登记、未绑定 Rite 的普通调用只保存首次实际请求者、日期并排一个 Rite scope 的次日回调，不建族、不迁族。维护、出生和普通 `on_rite_updated` 同样经过此入口。
- 真实 `on_rite_created` 在任何产品同步前，以原生 Character Root 固定 actor、原 Dynasty、House、当时 `is_dynast`。真实 `on_rite_edited` 以合法原生 editor 对应的 `head_of_rite` 固定同一组来源；不要求此立即回调的教义已经更改。
- 真实编辑只有带 `consume_rite_edit_token` 的 `on_rite_updated` 才消费该来源，并先于通用同步决定首次绑定。若次日普通回调遇到 native pending，只等待原生更新，不抢先创建。
- 次日仍无 native pending 时，普通路径获得登记并使用原新建规则；原生已先绑定时只同步，不重抢 head。`create_dynamic_rite` 的低层测试属于这一普通路径，不冒充真实 UI。

初始 None 对象也保留屏障，使编辑时即使某个角色变化通知先于立即编辑回调，也不会提前迁族；不依赖尚未闭合的 C++ 内部通知顺序。普通关闭但仍保留绑定的 Rite 不重新取得首次政策，重开继续原绑定。

## 持久读回合同

| 数据 | 含义 |
| --- | --- |
| Rite `des_binding_mode=flag:native_dynast_reuse` | 可信原生创建／编辑来源选择复用 |
| Rite `des_binding_mode=flag:new_dynasty` | 原生非 Dynast 或普通采用选择新建 |
| Rite `des_native_source_actor/dynasty/house` | 产品迁族前从该次真实原生操作者固定的对象 |
| Rite `des_native_source_was_dynast=yes` | 当时确实为 Dynast；缺失不表示有可复用来源 |
| Rite `des_native_head_claim_kind/date/actor` | 真实 created／edited 来源及日期 |
| Rite `des_native_head_claim_pending/attempted/succeeded` | 来源等待、一次消费、最终两个真实 head 已读回的结果 |
| Rite `des_native_head_claim_dynasty/house` | 成功后的实际绑定对象 |
| Rite `des_deferred_binding_requester/date/queued` | 未知 Rite 的首次普通请求者、日期与待处理状态，不是 native 来源 |
| Rite `des_ordinary_binding_ready` | 仅供读回；真正通用首建资格以全局对象 list 为准 |
| Character `des_adopted_bound_rite` | 此人物实际采用并归入过该绑定 Rite，不由同 Dynasty 推断 |

真实来源仅从原生回调进入，fixture 不得直接调用 capture／claim／completion helper 来制造。复用 helper 只由一次 completion 调用，确认 actor 仍是原 Dynasty 的真实 Dynast、实际原 House 的 head，且原 House 属于该 Dynasty；不调用任何建族、造人、迁 House、设 head 或改 CoA effect。原来源失效只保存 fault，不回落到普通新建以掩盖状态漂移。新建路径仍保留原单 House finalizer 及真实中间创始者存活规则。

## 转移与背离

转移前要求旧 Rite／Dynasty／House 的剩余双向关系真实一致。旧 Rite 先 `remove_rite_doctrine=des_doctrine_dynastic`、`add_rite_doctrine=des_doctrine_none`，快照其产品 apostate 索引并调用共享精确清理，再解除旧 backlink、绑定、mode、原生来源、普通登记和排队状态，保留 transferred-to／date 审计。新 Rite 绑定原 Dynasty／原 actor House 后应用名称。源不存在 identity-applied 缓存；新绑定的 identity 每次明确应用，复用分支整块跳过 CoA，原 Dynasty／House 原本不同的 CoA 也分别保持。

普通关闭流程不清这些绑定对象。只有明确转移才清旧状态，后续维护见旧 Rite 为 None 且无绑定，不会重建或抢回。旧 Rite 后来若经另一真实合法操作重新开启，必须重新固定该次来源，不继承上一次 claim 或普通准入。

背离要求曾实际采用当前绑定 Rite。复用前从未加入新 Rite 的原成员不会因同 Dynasty 被标背离；先前已经明确存储的本产品 `des_apostate_rite` 可作为旧档兼容证据。现有犯罪／意见清理仍只移除 `des_apostasy_opinion`、产品双向索引、`des_apostate` 和对应产品来源，不调用原版通用赦免或删除独立罪行。

## 原版来源与验收边界

本机游戏 build `25734779`，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。来源根 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game`，只读离线检查：

- `common/on_action/religion_on_actions.txt`（59,475 B，SHA-256 `ef9367ddf5f89c912b895743f8b72441e88af3a5b03a5c1a9eddea0e5681ee2d`）：418 起 created Root 为创建者；442 明确 `create_dynamic_rite` 跳过此回调；725 起 updated 为 Rite scope、界面更新有 token；833 起 edited 为立即界面提交，updated 延后。
- `events/religion_events/faith_creation_events.txt`（33,619 B，SHA-256 `419c04b9ca889e96e572b894ec346ae6119af2fd6eb9be4833d6659edfba923e`）：1244 明确只有玩家 rite-creation command 发出 `on_rite_created`。普通 stock factory 没有真实 UI 来源。
- `common/scripted_triggers/00_religious_triggers.txt`（88,549 B，SHA-256 `e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2`）：3062–3065 无条件要求合法 editor 等于 `rite.head_of_rite`；附加 puppeteer 条件没有取消该条件。
- `common/character_interactions/pam_interactions.txt`（724,542 B，SHA-256 `2db73b0da8572e218f1a677a91ff4281a890ade115e6dc40e696ecb59c0b1049`）：14119–14138 执行式 Rite scope `add_rite_doctrine`；`common/on_action/game_start.txt`（218,249 B，SHA-256 `f2f5ce78a03cfbdba0f5a68fc466f8bac89126cdd4843545b4ad6d468ed238b8`）：2276–2283 执行式 Rite scope `remove_rite_doctrine`。

`HeadClaimContractTest` 读取完整实际脚本 AST，检查全部生产调用者、来源消费顺序、unknown barrier、复用禁止新对象和迁族、旧 Rite 实际 None、CoA 条件支配及既有单 House guard，并用真实源突变证明会拒绝回归。它不执行 CK3 引擎。下一场真实 UI 创建、此前未绑定 None→Dynastic 改革、跨 Rite 转移，仍须各自操作前原件与 +1／+2 全员 Native、独立 Save 比较原 D/H/两 CoA、两个实际 head、旁支、未入教原成员与独立罪行来源。低层 factory headcells 只验证普通新建，不授予 UI reuse 通过。

编辑来源的精确边界：原版资格要求提交前操作者是 head，原版立即 edited 回调也以当前 head 消费 once；现阶段未闭合 C++ 全部虚调用，不能仅凭此推定同时改变 head／governance 的任意编辑在通知时仍为同一人。None→Dynastic 且 head 保持的必要真实用例应比较操作前 Native actor／head 与回调持久 actor；不同则判失败，不用新 head 冒充实际 editor。离线来源报告位于 `C:/ck3-dynastic-esotericism-20261024/resume-builder-a20/native-creator-source-a01/REPORT.md` 及同目录 `source-readback.actual.json`。
