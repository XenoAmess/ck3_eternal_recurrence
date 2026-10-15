# 四期 R04：县进入倍率 M 的零分支、来源与下限（1.20.0.4）

`24DD830` 已完整闭合到两个 RET。它不是一般兵种免损耗开关：
只有 Army+1D4 非零、owner 的 Government 所选定义开关、以及选定
Situation 的当前县覆盖同时满足，才使 `24DD9A0` 提前返回 M0。
普通路径的 Army modifier 也不是只读玩家：原生 getter 汇总 Army
owner、不同的 commander 和 roster 中角色关联来源。Army+1D8 对象的
`+280` 则是另一个独立的 keyed modifier container。

两个下限地址的**比较位置已闭合，运行值没有闭合**。它们落在 EXE
`.data` 的 zero-fill 区，不能从文件读取出运行期0或100000。本包不把
“第二下限为100000”的预期写成实际常量资格；下文对此给出条件结论。

## 来源、机器与范围

来源机器 `machine_id: desktop-3fevhd2-1c74096080`；首次新 predicate
读取 `2026-10-15T18:34:33.618272+00:00`。冻结 CK3 `1.20.0.4`、
Steam25734779、EXE SHA256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
源码包为 `C:/ck3-e04-resume-20261015-a01/high-parallel-county-multiplier-a05/`；
机器、实际读取时间、argv、source pins 与失败边界见 `SOURCE-FACTS.actual.json`。

已有 M/F/B getter、353B allocator、原常量包均只读复用，没有重新
采集或复制。新增来源只沿实际 CALL 和实际控制流；无全 EXE hash、
全 pdata scan、随机 xref/邻域、EXE执行、构建、SDK、游戏、桌面或
主树写入。仅文档增量，未运行旧矩阵，也没有新增依赖缺失输入的
半成计算器。

| 新源 | 已闭边界 |
|---|---|
| `24DD830..24DD99A` /362B | 整个零谓词，全部本函数分支与两个返回 |
| `24DFBB0..24E013E` /1422B | Army keyed modifier 汇总的完整函数 |
| `23036E0..2303783` /163B | key U16 查询；已读 prefix45B复用，只补其控制流后续 |
| `24E0E90..24E0EDC` /76B | 无 pdata 的 current Province leaf，按可达指令读至 RET |
| `25CA9B0..25CAA64` /180B | Situation 覆盖集合的 any-member 查询 |
| `2579920..2579A0C` /236B | 当前 CountyData 的直接/命名集合成员路径 |
| `8FD480..8FD4D7` /87B | singleton getter；不擅自给其类型命名 |
| `2A33570..2A33697` /295B | singleton+F00 的64位 key查 Situation，不是 FullID resolver |

Government getter `28C2DF0` 复用[已闭合237B来源](returned-selector-28c2df0-12004.md)
与[Government合同](council-government-12004-adopted-mcp-port.md)，没有重采。
源资料和当前机器运行资格分开，旧 Z 原件不可读的状态保持不变。

新 source-read metadata 已逐字节核对后压缩保全为
`source-read-metadata.actual-a01.zip`；展开路径已回收，原始字节仍可按
同名 ZIP member读取，具体 SHA和原因在 `METADATA-COMPACTION.actual.json`。
不制造同名替代文件。Root后续将本lane metadata分配修订为128KiB；
总任务1MiB、共享池与原期限未变。此后未再做压缩或回收。

## 24DD830 的完整条件

按实际执行顺序，任一不通过即 AL0；只有最后一项通过才 AL1：

1. `24DD83A..844`：Army+1D4 必须非零。零时直接走 false RET，后续
   owner/Government/Province/Situation 均不读取。
2. Army+124 经 Unit storage、完整 FullID 或原生 fallback解析；取
   selected Unit+174 的 owner Character FullID，再按 Character+18
   核完整身份。selected Character magic+1C为 Char、ID非-1才继续。
   不把 commander或玩家替代为这个 actor，也不增加原生没有的正ID门禁。
3. `28C2DF0(owner)` 返回非空 Government。Government+82C tag为2时，
   取其+820指针；其他tag走实际 fallback。所选对象 magic+38必须为
   GDbo，且 byte+17E非零。该 definition的正式类别名、开关名称未闭合。
