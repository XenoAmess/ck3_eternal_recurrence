# R0217五条空DATA调用：精确零分支与副作用边界

五条记录确实满足现有physical capture合同的**完整空DATA捕获与精确物理debit=0**；它们不是缺采样、null补零或空history。然而，仅凭这些记录和桥接源码，**不能把整个原生writer调用称为无副作用**。当前direct-v2继续排除五条，没有修改守卫或追授资格。

分析机器`desktop-3fevhd2-1c74096080`；新鲜机器ID、观察时间、全部实际条件与冻结源SHA见[AUDIT.actual.json](AUDIT.actual.json)。输入只读原82KB实际投影及已知精确源码，无新SDK、游戏、EXE读、构建或生产源码改动。Root另行报告本场已正常闭场；本分析不替其退出回执签核，不覆盖原消费时仍待闭场的历史记录。

## 冻结来源已与实际生产身份绑定

本轮runtime为`efda0d8cfbeee1dbeffd05c5f662cfd0f5c4073b`，native实际build source为`43fd32670897f657da681cf0a94d162e3135a89c`。两者native Git subtree均为`28dda02c23eda2efdc0a09c8a9cba122dd06cca9`，与R0217的common runtime a39-a03 manifest/native-source-index精确一致；该manifest绑定DLL SHA `f52db5e8a1be4c55416155536d7b5cee519e1ee69c99123aa6edd1f42a63c9a2`，本次没有重读二进制。

本目录`source/`保存四个冻结Git blob的原字节；当前worktree逐字节相同。关键两份：

- [physical journal](source/ck3_12004_actual_loss_writer_journal.cpp)：32977B，SHA `81d1b2ecc85711a00a3e63fdcb4887666cf3a3a84ae09c3123e42ad2f7d90f61`。
- [direct-v2 capture](source/county_primary_direct_owner_at_writer_12004.cpp)：15430B，SHA `fda4b2ad0dec3555e2dd40c4d2e4b830974cef53e5474dc9fcbc6ccc6d389001`。

DTO/header的精确SHA、Git blob及原路径同见AUDIT，不用当前HEAD或文件名代替编译来源。

## 五条原记录究竟证明什么

seq1207–1211，ArRg56–60，实际Army/CArmy FullID均0。每条都有：parent capture flags=0、same_instance_after=true；native/captured DATA count与physical slot count均为明确整数0；aliases/slots均为空；physical_capture_complete及physical_debit_observed均true；actual_physical_soldier_debit为明确整数0；request_raw=0；缓存current与max前后都为1/1。

同时，direct-v2所有非physical-association守卫均true，实际registry/receiver、唯一roster occurrence、caller `24E25EE`、writer clock/thread/token、实际日期及同一采样epoch均相符。唯一v2 failure为4096 `physical_association_incomplete`，source_complete=false。这些条件已对五条逐项核验，并写入AUDIT；没有将ID0按假值丢弃，也没有用query membership补原生身份。

[journal](source/ck3_12004_actual_loss_writer_journal.cpp)中的定义给出精确含义：

1. `ReadDataHeader`（L134）接受`count==0`，仅非空count才要求非null data；每次仍需成功读取pointer/capacity/count且`0<=count<=capacity`。
2. `CapturePhysicalBefore`（L155）在有效header后设置`context.complete=true`，发布native count；count0使DATA和physical捕获循环自然为空，没有partial/truncated错误。
3. `CapturePhysicalAfter`（L211）重读header并要求相同data pointer/count及same ArRg实例；debit从0开始，空槽不进入累加。只有complete仍true时才发布这个0。因此本次0是有资格的空集合signed sum，不是default/null兜底。
4. serializer中的`std::optional`有值0会发布`physical_debit_observed=true`及数字0，不会转成缺失。

这证明的是该次DATA关联物理观测域中的精确零净扣减。父journal没有发布capacity前后值，其same-header比较也只比较pointer/count；不能额外声称capacity完全未变。

## 为何原v2仍false

[direct-v2 capture](source/county_primary_direct_owner_at_writer_12004.cpp)的`physical_ok`硬要求`data && count>0`及`event.physical_slot_count>0`。有效空DATA必然不通过，并置4096；`FinishCountyPrimaryDirectOwnerAtWriter12004`只在全部failure flags清零时设置source_complete。Python当前consumer又明确拒绝`source_complete=false`。

因此，不能把“空集合已完整捕获”改写成“当前v2非空关联已完成”。源合同的两个`complete`定义不同。五条既有v2结果必须保留false。

## 一个可证明但尚未实现的新零分支predicate

可以独立定义派生分类`complete_empty_DATA_zero_physical_debit`，保留原v2字段与失败原因。最低输入同时要求：

- 原事件成功same-instance、parent flags0、完整physical capture/debit observed；native/captured/physical counts精确为0，aliases/slots为空，实际debit明确为0。
- 精确本build/caller、原始进程/帧/序号窗、同epoch/date/thread、唯一token、完整generation身份与非空registry/receiver关系均通过；v2所有其他守卫true，唯一flag恰为4096，原source_complete仍false。
- 对本次最窄零分支，再要求request明确0、缓存current/max前后不变；不能用这些缓存替代上一项physical证据。

五条真实记录都满足这个分析predicate。它还不是生产API、既有v2合格结果或新合同验收，不自动把18个既有合格个别调用改成23个，也不生成县总额或整卡GREEN。

## “无副作用”仍未证明

journal仍无条件把原始调用`original(regiment, request_raw)`转发一次，随后还会发布journal/执行可选completion observer。它不记录原生skip verdict、refresh是否执行、全部写地址或原函数内部瞬时状态。当前/max相同不能排除同值写、刷新、Q统计或其他域变化；空header的前后相同也不能排除中间变化后恢复。

本轮冻结的桥接C++源码证明采样与发布算法；它不是`2634190`原生游戏函数及全部callee的源码，也不是全写跟踪。已有writer专题明确说零remaining budget也可走后续pass。因此不能把`request_raw==0`提升为原函数必然跳过。若将来真的需要“调用无任何游戏副作用”的更强结论，需先复用已持有的原生writer/skip/refresh精确body及实际分支输入，另行逐域证明；本任务不读新EXE或扩研究范围。

## 最低必要后续验证

若Root决定只新增上述**物理零分类**，已有wire字段足够，不需要新hook/SDK或重新拍摄。只需独立、版本明确的pure派生consumer：保留当前v2不变；用这五条实际投影核正向分类，再对missing/null count、partial flag、非空slot、跨Army/token/date/epoch、非0 request或缓存变化做少量拒绝验证。先验证语义，不用改5条原件来制造当前v2 PASS。

只有未来真的改C++ producer，才补对应的一个focused empty-header native→wire→consumer验证；单纯派生分类不应强加新native build或新实机。即使新零分支通过，整军县总额与R04整卡仍按各自合同独立结算。

本分析不作为现有17条正例或已拍镜头的前置。没有新增永久待办：五条已离线分析并明确来源/边界；是否实现新分类由后续具体需求决定。
