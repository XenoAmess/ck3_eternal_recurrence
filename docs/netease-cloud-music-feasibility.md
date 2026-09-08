# CK3 内播放网易云音乐：音乐播放器机制与可行性研究

状态：**research / NO-GO（纯 CK3 Mod）**

研究日期：2026-09-08（Asia/Shanghai）

目标游戏版本：Crusader Kings III 1.19.0.6（Scribe）

## 1. 结论与停止条件

在同时满足以下约束时，当前没有可施工的实现方案：

1. 音乐来自网易云音乐在线服务，而不是随 Mod 分发或预先放入 Mod 的本地音频；
2. 不使用“本地播放桥”；
3. 不使用外部伴随进程或伴随线程；
4. 功能必须由正常的 CK3 Mod 完成，而不是修改、注入或替换游戏可执行文件；
5. 最终应能作为常规 Mod 使用，而不是只在开发者调试模式下工作的实验。

CK3 现有 Mod 接口只能把**启动时已经注册**的 FMOD event 或 Mod 虚拟文件系统中的音频文件交给游戏音乐系统。没有发现脚本或 GUI 可调用的 HTTP 客户端、任意 URL 播放、操作系统进程启动、系统协议唤起、WebView，或运行时动态注册音乐源的接口。因此，原始需求中的“如果可行再施工”门槛没有通过。

本轮已经停止所有功能施工：不创建 `mod_netease_cloud_music/`，不创建生成器，不创建伴随程序，也不安装或配置网易云账号凭据。仓库只新增本研究文档。

唯一仍有实质希望、且能真正做到“游戏内在线播放”的路线，是**网易云音乐与 Paradox/CK3 发行方共同完成厂商级原生集成**。它是商务合作和游戏引擎开发项目，不是 CK3 Mod 项目。

## 2. 取证基线

### 2.1 游戏与文件版本

本轮直接检查了本机 Steam 正式安装，而不是只依赖社区文档：

- 游戏目录：`D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III`
- `launcher/launcher-settings.json`：`1.19.0.6 (Scribe)`，raw version `1.19.0.6`
- `binaries/ck3.exe` SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- `game/music/_music.info` SHA-256：`385EC52A3BF98AB7501EBD4699D4993218EBCDBB9EA1BA08CE85CF6CE8E1D21B`
- `game/gui/jomini/music_player/music_player_view.gui` SHA-256：`6C02BE00D3554F9F3A59D736B9E107D092F1BD8C3DB35F5C65FD0CACBC7B4982`
- `game/gui/hud.gui` SHA-256：`1AE3F1371E0A9C43D0B62FC1C1F3A0CDBB0EAB9CF08B85545556CBF3D7386312`
- `game/common/scripted_effects/00_music_effects.txt` SHA-256：`F0271E7105559664BBEC693160487501FF71C5166E5F9C2E619B818C22D3427C`
- 游戏随附 FMOD Core/Studio 版本：2.2.11。

这些哈希用于限定结论适用的精确版本；未来 CK3 更新后应重新取证，不能把本报告永久视为引擎合同。

### 2.2 原生音乐数据库

`game/music/_music.info` 给出的音乐定义结构包括：

- `music`：音频 event 路径；
- `pause_factor`：曲目之间的停顿因子；
- `mood`、`prioritized_mood`：自动选曲及优先级；
- `is_valid`：按当前扮演/观察角色计算的有效条件；
- `can_be_interrupted`：能否被另一曲目打断；
- `years`、`months`、`days`、`calls`、`reset`：冷却规则；
- `dlc`：主菜单主题曲的 DLC 条件。

本体与已安装 DLC 的音乐目录共取得 241 个 `music =` 定义，241 个全部使用 `event:/...`，没有 `file:/...`、HTTP(S) URL 或 Windows 绝对路径。

原生音乐链路可概括为：

```text
CK3 script / GUI
        |
        v
已注册的 track key -> MusicPlayer C++ 数据模型
        |
        v
FMOD event:/...  或  Mod VFS 的 file:/music/...
        |
        v
CK3 音乐总线与原生播放器 UI
```

在当前暴露接口中，没有从上述链路通往 HTTP 客户端、网易登录态或动态 URL 的箭头。

### 2.3 原生播放器 UI 能做什么

