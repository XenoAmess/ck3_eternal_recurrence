# Steam 创意工坊发布（PDX 启动器上传器）

2026-08-17 与 2026-08-21 发布实测（启动器版本 2026.10-rc.1）。启动器行为来自日志
（`%LOCALAPPDATA%\Paradox Interactive\launcher-v2\logs\launcher-YYYY-MM-DD.log`），远端结论另以 Steam API、
公开 HTML 和从空路径下载的 Workshop cache 逐项验证。

## 物料清单

| 项 | 位置 | 要求 |
|---|---|---|
| 外层 .mod | `Documents\Paradox Interactive\Crusader Kings III\mod\<name>.mod` | 含 `path=` 指向 mod 本体；上传后启动器自动写回 `remote_file_id` |
| 内层 descriptor.mod | mod 本体根目录 | **禁止含 `remote_file_id`**（见下） |
| 预览图 | mod 本体根目录，文件名固定 **`thumbnail.png`** | 启动器按约定自动找（同各 dev mod 目录）；descriptor 里同时写 `picture="thumbnail.png"`；**< 1MB**，超限日志 warn "too large. Skipping."（上传照常成功，但预览图被静默跳过），约 900×500 PNG ≈ 700KB 是安全规格 |

## 血泪坑（全部实测复现）

### 1. 预览图约定：`thumbnail.png` 在 mod 根目录

启动器（含工坊预览图）认的是 mod 根目录下名为 `thumbnail.png` 的文件——这是 PDX 系惯例，
本机其他 dev mod（pod_greedy_head_of_faith、more_tenets_slots 等）全是这个布局。
自定义文件名/只写在 descriptor 里 → 工坊页预览图保持默认占位图，且无任何报错提示。

### 2. 上传器必须经 Steam 启动

直接运行 `launcher/dowser.exe` 虽能打开完整 Mod 上传表单，但 2026-08-21 实测创建物品失败：

```
Steam API is not initialized: Steam initialization failed. Steam is running,
but steam_appid.txt is missing.
```

关闭该实例并通过 Steam 客户端启动 CK3（等价于 `steam://rungameid/1158310`）后，同一 descriptor、描述与
staging 首次上传成功。不要通过复制 `steam_appid.txt` 绕开启动链；上传证据必须来自 Steam 初始化成功的实例。

### 3. `remote_file_id` 的 canonical 副本只能在外层 .mod

上传前内层 descriptor 必须没有 `remote_file_id`；更新上传的预写校验器见到该字段会直接拒绝：

```
Publishing mod to Steam failed: Saving descriptor.mod in mod sources failed:
... Loading mod descriptor failed: Mod descriptor validation failed
```

但校验通过后，启动器在首次上传和更新上传中都会把新/既有 ID 写进 staging 内层 descriptor，再把该版本发布到
Steam。仓库源、正式 manifest 与 GitHub ZIP 仍必须保持无 ID；上传完成后立即重建 staging，恢复 canonical
内容。排查方法：搜启动器日志 `Failed to publish mod`，错误链末尾就是真因。
（同理，descriptor 的 BOM 读路径能容忍，但回写路径不想赌，保持无 BOM。）

## 标准流程

1. 运行 L0：`py tools/validate_static.py`、计分 reference vectors 和
   `py tools/build_release.py --check`。这些步骤不会启动 CK3。
2. 开发候选运行 `py tools/build_release.py`；正式版本先保证 clean worktree 且 HEAD 有与 descriptor 一致的 `v<semver>` tag，再运行 `py tools/build_release.py --release`。1.0.0 输出 staging、`-v1.0.0.manifest.json` 和 deterministic `-v1.0.0.zip`，命令同时打印 manifest/ZIP SHA-256。
3. 发布前把用户目录外层 `.mod` 的 `path=` 临时指向上述 staging，保留其
   `remote_file_id="3784706360"`；不要把该字段写入 staging 内层 `descriptor.mod`。
4. 经 Steam 启动游戏启动器 → Mods → 上传 Mod → 选同一物品。Steam 上传源必须是 staging，不能是仓库 mod 源目录。
5. GitHub 候选发布附加同一次构建的 `.zip` 和 `.manifest.json`；记录 commit、manifest SHA-256
   与工坊物品 ID，使 GitHub 与 Steam 使用同一 staging 内容。
6. 上传后重建 staging 以移除启动器注入的内层 `remote_file_id`，再把用户目录外层 `.mod` 的 `path=` 恢复为开发目录，避免后续游戏误加载旧 staging。
7. 工坊网页：描述用 BBCode（`[h1]`/`[list]`，**不渲染 markdown**——别直接贴 README）；
   可见性默认"隐藏"，确认后改公开。
