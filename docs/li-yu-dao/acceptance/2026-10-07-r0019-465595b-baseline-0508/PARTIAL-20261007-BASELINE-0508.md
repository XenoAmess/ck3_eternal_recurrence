# R0019 基线三源合并与 HEAD 来源修正增量

截止 **2026-10-07 05:08:00 UTC**，原 CK3 PID19980 / native session `172caf27cc8b44549ea94ed2f306cfe0` / generation1 的基线保存、原生 G2/G3 观察与已解析保存观察已真实合并。`baseline-author-002` 原执行 exit0，状态为 `ACTUAL_COMPACT_NATIVE_SAVED_OBSERVATIONS_JOINED`；87 项保护全部 TRUE、失败 0。整个 mod 仍 **NOT_GREEN**，`actual_pass` / `formal_mandate_credit` 均为 NULL；没有 formal、新 T、C3 或 I4 验收信用。

主执行树、mod/export/native binary 仍冻结 exact HEAD `465595b67efa8f72dfc97bc0de218302c75e3bfd`。文档基底为 `52094f0133e59bd643de46258cbc14c40dc93afb`。实际 Python 服务另有已加载的晚 attach 修复来源，见[既有生产修复与 04:52 回执](../../../ck3-native-ai/native-profile-explicit-late-attach-verification.md)；不能把运行中的 Python 称为仅 frozen465 字节。旧[04:35 启动截止](../2026-10-07-r0019-465595b-startup-0435/PARTIAL-20261007-STARTUP-0435.md)与所有原 RED 保留。

首次作者在 04:59:35 返回 `RED_PRESERVED` / `MigrationError: actual69 manifest/source differs`。原 manifest 的 `source_head` 残留 dbaf；migration reader 第109行 schema/HEAD/immutable business map 检查中仅 HEAD 不符。`save_body_reads=0`，原 RESULT 与 traceback 原样封存。

后继恢复包仅修正 registry/windows/manifest 的当前 HEAD 引用，manifest 改键为 `source_head`、`business_files_changed=[]`；69 项业务字节映射、policy 与作者不变。执行作者仍为原 source005、SHA `900a0351cc107d10d12e60e83fe035b0d7f2e11c9042b1c61b9bfb8581f5dcf5`。CP002 与 CAP002 是来源及最小 SHA pin 更新，CAP 的 helper 仅更新 checkpoint INDEX SHA、spec author 仅更新 CP 默认002及 helper SHA；B0SPEC、label regex 与业务谓词不变。这些准备 INDEX 的 SOURCE_ONLY/未执行字段保持原样；后续实际作者执行由独立 ROOT wrapper 证明。原政策登记的既有 2 项允许业务迁移与 67 项原字节不变，是先前政策范围，不是本次 HEAD 修正新增业务变更。

第二次实际作者执行为 05:07:04.431306–05:07:31.722851 UTC，exit0、无自动重试；`save_body_reads=1` / `game_calls=0`。三源结合的 frame 为 public revision3 / native revision2、date53144712、actor31254、PID19980、generation1。原 TYPED identity 内 `revision=2` 原样保留，属于其原身份层，不能改填 public revision3。G2 为 `BOUND_COMPLETE_NATIVE_OBSERVATION`，G3 为 `BOUND_NATIVE_HEADLESS_OBSERVATION`；`strict_formal_reader_executed=false`。`ORIGINAL0240-CONTROL.actual.json` 是此次已解析 RESULT/STATE/TYPED/qualified-native 引用的控制对象，建立它没有第二次读取正文。

基线 checkpoint 仅记录原 descriptor：91,669,783 B、SHA `8f05670973c3b4084259816ffcdc103c59cdc0765b5ca10696673069289401c8`，不入 Git，本归档未读取或复制 `.ck3`。SDK0005 SAVE、0006 G2、0007 G3 的既有 request/response/SDK/native 原件与两次作者结果、已解析 STATE/TYPED、源码小件、失败 trace、ROOT 原执行 stdout/stderr 在 ZIP 中按原字节保存；[清单](INVENTORY.json)逐项记录外置原路径、bytes、SHA256 和 ZIP entry。[事实对象](FACTS.actual.json)只投影既有原对象，不重跑作者或保护检查。

此前 exact465 OfficialRunner CI 成功、LiYu 未触发、native 编译及五项 focused 通过，outer exit1 的 Defender 设置失败，均沿用[原 CI/build 分层报告](../../../ck3-native-ai/acceptance/2026-10-07-r0019-exact-head-ci/REPORT.md)，本增量不重复核验。截止05:08正常退出尚未验；ROOT 后续 formal begin 与业务结果须另有实际回执，本报告不预填成功。
