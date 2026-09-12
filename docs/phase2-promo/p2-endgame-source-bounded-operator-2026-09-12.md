# P2 跨周期来源：30 日有界采集 operator

日期：2026-09-12（Asia/Shanghai）

## 目的与输入

P2 四类来源中，promotion、projects、incidents 已由 schema-3 三项前缀
`0828ED6F...9644` 冻结。缺项仅为 owner-facing `zg361we.356`。旧 R357 从早期
世界线跑到 7190 日上限的 RED 继续保留，但不再作为现行施工入口。

现行入口复用 R366 的 Stage 11 临近存档 `1197A098...861A`。该存档
`date_raw=53365920`，既有实机已在 27 个游戏日后的 `53366568` 观察到真实
`.355/.356`，owner/player 为 `32904`，subject 为 `31450`。最终来源仍须在
当前 P1 产品树 `C428C42B...B5DC` 上重新实机验证，旧产品树的观察只用于确定
最短边界。

## 执行合同

`tools/zg361_phase2_endgame_source_action_cell.py` 只接受已加载、暂停、map-ready
且玩家为 owner `32904` 的会话。它把载入帧作为时间原点，将绝对截止写为
`origin + max_advance_days * 24`，并硬拒绝超过 30 日的输入。导航复用现有
production entry，目标固定为第一次真实 `zg361we.356`；进度查询按 30 日采样，
事件窗口仍逐帧识别，因此不会因每日重查慢查询扩大墙钟时间。

到达目标后，它不重新实现来源语义，而是调用既有
`capture_cross_cycle_endgame_source_checkpoint_v1`：保存 owner-facing 同帧，
复核事件 root/subject/value scopes，切换到事件绑定的 subject 查询 Workforce
成熟度，然后把第四项追加进既有三项前缀并调用 canonical registry builder。
成功输出完整 manifest、4/4 registry、保存收据和字节哈希。

`tools/zg361_phase2_endgame_source_operator_job.py` 复用现有冻结 activation、
frontend warmup、single-CK3、loader、bridge 与 canonical cleanup 生命周期。
新增的 target-side job role 为 `phase2-endgame-source`，控制只有
`status / run-source / cleanup`。activation 还必须绑定：

- 三项来源前缀的绝对路径、长度与 SHA-256；
- owner、目标 `date_raw`、不超过 30 日的游戏日上限和正的墙钟上限；
- 当前 product tree、代码 commit、输入 checkpoint、bridge、exact EXE、
  exact game version、vanilla rules、projection 与上轮 canonical cleanup。

来源 lineage 由 checkpoint SHA 与 product-tree SHA 确定，记录 product-only
mount、代码 commit、真实 CK3、无 fixture、无 console。它不含固定机器、账号或
轮次；具体路径与轮次只属于 target activation。

## 静态状态

当前状态为 `static-ready / live pending`。聚焦验证为：

- action cell：普通 `2/2`、优化 `2/2`；
- operator：普通 `2/2`、优化 `2/2`；
- 四个文件 `py_compile` 与 `git diff --check`：GREEN。

首次 no-launch preflight 保留 `source_capture_runtime_lineage_mismatch` RED：第四项
lineage 已绑定 EXE SHA，但没有提供 schema-3 前缀要求的 game version 字段；CK3
未启动。最小修正把 exact game version 与 EXE SHA 一起写入 runtime lineage，
不改变游戏输入或来源语义。

该工作包新增 Python target-side operator 与证据格式，没有修改 DLL、游戏文件、
加载顺序或产品行为。下一步只执行一次 frontend warmup 加一次 gameplay；到达
目标、出现真实 RED 或达到 30 日边界后立即停止，不扩成长跑。
