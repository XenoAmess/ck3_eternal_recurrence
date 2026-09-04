# B3 manager 累积候选：no-launch 冻结（2026-09-04）

状态：**GREEN_NO_LAUNCH / `static-ready-live-pending`**。本轮只构建、投影和执行 preflight，**没有启动 CK3**；因此本文不把 provider-observed 后置条件写成 live，也不把 B3 写成 complete。

机器可读冻结清单为 `phase2-b3-no-launch-attempt-2026-09-04.json`；外部同字节副本为：

`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b3-48da012-20260904-054011Z\attempt-manifest.json`

两份 SHA-256 均为 `2D9C81C42E52A651FC3B93DC00EE7A05190FD83A0B207A317DA855BC111C7E53`。

## 精确源码与原生构建

- 当前 canonical 基线：`12b2f73a401b73c7385b2a1e52a2b85c65aa9f73`；冻结工作树提交：`2968db8d93f629cdb74ca8c0ff3d1a54dc5f1d77`。attempt 目录名中的 `48da012` 是 fresh build 创建时的标签，不是最终 Git 基线声明；最终 manifest 已重新绑定 `12b2f73` 及其新增的 G2 research/docs inputs。
- exact game：CK3 `1.19.0.6`，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- native source fingerprint：`F38A16E6184A6F38198E9D1BD909238C50A5ECC14CD1DDB490C9BC7F116CFE5B`。
- bridge DLL：`2,323,456 bytes`，SHA-256 `29A5E4AE62D7F414B9CE3BC76A51F54A7D5E59AA2D80054508E31611ED7BAC0A`。
- paired injector：`39,936 bytes`，SHA-256 `74ADC3DE8EF0890BEE9F82F8D20A5AEA8AA55555B51E3C763E5FDBEF4FEFF1D8`。
- fresh native CTest：`90/90` GREEN；日志 SHA-256 `8B0C446858B872A153E1C4684567B840FCE3B91A8A13AE25D294313B9FCCD442`。

冻结清单逐文件记录 CMake、`include/`、`src/`、exact-build research/ABI、正式 runner、B3 action cell、seed contract、历史 B2 r10 closure contract、projection utility 和游戏 EXE 的路径、字节数与 SHA-256；没有以单一 commit 名替代输入账本。

## 累积 B3 production projection

历史 B2 r10 source/contract 保持不变。新的 `phase2-b3-manager-cumulative-48da012-r1` 是独立累积投影：

- `311 files / 12,568,195 bytes`；source tree SHA-256 `91475D061D84F529228D4DE07A9A7A13EF5B47DC16AD7CEB45FB0825228C6113`；formal overlay SHA-256 `E14552048B3D2D40F11FB1ED1C5785A49DCEF0CB3DCB5760CF4ED3BA53930820`；file-list SHA-256 `E28888EB7C31B770E5DFD71D10494E3156F2122A0286209D18E89AE764AB7DA1`。
- projection manifest SHA-256 `27D2282B6C2EDB03680B806CB3A90128F80A55F85F2C3E62588EA90F246A47EA`；materialization receipt SHA-256 `8C89D17528E147BD708EFBBA384CE8267BE2C989383F1626BADF6A43BDCB94DF`。
- 相对 r10 为 `61 added + 2 removed = 63` 个路径变化；旧 `zg361_case_kernel_effects.txt` 与 `zg361_workforce_probation_fact_effects.txt` 不存在于新产品。
- case kernel 为 `39` 个按用途分片；probation 为 `3` 个按用途分片。freezer 现在显式要求这些分片齐全并拒绝旧 monolith，防止只凭宽 glob 造成“旧文件已删但新分片漏投影”的假 GREEN。
- B3 manager 为 `7` 个用途分片、`43` 个 effects，逐片计数 `10 / 7 / 6 / 8 / 4 / 3 / 5`，单文件最大 `10`；本次 delta 中超过硬上限 `20` 的文件为 `0`。
- 全产品仍有三个 pre-B2/B1 继承文件超过 `20`（`41 / 36 / 1449`），均逐字节继承且未由本轮新增或放大；不把它们冒充 B3 例外。

## no-launch 门禁与诚实边界

- manager generator `--check`、manager runner test normal、manager runner test `-O`：全部 GREEN。
- formal B3 preflight：GREEN；日志 SHA-256 `20A9A4EBE90943DFA08622504C126BEE56D61B8D64226688DD51EB3E4D23B4FB`。
- 五个新 action-cell-only Python 文件均已逐文件哈希并登记为 `included_in_product_projection=false`、`live_claim_changed_by_this_freeze=false`。它们不是 CK3 mod 产品文件，不随 B3 候选获得 live claim。
- 唯一获授权的下一条 CK3 命令及 pipe 已写入 JSON 的 `launch` 字段；先前被 G2 独占进程阻断的 RED 和基线更新前的 pipe 均未被复用。
- 当前仍缺真实 paused artifact 中的 typed provider-observed selector、直接下属身份和动作后置条件。只有下一轮实机同时取得这些观测并完成清理后，B3 才能从 `static-ready-live-pending` 提升。
