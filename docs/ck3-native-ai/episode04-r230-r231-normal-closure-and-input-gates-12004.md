# R230/R231：普通 Save、拍摄准备与失败后的正常闭场

2026-10-21 UTC；machine_id: `desktop-3fevhd2-1c74096080`。这是来源明确的执行知识与研究源码归档，不是新场动作授权。原证据的实际观察时间、完整路径、字节数、SHA 和仓库映射见[来源索引](evidence/episode04-r230-r231-closure-20261021/SOURCE-INDEX.actual-a01.json)；[当前快照](evidence/episode04-r230-r231-closure-20261021/CURRENT-SNAPSHOT.actual-a01.json)是出版者从原件生成的投影，不冒充 owner 原回执。

## 两场发生了什么

| 场次 | 业务结果与原退出码 | 后续闭场 |
| --- | --- | --- |
| R230 | 本场实际/请求各15日、rich2、Move0；累计113日、rich6、Move1。加速尾段缺少实际 camera-start，原 hot1、public2 保留；没有正常驻留拍摄日、Arm 或 Start | 17:51:17Z owner 确认普通 Save、正常 GUI 退出、retained OS0/native0/host0、keeper0/allocator0，screen 已释放 |
| R231 | 600秒相机准备窗口到期，在新 rich/claim/Start/Arm 前拒止。新增 day/request/rich/Move/Arm/Start/Hot 全0；原 public2 保留 | 19:23:02Z owner 确认普通 Save、正常 GUI 退出、retained OS0/native0/host0、keeper0/allocator0，screen CAS8002 完成 |

R230 原错误是 `No actual camera-start signal; natural action not submitted`，见[原 stderr](evidence/episode04-r230-r231-closure-20261021/r230/hot-original-stderr.actual.txt)。R231 原错误是 `Bounded camera preparation expired; no rich/claim/Start/Arm consumed`。其[原 stdout 无损 gzip](evidence/episode04-r230-r231-closure-20261021/r231/public-original-stdout.actual.txt.gz)解开后必须是23,833字节、SHA `02fa5306b237251137e12c63f749e3f90bc161cc50203c7cae40f59c19ef54b7`；它保留原 `RED_OR_INCOMPLETE` 和 `case_error`，不能用正常关闭改写为业务成功。

原 [R230 owner](evidence/episode04-r230-r231-closure-20261021/r230/OWNER-CLOSED.actual-a01.json)与 [R231 owner](evidence/episode04-r230-r231-closure-20261021/r231/OWNER-CLOSED.actual-a01.json)分别绑定各自的原 public、allocator、keeper 和正常关闭证据。两场收尾时仍是 actor31254、date_raw53149608、Army18在2624、route为空。R231继承累计113实际/请求日、rich6、Move1，没有把继承计数当作本场新增。

formal仍8/11、B0/2、ABC0/3；正常闭场不增加 R08、增长点或完整镜头信用。普通 Save 的文件事实也不确认 oneLife persistence。R230/R231 的约74MB Save 只保留原证明中的精确 pin，出版者没有重读、重哈希或复制其文件体；小证据入库不续期保护大存档，也不证明其今后一直可读。

## 下一位游玩智能体怎样使用

先分清输入继承、当次观测、业务提交、拍摄及资源退出。旧 rich 可以提供有限路线线索，不能冒充新场、同一 actor/Army、当前日期和局面下的新 native snapshot。前场 Move1、113天或 rich6 不能再次消费为新动作。遇到已知失败或未知提交，先保留原结果，按实际原 owner 的正常收尾路径退出，不重发旧动作。

相机准备必须在有限窗口里取得当次真实像素、正确游戏窗口与 Root 审阅。R17 源码的 capture 新鲜度是180秒，Root review 是120秒；准备最多600秒，并且要给实际 hold/hard deadline 留足配置中的916秒后续尾段。审批或截图过期就拒止；暂停地图、等待截图或源单元检查通过都不会延长 hold，更不会制造 camera Start。Root 的画面审阅还须随后重新核 native snapshot，元数据校验不能替代所需的真实图审。

