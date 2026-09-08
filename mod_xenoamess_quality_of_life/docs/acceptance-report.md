# 验收报告

执行日期：2026-09-08（Asia/Shanghai）
目标：XenoAmess 的生活质量 1.0.0 / CK3 1.19.0.6

## 结论

| 层级 | 结果 | 证据 |
|---|---|---|
| L0 静态、exact-byte、可复现构建 | GREEN | `validate_xenoamess_quality_of_life.py`、7 项 builder 单测、双构建 SHA |
| L1 隔离加载、MCP readiness | GREEN | 最终 live artifact 的 `04_mcp_readiness.json` |
| L2 开关、死亡、卸任、禁转 flag | GREEN | 14 个必需引擎 marker 各一次 |
| L3 Steam fresh-cache | NOT RUN | 待首次 Workshop 上传取得 item ID 后执行 |

## L0

执行命令：

```powershell
& tools/.venv/Scripts/python.exe tools/validate_xenoamess_quality_of_life.py
& tools/.venv/Scripts/python.exe tools/test_build_xenoamess_quality_of_life_release.py
& tools/.venv/Scripts/python.exe tools/build_xenoamess_quality_of_life_release.py --check
```

结果：19 个 runtime 文件、五种 appointment type、三份受控原版覆盖、九种本地化结构与 640×640 thumbnail 均 GREEN。七种非英中语言仍是英文占位，不冒充完成翻译。三份 appointment 文件移除五个 `XQOL_AUTO_APPOINTMENT` 块后逐字节等于本机 CK3 1.19.0.6 原版。

## L1 / L2 最终 GREEN

命令：

```powershell
& tools/.venv/Scripts/python.exe tools/run_xenoamess_quality_of_life_acceptance.py `
  --bridge-dll ck3_autonomous_player/native_bridge/.build-event-scopes-a860702-msvc/xar_ck3_bridge.dll `
  --bridge-injector ck3_autonomous_player/native_bridge/.build-event-window-cea30a0-msvc2/xar_ck3_bridge_injector.exe
```

最终 artifact：`Z:\ck3_mod_rewrite_process_assets\xqol\runs\zqa_20260908_200006_b78dc866`

- 结果：GREEN；耗时 300.074 秒；共享 CK3 槽位等待 0.339 秒。
- exact build：CK3 `1.19.0.6`；`ck3.exe` SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
- MCP：`native-headless`；paused、map-ready、semantic state、transport 与 PID binding 全部 GREEN；无 visual fallback。
- 产品开启决议、产品关闭决议、原版 baseline heir 冻结、启用态最高非玩家 heir、真实 `force_step_down_landed_titles`、真实自然死亡继承、禁转 flag 所有权、关闭恢复与既有 flag 保留全部 PASS。
- 14 个必需 `ZQA: TEST PASS/DONE` marker 各出现一次；没有 `ZQA: TEST FAIL`。
- runtime/source 树未被 CK3 改写；原生进程树清理证明 GREEN；一次性 state dir 已删除；受保护 Steam/真实用户目录未变化。

关键哈希：

| 文件 | SHA-256 |
|---|---|
| `report.json` | `88d01a7ba5f6fb2c817e0bb186edf2fd0dfab0b7d1fb0a07981dd5fa7f73d2fb` |
| `cell/report.json` | `e218e1cd77192452a3626f8efb8c07507bf7e3ab01886849149191f1dd2de632` |
| `cell/04_mcp_readiness.json` | `49d75bdb620dccd5dbe29908012f039c1e68eb980c3bc808942b19c1e87ff971` |
| `cell/12_mcp_final_paused.json` | `6fd0860542fb11c4baee41d18b05504d2277bd506f5adaeb963df57e7465b2f2` |

MCP 当前不发布 appointment score、角色变量或角色 flag，故这些字段按验收方案降级为 CK3 引擎内外部夹具断言；暂停、地图 readiness、前后 paused snapshot 与必要的 pause 操作仍由 MCP 完成。

## 保留的 RED 尝试

以下失败均为 harness/fixture RED，未被冒充产品失败或最终 GREEN；artifact 原样保留：

1. `zqa_20260908_192321_2491c603`：enabled-mod 日志清单被错误按顺序比较。
2. `zqa_20260908_192843_e70d3a85`：决议组缺 `big_button` tag，且夹具死亡原因 key 错误。
3. `zqa_20260908_193602_a647b582`：关闭态 baseline 在开启开关后才采样。
4. `zqa_20260908_194303_678e040f`：宋朝样本本来没有“玩家是当前 heir”，夹具前提无效。
5. `zqa_20260908_195139_c1da5def`：卸任已 PASS；死亡 holder 在同一 effect 内尚未结算，且排队 state 导致二次执行。

最终修复仅调整验收器或外部 fixture；产品机制在第三次以后的实机中未因这些 harness RED 改写。

## L3

状态：`NOT RUN`。首次上传后必须记录 Workshop item ID，从 fresh cache 以 ID-bearing manifest 验证 19 文件，并至少复跑 MCP readiness 与天朝死亡/卸任/禁转核心矩阵，之后才能把本节改为 GREEN。