`music_player_view.gui` 暴露的 C++ 数据模型调用包括：

- `MusicPlayer.OnTogglePlayPause`
- `MusicPlayer.OnNextTrack`
- `MusicPlayer.GetVolume` / `MusicPlayer.SetVolume`
- 选择类别、启用/禁用类别；
- 启用/禁用单曲；
- `MusicPlayer.OnSelectAndPlayTrack(MusicTrack.Self)`；
- 当前曲名和已播放时间。

HUD 入口调用 `ToggleMusicPlayer`。播放器的 density 滑块虽然留有绑定，但在 CK3 中明确标成 unused 并设为隐藏。

没有发现上一首、seek、搜索、文件选择、账号登录、动态播放队列、运行时新增 track、任意 URL 或外部媒体状态同步接口。类别文件只能引用已经存在的 track key；它不是动态数据源。

脚本层的 `play_music_cue` 和 `play_music_cue_once` 也只接收已经注册的 track key。二进制中的调试命令 `Music.PlayTrack`、`Music.StopTrack`、`Music.Reset` 同样围绕音乐数据库工作；附近错误文本包含 `No track specified`、`Could not find track`、cooldown、uninterruptable 和 disabled 等状态，没有显示其能接收文件路径或 URL。调试控制台也不是操作系统 shell。

### 2.4 当前 Mod 生态的实证

本机 Steam Workshop 缓存中有 83 个 CK3 Mod，其中 15 个含 `music/` 目录。对这些音乐目录的 160 个文本文件进行统计：

- 音乐定义总数：11,093
- `event:/...`：718
- `file:/...`：10,375
- HTTP(S) URL：0
- Windows 绝对路径：0
- `file:/...` 中 OGG：9,434，MP3：883，WAV：58
- 所有本地文件引用都位于 `file:/music/...`。

例如 Workshop item `2216659254` 的 `music/in_game/POD_music.txt` 使用：

```text
music = "file:/music/POD/Kingdom_of_Darkness.mp3"
```

对应 MP3 文件存在且以 ID3 头开始，类别文件把 track key 加入原生播放器。这证明 CK3 1.19.0.6 能播放 Mod 内 MP3/OGG/WAV，也同时证明该机制是**预注册的 Mod VFS 文件**，不是 URL 播放器。该路线属于本次明确禁止的本地音频方案，不进入施工。

另有一个大型 Mod 用 `sound/banks/*.bank` 与 `sound/GUIDs.txt` 注册自定义 FMOD event，证明自定义 bank 可以随 Mod 加载；它仍是构建时生成和随 Mod 分发的静态声音资产。

## 3. 更多候选路线逐项分析

| 候选路线 | 技术判断 | 是否满足当前约束 | 主要阻点 |
| --- | --- | --- | --- |
| 在 `music =` 中直接填写网易播放 URL | 没有可用证据，按当前 schema 与样本判断不可行 | 否 | 音乐数据库只见 `event:/` 与 Mod VFS `file:/`；网易 URL 还涉及登录、时效、版权与音质鉴权 |
| 自定义 FMOD bank + programmer instrument | 只有游戏宿主代码提供回调后才可能动态选源 | 否 | CK3 Mod 没有暴露 programmer-sound callback 或 FMOD Core API |
| 直接调用 FMOD `createStream(URL)` | FMOD Core 本身具有 URL 流能力 | 否 | “底层库有能力”不等于 CK3 Mod 有绑定；需要修改 CK3 原生代码或注入 DLL |
| CK3 GUI 内嵌网易 Web 播放器 | 当前不可行 | 否 | 未发现 WebView/CEF widget 或通用 `OpenURL(url)`；只有前端硬编码的 YouTube/Discord 方法 |
| Steam Overlay 浏览器 | 玩家可手动打开网页，但不构成 Mod 集成 | 否 | Mod 脚本不能调用 Steamworks 的任意网页 API；声音与状态不属于 CK3 MusicPlayer |
| 唤起 `orpheus://`、浏览器或系统媒体协议 | 当前不可行 | 否 | 未发现可供脚本/GUI 调用的 ShellExecute、CreateProcess 或协议处理接口 |
| CK3 调试控制台 / `run` / `Music.PlayTrack` | 只能控制已注册 cue | 否 | 不是 OS shell，不能完成 HTTP、登录或动态注册；且调试模式不是正式 Mod 路线 |
| 利用 multiplayer、telemetry 或 Paradox SDK 网络功能 | 不可复用 | 否 | 这些是引擎内部的特定服务，没有向 Mod 暴露任意请求接口 |
| Steam Workshop 高频更新歌单 | 只能发布静态内容包 | 否 | 不是流媒体；更新、下载和游戏重启均在播放前发生，还需要曲目分发授权 |
| 与网易合作后发布静态授权音乐包 | 技术上可行 | 只满足“曲目来自网易曲库”的弱解释 | 仍不是网易云账号、歌单、搜索或在线播放；每首曲目需取得分发许可 |
| 网易厂商 API + Paradox 原生引擎改造 | 条件式可行，是唯一完整路线 | 条件满足后可以 | 同时需要网易商务/技术授权与 Paradox 的游戏原生开发，不是 Mod 能力 |
| DLL 注入、内存 hook、替换 FMOD/EXE | 原理上可能获得网络和 FMOD API | 否 | 不属于受支持 CK3 Mod，版本脆弱，无法作为普通 Workshop Mod 交付 |
| 官方 `ncm-cli` | 能在线搜索、登录和播放 | 否，用户明确禁止 | 它必然是 CK3 之外的进程，Windows 播放还依赖 mpv |
| 本地音频导入、目录映射、WebDAV/命名管道伪文件 | 有些变体可能让 CK3 看见“文件” | 否，用户明确禁止 | 本质仍是本地播放桥，且没有网易账号/歌单/播放器状态语义 |

