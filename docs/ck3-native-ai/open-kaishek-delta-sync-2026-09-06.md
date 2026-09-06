# open_kaishek T2 伴随同步（2026-09-06）

## 结论

基于 root `bf314be42b62b69c87c8825bf473286bf524a79b`，open_kaishek 已同步并推送
`ce62218a01020a55d88b511ba200fd768a3b19d0`。默认 checkout 为 clean，且
`HEAD == origin/main`。本轮没有启动或附加 CK3。

唯一真实兼容改动是 career-HC/workforce 精确 source pin：ABI 新增 default-OFF
候选声明，source contract 同步正式 runner 登记和按用途拆分后的 effect 输出路径。
能力 ID、公开请求、77 个响应字段、12 个不变量、JSON schema、Python contract 与
readiness 均未变化。因此 open_kaishek 只刷新两项哈希，没有新增 parser 词汇、IR、
runtime handler、CLI 命令或 action 广告。

这也形成一条可复用的文件拆分取证经验：source contract 若把生成文件路径纳入哈希，
按用途拆分文件会导致 provenance hash 合理变化；应继续逐字段比较 capability/schema/
invariant，不能把“哈希变化”直接解释为 public API 变化，也不能把 parser corpus GREEN
解释为 CK3 加载性能或运行语义已获认证。

G2 source-specific live adapter 仍是
`static-ready-live-command-default-off` 且 `live_executed=false`；owner-budget 与
white-peace comparison provider 是父仓 Python policy 输入，不是 open_kaishek 的公开
transport。source-specific loss、comparison input、three-way comparison、decision、
automatic surrender 与 GEN-034 均保持 false。

## 验证

- open_kaishek Maven reactor：156 tests，0 failures/errors/skips，`BUILD SUCCESS`。
- domain：8/8；独立 validator 与 CLI smoke 均 PASS。
- 主 mod corpus：54/54，2,217,794 bytes，0 errors。
- 天朝二期 corpus：827/827，23,460,956 bytes，0 errors。
- 父仓 focused：63 passed，24 subtests passed。
- 父仓 `verify_g2_open_kaishek_compatibility.py --require-checkout
  --require-clean`：`GREEN_STATIC`。

完整 branch 删除/保留清单、哈希和首次隔离 worktree harness RED 的说明见
[`open_kaishek_6b104f2_compatibility_audit_v1.json`](../../ck3_autonomous_player/native_bridge/research/fixtures/open_kaishek_6b104f2_compatibility_audit_v1.json)。
既有 full-validator coverage RED 边界保持不变。

## 2026-09-07 effect 分片来源跟进

014 appeal 离线回放夹具原先仍引用拆分前、现已删除的
`zg361_effects.txt`。open_kaishek `ce62218a01020a55d88b511ba200fd768a3b19d0`
将来源重绑定到
`zg361_core_appeal_scoreboard_effects.txt#31-137`，whole-file SHA-256 为
`8fa31bc18a16a520dd1bf25dcf5cfe55c958c4a05c588a09640771dbda308211`。
这是文件边界/provenance 修复，不改变 parser、IR、runtime 或公开能力。

更新后的 shaded CLI JAR 为 362,766 bytes，SHA-256
`2e2e9f7edee40158cfe960390dcbf4279bf3fa75d8bc61500eb7de7a1ae5ba2e`；
Maven 156/156 与天朝二期 corpus 827/827 均为 GREEN。本轮未启动、停止或
附加 CK3。
