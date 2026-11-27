# CK3 1.20.0.3 胜方所属战争读取归档

[Git bundle](battle-winner-war-membership-12003.bundle) 保存
`codex/battle-current-war-membership-20261007` 的原提交
`3097ca1bacea92685c94c424843b981f46767261`。前置提交为主线中的
`97a2a77da0359ceb1215e1ee8ce57831cda5f531`。Bundle 为 42,520 字节，
SHA-256 为 `7f9c48017adbd646825207cc6c3146cd5822976084f80f8b579a16e8667e2ed0`。

旧补丁尝试读取当前战斗胜方所属 War 及其进攻方成员，包含对应的原生读取、请求合同、
夹具和源码定位。分支的范围是 CK3 1.20.0.3 / Steam 25652598，原编译、
FIRST 和 Service 验证仍为 NOTRUN。其战分上限部分已经由主线 `48025dbc86` 接入。
当前 CK3 1.21.0.3 的原生读取仍使用现行合同。

在含主线历史的仓库中恢复原对象。

```text
git bundle verify docs/maintenance/retired-git-refs/battle-winner-war-membership-12003.bundle
git fetch docs/maintenance/retired-git-refs/battle-winner-war-membership-12003.bundle refs/heads/codex/battle-current-war-membership-20261007:refs/archive/battle-winner-war-membership-12003
git rev-parse refs/archive/battle-winner-war-membership-12003
```

2026-11-26 在 `machine_id: xenoamess-full-tower-eb9d2c1186` 核对原分支、
原始源声明和 bundle。此归档为源码保存。
