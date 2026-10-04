# CK3 1.20.0.3 合军补给角色权重观测

2026-10-05：补齐既有 `ArmyStrength` 的只读数据，尚待新冷载实机验收。它服务于[合军补给继承研究](army-meeting-merge-supply-inheritance-12003.md)，不执行合军，也不证明某次合军已发生。

只在 EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6` 绑定两个原生叶函数：`24E0160(CArmy, int64_out, flags=0)` 和 `24E02A0(CArmy, int64_out)`。两者只写输出及局部栈，各自返回原输出指针；前者排除 ObDG 标签，后者只取该标签，两类互斥。标签不外推为尚未证明的玩家部队分类。

查询行增加可选 `merge_supply_destination_weight_raw`，scale 为 100000。它是该行军队作为目的军时的角色权重 D。被吸收军的 S 权重复用该军已经原生 `2A95740(flags=0)` 与完整团数组交叉核验的 `current_soldiers × 100000`。两者必须来自实际合军前同一暂停帧，不可把目的军的 D 等同于所有部队人数，或用另一支军队的人数作 D 的上界。

生产读取保留既有 FullID、CUnit/CArmy backlink、团数组和原生总人数校验。新增叶绑定缺失、返回指针不符、负值或总权重大于本军当前人数时，只把新权重留为未知；合法零值保留。用先检查 A，再检查 `B ≤ 本军人数权重 − A` 的方式避免相加溢出。历史 .2 绑定不赋值。原生访问异常仍由外层 mailbox 拒绝整次查询，不承诺异常时返回普通 Strength。

离线验证使用实际生产 reader/serializer 的九个合军权重夹具，以及 Python normalizer 的四个拒绝用例；旧补给和补员夹具也通过。Root 集成后的现有 Strength 合同十项测试通过。它们使用合成内存和本地函数桩，没有调用游戏函数。`open_kaishek` 对原生 ABI 和内存读取无可覆盖语义，本项预验为 not-applicable。

冻结过程资产位于 `C:/ck3-war-episode04-research-20261004-a01/merge-supply-weight-source-a01/`；采用补丁 `merge-destination-weight-a02.patch` SHA-256 `63cf6daa22ff4d56983ea357c393886b3cdf1093f0e5c845058c9482fdce982a`。下一项是新正式 DLL 冷载后读取双方 D/S、库存、上限、统帅及全团身份，再对实际合军前后计算，不能以离线夹具闭合实机公式。
