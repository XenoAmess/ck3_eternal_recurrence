# 《超人强》正常游玩实机宣传图

2026-10-04，生产战役取材P0002 / R0016，执行UUID `db297ed6-297c-4a92-aafd-e6b5ae7f168b`，实际PID9808。普通战役来自首发R0013之后的原版旧档，只加载22文件production；没有测试夹具、debug_mode、控制台事件、人工经验/属性写入。运行机制与首发1.0.0相同。本页保存取材及图片事实，工坊上传结果另见正式展示修订发布报告。

玩家罗贝尔31254正常选成年廷臣阿梅利娜32535，赠礼55金币后通过实际菜单发起勾引；独立存档正证type=seduce，初始界面95%成功率、12个月。正常推进和选择原版事件后，1070-03-19（date_raw53175072）出现真实 `seduce_outcome.2020`、instance20，root31254、target32535。[原生事件上下文](native-sex-event-context.json)与[身份](identity.json)保留，画面为“厕室之横／计谋成功”。

[实际原生存档](native-sex-checkpoint.json) SHA `a9843d89aba28643818fd37babf993ffc10233985e11930516f221bf34ad7ff2`，独立melt SHA `7c15dcc77a1fc5c12c070a446c2d3e45757a1241c79935fad041a195e2b91d41`。[两个角色原始字段](actual-sex-characters.json)显示双方经验identity100000、integer_exact1，新增经验特质，无sxad属性modifier；基础数组保持罗贝尔4/9/6/6/6/10、阿梅利娜4/5/7/6/2/3。本次双方事前经验0→1，平手不转移；这些图不声称本轮发生属性吸取。

随后正常右键阿梅利娜→“查看性经验”，真实 `sxad.1`、instance21，root31254、`sxad_view_subject`32535。[原生查看上下文](native-experience-view-context.json)与截图显示累计1次，实际当前属性2/3/12/12/2/0，六项净修正均0，保留人物及姓名。正常查看，无夹具触发。

两份原PNG和精确最终JPEG保存在[工坊实机素材](../../../workshop/superman_qiang_media/v2/)。事件裁切[170,194,854,574]→684×380，记录裁切[236,235,787,532]→551×297；JPEG95、optimized progressive、4:4:4，均严格小于1MiB。仅裁切无关地图并编码，不缩放、不改字或游戏内容、不用AI编辑。root直接审阅完整原PNG与两份最终JPEG，[来源/审图记录](../../../workshop/superman_qiang_media/v2/root-review.json)。可用 `tools/compose_superman_qiang_gameplay_media.py --check` 逐字节重建，参数见两个provenance。

实机GUI比例实际0.5。正常设置尝试中Esc仅ACK，新的画面仍地图，未取得菜单改变正证；保留该次操作，停止调整，不宣称0.65生效。采用已实读的原图尺寸及显式裁切。

P0001误选谋杀，30%成功率被误记为勾引进度，P0002真实 `murder_outcome_reworked.0013` 确认失败；[追加勘误](prior-capture-correction.json)绑定原报告和新的独立事件证据。旧报告/素材均保留，P0001图不用于宣传。P0002完成真实勾引后停止新取材场景，最终清理与screen释放事实在发布报告补齐。

[生产manifest](production.manifest.json)及[原始来源索引](artifact-index.json)绑定各份存档、原生回执和图片。此为正常玩法中计数、查看与宣传取材证据，不扩充多人、其他游戏版本、战争、继承或完整自动游玩能力结论。首发机制矩阵和边界另见[既有验收](../acceptance-1.0.0-20261004.md)。
