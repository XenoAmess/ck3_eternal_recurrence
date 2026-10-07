# R0024：合法签署通过，建宗教头衔后继承保护失败

CK3 1.20.0.4/build25734779，加载 clean source `e0e017da1ad84eea9cf623728d38d29d55d8bbdf`；运行 `bf-202609141645-5434332d4d--li-yu-dao--R0024`。正式四项批准和单次 factory 已实际执行，但五个政治头衔的继承人数组及角色继承候选改变，整体保持 **NOT_GREEN**。新头衔不获得冷载或争统信用。

本轮从 R23 的真实撤回存档（91,670,781 B，SHA `5501caf084a7cc6058c63d5b540e54dd2770596a51184f340a36aa0e593205fe`）冷载；首次独立保护87项全TRUE。原0240仅作比较，不重复首轮或重置NPC票。第二轮 serial2 的NPC65865投反对票，2票1赞成，未满足逐派三分之二；依法撤回。第三轮 serial3/nonce6 自然获得2票2赞成，玩家代表410、受影响人类412、学者411、最终签署413分别由实际 query→select 回调证明；独立 B3 证书状态为 `FORMAL_NATIVE_CALLBACK_SAVED_MANDATE_PASS`，qualification_pass=true。传统STATE中的空信用没有回填；新增独立证书明确区分。

第三轮签署后的保存和原生名册读回87项全TRUE。实际新的430查询随后仅一次提交，原生G3及独立保存证明新宗教Title18373、Faith107、holder31254，4项属性为TRUE且有temporal_head_of_faith_succession_law；实际结果事件431。这个fresh R24新建对象即使整数与旧失败分支相同，也不借用旧generation或旧资格。

B4共88项：原87保护加允许的Faith factory变化。Faith附加检查TRUE、钱包/历史/HoR169/政治holder稳定；原政治2230、2231、2235、2262、2264完整AST保护FALSE，actor完整受保护landed投影FALSE。薄字段比较证明五个Title只在heir数组变化，actor只在succession数组从45项变为27项；realm_laws字段已经恢复。删除的18名候选中10人仍属Faith107，当前证据不能归因于单一same-faith过滤。生产检查器按88项判断，计数不是拒绝原因。B4作者正常执行0但业务检查RED，独立资格保持UNKNOWN/pass NULL；没有B5成功、newT冷载或NPC授予，没有第二factory或HoR维修。

第二轮待审事件430的提交按钮在NPC反对时仍由native读成shown/enabled TRUE；ROOT随后保存独立核对并明确更正最初判断，未按错误按钮继续提交。修复候选把完整准入条件从custom_description移至option trigger顶层，保留原tooltip和隐藏commit guard。另一最小候选把原same-faith临时法清理块从Title law之后移到resolve之后、law之前。该顺序只是待实机验证的假设，.4当前没有中间milestone观测，未声称唯一engine根因，不重放heir或放宽AST。候选源码验证不能改变本轮RED。

最后失败现场保存 `live-attempt-024/checkpoints/R3-final-protection-RED/checkpoint.ck3`，91,676,695 B，SHA `d0051a105e2b9eb99bf90c624ad0423c9f3683426d1993aa5713328befcf8fff`。第二轮撤回保存 `checkpoints/R2-withdrawn/checkpoint.ck3`，91,671,419 B，SHA `3b1f6e9326780f7c95a3ddf85f5d2346c7d7ac6c194524081ce6e5363da21bdb`；这是无HoF的后续合法续跑输入，不能用失败factory场景充当新基线。所有存档原件外置永久保留，本次入库不再解析正文。

新版正常退出绑定实际通过：prepare、continue各执行一次，异步待确认后仅新query读取，不重放claim；最终confirm_desktop一次、observe证明typed_normal_exit_observed=true/process_exit_observed=true/exit_code0，autosave_verified=false。外部独立保存的原game HANDLE也wait0/exit0；原Client与keeper HANDLE及原执行全部exit0，停止keeper FINAL3706后CAS3707释放，postrelease census无游戏/所有六个原owned进程，无读取异常。最终Steam原图2:12 Oct8直接审阅“离线模式”，窗口位移与新pixels/hash证明新鲜，未改变Steam模式。

e0e官方Official CI与Linear CI已SUCCESS，LiYu工作流按路径未触发，不写成通过；native code build和5项focused通过，Defender实际登记环境RED单列。首Client前景准入失败和关闭、错decision key/工具名的本地拒绝、optional numeric hook只接受430导致413窗口作者RED、unsupported正常退出参数派生、所有原始失败和partial都保留。413作者已完成一次保存正文解析后才在optional hook失败，没有重读正文来改成GREEN；后继签署B3是独立新的保存和真实全部回调证书。

`INDEX.json`与`raw-evidence.zip`保全实际请求、原生/SDK字节、保存STATE/保护、证书、所有正常关闭边界及定点诊断候选。下一轮以修后新clean HEAD/export/build/profile及当次离线/排他准入，从真实无HoF撤回状态继续新轮；依次满足合法B3、B4全部88、B5及cold保护，才把该新T交给同Faith NPC65865并执行C3。I4关键及代表高风险、自然到期、清理/冷载随后继续；军会/圣物未实现，朝代分隔二期，Workshop未发布。
