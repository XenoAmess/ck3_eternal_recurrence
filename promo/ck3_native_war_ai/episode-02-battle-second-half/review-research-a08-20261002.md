# Episode02 a08：研究成果已入片，等待人工完整审阅

本轮先完成 R0148 六项受控案例研究，再完成 R0149 增援完整画面补采，随后更新视频。原版角色次日状态、完整骑士名单、完整战斗窗、骑士选择器、本窗口唯一相关死亡路径、声明的 13 个可变状态域都已有本轮原读数/原图与独立核对。有限案例结论不外推所有事件、整场概率或未来状态。

本地审阅成片：`C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-War-AI-Episode02-BrownGold-Research-20261002-a08.mp4`。

- 232,268,593 B，SHA-256 `CFF09685022C148C7300D56DB636A75D45A4054416440FB05D5E4F641C3B3AD4`。
- 时长约 30 分 39 秒；1920×1080、30 fps、H.264，AAC 48 kHz stereo；六章、167 句、中英字幕。
- 20 句骑士机制解释及 5 句增援解释改写，25 张新图卡使用战争系列棕金包装。人物前后属性、四份完整名单、两日战宽提示放大显示；真实 UI 像素保持原色。
- 25 句重新配音；在后续独立 attempt 只再重配来源转场一句，明确历史 A01 原生图卡与本轮 R0149 复核。其他 166 句验证后复用处理过的音频。
- 重新计算旁白、字幕与六章时间；没有套用旧整片 AAC。独立 a02 通知录像仍标原来源，其 2.5 秒放大层保留。
- 180 项最终机器检查通过，整片视频和音频完整解码成功。root 直接审阅 34 张最终帧，九张拼图覆盖全部新图卡、六章入口及通知放大层时序。

最终 run：`C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-research-20261002-a02/`。原始 a08 attempt、第一版图卡、图卡放大版本、TTS、字幕、chunks、失败记录和旧 a07 均保留。每个新 run 查询最新正式工具链，实际使用 xar-promo-toolchain 0.2.1，wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，显式使用主 worktree 的 `tools/.venv/Scripts/python.exe`。

归档已完成：882 份过程文件逐字节建立完整哈希清单并再次验证，原目录永久保留；正式 RunManifest 有 294 份保全记录，CLI validate 通过，人工 signoff 数量为 0。原逐文件保全器因反复校验大素材而由本轮停止，其 exit 15、已生成 CAS、manifest 历史与独立 failed phase 均保留；后续一次完整清单封存使用另一个 succeeded phase，没有把中断记录改为成功。回执见 `native-preservation-complete.json` 和 `retained-process-index-a02.json`。

`audit/machine-report.json`、`frame-review/final-frame-quality.json` 只证明其声明条件。正式工具链已生成 `pending-human-review/` 包，其人工反馈与 signoff 留空。尚未发生人工按 1× 完整观看/听音签核，不能把成片标为已获人工批准或 production-clean。

OneDrive 只传这一份 MP4，固定目录和客户端设置未改变，没有客户端下载其他文件。13 次 metadata 采样后为 `CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED`：本地副本 SHA 一致，客户端 InSync、validated 全尺寸、modified 0；没有独立云端回读。原始回执见 `delivery/final-delivery.json`，不得把这个边界省略成云端独立确认。

机制结论的 exact-byte 副本保存在本目录的 `evidence-a08-research-20261002/`；原有详细证据继续由原封存清单回链。研究提交在 `codex/war-e2-mechanism-closure-20261001`，视频在 `codex/war-series-brown-gold-20261001`，冻结实机执行源码在 `codex/war-e2-identifier-append-capture-20261002`；没有拉取、合入或推送 master。

后续只需对当前 SHA 的成片人工完整观看和听音，按 `pending-human-review/` 中模板记录实际决定；若修改成片字节，必须建立新 run 和重新审阅，旧签核不能沿用。
