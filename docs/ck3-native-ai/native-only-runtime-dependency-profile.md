# 原生 MCP profile 的依赖选择

2026-10-17：本期实机准备暴露一个实际阻点。`environment.agent_runtime_fingerprint()`
默认要求视觉/OCR、CUDA 和原生客户端的完整依赖；只有 MCP、规划器与 Windows 原生进程管理的
环境也会因缺少 GPU 分发包而无法生成、验证普通 profile。

明确选择 `prepare-profile --runtime-dependency-profile native-only` 后，只对原生传输、
规划、schema、原生帧图像及 Windows 进程管理实际使用的包读取真实安装版本。
原默认 `full` 的依赖表与既有 fingerprint 形状保持；旧 manifest 缺少选择字段时仍解释为 full。

native-only 的 `agent_runtime` 单独保存 `runtime_dependency_profile="native-only"`、
`disabled_capabilities=["visual_ocr", "hybrid_fallback"]`，并纳入原来的 runtime/environment
hash。它不记录 GPU/OCR 包已经安装，不启用视觉策略，也不新增另一套 CK3 版本或 mod 准入。
核心包缺失继续报错。`verify-profile` 默认按已保存的选择复验，也可以显式要求某种 profile；
选择不一致时拒绝。原生 bridge 的 exact EXE、状态、规则、mod、存档及后验守卫继续生效。

`runtime.launch` 在实际 `NativeBridgeLaunchConfig` 完成解析和验证之后、创建进程之前核对
该选择。native-only 必须使用实际 `native-headless` 配置；环境变量文字不能覆盖一个
hybrid 或 disabled 配置，fixture 跳过普通 profile 验证也不能跳过这项检查。

本次机器观察为 `machine_id: 4-8e1c2f1861`，时间
`2026-10-17T07:52:54.888833Z–07:53:00.261029Z`，出处为外置
`C:/workspace/ck3-faith-and-power-20261017/episode01/runtime-audit/actual-dependency-profile-qualification.json`。
生产默认函数实际报 `required runtime distribution is missing: nvidia-cublas`；候选原生函数
实际读回 13 个核心包身份，未下载安装 CUDA。完整版本、解释器 SHA 和候选 SHA 均在该回执。
候选验证没有授予已准备 profile、游戏启动、宗教业务或视频素材资格。

聚焦验证覆盖 7 项依赖选择、CLI、prepare 转发与 verify 行为，以及 6 项实际 launch 前置路径
（抽取生产函数 AST、在既有 verifier 处停止，不创建进程）。包版本夹具测试与上述真实安装
回读分别记录。`open_kaishek` 为 not-applicable：本变更处理 Python 分发身份与后端选择，
不求值 CK3 脚本或游戏机制。

用户批准的独立机制实验场景与普通罗贝尔战役分开记录；本依赖选择本身不会改变场景权限、
玩家 allowlist 或普通战役成绩。