### 3.1 为什么 FMOD 的网络能力不能直接解锁 Mod

当前游戏附带 FMOD 2.2.11。FMOD Core 的 `System::createStream` 确实可以接受文件名或 URL；FMOD Studio 的 programmer instrument 也可以在运行时由游戏代码指定声音。但是二者都要求**游戏宿主代码主动调用 API 或处理 callback**。

一个 `.bank` 文件只能描述事件、总线和预构建资源，不能自行把新的 C++ callback 注入 CK3。现有 CK3 track 定义也没有暴露 `createStream` 的参数、请求头、cookie、DRM、刷新回调或字节流提供器。因此：

> FMOD 可以播放网络流，不推出 CK3 Mod 可以让 FMOD 播放网络流。

如果未来 Paradox 暴露 `IMusicStreamProvider` 一类正式扩展点，FMOD 路线才值得重新评估。

### 3.2 为什么 Steam Overlay 不是隐藏的游戏内方案

Steamworks 为**游戏开发者**提供 `ISteamFriends::ActivateGameOverlayToWebPage`，能把任意完整 URL 交给 Overlay 浏览器。当前 CK3 GUI 文件中只找到 `FrontEndMainView.OnOpenYoutubeUrl` 和 `OnOpenDiscordUrl` 两个硬编码动作，没有能传入任意 URL 的 Mod 调用。

即使玩家手动用 Shift+Tab 打开网易云网页，音频、登录、暂停、音量、曲名和队列仍属于 Overlay 页面，不属于 CK3 音乐总线和 `MusicPlayer` 数据模型。这只是同时开着网页听歌，不是“CK3 Mod 中播放”。

### 3.3 为什么二进制内部出现 HTTP/进程符号仍不能算接口

`ck3.exe` 及依赖库必然含网络、Steam、Paradox 服务、Windows import 等内部能力。本体脚本、GUI 和音乐 schema 中没有发现对应的通用 callable。能在二进制字符串或 import table 中看见 `HttpRequest`、`CreateProcess`、`ShellExecute`，只证明游戏程序自身使用过这些平台能力，不能证明数据型 Mod 可以调用它们。

本报告采用的判定标准是“存在可由普通 Mod 稳定调用的公开数据/脚本/GUI 合同”，而不是“进程地址空间里存在某个函数”。

## 4. 网易云音乐官方接入边界

### 4.1 个人开发者路线

网易云音乐个人开发者平台当前公开的是官方 `ncm-cli`：支持 Windows/macOS/Linux、搜索、登录、歌单和播控；Windows 的音频后端是 mpv。官方 FAQ 明确说明个人开发者暂不支持直接接入开放平台 API，目前个人应用只提供 CLI；CLI 必须登录，也受曲目版权和账号权益限制。