4. `24E0E90(Army)` 以 Army124→Unit+20取得当前 Province，必要时用
   原生 fallback；其+848 CountyData指针必须非空。这里是实际当前县，
   不是 target Province、路线终点或 owner首都。
5. `8FD480()` 返回 singleton，取其+F00的**64位 key**。以
   `GameData+275E0` 为 manager调用 `2A33570`。后者对8字节 key 做
   FNV/开放寻址查找，返回槽内指针或实际 fallback；不是mask24
   FullID查找。返回对象 magic+C为 Situ、ID+8非-1才继续。singleton
   正式类型、+F00 key的业务名称仍unknown，不能改写成“任意Situation”。
6. `25CA9B0(selected Situation,current CountyData)` 必须 true。
   它按 Situation+128/+134 的原始ref顺序，解析每个候选并调用
   `2579920`；任一命中才 true，空集合/全不命中为 false。
   后者先查接收对象+1A40/+1A4C中的 CountyData+18完整ID，再查
   +1A58/+1A64命名集合：通过 `2AA8590` 取得 provider，向
   `BCAB30(provider+30,&county)`问实际成员。两个末级helper及集合
   正式类型名未展开；不擅自称“所有敌对县”或“同一战争方”。

这解释零分支的机制边界：它是 **特殊原始 Army状态＋Government
定义配置＋选定 Situation 的当前县覆盖** 的合取条件。不是只要
处于某个大地图区域、Army+1D4非零或某modifier为负就会触发。

`24DD9A0` 对上述 AL1 立即写 M0，跳过所有 property和下限读取。
若某次预算中的 fraction用M和minimum用M都走该零分支，两项为0；
但当前预算0仍不是一次实际县扣兵/损耗零值观测。

## Army property1A7/1A8 与 Army+1D8 的来源

M getter向 `24DFBB0(Army,out,U16key)` 分别请求1A7及条件性1A8。
该 getter先将输出置0，然后按原生顺序累加：

- 有效 Army owner：Army124→Unit174 Character，调用
  `28C3AC0` 取得其modifier context，再以 `2C4D530`、相同key、mode0、
  scale100000取得贡献。
- 有效 commander：Army120 Character。只有其完整 Character ID和
  owner不同才另加一次；同一角色不重复计入这两项。
- 原始 ArRg roster occurrences：ArRg148有效角色路径还有独立贡献。
  它读取角色关联对象、解析其+570 ref，再处理该对象+58/+64的
  24B definition记录、构造临时 modifier context并查询同一key。
  这里不以军队的总人数加权，也不先按角色/ArRg去重。关联对象与
  记录的正式游戏类别尚未闭合，不把它随意叫作特质、骑士荣誉或装备。

因此1A8不是 M getter中的另一个硬编码倍率；它是对这个完整 Army
property汇总机制使用不同的U16 key。1A7、1A8的本地化modifier名称
和完整枚举注册链仍未闭合。

非零 Army1D4 的普通分支还从 **Army+1D8实际所指对象+280** 调
`23036E0` 请求key1A8。该receiver是独立 PC：keys pointer+0、signed
count+C，按 unsignedU16二分查询，映射值来自同index的 values+68，
返回 signedQ64；FFFF或原生absence返回0。这里没有再次汇总玩家、
owner或commander。它是对象保存的 keyed modifier来源，不能用
Army汇总1A8替代，也不能从缺读取补一个0。

Army1D4的正式状态名、Army1D8所指对象的类型/生产者，以及它是否
等于 Government+820选出的definition，均未证明；本包不合并两者身份。

## M 的顺序、零值和“100000下限”

令 `A=ArmyProperty(1A7)`、`B=ArmyProperty(1A8)`、
`T=PC(Army1D8+280,1A8)`。以下 ADD及比较保留原生signed64语义：

```text
if raw Army1D4 !=0 and zero_predicate_passes:
    M = 0                         # 无下限/property读取
else:
    M = max_signed(wrap64(100000 + A), loaded[5C68F68])
    if raw Army1D4 !=0:
        M = max_signed(wrap64(wrap64(M + B) + T), loaded[5C69118])
```

