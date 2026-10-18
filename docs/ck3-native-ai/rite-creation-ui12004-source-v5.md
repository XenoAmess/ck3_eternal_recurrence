# CK3 1.20.0.4 Rite 草稿与原版确认入口

静态来源机器 `machine_id: 4-8e1c2f1861`；观察日期 2026-10-18 UTC。精确 EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本包只复用已固定 section cache，新增 EXE 读取、整文件哈希、进程读取、游戏操作、构建均为零。实际安装 GUI 的读取时间、SHA 与必要行见三个 stock JSON。本记录不继承 1.19 或 1.20.0.3 的资格，也不证明任何 live action 成功。

## 原版调用链与最小候选

Faith 窗口原 GUI 第 1320/1364/1379 行均为 `OpenGameViewData('rite_creation', FaithWindow.GetSelectedRite)`。来源文件 SHA 为 `67924e58ccba26d95853ac48af35d91a774f5ce6d2e7f32a0a033de3b9d51521`。`AEB0F0` 复制 FaithWindow+258 的完整 Rite ID；反射 `14C7F10` 以 storage `5D1E2F8` 检查 generation，返回实际 Rite 对象。

打开仍有真实 UI gate：祖先 actions 第1307行要求 GetPlayer.IsValid 且 Rite.IsVisibleInGui；edit_rite 第1315行要求 FaithWindow.CanEditRite；create_rite 第1358行要求 CanCreateRite 且不满足 puppet_create_rite/faith 两 trigger；create_rite_puppet 第1373行取同 CanCreateRite 且满足 puppet trigger。三个按钮还必须实际 effective visible/enabled。原 opening bool(this) 分别为 `14C5B40`（selected Rite founder==当前 actor）、`14C5B90`（当前 Rite Faith==FaithWindow+E8，且 founder!=当前 actor）；这些不能用窗口内提交 fullCan 替代。typed open 的 expectmode 只能读回断言，不能强制切模式或绕过按钮 gate。

可由封闭 enum 包装既有 `AF39E0(handler, 0x3C, &Any)`。Any 为 40B：首 QWORD 是 `B19A70()` 返回的 metadata singleton `54D70E0`，其 firstQ 必须是 `base+44B9360`；其后 32B 清零并在首 DWORD 写入完整 Rite ID。COL `4A58588`、TD `5691FA0` 证明它是 `SCopyableAnyTypeInPlace<TPdxRef<CRite>,32>`，不是原始指针 Any。metadata+18 析构 `8522C0` 无操作，copy `8771F0` 只拷 DWORD，data getter `876E00` 返回内联 payload，原路径不会持有 caller 栈对象。

window primary VT `4565C40` 的 +90 是 `14F3400` SetData。该函数构造 `SRefVisitor<CRite>`；其 RTTI TD `57A5898` 包含 `CPdxAnyTypedVisitor<TPdxRef<CRite>>` 基类（TD `5513290`，偏移 8），该基类 VT `4565B70` 的 +8 是 `8747E0`：读取 payload DWORD 写入 visitor+18。metadata+50 `B1AAE0` 正是向该基类进行原版 dynamic_cast 并调用 +8。SetData 随后核 storage row/fullID+8/magic+C=`52697465`，写 window+C8 为完整来源 Rite ID、window+CC 为实际 current actor `[54DBC00]`，初始化原草稿并显示窗口。窗口 secondary VT 为 `4565C18`，handler 槽 +278，primary+90/+98 对应 SetData/MatchesData。实现继续沿既有 window owner/backlink/UI root/visible/revision 守卫，不开放 caller 指针、任意 view 字符串或 RVA。

`14F43E0` 的编辑模式判断还要求当前人物实际 Rite 等于 window+C8 且 Rite+4C0 founder 等于该人物。不能仅按请求文字认定这是编辑模式。应读回实际 actor/source/mode/visible，再暴露草稿编辑能力。

## 合法性、准备与确认

实际 `window_rite_creation.gui` SHA `9476299fdbf0975e41923eac9b192d3fe0b2cd74a4da0d928d0da7974b7ea9f8`：第 594 行 edit_faith，第 598 行 `CanEditRite && !IsObserver`，599 EditRite；607 create_faith，611 `CanCreateRite && !IsObserver`，612 CreateRite；620 reform_faith，624 同创建 guard，625 CreateRite。创建/编辑/改革可见条件不同，必须遵守实际模式。文字输入与教义选择另由 selection lane 提供，不从本入口反推已可任意写草稿。

