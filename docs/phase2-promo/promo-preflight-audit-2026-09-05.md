# 天朝二期宣传工具更新与真实媒体环境回执（2026-09-05）

状态：**宣传工具更新前置已完成；媒体环境 GREEN；双片仍为 footage pending。**
本工作包不启动 CK3，不制作占位媒体，不签署真人审片，不发布；日报/周报由协调者合并。

## 更新顺序与结果

2026-09-05 10:19:53（Asia/Shanghai），先检查 `Z:\workspace\xar_promo_toolchain`
的版本、分支和 clean 状态，然后实际执行：

```powershell
git -C Z:\workspace\xar_promo_toolchain pull --ff-only origin main
git -C Z:\workspace\xar_promo_toolchain rev-parse HEAD origin/main
git -C Z:\workspace\xar_promo_toolchain status --short
git -C Z:\workspace\xar_promo_toolchain describe --tags --always
```

拉取返回 `Already up to date.`；更新前后均为 `main`、工作树 clean，
`HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`，
`describe=v0.2.1-1-g57c42fc`，源码版本 `0.2.1`。没有新提交需合并，也没有本地修改需提交。
历史 `Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903` 是 detached checkout，保持原样。

随后使用明确解释器和源码路径核验了实际 `python -m xar_promo --help`：十个命令仍为
`init/start-run/validate/preserve/signoff/plan/build/audit/review/export`；没有 publish 命令。
已读当前工具 `README.md` 与 `docs/architecture-and-migration.md`，不虚构新的制作入口。

## 解释器与源码覆盖

当前 secondary worktree 的相对 `tools/.venv/Scripts/python.exe` 不存在，因此显式使用并核验：

- 解释器：`Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe`，Python `3.13.2`；
- `XAR_PROMO_SOURCE=Z:\workspace\xar_promo_toolchain`，项目 wrapper 实际加载该 checkout 的 `src/xar_promo`；
- 源码 `xar_promo.__version__=0.2.1`；Pillow `12.3.0`，edge-tts `7.2.8`；
- **安装元数据仍为 `xar-promo-toolchain 0.1.0`，不能把它误报成已安装 0.2.1 wheel。**

本轮没有在协调者的 CK3 长局期间修改共享 venv。`XAR_PROMO_SOURCE` 由项目
`promo_toolchain_loader` 消费，不是 Python 本身的模块搜索参数；因此直接运行工具 CLI
时还应明确设置如下 `PYTHONPATH`，以保持与 wrapper 相同的最新源码：

```powershell
$env:XAR_PROMO_SOURCE = 'Z:\workspace\xar_promo_toolchain'
$env:PYTHONPATH = 'Z:\workspace\xar_promo_toolchain\src'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' -m xar_promo --help
```

共享解释器可在不影响进行中任务时按当前 `tools/requirements-promo-toolchain.txt` 升级到
hash-pinned `0.2.1` wheel；本轮 source override 的 GREEN 不依赖该升级，也不声称已经完成它。

## 人物版真实环境预检

本次没有重复旧版全量单测、authoring 校验、no-media runbook 或素材复用审计。
唯一新增的制作准备是运行现有 `preflight_phase2_media.py`，实测当前网络语音目录、字体、
字幕内存布局、FFmpeg/ffprobe 编解码能力和拟用输出路径。命令为：

```powershell
$env:XAR_PROMO_SOURCE = 'Z:\workspace\xar_promo_toolchain'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' mod_zhongguo_style/tools/preflight_phase2_media.py `
  --output Z:\ck3_mod_rewrite\_runtime\phase2-promo-preflight-20260905-1021\media-environment-character.json `
  --project-config mod_zhongguo_style/promo/phase2-promo-character-project.json `
  --expected-toolchain-head 57c42fca13ea459432c1caf76e069a1fbccf602c `
  --planned-work-dir Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-character-led-final-20260905 `
  --planned-tts-cache Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-tts-cache `
  --planned-export-dir Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-character-led-export-20260905
```

运行前只创建新的 receipt 父目录，没有创建候选 workdir 或媒体。退出码 `0`，
`PHASE2 MEDIA PREFLIGHT: GREEN`。回执：

