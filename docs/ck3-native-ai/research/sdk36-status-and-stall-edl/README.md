# SDK36 状态连续性与停顿编辑元数据

机器：`xenoamess-full-tower-eb9d2c1186`。第十一 `1af385fc` 的
[Official39003837013](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39003837013)
及Linear39003836974均已实际success。本包仅收小源码、必要字段投影与
[来源索引](SOURCE-PINS.json)，没有复制Driver、SAVE、录像或2.78MB完整AUTO。

## 原故障和当前故障分别绑定

[transfer](../../../../tools/g2_saved_campaign/runtime_repair_sdk_transfer.py)
保留原349、原停止时间和source binding；新SDK readiness只表示修复已应用。
只有新namespace的已结算TURN、配对AUTO／MET及精确存活双进程身份才能表示恢复。
原19／20是实际首推进，12603只作查找提示；后续计数再大也不能将晚到badge当停顿终点。
公开模块采用正常相对import，不在导入时修改v5全局proof。

[自动应用识别](../../../../tools/g2_saved_campaign/runtime_repair_auto_applied.py)
只认当前已审核的campaign-root preflight `state_changed`恢复合同：原HALT／原AUTO／
控制／audit／fresh SEM均绑定，0业务／无重放／同日期。控制1876及SEM1877只进入
waiting-for-progress；从13510开始顺序检查小TURN，13510–13525均零日期，完全不读其AUTO。
真实首正向AUTO1911／MET1912在04:47:06.511988Z闭合+216 raw／9日，不是1876的ACK。
专用clock外封上限4MiB、decoded body上限2MiB，普通core的1MiB上限保持；
私有e7a注释曾误写64KiB，归档原件不改，此处勘误。
大外封测试使用真实必要字段加明确synthetic padding，没有伪称原包字节。

旧watcher32513已实际exit1。后来又有录制历史指针和旧FULL重开误报4b／0c；Root已撤回，
撤回不等于恢复、不加计数、`EDL_wait_interval_allowed=false`。
[当前故障守卫](../../../../tools/g2_saved_campaign/runtime_repair_current_fault_guard.py)
要求当前匹配pending或当前精确stopped FULL，按原HALT／AUTO pin、SDK／Game代去重；
一轮有界terminal迁移后使用内存索引。
[录制守卫](../../../../tools/g2_saved_campaign/runtime_repair_recording_guard.py)
要求当前pending或明确operator-stopped证据，保留公共晚到HALT／feeder／stop刷新修复。
Root／录制owner报告498b watcher47641已启动；这不是新公开源码的持续健康或全故障验收。

Root此前确认窗口31失败12日／12597周期，SDK35正常0/0退出；SDK36窗口32随后准入，
基线53484792／12603。较新协调截点报告383日和采集健康，同Game／录像保持，
不是公共整理者读取可变ledger所得实时值。失败窗口不累计，连续30年稳定优先，
其后<1秒／日、0.5秒／日，均未达；近期45秒约2.58秒／日也只作历史小样本。

## 通用算法在独立仓，项目只接元数据

