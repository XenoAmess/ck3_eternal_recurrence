# XenoAmess的体验优化：Steam Workshop 首发交接

交接时间：2026-09-08（Asia/Shanghai）  
产品：`mod_xenoamess_quality_of_life` 1.0.0  
目标游戏：Crusader Kings III 1.19.0.6  

## 当前状态

- Git tag：`xqol-v1.0.0`
- Git commit：`fed5ccaca9700b13ecc33d70869329a2209bf47c`
- GitHub Release：<https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/xqol-v1.0.0>
- 本机只打开过经 Steam 初始化的 PDX Launcher，随后在打开上传表单、选择物品或提交前按项目所有者要求退出。
- **本机没有点击上传、没有创建 Steam Workshop item、没有提交描述、没有修改可见性、没有接受任何法律协议。**
- Workshop item ID 尚不存在；仓库内 `descriptor.mod` 与 GitHub ZIP 均不含 `remote_file_id`。
- L0、隔离 L1 与 L2 为 GREEN；L3 fresh-cache 仍是 `NOT RUN`，见
  `mod_xenoamess_quality_of_life/docs/acceptance-report.md`。

## 冻结发布物料

| 物料 | SHA-256 |
|---|---|
| `mod_xenoamess_quality_of_life-v1.0.0.manifest.json` | `4df8d265bdba2cf31d59fb38714a9bb7515204e61ca98852d6b10caab86e8228` |
| `mod_xenoamess_quality_of_life-v1.0.0.zip` | `f573b879a2e3a2dee8321e04b26e3983a12a10fdd0db071642b823f87c0b6b2f` |
| `thumbnail.png`（ZIP 内） | `832e36c9394e6ed74aa8669507d55486ceacc0403f49daa8b456fc3cb1067fe3` |

ZIP 解压后顶层目录为 `mod_xenoamess_quality_of_life/`，共有 19 个 runtime 文件。Canonical Workshop BBCode 为
`workshop/xenoamess_quality_of_life_description.bbcode`；当前 UTF-8 大小 2,879 字节，低于 Steam 8,000 字节上限。

## 推送机准备

1. 使用拥有目标 Steam Workshop 物品的账号登录 Steam，并确认安装的 CK3 为 1.19.0.6。
2. 克隆或更新仓库，至少取得最新 `master` 和 `xqol-v1.0.0` tag。
3. 下载 Release 资产并核对上表 SHA-256：

```powershell
gh release download xqol-v1.0.0 `
  --repo XenoAmess/ck3_eternal_recurrence `
  --dir .\xqol-v1.0.0-release
Get-FileHash .\xqol-v1.0.0-release\* -Algorithm SHA256
Expand-Archive `
  .\xqol-v1.0.0-release\mod_xenoamess_quality_of_life-v1.0.0.zip `
  -DestinationPath .\xqol-v1.0.0-staging
```

4. 确认 `xqol-v1.0.0-staging/mod_xenoamess_quality_of_life/descriptor.mod` 中没有 `remote_file_id`，并运行：

```powershell
& tools\.venv\Scripts\python.exe tools\build_xenoamess_quality_of_life_release.py `
  --verify .\xqol-v1.0.0-staging\mod_xenoamess_quality_of_life `
  --manifest .\xqol-v1.0.0-release\mod_xenoamess_quality_of_life-v1.0.0.manifest.json
```

5. 在用户目录创建一个**新的**外层 descriptor：

`Documents/Paradox Interactive/Crusader Kings III/mod/mod_xenoamess_quality_of_life.mod`

```text
version="1.0.0"
tags={
	"Gameplay"
}
name="XenoAmess的体验优化"
picture="thumbnail.png"
supported_version="1.19.0.6"
path="<推送机上的绝对 staging 路径，使用正斜杠>"
```

首次上传前不得预填任何既有产品的 item ID，也不得把 `remote_file_id` 写进内层 descriptor。

## CK3 槽位与启动方式

先确认没有 CK3 或 PDX Launcher 在运行。推送全程复用项目已有的
`xar_autoplayer.locking.exclusive_launch_lock`；不要另造锁。可在一个单独终端持有槽位：

```powershell
$env:XQOL_CK3_EXE=(Resolve-Path '<Steam库>\steamapps\common\Crusader Kings III\binaries\ck3.exe').Path
& tools\.venv\Scripts\python.exe -c "import os,sys; from pathlib import Path; sys.path.insert(0,r'ck3_autonomous_player/src'); from xar_autoplayer.locking import exclusive_launch_lock; p=Path(os.environ['XQOL_CK3_EXE']); print('waiting for CK3 slot...',flush=True); c=exclusive_launch_lock(p); c.__enter__(); print('CK3 slot acquired; press Enter only after launcher is closed',flush=True); input()"
```

如果槽位正在被其他项目占用，让该命令继续等待。不要杀掉别人的 CK3。槽位取得后，在另一个终端通过 Steam 启动 PDX Launcher：

```powershell
Start-Process 'steam://rungameid/1158310'
```

不得直接运行 `dowser.exe`；那条路径没有可用的 Steam API 初始化。

## 首次隐藏上传

