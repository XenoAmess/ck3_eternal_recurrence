# R08：当前费率 getter 与真实 c/d producer 的最小下一步

当前没有已持证据把 settlement 的 c=context28 或 d=context30 命名为实际已付军费。公开 current2C13F60 与 allraised2C152B0 是替代月费率；gross/full expenses 的查询和软件NET也没有向四raw赋值。ExpenseContextCharacter返回Character，不等同于解引用的Character1C0对象。

formalcompletion提供了既有完整846B **2C13F60..2C142AE** asm，已直接复用，无新EXE读。公开query第三arg=null，2C13FA5跳2C141CF，实际2C141D7调用 **28C43A0(Character,localout80)**，把返回十槽累加到callerout；然后2C14238调用 **2C142B0(localout80,Character,null)**，再累加十槽，2C1428E返回callerout。getter本体不读Character1C0或四raw。

下一最小具名来源是 **28C43A0**（第一实际vectorproducer），同时保留2C142B0为第二必要component。formalcompletion已核其具名库存没有这两个callee的完整body。下一步须Root另授两个有界source scope；本lane没有执行新读取。随后沿真实Character/context/资源槽选择和写入查证，不猜未知callee。若只证读某field，也仍不等于producer、刷新或已支付归因。无需再读2C13F60或寻找旧失效FAMILYMAP。

28A63E0的新copy只推进a/b到context18/20，尚未命名；28A6B50纯整数比例分配已闭，不是producer。28F7840中的currentmaintenance分支发生在settlement之后，不能倒归当前positiveNET。暂不新增hook或扩大观察字段，maintenance_attribution保持unclosed。

机器desktop-3fevhd2-1c74096080；时间、exact sourceSHA与逐字段ABI见同目录source-index.json。没有EXE新读、游戏/SDK/桌面/构建或主树写入。原截止2026-10-16T07:45:01.597Z不延长。
