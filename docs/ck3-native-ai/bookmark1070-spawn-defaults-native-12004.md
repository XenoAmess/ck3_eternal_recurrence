# bookmark.1070 事件兵：原生默认与创建类别（actual 1.20.0.4）

machine_id: `desktop-3fevhd2-1c74096080`；本次来源观察 `2026-10-15T20:03:31.720049+00:00`。
exact build **1.20.0.4 / Steam25734779**，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
复用Root冻结身份，未整文件hash、执行EXE、连接游戏/SDK/桌面或构建。

本次新增闭合：**`uses_supply` 的当前内置文档默认是yes**；其解析/执行/供给消费者字段链已核。
**spawn创建persistent时固定传分类raw1，且该值被现有CanReplenish源码直接拒绝。**
这两个来源轴独立，不能将raw138命名为`can_reinforce=no`或`uses_supply`。
三个spawn条目及历史事件选择继续复用[既有专题](bookmark1070-event-troop-policy-12004.md)，不重跑事件策略。

## 当前对象身份与来源

获准的一次actual `.rdata` `[43DA000,542EC00)` 字面定位得到：
`spawn_army` 在 **4838EE8**，`uses_supply` 在 **46CAC68**。
同一读取只保存命中窄span与spawn邻域4KiB，没有保留全段。
邻域中的vtable **4839B88** 经其COL **4EB9540**→TypeDescriptor **5A71D20**，
实际名字为 **`.?AVCSpawnArmyEffect@@`**。因此下面函数来自当前真实类型，不是按旧1.19地址平移。

| 来源 | 已读取范围/作用 |
|---|---|
| builtin effect help | `4838F60`起的NUL终止文本，当前EXE直接写uses_supply默认yes |
| parser虚槽2 | `2CCCFA0..2CCD15D`，445B，实际按intern token分支 |
| Execute虚槽22 | `2CCD680..2CCE03E`，2494B，含两条创建路径与flags复制 |
| levy创建helper | `2CCE460..2CCE536`，214B，真实CALL来自2CCD999 |
| persistent创建入口 | `2A96C00..2A96D36`，310B，真实CALL来自2CCDB38与2CCE4E2 |
| supply eligibility leaf | `2A956B0..2A95720`逻辑112B，其中98B代码至RET、14B INT3填充 |

完整raw hex、指令、SHA和读取记录在[portable source index](evidence/bookmark1070-native-defaults-12004/source-index.json)。
`spawn-name-leaf`只是采集阶段旧文件名；其实际16B函数返回scope mask8，**不作为类型名称证明**。
类型名称由上述独立RTTI链证明。slot8与slot9为辅助验证片段，未作为constructor或全函数闭合信用。

## uses_supply：默认值与实际字段链

当前EXE内置文本明确：`uses_supply = yes/no # Default: yes`。
同文本也写inheritable默认yes、origin省略时取location；这两项本次只授当前文档信用，不扩展继承/驻地业务。

actual intern表在 **46F1750** 保存id **32C7**、在 **46F1758**指向literal **46CAC68**。
parser `2CCD09A/0A1`匹配32C7后，`2CCD0E1`提供effect **byte4F1** 给bool解析器3F980B0。
两条真实创建路径均把这个byte复制到新persistent **byte141**：
Execute `2CCDB54/5C`，levy helper `2CCE501/508`。
不是由当前兵数、名称或另一个Regi字段反推其含义。

actual **2A956B0** 先检查ArRg kind14C；非1直接true。
kind1按首DATA、完整generation及原生fallback解析persistent，`2A95703`实际检查byte141是否非0。
它是既有supply-loss eligible消费者中的一环；不把它解释成整个army补给总公式，
不凭默认yes授当前补给消耗/伤亡已经发生。

**仍未读取CSpawnArmyEffect的constructor/factory初始化byte4F1=1那条store。**
默认yes证据是当前二进制内置文档；parser→Execute→persistent141→当前供给消费者是实际指令证据。
二者分层记录，不伪装已观察到未抓到的constructor写入。

## 补员：创建常量1到当前谓词，而非虚构独立开关

MAA路径 `2CCDB2F` 置 **R8D=1**，`2CCDB38`调用 **2A96C00**。
levy路径 `2CCE4D9`同样置 **R8D=1**，`2CCE4E2`调用相同入口。
`2A96C17`把R8D保存到EBX，**2A96C28将EBX写新persistent DWORD138**。
这闭合了spawn创建时raw138=1的producer，不再只有后读值；raw类别正式enum名仍未知。

复用[actual当前补员资格专题](episode04-special-troop-refill-eligibility-12004.md)：
**262C6F2**比较persistent138==1，**262C6FF**直接跳false262C990，早于Army/definition/资源。
因此当前build的这些spawn创建路径选择的raw类别进入该拒绝分支。
它与R0176 Army93四个physical DATA实际raw138=1、permissionfalse一致，
但不是逐spawn ordinal或当前兵团创建过程的新实机捕获，也不证明此类别永远不会被其他writer改变。

本次17MiB定位中`can_reinforce\0`零命中；parser也没有单独展示这个分支。
**不据零命中宣称所有generic parser都不支持该词，也不造一个can_reinforce默认bool。**
准确的可复用结论是：**当前spawn实际创建raw1，而当前原生CanReplenish对raw1直接false。**
uses_supply默认yes与此并不矛盾；没有补员许可不等于不用补给。

## 尚未闭合的下一入口与取证限额

下一入口是当前vtable **4839B88**的真实RIP code-xref，找到具体factory/constructor后，
只读其准确.pdata范围，确认effect4F1初始化及之后是否覆盖。
现有小source没有该xref索引。整`.text`搜索需71,141,888B，超过Root本任务累计code256KiB限额，**未执行**。
不把旧1.19factory RVA换偏移当新入口。只要默认值声明与已闭合字段链足够供当前解释，就无需制造新游戏验证。

一次辅助leaf16B前缀把MOV immediate切在末端导致decoder RED；首个helper未留raw。
修正为先落raw后解释，必要重取同16B，再只读后续96B并复用前缀，得到真实RET和padding。
该失败/重复16B计入源读取总量，不是游戏或能力RED。

本次无新实机/自然日/补给或补员业务信用；没有策略、SDK、native或游戏操作变更。
外置包≤2MiB，属于Root原active32MiB池，截止/复核仍为2026-10-16T07:45:01.597Z，不自动延期。