完整 native Can 是 `bool(window*, CString* nullable)`：创建 `14F56B0`，编辑 `14F5030`。两者构造原版命令临时量并深拷贝 window+8E8 的草稿，创建调用 `29A2F40`，编辑调用 `29A2620`，同时调用 `14F8910` 名称冲突检查，结果为两者合取，最后销毁临时草稿。不能用分支查询 `2BDCA70` 代替提交或完整 Can。

准备确认是独立操作。创建反射 `14FB060` → `void CreatePrepare(window*) 14F5130`；编辑反射 `14FAED0` → `void EditPrepare(window*) 14F49C0`。两者计算原 piety quote、分配 0x138、调用确认对象构造器（创建 `14F0ED0`，编辑 `14F11B0`），再经 `C45E70(unique_ptr<GameDialog>*)` 转移所有权。准备操作没有执行写端，也不应返回提交成功。

确认对象必须从游戏自身寻找。`void* C45DF0()` 经当前 global GUI owner `[5C6A520]` 的 +10 idler 原生 dynamic_cast 获取 popup manager；实际 ingame 分支返回 cast+28。manager 的 +18 是 owned modal vector：ptr+18，capacity DWORD+20，count DWORD+24，allocator+28，entry stride8。`C45590` update 逐 entry 调 vt+8，失效则销毁、置空并压缩，证明该 vector 是活动弹窗集合；manager+8 实际是 DWORD mode，不能作为 current modal pointer。

只读有限枚举 vector，要求唯一精确类型、实际 owner 与 GUI root 同时匹配；不按队首或首个按钮选择。创建 primary VT `4565DB8`，secondary+10 `4565D98`，context+20 `4565D70`；编辑 primary `4565D10`，secondary `4565E40`，context `4565E18`。两者 +130 保存实际 RiteCreationWindow*，+70 为原 GUI root，+A8 为 closed byte。`C46470` 以 secondary=this+10 调 `B1E950` 取 root，存 secondary+60=primary+70，随后 `C466C0(root,primary,flag)` 装 GameDialog context。+78 是 GUI 构建上下文，其与全局 owner/window+98 的等式未证，不能猜。root 必须读回为当前唯一可见 `basic_confirmation_popup`，并绑定对应 modal，actorCC/sourceC8/draft 当前状态来自同一 owner frame。

原 stock `gui/shared/dialogs.gui` SHA `b83ca05ff9aab1eab38d079512c4e1a2c0154b9a8f12c0082c652ca7eef6fa16`：106 accept_button；110 GameDialog.Accept；111 CanAccept；112 GetCanAcceptBlocker；134 basic_confirmation_popup。精确源约定 `Can38` 分别为 `bool(modal*) 14F1170/14F1450`，检查所属窗口 vt+38 的可见状态并调用完整 fullCan；`Accept48` 为 `void(modal*) 14F1160/14F1440`，尾调原 writer。通用 `C46340` 的 CanAccept 实际走 vt+40，在这两个 modal 都为 `855AA0` 恒 true，故 GUI enabled 单独不能代替 fullCan。`C46400` 是有副作用的 lifetime check：Can38=false 会调 Cancel50 并置 +A8；不能当纯只读查询调用。

真正 GameDialog.Accept 反射 `C46680` → `void C46380(primaryModal*)`：调用 vt+48 后还写 modal+A8=1。候选应在同一 owner/TLS/paused/revision frame 再验证 active vector 成员、精确 VT、owner130/root70、A8==0、当前 actor/source/mode、fullCan 与 Can38，然后调用原 C46380 一次。直接调用 Accept48 会漏原关闭语义。任何异常或结果未知都不得自动重试。

## 写端与结果边界

原创建 writer `14F51B0` 与编辑 writer `14F4A40` 会先合并/更新界面草稿，再构造原命令。创建用 command VT `4770560`，编辑用 `4770498`；通过 command virtual+40 取得 owning clone，交 `37F06D0([5CC1240], &uniqueCommand, 0x0E)` 入队（14十进制，不能写成0x14）。编辑 writer 还单独再做 `29A2620`。两个原 writer 均忽略入队返回 bool，并关闭 Rite 窗口。因此“回调调用完成”“modal 消失”“窗口关闭”“队列接收”与实际教改结果是不同事实。提交后须独立读取实际人物 Faith/Rite 关系、Rite definition/fullID 与所选教义/名称等业务状态；本 lane 没有这些实机后验。

