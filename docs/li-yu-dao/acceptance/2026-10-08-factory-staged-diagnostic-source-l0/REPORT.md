# Factory 分阶段诊断源码 L0

R0029 的正式提交后，五个政治头衔的继承名单和角色完整继承缓存发生变化。现有两端点只能确认 native 与 saved 均为45→40，不能定位具体操作。本次新增独立 development overlay builder，在原操作之间设置六个显式事件边界，每页只有一个经真实上下文重核的推进选项。

可复用源码为 [builder](../../../../mod_li_yu_dao/tools/build_factory_diagnostic.py)、[结构校验器](../../../../mod_li_yu_dao/tools/validate_factory_diagnostic.py)；调用和运行合同见[说明](../../factory-development-stage-diagnostic.md)。生成 overlay 不入库、不进入正式 staging。原 factory 与 commit 生产文件未改。

已有实际 clean487 export 上生成的候选经过33项结构检查，实际退出0：[原结果](STATIC-CHECK-002.actual.json)、[原stdio回执](validate-candidate002.RESULT.actual.json)。检查使用现有 Clausewitz parser，确认完整成功操作逆投影、原授权、拒绝 continuation、authority receipt、postconditions和show_result的AST精确保留；D2的create/holder/resolve保持原子。首次括号提取失败及原候选manifest保留，不追改为通过。

ROOT按精确bytes/SHA导入可复用源码及本报告原证据，[导入回执](ROOT-IMPORT.actual.json)记录12个证据文件。原生成目录、日志与scope来源继续外置永久保留；未重跑既有检查、未读存档正文。候选历史source487不是未来新HEAD的native编译资格。

仅实际签署B3可以作为新诊断种子。新冷载及跨事件/SAVE的scope保持性仍待实机；若D0状态已改变或阶段scope缺失，保存实际RED并拒绝推进。原87/88保护不放宽，局部分步不能代替正式B4/B5、newTitle冷载、C3或I4。整体NOT_GREEN。
