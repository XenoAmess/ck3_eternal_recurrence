# QOL：R71 阴性通过、R72 正例槽位准备与 Source18

记录时间：2026-10-11 01:01 CST。范围仅原十项非天朝二期迁移，正式交付仍 7/10；没有发布 QOL 1.1.1。

## 已实际取得的阴性信用

Source18 / Main `577082f3497a5bb1d94b35eff834423c82c5b77a` / 新正式候选27文件运行 R71/a172。原35步全部 PASS、12个24小时、同一实际 actor34422、17个 required各1、forbidden0；自然接受1/拒绝0、pending清除、Catholic/Roman、Acts精确piety、Mendicant不加piety、两项SP前后及实际doctrine absence均成立，fixture/product error条目为空。run0、once verify0、case/contract qualified。normaltrue、retained OS0、strictnativezero、原allocator61779本人poll0、keeper0、CAS8490 done/resources[]、三closure齐全，16:25:31.347304Z真CLOSED。

本场只签原 `pam_negative`，POST的business_pass/product_release_pass=false保留；同步合法度raw delta仍null。原[双入口卡](handover/2026-10-06-ck3-upgrade-handoff-artifacts/qol-pam-two-entry-card.md)明确该差值为GAP，wrapper的legitimacy_level不能证明+50点。R70旧scope错误及RED不追认。[R71薄回执](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_negative--a172/ROOT-FIELD-RETURN-R71-01.json)：13824B / `307cfa469600ef3c2086a8445c5dfce62c7d8000a8b8c42b2a2f03769a72352a`；POST4766B / `41887afbf869584f8abf8e3d2f398ceb2e87a0556e37f3637c315dbf2802a1c9`。

## 正例原观察及最小夹具修订

R72/a173原正39在startup AND失败，35步均NOT_RUN、0自然日，run2/verify2。原obs02在remove_all后及紧邻双setter guard前均见DLC=true、free==1、free>=2=false、owned_any=false；guard前piety==4=true，两项setter后的观察阶段缺失。这证明准备时缺一个槽，不能进一步猜piety缓存或隐藏modifier的具体原因。named Song D0资格成立，但native数字actor ID未取得，保持null。

16:42:20.897598Z原失败全闭，retained OS0、failureproof/lifecycletrue、allocator61435本人poll0、keeper0、CAS8498 done/resources[]、三closure齐；normalfalse/strictnativezero false原样保留。[R72薄回执](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_positive--a173/ROOT-FIELD-RETURN-R72-01.json)：11356B / `3735208d0fd7be78d813a692a8010c38c3bee4b81d4e835c9770b2314f846a89`；POST3673B / `7dd297c33decdc16285fd8ea2c38b953bb0d83200b1ea685bbdce2a739bda65b`。

本次三文件修订只在原piety准备之后、DLC已开且free==1时，给当前夹具actor一次 `zqp_controlled_personal_slot_modifier`，仅含 `personal_tenet_slot_add=1`、years1覆盖原12日。它属于一次性profile的controlled-positive准备，不声称自然宋帝容量改变。仍执行原free>=2 guard、双setter、最终AND、SP0→10→13及全部奖励断言；负例、原计划、obs02、生产树与生成器未改。stock `00_defines.txt:902–905`、`00_basic_modifiers.txt:144–163`及 `pam_effects.txt:516–523`给出槽位key/character modifier语法；zealous还改SF倍率，因此未使用。

外置candidate实际一次生产contract校验、已有focused2项及现有Kaishek syntax-only两个文件parsed2/errors0均通过，逆除新增块逐字节还原原fixture；这不授引擎生效。candidate73808 allocated bytes、216.54秒、children0，128KiB/600s内真closed。[补丁](C:/workspace/ck3-upgrade-20261010/pam-positive-controlled-slot-candidate-01/PAM72-CONTROLLED-SLOT-FIX01.patch)：2588B / `3faee52878b39b3661f3ac91aecab231dd1350f9972190ea73c23fb35a25e0a3`。后继必须新unused public prepare及原35步/12日实机，不能复用正39状态或改旧失败。

## 共享运行时及入口实际范围

Source18已实际冻结并由Root公共xqol/pam_negative plan0选定：6904个不可变硬链接及两个独立Python文件，冻结阶段约5秒，独立逻辑3084601B。runtime16802B / `90a24de0f9587b3ffb79e8739c151926aa8503611a92e4d8feee01d712d02398`；manifest58771B / `e27ee846eddbe4f991fc5995a4a6185885f056ce575f481238a1551cf8094639`；index2957504B / `ffd63a5e73a9be4b0c125e8c56cad2b45c6d8f77c32f30241d7c1596da276c8f`，根为 `C:/workspace/ck3-upgrade-20261010/shared-source18-ready-01/`。

DLL9087488B / `b4b19bcdb27076e0958d9e27a75da239798b459d017ee9e19720752ac86101be`来自21对象增量及552父对象，14 focused已真实通过；native provenance index明确partial父/回退，不声称source_refs完整自动解析。R71已实测本条PAM运行路径；新tier诊断及Character/query仍未获实机信用。canonical `tools/steam_offline_nonce_capture.py`已在R71/R72实际采集并由唯一现场operator审阅新双nonce及Steam离线；Root只审回执，未冒称人工看图。公共launcher协议不变。

`577082f3`[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38065507644) attempt1已SUCCESS，16:20:40Z真实读回66success/20skipped/0failure；没有下载日志或外推单测细分。之后同步的其他owner8提交由fetch/rebase保留，338文件，禁止merge/forcepush。行政40/merit41仍READY；后继精确依赖需按新Main核对。

## 发布边界

玩家Notes补充已合入actor条件修复，当前仍DRAFT_NOT_PUBLISHED：4641B / 3353字符 / 31行 / `ad48a09a2a9155237afe453460c731624902512636fcba9e0172ee02f6e6fd85`。正式tag、上传、匿名exact Notes/tags、真实Steam下载文件一致及CK3加载、永久changelog push均待实际完成。缓存按[永久规则](workshop-cache-acceptance.md)只核字节和加载。
