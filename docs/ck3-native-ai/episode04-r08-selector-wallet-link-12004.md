# R08：rawselector4 写址与原生余额 getter 的连接（1.20.0.4）

机器 `desktop-3fevhd2-1c74096080`，审阅基线60de49f6，exact EXE98702f88…dd518。只消费已持小原件，新增EXE读取/哈希/扫描、SDK、游戏、桌面、构建均0。源文件和实际审阅时间见[便携source](evidence/episode04-r08-selector-wallet-link-12004/source.json)。旧source机器时间仍保留，不授当前现场或跨机安装资格。

新增闭合的是**同一物理槽的读写连接**，没有补出正式币种名：

| 已持源 | 实际关系 |
| --- | --- |
| 父28F7840后段、gateway28B9950 | ADD28F7C66与selector4 SUB28B9B3C均写`[*(Character+1C0)+4A0]`；原有2BAFF30等门保持。 |
| getter28B9490 | ABI为`fn(Character*,out64*,rawselector)`，正常返回原out指针；selector4到28B954B，经context1C0读取4A0，28B955E写out。该分支没有CALL。 |
| 默认值 | Character1B0为空、selector无支持、或raw4的context为空，写out0。这个默认0不证明实际4A0为0，也不证明该角色可用/可扣该资源。 |
| 唯一已核incoming | 2BCA600在selector0或3时由2BCA61F调用getter；未持有实际传4的incoming。不能把getter存在分支称为已经观察到raw4调用。 |

原getter完整256B包含232B代码和24B跳表，table位于28B9578。旧ASM末尾的retf/xchg/imul等是误解码的表数据；原字节/旧ASM原样保留，新ASM只解232B。六项表为0→28B94CB、3→28B94DD、4→28B954B，1/2/5均→28B9569写默认0。因此“六槽按gold/prestige等顺序命名”没有证据。selector5的24C4790差值变换是另一函数的输入，不能补成这里的资源名。

raw4 getter没有2BAFF30使用资格门；读余额和原生扣减资格是两个合同。金额为signed64原值，保持负数/零。当前共享资源snapshot只正式发布已证个人gold/prestige/piety等字段；不能把resource4改名塞入这些字段。也没有依据把slot9军事率、resource4余额、NET钱包入账或local88 selector5视为同一业务单位。

下一原生入口已明确为28B9490的自然R8D==4调用，候选[once-observer接线recipe](evidence/episode04-r08-selector-wallet-link-12004/observer-candidate.json)只用于未来原始caller定位：保存真实return PC、角色/context/out身份及原函数一次返回值，再沿真实caller接到具名GetCurrency/HasBarterGoods注册。当前只有HUD `GetPlayer.GetCurrency(barter_goods)`这个独立具名目标，尚未与本getter连上；旧字符串/token邻近与零xref不补这条边。recipe未实现/未构建/未运行，不改冻结a31，不新增公共API或假动作。

Agent可复用raw4物理别名与默认值边界；正式资源名、GetCurrency callback绑定、军事已付金额、payer和cadence继续unknown。下一步不能重复读2BD36D0、24C4790或遍扫EXE；应由未来observer取得真实raw4 caller，再只读该caller的有限metadata/body。本次不增加R08整卡或动态分子。
