# 地图正常退出 MCP 源码整合记录（2026-10-05）

本记录状态为 **OFFLINE SOURCE_ONLY**。ROOT 已实际应用 native 六处共享 hunk 与七个专用新文件、Python 五处共享 hunk 与六个新文件；本轮 rebase 前 ordinary24 + host13 + stress23 + outcomes29 + profile18 共 **107 项组合检查通过**；rebase 至 f861921e1 后，ordinary24 + stress23 + outcomes29 + profile18 共 **94 项 fresh 检查**及四项非 unittest 检查通过。作者编译、离线互操作、mock/pure 测试与 011 定向组合均有精确字节回执。组合 Release、真实 CK3 正常退出和存档完整性仍未验证，native gate 保持 CLOSED。

## 已实现的源码合同

能力 normal-exit-map-v1 仅支持精确 CK3 1.20.0.3 的暂停地图，private feature 默认 OFF，frontend revision 0 不支持。公开查询绑定 expected public revision；请求只接受 prepare_confirmation 或 confirm_desktop，并回传新鲜后端查询给出的上下文签名。公开无参数 observe 读取先前保留的 original HANDLE。query wire 闭合为十二个 key、mutation 为十三个 key；实际 endpoint 使用四字节 little-endian 长度加 compact UTF-8 JSON，public/native revision 由实际 driver 映射。

固定原生入口链为 timeline_widget/pause_menu_button → ingame_pausemenu/exit_button → ingame_resign_confirmation/descktop_button。每一阶段保留 Bridge Session 的独立一次性 consumed claim；query、revision、generation 和 reconnect 均不能重置已消费阶段。native_handled=false、响应未知、post-frame 丢失或 mailbox 漂移保留 UNKNOWN，不产生重发许可或退出成功。

发送 terminal 确认前，host 保留 original read-only process HANDLE，并绑定 exact PID 与 uint64 FILETIME。confirm/observe 单次等待最多五秒；timeout/failure 保留该 HANDLE、原请求、ACK、receipt clock 和 once claim。后续 observe 不新提交 native、不读取 live snapshot/guard、不重新打开 PID。仅已验证的实际 desktop dispatch-pending 加同一个原始 HANDLE signaled、实际 DWORD exit_code=0 能形成 typed orderly exit；消费者重算过程事实，不信任汇总 boolean。终局事实在 close 前落盘，close receipt IO 失败保留事实与错误。explicit close 只释放 ownership，不能制造进程退出证据。

源码准入要求本次实际 managed -userdir 的 inventory SHA、profile projection、pdx_settings.txt/dlc_load.json、启用 mod descriptor 顺序与全部 mod 文件 census/SHA，以及六个 exact stock GUI SHA。Python 拒绝任何 replace_path/archive 和 enabled-mod GUI 文件；native 拒绝 GUI-affecting replace_path/archive。有效支持范围受 Python 更窄规则约束。inventory 缺失必须 typed unavailable，未来 R8 的 PID/generation/profile/GUI 值未生成或借用旧 R7。官方 autosave checkbox 默认保持原样，保存与 autosave integrity 不由源码测试推断。

## 冻结来源与无损证据

| 来源 | indexed payload | INDEX SHA-256 |
| --- | ---: | --- |
| native009 full | 5661 | 30ea4f0b9d06b0d8953d93c5ef31c73b456d6b68b6a00fb5c25e273a31d3438f |
| native009 directed slice | 36 | 38b817da97321d1051d31634685e364eebf25780b238a9b74f0ffe6a6e5b70e3 |
| Python010 final002 | 1989 | 30d659d2a079b4d9f51e9cd285fe5200ab9e767dbca351cf33e31eec24766cb3 |
| composition011 | 91 | dc466741f4480709c2abdf6b1a760787d83eb5702d4f1457be088a87351c8745 |

Python 最终 INDEX 实际位于 Python010 根目录；review-package-002 为最终 DELTA、metadata、after 与 hunks 子包。native slice DELTA SHA 为 737e8bb24b1db8ebab2624c4f44c3b4070e5adb25d2cfc5876e711afb55693b9，Python 最终 DELTA SHA 为 12611022b9663397c92b24c01bab68e231d0841b7abfda9bd7f68f583c8b3b8f。011 验证 native 六处、Python 五处 directed diff 的正向与反向应用；共享 whole after 未覆盖已导入的 ordinary/admission/stress。

[无损文本证据包](evidence/normal-exit-map-generic-mcp-source-only-2026-10-05.text-evidence.tar.gz)共 2279903 bytes，SHA 0bedd83acbfae09cf4b3be54889b472cca780beacbdb457c0927f636bf9c18cd。catalog.json 按原来源记录 bytes/SHA，367 个内容寻址文本对象对应 7915 个来源引用，787 个入包来源已实际回读 SHA。其余 payload 明确为 frozen INDEX 元数据引用，本文档整理未再次读取全部源码，不将作者/011 的完整 SHA 检查冒充为本轮独立全量复验。文本保留原始 bytes，不转码或归一换行；packet.bin、EXE/DLL/OBJ、大片 source/before 与 stock GUI 保留外置。

