# Episode 04 — R197 后 native admission 与 shared-v3 focused cold

machine_id: `desktop-3fevhd2-1c74096080`；实际资格时间：`2026-10-17T09:28:49.550677+00:00`；生产源码与运行时源码：`dc031358981450ae3f8e40c6234b7f27fd4662ef`。这是一份本机生产字节和有限 cold 资格，不是其他机器的安装、Defender、生效运行或游戏业务验收。

[`source-index.json`](evidence/episode04-post-r197-native-admission-12004/source-index.json) 固定原件的原始路径、大小和 SHA-256；[`small-originals.zip`](evidence/episode04-post-r197-native-admission-12004/small-originals.zip) 压缩保留 20 份原件；用 [`verify_portable.py`](evidence/episode04-post-r197-native-admission-12004/verify_portable.py) 独立核对归档和合同。主生产资格为 42,012 B / `cdd9919fce057a6a96362dac80640a97616efde4455ac2d9dc6becddaaf15a86`，completion 为 39,026 B / `3a499072d11c0303d013576b2f50144b5d7a77cf7d6de8b770193617efd4f81d`。

- A03 主目标首次链接失败；随后 sourcefix 的受影响 19 个 object 编译并成功链接。旧 D cold 两个 EXE 虽编译，SYSTEM 因源绑定不符拒绝，不能算登记成功。
- A04 在 C root 的 6,112 B source snapshot 下实际构建并取得 SYSTEM 登记。military reinforcement admission 原生执行 exit 0，stdout 的 `no GUI/toggle claimed` 是限定条件。A04 wrapper 自身因过窄 stdout 期望 exit 1；A05 明确复用这份 admission 原件，并未再执行 admission。
- A05 的 shared-v3 normal 与 strict consumer focused cold PASS；本次只做 2 项 focused 判定、未重跑旧矩阵或全部 701 object。严格 consumer 与 synthetic producer 为源级/冷测信用。
- A05 资格明确为 `PRODUCTION_BYTES_ADMISSION_AND_SHARED_V3_COLD_VERIFIED`。`live_runtime_qualified`、`gameplay_result_qualified`、`capture_qualified`、`actual_toggle_qualified`、`natural_refill_ADD_qualified`、`R04_county_loss_positive` 均为 false。R198 此时尚未启动；研究 9/14、业务 6/11、动态 0/11、ABC 0/3 不变。

归档保留两个 Defender manifest、生产 producer、旧拒绝原件及 305,563 B cold SYSTEM receipt 的压缩原件，不在仓库展开设置列表。269,144 B main SYSTEM receipt 未复制；其精确路径、长度及 SHA-256 在原资格与 index 中，可在来源机器审验。别机须重新构建、登记并读回 SYSTEM receipt，不能复用本机成功结论。仓库入口采纳后，可在当前执行图、导演计划和研究状态各加一条指向本专题的链接，并保持 cold 与 live 的边界。