这条路线在一般桌面集成中有价值，但由于它是独立进程，已经被当前约束明确排除。本仓库不会围绕它继续施工。

### 4.2 厂商合作路线

网易开放平台的 SDK 介绍把 PC 列为商务合作时应声明的终端类型之一，并说明音乐服务不是免费提供，项目需经团队评估。这里的“PC”是**可提出合作的终端类别**，不是“已有可直接嵌入 CK3 的 Windows SDK”的证明。

公开 OpenSDK 快速开始目前是 Android 实现：AndroidX、Gradle/Maven、Kotlin/Java API、Android `Application`、`AudioManager`、JNI 播放层，最低 Android API 19。它不能装入 Windows 版 `ck3.exe`。

厂商 API 文档显示，正式接入至少涉及：

- 网易分配或审核的 app、channel、device type、OS 等标识；
- appId/appSecret、RSA 签名与 access token；
- 匿名/实名登录切换和版权/会员鉴权；
- 搜索、歌单、曲目详情、临时播放资源与音质能力；
- 稳定且唯一的 deviceId、真实终端出口 IP、网络状态；
- `startplay`/播放结束等播放数据回传；
- 两个账号与两台设备的验收、上线审核；
- 产品交互、视觉稿和品牌使用审核。

因此厂商路线不是拿到一个 URL 填进 `music.txt`，而是完整的授权播放器产品接入。

### 4.3 服务条款边界

网易云音乐服务条款（2025-09-03 生效版本）禁止通过未经开发、授权或认可的第三方兼容软件/插件使用服务，也禁止逆向工程，以及未经同意复制、修改客户端与服务器交互数据或制作相关衍生插件/服务。内容和品牌也需获得相应授权。

所以以下方向不应成为替代实现：逆向 `weapi/eapi`、复制客户端 cookie/token、抓取和刷新临时播放 URL、解密 `.ncm`、绕过 visible/会员/区域判断，或把网易曲目重新打包进 Workshop。它们既不能解决 CK3 引擎接口缺口，也绕开了明确存在的官方接入流程。

## 5. 唯一完整的条件式方案：双方官方原生集成

如果目标必须是“在 CK3 自身 UI 和音乐总线内浏览并播放网易云在线内容”，合理的目标架构是：

```text
CK3 原生 C++ / Jomini 扩展
        |
        +-- 网易批准的登录与授权 UI
        +-- 搜索、歌单、版权与音质鉴权
        +-- 动态 MusicTrack / queue 数据模型
        +-- 临时资源刷新或网易提供的 Windows 播放组件
        +-- 播放数据回传与设备生命周期
        |
        v
CK3 持有的 FMOD/Core 流或经批准的原生播放内核
        |
        v
CK3 MusicPlayer：曲名、进度、暂停、下一首、音量、退出清理
```

这条路线没有外部伴随进程，声音也可以进入 CK3 的音量、暂停和生命周期管理；但前提是两侧分别补足当前不存在的能力。

### 5.1 需要网易确认的事项

1. 是否接受“Windows PC 单机游戏内音乐播放器”这一产品与终端形态；
2. CK3 全球发行地区中可提供哪些曲库和账号权益；
3. Windows 应使用厂商 API 还是尚未公开的原生 SDK；
4. 登录、token、DRM、临时 URL、音质和缓存的允许实现；
5. 播放数据回传、deviceId、IP、隐私告知和验收合同；
6. Steam/Paradox Mod 或游戏更新渠道是否属于获准分发形态；
7. 名称、图标、曲名/封面/歌词展示和品牌审查；
8. 费用、调用量、SLA、下线和曲目撤权后的行为。

### 5.2 需要 Paradox 确认或实现的事项

1. 由官方在 CK3 可执行文件中集成网易能力，或提供受支持的原生扩展 ABI；
2. 向 Mod/扩展提供安全的异步 HTTP、凭据存储和授权回调；
3. 支持运行时增删 MusicTrack、动态队列、搜索结果和封面；
4. 把动态流接入 CK3 音乐总线，处理暂停、音量、存读档和退游；
5. 明确 Windows、Linux/Steam Deck、macOS 的支持矩阵；
6. 提供不会随小版本轻易破坏的兼容合同与 Workshop/launcher 分发政策。