native 全包共 270943976 bytes，未导入仓库。作者 final exit-only DLL 为 5396480 bytes、SHA 8b761c09ec2f4cb416508cf1c423902f659dfbbc34a281870271a8d8feefcb42，仅绑定 native009 原始 build004 输入，明确不包含普通角色互动 native18；不能称为 011 组合 Release。生产 parser EXE 492032 bytes、SHA e96e7c1373ecc73b6bbd8236e9c4c7fbd2520796207ffab2441f1bc18c4a59fd，其 source attestation 与实际调用回执均入文本证据。

## 已有检查的实际范围

作者 Build003 三个 source units 与 Build004 final provider 在 default-OFF/enabled 模式均以 C++20/W4/WX 严格 object 编译通过；Build002 完整 367-step DLL、Build003 stock manifest schema rebuild、Build004 backend signature echo rebuild 回执保留。它们是作者原始 exit-only 输入的离线编译，本文档任务未重编译。

生产 Python encoder 仅替换 write_all 捕获实际 endpoint 字节，再由实际 native production parser 消费：四个合法 query/action packet 接受，十三个腐化 packet 拒绝且 output 不变。exact uint64 FILETIME、signed int32 actor 域、closed fields/signature 的负例均绑定原包回执。这不证明 owner callback、菜单 transition 或自然退出已在真实游戏执行。

Python focused-tests-005 实际运行 60 项 mock/pure focused 与 18 项既有 profile regression；原始 stdout/stderr SHA 已回读。sdk-schema-005 实际 MCP 2.0.0 完整 schema 为 exit-only baseline broad162/profile19，各二十个非法输入拒绝、business callback 为零，556 Python 源码 before/after manifest 相等。这些是作者 exit-only 基线观测，不能当作最终组合主树的 SDK 工具总数。ROOT 主树与组合 SDK 的实际后续回执见下文；它们复用相同测试，不构成另外六十项。

## ROOT 本轮实际应用和组合检查

| 应用回执 | APPLIED SHA-256 |
| --- | --- |
| root-exit-native-hunks-integration-20261005-001 | 7c2fc5e570db375afcc97c97a957a490545863135c4de52c3a8db01cbbc2ff9f |
| root-exit-python-hunks-integration-20261005-001 | de9265d6d57851f24a1923ce96d3dde6d8db0525a8fcfc09934f8154e9979a64 |

| 检查 | 实际结果 | unittest 数 | RESULT SHA-256 |
| --- | --- | ---: | --- |
| ordinary | PASS / exit 0 | 24 | 21d0aff557fdbcae06c70f9040820da7ccffcc35034b1877880d83c90f86a9f7 |
| host | PASS / exit 0 | 13 | 43d431fb976f0f71653ec4069e33445f8563447f713fd9212ee431d5e50008a7 |
| stress | PASS / exit 0 | 23 | 895f43c83df8bc97b7406eab10c7ec02c7d2221c84838403fd1bd11b7135e861 |
| outcomes | PASS / exit 0 | 29 | b8e8b9ca77271c11bdaf1f0d850c93a16bc50bd51f62c8a209ad765a882e1a53 |
| profile | PASS / exit 0 | 18 | 530f232b46f49a385742946647af6301028ba312c7f98adb8be1e0ce4505640b |

上述 107 项不与作者 60/18 或上一轮 ordinary source-only 107 合并成新的统一测试总数。INPUTS、RESULT 与原 stdio 均绑定精确来源；没有因文档打包重跑检查。[机器状态](evidence/normal-exit-map-generic-mcp-source-only-2026-10-05.status.json)保留 ROOT 应用与检查事实，最终主树 rebound/schema 与 rebase 后检查收据已独立 append，原始 base snapshot 的 PENDING 状态仍保留为历史。

## 保留的失败及未验证边界

旧 baseline clone 长路径失败、Build001 工具 PATH 环境失败、Build002 相对 stock record schema 的旧编译输入与回执均永久保留。011 旧 reader 的 size-key/long-path 失败、Python composition-attempt-001/002 失败原文也保留；不得把失败原件改写为 GREEN。WinDefend Disabled/Stopped 与 COM Add 0x80041001 登记失败仍属环境 RED，已获授权的离线夹具不等于 Defender 配置成功，policy mutation=0。

R7 官方桌面 GUI 点击仅观察到进程/窗口消失，实际 CK3 exit_code 为 NULL，不能赋予 MCP 正常退出能力验收。组合 HEAD Release、未来同 epoch PID/profile/guard/session/HELLO、真实 getter/signature、三阶段 owner callback/UI transition、原始 HANDLE 的真实 Win32 观察、自然 exit_code=0、autosave/save integrity 均未验。后续 ROOT 检查或实机结果用新的 hash-bound append 收据记录；本记录不宣称 business/MCP exit PASS。

## ROOT 主树测试修正、组合 SDK 与 rebase 后追加

