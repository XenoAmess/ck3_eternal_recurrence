# 固定借款本金的 player-root 原生 getter 候选

`machine_id: xenoamess-full-tower-eb9d2c1186`，身份由本轮 `tools/ck3_live_run_id.py machine` 实际读回。观察时间、源码 SHA、既存缓存与指令核对见 [source contract](../../ck3_autonomous_player/native_bridge/research/holy_order_loan_principal_12004_source_contract.json)。原始 migration cache 未记录机器 ID，仍为 `unknown`；其固定字节可以用于源码研究，不能证明本机当前安装或加载状态。

新增独立 [头文件](../../ck3_autonomous_player/native_bridge/research/holy_order_loan_principal_12004.hpp) 与 [实现](../../ck3_autonomous_player/native_bridge/research/holy_order_loan_principal_12004.cpp)。入口固定为 `ReadPlayerHolyOrderLoanPrincipal12004`，只解析实际暂停且存活的玩家，原生求已加载的 `holy_order_gold_value`，返回 signed int64、Q100000 的 prospective quote。没有任意 actor、interaction scope、贷款人、决议或事件选项输入，也没有债务、付款或可花资金输出。

本轮完成的是候选源码与确定性的来源核对；没有编译、链接、执行 getter、现场 RPC 或业务验收。没有修改 Native26、冻结 SDK、Service、native_driver 或当前运行树。旧两份静态源链记录保持原 SHA，不追加或改写其 ready 状态。

## root 与 scratch 的实际 owner

不需要 clone。现有 interaction helper 接受已经准备的交互 scope；这个入口直接调用 actual `.4` `889F60`，在自己的稳定、16 字节对齐 buffer 中构造唯一 root。构造完成后才按现有原生 caller 的语义写 `WORD+0=4` 和 `QWORD+8=零扩展完整 CharacterID`。`87E0E0` 是这一 root 的唯一析构者；不同时手工释放 root vector，也不析构任何游戏持有的 definition、intern entry 或角色。

本轮实际重读了保留的完整 constructor 186B 与 destructor 126B，分别为 `8280d519…b66f2`、`878033e6…8bd43a`。构造中的 self pointer 指向这个稳定 buffer；析构先处理 `root+118`，再处理 `root+100` 与 `root+18` 的自有容器。buffer 的零初始化只是本地分配行为，不宣称原生未写的空洞均有完整 class 初始化语义。

数值 scratch 依 actual `3761680`：先 `3736040(scratch)`，再 `3735F90(scratch+128)`，借用的 root 放在 `scratch+3D0`。实际 context 是 **`{root, NULL, root, scratch, loaded_mode}`**；第二槽的 NULL 来自 `37616C6`，没有从 interaction helper 的三个相同 scope 指针推导 root-only 合法性。

释放顺序也来自同一个实际 owner：第二 vector 先 `9D7340` 清值，再重读其 data 与 allocator；allocator 的虚表 `+10` 接收 allocator/data/8。随后释放第一 vector，最后调用 root 的原生析构。每个已经取得的 owner 单独尝试一次，前一个失败不会跳过后一个。构造中断、释放异常或来源变化均不给 quote；不把局部清理未知写成已释放，也不自动重试 getter。

## 固定值调用与前后校验

factory 只接受 `.4` 精确 EXE SHA，使用现有 `.4` core、named 与 root bindings。旧 `.3` 命名的 root 类型只复用软件函数签名，没有调用 `.3` factory 或沿用其地址。

按固定 key/hash 查实际 named definition，核 primary/secondary vptr、ObDG、hash 与完整 key；构造固定 key 的 borrowed intern source descriptor，然后只调用一次原生 `37542D0`。该 wrapper 自己处理 `+70` expression/provider 与 `+7B/+68` constant 分支；没有复制旧 `.3` 的 `+7C` compiled 判断、重算旧公式或把原生0改成 unavailable。

清理之后再次核暂停玩家指针、完整 ID、local PlayerID、日期和 named database/definition/key 身份。capture epoch 仍由未来 application-main owner 提供；这组前后校验没有制造 native revision、连接代际或同帧资格。因此它尚未注册到任何 public query，也没有接入当前 consumer。

后续实际能力步是另行准入的小范围离线编译，再由未来发布的 application-main capture owner 聚合实际 frame 与同帧资格/全费用读回，最后取得真实本金读回。quote 自身始终不计入钱包；债务建立与实际到账仍须独立归属和读回，不能为观察本金先执行借款。

本轮候选三叶与本文共用既有 research 额度，硬上限64KiB，无新外置包、全局预留或构建产物；source contract 登记闭场 future write=0、process=0、allocated unknown。文档按通用策略180天复核归纳，既存 closed 包不复开。
