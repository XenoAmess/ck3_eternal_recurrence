# 保留E6的21日续行：软件验证记录

2026-11-22，machine_id: `4-8e1c2f1861`。实际验证树是35dec8e基线加Root已采用的13份受审代码／测试／CI／合同说明增量，不是纯35dec提交树；最终提交头尚未在本记录确认。金融Java旧640项、loc25及R71实机结果保持原范围。

## 当前软件结果

| 实际操作 | 原进程／方法结果 | 范围 |
| --- | --- | --- |
| affected03 | 退出0／51.6211657秒；115项、内部48.478秒、0失败／错误／跳过 | 最终受影响公共接线与既有回归，包含新增13项 |
| optimized13-02 | 退出0／6.5432700秒；13项、内部1.491秒 | 上述13项的优化模式复验，不追加到115 |
| old-timer-isolated02 | 退出0／12.2657036秒；1项、内部11.658秒 | 旧严格sevenSave夹具及独立公共verify，属于115中的同一方法 |
| TYPE02 | 退出0／2.3536509秒；2份生产源码 | 保留4条既有untyped-body提示；不是全树strict类型通过 |

24个精确来源在最终检查窗口前后逐叶相同。最早focused13原0／4.7225817秒、内部1.648秒保留其较早源切点，不拿它外推Host或整体115通过。TYPE02也早于这个24叶窗口，按原两源范围单列；最终当前组合回归来自affected03。所有子集与旧640／25均不累加，没有新增Java／Maven或Native编译信用。

## 原失败与最小修复

首次affected01原1，93项／2ERROR：一个是Root外置runner漏仓库sys.path，另一个是实际Host一日路径仍只允许旧两案。外置runner02只修自己的搜索路径；Host在日进和saved-startup两个同语义set仅增加 `market-evolution-continuation21`，原event mode、product、current purpose、存档与actor guard保持。

affected02原1／115项中1FAIL，旧timer隔离01亦原1／1项失败，证实它不依赖先跑新13项。原因是future annotations下TypedDict可选saved_entry的运行时required-key元数据与默认六字段emission不符。只将六必填字段放入TypedDict基类、saved_entry放入total=False子类；发射函数、timer／curse严格guard和原信用期望未改，也没有增加镜像键表测试。TYPE01的import-not-found原1保留，后继只补实际MYPYPATH依赖根，没有ignore或放宽检查。

## 验收边界

新独立合同本地0／16／21读取同一E6累计14／30／35，原12个fixture文件逐字节复用；派生manifest只改case名与尚未出现的终标记要求，不重发前三个once-only标记。源savedPair／机器／独立归档／JSON范围和36条原记录继续严格校验；原35日case及R71 run2／verify2／D14 GAP永久不变。[合同说明](market-evolution-continuation21-acceptance.md)。

这些是NoGame软件结果，不是新21天实机。Host源码已经变化，仍须由Root沿既有shared Python host-delta路径完成实际来源绑定，不用旧Host rawpin／Q49替代；此记录不宣布其已完成。尚无新Game、SAVE、ARM、35日观察、容量／395日性能、完整产品或Workshop首发通过，也不从缓存PLAN推算已释放空间。后继从R71 D14真实档继续，不回滚R64、不新开世界、不补旧日。

[实际wait、来源窗口与全部失败索引](../../docs/maintenance/evidence/2026-11-22-financial-markets-continuation21-software.json)。
