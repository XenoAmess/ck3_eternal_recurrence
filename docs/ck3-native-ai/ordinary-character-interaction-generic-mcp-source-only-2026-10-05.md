# 通用角色互动 MCP 源码整合记录（2026-10-05）

本记录状态为 **OFFLINE SOURCE_ONLY**。ROOT 实际导入 native 18 项、Python 9 项候选；聚焦源码检查共 **107 项通过**，另有 python-only 和 diff 检查通过。旧 stress 两项 SDK 计数断言错误原样保留，后续测试修正以独立回执追加。编译互证和源码测试不证明真实 CK3 互动消费、auto_accept 结果、儒家制度业务或 MCP exit 验收。native gate 保持 CLOSED。

## 公开输入与原生行为

新增 query/initiate 公开工具只收 interaction key、完整 uint32 recipient ID 和 expected public revision。Actor、PID、连接 generation 从实际绑定帧取得；key 使用 ASCII字母、数字及下划线，保留大小写。recipient 包含 generation 的完整32位 ID 不截断。Driver 将 public revision 映射到 native revision，wire 仍使用 expected_revision，没有 snapshot alias。

Provider 固定精确 .3 可执行 SHA 94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6，读 native final terms、六类实际角色、完整 Shown/CanSend、十项 Q100000 成本、auto_accept 和 answer。two-role 指公开输入；finalization 后六角色及合法重定向保留。零 declared options、null special payload 与 complete CanSend 的范围不扩大。

Durable claim 在实际发送前落盘，原生 owner/TLS/paused-frame 核验后只 queue 一次。ACK 始终 pending，auto_accept、没有 outgoing 窗口或新的 revision/连接/episode 都不产生 business PASS 或重试信用。下一真实意图需要 ROOT 冻结的独立实际业务 readback verifier 与一次消费 permit；本轮没有实际执行业务 release。

Private 默认 OFF，runtime/bridge 两 target 同受私有定义约束。ordinary executor 与 admission/stress 不覆盖；已有 admission/stress driver 方法及 generic profile helper 的 AST 保留。native002 原17项仅纠正换行，归一内容与 compiled001相同；第18项是只读文件 pins generator，生成 include 保留原 CRLF 精确投影。

## 冻结来源与证据

| 封包 | payload数 | INDEX SHA-256 |
| --- | ---: | --- |
| native final002 | 79 | 94ba76d3f5b98b7558b6a8610cdebc6f281117835955b88c33529ebc336ee21b |
| Python final002 | 46 | 44dd6a46a8789bb1b1d7261051104687adf403329121afa8a97b6f717d2d78fc |
| 独立有限审查 | 128 | f39c72529199f6b5e2c2f38d77fa0936e00bccec4f3edda6341599be0f34b3ea |

作者 DELTA/INDEX、合同及角色补充、实际测试源码、失败 stdio、ROOT INTENT/APPLIED/INPUTS/RESULT、独立反例和 immutable 引用保存在[无损文本证据包](evidence/ordinary-character-interaction-generic-mcp-source-only-2026-10-05.text-evidence.tar.gz)。包为 2241280 bytes，SHA 90954b51f35a2896874cd47ee21942d7e676c22b6dc8ca7ff800fcfd328f416d；494 个文本对象按内容 SHA 去重，覆盖 1447 个来源。

catalog.json 将每个来源映射到原始大小、SHA及对象；对象不转码、不纠正换行。二进制、packet、full Debug DLL、before 和大型消费者源码继续外置，仅保留实际 SHA/大小/来源。旧 Debug DLL为 15034880 bytes，SHA 2674227def2f758716c611a27e620724fe71095696b599686f3313c700b2b3b5，位于 C:\lgi1\build-on-001\xar_ck3_bridge.dll；它只绑定原001输入，不能代表最终 HEAD Release 或实机。

原 episode UNKNOWN 绕过和 Python001 六角色 false-refusal RED 均保留。前者从稳定 unresolved identity 移除 episode；后者移除 consumer 推断的后四角色必须 null 条件。Python002仅 contract/test 两目标改变，其余七目标逐字节同001。独立初次 MSVC/AST harness 环境和依赖失败、作者旧 fixture/registry 失败均未重写。

