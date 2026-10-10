# R0050 I4 启动 RED 与实际闭场

完整运行 ID：`bf-202609141645-5434332d4d--li-yu-dao--R0050`，共同 keeper 为 `20261010-a12`。
此包归档2026-10-10实际启动失败及闭场；[索引](INDEX.actual.json)给出原路径、目标路径及共有的精确bytes/SHA-256。原件按字节复制，未重跑验收。

公开 `run` 于13:28:04→13:42:15 UTC返回2，`verify`返回2。实际共享host原进程退出1，native managed shutdown记录CK3退出1；这不是正常GUI关闭。启动期间campaign typed query出现 `timeout_cancelled_before_execution`，原错误完整保留在[有界投影](diagnostic/PROJECTION.actual.json)。其状态为RED，`steps=[]`、readiness及readiness_guard为NULL，adapter未进入：0次SAVE、0游戏日，修派flag初始/最终资格与自然消失均未验收。原因尚未由本包认定；投影保留先前一次cap失败及随后纠正读取的计数，没有把失败改成通过。

[host原退出](closure/host-original-process-exit.json)与[keeper父进程实际退出](closure/keeper-actual-parent-exit.json)分别保存。keeper report为exit0、failure=NULL，停止时 `screen_released=false`，不冒充随后释放。释放001错用status参数返回2；002小写CLI SHA被拒返回3；只有[003原stdout](release-command-003/stdout.log)证明正确大写pin的CAS实际释放，返回0、sequence4487、resources=[]。两个错误原输出均保留。

启动fresh001焦点错误和最终fresh001窗口边界错误保留小型原件。随后fresh002与ROOT直接审阅的最终原图descriptor分别保存，[最终离线审阅](offline/FINAL-OFFLINE-REVIEW.actual.json)明确见“离线模式”；[显示恢复](offline/display-final-evidence-restore-001.json)记录change_result0。截图仍在外置原路径，本包没有读取或复制PNG。

[4GiB预留闭合](storage/CLOSED-RESERVATION.actual.json)及[实际测量](storage/CLOSURE-MEASURE.actual.json)记录closure执行0、remaining0、已知新增保留logical278,937,819 bytes、当时free623,740,022,784 bytes。已知小计不是项目总量或历史峰值。原receipt中a11/r49及旧owner的人类描述为模板残留，原始字段不改；本次实际namespace以R0050/a12/I4及groups的实际路径为准。49,297-byte资产组清单仅留external pin，避免重复复制；未新建cache-seed-snapshot、未延长原期限，新增profile coldcache的复核仍为2026-10-17T13:06:29.278808Z。

[单次精确CI观察](ci/EXACT-CI-e34dc9f7.actual.json)只证明e34dc9f79d971df608a49ad397c257f127a70355的Official38055623143及Linear success；Li Yu Dao static checks未触发，不计成功，不外推其他HEAD或实机。

一期仍75% / NOT_GREEN。正式I3b B4/B5、新Title政治保持冷重载、C3及I4仍待完成。下一门槛为共享启动query/owner问题的最小修复发布后，沿公共入口重新准备、分配一次新run并实际取得初始资格；原R0050不重放、不授业务信用。此案例仍只观察既有冷却，不是新建完整365日周期。

本包没有游戏/SDK/进程/桌面操作，没有存档或native-report body读取。3,750,943-byte native-report仅引用原pin。小记录依通用存储策略1.0.0按record期限复核归并；旧外置原件期限不因入库而续期，未来回收应准确披露不可读，不制造同名替代。
