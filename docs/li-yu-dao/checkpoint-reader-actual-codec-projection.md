# R0020 checkpoint reader 实际 codec 投影更正

2026-10-07，冷准备在实际 `C:/lr20s1` 导出中拒绝 SDK codec：`_common_payload`、`normalize_title`、`project_native_query` 与 reader trusted primitive 的 12AST 不同。旧冻结失败、前一源码修复及测试包全部保留。本记录更正 [首次精确 .3/.4 修复](checkpoint-reader-exact-build-compatibility.md) 的验收范围：其 inert fixture 与 trusted primitive 同步，54 项测试通过只证明该 fixture 自洽，没有证明当时最终生产 normalizer 的三函数 AST 相等。

本次从实际生产 `confucian_readonly_private_v1.py` 逐 AST 提取原 12 个 DTO 函数和 `_query_build`、`_operation_backend` 两个纯 helper。生产 `VersionIdentity` 的纯定义按原字节复制为 reader `dependencies/native_build_identity.py`，新 trusted primitive 与 inert codec 使用同一投影；lineage 同步真实 primitive SHA，并核对新增 helper AST 和纯 build dependency 字节。原 12AST 一项也未跳过，实际 codec SHA 与历史 contract SHA 分开保存，读取及 AST 比较不会 import 或执行实际 SDK 文件。

原 .3/.4 的 HELLO version、EXE SHA、adapter 和 outer/nested/query backend 必须属于同一个精确 build；.4 title 的三个 ABI index 仍绑定实际 `5f5a1005711ef523bcd228c1b2ff2822a9767e13c1b9a934f9a3a87f37287e3d`，.3 原 tuple 保留。生产 `expected_build` 关联分支逐 AST 保留。`snapshot_build_identity` 和 converter 的七字段 frame 返回不变，saved/protection/readiness/frame/generation/业务信用谓词未放宽。

新增生产 codec 文件直接通过 lineage 的正例，使用该 descriptor 进入 .3/.4 的完整惯性 checkpoint-transition 路径；connected-build 错配及 helper 篡改拒绝。相关三模块共 56 项测试通过。第一次新测试因为误读 `actual_binding` 字段失败，原 stderr 和 exit1 回执保存；使用真实 `runtime_binding` 字段后 exit0。没有 SDK、CK3、进程操作、存档 body 或 native build，本次不授新版本实机或全模组 GREEN。

测试命令（cwd `tools/lyd_i3b_checkpoint_readback/tests`）：

```text
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe -X utf8 -m unittest test_sdk_exact_build_pairs test_sdk_checkpoint_seam test_checkpoint_transition_v2 -v
```

新冷准备应只从最终真实导出复制完整 `tools/lyd_i3b_checkpoint_readback/reader/`，包括新增纯 build dependency；重新生成 executing-reader inventory、codec descriptor 和 source HEAD。旧 R19 sourcepack、旧 saved/native raw 继续按历史来源保全，不用此新代码重验为新版信用。

小型 [归档索引](acceptance/2026-10-07-r0020-actual-codec-projection/INDEX.json) 保存原 cold RED、真实 codec AST 比较、前后源字节、patch、失败和通过测试回执。发布只使用 fetch、rebase、复测与普通 fast-forward push，不执行 merge 或 force push。
