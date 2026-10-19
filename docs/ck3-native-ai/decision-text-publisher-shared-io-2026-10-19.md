# 决策文本 publisher 的 Windows 共享 I/O 修复

2026-10-19。实际机器为 `xenoamess-full-tower-eb9d2c1186`，身份于 `2026-10-19T06:34:02Z` 用 `tools/ck3_live_run_id.py machine` 重新读回。源码、定向测试和实际回执的精确 pins 见[配套证据](evidence/p51-c6-shared-io-2026-10-19.json)。本专题只记录该机器的观察，不外推其他机器或后续长期稳定性。

## 实际故障

C5 publisher 在 `2026-10-19T06:14:15.202945Z` 读取 `decision-text-publisher-c5/CURRENT-INPUT.json` 时，经 `run:314 → read:28 → Path.open('rb')` 抛出 `PermissionError: [Errno 13]`。该子进程是 PID `187296`、birth `134368630096239765`。它的 `CLOSED.json` 保留 `normal_STOP_observed=false`；没有 `OWNER-CLOSED.json`，原 owner 的实际退出为 1。这与此前文本目标 `os.replace` 的 WinError 5 是不同入口，不能用旧的文本替换修复宣称已覆盖本次读取。

当时 AUTO285 的选项 3 已执行，MET286 的原始结果也已成功返回；286 的不可变显示投影已经生成，但缺少对应 `TEXT_PUBLISHED`。它们均未重发。原始故障、输入、285/286 原件及 ACK 状态已冻结到外置 `p51-c5-current-input-read-review01`，原 attempt、源码和回执保留，未用成功回执覆盖失败历史。

实际占用句柄、ACL 或其他拒绝来源仍为 **unknown**。本地显式读锁能复现冲突，不足以认定实际占用者是 OBS、Defender 或某个 Python reader。

## 共享入口和预算

[publisher](../../tools/g2_saved_campaign/decision_text_publisher.py) 的 `read`、`pin`、`checked` 和 `read_text_binding` 共用读取入口。Windows 以 `GENERIC_READ`、`FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE`、`OPEN_EXISTING` 打开，立即读取有限字节并关闭；句柄转为 Python descriptor 失败时同样关闭。微软文档说明 delete-sharing 允许后继请求删除权限，涵盖删除和重命名；它不保证所有原子替换在 reader 仍持有句柄时都成功。[CreateFileW 规范](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)。

`checked` 只读一次原始字节，并对同一份字节核路径、长度、SHA-256 后再解析 JSON，避免分别 hash 和 parse 两次读取。损坏 JSON、来源不符、缺失文件等仍报真实错误，不作为锁冲突无限重试。

读取及原子 metadata 发布仅对 Windows WinError 5/32/33，或未携带 winerror 的实际 PermissionError/Errno13 做有限重试。每项最多 8 次，读取和 metadata 的局部等待上限为 0.5 秒。文本替换仍仅重试 WinError 5，局部上限为 2 秒。临时文件、内容和发布身份在重试间保持不变；create-only 的同名占用仍拒绝，永久拒绝最终抛出原错误。

同一次父侧 callback/ACK 等待及子侧单个 input 处理分别共用 **4 秒 deadline**，嵌套调用只取更早 deadline，不重置累计预算。父侧配置的 5 秒 ACK 上界保留，实际等待还受该 4 秒预算约束；计时从验证和 enqueue 之前开始，晚到 ACK 不能被当作本次提交许可。启动等非 publication 操作仍有各自有限局部预算，4 秒不是整个进程的寿命限制。

文本完整原子替换成功后才写真实 `TEXT_PUBLISHED`，Service 的 before-submit hook 仍在消费真实 ACK 后才允许原生 dispatch。重试成功只证明 I/O 完成，不证明事件收益、原生动作完成或 OBS 已绘制。

[API 模板](../../tools/g2_saved_campaign/migrate_p51_decision_text_v20261019.py) 对 `SHARED_IO_RETRY_VERSION==1` 直接使用新 publisher 的共享 I/O，避免旧的仅 `CURRENT-INPUT` 父侧 wrapper 覆盖新实现；旧 wrapper 仅留给旧版 source。C6 采用独立源码、API、state、text、STARTED 和录制 UUID，未热改 C5 文件或冒用旧进程绑定。

## 已完成验证

共 10 项定向用例分别通过：

| 范围 | 项数 | 证据内容 |
| --- | ---: | --- |
| 共享 I/O | 5 | 真实 Windows 独占读锁释放后恢复；实际 delete-sharing 和及时关闭；metadata 同 temp/bytes 遇真实锁后恢复；生产 parent wait 与本地 publisher 线程产生真实文本/ACK；永久拒绝、损坏 JSON、同 raw 校验及累计 4 秒预算 |
| 文本替换 | 3 | 真实 Win5 锁释放后成功；永久 Win5 有界且保旧文本；其他错误不重试 |
| 多 callback | 2 | 独立 ordinal/source 与同 decision 拒绝不变；真实 feed 变换范围保留 |

这些用例不启动 CK3、OBS 或 SDK。锁释放 Timer 从首次真实失败后才启动。publisher 线程使用显式 qualification-only 配置；另两份 C6 namespace/owner AST 夹具明确使用本地 fake ACK，只授源码接线资格。

新增测试的 Windows CI 单命令：

```text
python -B -X utf8 tools/g2_saved_campaign/test_decision_text_shared_io.py
```

当前 `static-ci.yml` 的 Windows job 已有 `test_decision_text*.py` discovery，可发现新文件。无需重复矩阵或新增 Native 调用。

## MET286 的实际恢复

C6 同 Game `153556`、birth `134368602545256920`，新 publisher 为 PID `179008`、birth `134368649316828418`，实际采用源码 SHA `38438b9b50896e8050f6c864c78a11291750a33bd7d0f73a5e0bde0130008bbe`。

新 owner 先核 MET286 原始响应及既有投影的精确 SHA，再调用新 publisher 的 `wait_text_published`；未另造投影、倒退共享 current request 或重取 MET。新 ACK 的时间为 `06:28:51.930951Z`，早于新 OBS UUID `e6f643ea-3404-446b-ae18-6b75cb9d682a` 的 `06:29:00.258469Z` 启动回执。实际回执 `ROOT-MET286-TEXT-PUBLICATION-RECOVERED-C6.json`、新 TEXTACK 和 OBS started 已独立核 pin 并冻结，详见配套 JSON。

这授予原 MET286 投影在新 generation 的真实文本发布事实，不授予新事件结果、像素准入或后续普通循环成绩。实际恢复是否命中过临时锁重试仍为 unknown；永久失败仍保留真实停止诊断。
