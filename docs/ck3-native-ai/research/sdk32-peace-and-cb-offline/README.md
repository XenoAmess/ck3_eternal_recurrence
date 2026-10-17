# SDK32 的两份有限离线报告

机器 `xenoamess-full-tower-eb9d2c1186`。这里只保存四份原始小报告／清单和精确 [pins](SOURCE-PINS.json)；原始 Driver、完整 history、视频和 CB 逆向窗口仍在外置场次目录，不进入 Git。原报告中“SDK32 正在运行”是各自研究截点的记录；之后窗口27实际在1824日失败，SDK32已正常0/0退出，Game／OBS保留，见[最新交接](../../../handover/2026-10-17-p27-native21-continuation.md)。

[和平段分析](peace/FINDINGS.md)及[固定范围 JSON](peace/P32-PEACE-5MIN.json)覆盖完成回执738至1017、2026-10-16T21:05:52.516662Z至21:10:52.428643Z：299.911981秒／288游戏日＝1.041361秒／日，含3次真实SAVE。该范围的相邻间隙未见调试长停顿，全部推进为speed5、空战争列表；不代表整场均速、战时速度或已低于1秒。阶段存在嵌套，不能把完整推进、内部等待、规划、持久化直接相加。此包没有部署性能候选。

[CB actor前置研究](cb/REPORT.md)及[原始外置manifest](cb/MANIFEST.json)记录原研究截点：当时type+48 loader的源码字段映射尚未闭合；下文Loader02补记已静态闭合这一窄缺口，29项脚本候选仍不是已启用白名单。原调用必须保持false,false及完整保留目标评价；actor-root不等于actor-only，group规则仍读defender，claim继续wide。1,110,468次既有调用／1.8726934秒只表示历史P23机会规模，不是已节省量或当前秒／日收益。没有生产patch、构建、部署或新实机验收。

CB manifest仍列完整外置研究输入；本目录只归档REPORT与manifest，未冒称全部原件已便携化。候选源码绑定缺口没有因入库自动消失。稳定连续30年优先，其后低于1秒／日、再0.5秒／日，均未达。

Loader02 follow-up: [report](cb/LOADER02-REPORT.md), [manifest](cb/LOADER02-MANIFEST.json), and [14 static checks](cb/LOADER02-STATIC-RESULT.json) now close the source-field mapping. The original registry row is {int32 token, pad32, name*}; the old locator read the next row ID after the name. There is no token-minus-one conversion. Same-build table/parser/RTTI evidence maps allowed_for 0x2B0F to type+0x48, allowed_against 0x2B15 to +0x1E8, and display 0x3114 to +0x118. The earlier REPORT remains the historical failed locator, explicitly superseded on this narrow gap. No Native execution, bool shadow, pruning deployment or measured saving follows from these static checks.
