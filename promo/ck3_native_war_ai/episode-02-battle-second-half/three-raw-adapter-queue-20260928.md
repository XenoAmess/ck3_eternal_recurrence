# 第 2 集三条既有 raw 的 adapter 后续队列

2026-09-28 E2-05 正占 `ck3-screen` 时，只读了既有小型 `recorder-final.json`、marks、PTS
审计和取样说明。机器清单为 [three-raw-adapter-queue-20260928.json](three-raw-adapter-queue-20260928.json)。
本轮**没有读取、重新哈希、转码或复制任何 GB 级 raw**，也未生成 clean span、人工审阅或正式
adapter bundle。表内 raw SHA 是原 recorder 的历史回执值，并非本轮重验值。所有操作命令留给
E2-05 受管录制结束、`ck3-screen` 释放且机器负载空闲之后串行执行。

| 源 | 原 raw / ffprobe 大小 | 小报告机器状态 | 拟用内容 |
| --- | ---: | --- | --- |
| E2-02/03 A01 a01 | 1,304,900,034 / 15,439,959 bytes | 16,247 帧，0–599.967 s，无 >0.2 s PTS gap；`PTS_CONTINUOUS_UNREVIEWED` | 第 27–29 日上下文，**无第 31/32 日** |
| E2-09 A05 a01 | 951,186,809 / 16,086,455 bytes | 16,934 帧，最大 gap 0.067 s；`ENCODED_UNREVIEWED` | WarID4 前态、第 27→28 日 |
| E2-09 A05 a02 | 840,210,967 / 15,730,950 bytes | 16,560 帧；7.566/0.767/0.467 s 三处大 gap；`ENCODED_UNREVIEWED` | 第 28–32 日、writer 和 WarID4 后态 |

来源：A01 的 `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-02-03-live-20260928-a01/pts-audit-a01/pts-audit.json` 与
[稀疏视觉索引](a01-a02-sparse-visual-index-20260928.md)；A05 的
`D:/ck3-research-artifacts/episode02-a05-pts-span-verification-20260928/attempt-03/a05-pts-span-candidates.json`
（SHA `98BD4FE38B87EBC0596744303E2A4A8921E5E6AD09F0FB7D4AE8979E532D9897`）及
[`a05-machine-pts-candidates-20260928.md`](a05-machine-pts-candidates-20260928.md)。

## 只供选片的 PTS 搜索清单

| 源 | 机器候选区间，秒 | 当前可用证据与边界 |
| --- | --- | --- |
| A01 a01 | **约** 30–120、220–260、390–480 | 来自 JPEG seek 样本；首末数字**未证明为真实帧 PTS**。分别看第 27 日、第 28 日起追、第 29 日写回。 |
| A05 a01 | 245.000–270.000；350.000–450.000 | A05 attempt-03 已按完整 ffprobe 验两端存在，区间最大 gap 0.067 s；画面/来源标签尚未审。 |
| A05 a02 | 60.000–170.000；200.000–250.000；300.000–350.000；385.000–500.000 | A05 attempt-03 各窗机器最大 gap ≤0.100 s；第 32 日窗口需审 writer 与后态同源、UI 遮挡。 |
| A05 a02 | **拒绝跨越** 250–300 | 271.267–278.833 缺帧 7.566 s；另有 37.933–38.700 的 0.767 s 和 179.600–180.067 的 0.467 s，任何段不得跨越。 |

A05 a02 后态截图上方战争面板被事件弹窗覆盖；`385–500` 只证明媒体 PTS 连续，尚不满足
封装器 `no_foreign_overlay` 视觉门。审片若发现弹窗贯穿所需画面，应缩到无遮挡的真实连续区间
或另补镜头，不得勾选通过。A01 a01 的长静态面板和底部细项裁切也需按原速决定实际可用秒数。
mark 的墙钟秒和“最近视频 PTS”只用于导航，不能作为 clean span 端点。

## 屏幕释放后的执行命令

