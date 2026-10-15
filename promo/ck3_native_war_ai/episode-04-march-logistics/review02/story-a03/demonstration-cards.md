# Review02 story-a03：讲解与演示卡设计

以下9张是未生成媒体的制作指令，沿原六章对应段插入。每张只解释所列source；不出现虚构的当前游戏日期/Army数字，不代替缺失动态过程。示意整数全程标“假设算例”。

## D01 0→0仍可能走完更新

对应段：C03-10。共用source IDs：`24E4CF0 / 24E3410`。

1. 库存0，变化率为负（假设）
2. 执行本次ADD→结果负数→floor0
3. 成功返回→计算更新后供给预算→可能进入writer

画面限定：只画源码分支，不假造某日真实AL=true；没有拿stock delta0代actual soldier delta。

缺拍/缺实证：Robert自然stock0→0与same-parent supply writer positive physical。

## D02 0与9.99999同一档，10在边界另一侧

对应段：C03-11。共用source IDs：`24E4F80`。

1. loaded levels [60,10,0] / base [0,0,5000]（假设当次已加载该表）
2. 0→integer0 / 9.99999→integer9：同state2
3. 10→integer10：state1；将领/fleet等仍另算

画面限定：单位为绝对库存，非库存/cap百分比；5%只为该表base，不是每团最终扣率。

缺拍/缺实证：实际loaded表及自然严格低阈值positive。

## D03 分开预算：9+1与一次6%的11不同

对应段：C03-02 / C03-03 / C03-04。共用source IDs：`24E3410 / 24E32C0`。

1. 假设共同原始人数199、供给5%、围城1%、raid0
2. 供给预算9；围城预算1；两个整数合计10
3. 若错误地先合6%：11；真实后续分配还按变化后的current执行
4. 围城单笔归因需该笔真实siege>0/raid=0、parent与positive physical，不用本卡代填

画面限定：普通非负无溢出输入；预算不是physical debit；不把合计10画成Robert已死10人。

缺拍/缺实证：新预算leaf的真实新生产/自然记录与独立physical。

## D04 县剩余预算先冻结，不按首选实扣退款

对应段：C03-05 / C03-06。共用source IDs：`24E23E0 / 2A957E0`。

1. 例A：B100 / S_pref120 → P100 / R0，县不调用residual
2. 例B：B100 / S_pref40 → P40 / R60，先存60再执行首选
3. 首选逐次减请求q；实际debit单列未知，R不会按实际写回重新算

画面限定：普通非负安全整数域；例中实际writer debit不推导、不填0；缺residual事件不是观察到zero-budget调用。

缺拍/缺实证：实际current B/S_pref和county源parent/physical。

## D05 修正先取整，49不能扁平算成50

对应段：C03-07。共用source IDs：`24E6650 / 24E6570 / 24DD9A0`。

1. W3001 / C5000 / M=M2=33339 / N100 / Q100000（假设）
2. F=1666；比例人数49；minimum33；B=min(3001,max(49,33))=49
3. 把C×M×W推迟到末尾才除Q²得到50，顺序不同

画面限定：普通非负无溢出；极端机器宽度分支保留原专题；未读本场loaded值，不填Robert当前预算。

缺拍/缺实证：当前真实county输入与真正writer。

## D06 整数预算、兵团请求、物理写回分层

对应段：C03-09 / C03-12。共用source IDs：`24E32C0 / 2A957E0 / 2634190 / 2657E80`。

1. 假设F5%：E19→预算0；E20→预算1
2. 整军预算→有序ArRg请求→unique physical DATA写回→cache refresh
3. DATA别名只计一物理槽；每次实际零/正/负变化独立保存

画面限定：不从两个端点推每个中间写入；请求0仍可能有writer；无事件不是完整零loss。

缺拍/缺实证：完整actual AL/预算/physical窗口，实际current+max与alias覆盖。

## D07 拆半搬whole ArRg，库存字段独立复制

对应段：C05-06。共用source IDs：`296C2F0 / 296B240 / 296B6C0`。

1. 图示以完整ArRg ID为整块，按原生分类权重迁移，不画每个chunk切半
2. 新Army初始化复制stock180，不按所分人数除二
3. 独立后态重读两军人数/DATA/commander/stock/cap

画面限定：图中不填虚构当前Army ID/人数；未展开callee不绘成全部物理无副作用；不宣称UI总数严格半或每次实际DATA必守恒。

缺拍/缺实证：正常split微实验与全部DATA/actual commander/供给后态。

## D08 分两军仍要看聚合用量

对应段：C05-07。共用source IDs：`strategy_a_route_inputs.next_decision / 296C2F0`。

1. 假设选中Army100；全省current usage6000 / limit4000
2. 分成50+50仍同省，其他贡献者/身份/资格不变
3. 同一合格兵团贡献仍为100，总6000；离省/改资格后重新读native用量

画面限定：全部贡献者和资格固定只是算例条件，真实split可能改变相关上下文；目标当前usage不包含未来入军，不承诺未来underlimit。

缺拍/缺实证：当前同帧usage/limit→真实split后聚合用量→真实离省重读。

## D09 角色记录、现任统帅、骑士、物理兵员四列

对应段：C06-06。共用source IDs：`28CC150 / 2632CB0 / 2633ED0 / 24DF9F0`。

1. 条件source：清旧统帅→分配ArRg→构造DATA空/缓存0→关联旧Character
2. 角色refresh可形成缓存1/1；实际DATA仍独立取证
3. 分别列：角色叶/actual commander/完整combat Knights/physical DATA；不可互填

画面限定：不是每次merge必创建；构造时空DATA不外推所有角色记录永远无DATA；当帧角色身份不授历史出生被观察。

缺拍/缺实证：新同场extra fullID、native_character_role/count0/backlink、统帅与Knights独立查询。
