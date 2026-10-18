# 圣地最大值能否通过原版事件、决议或效果增加

machine_id: 4-8e1c2f1861；UTC: 2026-10-18T02:47:04.736026+00:00；exact CK3 1.20.0.4 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；native 来源基线 d1c2bc7eb568a4eab3f55c065adb645a9dbace6f。后续只读见 main 已演进到2ac64cc39f7adf5a50f2e3096dac43599658ffd1，未改本专题旧交付，也未重建或操作游戏。

**没有找到原版可用的“增容”进程。** 全部安装原版/DLC脚本中，没有 event、decision、effect、教义、特质、传统、政体或 modifier 调用/定义去提高 HolySite 总上限或 eminent 上限。此前的9/3是全部49个 authored Religion 的默认值；本次补查覆盖动态脚本，仍未找到提高最大值的原版渠道。这个结论与“原生引擎在任何隐藏路径都绝不可能写这些字段”不同，后者没有证明。

## 动态来源与实际 getter

重新读取并逐SHA核对完整7,536文件、222,428,209B，包含安装的DLC、全部events/decisions/scripted_effects/on_action与各种定义；收集514个圣地/主要相关 token。最大值相关只命中原版阈值读取、默认define和Religion可选字段说明；没有set/add/change max/limit/capacity的实际调用或容量modifier。`MAX_HOLY_SITE_RARITY_TOTAL`是神器稀有度总和上限，不能混作圣地数量上限。

完整cached `.rdata` 中261个相关ASCII串、183个identifier形状名字，有 `add_holy_site`、`add_eminent_holy_site`、`make_holy_site_eminent` 等改变名单/等级的接口，没有发现最大值setter名。这个清单是完整范围内的literal locator，不能单凭名字证明所有构造、哈希或通用alias注册都不存在。

更强的消费证据是四个完整原生limit leaf：实际解析Religion fullID，取Religion+20 definition，直接读取9E8/9EC/9F0/9F4四个int32。它们没有读Faith/Rite参数、变量/flag、trait、doctrine、government、modifier aggregate或HolySite Type的动态回调。因此这些因素本身不对最大值进行加算。免费操作改变费用，`allow_adopt_any_holy_site`改变可采用范围，均不等于增加数量上限。换Faith只改变其实际引用的Religion定义；103个authored Faith不能被外推成运行时动态Faith总数。

## 有没有自然超过第9／第3个的原版源码例

没有找到可证明的原版正常满额第10／第4例。七种原生名单/创建/owner变更拼写在整个语料的出现位置全部保留在 `dynamic-all-membership-mutator-occurrences.json`：

| 实际出现 | 普通门槛与范围 |
|---|---|
| `make_holy_site_eminent`：50_holy_site_decisions.txt79，唯一一次 | 同决议is_valid38要求E<Emax；AI107也要求E<Emax |
| `add_holy_site`：同557，唯一一次 | Adopt is_valid499要求T<Tmax；AI571–574还保留一格，要求T<Tmax-1 |
| `make_holy_site_not_eminent`231／`remove_holy_site`392 | 减少等级或会员；不是增容 |
| `add_eminent_holy_site` | 原生有这个名字；authored脚本出现次数为0 |
| `create_holy_site`：scripted_costs/00_costs.txt777 | 这是命名费用块，不是effect调用；创建实际由原生命令validator29A5AD0检查当前T<Tmax |
| `set_holy_site_owner`：starting_holy_site_relics_effects1594 | scope1592是newly_created_artifact；归库存并装备神器，不增加Faith圣地名单 |

原版event没有上述七种直接变更接口的引用；AI没有满额时放宽的stage源码例。原生debug/requirements bypass或强制执行任意effect属于另一个执行合同，不能冒充普通合法路径。低层2441990可以直接编辑eminent名单，这只说明名单不是该setter强制保持E≤3的容器；它既不证明自然能调用第4次，也不把Emax从3改成4。即使出现真实超限名单，也必须分别读取当前max，不能把两者混为“上限提高”。

## 原生写入排除的边界

只扫现有immutable cached `.text`，先统计正位移候选：9E8=109、9EC=18、9F0=86、9F4=16，共229处，每项低于256门限；之后才提取可能写指令。相同disp、错误解码起点或局部栈地址不是Religion typed owner证据，未据此增加“原生动态写入”结论。此前已闭的typed写入是constructor初始化四个-1，以及finalizer按-1条件装载define。其它候选未穷尽到typed owner；本轮不新增EXE元数据读取，不能绝对排除负偏移别名、间接/index写、反射加载、对象复制或bulk copy。因此给智能体的是“原版已知进程没有增容路径”的有范围结论，而非全引擎永久不变量。

交接：`SOURCE-CONTRACT-DYNAMIC-a01.json`、`dynamic-plan.json`及其check/render。验证使用显式require并在Python `-O`执行，旧合同原字节保留；无native fixture、MCP、游戏、主树写入或构建。
