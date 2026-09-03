# CK3 启动 A/B 探针：`-noWorkshop`（2026-09-03）

## 目的

在不加载宣传素材、不使用 bridge、不触碰真实用户目录的前提下，检查 Workshop 初始化是否是当前 CK3 启动崩溃的必要条件。探针使用隔离 userdir，仅运行 CK3 本体；没有点击商店、购买或付款控件。

## 运行参数

```text
ck3.exe -nolauncher -noWorkshop -debug_mode -userdir=<isolated userdir>
```

- 游戏版本：`1.19.0.6`
- EXE SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- 进程启动成功，约 15 秒内退出，退出码 `1`
- CK3 未进入 loader/database，未生成可用 seed 或视频素材

## 结果

崩溃仍为 `C0000005`，地址 `0x00007FF68F81BD89`（模块 RVA `0x1DABD89`），与不带 `-noWorkshop` 的既有复现一致。因此 `-noWorkshop` 没有解除启动阻塞，也没有证据表明 Workshop 是唯一原因。

## 回执

隔离现场：`Z:\ck3_mod_rewrite\_runtime\ck3-no-workshop-probe-20260903\userdir\crashes\ck3_20260903_075713`

- `exception.txt` SHA-256：`7D87BB1357521CF9610D23AB89C7C9D5A6FE6E9F23CC79508A1E243B5992E1CA`
- `meta.yml` SHA-256：`F59207AAB1CC711D9A272DAEDC0D3CDAD0FDA2558DD51B39960156988CC93E33`
- `minidump.dmp` SHA-256：`3E0751573FD2AE97799DAB164E2B1D1805B2B68ECD64C8CF9A8DF8B6D326A81F`

该探针只增加了一个新的启动参数对照，不改变二期视频的真实素材门禁；下一次启动实验必须有新的外部环境差异，不能继续盲目重复同一崩溃路径。

## `--userdir=<isolated path>` 复核

随后用等号形式显式传递隔离 userdir：`-nolauncher -noWorkshop -debug_mode --userdir=<isolated path>`。CK3 同样在约 15 秒内以退出码 `1` 结束，`meta.yml` 仍记录 `1.19.0.6`，异常仍为 `C0000005` at `ck3+0x1DABD89`。因此不是短参数传递形式导致的差异，仍没有 loader/database readiness 或视频素材。
