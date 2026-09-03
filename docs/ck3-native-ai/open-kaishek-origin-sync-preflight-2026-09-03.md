# open_kaishek 主线同步前置检查（2026-09-03）

## 目的

此前的离线 `open_kaishek` preflight 只记录 checkout 的 `HEAD`，不会判断
它是否已经追上本地已抓取的 `origin/main`。这会让一个已经落后的本地 CLI
仍然通过语法/fixture 检查。该缺口在交接审计中有实际依据：曾出现本地
`main` 落后远端主线的状态。

本次只增加一个**可选、只读**的新鲜度门槛，不改变默认行为，也不会自动
`fetch`、`pull`、改写 checkout 或启动 CK3：

```text
HEAD == refs/remotes/origin/main  -> synced
HEAD != refs/remotes/origin/main  -> stale
缺少任一 ref                    -> unavailable
```

## 使用方式

在需要把 open_kaishek 作为当前主线配套工具的验收前设置：

```powershell
$env:XAR_KAISHEK_REQUIRE_ORIGIN_SYNC = "1"
```

或者在 Python 调用中传入 `require_origin_sync=True`。门槛通过后才会执行
JAR；`stale`、缺少 `origin/main` 或缺少 `HEAD` 都会在执行 CLI 前返回
`FAILED`，并在结果中保留：

- `provenance.open_kaishek_head`
- `provenance.open_kaishek_origin_main`
- `provenance.origin_sync_state`
- `provenance.origin_sync_required`

默认 `require_origin_sync=False`，因此 detached 的历史 evidence checkout、
显式固定的本地 JAR 和现有测试不会被改变。需要同步时，调用方应先自行
完成并验证 `git fetch origin main`，再重新运行 preflight；适配器本身不做
网络操作。

## 验证边界

`tools/test_kaishek_preflight.py` 覆盖了匹配、落后和缺失 remote-tracking ref
三种情况，并确认 stale 情形不会调用 CLI。2026-09-03 本地 checkout 的只读
结果为：

```text
HEAD       = 981c79388a07e447b18f8e4472a16fd65e28c083
origin/main= 981c79388a07e447b18f8e4472a16fd65e28c083
state      = synced
```

这项检查只证明跨仓版本新鲜度；它不提升 G2 的 `nativeCertified` 或
`runtimeCertified`，也不替代 exact-build paused evaluator artifact。
