# R58 法理关系一次静态补定位

官方 `.4 game/common/succession_appointment/_succession_appointment.info:32–41` 的原注释确实区分两个条件：`:37` lower要求候选tier低于目标；`:38` lower_or_equal允许同tier。`:34` 另说明有地统治者降任较低有地title时须是其de-jure liege。后一句是必要条件，不能读成“独立皇帝只要法理在内就必然合法入池”，也不能用realm liege替代de-jure。

本机实际Steam `.4 game/common/landed_titles/05_goryeo.txt`（20,648 B，SHA-256 `c6c1d46941b22f00e0daee33abacd3e3ed3c5bfa85c07d809e0ca38d2ff74f57`）的原始嵌套为：

| 县名 | 源文件法理祖先及行号 |
| --- | --- |
| c_gokju:113 | d_gaeseong:83 → k_goguryeo:60 → e_goryeo:6 |
| c_dangseong:513 | d_gwangju:468 → k_goguryeo:60 → e_goryeo:6 |

所以**这两个county在原始源定义中确属e_goryeo法理链**；本次不能证明operator误选了非玩家法理title。源码嵌套不是当前实机de-jure查询，不排除历史/存档/实机关系变化，更不能据此指定人类31883缺席的真实根因。

现有公开 `ck3_query_title_holder_v1` 的 `title_holder_v1_serializer.cpp:79–90` 仅给 holder_character_id、holder_in_player_realm、holder_immediate_liege_character_id、holder_top_liege_character_id；后两者是人物实际领主，前者是realm归属。此公开返回没有title de-jure祖先字段。`title_holder_contract.py:103–107`也只列上述字段，不能把它们当法理关系证明。本包不新增provider、capability或live query。

对新admin36/未来merit的具体防盲试建议：在既有GUI导航中，先审阅**当前实际头衔的法理层级**及玩家实际持有头衔，再作现有无breakdown完整池资格发现。源码可指导导航候选范围，不能代替当前关系；完整池仍是人类是否自然入池的实际依据。不循环更换同类title并假设realm归属已足够，也不预设查到de-jure关系就一定解决。没有现成真实关系观察时明确保留未知；原deadline、完整池、人类/AI、分数和任命继任判据不变。

仅有限静态源与现有公开字段读取；无活动大报告、实机、ABI复研、MAIN/Git修改、fixture、build、prepare、测试或新预算。
