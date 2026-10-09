# 公共验收的本机启动、队列和屏幕续租工具

2026-10-10：不存在的旧外置工具目录不能作为运行依赖。公共验收继续使用 `tools/ck3_mod_acceptance.py` 的 `plan → prepare → allocate → preflight → run → verify`；本页三个公共工具由同一份 machine runtime 配置引用并冻结 SHA，不允许产品指定另一份 host、native 或启动器。工具源码现已入库，旧 attempt 和旧工具不变。

这次只交付公共工具和离线契约回归。静态测试通过不等于本机 CK3 启动、Steam 离线、原生工具或产品业务已验收。

## 运行时引用

`reviewed_launcher` 指向 `tools/ck3_mod_acceptance_launcher.py`，`control_queue` 指向 `tools/ck3_mod_acceptance_queue.py`，`allocation.screen_keeper` 指向 `tools/ck3_mod_acceptance_keeper.py`。三个引用均需完整 `path / bytes / sha256`。allocator 已把三个文件和 canonical `screen_bus_lease.py` 加入实际 `frozen-argv.json` 的输入 pins。复制工具时必须把三个兄弟模块一起冻结。

keeper 不领取或释放屏幕。公共 allocate 先注册真实独占任务，再立即启动 keeper；keeper 消费 `--repo --root --task --sequence`，默认任务总线为 checkout 父目录的 `.codex-task-bus`，CLI SHA 为 `B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE`。也可以明确配置 `--bus-dir / --bus-cli / --bus-cli-sha256 / --expected-head / --interval`。这些参数属于公共机器配置，不属于产品 case。

keeper 的实际文件为 `inputs.json`、`ready.json`、append-only `journal.jsonl` 和最终 `report.json`。它使用仓库既有 `screen_bus_lease.renew_once` 的真实 CAS 与独立 list 回读，冻结入场时的 clean HEAD，180 秒续租，5 秒检查 clean HEAD；异常写 `ROOT_STOP_REQUIRED.json` 并返回非零。按既有正常关闭合同结束游戏和公共 host 后，操作者创建 keeper 根目录中的 `STOP` 文件，等待实际 keeper 父进程退出和 `report.json`，再按最终 sequence 释放。不能把创建 `STOP` 或 keeper ACK 视为释放成功。

## 新鲜截图与直接审核

先依已有离线恢复/截图合同取得新鲜原图 `steam-moved.png` 和 `steam-frame-freshness.json`；图片必须来自当前独占屏幕 epoch。公共 challenge 不移动桌面、不启动游戏、不推断离线，只消费已有实际图像。所有路径均由当前公共 run 和公共 runtime 决定，以下 `<...>` 是必须替换的操作占位值。

```text
<verified-python> -B -X utf8 tools/ck3_mod_acceptance_launcher.py --run-root <actual-live-dir> --keeper-root <actual-keeper-dir> --create-challenge --fresh-frame <fresh-attempt>/steam-frame-freshness.json --image <fresh-attempt>/steam-moved.png --output <new-review-challenge-dir>
```

该命令保存 `challenge.json` 和 `direct-review.png`。审阅图保留完整原图，在上方新增随机 nonce 横幅。操作者必须实际打开原始截图和审阅图，直接读到当前 Steam「离线模式」，读出图上的 nonce，然后写新的 proof；代码、布尔字段、用户同意或旧图都不能代替这一步。

proof 是如下 schema 的 JSON 对象。示例不是实际验收事实，不可原样提交；所有 pin 必须由所列文件的实际字节生成。