## 独立实际离线执行

实际 typed 方法、primitive binder 与 compact encoder 经 memory writer 向真实编译 production parser 提交六条 query/send：recipient 0x80000002、0x81000002、0xFFFFFFFE 和 public1→native7 完整保全；五个 key/ID/payload/alias 负例拒绝。真实编译 production leaf 在 synthetic callbacks 下保留额外 final roles，send/queue/clone 各一次、cleanup三次。

真实 leaf→production serializer 的同两份 query/initiate 字节经最终 Python 四条消费路径保留全六角色；八个负例、CanSend=false 零 initiate/零 claim、四种 UNKNOWN lineage 挑战通过。以上是实际源码或编译字节的离线夹具执行，不能当作真实 actor/game 预期或业务完成。

## ROOT 实际导入后检查

| 检查 | 实际结果 | unittest项数 | RESULT SHA-256 |
| --- | --- | ---: | --- |
| ordinary | PASS / exit 0 | 24 | 52a6eefd22051557b2351ccc54d8f17b07b4440888ce77e292022b98a26e0d16 |
| host | PASS / exit 0 | 13 | 675da7a7845b02585f95dfec8c7c817438d8a4a1279be411f68c16831c547028 |
| profile | PASS / exit 0 | 18 | c21b735246d902550242233fb197f60f9ef03103f6db5a4aeb856bf7067d0045 |
| stress | FAIL / exit 1 | 23 | e11ff9ef69870ca1d4bd20c28a32bf461ebf366979f74e9fe256ec7c3cf67179 |
| outcomes | PASS / exit 0 | 29 | 48bdc9bd3a8d9db9d319d84840e51440f8568307d7d795ec8fb1b1b770cd0481 |
| python-only | PASS / exit 0 | — | b2be0713a962306af7b046298393aedfb88a727b305a45df2ceda0d5587a8dbd |
| diff | PASS / exit 0 | — | a06f4d112005b9e7a259ca2c7dddeeb9606089b15a1e51dc75936b46e6d6707b |
| stress_corrected_append | PASS / exit 0 | 23 | f45ddc38378b80f24b5f5e346d4503604697c9f3c618c5834d42b55a0b270644 |

ordinary24 + host13 + profile18 + outcomes29 + corrected stress23 = **107**。此数不混入作者39 focused 检查，也不声称全部仓库测试均通过。python-only 实际在 2026-10-05 02:41:39Z exit0，ROOT报告13485，原 stdout 保留；diff exit0。

旧 stress 运行23项，两个 SDK旧计数 ERROR分别为160 !=158和18 !=16，exit1及全文保留在基础 archive。ROOT后续只改测试的 known tool names subtraction，无 production变化，23项于 2026-10-05T02:52:36.531328+00:00 实际通过。[追加修正回执](evidence/ordinary-character-interaction-generic-mcp-source-only-2026-10-05.root-stress-correction-025236.json)包含 APPLIED、before、脚本、INPUTS/RESULT和原 stdio 的无损 base64字节，SHA c58b66bf6abe607915c8e2b27f65a7a30a858f7374b27e513a3f57bf7dea06d4；基础 archive 中旧 FAIL/PENDING状态保持原样。

当前机器可读状态在[状态快照](evidence/ordinary-character-interaction-generic-mcp-source-only-2026-10-05.status.json)。后续 ROOT修正、build或实机证据应新增带日期的 append回执，绑定新 bytes/SHA；不得修改历史 RED。文档整理任务没有重跑产品检查。

## 尚未证明的能力

新 HEAD Release build、同一新epoch PID/profile/guard/session/HELLO、原生 getter真实当前 actor值、single command实际消费、auto_accept业务、产品 readback verifier/permit release、MCP exit业务、UI政治图、存档重载、真实 consensus和下一 engine日志仍不由本记录证明。历史 engine证据及旧 Debug编译不外推为本轮业务通过。
