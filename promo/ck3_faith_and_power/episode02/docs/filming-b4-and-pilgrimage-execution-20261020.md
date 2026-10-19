# D1实拍诊断与普通朝圣执行入口

本页本地事实属于 `machine_id: 4-8e1c2f1861`，观察截至 `2026-10-19T21:44:00Z`（北京时间10月20日05:44）。B4原件在 `C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b4-a01`，后续冷构建独立位于 `production-b5-a01`；其他机器不能复用本页的安装、离线、容量或实机资格。

## 实拍取得的结果

公共受管场次 `4-8e1c2f1861--faith-engine--R0002` 真实恢复D1原档。原生首帧人物31254、日期53144328、暂停、无事件；三项后续查询均成功。当前Faith为天主教13、Rite为0，礼仪和主流礼仪的领袖均为人物30490，宗教领袖头衔4；当前主办朝圣活动为0。当前决议列表有31行，`create_hof_decision` 匹配0行，返回 `requested_decision_key_not_in_actual_rows`。因此未选择该决议、未获取建制报价、未确认建立领袖，也没有朝圣Start或日推进。

宗教查询同时实际读到普通朝圣可规划、五个候选地点及各自路线。默认活动报价为70—110金币，明确不含旅费；当前钱包243金币。它证明可继续施工普通朝圣流程，不证明全包价、扣款或已出发。

新录制[27.900秒上下文原片](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b4-a01/captures/d1-existing-head-context-a01/raw-gameplay.mkv)为30,480,935 B，SHA `504f8b529868382be433d3a8b33d7383153e9140858d24efa996bd43b2ac3d44`。录制器和ffprobe退出0，2560×1440、H.264、单视频轨；30/1标头不能认证CFR。直接审阅的原图为暂停地图与右侧决议列表，下中部有地图tooltip遮挡，单图未见退役蓝窗；未作整段clean认证。它只作为已有领袖起点／诊断素材，不能冒充新建制或朝圣完成。原生结果和媒体精确索引见[媒体摘要](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b4-a01/media-review-a01/SUMMARY.actual.json)。

## 辅助脚本失败与正常关场

D1 adapter在取得实际snapshot后，延迟导入 `xar_autoplayer` 失败。此前17项测试预先增加包路径，未覆盖真实父进程入口。原公共case退出2和 `ModuleNotFoundError` 原样保留；原生查询成功、native host GREEN和正常退出均不能授予case业务PASS。

新修复从公共manifest已绑定的共享source加载真实opening contract，核对模块来源并恢复临时路径；依赖失败也保全首帧拒绝回执。当前仓库实际以 `-I` 隔离运行真实 `Selection.load_adapter → adapter.run_case` 的7项测试，以及原17项测试，全部通过。原版隔离复现、修复中间RED和最终候选保存在 `production-b3-a01/native/qualifications/next-scene-plan-a02/d1-adapter-import-fix-a01`。这是入口修复的离线资格，尚未通过后继实机。

本场使用原生normal Quit GUI回调：独立读回退出自动保存为false，Root直接审阅未勾选原图，再一次提交退出桌面并独立观察原进程exit0。原native host实际结束、cleanup完成，`normal_close_qualified=true`；原公共run仍退出2保留业务错误。录制器树清空、原keeper退出0，最后按CAS释放序号12397；缺少CLI SHA的首次释放拒绝另存，没有改写。新鲜窗口位移与像素差证明闭场采集有效，Root直接审阅Steam离线；桌面恢复原1024×768。总回执为[本场闭环](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b4-a01/EXECUTION-CLOSURE.actual.json)，SHA `f399fa4c7a2f711307df175e757bb6d8c2474aacbc5e5fa187acc4759b77fc8c`。

## 普通朝圣执行候选及下一门槛

三路研究已组合为专用普通pious朝圣流程：原生opener／stage1、单phase目的地、当前配置完整十资源费用、最终CanStart、一次Start与独立完整活动身份后验。完整费用通过GetCost的原生分解按实际资源索引读取；旧分项aggregate仅作诊断，不能当总价。Start前同帧双重报价检查并保留原生可负担判断，未知提交结果不重复。活动身份消失不推断旅程完成，抵达、奖励、结束和归返仍需实际观测。