第二个下限只在 **Army1D4非零、zero predicate false** 的分支执行。
如果同一来源/上下文实际证明两个loaded值分别为0与100000，则：

| 原始分支 | 普通非溢出域中的后果 |
|---|---|
| Army1D4=0 | M=max(100000+A,0)，A<=-100000也可使M0；不需要Situation零谓词 |
| Army1D4非零，零谓词true | M0优先返回，下限100000不生效 |
| Army1D4非零，零谓词false | M=max(max(100000+A,0)+B+T,100000)，最终至少100%基础倍率，仍可大于100% |

最后一行不是把每个原始modifier都clamp为非负；它先完成顺序相加，
再对**最终M**作一次第二下限。这里的100%是 M的Q100000倍率，
不是损失100%士兵，也不是固定“至少100人”。整军B仍由有效比例、
minimum人数项各自取整/比较和总人数cap产生。

**字面下限资格仍缺失：** 两地址均处于 cached PE `.data` virtual
范围但不在raw文件范围。一次只针对这两个qword的有限尝试在首个
target映射时拒绝，实际读到data0B；没有越界读、猜文件offset或
转为进程读取。要把上述条件表升级为本构建的字面0/100000规则，
下一来源必须是这两个地址的实际初始化producer或同机当前值回执。
本包未扫描startup/xrefs，亦未索取Root活跃R0176内存。

## 视频与智能体的用法

当前 `county_entry_inputs_v1.minimum_multiplier_raw` 已是原生最终M；
`effective_fraction_raw`、原生budget仍优先于上述缺输入的重算。
M0只说明当前getter结果，不能单独断言零谓词true：在第一下限为0
的条件下，普通modifier也可归零。M100000也不能单独证明第二下限
执行；未触发下限的顺序和同样可能等于100000。

视频可说“原生县倍率另有政府配置、局势覆盖和多来源modifier分支”，
目前不能为Army1D4、definition17E或1A8赋一个确定游戏名称，更不能
用同日空writer ring说明免损耗已执行。智能体继续读取现成native
M/B作为同帧预选，缺少这些分解输入时不自行重建。没有修改strict
consumer、DTO、TLS或任何运行接口。

## 下一 a07：只补两个 loaded floor 的当前读取

最小施工点沿用 `county_entry_inputs_v1` 的同帧 CArmy reader，在其
available父块内增加可选 `multiplier_floor_inputs_v1` child：

| 字段 | 合同 |
|---|---|
| `status` / `unavailable_reason` | 独立 available/unavailable；读取失败不抹掉已可用 native M/B |
| `source` | 固定 `native_current_county_multiplier_floor_inputs` |
| `fraction_scale` | 固定100000 |
| `base_floor_raw` | signed64，实际image_base+5C68F68 qword |
| `army_1d4_nonzero_floor_raw` | signed64，实际image_base+5C69118 qword |
| `army_1d4_raw` | unsigned8，已验证同一 CArmy+1D4 原始字节 |

三个数都读到才available；否则三个数均null并保留具体失败。合法
0、负signed64和非1的非零flag均保持原值。旧producer没有child时
仍缺字段，不填预期的0/100000。只增加两个绑定指针和已有内存reader
的拷贝；不调用新的原生函数、不增hook/ring/query或runtime开关。
现有双采样/owned DTO equality应包括该child，沿既有frame规则处理
漂移，不给单次读额外稳定性信用。

strict normalizer允许这个**可选**child并精确验证键、类型、scale及
null合同；父块原键和既有输出语义不变。采用a07后只需一次新的
生产reader/serializer compound验证真实0/100000、缺一个地址与
signed值保持，再让新wire进入生产consumer；不重跑旧TLS/allocator
矩阵。此处仅交施工合同，未写代码或运行测试。

fresh same-frame回执若读到base_floor_raw=0、
army_1d4_nonzero_floor_raw=100000，才能为该机器该frame授予上表
字面下限。它仍不能单凭最终M反推零谓词/下限是否实际命中，也不
自动补齐原始property名称或Army1D8类型。
