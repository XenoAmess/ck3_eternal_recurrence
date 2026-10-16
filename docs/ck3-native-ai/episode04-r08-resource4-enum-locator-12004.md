# R08 resource4：具名字符串与有界 locator 库存

machine_id `desktop-3fevhd2-1c74096080`；来源封存于2026-10-16T19:43:28Z，source `6bf30840af44231653f8e914389b59c8798f2cc1`。CK3 1.20.0.4/build25734779、EXE SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 沿用既有资格身份并核前后stat，本包不重hash完整EXE。历史本机观察不能作为其他机器的安装、容量或实机资格。

原 [SOURCE.final](evidence/episode04-r08-resource4-enum-locator-12004/SOURCE.final-a01.json) 与同目录 exact ZIP、账本、修正、stdlib [verify_portable_final.py](evidence/episode04-r08-resource4-enum-locator-12004/verify_portable_final.py) 已按精确 bytes 保全。无源机器路径依赖：从仓库根用 `python -I -B -O docs/ck3-native-ai/evidence/episode04-r08-resource4-enum-locator-12004/verify_portable_final.py`，默认从自身目录读取。其余 locator/producer 脚本仅保存已执行过程，不应作为新机器自动采集命令运行。

本次只得到 `GetCurrency` 独立字符串 RVA44DB128 与 `barter_goods` 独立字符串450BB80；rdata的46FC9F8有一个指向后者的QWORD，其相邻0x3E2D是原始token观察，不能视为selector4。旧非重叠RIP matcher的0有已证明覆盖缺陷，原失败与synthetic修正不删；后续独立opcode修正版测试693550个8B/8D+mod00/rm101起点，对具名目标仍报告0。data的8571392B有界QWORD检索也报告两目标0。只描述各已授权collector的有限范围，不推广成全局无引用或无实现。

总读取如实为sections **185103872B**、metadata **608B**、**9 reads**，未读新函数body、未重hash整EXE。完整段没有入库；便携验证只重算保留的小context、指针/token、修正反例、原件hash及累计账本，**不复演完整段穷尽检索**。原131445B首封超373B、repack与Root后来144KiB范围修订均保留，不以压缩掩盖首次RED。

这给[resource4应用专题](episode04-r08-rate-resource4-application-12004.md)提供可移机定位库存，不把字符串邻近、槽顺序或临近token解释成权威资源名。selector4/context+4A0的业务义、玩家钱包同槽映射、military c/d producer、payer、实际paid和cadence仍unknown。与[copy incoming有限定位](episode04-r08-copy-incoming-12004.md)相互独立；研究6/14、业务4/11、合格动态0/11、ABC0/3均不增加。
