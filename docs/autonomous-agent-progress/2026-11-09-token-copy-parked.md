# P158：exact-token 副本快路有条件收益，默认 PARK

候选仅在公共 `originalNativeState` 已完成原LE／预算／完整packet严格解析和envelope检查后，对标准parsed state调用既有 `stateToken` 的包内boolean比较。原TOKENS／private stateToken／parser／Guard／hash／oldencode算法体不改，所有miss保旧prefix veto、编码比较和完整state parse。4MiB只是优化否决，不缩64MiB接受域；Source02在大body跨stateBytes.clone之前清引用，小body也在旧路前清空。新增token切片最多4MiB，不等于整体额外liveheap或峰值最多4MiB。

必要生产2TU／10类、Test1TU／4类及sole JUnit实际exit0／accepted／CLOSE释放，case4.767秒、1P0skip；只Source02与Test02编译，01源码审后寿命修正及Test“保留冷首”文字修正均在首次编译前，没有把D草稿问题写成Java失败。actual A13来自currentP150＋P143Driver3，B13来自候选10＋同Driver3；两侧同包隔离、parent DTO／contracts Decimal共享，未重编或复制Driver、旧App／Main／SDK。

保留报告57,457B／SHA256 `32181d955601d95803ff087fe5e190696c8e2bfdcb3f5a04f60f69b3e229878d`，@TempDir.NEVER＋CREATE_NEW；96行全部端点、每形态8ABBA／16A16B、完整typed／order／canonical bytes／原件SHA后验通过。之后15个功能case／30次公有目标调用与7个纯DATA helper probe均通过，含1001digit窄parser miss仍旧接受、>4MiB旧路及多故障顺序。0setup target／0额外warmup，保留所有冷首和后续暖行，没有以“全冷”描述同JVM后续调用。

## 三种输入分别报告

| 输入／指标 | A | B | 实际方向 |
|---|---:|---:|---|
| compact allocation mean B/call | 50,880,780.5 | 54,284,090 | ＋6.68879%，8/8配对增加 |
| pretty allocation mean B/call | 91,552,115 | 54,271,728 | −40.7204%，8/8配对减少 |
| lexical miss allocation mean B/call | 91,551,250 | 94,949,477 | ＋3.71183%，8/8配对增加 |
| compact wall mean ms | 13.341025 | 13.08390625 | 微降，配对5负3正 |
| compact wall median ms | 11.3274 | 11.38365 | 反向 |
| pretty wall mean ms | 18.98930625 | 10.4564375 | −44.9351%，8/8配对下降 |
| lexical miss wall mean ms | 18.9263625 | 20.98810625 | ＋10.8935%，6/8配对更慢 |
| lexical miss wall median ms | 16.36825 | 17.67525 | 反向 |

pretty的强局部收益保留为事实，但compact每轮多分配，miss既多分配也大多更慢，不能转成pretty-only采用来规避当前compact目标。miss最慢B67.8939ms高于A最大31.5067ms，compact B最大31.3304ms也高于A29.8343ms，全部保留不删。current-thread CPU累计compact109.375→156.25ms、pretty218.75→140.625ms、miss218.75→234.375ms；compact A median为0、B15.625ms，其余median15.625ms且含0量化，不授零cost／可靠CPU提速。三形态不按未知自然频率合并headline，不作whole worker／峰值内存或因果提速结论。

Root据这些相互冲突的结果决定DEFAULT_PARK，current350仍P150。两叶Source02和Test均只保D，不正式发表；不补旧候选样本，不把P150私有state复用算作本次收益。P155／P156的PARK、P152原失败与P141历史预算失败各自保持。

## 全费用与边界

setup2.0016634秒、后置功能0.1363127秒、before-report4.334646秒不是完整进程或交付窗。3阶段actor合计22.4262089秒／operator资源子窗合计26.0068322秒，不能代替准备与等待；JUnit actor7.0210028秒／outer8.1407503秒，child stdout481B／stderr295B保留，未把outer空输出当child无日志。Native收尾metadata1,104,823B＜4MiB，报告小于256KiB，预算通过不授整个parent硬瞬时峰值。

更早已知Root源码审原件 `2026-11-08T20:01:14.677458Z`→末CLOSE1005.094941秒／→最终资格1200.086930秒，包含01复审、02寿命修、Test文本修、冷启动、等待、结算和后处理；此前仍UNKNOWN，不记0。Native20:09:53.812675Z起485.959724／680.951713秒只是更窄子窗。0新增SAVE，不报有限秒／保存日。

本次正常只发表unit／daily11-09／weeklyW46三份事实文档，不改业务／Test／AGENTS／CI，不捆P159。后继无token切片方案仅按新D契约及首轮前预锁的独立输入评估；旧原件不重算为新收益。无Runtime／Game／P100／head47／SAVE或10秒目标通过。

原件：[Native最终资格](D:/ck3-state/resume91-native-integration/p158-state-token-prod01/QUALIFIED-P158-SOURCE02-PUBLIC-ORIGINAL-STATE-FIXED96-SOFTWARE01.json)（47,788B／`6536b29df0643ad0dd3d517ba8d0783f1a4f881ecd74f13a9847c7ff85393ea6`）；[唯一96行](D:/ck3-state/resume91-native-integration/p158-state-token-prod01/tmp-junit/junit-5026169357550075561/p158-original-state-token-fixed96.json)；[Root153原件与默认PARK](D:/ck3-state/resume91-root/post-vacation-20261107/P158-ACTUAL-153REFS-96ROWS-AND-DEFAULT-PARK-DECISION01.json)（5,811B／`2fa2d10068fb492e08e2c957ea134c0c2d2a23c66c83fcf4ee89a6d85ad4b7cc`）；[更早Root源码审锚](D:/ck3-state/resume91-root/post-vacation-20261107/P158-ACTUAL-TWO-LEAF-FREEZE-INVERSE-SOURCE-REVIEW01.json)。