1. PDX Launcher → `Mod 库` → `上传 Mod`。
2. 选择新的 `XenoAmess的体验优化` 外层 descriptor；再次确认展示的内容路径是 Release staging，而不是仓库源目录。
3. 标题使用 `XenoAmess的体验优化 / Quality of Life`。
4. 描述从 `workshop/xenoamess_quality_of_life_description.bbcode` 整段复制，并从输入控件回读确认，而不是只检查剪贴板。
5. 标签选 `Gameplay`；首次提交保持**隐藏**，不要在 fresh-cache 验证前公开。
6. 若 Steam 显示新的 Workshop Legal Agreement，停在协议页交给账号所有者本人处理；自动化不得代为接受。
7. 上传成功后，在
   `%LOCALAPPDATA%/Paradox Interactive/launcher-v2/logs/launcher-YYYY-MM-DD.log`
   保存 `Publishing mod succeeded` 的时间与上下文。
8. 从用户目录外层 `.mod` 读取启动器写回的全新数字 `remote_file_id`。同时确认上传 staging 的内层 descriptor 被启动器临时注入的是同一个 ID。关闭 Launcher，再按下持锁终端的 Enter 释放槽位。

## ID sidecar 与 fresh-cache

下面用 `$itemId` 表示全新的 Workshop item ID。ID 只进入用户目录外层 `.mod`、一次性 sidecar manifest 和 Steam cache；不得提交进产品内层 descriptor。

从 tag 建立独立 clean worktree，再生成 ID-bearing sidecar：

```powershell
$itemId='<新 item ID>'
$tagTree=Join-Path $env:TEMP 'xqol-v1.0.0-tag'
git worktree add --detach $tagTree xqol-v1.0.0
& tools\.venv\Scripts\python.exe "$tagTree\tools\build_xenoamess_quality_of_life_release.py" `
  --source "$tagTree\mod_xenoamess_quality_of_life" `
  --release --workshop-item-id $itemId `
  --output "$env:TEMP\xqol-$itemId-sidecar\mod_xenoamess_quality_of_life"
```

把现有 numeric cache leaf **移动到备份目录，不要在不核对路径时递归删除**，随后从 Steam 控制台执行：

```text
workshop_download_item 1158310 <新 item ID>
```

只有从空路径重新生成的
`<Steam库>/steamapps/workshop/content/1158310/<新 item ID>`
才可作为远端证据。对它执行严格核验：

```powershell
& tools\.venv\Scripts\python.exe tools\build_xenoamess_quality_of_life_release.py `
  --verify '<fresh cache 绝对路径>' `
  --manifest "$env:TEMP\xqol-$itemId-sidecar\mod_xenoamess_quality_of_life-v1.0.0.manifest.json" `
  --workshop-cache
```

预期为 19/19 文件 GREEN；该模式只允许内层 descriptor 的正确 ID 注入和启动器换行规范化。

## L3：MCP-first fresh-cache 实机复验

最新 `master` 的 runner 支持 `--source`，可把刚通过 strict verify 的 fresh cache 作为唯一产品源。先按
`mod_xenoamess_quality_of_life/docs/acceptance-plan.md` 准备 exact-build native bridge，再运行：

```powershell
& tools\.venv\Scripts\python.exe tools\run_xenoamess_quality_of_life_acceptance.py `
  --source '<fresh cache 绝对路径>' `
  --bridge-dll '<xar_ck3_bridge.dll>' `
  --bridge-injector '<xar_ck3_bridge_injector.exe>'
```

这仍以 MCP 完成 readiness、暂停状态和前后 paused snapshot；appointment score、变量与 flag 继续由已提交的引擎 fixture 断言。只有最终 `RESULT: GREEN` 才能把验收报告 L3 改为 GREEN。记录 artifact 路径、顶层与 cell report SHA-256、MCP readiness SHA-256、item ID、fresh-cache manifest hash 和 launcher 成功时间。

## 公开与远端回读

L3 GREEN 后才在 Workshop 网页把可见性改为公开。随后匿名回读至少确认：

- item ID、标题与 `visibility=0`；
- 描述只规范化 CR/LF 与末尾换行后，逐字符等于 canonical BBCode；
- preview 下载件为 640×640 PNG，SHA-256 等于 `832e36c9394e6ed74aa8669507d55486ceacc0403f49daa8b456fc3cb1067fe3`；
- 页面中的 commit-pinned GitHub raw 主图实际加载；
- Steam cache 再次 strict verify 仍是 19/19 GREEN。

## 上传后恢复与仓库回填

Launcher 会把 ID 临时写入上传 staging 的内层 descriptor。上传证据保存后，必须从 clean tag 重新运行无 ID 构建，恢复正式树：

```powershell
& tools\.venv\Scripts\python.exe "$tagTree\tools\build_xenoamess_quality_of_life_release.py" `
  --source "$tagTree\mod_xenoamess_quality_of_life" `
  --release `
  --output '<正式 staging 路径>/mod_xenoamess_quality_of_life'
```

重建后确认正式 staging 与仓库内层 descriptor 均不含 `remote_file_id`；用户目录外层 `.mod` 保留新 ID，并把 `path=` 恢复为推送机日常开发路径或明确停用，避免误加载旧 staging。

最后回填并提交：

- 本文的 Workshop item ID、公开 URL、上传时间和 launcher 日志证据；
- `mod_xenoamess_quality_of_life/docs/acceptance-report.md` 的 L3 结果与 artifact/hash；
- fresh-cache sidecar manifest SHA-256 与远端 preview SHA-256；
- 若正文有任何调整，同步更新 canonical BBCode 后再回读。

不要提交用户目录外层 `.mod`、Steam cache、ID-bearing sidecar 或大型 live artifact。