正常退出是一条独立证据链。Save 原 response、独立 native before/after、物化文件 path/size/SHA/date 与实际 owner 身份需要按各自合同绑定；Save 时的 checkpoint proof 不能事后填入尚未发生的 GUI 退出。后来实际正常 GUI 操作、retained 原句柄 OS0、native finished/thread/cleanup、host 原 wait 与 screen release 分别保留，不能用一个 ACK 或新包装器退出码替代。

## R17 源码可复用到哪里

本包保留三份小型研究原件：[normal_saved_source.py](evidence/episode04-r230-r231-closure-20261021/r17-source/normal_saved_source.py)、[site_preparation.py](evidence/episode04-r230-r231-closure-20261021/r17-source/site_preparation.py)、[prepared_b_sites.py](evidence/episode04-r230-r231-closure-20261021/r17-source/prepared_b_sites.py)。它们分别说明普通 Save 输入、准备审阅与有限 B-site 路径怎样接起来；原 [source freeze](evidence/episode04-r230-r231-closure-20261021/r17-source/SOURCE-FREEZE.actual-a01.json)、[Root 源码采用](evidence/episode04-r230-r231-closure-20261021/r17-source/ROOT-R17-SOURCE-ADOPTION.actual-a01.json)及两个原 wait 一起保存。

R17 最终 focused 的4个方法及6个新/改源 strict 检查实际原 wait0；它们没有运行游戏、SDK、录制或 FFmpeg，合成的审阅/capture fixture 不提供真实图审信用。旧失败 strict 的路径和 pin 仍在原 freeze，不能把后来的通过追记为旧 attempt 当时已过。当前包没有重跑这些检查。

这些模块依赖冻结的外部旧 C/D 源、实际输入和机器路径。`public_normal_entry.py` 这份机器 bootstrap、检查源码及完整 runtime 只作原路径/pin引用，没有被安装为通用公共能力；runtime freeze 的 SHA 也不等于把整个展开 import 闭包装进本包。不要直接运行归档源码。应用到未来标准入口前，运行 owner 必须重新绑定实际代码闭包、机器、源 Save、PID/birth/gen/pipe、日期、余量和所需权限。

R231 raw owner 已有 `all_scene_writers_zero:true`、`source_writers_zero:true`、`game_writers_zero:true` 与 `future_scene_writes:0`，但没有旧 normal validator 需要的整数 `all_scene_author_writers:0`。R18 的[显式兼容投影](evidence/episode04-r230-r231-closure-20261021/r18-source/R0231-OWNER-CLOSED.projection.actual-a01.json)保留全部原字段与原件 pin，仅增加该整数0、schema和来源说明；消费端须逐原字段核等。它没有把 `new_R0231_counts` 的整数0改成布尔，也没有新增 OS 观察或改写原 public2；不能称为已部署到 R17。R18 的新源、cache、实际启动和业务结果属于独立后继，本包没有消费其新的 launch/业务原件。

## 当前入口与未闭边界

这些文件可供其它游玩智能体显式查询和参考，普通 planner 不自动加载，不新增通用路由或任何 Game/SDK/拍摄授权。当前 R05/R08/R10、B 两个增长点及 ABC 三方案仍按各自原证据判断；不得从新解释、源检查或正常闭场推成已完成。

上一已发表 `6f5ede548df75f8c9cd69f8497b0c891ca79aeda` 的 [Official CI 39610492374](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39610492374)已于14:17:30Z记录 completed/success，static job于14:17:27Z完成。出版者在14:23:11Z仅只读一次取回终态，依据为会话工具 transcript `672fb9` exit0；这里明确是该观察的派生记录，没有伪造单独的原 Popen 回执，也不作为后继提交的 CI 结果。
