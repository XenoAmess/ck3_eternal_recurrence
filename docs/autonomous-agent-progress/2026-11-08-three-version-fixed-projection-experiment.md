# P146：三版本固定96调用，未证明稳健 CPU／延迟收益

接受的是离线软件实验记录，不是新的生产优化采用。生产源码及P144基线351保持；同输入的分配下降得到更完整复核，但 count 版本 wall 未胜原版，CPU／wall方向不一致，不能据此授 worker速度或10秒目标，也不凭混合结果立即回退。

独立 Test 1TU／2类首次编译0，唯一 JUnit 1P，公开 `projectFull v3` 固定16轮 A/B/C/C/B/A＝96调用、每版32次，0额外 target warmup。所有冷样本保留，不按结果加样本、删首项或筛子窗。

- A：P138 Assembler6＋P137 Driver2，同child两root，有效8类，计数改动之前。
- B：P143 Assembler6＋Driver3，同child完整9类，含 EncodedByteCount。
- C：P144 Assembler6＋原P143 Driver3 parent9，计数＋证据副本复用。

三侧输入共享同一不可变 frame／facts／ref，反射适配对称；各自 FullSnapshot 公开 getter 核 actual／facts身份与原件ref，逐行核完整 semantic bytes、member order、binding、原state／packet SHA和全部后置条件。96行端点及后置条件、组内统计、16轮配对均由Owner与Root独立复算一致，不保留96个大型结果对象。

## 全32样本分布

时间单位ms，allocation单位B；没有剔除冷项：

| 版本／指标 | n | 总计 | 均值 | 中位数 | min | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A wall ms | 32 | 945.9629 | 29.561340625 | 24.03745 | 20.4691 | 144.119 |
| A CPU ms | 32 | 718.75 | 22.4609375 | 15.625 | 0 | 62.5 |
| A allocation B | 32 | 2533977824 | 79186807 | 79112184 | 79112080 | 81493848 |
| B wall ms | 32 | 950.5882 | 29.70588125 | 26.134 | 19.7457 | 73.774 |
| B CPU ms | 32 | 593.75 | 18.5546875 | 15.625 | 0 | 31.25 |
| B allocation B | 32 | 2172033440 | 67876045 | 67870120 | 67870032 | 68039024 |
| C wall ms | 32 | 830.8202 | 25.96313125 | 23.9627 | 20.274 | 40.3326 |
| C CPU ms | 32 | 671.875 | 20.99609375 | 15.625 | 0 | 31.25 |
| C allocation B | 32 | 2063122016 | 64472563 | 64469648 | 64469048 | 64561112 |

CPU有15.625ms量化背景，A／B／C各有2／4／2个零值，零不表示零计算成本。B wall总计比A略高，且中位数26.134ms高于A24.03745ms；C wall较低，但C与B的CPU累计方向相反，不能只挑较好的指标。

## 预声明16轮配对

每轮每版两次调用求和后比较；负值仅表示该轮对应累计指标较低，不作独立性、显著性或p值推断：

| 配对指标／差 | 负／零／正 | 16轮合计 | 均值 | 中位数 | min | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| wall ms B−A | 5/0/11 | 4.6253 | 0.28908125 | 2.82975 | -82.64 | 57.1833 |
| wall ms C−B | 10/0/6 | -119.768 | -7.4855 | -3.62345 | -59.9908 | 6.5724 |
| wall ms C−A | 9/0/7 | -115.1427 | -7.19641875 | -1.6686 | -95.1417 | 17.4071 |
| CPU ms B−A | 7/7/2 | -125 | -7.8125 | 0 | -46.875 | 15.625 |
| CPU ms C−B | 4/7/5 | 78.125 | 4.8828125 | 0 | -31.25 | 62.5 |
| CPU ms C−A | 5/8/3 | -46.875 | -2.9296875 | 0 | -46.875 | 46.875 |
| allocation B B−A | 16/0/0 | -361944384 | -22621524 | -22484096 | -24698192 | -22471688 |
| allocation B C−B | 16/0/0 | -108911424 | -6806964 | -6801840 | -6877560 | -6800832 |
| allocation B C−A | 16/0/0 | -470855808 | -29428488 | -29285072 | -31575752 | -29284240 |

