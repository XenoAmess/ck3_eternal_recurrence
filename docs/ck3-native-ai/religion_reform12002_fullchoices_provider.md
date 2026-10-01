# CK3 1.20.0.2 全实际草案 Doctrine 只读 provider

2026-10-01，宗教已获用户授权。输入为已冻结 [完整 native/stock 树](religion_reform12002_fullchoices.md)，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。当前为 **static-ready**，没有本包 paused/live artifact。

`ReadCurrentDraftFullDoctrineChoices12002(DraftChoiceBindings,epoch,DraftFullDoctrineChoices&)` 读取真正可见的当前 Rite creation window、实际 selected slots790/stride48、每个 slot 的 groupB08→source array140。它以既存 D0 TopScope 对 source definition 求值，不依赖当前 popup 曾打开或当前 category/cache是哪一组，不读取全局 doctrine registry，不构造 item/scope、不调用 ShowWindow 或选择动作。

每个 source 保留 source index/稳定 doctrine key、是否该slot当前所选、是否因其他已选definition排除、native shown/raw CanPick/knowledge/prophet 与最终 `final_selectable`。先排除重复，随后 shown，随后 can_pick，随后 KnowsDoctrine OR prophet；同一slot自己的当前 definition 不因已选集合包含自身而排除。raw native_can_pick 包含 shown AND definitionE8 条件，与已证明的原生 getter相同。

`null` 仅表示 native short-circuit没有求值该分支，最终布尔仍有完整答案：duplicate排除行的 shown/raw/knowledge未调用；hidden或raw blocked行的knowledge未调用；known=true行的prophet未调用。这不是未知最终gate。数据库只读已初始化 prophet cache，并复用已有绑定，不触发 lazy getter。

serializer 是 `SerializeCurrentDraftFullDoctrineChoices12002`；schema `ck3_12002_current_draft_full_doctrine_choices_v1`、scope `actual_current_draft_selected_slot_group_sources`。顶层 `doctrine_gates_complete=true` 仅表示观察到实际当前草案且全部实际slot source最终选择门已求出；它不代表费用充足、名称有效、整个创建命令可执行或实际完成创建。空source slot与零slot草案都保留 `draft_observed=true`，缺/隐藏窗口为 `draft_observed=false` 且 complete=false。输出没有 native 指针。

唯一必要的新 `/O2 /W4 /WX` actual C++ reader→serializer fixture 是 `fullchoices/fixture-attempt-01/result.json`，**5检查、5 actual JSON GREEN**。主例包含四个 actual slot、三个实际group（其中一组零source）、十五个source：同组两slot使用不同 definition，互相重复排除；当前所选仍保留；hidden/rawblocked/knowledgeblocked/nativeknown通过分别求出，未物化popup也可完整读取。prophet子例只改变knowledge分支，final true由5增至9而排除与原生false保持；零source、零slot与隐藏窗口分别输出。所有 JSON 都来自实际C++ serializer，Python仅解析其结果；原生 callbacks 验证真正currentwindowD0、实际actor、source definition参数及short-circuit调用次数，不手编结果 JSON。

本包新增 header/source/test runner 与本文；先前三份树源及旧 R7/model/mailbox不改。精确 source/dependency/proof SHA 与日／周报告字段见 `Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\fullchoices\delivery-result.json`。中央 owner 后续接独立默认OFF只读 mailbox/Python query，再以暂停实机确认真实草案各slot最终eligibility；本 worker 不操作CK3/Git/shared接线。Tenet仍由独立 sources owner处理。
