# CK3 家徽大源码 MCP v2 传输合同

> 状态：`native-live-text-roundtrip-passed / native-framebuffer-pending`（2026-09-15）
> 适用版本：CK3 `1.19.0.6`，`ck3.exe` SHA-256
> `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
> 传输实现提交：`87d2b954`；live runner：`05b54e26`；原生规范化比较器：`547daebb`

## 1. 结论边界

旧的 128 KiB 数字是单请求 `ck3_probe_coat_of_arms_source_v1` 的开发桥合同，不是 CK3 引擎上限。
v2 通过四个 MCP 工具在 Python 侧有界组装源码，全部分块到齐并验证后，才向原生桥发出一次完整请求：

1. `ck3_begin_coat_of_arms_source_upload_v2`
2. `ck3_append_coat_of_arms_source_chunk_v2`
3. `ck3_commit_coat_of_arms_source_upload_v2`
4. `ck3_abort_coat_of_arms_source_upload_v2`

当前 v2 的 **开发传输资源上限**是 512 KiB；它不是网页产品图层上限，也不是 CK3 引擎上限。网页仍允许用户输入任意正预算，
资源不足时由网页任务状态机显式失败并保留恢复状态。v2 的 512 KiB 只覆盖当前 hunter v4（380,862 bytes）的原生验收需要。

## 2. 有界合同

| 项目 | v2 固定值/规则 |
| --- | --- |
| 完整源码 | 1–524,288 ASCII bytes；无 NUL；提交时必须已是 CRLF |
| 分块 | base64；每块 1–49,152 decoded bytes；最多 32 块 |
| 完整性 | 每块 decoded bytes + SHA-256；整体 bytes + SHA-256 |
| 顺序 | `chunk_index` 必须从 0 严格递增；重复或越序立即销毁会话 |
| 编码 | 必须是 canonical base64，包括零 padding bits |
| 会话 | 128-bit 随机 ID、单调 generation、60 秒 TTL |
| 资源预算 | 最多 2 个会话；按声明总量预留，进程总预留不超过 768 KiB |
| 意图绑定 | 每块和 commit 重复绑定 revision、apply、game version、exe SHA |
| 页面绑定 | begin、commit 前、原生返回后均复核同一个 exact frontend/gameplay binding |
| 原生调用 | 缺块、错误哈希、过期、冲突或绑定漂移时为 0 次；成功 commit 恰为 1 次 |
| 原生 frame | 完整 512 KiB 源码 base64 后仍低于既有 1 MiB named-pipe frame 上限 |

协议错误采用 fail-closed：会话被销毁，不能补传后继续，也不会留下可误 Apply 的半成品。abort 和 TTL 都释放预留资源。
public v1 仍保留 128 KiB 上限，避免未经版本协商的客户端得到行为漂移；只有 v2 commit 使用扩展后的内部原生传输。

## 3. 离线验收（2026-09-15）

官方 Python MCP SDK 2.0.0 已真实执行超过 128 KiB 的 `begin → 4 chunks → commit`，断言组装后的 source bytes/SHA
与输入一致，并断言 commit 前原生驱动调用次数为 0、commit 后恰为 1。聚焦 Python/MCP 回归为 35/35 GREEN，覆盖：

- 重复、越序、坏 chunk hash、非 canonical base64、非 CRLF、缺块、过期与 abort；
- 声明总量预留、会话资源预算和 frontend connection-generation 漂移；
- v1 的 128 KiB 拒绝行为保持不变；
- v1 Apply/Copy schema 与 v2 扩展后的 export 大小校验。

全新短路径 native build `C:\xb\coa-wp1-v2-final` 完成 830 个构建步骤，CTest 155/155 GREEN，且 fresh-build
依赖门禁为 `ck3_11906.hpp-recorded`：

| 产物 | bytes | SHA-256 |
| --- | ---: | --- |
| `xar_ck3_bridge.dll` | 3,095,552 | `9DDC30CAF4373F4370E597DE42A3FADE5DC70AE597511D6654BBC13D4D14C987` |
| `xar_ck3_bridge_injector.exe` | 39,936 | `880885ABBF26C0D4147CFB55B70C5608B581F40C4229099D44A610B5CD589137` |

source fingerprint 为 `548B280BCDC29290E1B7439FDEB8F15A2CAE75AD6FF1C341E291B4076F57E2CF`。

这些结果证明分块合同、MCP SDK、Python service/driver 和 native 构建链可用；下一节另外记录真实 CK3 的文本闭环。
文本闭环不证明原生 framebuffer 像素一致。

## 4. hunter v4 实机文本闭环（GREEN）

2026-09-15 运行 `mcp-hunter-v4-large-source-live12.json`，使用 exact CK3 1.19.0.6、上述 fresh-build DLL、Steam 离线模式和
独占共享槽位。runner 只调用官方 Python MCP client 与注入桥；报告固定记录 `uses_ocr/uses_keyboard/uses_mouse=false`。

| 项目 | 结果 |
| --- | --- |
| 输入 | 380,862 ASCII/UTF-8 bytes；14,006 行；SHA-256 `C4648E2C98D3503252D9A9A298B4A39E27A8F4C7269944E607F34F86B3C60571` |
| 分块 | 8 块；前 7 块各 49,152 bytes，末块 36,798 bytes；每块及整体 bytes/SHA 全通过 |
| Apply | `detected=true`、`applied=true`、源码 bytes/SHA 身份一致；唯一 commit 调用 0.101 秒 |
| 原生 Copy | 240,453 bytes；13,006 行；SHA-256 `C4BF2090BCACA0CCEC683829141ECCD48E7A4DF31E889B58A5C9DA3F9AC99040`；1.319 秒 |
| 计数 | 输入/回读均为 1,000 逻辑层、1,000 `colored_emblem` 块、1,000 `instance`；`textured_emblem=0` |
| 语义 | pattern、texture、color、mask、position、scale、rotation、depth、parent 九类顺序/数值检查全通过 |
| 生命周期 | 总耗时 176.632 秒；共享锁释放；job active process 1→0；最终 CK3 inventory 为空 |
| 报告 | 本机 process artifact `artifacts/coa-clipboard-probe-2026-09-08/mcp-hunter-v4-large-source-live12.json`；SHA-256 `81DBDEBF23088C77CC0189DCB486751E0F6085ADBEC6015F03B57E6E434DD150` |

输入与 Copy 的原始文本哈希不同是 CK3 的规范化，不是截断：CK3 改写空白与外层 key，把所有显式零旋转省略，并将归一化
`rgb { 1 0 0 }` 写成 byte-domain `rgb { 255 0 0 }`。比较器没有忽略这些字段：RGB 两种合法域先投影到同一个 `[0,1]`
语义值，数值容差仍为 `5.1e-7`；rotation 仅在输入全部显式为零且 Copy 全部省略时按引擎默认零判等。18 个颜色字段发生
上述等价写法变更，非零旋转丢失、颜色顺序变化或超容差变化仍会令门禁失败。

这是真实的 **380,862-byte** CK3 Apply → Copy 证据，因此已经推翻“超过 128 KiB 就不能导入”的猜测。它只证明当前 exact
build、当前页面路径和 380,862-byte / 1,000-instance 构造可接受；512 KiB 仍只是 v2 开发传输上限，不应冒充 CK3 引擎上限。

前驱 `live11` 完成了同一次大载荷 Apply/Copy，但旧比较器把上述两种规范化误报为颜色/旋转丢失，故保持 RED 且未覆盖；
`live12` 是修复比较器后的独立重跑和当前晋级证据。

## 5. 实机验收门禁与剩余边界

hunter v4 实机晋级必须同时保存：

- 输入原文 bytes/SHA、chunk 数、各 chunk bytes/SHA、会话 generation 和 exact-build binding；
- Apply 的 `detected/applied` 后置条件与耗时；
- 紧接着原生 Copy 的原文、bytes/SHA、结构计数和耗时；
- 输入与 Copy 若因 CK3 格式化而字节不同，分别保留原文，并比较 pattern、颜色、texture、mask、instance 顺序、变换和 depth；
- `colored_emblem` 块数、`instance` 数、完整代码 bytes/行数与浏览器模型元数据一致；
- 运行过程明确记录 MCP-only、OCR/keyboard/mouse=false、Steam 离线、共享锁释放及进程清理状态。

上述 Apply → Copy 门禁已经通过。framebuffer 或稳定空间像素摘要仍是单独证据级别，不能由文本 round-trip 替代，当前继续
标记 `native-framebuffer-pending`。

## 6. 复现命令

```text
cd ck3_autonomous_player
..\tools\.venv\Scripts\python.exe -m unittest tests.unit.test_coat_of_arms_source_upload_v2 tests.unit.test_coat_of_arms_source_upload_v2_bridge tests.unit.test_coat_of_arms_source_probe_v1_bridge tests.unit.test_coat_of_arms_source_export_v1_bridge -v

cd ..
call C:\PROGRA~1\MICROS~1\18\COMMUN~1\Common7\Tools\VsDevCmd.bat -arch=x64
py ck3_autonomous_player\native_bridge\tools\build_fresh.py --build-dir C:\xb\coa-wp1-v2-final --ck3-executable-path C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe

tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile C:\Users\1\DOCUME~1\PARADO~1\CRUSAD~1 --state-dir D:\ck3_coa_hunter_v4_mcp_live_20260915_r03 --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar-coa-hunter-v4-live12 --bridge-dll C:\xb\coa-wp1-v2-final\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-wp1-v2-final\xar_ck3_bridge_injector.exe --timeout 600 --large-source docs\coat-of-arms-fit-artifacts\xenoamess-hunter-v4\coat_of_arms.txt --output artifacts\coa-clipboard-probe-2026-09-08\mcp-hunter-v4-large-source-live12.json
```

以上命令由 `cmd.exe` 执行。
