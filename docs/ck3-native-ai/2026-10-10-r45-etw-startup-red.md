# R0045：900秒启动失败、ETW观测与实际闭场

本轮未完成加载，未注入、未进入业务步骤，全产品仍为 NOT_GREEN。工作进度估算维持75%，不表示验收覆盖率。本报告记录本轮原始失败、独立观测与其后的实际清场；原host汇总缺项和旧分析失败均保留。

冻结源码为 `fde5fb0a03d24ba00b8a09ce0a52462a50882671`，沿用 Source05、正式71文件加诊断 overlay6文件、原 seed、debug/delayed injection 开关和900秒 readiness。没有调整本轮预算、重放业务动作或使用失败世界作为新 seed。

public run于03:33:20.600317至03:48:25.157520Z返回2。native-report保留 RED、1374项启动观察、native frames0、steps0、session错误906.434秒、`cleanup_ok=false`和`session.report=null`。未出现 Setup completion，未调用原 contained injector；verify返回2。原 allocation进程返回0，只证明分配成功。

独立观察句柄记录CK3 PID16528于03:48:44.263007Z退出1，观察耗时904.963866秒；原 host Popen7036于03:48:46.634948Z退出1。该观察句柄不是 CreateProcess原句柄，原 Job最终计数未知，不能补记 typed正常退出0。ROOT随后 closeout返回0：当前CK3与相关进程清点及control残留为空，直接审阅11:49的Steam离线原图，桌面恢复1024×768。keeper原进程退出0，FINAL为thread_exited=true、failure=null、last_sequence4358；原CAS实际4358→4359，任务DONE、resources=[]。当前清场事实不改写原host汇总的cleanupfalse。

实际ETW使用本轮独立instance，五个xperf导出及最终own status均返回0，外层于03:58:02.736483Z结束。tracestats记录03:43:43.3489677至03:45:12.4547080Z，真实时长89.1057403秒，lost buffers/events均0。等待采样60秒、own-stop命令95.507秒和trace时长分别记录。ETL为1,103,101,952B；约10GB dumper及process/profile/stack正文留在外置原路径。归档复用实际已有pins，不再次读取或hash这些正文。synthetic CPU proof与实际CK3 trace分列，前者不授本轮语义或业务信用。

004分析器于04:19:56.543007Z完成首次完整单pass，匹配439548条SampledProfile，125个目标线程身份中51个有匹配样本。另2条TID17252样本分别超出记录的线程end 5179/8049微秒，隔离为UNKNOWN，不进入热点资格。原始Stack正文统计明确SKIPPED，attached-stack覆盖率NULL；官方stack.txt独立保留，未取得完整用户栈。模块样本Count：ck3.exe184762、ntoskrnl.exe106155、D3DCompiler_47.dll80542、ntdll.dll31021、nvwgf2umx10022、ucrt9741。CK3最热RVA0x3f91ed9为59290样本、0x3f91f8f为49837；线程角色和函数语义均UNKNOWN。官方profile Weight与样本Count单位不等同，Usage%使用系统分母。

002首次分析在432793字节附近遇到非UTF8信息字段而失败，GetACP936/mbcs严格解码亦失败，不能声称全局ANSI。003采用ASCII关键字段加非ASCII byte escapes后，仍因线程生命周期不匹配于04:12:05Z、446.66秒后失败，没有完整dumper SHA或资格结果。004保留严格生命周期关联，只将两条不匹配样本隔离，原始每行参与SHA；首次完整流式生成的dumper pin为10098403170B / `a3ce7977583cdcf0793aa4e2724d83842b91ad1162164b82020d7e2ee9ab58a7`。两旧RED、四版源码及原执行回执纳入小证据链。归档不再读或hash该大正文。CPU热点、D3D活动、缓存mtime与导出成功只证明并存活动，不证明加载死锁、前台原因或业务成功；根因仍UNKNOWN。

新shader-cache元数据记录R45为3523文件/135,508,874B，R44为3687/143,124,020B，R38历史为3740/146,942,067B。R45有804项birth/mtime位于[600,900)秒，最后892.7068074秒，109项位于[840,900)。与R38同名且长度相同的3511项仅是元数据相同；没有缓存正文比对、命中或编译完成证明，也没有预热或复制缓存。新小原件纳入归档，旧R38正文证明不重复打包。新鲜R38 stat清点仍为3740文件/146942067B，名称、大小和mtime均与原元数据相同；窄查42源码、68实际argv和7份prepare记录未找到清理这些cache的证据，但全局“从未删除”、历史delete-and-recreate及正文一致性仍UNKNOWN。新建profile未复制旧cache与删除已有cache是不同事实。

精确fde CI的Official38020302422与Linear38020302413均SUCCESS，Official内shared acceptance SUCCESS；LYD工作流NOT_TRIGGERED。这些是源码CI结果，不改变本轮startup RED和业务未执行事实。

ROOT在释放后以四条有记录的本地Git identity操作读回 `XenoAmess <xenoamess@gmail.com>`。2026-09-10日报line223已固定此身份；此前本地Codex配置解释当时选用值，但谁或何时改变配置UNKNOWN，ROOT承认提交前未核查。历史R44作者、提交及原证据不改写。首次错误`--task-id` poll仅有direct-tool退出2的对话观察，没有原始记录目录；更正`--task --ack`退出0、cursor4349按其真实来源记录，不制造失败原件或重跑命令。

当前归档见[acceptance索引](acceptance/2026-10-10-r45-etw-startup-red/README.md)、[实际事实](acceptance/2026-10-10-r45-etw-startup-red/FACTS.actual.json)与[原件清单](acceptance/2026-10-10-r45-etw-startup-red/INDEX.json)。同目录保留RAW-EVIDENCE.zip、VALIDATION及producer源码。91MB seed、ETL、dumper、二进制、缓存正文和旧source ZIP继续只保留外置引用。归档CRC/member/bytes与小原件SHA检查见实际VALIDATION；没有新增启动、SDK、屏幕操作或业务资格。

本包与外置原件是当前诊断的保全与引用，不承诺永久可读；后续按仓库retention政策实行有期限管理。已有实际路径名及历史证据不因本次措辞调整而改写。


## 2026-10-10 派生正文可用性勘误

05:08:02.907437Z，实际 `etw-cpu-001/dumper.txt`（10,098,403,170 B；历史 SHA-256 `a3ce7977583cdcf0793aa4e2724d83842b91ad1162164b82020d7e2ee9ab58a7`）已按明确授权删除，路径已确认 absent；05:08:03.071381Z，同批 synthetic `offline-stack-001/one-dumper/events.csv`（1,092,354,095 B；历史 SHA-256 `3beff29c91464316402540b84d311bf99399cec2b5d510249993cb55840fccc0`）亦已删除。上文“dumper正文留在外置原路径”记录的是原归档时状态；这些路径现在只有历史身份和 tombstone，不能再视为当前可读正文。

本次保留两原 ETL，实际打开 READ_DATA 成功且 size/mtime/native identity 有据，没有重新读取或 hash ETL/大文本；已校验摘要、源码和原导出命令回执保留，可在新的容量准入后从 ETL 重建。现有 process/profile/官方 stack 不在本次清理目标内。首次完整分析与原 RED 不改，startup 根因 UNKNOWN、业务 NOT_GREEN 不变。两项精确路径、原 ETL、删除时间、容量及 INDEX/RESULT/TOMBSTONES pins 见[清理记录](../maintenance/storage-cleanup-2026-10-10.md)。