独立编译gate默认关闭，Read身份查询与执行权限分开。公共case必须显式 `opt_in_player_pilgrimage_execution=true`，同时声明planner query／submit两工具；参数经真实父子host传到Driver后才注册。只读声明、旧宴会权限或现有身份查询不能提升执行权限。

Root在B4游戏、host、录制及keeper全部关闭并释放后才应用候选。应用后的实际检查为：planner transport／真实MCP20项、真实公共host转发14项、D1入口7项及原17项、媒体integration原58项及新增3项真实回执登记消费者，均退出0、无skip；MCP拒绝非法参数的日志属于预期负例。新Python脚本补UTF-8 BOM。[实际执行汇总](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/ROOT-APPLIED-TESTS.actual.json)保留命令与输出出处。C++源码候选尚不能算生产DLL或游戏执行通过。

`production-b5-a01/ADMISSION.json` 于 `21:38:26Z` 获新的768MiB冷构建硬额、704MiB停线额。已独立封存原423ce的5,006份必要源码后，B5单独应用候选，Root同步处理文档和后续case。`21:45:30Z`明确修订同一额度内的profile，首次编译前开启现有ItemActions／Outcome，供后继领袖决议使用；两gate没有增加生产TU，确认关闭窗口仍不算新领袖业务成功。`21:46:06Z`完成重配置，随后已启动实际冷编译；另一路编写真实Confirm回调的有限夹具。全部峰值计入同卷项目容量；重归档出现旧／新大库并存前须停线重算，不借用已闭B3额度。新DLL、真实packet消费者与后继实机是下一门槛，不能用本轮软件测试代替朝圣全过程。

## 派生文件回收与期限

此前B2、B3已过时的精确 `.obj`／`.lib` 共1,386份、逻辑703,285,990 B已按逐文件计划回收；这些原件现在不可读取。保留源码pin、生成输入、配方、构建／失败日志、DLL、EXE、packet和资格回执，下一次需要冷构建，不保证逐字节重现旧链接结果。删除清单与实际结果在 `production-b3-a01/native/qualifications/reclaim-plan-a01/EXECUTION.actual.json`。这是对较早“完整构建树保留”的当前可用性补注，不改写当时构建成功。

样片640MiB未来媒体预留已关闭，改按实际约80.2MB计入，未来媒体写入0；B4重写入已闭，实际约340MB计入。B5新准入的保守项目上界50,693,568,747 B，小于本机有效额51,177,672,294 B；本机当次可用112,125,607,936 B。统一采用[存储策略](../../../../docs/storage-retention-policy.md)，没有自动预留部署声明。当前样片、原片、DLL和代表故障按活跃用途限期保护，七天内复核，不无限保留历史中间件。

`21:54Z`闭场细分补注：B4非视频实际309,519,128 B，比原256MiB子额多41,083,672 B（约39.18MiB），虽然整包约340MB没有超过768MiB总额，子额超支仍如实记为 `OVER_NONRAW_SUBALLOCATION`。主要是实际生成的约155MB shadercache、约69MB恢复存档和约54MB传输日志；实际555对MCP还包含恢复等待和后台流量，不能以少量业务步骤估算全流量。Root停止该包重写入，后继须按实际闭场占用、可重建闭场副本的精确回收及新raw／nonraw分额重新准入，不能借总额改写旧子额通过。来源为 [B4容量后检](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b4-a01/STORAGE-POSTCHECK.actual.json)和[后继估计](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b4-a01/media-review-a02/B6-ESTIMATE.actual.json)；估计本身没有授权下一场写入。

同机 `21:52:09Z` 已用现有open_kaishek CLI对实际 `pilgrimage.txt` 与包含HoF决议的 `pam_decisions.txt` 作通用lossless parse，均退出0、零diagnostic、roundTrip=true。实际本地source HEAD为 `2b559966c72f4e845111e3e15652ae2354aaed57`；既有CLI JAR独立SHA绑定，但其build commit未知。现有语义profile仅1.19.0.6，本次仅语法结构子集，1.20.0.4条件／效果、C++ABI、GUI、付款和后验均不适用，不能代替实机。[预验回执与完整命令](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/open-kaishek-e02-a01/ASSESSMENT.actual.json)。
