# R189 R06：actual stable8父前缀与独立3E4BC50来源

machine_id `desktop-3fevhd2-1c74096080`；来源封存2026-10-16T19:46:31Z，实际部署source `6bf30840af44231653f8e914389b59c8798f2cc1` / nativea30。CK3 1.20.0.4/build25734779，EXE SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。其他机器可复用来源和代码，不继承安装、进程、权限、容量或此实机资格。

[EVIDENCE](acceptance/2026-10-17-r189-parent-prefix/EVIDENCE.actual-a34.json)保存五条exact body spans、去重四份raw切片和两份冻结production消费者，所有source/frame/identity pins随原件保留。两次实际叶完全一致：full仍是candidate_parent_depth_exhausted，稳定双读前缀0..7为available；depth0与4的单entry是mode0/flag0/direct空/provider空，其余已观测深度没有eligible provider。eligible parent provider RVA列表为`[]`；不是null也不是provider执行资格。depth8 definition和更深receiver仍unknown，native_receiver_selected/provider_execution/toggle/actual_ADD均false。不能把旧R186本地叶或候选source与这次actual stable8混为同一观察。

独立新source `[3E4BC50,3E4BEAC)`完整604B/162指令、metadata40B/4次授权读取，原bin、ASM、逐读账本和[合同](acceptance/2026-10-17-r189-parent-prefix/source/SOURCE-CONTRACT.actual-a35.json)可移机复核。direct body先处理既有expression block的有符号+8C计数，再处理pre-expression +C；可读既有变量槽、调用既有preparation record的+20 target。它没有在direct body遍历context parent，不能称无副作用纯getter；未读helper/indirect的传递效果未知，+8C/+C实际值没有在R189观察。此静态来源不让unknown receiver或callback自动成立。

全部原件在[同一acceptance目录](acceptance/2026-10-17-r189-parent-prefix/EVIDENCE.actual-a34.json)和source子目录。a35旧sealed短copy列表漏了conclusion plan/check，本次按作者确认的原SHA显式追加两件，旧receipt不改；它们与SOURCE-GRAPH同源。原两个assert-bearing verifiers按exact bytes保留，[verify_portable_explicit.py](acceptance/2026-10-17-r189-parent-prefix/verify_portable_explicit.py)固定它们的SHA，只把Assert AST改为If-not/Raise后执行，故`python -B -O`仍会拒绝失败，不读EXE、不重建缺失after或新采样。

```text
python -B -O docs/ck3-native-ai/acceptance/2026-10-17-r189-parent-prefix/verify_portable_explicit.py
```

R06新增的是本机actual stable8只读观察及可重算小来源，未授receiver/toggle/ADD业务。研究6/14、业务4/11、合格动态0/11、正式ABC0/3不增加。
