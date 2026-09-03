# open_kaishek 兼容性审计（2026-09-03）

## 结论

本次审计完成了 open_kaishek 的远端同步和离线兼容性复核；当前身份绑定为

`HEAD == origin/main == 981c79388a07e447b18f8e4472a16fd65e28c083`。

root G2 侧与 open_kaishek 侧的 capability ID、profile ID 和提交绑定一致，离线测试通过，
因此 T2 当前为 **GREEN（静态/离线兼容）**。这不是 CK3 实机认证：
`nativeCertified=false`、`runtimeCertified=false` 仍然保持，尚无新的 paused evaluator
artifact。

本次没有启动 CK3、没有加载存档、没有修改游戏状态，也没有猜测或注册 Paradox opcode。

## 同步动作与基线

审计开始时，`Z:\workspace\open_kaishek` 工作树干净，但本地 `main` 为
`0390b9a959fa1a59a968000ed49e827a03b8d4e4`，而远端 `origin/main` 已推进到
`981c79388a07e447b18f8e4472a16fd65e28c083`。执行 `git fetch origin main --prune` 后，
以 `git merge --ff-only origin/main` 快进本地分支；没有本地冲突或未提交改动。

当前检查结果：

| 检查 | 结果 |
| --- | --- |
| open_kaishek `HEAD` | `981c79388a07e447b18f8e4472a16fd65e28c083` |
| open_kaishek `origin/main` | `981c79388a07e447b18f8e4472a16fd65e28c083` |
| open_kaishek 工作树 | clean |
| CLI shaded JAR SHA-256 | `97027DB3CF01B4130E280D17B552FD9243193181A3EE968E1BB8FD7734C97C57` |
| CK3 build / EXE SHA-256 | `1.19.0.6` / `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |

## root ↔ open_kaishek 绑定

两侧当前值如下，且由 root focused test 做了精确断言：

| 项目 | 值 |
| --- | --- |
| capability | `game.command.query-g2-truce-evaluated-days-v1` |
| profile | `ck3-1.19.0.6-g2-truce-evaluator-v1` |
| open_kaishek commit | `981c79388a07e447b18f8e4472a16fd65e28c083` |

字段语义按两层合同对应：公开 exit-terms truce 行共享
`owner_character_id`、`toward_character_id`、`evaluated_days`、
`current_date_raw`、`expiry_date_raw`；G2 低层观察合同另外保留
`evaluated_days_observable`、`expiry_observable` 和 frame/stability 身份字段。
低层 root payload 的 `date_raw` 是同一当前日期在内部观测合同中的命名，不能把这两个
层次误当成同一个 JSON shape。open_kaishek profile 只声明能力和不变量，不充当运行时
转换器，也不改变 root 的 fail-closed 检查。

## 离线验证

### open_kaishek

在同步后的 `981c793` checkout 执行：

```text
mvn -o -ntp test
```

结果：`BUILD SUCCESS`，共 `125 tests`，`0 failures`、`0 errors`、`0 skipped`。

另外用同一 checkout 构建 CLI，并对以下无 CK3 fixture 做了实际 CLI smoke：

- `synthetic-361-014`: parser/validator/IR/runtime 均 GREEN；
- `zg361-projects-metrics-postcondition-v1`: parser/validator GREEN，IR/runtime 明确 SKIPPED；
- `zg361-promotion-compensation-postcondition-v1`: parser/validator GREEN，IR/runtime 明确 SKIPPED。

完整 75-file ZhongGuo 语料的 parser 仍为 GREEN；validator 的
`172255 UNKNOWN_OPCODE` 是既有、已记录的 bounded schema 覆盖边界，不能写成 G2
兼容失败，也不能借此放宽 schema。

### root

在不启动 CK3 的情况下执行 G2 focused slice：

```text
18 passed, 12 subtests passed in 14.60s
```

覆盖 root truce 合同、preview observer seam、静态边界和集成接线；结果只证明静态/
fixture 一致性，不证明 native evaluator 已返回值。

## 当前边界与下一步

- T2 的同步缺口已修复：默认 checkout 现在不会落后于 root 所绑定的 `981c793`。
- G2 仍不能升级为 `fixture-live` 或 `production-live`；下一项价值工作仍是一次独占的
  exact-build paused evaluator 双读 artifact。
- 在该 artifact 出现前，不添加 `evaluated_days` 的新 opcode、expiry 推导、写操作或
  未证明的 activity schema；每次 CK3 验收前继续先跑本地 open_kaishek preflight。
- 若 capability ID、字段、不变量、profile ID 或版本绑定发生变化，必须同时更新 root
  合同和本记录，再重新跑 Maven/root focused smoke。

