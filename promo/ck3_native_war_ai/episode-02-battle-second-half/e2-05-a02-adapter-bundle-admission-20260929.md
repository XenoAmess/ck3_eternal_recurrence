# E2-05 a02：CK3 adapter bundle 结构准入与缺口

2026-09-29 CST。本记录只核已有小型回执与代码路径；不重读原始 MKV、不重新探测媒体、
不审定 clean span，也不生成 adapter GREEN。

## 本次工具链身份

- 查询 `XenoAmess/xar_promo_toolchain` 最新正式 GitHub Release：`v0.2.1`，非 draft / prerelease；
  wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`。
- `tools/requirements-promo-toolchain.txt` URL 与 SHA 与该 Release 一致。
- 显式解释器 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 报告
  `xar-promo 0.2.1`；已核 `python -m xar_promo --help` 与 `validate --help`。
  本 secondary worktree `D:/w/e2adapter` 无相对 `.venv`。
- 本次读取的工具脚本为本 worktree commit `8cb8dcb79` 的
  `prepare_existing_capture_bundle.py`；未用运行中的 `D:/w/e2` HEAD。

## 已有机器证据

| 证据 | 结构结果 |
| --- | --- |
| `e2-05-a02-postrun-audit-20260929-a01/pts-audit.json` | SHA-256 `A3A9243E48D987134664F1A0E951938E17A0CA36D86B50750AFAA6CA4BD8645A`；`PTS_CONTINUOUS_UNREVIEWED`，12,656 个有 PTS 帧，0.000–599.967 s；missing / nonmonotonic / gap >0.2 s 均为 0。 |
| 同目录 `postrun-links.json` | SHA-256 `213988D4278A26EFD4AA93BD8FE8DA2A56234D9B5EC3B1AE019EB53212B0EB0C`；`MEDIA_PTS_CANDIDATE_UNREVIEWED`，关联原 capture/session、recorder 首末、marks 与 3 个游戏截图和回执；明确 `adapter_bundle_validated=false`、`clean_spans_certified=false`、`human_1x_review_performed=false`。 |
| `episode02-e2-05-a02-visual-index-20260929-a02/sample-index.json` | SHA-256 `28D525DBDCC73167133E19968969682C3B42584035BE25AA1234A2F3D11662C4`；15 个 sparse PNG 样本，各有 FFmpeg 命令、exit 0、showinfo 与冻结 ffprobe PTS 对照，索引原件绑定上项 postrun links。采样位置为 0、90、175、190.033、210、240.033、265、285.033、300、315、335、385、400、500、580 s。索引自身仍为 `SPARSE_VISUAL_CANDIDATE_UNREVIEWED`。 |
| 同索引 `final-source-audit.json` | `STABLE_STAT_ONLY`，raw 与 ffprobe bytes/mtime 与索引前一致，`raw_rehash_performed=false`。 |

原片身份由此前**一次**完整 PTS 审计冻结：
`recording-e2-05-d26-a01/raw/e2-05-d26.mkv`，2,451,530,594 B，SHA-256
`7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`；
完整 `ffprobe.json` 为 12,044,180 B，SHA-256
`06A9C1FB92983390F6EE5FA48352732B09E01C4336B4D956F9CECC19F7C3A1FB`。
上述后审是机器连续性与来源候选，不是画面内容或视觉连续性证明。墙钟 marks
190.884 / 304.990 / 388.113 s 不能直接用作视频 PTS。

## 当前准入与缺口

1. **结构候选已满足**：原会话是 `ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO`，录制是
   `ENCODED_UNREVIEWED`，外置 PTS/mark/截图链条在后审报告中通过。15 张 PNG
   可以帮助定位内容，但不是完整原速审片回执。
2. **正式 `prepare` 现在不运行**：现实现的 `prepare()` 先对 `final.raw` 调用 `verified()`，
   又对 `recorder-end.raw` 调用一次，最后在固定文件清单对 raw 调用 `record()`；这些操作
   各自完整读取 2.45 GB 原片算 SHA。它也重复读取完整 ffprobe。当前高磁盘窗口约束下，
   无法用该命令产出 `PENDING_CLEAN_REVIEW` 而不重新扫原片。手写相同 schema 的清单也
   不具备 `validate_source_inventory()` 所要求的原件证明，不能冒充正式 prepare。
3. **目视审阅仍缺**：尚需实际人员原速看完整原片，区分可用画面、加载/弹窗/外来覆盖、
   同一游戏来源及事件是否可见。稀疏样本和待交付目视报告不能代替每段完整连续画面审阅；
   尤其不能据原生 trace 单独声明画面出现骑士击杀。
4. **exact-span 证据仍缺**：审阅者先选真实可用区间，再从完整 ffprobe 选**确切存在**的
   起止帧 PTS；对每个端点运行该脚本 `extract-frame`，保存 raw-derived PNG、showinfo、
   stdout/stderr、命令和 extraction receipt，并在抽帧后审阅这些端点。现有 15 张 sparse
   PNG 虽各有来源绑定，却不是该脚本所需的 `EXTRACTED_UNREVIEWED` 端点回执。
5. **正式 package 与 adapter 验证仍缺**：由真实审阅者提交绑定 source manifest、原片、
   exact span 与两端回执的 `human-review.json` 后，`package()` 才复制 2.45 GB 原片和证据、
   生成 report/timeline/index 并调用 `load_capture_bundle(...).verify_unchanged()`。
   这一步另需至少一份原片大小的空余空间及读写预算；包的 adapter GREEN 也不等于成片签核。

## 后续最小顺序

等磁盘窗口释放，在新的外置目录运行正式 `prepare` 并保留 `PENDING_CLEAN_REVIEW`
清单；等真实完整审片和 exact span 选择后，对每个起止点分别新建 `extract-frame`
attempt；最后用独立的人审回执在另一新目录 `package` 并实调 adapter 验证。
所有旧 attempt、15 张样本、原 capture report 与原 raw 均保持原样。每个新 run
前再查询最新正式工具链 Release 并记录所用 wheel SHA。
