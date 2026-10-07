# 本机 CK3 更新、仓库快进与原任务续接（2026-10-07）

用户要求“CK3更新→本机repo更新→继续任务”的前两步已有实际结果，Steam已恢复离线；原任务进入新版身份与资格绑定主线。新Steam安装 build **25734779**，最终manifest `StateFlags=4` / `UpdateResult=0`，下载5,362,624/5,362,624 B、staging101,041,657/101,041,657 B完成。新EXE **101,040,248 B** / SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；manifest4239 B/SHA `cae2d24d0f7c77a177c26e72931c24393847f5023d697196ca6bfc81a5e9e576`。EXE与build匹配已登记的1.20.0.4 adapter；**公共游戏运行版本显示尚未新启动观测**，新R20、运行GREEN和正式能力信用仍NULL。

旧 R19 先取得[实际关闭边界](../li-yu-dao/acceptance/2026-10-07-r0019-465595b-closed-055142/CLOSED-AND-UPGRADE-HANDOFF-20261007-055142.md)：typed正常退出、原game/helper句柄及原EXEC完成0、CAS3570释放、fresh census为空。旧 source465与各失败/恢复/业务NOT_GREEN记录保留，不能外推为新版验收。安装前原EXE和appmanifest保全于外置 `installed-before-update/`；旧build25652598、旧EXE101,039,736 B/SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。BEFORE937 B/SHA `15086d27d462f7c60c72e80ef6acf46d3ffbc6336f1dfc924d69179e7059e00e` 中 `game_file_version=1.0.0.0` 是generic PE FileVersion，不能作为CK3公共patch号；本证据包只登记EXE原件身份，不把二进制或保存正文入Git。

ROOT实际主树已由 `465595b67efa8f72dfc97bc0de218302c75e3bfd` 快进至 `cee18726fe159d4f4629b37e04e4bad0349b3859`，FINAL `git status` stdout为空。06:14:29的原远端回读已是 `ca13dff195c7fbab08fd71b48ae6197de5448b0f`；主树更新成功与并发远端继续推进分别保留，不能把那一刻写成HEAD/REMOTE相同。本文件在独立文档树正常追远端交付，后续主树同步和新版绑定由ROOT执行。

Steam最终离线证明来自 `final-offline-frame-001/probe-1/steam-moved.png` 原图1920×1080及位移新像素，ROOT直接审阅底部“离线模式”、画面时钟14:11（2026/10/7）。原review898 B/SHA `958e975b6d843a02dd2a6035668e7bf5ba72deb77fb0d86f96b1a01308b7ad94` 记录 `offline_confirmed=true`。自动freshness receipt只证明窗口变化，其 `offline_status_observed` / `clock_check` 仍NULL，离线判定由独立直阅完成。更新任务FINAL RELEASE的原stdout证明CAS **3575**、done/resources=[]；回执中的git465是任务登记时的保留上下文，最终主树实际HEAD由上述独立git回执证明。

过程失败保持原样：首次登记因lowercase CLI SHA pin在写入前拒绝，不是已证明的screen owner冲突；改为精确uppercase pin后登记成功。旧default D:/bus导致恢复失败，后继使用本机实际bus。旧HWND语义动作只有invoke ACK、无离线postcondition；mouse001参数拒绝未触发输入，mouse002实际按source/live1920×1080、preview[0,0,1920,1080]、observed[134,59]映射到screen[134,59]，同样不能证明离线。mouse002 `--receipt` 的现存原件是PNG；mapping JSON仅在原工具输出中，外置原文件NULL。最后新Steam HWND24511660/popup16581844语义进入离线模式，仍由随后新像素直阅证明业务结果。必要原receipt保存在ZIP，完整过程目录保留外置，未将每次只读控件列表搬入正文。

ROOT `finish_update` 原直接工具调用exit0 / wall2.5784866 / chunk a013d6是对话中的实际执行事实，原工具结果未外置，文件引用明确NULL；FINAL已有UPDATE-AND-GIT、HEAD/REMOTE/STATUS及释放实际subprocess原件，不能伪造另一份工具wrapper。[事实对象](../li-yu-dao/acceptance/2026-10-07-local-update-build25734779/FACTS.actual.json)、[原件SHA与ZIP清单](../li-yu-dao/acceptance/2026-10-07-local-update-build25734779/INVENTORY.json)保存必要小JSON、manifest、原stdio与最终离线PNG。

既有75%是工作量估计，属于计划进度；10/7晚I3B/cold、10/8 C3、10/9 I4均为估计，受新版实际资格/绑定迁移及正式NPC自然投票批准影响。节点估计在新版实际资格后再评估。下载完成、Git更新及离线恢复不提供formal/new T/C3/I4或产品GREEN。本归档作者未修改主树，未操作SDK/CK3/屏幕/进程/总线，也未重新跑CI、测试或构建。
