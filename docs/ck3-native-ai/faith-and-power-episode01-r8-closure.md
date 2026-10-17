# 第一期R8：D3保存、正常闭场与资格后继

R8的W退出和Create新建已各有独立业务后态；随后生成并冻结D3存档，完成原版GUI正常退出、独立OS0、原始run/host/keeper等待及屏幕CAS释放。公共验证仍为research holder，正式影片人审与whole-product业务验收继续单独结算。

`machine_id: 4-8e1c2f1861`；run `4-8e1c2f1861--faith-and-power--R0008`，PID21564/create1792253831.3987103，creation FILETIME134367274313987102。运行源为 `02eea1e57a44a733cb833038b55a5fdc7bd4302a`，a06 DLL SHA-256 `7a5ef6ca4eeb05c56d0f96b2ace2409bff704d067e66136f2b29dd253c3475c7`。本节直接保留来源2026-10-17 UTC事件时间；全部小原件路径、SHA、结果和观察者角色见[闭场投影](faith-and-power-episode01-r8-closure.json)。

16:36:59.703163–16:37:00.743375+00:00调用原生save checkpoint，回执checkpoint.status=saved，date51394920；16:37:38.911418+00:00的复制回执冻结为 `scenario/saves/D3-samarra-wisdom-created.ck3`，50,210,947B、SHA-256 `c6095d1dfed9b9c5df6f03e69905b16a2f365128a2ceafe7695f5ebc969c5f0a`。保存回执与复制回执的大小及来源/目标SHA一致；本次只读这些小回执，没有重新hash大存档或覆盖C2。

同一保存回执仍明确 `driver_state_replace_receipt.status=unconfirmed/save_binding_verified=false/reason=save_binding_mismatch`；attempt中保留legacy rogue_one_life默认绑定。故D3只结算“已保存文件及冻结副本”，不声称Driver状态已正确绑定、完整恢复链通过或D3冷载已验。后续恢复必须重新核实际身份/日期/钱包/站点及Driver绑定，不能用文件保存成功抵扣。

| 闭场证据 | 来源时间（2026-10-17，+00:00） | 结果 |
|---|---|---|
| 一次正常GUI confirm_desktop | 16:42:22.873125–30.821332 | native submission1；返回pending，保留句柄等候仍timeout |
| 独立observe_normal_exit | 16:42:44.947187–45.194231 | 同request及进程身份，句柄signaled、OS0、typed normal exit=true；新提交0 |
| Root正常GUI审阅记录 | 16:43:03.191826 | Root直接审阅r2-frame-20261017T164125Z.png的unchecked自动保存框 |
| public run原Popen完成 | 16:43:07.773312 | PID23124，actual_original_popen_wait=true/returncode0 |
| host原Popen观察 | 16:43:08.047259 | PID23220，actual_original_popen_wait=true/returncode0 |
| keeper报告／allocate原等待完成 | 16:43:19.888179／16:43:20.000763 | keeper actual0/thread_exited；allocate PID21704原wait0 |
| 屏幕CAS事件 | 16:43:34.062600 | sequence11495，task faith-e01-shared-a09 done/resources[] |
| public verify原进程结果 | 16:43:59.005634 | exit2，research_holder_completed=true；case/gui/business/product-release等资格false |

初次正常退出pending没有被重发；后续独立观察完成同一次退出的结算。normal-close为normal_close_qualified=true/cleanup_ok=true/business_pass=false，保留进程树清理证明。自动保存框unchecked与autosave_verified=false原样记录；手动D3保存是前述另一动作，不能混为退出自动保存已验。正常GUI审阅小原件SHA `b440fc2a9daf1f810dad1d99d1b42d6bfdee2719de66eaa322b7e8775b4fdcbb`，normal-close SHA `b529867617a19e8631e38e23d90f85992af45fafd395173029aaab1f9636cde0`。

overlay历史分别保留：第一次缺identity参数，Root直接工具返回IndexError/exit1，未创建overlay；第二次写出16:23:40.897418+00:00的旧start/PID20504后，因缺state报错，经finally close，Root工具exit1。16:24:24.335135+00:00初始化修正与16:24:24.606537+00:00的a02 start记录均另存，实际PID20780。a02工具会话10391的wait0仅由Root直接工具结果报告，三次均没有独立local original-exit文件；不补造OS等待回执，不把初始化或start记录当退出证明，也不将旧失败改成0。

三条raw的keeper原终态均为FFmpeg returncode0/NORMAL_TREE_EMPTY/job_active_processes0、probe0，分别为W-take01（86,261,191B）、creation-ui-take02（86,432,690B）、create-once-take03（61,485,536B）。Root报告QA已完成；该QA范围不在本补注重建，keeper终态仍为ENCODED_UNREVIEWED、human_review_performed=false/clean_spans_certified=false。未重hash、重解码原片，不据此宣布正式一期影片完成。

source02ee的[Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39048143772)和[Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39048143764)均有16:33:32.382198+00:00终态记录success。该记录的machine_id4-8e1c2f1861是观察者，GitHub runner_machine_id=unknown；CI不抵本机实机或产品业务资格，也不自动授予后续提交同样成绩。

局部游戏事实继续引用[W退出研究](faith-and-power-episode01-r8-abandon-12004.md)及[Create新实例研究](faith-and-power-episode01-r8-create-12004.md)。保存、闭场与CI补齐后，其未测的奉献、创建冷却、王国数量、具体受益者修正及净收益仍unknown；普通罗贝尔成绩与whole-product PASS不增加。下一规划应使用新的绑定证据恢复D3，不把失败绑定、已消耗Create意图或仍未完成人审的原片隐藏为完成项。