8. Steam 刷新缓存后运行 `py tools/build_release.py --verify <workshop-cache> --manifest <versioned-manifest> --workshop-cache`。该模式只规范化启动器对内层 descriptor 的 LF/CRLF 与末尾换行重写，以及其强制注入的唯一
   `remote_file_id="<manifest workshop_item_id>"` 行；规范化后的 descriptor 及其余 84 个文件仍要求大小/SHA-256 完全一致，任何字段、顺序、ID、其他 mismatch 或 extra 继续判 RED。通过后再发布 GitHub draft 与工坊可见性。

### 4. 成功上传会把 `remote_file_id` 注入远端 descriptor

2026-08-21 的原版更新上传和白绮独立版首次上传均实测：即使 staging 内层 descriptor 在提交前没有 `remote_file_id`，
启动器仍会在点击上传时先把正确 item ID 回写进去，同时把 descriptor 统一改写为 LF 且末行不留换行，随后将其发布到 Steam。该行为不是允许仓库或
GitHub ZIP 携带此字段：预先存在该字段仍会触发 descriptor validation failure。正式 manifest 继续描述无字段的
canonical staging；`--workshop-cache` 只接受远端下载缓存中与 manifest `workshop_item_id` 完全相同的单行注入。

强制重下载时不能只覆盖旧工坊目录：Steam 不会删除 runner `/MIR` 曾留下的多余文件。先把整个 item 缓存目录
移出 `steamapps/workshop/content/1158310/`，再通过 Steam 控制台执行
`workshop_download_item 1158310 3784706360`；只有从空路径生成的新目录可以作为远端 manifest 证据。

同次发布还发现，tag 当时尚未设置 `.gitattributes`，长期工作树中的 LF 文件与 Windows clean checkout 的 CRLF
物化会产生不同 ZIP/hash。1.0.0 tag workflow artifact 已由独立 clean-tag worktree 在本机复现为完全相同的
manifest/ZIP hash，Steam 与 GitHub 随后统一使用这份 clean-checkout 产物；不得混用长期工作树的本地 ZIP。
发布后根 `.gitattributes` 已把后续文本 checkout 固定为 LF，并把 DDS/PNG/JPEG/ZIP 标为 binary，避免未来版本再次出现该分歧。

### 5. Workshop 截图实际硬限制为 2 MB

图片/视频编辑页文字声称单文件不超过 8 MB，但 2026-08-21 实测 3.2–4.8 MiB 的 2560×1440 PNG 会在提交时
弹窗拒绝：`预览图片不能大于 2 MB`。保持原分辨率、无裁切转换为 quality 90 的 JPEG 后，八张图片为
0.431–0.702 MiB，全部上传成功。验收 artifact 继续保留无损 PNG；Workshop 上传副本单独生成，不得进入 mod
staging。公开页 HTML 应按 `highlight_strip_item` 复核实际图片数。

### 6. Workshop BBCode 可直链 GitHub raw，但只用固定 commit URL

2026-08-21 对 Steam 公开页、GitHub 响应头与 Chromium 实测：Workshop 描述会把外链生成为
`<img src="..." crossorigin="anonymous">`，不会先代理到 Steam CDN。只有直接
`https://raw.githubusercontent.com/<owner>/<repo>/<40-char-commit>/<path>` 在当前行为下可靠加载：响应必须无
重定向、MIME 为 `image/jpeg` 或 `image/png`，并提供 `Access-Control-Allow-Origin: *`。本项目提交
`e7592964603546f860b5d59ba00626819d8e0523` 的 gallery JPEG 实测返回 `200 image/jpeg`、无重定向、CORS `*`
和 `Cross-Origin-Resource-Policy: cross-origin`。

两件当前公开 Workshop 物品提供了 Steam 端实证：Terraria Overhaul
`https://steamcommunity.com/sharedfiles/filedetails/?id=2811803870` 使用可变 branch raw URL；tPronouns
`https://steamcommunity.com/sharedfiles/filedetails/?id=3740445376` 使用完整 commit-pinned raw URL。后者是本项目
采用的形式。`github.com/.../blob/...` 返回 HTML；blob `?raw=1`、`github.com/.../raw/...` 与 GitHub Release
asset 都经过重定向，Release asset 最终还是 `application/octet-stream` attachment。它们在 Steam 同款
`crossorigin="anonymous"` Chromium 请求中均加载失败，禁止写进 BBCode。

GitHub raw 只用于描述正文，不会把图片加入 Workshop media strip；精选预览仍优先上传 Steam CDN。固定 commit
避免 `master` 改写图片，但仓库删除、私有化、历史重写或 GitHub 限流仍会使链接失效。Steamworks 常量
`k_cchPublishedDocumentDescriptionMax` 把描述限制为 **8000 UTF-8 bytes**，所以提交前必须按 UTF-8 字节数检查
整份 `workshop/description.bbcode`，不能按字符数或图片数量猜测。完整图片集留在 README，Steam 描述只放精简集。

