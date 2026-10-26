# CK3 1.20.0.4 Title 窗口只读观察

来源机器为 `desktop-3fevhd2-1c74096080`，观察日期为2026-10-26。当前问题是宗族化密教两枚帝国级信仰领袖的正常建立／恢复验收缺少实际已选头衔身份，不能将导航ACK、旧保存中的头衔或按钮文字当作当前窗口的真实目标。产品不恢复已撤销的政体转换或额外DLC门。

共享实现扩展既有 `ingame_ui_navigation_v1` 查询，`window=title` 仅观察既有窗口。原生序列化的实际32位Title ID经过同一SDK primitive、service及MCP消费；没有打开、摧毁、建立、确认或改变政府的动作接口。查询本身不证明原版按钮合法性或任何业务完成。

版本绑定为CK3 1.20.0.4／Steam build25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。`title_window12004_source_pins.hpp` 保存该build的loaded instruction、vtable、RTTI与布局绑定。调用链从原版GUI窗口上下文和Title handler反向关联当前窗口，再解析完整Title身份；不是遍历所有头衔猜测当前选择。handler的Title字段为`+0xCC`，不能误用相邻`+0xC8`。存储低24位仅定位槽位，必须比较完整32位身份；回退对象不得发布为真实头衔。零和高位ID按完整无符号范围处理，`0xFFFFFFFF`是不可用值。

观察复用既有owner、GUI context、frame及固定root守卫，并比较读取前后的窗口关联。窗口存在、可见和可用身份分别表达；隐藏窗口、陈旧handler、错误root或身份漂移不授予当前可见目标。原先宗教presentation路由的数值范围判断改为明确的五种presentation枚举，新增Title枚举不会被误送宗教动作路径。

实现只编译一次进入共享`xar_ck3_12002_runtime`，各生产navigation消费者沿原链接关系使用它。独立fixture另行编译同一helper。持久门禁在`rite-confirmation-sdk.yml`中覆盖生产bridge／runtime、UI与registry、独立Title测试、真实C++ wire，以及分进程的实际SDK primitive→service→MCP链。不得以手写JSON或仅单测替代真实serializer输入。

集成时SDK整模块77项通过；两份生产叶与测试整叶的完整指定mypy命令通过。最初13项存量生产类型错误及首次测试依赖解析失败保留，局部使用Mapping／None运行时窄化修正，没有Any、cast或ignore。原生构建、真实wire链和实机当前均待实际执行。研究候选、源补丁与初始失败位于 `C:/ck3-dynastic-esotericism-20261024/resume-product-a20/core-a29-administration/title-observer-candidate-a01/`；新源使用独立构建及资格索引，不热改Native05或runtime19。

该能力只补实际窗口身份观测。两枚帝国的正常取得、无领袖后合法恢复、继承、纹章与冷加载仍按产品测试矩阵分别验收，不能用本查询的静态通过代替。
