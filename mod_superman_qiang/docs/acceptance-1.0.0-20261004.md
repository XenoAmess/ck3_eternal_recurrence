# 《超人强》1.0.0 实机验收汇总

**L1–L3 实机验收 GREEN。正式 tag 对应构建、公开发布、订阅缓存与最终 changelog 仍 pending，不能据此宣布已发布。**

2026-10-04，本机 Steam CK3 1.20.0.3/build 25652598，简体中文，A0004 production 22 文件。已完成 42 项核心矩阵、正负百分比、原始基础数组/账本/真实保存倍率、正常玩家及非玩家查看、百万 holder hover、真正退出重载、无模组旧存档中途加入、干净玩法截图和反向离开两个账本边界。

产品运行输入 source `2873141e76177f52e218aa7da05e75cbdd312fc1`，manifest SHA `63b0bc75a4c13bfdb343d77d621617eb425c204af081f00658454b193f261aac`，EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。后续文档/工具提交不改变该受验收的22个运行文件；正式构建还需绑定最终tag并逐文件证明等价。

详细报告：[R0009/R0010](live-R0009-and-R0010.md)、[R0011](live-R0011.md)、[R0012–R0014](live-R0012-R0014.md)。完整机器结果、每个gate原文和SHA在[汇总JSON](acceptance-1.0.0-20261004.json)，原始MCP请求/响应、保存文件、melt、角色原始块、截图、stdio与实际输入的逐文件SHA在[永久原件索引](acceptance-1.0.0-20261004.raw-index.json)。

## 计划逐项映射

| ID | 状态与实际证据 | Gate |
| --- | --- | --- |
| L1-01 | GREEN；真实A4+夹具加载与A4-only中文旧档；R13最终error.log0B；其他轮未知formatter噪声原样保留；不称全局日志零错误 | `r9 / existing_save` |
| L1-02 | GREEN；原版两个hook实际执行且只计一次；原版memory/stress保全 | `r9` |
| L1-03 | GREEN；A4-only普通旧档正常肖像交互与原图；无夹具 | `existing_save` |
| L2-01 | GREEN；未初始化0/0→1/1，tie无转移 | `r9` |
| L2-02 | GREEN；前经验赢家真实selector、同项paired ledger ±1；R14另实际10/3→11/4；R9受控无百分比技能±1；R14有效值受边界钳制 | `r9 / reverse_xp` |
| L2-03 | GREEN；低经验发起，吸取方向仍由先前经验决定 | `r9` |
| L2-04 | GREEN；非零相同经验各+1，无属性转移 | `r9` |
| L2-05 | GREEN；6生产helper各实测；真实selector多样本/多技能结果；每次最多同项1点；有限样本不证明分布；等权静态检查另有L0 | `r9 / reverse_boundary` |
| L2-06 | GREEN；来源基础0+正修正可贡献；接收者面板0能收；原base不变 | `r9 / reverse_xp` |
| L2-07 | GREEN；receiver/donor -50%与+50%、取整0或2、上下钳制；raw ledger/scale守恒；不把面板未变化误作原始修正未转移 | `r9 / positive_and_control / reverse_xp` |
| L2-08 | GREEN；六项无法转移仍双方经验+1 | `r9` |
| L2-09 | GREEN；16/17岁、自身、死者拒绝；死者真实level2 base独立读回 | `r9` |
| L2-10 | GREEN；AI/AI和玩家/AI真实经验与ledger方向 | `r9` |
| L2-11 | GREEN；匿名只计已知合格角色，无属性转移 | `r9` |
| L2-12 | GREEN；同日两次真实pair各+2、两次paired ledger原始点守恒 | `r9` |
| L2-13 | GREEN；show_as_tooltip不写XP；no_sex_memory真实hook仍计一次且无sex memory | `r9` |
| L2-14 | GREEN；99/100/101、1000001、安全max/max-1固定点整数读回与重载 | `r9 / reload` |
| L2-15 | GREEN；原版lustful压力下降、had_sex memory与禁用memory行为保全；概率性怀孕结果未视为必定发生 | `r9` |
| L2-16 | GREEN；合法最后一点至±百万、at-limit跳过、真pair/selector相反方向离开两边界；六helper静态共享边界合同；native极值以外交实测 | `r9 / reverse_boundary / reverse_xp / reload` |
| L2-17 | GREEN；正负成长/翻转/回零；variable-only实际old scale1，rebuild两次唯一scale3 | `r9 / positive_and_control / rebuild` |
| L3-01 | GREEN；未初始化NPC0及真正旧档自身0；base/traits/sxad fields无写入 | `readonly / trait_readonly / existing_save` |
| L3-02 | GREEN；正常root1001、NPC0、million holder1000001各目标准确；holder hover1000001；采用不同真实计数，不为3/10示例额外造UI角色 | `readonly` |
| L3-03 | GREEN；三正常目标查看和holder hover后127角色SXAD/base/rawscale零变化 | `readonly / trait_readonly` |
| L3-04 | GREEN；退出真实load_save_name重载127角色XP/base/ledger/rawscale保持及正常有效值UI | `reload` |
| L3-05 | GREEN；真正enabled_mods=[]旧档→A4-only载入默认0；无反推；原版首事件计数另组合R9；R13没有发生性行为，后续首次计数由R9未初始化hook矩阵组合证明 | `existing_save / r9` |
| L3-06 | GREEN；R13真实中文A4-only普通旧档干净原图+完整frame JPEG发布素材；仅证明可用于发布，未宣称Steam媒体已公开 | `existing_save` |

