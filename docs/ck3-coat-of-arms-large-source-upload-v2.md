# CK3 家徽大源码 MCP v2 传输合同

> 状态：`mcp-static-ready / native-live-pending`（2026-09-15）
> 适用版本：CK3 `1.19.0.6`，`ck3.exe` SHA-256
> `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

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

这些结果只证明分块合同、MCP SDK、Python service/driver 和 native 构建链可用。尚未把 hunter v4 送入真实 CK3，
因此当前不能声明“大于 128 KiB 已被 CK3 reader 接受”，也不能声明原生 Copy 无规范化或原生像素一致。

## 4. 实机验收门禁

hunter v4 实机晋级必须同时保存：

- 输入原文 bytes/SHA、chunk 数、各 chunk bytes/SHA、会话 generation 和 exact-build binding；
- Apply 的 `detected/applied` 后置条件与耗时；
- 紧接着原生 Copy 的原文、bytes/SHA、结构计数和耗时；
- 输入与 Copy 若因 CK3 格式化而字节不同，分别保留原文，并比较 pattern、颜色、texture、mask、instance 顺序、变换和 depth；
- `colored_emblem` 块数、`instance` 数、完整代码 bytes/行数与浏览器模型元数据一致；
- 运行过程明确记录 MCP-only、OCR/keyboard/mouse=false、Steam 离线、共享锁释放及进程清理状态。

只有实机 Apply → Copy 完成后，本合同才可从 `native-live-pending` 提升。framebuffer 或稳定空间像素摘要仍是单独证据级别，
不能由文本 round-trip 替代。

## 5. 复现命令

```text
cd ck3_autonomous_player
..\tools\.venv\Scripts\python.exe -m unittest tests.unit.test_coat_of_arms_source_upload_v2 tests.unit.test_coat_of_arms_source_upload_v2_bridge tests.unit.test_coat_of_arms_source_probe_v1_bridge tests.unit.test_coat_of_arms_source_export_v1_bridge -v

cd ..
call C:\PROGRA~1\MICROS~1\18\COMMUN~1\Common7\Tools\VsDevCmd.bat -arch=x64
py ck3_autonomous_player\native_bridge\tools\build_fresh.py --build-dir C:\xb\coa-wp1-v2-final --ck3-executable-path C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
```

以上是 `cmd.exe` 命令，不依赖或调用 PowerShell。
