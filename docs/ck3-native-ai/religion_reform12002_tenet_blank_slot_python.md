# R9：消费合法的 native default Tenet 空槽

2026-10-01，root 的 R8 暂停态 Tenet 查询出现实际 RED。唯一 root VM_READ 确认当前第三槽 `slot_index=2` 指向游戏 native default definition（global `0x5D1F6C0`）；这是合法的未选槽。原生 provider 原先尝试复制它的字符串 key 而失败。R9 provider 将这一 exact default 识别为正常空槽，保持槽位 ID，并把 `selected_tenet_key` 输出为 JSON null；普通 definition 的 key 和全源最终 gate 保持原样。实机根因证据保存在 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-reform/tenet-sources-r9-blank-slot/actual-selected-slots.json`。

## 最小 Python 依赖修复

生产 leaf [player_religion_draft_tenet_choices_private_transport.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/player_religion_draft_tenet_choices_private_transport.py) 的 slot 校验原先强制字符串。直接调用原生产 normalizer 消费 R9 实际 provider DTO，确定性得到 `native final Tenet slot schema is malformed`。原 leaf SHA-256 `969e51dc3c7bcc428a67564ab707e4f149d5baf654a246b4c88bf8246cf383a2`，失败复现保存在 `tenet-blank-slot-python-r9/baseline.json`，没有编造 envelope 或访问 CK3。

唯一生产变化是把 `selected_tenet_key` 类型放宽为 `str | None`。null 表示原生已证明的合法 default 槽，不替换成空字符串、不丢弃该槽、不增加虚假候选。normalizer 仍深拷贝整个实际 DTO；slot index、实际 source/filter、MainRite 与 actor Faith raw status、知识、trigger 和最终 gate 都保持原值。新 leaf SHA-256 `83d876d581a70268e7992316b7b395567eb1c214c3d2887165097156a3ab6b59`。只放宽选中槽 key，来源定义的 `tenet_key` 仍为真实字符串。

## 必要验证与证据边界

唯一[新增消费单例](../../ck3_autonomous_player/tests/unit/test_ck3_12002_player_religion_draft_tenet_blank_slot_wire.py) **1 passed in 0.26s**。输入为 R9 provider `/O2 /W4 /WX` 新单例实际输出，原字节 SHA-256 `8bee8bc19398cf9006a68e5538492c779c7be26fcd45f2a408ade7c66899df84`；复制到 [native-default-third-slot.json](../../ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_player_religion_draft_tenet_choices/native-default-third-slot.json)，[独立 provenance](../../ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_player_religion_draft_tenet_choices/native-default-third-slot-provenance.json) 记录原生 candidate、实际原包、provider receipt 和 root 暂停态证据的精确 SHA。

新单例调用生产 normalizer，逐字段比较完整 DTO，覆盖 `[0,1,2]` 三槽及第三槽 null、全部八条真实来源、最终 true/false 和 MainRite status 0／actor Faith status 2 的独立值。输入是实际 provider DTO，**不是完整 command_result**；本次不声称重新完成 transport/cache/SDK 验证，不补写 wrapper metadata。R8 的完整 packet／官方 SDK 证据和旧 6 文件 manifest 保留为历史；原 unit、SDK、原生矩阵均未重复运行。

结果位于 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-reform/tenet-blank-slot-python-r9/result.json`。独立 R9 5 文件清单包含仅一处 leaf 修复、新 unit、新知识文档和原包／provenance，并提供日周报告字段。状态为 **static-ready R9 consumer correction**；实际默认槽身份已由 root 暂停态确认，但更改后的整体 R9 query 仍须 root 联编并重新查询。没有新的 Python 实机或宗教行动 credit；没有改动资源报价 leaf、共享 Driver／MCP／CLI 或任何战争路径。
