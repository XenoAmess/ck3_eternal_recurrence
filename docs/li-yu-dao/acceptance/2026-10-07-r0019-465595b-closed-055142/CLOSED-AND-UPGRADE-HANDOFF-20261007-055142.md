# R0019 实际关闭与升级前交接

截止 **2026-10-07 05:51:42 UTC**，旧 R19 已实际正常关闭并释放：原 CK3 PID19980 的 typed normal exit 为 TRUE，原 game HANDLE wait0/exit0；原 Client17364、keeper1984 HANDLE exit0，原 holder17104 / keeper / Client 的执行完成分别为 session88883 / 34416 / 42487、exit0。05:51:24 新鲜 census 四项原身份均不存活、受管服务为空、errors=[]。实际 RELEASE 的 CAS sequence **3570**，旧任务 done/resources=[]，after-list 同任务也为空。闭合是已有实际能力；整个 mod 仍 **NOT_GREEN**，formal approve、新 T、C3/I4 信用仍 NULL。

闭合来源为 exact `465595b67efa8f72dfc97bc0de218302c75e3bfd`；mod/export/native binary 在旧现场始终冻结，Python晚 attach overlay另见[原修复事实](../../../ck3-native-ai/native-profile-explicit-late-attach-verification.md)。闭合 INDEX1609 B/SHA `20343839fca7ae203e5000f8d75e3846af92617838f4da53efd3e7b14a46550c`、PREVIOUS-BOUNDARY3095 B/SHA `d348eef0541f21e3bda607761940346237bf7d33d65dc1808dad4b36a381907e`、原 verifier/作者输入/原句柄观察/执行wrapper/census/释放回执均按原字节归档，不重复执行验证。

B2 后继002使用既有 ballot 阶段取得真实 post-seal phase2 / serial1 / nonce2 观察，正文读取1次、保护87/87 TRUE。原 STATE SHA `a354377c0dba98bdcfd13d04283294c0cfd863ef4544a9ec6b9a89cd93916691`、TYPED SHA `9e053385afb7473dfb8565e517ae17955c4363e07003cb9085e3cf5b7871cad5`；原 assessment为 `INCOMPLETE_NATIVE_QUALIFICATION`，正式信用仍NULL。旧 pre-seal B2未捕获及 failed001阶段 mismatch 在[05:32:30原截止](../2026-10-07-r0019-465595b-formal-r1-053230/PARTIAL-20261007-FORMAL-R1-053230.md)保留，后继观察不补填旧窗口。

B3 materializer001原exit1、正文读取0，原失败stderr保留。SOURCE CLOSEOUT-001只把旧 first430 Title路由到正确registry历史入口，R1当前 formal registry仍NULL；原CP/CAP、业务谓词与来源冻结保留。恢复 materializer002为ROOT直接工具执行exit0；其外置原工具stdout/RESULT wrapper与精确chunk ID缺失，明确记录NULL，保存现存title-routed输入及实际 AUTHOR-INPUT/ARGV输出，不发明wrapper。后续 author002有独立原执行wrapper exit0，唯一正文读取1次；STATE SHA `5c3c707e48acffad34b54d7419179de25c8182b2a800c72b7c36fd6ef324fd43` 的实际票数 total2 / yes1 / signed0、delegate31254，NPC65865 vote0，人类31254 player_yes1/vote1。原 assessment `OBSERVED_CONTRACT_MISMATCH` 保留，保护87TRUE/TYPED SHA `0c234ba9c7685cb19530cb4e8161d71cc2815a1b916d42c837184fb33f67c353` 只证明保护，未取得正式批准。

R1 withdraw实际完成，R2BEGIN已发；用户提出“升级本机游戏→仓库→继续”后，R2 withdraw-before-upgrade实际完成。最终主动SAVE SDK0054及G2/G3 SDK0055/56已有原件。保存 descriptor为 **91,671,418 B** / SHA `9977b3527478849190acfcc408b3af2d4c33a499fcbdbd6a562ef005cf9faeae`，由原 PRESERVED.actual.json证明；不把 `.ck3`正文入Git或再次读取。

SDK0057–63保留完整实际退出层次：首个prepare为 `dispatch_unknown_claimed` / `opening_callback_postcondition_not_yet_observed_no_retry`；后续fresh query、continue、fresh query、confirm一次、observe得到 typed normal exit TRUE和原HANDLE退出0。SDK63原native内部旧 `dispatch_pending` 也原样保留，最终独立句柄观察与ROOT实际闭合分别证明退出。`autosave_verified=false`；前述主动SAVE成功有自己的实际回执，二者独立。

新游戏版本、未来HEAD/新binary/metadata/RUN/PID/session和GREEN均 **NULL**；后续升级及重新启动须建立新身份，不以旧465证据外推新验收。本增量保留旧各PARTIAL截止，新增CLOSED事实，不纳05:51:42后升级lease或其他新事件。[事实与缺件边界](FACTS.actual.json)、[原件SHA清单](INVENTORY.json)和ZIP保存必要JSON/小源码/真实stdio；复用既有归档，不重复全部历史SDK。本作者SDK/屏幕/总线/进程/保存正文/CI/测试/构建/主树写入均0，只有独立文档工作树的归档与正常交付。