若 Paradox 不参与，普通 Mod 作者无法从仓库侧单独补出这些 C++ 绑定。

## 6. 可以继续做的研究，但尚未获得施工授权

以下工作不需要假装已有实现，但能降低商务或引擎层的不确定性：

1. 向网易开放平台提交不含代码的厂商预咨询，明确 PC 游戏形态、授权范围和 Windows 技术交付物；
2. 向 Paradox Modding/开发团队询问动态音频 provider、任意 URL/WebView、Steam Overlay binding 和原生插件 ABI 是否存在未公开支持计划；
3. 在 CK3 每次大版本更新后，重新检查 `_music.info`、播放器 GUI/data model 与脚本文档；
4. 只有用户重新授权实验后，才用自有、无版权争议的短测试音频做隔离黑盒探针：
   - `music = "https://..."` 是否被明确拒绝；
   - 自定义 FMOD programmer instrument 是否会触发宿主 callback；
   - release 模式下是否存在未记录的通用 `OpenURL` GUI callable。

第 4 项本轮没有执行，因为它需要创建临时 Mod/资产并启动游戏，属于用户刚刚要求停止的施工与实验动作。即使其中任一探针意外成功，网易登录、鉴权、临时资源更新、状态同步和授权仍需分别解决，不能由单个“能响”的测试推导出整体可行。

## 7. 决策建议

当前决策应是：

- **纯 CK3 Mod：NO-GO，不施工。**
- **本地音频或外部播放器桥：技术上各有可行变体，但被用户明确禁止，不施工。**
- **非官方 API、解密、注入：不作为项目路线。**
- **静态授权曲包：只有在需求退化为“若干获授权曲目”时才成立，不是网易云在线播放器。**
- **网易 + Paradox 官方原生集成：条件式 GO；先做双方预咨询，再决定是否值得立项。**

在获得至少一方的积极书面答复前，不应创建 `mod_netease_cloud_music/` 空壳，因为空壳无法验证核心能力，反而会造成“已经进入可实现阶段”的错误预期。

## 8. 资料链接

CK3 / 音频：

- [CK3 1.19.0.6 本体文件镜像](https://github.com/jesec/ck3-mod-base/tree/base/1.19.0.6/base/game)
- [CK3 社区 Music modding 文档镜像](https://github.com/jesec/ck3-modding-wiki/blob/master/wiki_pages/Music_modding.md)
- [FMOD Core `System::createStream`](https://www.fmod.com/docs/2.03/api/core-api-system.html#system_createstream)
- [FMOD Studio Programmer Instrument](https://www.fmod.com/docs/2.03/studio/instrument-reference.html#programmer-instrument)
- [Steamworks Overlay 文档](https://partner.steamgames.com/doc/features/overlay)

网易云音乐官方资料：

- [个人开发者平台介绍](https://developer.music.163.com/st/developer/document?docId=c5cb8108c73b42c8bec8869b26a15738)
- [个人开发者使用引导](https://developer.music.163.com/st/developer/document?docId=9504d35aa41a47c6ac9830b2dbf48f94)
- [个人开发者 FAQ](https://developer.music.163.com/st/developer/document?docId=3b75ab8e475d41ca93d91ebd4dfd383f)
- [官方 ncm-cli 文档](https://developer.music.163.com/st/developer/document?docId=2327e302009c437eb02af48f63d6e514)
- [开放平台厂商平台概述](https://developer.music.163.com/st/developer/document?docId=2cab673ca11b43c0b9d26c84e693987e)
- [开放平台 SDK 介绍](https://developer.music.163.com/st/developer/document?docId=893c051f4593429f9266af9fadba828b)
- [Android OpenSDK 快速开始](https://developer.music.163.com/st/developer/document?docId=9f2f7f65197a42b7849bff35f85fb6a5)
- [厂商数据验收与发布上线](https://developer.music.163.com/st/developer/document?docId=4edf1dd9ff644031820598306ca51197)
- [厂商视觉设计规范](https://developer.music.163.com/st/developer/document?docId=8f0fed4ef0484cab9db5ab0d3deb07d4)
- [网易云音乐服务条款](https://y.music.163.com/g/yida/36a81250504747a19283b29e4e9ff38c)
