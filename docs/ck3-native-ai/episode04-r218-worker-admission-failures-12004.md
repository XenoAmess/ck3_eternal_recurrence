# R218：两次 worker 准入失败与下一次线程预算

`machine_id: desktop-3fevhd2-1c74096080`。本场是公共运行 R0214，实际运行源码 `ba3528fc04621529ed528930623b5d34826a46a4`，a37 编译来源 `bc4604bed4eb8558b3f4e0e554a642aa69a4ba2f`；普通战役的原生 episode 保持 null。以下是 2026-10-19 UTC 的已发生事实，不能用后来的源码、容量或新 N 追授本场。

| attempt | 实际停止点 | 结果与恢复 |
| --- | --- | --- |
| a01 | 完整 selected army packet 编码为 19,814,013 B，超过原 2 MiB 输入上限，尚未启动 worker | 0 day、ADD false；独立 OFF/clear、Save。terminal 的 `native_restore_verified=false` 保留，不能改写为已有原生 observer 恢复证明 |
| a02 | observer 已实际武装 64 个线程代际，第 65 次 ownership 请求触发不可变的 `maximum_owned_threads_exceeded` | observer exit1，READY false，0 hit、0 day、ADD false；原生 DR 清理、detach、actor restore 与独立 OFF/clear、Save 均有小原件 |

这两次失败均发生在月界自然日之前，不能据此判定月界补员不发生。a03 对 selected prepare packet 的 32 MiB 例外是另行授权的输入边界修正；普通 metadata 上限、完整 legacy Core 4 MiB、目标物理 proof 与原全局闭包未放宽。不得把修正源码本身算作 a01 的成功重放。

[a01 terminal](evidence/episode04-r218-worker-admission-failures-12004/attempt1-terminal.actual.json) · [packet 边界来源](evidence/episode04-r218-worker-admission-failures-12004/attempt1-packet-bound-source.actual.json) · [a02 原生根因](evidence/episode04-r218-worker-admission-failures-12004/attempt2-native-thread-budget.actual.json) · [原始 observer 逐行记录](evidence/episode04-r218-worker-admission-failures-12004/attempt2/observer.raw.ndjson)

下一次应先测什么：

1. 对新的实际 PID 和 creation FILETIME 做三次完整 OS 线程代际 metadata census，保存实际 owner PID、线程 creation FILETIME、完整性、出生与退休；核对进程 FILETIME 前后一致。数值 TID 不代表同一代线程。OS census 不证明 debugger 已拥有这些线程。
2. Root 根据实际代际并集和明确的正 birth reserve 选择新 `N<=256`；新 admission 前再取第四次 metadata。任何部分结果、未知代际或超过现 producer 的 256 上限都在 DR/day 前停止。点采样不能保证未来无 churn，原生上限仍须实际执行。
3. 新场、新授权、新 admission 绑定实际进程、模块、容量、构建与冷测来源；不改旧 max64 回执，不丢弃“不像 worker”的线程，也不复用历史 worker TID。现有 1..256 参数范围不等于任何新值已实机验收。
4. 严格次序仍为 fresh 月界/q/position gate → 唯一 launch → **实际 READY** → 原有最多一个 exact day → 原始父/目标物理证据与同次 carrier join → restore → OFF/clear/Save。不能因两个准入失败而降低 ADD 闭包或重发结果未知的动作。

[下一线程合同的历史 source receipt](evidence/episode04-r218-worker-admission-failures-12004/next-thread-census-contract.source.json)只封来源和合成检查；此知识包没有把外置 `worker_next.py` 安装成公共运行 API，也没有执行 census、DR、SDK 或新一天。

本场后来正常闭场：Root 在 03:41 UTC 直接审原版退出确认框并正常 GUI Quit；retained OS0、native process0、Job0、tree gone 和 cleanup proven 由 [normal-close](evidence/episode04-r218-worker-admission-failures-12004/close/normal-close-result.actual.json)保全。原 public session73348 和 allocator17974 的实际 wait0 分别保留；keeper last6834、线程结束，Root CAS **6835** 于 03:52:32 UTC done/resources[]。Root [闭场森林](evidence/episode04-r218-worker-admission-failures-12004/close/closed-owned-forest.actual.json)另记原 host0；业务 RED 与正常释放分开，不使用后续 Steam 维护的 CAS6852 代替。

88.2 秒窗口原片只在来源机器引用，未复制。H.264 1280×720/30 fps 完整单线程解码通过；三张稀疏帧均为 Mar31/Army6679，没有 ArmyWindow、supply 或日期过渡。[技术 QA](evidence/episode04-r218-worker-admission-failures-12004/media/media-qa.actual.json)与[后续 AI 稀疏审阅](evidence/episode04-r218-worker-admission-failures-12004/media/sparse-visual-review.actual.json)分列；不授连续 clean、人类1×、正式动态或补员资格。

研究10/14、业务7/11、正式动态0/11、ABC0/3 均不增加；R06 ADD 与 R04 仍未闭。[小原件与可移机校验入口](evidence/episode04-r218-worker-admission-failures-12004/source-index.json)只核记录完整性，不能在另一机器追认安装、权限、进程或实机状态。
