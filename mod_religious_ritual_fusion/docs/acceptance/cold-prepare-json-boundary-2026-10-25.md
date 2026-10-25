# 冷读准备的 JSON 边界修复

机器：`4-8e1c2f1861`。观察日期：2026-10-25；首次失败发生于 `01:51:15Z`。当时源码为 `f05e5ec02522d3e66448f9594defa53ec601bd63`，公共 runtime 为 `runtime-a10`。尚未分配 R0009、启动游戏或复制原始存档。

公共 `cold_reload prepare` 在生成隔离 profile 后返回 2，原因是 `Value is outside the finite JSON type domain`。真实引擎选择器会在内部 context 缓存 `(module, identity)`；保存载入分支随后错误地把整个 context 当作 JSON 验证。该缓存属于运行时实现，不能进入公共序列化合同。

共享 adapter 现仅把保存启动真正使用的 `saved_campaign`、`output`、`state_dir` 投影到严格 JSON 边界。全局 JSON 校验及内部缓存均保留。新增回归执行真实引擎缓存、公共 saved 分支、序列化往返、V2 部署 inventory 和 canonical host 保存复制消费者；使用明确标记的人工小输入，不声称运行了游戏。

本次真实冷读输入也已通过修后的公共 `prepare → plan → preflight`，三次原进程均返回 0，blockers 为空。受保护的 R0008 存档仍为 68,422,055 bytes，SHA-256 `2949d870266b21bf078db88f9d6f0ca4b3a714e77bda6b3af0b0f41e5e60ccf3`，未复制、未修改。它包含真实融合结果；这次离线准备不授冷读业务通过。

原失败、partial profile、runtime 和原始退出码继续保留。证据根：`C:/workspace/rrf-development-20261024/runtime-preparation-a09/`；修复回归及真实公共链：`public-chain-a01/r9-cold-engine-cache-a02/`。实机后继使用全新 prepared/state 和重新绑定的 runtime，不覆盖失败场。

Validation: 50 tests, zero skips; six complete existing commands returned 0. Actual receipt: public-chain-a01/r9-cold-engine-cache-a02/VALIDATION.full-scope.actual.json, 4580 bytes, SHA-256 f7272f34dbf1d52e0bfc80f71fe9a70b3c342614665dadf9ed2d921c4fee9020. Other platform matrices and native/Java builds were unchanged and were not rerun.