本项目主物品 `3784706360` 随后完成活体验证：API 描述规范化 CRLF 后与仓库 BBCode 完全相同；公开 HTML 有八个
固定 commit gallery URL、八个 `crossorigin="anonymous"` 图片节点，桌面 Steam 客户端逐段滚动时八张都实际显示。
同次把四张历史 media strip 图替换为 `01_pact`、`02_reincarnation_shop`、`03_blessing_choice`、
`06_lifetime_contracts`、`08_courtier_essentials`、`10_death_settlement` 六张精选图，公开 HTML 精确包含六个
`highlight_strip_item`。此次只改描述与 media strip，没有重新上传 mod 内容包。纯描述保存后 API 的
`time_updated` 仍保持内容包时间，因此不能用该字段判断网页编辑是否生效，应比较远端正文并检查公开 HTML。

## 上传内容范围

启动器会上传 `path=` 指向的整个目录，所以正式路径必须指向 release staging。
`tools/build_release.py` 只允许根目录的 `descriptor.mod`、`thumbnail.png`，以及
`common/`、`events/`、`gfx/`、`gui/`、`localization/` 内明确允许的 CK3 文件类型；不会复制
mod 内 `tools/`、仓库文档、`__pycache__`/`.pyc` 或源素材。manifest 不放进 staging，避免改变
Steam 实际内容；它作为旁置追溯物料与 ZIP 一起发布。

构建器从同一开发树生成 production-only 投影：明确排除 selftest effect、死亡探针事件/on_action/effect 与
trait bridge GUI，并剥离混合文件中的 `XAR_ACCEPTANCE_ONLY` 区域；`XAR_RELEASE_ONLY` 注释行在 staging
中展开为生产逻辑。构建会扫描所有运行文本，任何 selftest/test flag/marker 或 marker 注释残留都直接 RED。
生产 smoke 场景也会先生成此投影，再 `/MIR` 到工坊缓存实机运行，因此不是只做文本检查。

## Vivhite 独立版首次上传

白绮独立版使用 `tools/build_vivhite_release.py` 和全新的外层 `.mod`。1.0.0 的新物品为
`3787304042`。首次上传时外层 descriptor 只含指向
formal staging 的 `path=`，不得预填原 mod 的 `3784706360`。启动器创建新物品后把新 ID 保存在独立外层
descriptor，同时临时写入 staging 内层 descriptor 并把该版本发布到 Steam；上传后必须重建 staging。
仓库内层 `descriptor.mod`、重建后的 formal staging、formal manifest 和 GitHub ZIP 继续保持无
`remote_file_id`，只有独立外层 descriptor 保留 canonical ID。

上传成功后，从 clean tag 另建不发布的临时 sidecar：

```powershell
py tools/build_vivhite_release.py --release --workshop-item-id <new-id> --output <temporary-output>
```

把新 item 的整个缓存目录移出 `steamapps/workshop/content/1158310/`，再执行
`workshop_download_item 1158310 <new-id>`。只对这次从空路径生成的目录运行
`build_vivhite_release.py --verify ... --workshop-cache`；验证通过后才公开 Workshop item 和 GitHub Release。

2026-08-21 首发时从空路径下载 `3787304042` 后，带 ID sidecar 对全部 27 文件验证 GREEN；1.0.0 sidecar
manifest SHA-256 为 `252bdd294a1e62a5a4d201fffc91e5581b4632f97058cf0d8ab16b74cb37ff74`。匿名 Steam API 返回
`visibility: 0`，1.0.0 公开页面精确包含八个实机 screenshot item。对应历史 GitHub Release：
`https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/vivhite-v1.0.0`。

同日 1.0.1 更新实测：Steam 启动链中的 PDX launcher 在 `2026-08-21T10:50:40.275Z` 记录
`Publishing mod succeeded`。匿名 API 的 `time_updated=1787309440`、内容 manifest
`5798322135786279034`、`visibility: 0` 与描述内 `Version 1.0.1` 同时生效；新预览图由 CDN 原样返回
640×640、821,769 字节，SHA-256 为
`3482a3ceb8d8fec5af2a23f3b10324ddd2297a8406067dec39851c87161dc164`，与 tag 产物逐字节一致。公开 HTML
精确包含九个 media strip item：八张实机截图加一张决议主视觉；BBCode 第一项也是该主视觉。

验证时先把旧 `3787304042` 目录完整移出缓存根，再执行 `workshop_download_item 1158310 3787304042`。
Steam 从空路径安装上述新 manifest 后，sidecar manifest SHA-256
`3af6032095e4c6b5a94dd0a82144a1bd307b1df32dfcb50e39b6aedf0bea4541` 对全部 27 文件 strict
`--workshop-cache` GREEN。随后重建 formal staging，恢复无 ID descriptor；formal manifest/ZIP SHA-256 分别为
`4b2cb5c58c19f90a9b7f9ce98afc7d99bdbf581d277adf0cc1c2259fdcfa2704` 与
`b5d7f276c128878ae3f6a7f28110840515f7ce585fc6bf2e3cb998d73b460c08`。官方 tag artifact 与公开 Release
下载件哈希一致：`https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/vivhite-v1.0.1`。