[追加回执](evidence/normal-exit-map-generic-mcp-source-only-2026-10-05.root-rebase-rebound-sdk-append.json)记录原始 APPLIED、失败及修正后的执行、完整 schema/source manifest、当前 HEAD source checks；精确原 bytes 同时在无损 archive 中按 SHA 去重。

012 原 INDEX 3fb2f9ab95331bad3cb7188705ff2b6c90cc9855cb03d03a85730d001ff46e4b（16 payload）原样保留。三个 production unit 文件共 41 项（contract6/observer12/integrated23）被 ROOT 导入；旧 v2 十九项仍属 external auxiliary。初次 main41 exit1、十七个 NameError 来自适配移除 ROOT 后残留 TemporaryDirectory(dir=ROOT)，原 stderr SHA 9845af5addf6a9f4d467a176be780b9acacab5a478f7cccc525c6e17da871ff9 未改写。

ROOT setup 补全 ROOT=Path(tempfile.gettempdir()) 后 main41 + external19 分别 exit0；corrected RECEIPT SHA 1d054c0b467547a3b5cf680fd93317092bdea139a6f989931000c6421ffbaffb。本文档整理只从 frozen012 插入同一 global 定义，重建字节精确匹配 ROOT current main SHA d66ec3222b45b287dc45b913341f94dd0981f9d701e8641c7b7d51af08bf884e，并静态确认二十三个 integrated test method AST 未变，未运行这些测试。013 独立回执 INDEX 233f18ed3eeaf4feef12d929874dba40ed5bad15abf4af952f0b7423c91bef09（18 payload）及 REPORT 4cc24f25a46feb5d3cb90fcb8f899f3a0d42a1fcccf2dfe288a44b8cefb93e28 同时入包。41+19 是作者原六十项的主树重绑定，不是新增六十项，也不是已完成 CI 或真实 Win32 进程验收。

ROOT 实际组合 MCP 2.0.0 schema 为 broad165/profile21，每端二十个非法输入拒绝、business callbacks=0；完整工具列表 SHA 分别为 a7ae31d790f1a2488629e5407ec437a493fa5fb6ccd8b41d6cfc337f7e97aa20、df30e2306140475582340f48180b98320582f28f432c2a5d48f4c268313d5610。1092 source 的前后 manifest 原 bytes 相同，SHA 038b7c646aac24ecd8766bd07346251fbe06010bd49323c5ab13e10d53664f0d，RECEIPT SHA 7526c7a428a50d1931cbd7b8f192538529a9eb4dc2f21cab5c822b2fc15eb375。metadata/input parser 观察不计 MCP business exit PASS。

ROOT rebase 后实际 HEAD 为 f861921e137009cba1d739a6e53fba8c8965ee0b。独立 source 保全 SHORT-RECEIPT SHA 12579ce703eca3ab5d625d5a3efdc22bfecb44a65e3acfde8c6d3e0da0eb47f4 / INDEX 00bcddd9376ed9f2ce9b73aac5b4b0a390eb4d47e200a520b59110b162517bdc 验证四个冲突文件的九处独立 hunk、双方条款、MAA 三层 AST 与八项 runtime/bridge flag 路径保留；该 reviewer 未重跑 tests/build。ROOT rebase 的 RESOLVED 以及后续八命令 INPUTS/RESULT/stdio 均有原始字节。

| rebase 后检查 | 实际结果 | unittest 数 | RESULT SHA-256 |
| --- | --- | ---: | --- |
| ordinary | PASS / exit 0 | 24 | 32657085b0ac49fe3bb384f579816e9bba3f6895278c3975ab39caca2b46cd0f |
| stress | PASS / exit 0 | 23 | adb779aaf9cf6a515f01e10e48f4dea44e0c7a01d8360463cdcd09c923448ffb |
| outcomes | PASS / exit 0 | 29 | a4834277e85dcb50cee30415de8c416eca2f49d7d517305e21ca7ac39103d77b |
| profile | PASS / exit 0 | 18 | ea4fea9da53a0cc63681c672ccafe3a20423b30a57160e4111e32479743a50cb |
| product-static | PASS / exit 0 | — | 80730e12f421f1a7f5426016470550cd741a2c01d2c99d3f9f504b6e5f44a412 |
| product-build | PASS / exit 0 | — | 8ea5290e3e1efe529afa16f405b0581bf0e22f3a13b784a262326c8457007bd7 |
| c2-generation | PASS / exit 0 | — | 4f6f6694d34264c95cda8b361ba411e5b4da00dc8126b8ff2e2cc59090c1f89b |
| python-only | PASS / exit 0 | — | 82f0d12c66b3ee936d9e3c02e1b9caefa5198bc2fe4f2708d15ef27b4712e8da |

Fresh94 为 24+23+29+18；host13 生产源码未变，仅保留此前 PASS，未重复计入这九十四项。另有 product-static、70-file deterministic product-build、C2 generation 与 python-only 四项实际通过；python-only 实际完成于 2026-10-05T03:26:39.132059+00:00。源代码静态与 mod deterministic build 不能称为 native 组合 Release。当前 HEAD 最终 Release 和真实 map exit 保持 NOT_RUN，后续实际结果应另行追加。
