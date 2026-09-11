# XQOL 1.1.0 验收报告

执行日期：2026-09-11（Asia/Shanghai）
目标：XenoAmess的体验优化 1.1.0 / CK3 1.19.0.6
公开基线：Workshop item `3798133925` / 1.0.2

## 结论

| 层级 | 结果 | 证据 |
|---|---|---|
| L0 静态、九语发布本地化、生成 parity、可复现构建 | GREEN | XQOL validator、生成器检查、builder 单测与双构建 |
| L1 隔离加载、MCP readiness | GREEN | `D:\workspace\ck3_xqol_phase2_release_live1\cell\04_mcp_readiness.json` |
| L2 一期回归与七项二期功能 | GREEN | 同一次完整 CK3 运行的引擎 PASS/DONE marker、截图和 MCP 快照 |
| L3 Steam fresh-cache | 待发布后复核 | 只在 Workshop 上传并从空缓存重新下载后关闭 |

本报告冻结发布前候选的实机事实；Workshop 上传、fresh-cache 严格核验和正式发布事实记录在 `docs/release-changelogs/xqol/1.1.0.md`，只有三者都完成后才标记本次发布完成。

## 已验收候选

- 实机测试代码与九语本地化 commit：`e877a0b31f2b10d2d7b837e1eaac057e2a23bbf6`。
- 版本：`1.1.0`；正式中文名：`XenoAmess的体验优化`。
- 正式 tag、manifest 与 ZIP 由后续 clean release freeze 生成；不在本报告中循环嵌入自身哈希。
- 七种外语各新增 50 个二期值，共 350 个值；发布本地化门禁为 GREEN。完整审阅见 `docs/xqol-release-localization-review-2026-09-11.md`。

## open_kaishek 离线预验

- checkout commit：`890b32de49081b7b5510e40c5518dfb59d5c8a6d`。
- CLI JAR：`kaishek-cli-0.1.0-SNAPSHOT-shaded.jar`，SHA-256 `7262e771ad3e1f5d724d663ac259a20e2a7df0c491d4c125f56cb4c3a604e75c`。
- profile/version：CK3 `1.19.0.6`；EXE SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
- 产品确定性语法子集 13/13 parser GREEN，corpus SHA-256 `5ab8093df9e3a36024954f8f93db1b4071e8430d721036c2fee35100d72f52c2`。
- 最终验收夹具确定性语法子集 10/10 parser GREEN，corpus SHA-256 `b9640ac51984a0bc06115431c6ae0067d4893aa2d1ee0335e7324738abb4e01f`。
- 尚未覆盖的互动运行语义记录为 tool-coverage `not-applicable`，没有把离线 parser 冒充实机 GREEN。

## L0 发布门禁

同一候选上的发布本地化工作包一次通过：

```powershell
& tools/.venv/Scripts/python.exe tools/test_translate_localization_minimax.py
& tools/.venv/Scripts/python.exe tools/validate_xenoamess_quality_of_life.py --release-localization
& tools/.venv/Scripts/python.exe tools/test_build_xenoamess_quality_of_life_release.py
& tools/.venv/Scripts/python.exe tools/build_xenoamess_quality_of_life_release.py --check
```

结果：26/26 翻译调用器测试、发布本地化门禁、8/8 builder 测试、24 文件确定性双构建全部 GREEN。该次文档冻结前开发快照的 manifest SHA-256 为 `617c4eb6d4dc3e9b2b717465c21351de9d45640b896d56d9e5bb8af53309a058`，ZIP SHA-256 为 `58f79aa467615d11d1473898b5b9e08f63b08d609a0ef0c68c575bffc5bbe9b8`；正式 tag 构建哈希以后续 changelog 为准。

## L1 / L2 完整实机

命令：

```powershell
& tools/.venv/Scripts/python.exe tools/run_xenoamess_quality_of_life_acceptance.py `
  --artifacts-dir 'D:\workspace\ck3_xqol_phase2_release_live1' `
  --bridge-dll 'D:\workspace\ck3_xqol_publication\ck3_autonomous_player\build-fresh-xqol-1.0.1\xar_ck3_bridge.dll' `
  --bridge-injector 'D:\workspace\ck3_xqol_publication\ck3_autonomous_player\build-fresh-xqol-1.0.1\xar_ck3_bridge_injector.exe'
