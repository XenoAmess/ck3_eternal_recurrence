# R58 pre-action 累计计数修正（源码采用／离线验证）

状态：`STATIC_READY / LIVE_NOT_RUN`。ROOT 已标准应用 F58 两路径 patch；本包仅读回实际 MAIN 两个源码文件，其完整字节与原 SOURCE-CHECK 的 after pins 相符。原 R58 public2/verify2/host1、counter1→2 的实际RED保持原样；本修正没有读取第二条 rejected payload，不能追认其已满足原识别合同或获得恢复/业务PASS。实机场景见 [R58原RED](2026-10-11-i4-r58-rejections-increment-red.md)。

生产仅改两行：把全进程累计0→1限制改为本动作起始counter到initial+1的精确增量。原六项successor、uint64类型/边界、owner/date/pause/revision、确切错误类别与rejected-frame id、原deadline、唯一pre-action readmission、新完整native帧要求保持不变；speed/resume已提交或resume后的新拒绝仍失败，不重执行动作、不递归重试。未知payload、旧id、多拒绝、回滚与跨owner/date仍拒绝。

原独立审阅为16项静态 `SOURCE_REVIEW_PASS`。它及原SOURCE-CHECK的“尚未运行”状态按当时原件保留；ROOT其后实际完整文件测试一次，命令 `C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe -B -X utf8 tools/test_ck3_mod_acceptance_preaction.py -v`，cwd为仓库。实际 UTC 2026-10-11T06:49:25.612325 至06:49:27.486625，exit0，stderr明确12 tests/OK、stdout0。新增6方法与1个受影响旧negative覆盖非零基数、uint64上界、多拒绝/回滚/错误revision、旧id/未知payload和resume后拒绝；测试夹具抽取真实canonical方法。此包未再执行测试。

实际 host 为275,663字节／`25ee2015a7ad257d7c2a34dbe87b0662c990d38feb58b85f3f6db8ef2e92624a`；实际 test 为20,327字节／`793f1175bfa12e8b4c14349d8a4847f977ea377a639c3e28211f0f37e5aff195`。原 patch8934字节／`be333bcdb7f08a89b19a7b6e96bc72b3a3ca7a532c80f2dc8ab7eb5cb886e080` 含生产两行和测试增量。完整原命令、stderr、patch、source-check及独立审阅见 [证据索引](acceptance/2026-10-11-i4-r58-preaction-counter-fix/INDEX.actual.json)，不复制完整host/test源码。

`open_kaishek: not-applicable`：本次是host Python coroutine累计计数与readmission判定，没有改变CK3脚本、原六项guard或native输入，不能由脚本parser验证这段异步host语义。本次没有native build、source freeze、CK3/SDK操作、SAVE/cache/native正文读取或新live验收。已运行的Source16/O16与R58历史证据不改；后续freeze及实机仍需另行绑定。Phase I仍75%估计、`NOT_GREEN`。
