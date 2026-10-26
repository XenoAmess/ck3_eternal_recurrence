# Resume63：Type2C7E860 的261字节

machine_id: `xenoamess-full-tower-eb9d2c1186`。离线观察，无Game/Steam动作。原件根 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-type2c7e860-01/`。实际 caller 是 [Base](resume63-m1-base2c7d920-result.md) 的 `2C7D9E6`：flags+4非零才传 member RCX、type RDX、collector R8；返回 AL=0只会清原Q，AL=1不会恢复已零Q。自然继承 producer仍未知。

历史 locator只作导航；当前PE全hash及已知row153800新读12 B确认 `[2C7E860,2C7E965,52B886C]`，再经两个named cache未命中才固定读261 B。PE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，base `0x140000000`；build来源合同1.20.0.4/25734779，不授loaded资格。raw SHA `a8bc757e3df1a56d454ab1e6f789f358114e1bd91d0ef95416b06f7005378f95`。Capstone/Rizin59条261 B逐VA/size/bytes相同；7branch/6direct target独算一致，12块16边、2virtual、RET `2C7E951/2C7E964`，无非call越界。未跟callee/globaldata/incoming/vtable。

- entry RDX非空且 `[RDX+E5B] != 0` 直接返回 AL=1；type为空会继续后继路径，不是直接false。这是该RF唯一显式entry type字段读取，字段正式名未知。
- `1D65640` 返回值保存为RBX，再由 `[RBX+EF0]+A90` 算出evaluator receiver。调用时RCX/member、RDX/type、R8/collector仍在寄存器，callee实际消费哪些未知。不能命名返回对象为global/type slot，也未证明它与entry type不别名。
- `9D78D0(&local20,&memberSlot)` 返回context给RDX。有collector时显式设置R8后调用 `372E4D0`；无collector时 `372DF10` 只显式设置RCX/RDX，不能把残留R8说成null第三参。两入口等价性/副作用未证。
- eval原始AL经BL保存，cleanup后TEST BL，最终 `XOR AL,AL` 或 `MOV AL,1`。正常Win64保存RBX前提下AL规范0/1；EAX/RAX高位未归一。直接写仅stack，opaque/cleanup/collector效果仍未知，不授pure。

这闭合了raw字段/地址来源和返回消费，未闭type loader→命名slot→join/persistent。Java继续保留来源与UNKNOWN，不新造已知资格字段，也不能把整个EAX当8位bool合同。

独立新300s work+60s close卡，slot1/provider1 GiB/30s、decoder256 MiB/20s，原Base4 MiB净分旧保2/新2，无删除或物理释放。decoder864ms/25243648 B；REA5474ms/Rizin592109568 B，providerclose18:25:46.402Z、service.close正常。Rizin复分析同261 B；header/hash/PE加载I/O另计，outer/joint/Job0未测。

先最小close：`CASE-CLOSED01.json`2089 B / `92f91a5ab9bef55368d60066fa56037ea7d96b8d3d833fc2be79ad117d28b1b5`，18:26:00.903Z/T0→78.256s，deadline内4个owned PID均缺席。原payload未审状态不回填。M1后继独审7160 B / `5445e3d09a5cc1e821099aadf01d3f068fb8ea4402fbcec6ed159f51c9ba9006`；富receipt11049 B / `0c70aa0689cceb34e6b980521e5336f623dd828057c361381846736af5390cb1` 在T0后576.739s落盘。准备前完整研究耗时未测，78.256s不是总研究时间。

普通plan check0，for-observation2的offline拒绝保真；无Shared/native dossier/Game资格。原件见 [sources](sources.json)。下一候选是accessor身份/loader来源；不自动采样或扩大本case。
