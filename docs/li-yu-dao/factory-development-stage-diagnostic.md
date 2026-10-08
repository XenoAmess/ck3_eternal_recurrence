# LYD factory development 分阶段诊断候选

这是独立、不可发布的诊断 overlay。生产71文件与原 factory 不修改。唯一覆盖相对路径是 `common/scripted_effects/lyd_i3b_commit_effects.txt`，按加载顺序置于正式 LYD staging 之后；其他文件仅新增 `lyd_factory_diag` 命名空间、三个诊断 trigger 和中英本地化。没有 replace_path，也没有新增 native ABI。

唯一 builder：`build_diagnostic_overlay_002.py`（建议 ROOT 导入为 `mod_li_yu_dao/tools/build_factory_diagnostic.py`）。它只读实际 clean export/report、检查 factory `bf1b40...ccc7` 与 commit `deb422...62ec` 的精确原件，然后生成一个拒绝覆盖的外置目录。没有注册/启动/Git/SDK/存档正文行为。实际已生成候选是 `diagnostic-mod-002`，六文件；001 提取括号错误与原候选完整保留。

ROOT 正式提交可复用 builder 后的调用：

```text
<verified-python> -B -X utf8 <actual-clean-export>/mod_li_yu_dao/tools/build_factory_diagnostic.py --source-root <actual-clean-export> --source-head <actual-full-HEAD> --export-report <actual-REPORT.json> --export-report-sha256 <actual-SHA256> --output <fresh-external-diagnostic-mod-directory>
```

HEAD 来自显式实际 export，未将历史487当未来HEAD。future HEAD/export/native/meta/allocated ID/profile/session 均不由候选填造。ROOT 新构造后在真实 source/manifest中冻结 package rows，不复用当前候选给未来 compiled/native 资格。

## 分阶段执行

合法初入口仍为原 `lyd.430`：原 ready/native admission 和完整 commit limit 不变。它执行原 doctrine/authority/presence capture，然后停在 `lyd_factory_diag.1`。D1→D2 的 option 再检查原 factory limit，避免 doctrine yield 期间已出现实际其他 HoF 还重复 create。

| 暂停事件 | 此前已完成的原操作 | 唯一推进效果 |
| --- | --- | --- |
| `.1` | doctrine＋原合法授权＋旧 law presence 捕获 | create/change/properties/holder/resolve 原子组 |
| `.2` | resolve 完成 | SetHoF |
| `.3` | SetHoF 完成 | 原条件 cleanup |
| `.4` | cleanup 已执行或原条件跳过 | 原 COA＋Title95 |
| `.5` | COA＋Title95 完成 | 原 office/auth bookkeeping＋原 postconditions＋原 close |
| `.6` | 原 postconditions/close 完成，实际 result_code保留 | 原 show_result_effect，按真实条件显示431或432 |

因此 D6 不复用已清除的 phase/授权变量；它核原 result_actor、实际 actor、result serial/nonce 与旧 event 数值。它不写成功旗。原 show_result_effect 的 AST 原样，仅延迟到 D6观察后显式推进。原拒绝路径直接完成原 postconditions/result，不伪造 D1。

midstage 的完整 `event_context` 不能直接使用：该 trigger 引入 headless/current 检查，D1变更 doctrine 后不再成立。这里只复用原 `cancel_context` 的真实 human/actor/active/serial/nonce/phase 身份，再检查原合法授权、原 faith/rite 与真实 event-local stage。新 title 使用 create_dynamic_title 提供并传递的 `scope:new_title`，并核真实 holder/owner metadata；无硬写 full Title ID。stage 数值只在 `save_scope_value_as` 的事件上下文，不写 actor 变量。未 resolve 的 change 从不跨事件。

stage controller 是真实六事件源，伴随 `STAGE-CONTROLLER.source-only.json` 供 ROOT 原 MCP query/select helpers 读取。ROOT 对每一页先取实际 event query，以实际 shown/enabled/rendered native index 选择名为 `lyd_factory_diag_next` 的选项；从不默认某个 index。推进前保存 cache-beforeSAVE、G2/G3、唯一 stage checkpoint、cache-afterSAVE 和政治 heirs。SAVE 前后 cache 差异作为保存/settling 观察，不冒称前一步 native call 因果。原87/88比较保持；诊断中出现的新阶段错误或保护FALSE照实保留，不写修复缓存/旗/继承人。

## 冷载 seed 与资格边界

仅使用 R29 真实已签署 B3 `checkpoints/B3-signed-precommit-r3-signed/checkpoint.ck3`：91,709,349字节，SHA `c8601e7ba08406a551dcddd2a19e454423db2be6b559fad9985c6d1121b537c9`。历史原 B3正式PASS/87TRUE/native=saved45是 seed来源，不是新诊断冷载的预信用；新冷载仍实际重读同actor、same-round signed状态、无新HoF、native/saved/cache和原CONTROL。禁用B4失败新T保存，禁重走投票或补授权旗。

当前 R29 正常收口之后，ROOT 为新加载输入分配新实际运行并完成其 build/metadata/profile/fixture资格。baseline/runtime signed-B3 intake由独立 owner施工，本包不修改旧原0240 adapter。新的 source/PID/session/frame/Title/revision先NULL，实际输入齐全后 late-bind。`LAUNCH-INPUTS.pending.json` 只声明诊断第六fixture挂载与真实历史seed来源，不是可执行 launch argv。

33项聚焦静态检查使用现有 Clausewitz parser、player_guard 与 localization grammar，验证原 commit/factory authorization、完整成功操作逆投影 AST、原拒绝 continuation、authority receipt/show_result AST、事务atomic、三处同一option guard及无immediate自动推进。它证明结构/顺序和既有脚本语法，不能证明引擎跨新阶段/SAVE保留 scope。缺失 scope、loader错误或意外其他head必须保留实际RED，不补flag、不重跑create。

生产release staging/upload不能包含overlay。D6与431仍只是原局部 postcondition显示，不能替代政治87/88或正式I3b/C3。本次没有MAIN/source71写入、游戏/SDK/桌面/总线操作、binary/body读取或native编译；整体NOT_GREEN。