从 `D:/w/e2`（#451 worktree 已接入工具后）运行以下命令。解释器为已验证的主 worktree
`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`；独立 wheel 当前为 v0.2.1，
SHA `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`。**每个新 run
开始前仍须查询独立仓库最新正式 GitHub Release**；若更新，按 AGENTS 更新 pin/安装/帮助探测。
所有输出目录必须新建于旧 attempt 之外；下列 `-next01` 是保留建议名，若已存在则换新 suffix。
命令对原件只读，向新外置目录追加输出。

第一步：三条 raw 串行 `prepare`，每条各自生成 `PENDING_CLEAN_REVIEW` 清单。不要在 E2-05
录制期间执行；工具会逐字节重验 raw 和完整 ffprobe。

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py prepare --attempt D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-02-03-live-20260928-a01 --recorder D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-02-03-live-20260928-a01/recording-e2-02-03-a01 --output D:/workspace/ck3_native_war_ai_promo_work/e2-adapter-a01-a01-pending-next01
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py prepare --attempt D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live --recorder D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a01 --output D:/workspace/ck3_native_war_ai_promo_work/e2-adapter-a05-a01-pending-next01
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py prepare --attempt D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live --recorder D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a02 --output D:/workspace/ck3_native_war_ai_promo_work/e2-adapter-a05-a02-pending-next01
```

第二步：确定要用的区间，在完整 `ffprobe.json` 里核实**精确存在**的首末 PTS，按原速看
整条 raw（每条 600 秒）及所选区间，再对每个端点各跑一次 `extract-frame`。例如 A05 a01 的
245.000 秒首帧（其完整 ffprobe 已有机器候选确认）；另端 270.000 秒另开目录。A01 a01 的
约 220/260 秒必须先从完整 ffprobe 选出真实 PTS，不能直接套入命令。

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py extract-frame --source-manifest D:/workspace/ck3_native_war_ai_promo_work/e2-adapter-a05-a01-pending-next01/source-manifest.json --pts-seconds 245.000 --output D:/workspace/ck3_native_war_ai_promo_work/e2-adapter-a05-a01-frame-245-next01
```

第三步：真实审阅者在**抽帧完成后**为每条 raw 分别填写
[`existing-capture-adapter-bundle.md`](existing-capture-adapter-bundle.md) 的
`human-review.json` 合同，写本人、真实时间、原速全片与端点观察；不能让工具代填 true。
然后每条 raw 各开新 bundle，`package` 复制原 raw 和证据、生成三件套并实调 adapter：

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py package --source-manifest D:/workspace/ck3_native_war_ai_promo_work/e2-adapter-a05-a01-pending-next01/source-manifest.json --human-review D:/workspace/ck3_native_war_ai_promo_work/e2-adapter-a05-a01-human-review-next01.json --output D:/workspace/ck3_native_war_ai_promo_work/e2-adapter-a05-a01-bundle-next01
```

其余两条只替换 `source-manifest`、真实 review 文件和新输出目录；review 尚不存在时不能运行
`package`。adapter GREEN 仅代表显式所选段的绑定合同，成片仍须独立人工 1× 审阅与精确字节
签核。

## 资源排队预算

三条 raw 原回执共 **3,096,297,810 bytes（约 2.88 GiB）**，完整 ffprobe 共
**47,257,364 bytes（约 45 MiB）**。三个 `prepare` 各至少顺序读本条 raw 一次，仅输出小
清单；三个 `package` 会逐字节复核并复制相同 raw，至少新增约 2.88 GiB，加截图、回执、
frame PNG 和索引后预留 **4 GiB 新磁盘空间**。`package` 还会对复制的 raw 做额外哈希与
adapter 复验，实际 I/O 多于一次读取。每个 `extract-frame` 从原视频起点解码到目标帧，
以单线程串行执行；即使只取每条 raw 一个区间的两个端点，也要做 **6 次**解码。三条各
600 秒，全片原速人工观看理论下限 **30 分钟**，不含端点复查和剪辑审阅。机器时长受磁盘与
解码吞吐影响，本轮未实跑，不承诺分钟 ETA。E2-05/任何受管 CK3 或屏幕录制占用期间不启动
这些高 I/O、解码或复制步骤。