```

- 最终结果：GREEN；退出码 0；耗时 1069.261 秒，其中本机冷启动约 11 分钟，runner 的启动等待上限为 30 分钟。
- exact build：CK3 `1.19.0.6`；`ck3.exe` SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
- MCP：`native-headless`；transport、PID binding、paused、map-ready、semantic state 全部 GREEN。
- runtime product tree SHA-256：`14f4b66cf41e7d560e7471b3307725b977c434f11e40f11828e7fa19274c0a41`；fixture tree SHA-256：`fe01439cade95449dbbe911fd026ffabf4fe48b2119d9face4d0b315a53a8ad4`。
- runtime/source 均 unchanged；进程树受控清理；一次性 state dir 删除；受保护 Steam 与真实用户目录 unchanged。

### 一期回归

- 三项产品开关的启用/关闭决议均由简体中文 UI OCR 实读并点击。
- 原版继承 baseline、启用后最高分非玩家继任、卸任转移、真实死亡转移均 PASS。
- 禁转封 flag 的启用、关闭、所有权边界与既有原版 flag 保留均 PASS。

### 七项二期功能

1. 自动防御召援：常规免费盟友与同时具有同盟/家系关系的重叠候选实际成为防御方参战者；付费宗族候选未加入，重叠候选只加入一次，重放调用计数为 0，玩家金钱、威信、虔诚未下降。
2. 批量要求改信：滑动条实际显示 50%，拖至 65%，再回到 50%；50 门槛筛选与接受/拒绝汇总 PASS。
3. 足额牵制索款：只处理可支付完整义务且可合法互动的目标，PASS。
4. 现有款牵制索款：只处理金钱严格大于 1 的目标并收取当前整数金钱，PASS。
5. 足额赎囚：只处理愿意支付完整适用赎金的付款人，PASS。
6. 现有款赎囚：只要愿意付款的 AI 至少有 1 金钱便收取现有整数金钱并放人，PASS。
7. 附条件释放：在牵制、招募、改宗中最大化兼容条件数，并按牵制、招募、改宗打破同规模平局，PASS。

关键哈希：

| 文件 | SHA-256 |
|---|---|
| `report.json` | `47a6fa24213e600b3c9fd8498273efe0efc5ae3ea27037f789be7ee554643e2f` |
| `cell/report.json` | `85707c8dd471807fcb936ef6dafaef2c69d04cb483952ef22ba18a96c84e0c06` |
| `cell/04_mcp_readiness.json` | `4f140c14340e1410099b8e77a97871f037552bf48cfa4125370f60a60d1d138e` |
| `cell/09_death_settlement_tick.json` | `9fc52382705b12bfba8a9253d2e8e51e68f7f62eb4012cde594c37dd7932a26a` |
| `cell/15_conversion_reply_advance.json` | `e03341c4bdb85bcae0b58fc267db15ec41d6856cb78969183e8b4a1477d9e3ab` |
| `cell/19_defense_war_advance.json` | `6b5d21b0f285e209a83e01d7a22bbd969d14aba2ff1d6177923216166e8bcdeb` |

## 保留的 RED 尝试

二期开发中的失败尝试按原目录保留，没有覆盖成 GREEN。`ck3_xqol_phase2_live27_process_assets` 已证明除防御召援外的全部二期互动矩阵；随后 `ck3_xqol_phase2_defense_live1` 至 `live5` 依次定位战争创建时序、虚构同盟被日结算清理和互动 wrapper 读取缺失 `scope:hook` 的问题。`ck3_xqol_phase2_defense_live4` 在历史加载期崩溃，归类为 environment RED。修复后 `ck3_xqol_phase2_defense_live6` 取得针对性 GREEN，最终由本报告的完整 `ck3_xqol_phase2_release_live1` 一次复核全部功能。