通用纯时间轴算法已普通提交到独立
[promo12ecaf98](https://github.com/XenoAmess/xar_promo_toolchain/commit/12ecaf9891e2685299002c5d2f2484f2f3acc67f)，
[v0.3.0正式Release](https://github.com/XenoAmess/xar_promo_toolchain/releases/tag/v0.3.0)
经既有[打包流水线39005285835](https://github.com/XenoAmess/xar_promo_toolchain/actions/runs/39005285835)通过。
正常／`-O`各275项、各2skip；wheel194037B，SHA
`f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`，
资产digest与SHA256SUMS实际一致，独立验证venv完成version／help／plan-help。
主仓精确依赖同步，现有live解释器未升级，也没有vendoring通用实现。

主仓[CK3 receipt adapter](../../../../tools/ck3_stall_edl.py)、
[collector](../../../../tools/collect_stall_edl.py)与
[启动hook](../../../../tools/ck3_recording_stall_hook.py)负责项目绑定。
未来正式`game_decision`录制在actual started.json之后自动请求一个hidden元数据子进程；
game_only显式不适用。metadata依赖／启动失败另存，不能请求停止既有录像。
采集cleanup仅写该writer自己的STOP，不控制Game／OBS，不把child PID ACK写成健康。
当前私有provider及collector35452未由本包修改，未来hook仍是离线资格。

默认策略头尾各2秒、中段快进最多4秒，overlay保留，无任意倍率上限。
CURRENT先保存不可变精确快照，再供EDL引用；SDK同号请求不会合并不同namespace等待。
晚到修复提示是独立marker；已闭真实等待不能被重启后的新incident覆盖。
误报撤回仅留下marker／排除对应false区间，不伪造推进终点，不压缩其正常画面。

所有偏移仍是wallclock估算。原私有qualified_render_plan仅检查边界ID和pin存在，
未完整绑定exact EDL／录制source／mapping／pixel review；
[原候选](edl/qualified_render_plan.unbound-candidate.py)仅保研究，不作为正式编码入口。
最终执行仍需真实PTS边界、精确素材／mapping绑定、人工像素复验、全部source关闭和新鲜渲染容量。
本包没有encoder调用或成片验收；元数据算法发布不等于影片完成。

## Family 源码修正及研究边界

公共Service仅修一行未定义`submit_step`：同帧Native已认定合法且child focus确实缺席时，
选择既有`private-select-child-education-focus-v1`。3项生产方法测试包含非法／已有focus／
disabled守卫，规划不提交动作；未声称当前游戏已给孩子设置focus。

SDK35两日期后30日技术负缓存的[完整窄研究patch](family/service-sdk35-research.patch)及
[helper](family/family_focus_definition_negative_v1.research.py)另存，未接入正式import或部署。
它保留`education_definition_missing`／native_legal null，不修Native定义查找、不给业务信用。
研究patch已包含同一latent单行；其base是38f715，不能在已修公共Service盲目重复apply。

## 新局交接与公开成片目标

用户最新决定：修复收口后从1066罗贝尔书签重开干净局，重新录制、重新运行完整普通规划器。
录制至少从主菜单开始；公开视频标题为《罗贝尔的三十年》，采用伪一镜到底呈现，
异常或智能体重启的阻塞中段严格少于5秒，默认快进到4秒，并保留错误原因和修复提示。
头尾各2秒是上下文保留，4秒指中段，不能把两者混称整个停顿只剩4秒。

旧局carry37计划取消，尚未据此现场drain；已准备Source37、技术缓存和focus-present修复
可作为源码复用，但新局不继承旧战果、推进天数、Driver状态或goal计数。
旧局945日等历史进展不算新局成绩。主菜单录制不要求已经存在地图、actor或SDK；
公开hook在actual started／Game与overlay代匹配后请求收集，CURRENT尚不存在时等待。
Root独占现场，新campaign／pre-menu录制资格另行保全；本批未启动新局或改动D2。

最终真实PTS、像素校准与渲染归独立promo工具链；v0.3.0此次发布的是纯EDL算法，
尚未授予最终影片编码或像素验收。D盘录制不设置session／segment时长或文件大小上限。
目标仍为先稳定连续30年，再低于1秒／日，最后0.5秒／日，均未达成。

## 本批验证

正式CI对应三个修改入口已本地执行：录制77项／45子例、状态61项／44子例、
Family与既有可选检查36项／2子例，共174项／91子例通过；精确依赖loader另1项通过。
小回执见[最终入口测试](PUBLIC-FINAL-STATUS-CAPTURE-CHECKS.json)。
准备中错误类名导入及首次CI多行命令提取错误已在提交前纠正，未修改现场或制造业务通过。
Family36项是修正提取后的完整入口实际结果；不是早期误执行3项的替代宣称。
