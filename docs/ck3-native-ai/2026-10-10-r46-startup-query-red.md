# R0046：加载后首次 campaign 查询失败，现场已闭合

本轮 public run2、verify2；产品仍 NOT_GREEN，业务没有执行。报告记录了一次真实注入及暂停地图帧，随后首次 campaign-root typed query 在进入执行器前超时。原始报告、stdout/stderr、十份观察样本和两次 release 输入失败都保留。

实际 host 绑定 `C:/csr7`、公共 runtime `20261010-006`，源码来源 `e8562cc04fae188f73c59ed33215126bb8bca7ac`，复用 native build `af20455212ed75000ba6136b3be308a9288cb06e` 的 `C:/cbr2/xar_ck3_bridge.dll`。这些与 helper 备料中的 csr6 标签分列；本包不新增编译或二进制验收。原 seed、71正式文件及6 overlay的身份由 prepared/runtime 原pins保全，没有复制其正文。

public run 原窗口为05:52:05.808148至05:58:08.446194Z，host 原Popen为PID10012。独立观察器持有CK3 PID11984/create1791611588.1719928、creation FILETIME134360851881719927。原注入准入读到462393字节日志，其SHA与最终日志对应前缀精确一致；完整 In Game 行恰从byte462393开始，因此不在当时准入payload内。R46和历史成功R38都没有另一条可声称为“最终Setup completion”的独立日志，两者只有history-loaded completion与In Game，顺序不同。这只证明准入顺序，不证明owner pump停滞的因果。

实际 injector exit0。host等待owner pump2→4后，于05:57:32.433318Z只提交一次 `ck3_query_campaign_root_context_v1`，05:58:02.488154Z返回 `timeout_cancelled_before_execution`，真实等待30.054836秒；executor_started/executed均0、pump仍4，completed_sequence1表示取消。此前约55秒是在等待owner pump推进，不能算作本次查询执行时间。Python抛错点是实际csr7 host的line828；底层为何不再进入执行器仍UNKNOWN。原report为93条 observations与309条 startup_observations，不将这些计数外推为native frame数。未选择事件、未SAVE、未推进日期。

本轮原 `cleanup_ok=true`、`managed_session_done=true`、`managed_session_thread_finished=true`，session shutdown cleanup_proven=true、Job最终active processes0。独立观察器05:58:07.706177Z记录同一CK3退出1、观察299.2961681秒；host原Popen05:58:09.031088Z退出1，observer wrapper0。它们是失败清理事实，不是typed正常退出0。06:00:20.019057Z当前清点CK3/相关case进程与controls为空，ROOT实际审阅14:00 Steam离线画面，桌面恢复1024×768×32@60；allocator原wait0、keeper thread完成。

release001缺pin、002小写pin被uppercase正则拒绝均保留；它们不表示原字节变化或CAS冲突。第三次实际成功于06:02:13.437048Z完成CAS4377→4378、DONE/resources=[]。当前闭场不会改写原业务RED，也不构成加载阻点或下一候选修复已经通过的证明。

归档见[acceptance索引](acceptance/2026-10-10-r46-startup-query-red/README.md)。实际RAW-EVIDENCE.zip为935110B，SHA-256 `de0342c9a145036162ae0cb4deb44ebd6f738bedf8a3e08f8473e6000faebded`；135个logical entries映射104份按原SHA去重的压缩对象，原逻辑18420440B。producer已一次完成CRC/member/bytes/SHA精确校验，不要求再哈希原body或重复全套测试。FACTS原命令返回码投影误读returncode而留下NULL，原件不改；新增FACTS-COMMAND-EXIT明确按实际schema的exit_code补为run2/verify2/observer0/allocator0/release0。

frozen argv、prepared大输入、源树、存档、缓存、图片、二进制与ETW正文不复制；对应实际source/runtime/prepared和图像pins留在INDEX。诊断和外置归档生产没有MAIN/Git、SDK、游戏、屏幕或新增删除动作；随后ROOT按显式清单导入7文件，见acceptance内ROOT-IMPORT。外置可用性和归档记录按retention政策有期限管理，不承诺永久保留。第一批10.42GiB派生文本清理见独立maintenance记录，不扩大删除范围。

## 闭场后采用的启动顺序候选

公共延后注入现在等待本轮完整history-loaded completion及完整In Game日志行，两者先后不限；R38与R46的真实顺序都覆盖。未写完的末行不授注入，原绝对deadline、单次注入、原生双owner帧与业务守卫保持。CPP源行号仍按原有数字格式匹配，不固定为635/583。ROOT采用后的16项针对性测试实际exit0，见[本机回执](C:/workspace/ck3_lyd_runtime_20261004/r46-root-adopted-marker-tests-20261010-001/RESULT.actual.json)。该候选尚未实机验证，不能称已修复pump停滞。

缓存匹配键只新增两项精确的启动控制例外：runtime.py及其专属延后注入测试文件；实际EXE、host/native、特性、其余源码和全部业务/配置仍严格绑定。17项缓存针对性测试实际通过，见[002回执](C:/workspace/ck3_lyd_runtime_20261004/r46-graphics-cache-launch-control-sourceonly-20261010-002/REPORT.actual.json)。算法变更后旧seed存储的key不再满足三方相等，下一场须从已闭场来源重新派生新manifest，不改旧seed或绕过校验。新Source08冻结及实机尚待执行。
