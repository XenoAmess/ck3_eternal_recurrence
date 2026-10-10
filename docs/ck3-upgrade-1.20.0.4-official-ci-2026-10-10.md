# CK3 1.20.0.4：官方 CI 实际 GREEN（2026-10-10）

`Official Runner CI` 的 [run 38016728117](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38016728117) 对提交 `b37013edc19dc3b8841634a4c8a9c5ac3d173f44` 实际完成并返回 `success`。步骤清单为 **84 项：64 success、20 conditional-skipped、0 failure**；不能把 84 项都写成已执行通过。

该 run 于 `2026-10-10T02:22:30Z` 创建、`02:32:04Z` 完成；状态原文于 `02:34:55Z` 取得，完整日志于 `02:45:24.983096Z` 开始单次获取（8.5615 秒、exit 0、stderr 0B）。本次整理复用既存原日志，没有再次 fetch，也没有重跑本地已过检查。

执行环境：GitHub hosted runner，Windows Server 2025 `10.0.26100`，image `windows-2025-vs2026 / 20260925.250.1`，runner `2.337.0`。只读取证机器为 `4号执行者`（现场标识 `4-8e1c2f1861`），工作区 `C:/workspace/ck3_eternal_recurrence`，命令壳为 `cmd.exe`、`login=false`。查询沿用既有本机 GitHub API/gh 读取脚本和既有 SOCKS 配置，未输出凭据。

实际查询和完整日志命令如下；日志已取得，此处只保留可追溯命令：

```text
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -P -X utf8 C:/workspace/ck3-upgrade-20261010/ci-watch-shared-quit-01/read_official_ci_proxy_once.py --label release-readiness-b37013edc-view-02 --run-id 38016728117
gh run view 38016728117 --repo XenoAmess/ck3_eternal_recurrence --log
```

| 证据 | 精确外置路径 | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| 实际状态查询原文 | `C:/workspace/ck3-upgrade-20261010/ci-watch-shared-quit-01/release-readiness-b37013edc-view-02.stdout.txt` | 15914 | `cb8a2f0a5639f4852b93b7222e66bbc87e5157741a1ce2637cb401e0480799a4` |
| 查询进程回执 | `C:/workspace/ck3-upgrade-20261010/ci-watch-shared-quit-01/release-readiness-b37013edc-view-02.result.json` | 626 | `e15e6e82f8c48f0ace9c444d78123bd9e047367ca004bf8df141c4764c2047ad` |
| 完整原日志 | `C:/workspace/ck3-upgrade-20261010/resume-release-ready-02/official-ci-b37013edc-actual-green-02/official-run-full.log` | 394072 | `b5e52d9e1c3975e67685a38465a34d2f925e2e5b99781a1d9b503c063e1af933` |
| CI 归档索引 | `C:/workspace/ck3-upgrade-20261010/resume-release-ready-02/official-ci-b37013edc-actual-green-02/OFFICIAL-CI-B37013EDC-ACTUAL-GREEN-02.json` | 8279 | `b5d2882405046838be6a98c5bf03c39f2988fde90d38a8d8896b3cc0127fefbb` |

20 项条件跳过包括第 38 项 `Verify ZhongGuo 361 release localization audit`、63–71 项 manual release builds、72–80 项 tagged release builds，以及第 81 项 upload。普通 push 的实际 GREEN 不能代替这些未执行的发布门禁，也不能代替 CK3 实机、正式 tag、SDK 上传、Steam Change Notes 匿名全文回读或真实下载缓存加载。此回执只绑定上述完整提交；闭场采纳 fixture/GUI/361 格式改动之后的新提交需要自己的官方 CI 回执。

截至本记录，QOL 1.1.1、重整河山 0.4.1、361 0.3.1 的正式 tag、Change Notes 与缓存步骤仍未完成；本文不记录新的公开发布事实。本次取证未修改 MAIN/Git，未使用 CK3/Steam/桌面。