- 路径：`Z:\ck3_mod_rewrite\_runtime\phase2-promo-preflight-20260905-1021\media-environment-character.json`；
- SHA-256：`E441A38C24FF2CE935BC85384300015FC831196BBEF44494BF05C1C791EEDC21`；
- 生成：`2026-09-05T02:21:17+00:00`，有效至 `2026-09-06T02:21:17+00:00`；
- `fresh_fetch_verified=true`，`production_refresh_still_required=false`；
- 实际 Edge 目录包含 `zh-CN-XiaoxiaoNeural`，没有合成语音；
- FFmpeg/ffprobe `8.1.1-full_build`，`libx264`、AAC、ASS/libass、`yuv420p`、MP4 能力可用；
- 实际加载 Microsoft YaHei UI/Segoe UI，双语布局在内存安全区内；没有生成字幕媒体或测试视频；
- `ck3_started/tts_synthesis_performed/subtitle_media_written/ffmpeg_encode_started/work_directory_created/candidate_generated` 全部为 `false`。

该回执只绑定人物版 draft 配置 SHA-256
`963735C8D32725A83D4A764CFD92D3C85519500C44FB2D71823F51992DB7042F`。
制度版配置 SHA-256 为 `77537A37D2D1B3E00F38120667491F8CF7047E999DFEEF640DCB8D4343524C7E`；
**不把同一环境回执冒充制度版或未来 promoted 配置的生产回执。** 素材审阅后配置发生变化时，
仍按既有双片生产合同分别绑定新配置和真实 source bundle。

## 10:58 制度版独立环境回执

按协调者后续明确工作包，制度版另跑一次现有预检，绑定它自己的 draft 配置。
没有重跑人物版、拉取或旧单测；沿用本日 10:19 已更新的工具 HEAD 和明确源码覆盖：

```powershell
$env:XAR_PROMO_SOURCE = 'Z:\workspace\xar_promo_toolchain'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' mod_zhongguo_style/tools/preflight_phase2_media.py `
  --output Z:\ck3_mod_rewrite\_runtime\phase2-promo-preflight-20260905-1058\media-environment-institution.json `
  --project-config mod_zhongguo_style/promo/phase2-promo-institution-project.json `
  --expected-toolchain-head 57c42fca13ea459432c1caf76e069a1fbccf602c `
  --planned-work-dir Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-institution-led-final-20260905 `
  --planned-tts-cache Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-tts-cache `
  --planned-export-dir Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-institution-led-export-20260905
```

只新建 append-only receipt 父目录，退出码 `0`，环境 `GREEN`。新回执独立于人物版：

- 路径：`Z:\ck3_mod_rewrite\_runtime\phase2-promo-preflight-20260905-1058\media-environment-institution.json`；
- SHA-256：`5601C5679FA7834DC8EB5B76421350FAB8A68DE4493DD11CC33DB76BED1633F9`；
- 配置：10 章，`3,176 B`，SHA-256 `77537A37D2D1B3E00F38120667491F8CF7047E999DFEEF640DCB8D4343524C7E`；
- 生成：`2026-09-05T02:58:09+00:00`，有效至 `2026-09-06T02:58:09+00:00`；
- 实际源码 `0.2.1`、HEAD `57c42fca13ea459432c1caf76e069a1fbccf602c`，clean，`fresh_fetch_verified=true`；
- 六项执行 attestation 全部为 `false`，无 CK3、TTS、字幕媒体、编码、候选 workdir 或候选视频。

制度版自己的 `final_promo_readiness` 仍为 `RED / waiting-for-inputs`，原因同样为
`footage_pending` 与 `publish_target_pending`。双版现在各有本日独立 **draft 环境** 回执，
不是两部成片完成，也不适用于随后 source review 提升后的不同配置字节。

## 尚未交付的部分

环境回执诚实保持 `final_promo_readiness=RED`，原因是 `footage_pending` 与
`publish_target_pending`。这不是宣传工具更新失败，也不把外部发布目标缺失升级为本地制作的
新门禁：先继续现有四 checkpoint/八段素材主线，素材和真实 source review 到齐后，两版分别
TTS、build、claims audit、真人 1× 审片、signoff、本地 export。外部上传仍需实际目标授权。

本工作包没有产出新的 source span 或 MP4，没有改变两版剧情、配置、制作合同或已有素材。
后续脚本和取材路线复用既有 [`phase2-dual-cut-production.md`](phase2-dual-cut-production.md)
及 [`final-video-source-reuse-audit-2026-09-04.md`](final-video-source-reuse-audit-2026-09-04.md)，
不为等待实机而重复生成同样的 RED runbook。