## 对规划智能体的边界

规划输入至少分开：实际 mode/actor/source；可读草稿字段及其覆盖范围；full native eligibility 和原 reason；原资源 quote；是否已准备 exact modal；是否 attempted；独立实际结果。来源失效、缺字段、Can=false、未调用、已调用但未知结果应保留不同诊断，不把静态 source-ready 写成 action-qualified。

已有 names/core/doctrines DTO **不是完整草稿 proof**。`29A1EF0..29A2124` 的真实 deep copy 除 names 外还复制：+8 CString；+28 起五组 grammar 字符串 +30/+60/+90/+C0/+F0 及 flags +50/+80/+B0/+E0/+110；四 CString +118/+138/+158/+178；四 CString +198/+1B8/+1D8/+1F8；scalars +218/+220/+228/+22C/+230/+238；+240 嵌套大 core 经 `29A2130` 深拷贝；+738 动态 vector（count+744、stride40）经 `29A85C0` 深拷贝。嵌套 core 仍包含多 vector、typed scriptvalues、颜色/图标及其它尚未逐项命名的字段。writer 又从 UI subdraft+ B28 等输入整理最终草稿。本轮不声称完整 canonical preview fingerprint；直接 hash 0x750 raw memory 含指针/allocator/padding/caches，不是语义 proof。

本轮后续已闭可实施的原命令预览路线，见 `command-preview-native-source.json`，无需枚举所有缓存字段。原 `CString* CommandText(CString* out,const CCommand*) 37F2060` 自行构造 writer、memory stream，调用原命令序列化后构造 out 并完整释放内部缓冲。输出是原文本命令表示，经过原 CR 归一化，不能称 binary bytes。按 CString+10 的明确长度复制/hash，cap+18<16取内联，否则取首指针；成功构造后任何后续失败都调用856050析构。

原无参数 owning factory 创建 `0x778` 命令：Create29A98D0、Edit29A9930；原 draft+28 大小750。共同 deleting dtor29A1EA0(cmd,1)销毁draft并释放命令；默认draft须先14F2FC0销毁，再29A1EF0原copy-construct当前草稿。只在copy成功后认定新draft构造完成，构造异常不能盲调全析构。Create写实际actor+20，Edit写实际sourceRite+20/actor+24。原factory序列化 envelope byte8、DWORD+C/+10/+14均固定0；未生成时间、随机数、request序号，type token分别固定3E66/416C。真正命令 serializer envelope37EB3A0→virtual+80（Create29A3120、Edit29A2AC0）→draft VT+8 wrapper3F7E2B0→draft actual Serialize243B710。该路线覆盖原命令payload，刻意不等于所有GUI缓存原始字节。

指纹前必须在私有 clone 上重现原 writer 的合并顺序，不能直接 hash 当前8E8。外部 tenet rows在 window778/count784/stride70，实际选中def+28；doctrine rows在790/count79C/stride48，实际选中def+28；Create按flag103A与row40跳过特定项。Create另按flag1039复制来源Faith两字符串。两mode复制来源Faith的原description getter24410A0与四字符串270/290/2B0/2D0，按14F2670→14F4DC0→14F2B50重置clone内core，再以2592720/2592500或2591A40合入来源与selected rows，14F8EF0复制ReligionType+648/+7B0，2591160重算，最后生成CommandText。完整相对偏移、先后与ABI在新增JSON。window+B28正是draft8E8+240内嵌core，不是第二个独立draft。

这些原 helper 的目标限定为native owning clone；它们不修改真实UI草稿、不入队命令。原recompute可能初始化definition缓存、分配内存或写诊断计数，不能称完全无全局副作用。规划/确认应分别在同一合法owner frame重建最终原命令文本，并绑定actual actor/source/mode、typed row内容与外部flag；实际两次同输入文本是否一致仍待授权实机资格。source-ready不能冒称这一步已live通过。

本包建议集成至 `docs/ck3-native-ai/`，能力状态保留 source-only / live pending。精确完整函数、首 32B pins（短函数完整长度）、虚表与 visitor RTTI 在 `rite-native-source.json`；图与边从同一 research-plan 生成。容量与闭场清单由 manifest 保存；保护至下一轮候选与未闭 seam 复核后按通用策略重新评估，不无限期保留过程副本。
