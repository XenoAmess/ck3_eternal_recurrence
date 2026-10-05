# R0009 来源提交的实际 CI

本目录为 **SOURCE_CI_ONLY**，绑定提交 `54457b371e947edb86903c2ebd578034f02695db`。实际 push 的 [礼与道 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37267312403) 和 [通用 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37267312446) 均成功、attempt 1。礼与道实际 159 个测试通过；通用 60 步成功、20 步条件跳过，失败和取消为 0。

产品静态结果为 70 runtime 文件、889 个本地化 key、68 个事件；70 文件可复现构建成功，manifest `295e101d1bbefff3aeb2f18d5856f7f5b46ab2c2971005753d2eea6706939d15`。CLA 为 **NOT_TRIGGERED**，没有签署成功或服务器绕过成功信用。这些结果不提供实机循环、退出或 R9 总体验收信用。[实际状态](STATUS.json)

[原始压缩包](raw/ci-evidence.tar.gz) 无损保留完整原始 gzip 投影，包括全部 134 个来源映射、job stdout、每一步、workflow 定义、suite/check/status、artifact metadata，以及六次网络超时回执。所有 90 个外层成员与原投影逐字节相同，134 个来源逐份解压复核 bytes/SHA。原始包、失败记录和旧 CI 保持原样；没有 rerun 或 dispatch。[原始映射](RAW-MAPPINGS.json)