三种 allocation 差都16轮全负，支持此前分配机制。wall的B−A为5负／11正，C−B10负／6正，C−A9负／7正，并非稳定一致的延迟证据。CPU配对含大量零／相反方向，分配下降也不等于 CPU、live／peak heap或整体延迟下降。

## 已知偏差与完整费用

fixture与semantic后置编码／SHA使用parent DriverJson，C与观察工作共享writer／factory／代码状态，A／B有独立child Driver；这是已知非对称预热偏差。共享JDK／Jackson／normalizer、不同JIT／GC历史及固定C/C相邻顺序也保留。ABCCBA仅平衡线性顺序影响，不是随机或相同JIT状态，不授孤立算法因果结论；固定大DATA也不能给自然调用频率。

Driver显式初始化A／B／C为361.4404／1.2327／0.9701ms；Assembler load/init为1.1528／0.6267／1.6957ms，反射／来源检查4.7669／1.2646／1.2533ms。setup2.0725372秒；目标 bracket wall总计2.7273713秒、含观察／post的row累计3.7833982秒，方法至summary/report前5.858361秒。差额不单独归为serialization／GC。

JUnit case6.371秒；编译 actor／outer5.9543323／7.2263501秒，唯一JUnit8.7703270／10.0152147秒，child stderr317B原件保留。actor含父记录／资格工作，不称纯child wall。两phase actor合14.7246593秒、outer合17.2415648秒，不代替整窗。

首operator→末operator44.505829秒，包含phase间隙27.264258秒；compile BEGIN→末CLOSE43.574616秒；更早Java Ready→末CLOSE399.605245秒分别保留。精确完整child lifetime仍UNKNOWN，不由差额倒推。最终owned metadata835311B＜4MiB，原件完整，没有额外JVM刷绿／JFR／模型HTTP／Game操作。

Root结论为软件实验记录通过、无稳健 CPU／latency采用；P143／P144此前allocation-only结论及原件不回填改变。0 saved、无Runtime／head47／P100或10秒／新增确认保存日信用。下一P147仅D源码准备，净CPU与compact快路／异常层次仍需单独证明和实际Reader路径测量，不能用本96次公开projection代替。

## 原件

- [Root固定分析合同](D:/ck3-state/resume91-root/post-vacation-20261107/P146-PREDECLARED-FIXED-ANALYSIS01.json)：3224B／`26ed28777e8ee83aa48d854bc89046b24abfd087e449d048011be74974e22b48`。
- [Root实验接受／无time gain](D:/ck3-state/resume91-root/post-vacation-20261107/P146-FIXED96-SOFTWARE-EXPERIMENT-ACCEPTANCE-NO-TIME-GAIN01.json)：3224B／`940d2e3b82d2a396c6ca95374d552d6017b741e438fb00e5bff35997b2479eea`。
- [原96行报告](D:/ck3-state/resume91-native-integration/p146-public-project-fixed96-test01/tmp-experiment/junit-6879727096979793503/p146-three-version-project-full.json)：141940B／`90350dac07d71f5c2bc9a82ea0def08ebe39608d3b06ff2806fcfa0eae57c6e3`；[Native完整资格](D:/ck3-state/resume91-native-integration/p146-public-project-fixed96-test01/QUALIFIED-P146-ONE-TEST-TU-AND-FIXED96-SOFTWARE-EXPERIMENT01.json)：47673B／`24618ab93b58ef6561c2d9cedc859bd4bfc32fab5d7edd59c5bf9a9fe289c7ac`。
- [Owner全96与预声明统计复核](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-projection146/P146-OWNER-ALL96-ACTUAL-REVIEW01.json)：22928B／`3594b23b39bcf36d86a0e74a019d48fa49c214d5122b2d74be360fdb25776a5a`；[同字节实验工具采用](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-projection146/FORMAL-TEST-TOOL-ADOPTED-AFTER-ACTUAL01.json)。