```json
{
  "schema": "ck3-mod-acceptance-direct-review-v1",
  "reviewed_at_utc": "<actual timezone-aware ISO time after challenge creation>",
  "reviewer": "<actual reviewer identity>",
  "direct_image_review": true,
  "steam_offline_confirmed": true,
  "observed_nonce": "<32 characters read directly from direct-review.png>",
  "run_id": "<actual allocated run id>",
  "screen_task": "<actual exclusive screen task>",
  "frozen_argv": {"path": "<actual-live-dir>/frozen-argv.json", "bytes": 0, "sha256": "<actual SHA-256>"},
  "challenge": {"path": "<new-review-challenge-dir>/challenge.json", "bytes": 0, "sha256": "<actual SHA-256>"},
  "image": {"path": "<fresh-attempt>/steam-moved.png", "bytes": 0, "sha256": "<actual SHA-256>"},
  "review_image": {"path": "<new-review-challenge-dir>/direct-review.png", "bytes": 0, "sha256": "<actual SHA-256>"}
}
```

`challenge.json` schema 是 `ck3-mod-acceptance-review-challenge-v1`，它固定 `created_at_utc / nonce / run_id / screen_task / frozen_argv / keeper_root / keeper_inputs / frame / image / review_image / cas_at_creation`；`frame` 指向 schema `ck3.steam_fresh_desktop_frame.v1` 的实际 freshness receipt。原图 SHA、位移边缘像素、实际尺寸和恢复矩形均重新核对，有 clock check 时其 `clock_pixels_unchanged` 必须是 `false`。frame、challenge、review 均最多 600 秒，依次发生。

把 `proof / challenge / observed_nonce / reviewer` 加入该 run 的后继 context，再经公共 entry `preflight`、`run`。原 allocated context、冻结 argv 和旧回执不覆盖。

launcher 在写入一次性 `launch-intent.json` 后启动公共 supervisor，后者再次验证所有冻结 pins、当前 clean HEAD、真实独占 CAS、fresh-frame/nonce/proof、Steam UI PID 和共同 Python 环境，再只启动一次冻结 host argv。它快速返回供 `CaseClient` 进入 held scene。supervisor 持有原始 `Popen` 到 `wait()` 返回，保存 `host-started.json` 和 `host-original-process-exit.json`。后者只证明 host 的真实退出码；不得推断 CK3 正常退出、native cleanup 或业务通过。这些仍由已有 `CaseClient` 和公共 native-zero 合同验收。

## 不重发队列

队列 CLI 保持 `--live <actual-live-dir> --plan <frozen-plan.json> --name <new-name.json>`。公共 `CaseClient` 自动调用；产品不能绕过公共入口独立启动现场。

队列检查 frozen run、公共工具/host/lease helper pins、keeper 当前真实 CAS、当前 host 的 state/source/pipe、held deadline 和所有既有 step 已完成，再用实际 host `mcp_tools.tools` 中的 `inputSchema` 验证实参。只有 host 负责填入的缺省 `expected_revision` 可以留空；不会虚构 revision。当前公共队列只接受 `tool`、单日 `advance_day` 和独立 `finish_hold`，拒绝未知 kind 与 symbolic 参数引用。增加其他 host kind 需先扩展公共工具的契约和测试。

每次提交先独占创建 name、原始 plan 内容 SHA 和每个 step ID 的永久 claim，然后将完整写入/fsync 的临时文件 hard-link 到公共 `controls/*.json`。失败 claim 保留，绝不覆盖或自动重发；新的文件名不能使旧内容或旧 ID 再次执行。普通步骤保留 90 秒正常 Quit 时间；`finish_hold` 必须经所选公共 host 原文中的 `finished_native_exit_zero_proof`，不能由 host exit0 或进程消失替代。

## 离线验证

```text
<verified-python> -B -X utf8 -m unittest discover -s tools -p test_ck3_mod_acceptance_local_launch.py -v
```

十项回归覆盖 fresh nonce/run binding、过期审核、原图变更、缺失直接审核/离线确认、冻结 pin 变更、STOP 和真实 CAS owner/stale 拒绝、内容/ID 重发拒绝、实际元数据参数校验，以及一个无害 Python 子进程的真实 exit7 保全。测试不启动 CK3、Steam，不连接任务总线、不取得屏幕。
