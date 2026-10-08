# Factory D2 更细诊断：D2a / D2b

本候选只改变 development overlay 生成器，生产71和87/88保护不变。R30真实D2在SetHoF/Title95/cleanup之前，native BEFORE SAVE已经45→40；保存之后40且五政治头衔heir变化。D1/D2四项realm laws完全相同，两边都没有same_faith_succession_law。具体原因仍UNKNOWN。

事件保持原 `.1`～`.6`，只插入 `lyd_factory_diag.20`：

| 原生事件 | scope stage | 边界 |
| --- | ---: | --- |
| lyd_factory_diag.1 | 1 | 原D1 doctrine/授权后，尚未创建新T |
| lyd_factory_diag.20 | 20 | D2a：create_dynamic_title＋两owner markers＋四原属性，无未决transaction |
| lyd_factory_diag.2 | 2 | D2b：create_title_and_vassal_change＋holder＋resolve原子完成 |
| lyd_factory_diag.3～.6 | 3～6 | 原SetHoF、cleanup、Title95、postconditions/close，原样继续 |

原 `.1` 下一步调用d20；`.20` 下一步调用d2；原 `.2` 及其后续路线不变。D2a guard保原actor/faith/rite/serial/nonce/phase身份及授权，要求真实new_title存在、两个owner markers与holder实际不存在。跨事件/SAVE后未持有title能否保留仍UNKNOWN，若实体或scope丢失，保留RED并停止，不补flag、不create重试。

这次唯一操作顺序改变，是将change-container创建从props之前移到props之后；installed1.20.0.4 pam_antipope_effects.txt128–151存在该原版顺序。holder与resolve不能跨事件拆开。完整操作序列经还原这个明确移动后与原厂AST一致；原授权、拒绝、receipt、结果码及postconditions保持。

ROOT导入两个tools源码和本说明，不导入source-validation-overlay生成物。未来实际cleanexport后使用原CLI：

```text
<verified-python> -B -X utf8 <actual-export>/mod_li_yu_dao/tools/build_factory_diagnostic.py --source-root <actual-export> --source-head <actual-full-head> --export-report <actual-report> --export-report-sha256 <actual-sha256> --output <fresh-overlay-dir>/mod
<verified-python> -B -X utf8 <actual-export>/mod_li_yu_dao/tools/validate_factory_diagnostic.py --source-root <actual-export> --overlay <fresh-overlay-dir>/mod --output <fresh-static-result.json>
```

实际manifest仍位于output.parent/output.name.MANIFEST.json，files六行shape不变。六runtime文件均UTF-8 BOM，legacy package/mount接口不变；只stage_keys现在七项，stage_labels明确20=D2a、2=D2b。controller source-only JSON给出了事件/scope映射，PID/session/revision/optionindex/HEAD/native/metadata全部待ROOT实际绑定，不hardcode rendered option位置。

保存及比较薄作者由coldlane负责，新增D2a marker20并保全部owner-marker候选T AST，不能只看actor已持有Title；本包不改reader或原87/88合同。先读完整ordered native cache，再各自保存唯一immutable checkpoint及saved完整actor/政治Title；不要把保存前后差异直接归因上一effect。

仅使用合法历史R29第三轮signed-B3作为诊断冷载seed。必须在当前实机正常闭场后新ROOT分配run/新加载输入，不热替换overlay、不使用已经政治变化的D2/B4存档。历史B3 PASS不授新cold资格，D6局部结果不等于87/88通过。

一次必要源码验证44项actual0，另直接确认原D1guard、D3～D6事件/effect和原三个身份/title/result trigger AST全等。使用原Clausewitz parser和validate_static helpers；没有执行native构建、SDK、游戏或存档正文读取。未持有T生命周期/引擎执行和业务验收仍NULL，整体NOT_GREEN。