每个 Gate 名对应汇总 JSON 的 `gates` 项，包含原始绝对路径、bytes、SHA-256 与真实结果全文。经验最大值 `92,233,720,368,547`、百万经验、正负百万账本通过真实整数保存及重载，不依赖浮点格式化推断。六项基础数组与modifier实际保存的multiplier均独立核对。

## L0 与正式发布门

| ID | 当前状态 | 证据 |
| --- | --- | --- |
| L0-01 | 候选GREEN，原版两个effect窄投影及source SHA | static-validation、A0004 manifest与来源报告 |
| L0-02 | 候选GREEN，18+/存活/顺序/AI/匿名/只读规则 | static-validation，加本轮真实scope/计数/只读 |
| L0-03 | 候选GREEN，变量默认0、经验max、账本±百万、holder作用域 | 静态+R9/R10/R13/R14保存及UI |
| L0-04 | 候选GREEN，六同项成对ledger/等权/方向bound，无base写入 | 六helper、随机样本、R11/R14真实base/scale |
| L0-05 | 候选GREEN，九语token/编码/语法及资产 | 非中文仅format-certified；中文本轮原图 |
| L0-06 | 候选GREEN，allowlist/无夹具/内descriptor无ID | A0004正式树22files；R13仅production加载 |
| L0-07 | 候选双构建GREEN；最终tag绑定产物PENDING | release执行者完成tag与最终等价校验后补 |

候选完整报告见 [静态验收](static-validation-2026-10-04.md)、[账本构建](build-validation-2026-10-04-ledger.md)、[A0004本地化构建](build-validation-2026-10-04-query-localization.md)。GitHub官方CI只证明L0；本报告L1–L3来自本机实际游戏。

## 原图、异常和收尾

R13仅A4、真正普通旧档、正常查看XP0的[原图](../../images/superman_qiang_gameplay_experience.png) SHA `dbb4b4085b775fcc93b9b2a1f13de82a2a6f4b562886f4409356a0561450e5cf`；fullframe JPEG SHA `d0d0adbaf28445d0aa1ced1de5351374337c6921a67919a9743bbf2dbb2eaa8d`，见[媒体来源](../../workshop/superman_qiang_screenshots.md)。执行者和root直接审图、独立保存只读gate通过。夹具人物和人工计数图不用于工坊media。

R9真实未知formatter27条、R11后续日历未知formatter121条原文与时间组保留，不把“无sxad primary”称成已证明原版来源；R12只复现pam:9254原版错误。R13正常production-only最终error.log0B。R6基础漏点产品RED、R7显示缺行RED及其他失败attempt均保留，未改写。

R14最初原生pause受原版故事modal阻塞，保留失效consumer和wrapper exit1；同PID恢复后实际暂停并保存，独立机制/基础/scale/XP通过。正常故事选择前未调用typed event-choice，记录MCP-first流程偏差，没有补造能力拒绝。

全部游戏完整进程树已清理，watchdog absent，tasklist/ToolHelp库存空；屏幕keeper停止无failure，真实CAS释放4108→4109，state done/resources=[]。执行者未切在线或上传，发布阶段可领取独占屏幕。

不声明多人、移除模组、成就或其他版本通过；不以有限样本证明随机分布。L3-05由真正旧档启用默认0/只读与R9未初始化原版首计数组合证明，R13本身未发生性行为。历史DLL编译stdio保全缺口见环境报告。
