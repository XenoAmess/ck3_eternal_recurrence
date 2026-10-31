# 本地模型：跨机器 worker 使用与实际经验

更新：2026-10-31。所有机器的 worker 共用本指南和 [唯一配置](local-model-executor-config.json)；不以旧交接中的地址、机器名或 D 盘路径配置新任务。用户已明确授权持续高并发使用本地模型，并要求继续探索能力边界。

## 连接与跨机器使用

| 项目 | 当前值 |
| --- | --- |
| OpenAI 兼容 base URL | `http://192.168.1.11:8080/v1` |
| 源码候选接口 | `POST /chat/completions`，流式 SSE |
| 模型别名 | `qwen38-coder` |
| 认证 | 无需密钥；客户端强制要求 API key 时填 `local` |
| 旧地址 | 不自动回退 `192.168.1.7` 或 `8000` 端口 |

接手时读取配置及本指南，使用已安装的 HTTP 工具或兼容客户端即可，不需要本机的 `D:/ck3-state/model-dispatch91/call91.py`。该脚本是一次执行机器的既有维护调用器路径，不是跨机器依赖，也不是新 worker 的必备入口。

日志、候选、构建输出使用**执行机器自己的**获准数据根和真实 `machine_id`。不要照搬另一机器的盘符、解释器、Maven 绝对路径、证据路径或 Game PID。运行期决策由该场游戏的唯一运行 owner 装配；源码 worker 的模型调用不能修改另一机器的运行账本或提交游戏动作。

只有需要排查连接时才做一次列表读取，不为每个任务增加探测前置。以下单行命令可由 CMD 或 POSIX shell 执行：

```text
curl --connect-timeout 10 --max-time 30 --fail-with-body --silent --show-error --noproxy 192.168.1.11 http://192.168.1.11:8080/v1/models
```

本机 `xenoamess-full-tower-eb9d2c1186` 于 2026-10-31 02:32Z 实际执行上述命令，退出 0，返回中包含 `qwen38-coder`。这是本机连通事实，尚未代替其他机器实测。其他机器需能路由到这个局域网地址；连接失败应检查其路由、代理和服务状态，不改用旧地址。服务列出的 `max_model_len=1048576` 是服务宣告，不是已验证的复杂任务能力上限。

## 请求布局与最小调用

先选真实尚未完成、能独立验收的任务。默认先让模型提出实现，再由 owner 审阅和编测；不要先写完整答案，再让模型复述。

请求始终使用配置里的实际 `model`、`defaults` 和**逐字固定**的 `prompting.system_template`。按顺序提供三条消息：

1. `system`：配置中的固定系统模板。
2. `user`：确定顺序的当前完整合同、相关生产者/消费者和目标源码。实际源码变化时正常更新，不为缓存保留旧代码。
3. `user`：变化的真实任务、实际诊断、输出约定和返工要求。

使用有限 `max_tokens`，启用 `stream=true` 和 `stream_options.include_usage=true`。既有维护调用器接受 `1..16000` 的输出预算；这是调用器约束，不是模型输出能力结论。按任务给够输出空间，优先精确方法或最小 hunk，避免要求重复整份长源码。默认 `temperature=0`、`chat_template_kwargs.enable_thinking=false`、`response_format.type=json_object`，具体值读取配置。

`request.json` 必须由 worker 用**真实源码和真实待办**生成，不提交含占位符的演示请求。一个 JSON 输出约定即可；不要把 `source="completeJava"`、`source="completecpp"` 这种示例放进任务，模型曾直接照抄它们，而没有输出源码。返回值中只有代码路径、但没有文件内容，也不能替代给无工具模型的实际上下文。

在已经选择好的任务数据目录内，有真实 `request.json` 时，以下是一轮实际请求的通用命令：

```text
curl --connect-timeout 10 --max-time 900 --fail-with-body --silent --show-error --no-buffer --noproxy 192.168.1.11 -H "Content-Type: application/json" --data-binary @request.json --dump-header ATTEMPT1-HEADERS.txt --output ATTEMPT1-RESPONSE.sse http://192.168.1.11:8080/v1/chat/completions
```

这条命令只保存一次传输。已有客户端应继续负责事件、重试、有效 content TTFT、usage 和候选审阅，不必为此新建调度平台。不要只看 curl 退出码或 HTTP 200：还需完整 SSE 终止、`finish_reason`、可解析的候选内容；`length` 和半截流不能采用。工具调用曾因服务缺少 tool parser 返回 HTTP 400；先使用已可用的普通 Chat Completions，不把接口配置问题当成推理能力不合格。

## 高并发规则

- 具备完整输入的源码 owner **直接并行派发**，不等中央逐单封包、ACK、整波完成或结果汇总。运营协调负责记录和调节，不能成为每次 POST 的串行门。
- 准备下一项真实方法、候选审阅和必要编测，与其他完整独立任务的 HTTP 重叠。共享编译读窗只暂停受影响的源码写入或编测，不暂停独立模型 HTTP。
- 以 **12–16 个真实在途请求为初始目标**；有真实积压和服务余量时继续增加。按实际服务 running/waiting、错误、KV 占用和延迟调整。这是运营目标，不是已达事实，也不是已经实现的分布式调度器；多机不能各自把目标写成已达全局并发。
- 一个任务内部有不同且独立的实现、消费者或必要 probe 时，可以提供各自完整上下文同时派发。保源码写权和输出目录互斥，不用多个模型无协调地改同一叶。
- 不设每岗刷调用配额，不重投已完成工作，不为数量制造总结或重复绿测。输入尚缺时明确具体缺口，改派其他真正有输入的工作。

经验：曾因准备、审阅和下一包衔接串行造成服务空闲。新地址历史客户端峰值截至本次已核记录仍为 8；固定窗口 2026-10-31 02:10:10–02:20:10 UTC 有 27 个新任务/27 次真实 POST，但窗口峰值只有 4、末刻服务 running0/waiting0。累计调用增加不代表并发已达标；这些观察也不代表服务容量上限。此前旧地址峰值 25 不混入新地址实测。

## 传输重试与记录

读取配置中的 `transient_retries`：最多 6 次尝试；瞬时 429/502/503/504、连接拒绝/重置、连接或读取超时、流不完整，按 `10/20/40/60/60` 秒并加配置抖动退避。等待期间推进其他独立工作。永久请求、schema 或认证错误先修请求，不盲重试。

保留每次完整请求、开始/结束事件、响应 headers、原始 SSE、有效正文、用量、错误和最终审阅。半截流保留为失败原件，**丢弃该候选并重发完整请求**，不能拼接两次响应。重试范围仅为模型 HTTP，绝不据此重放游戏或 Native 动作。

分别记录：headers 延迟、首个**非空有效 content delta** 的 TTFT、总耗时、服务实际返回的 prompt/completion/total tokens，以及可见 cached tokens。不能把 headers 或 curl 的首字节时间称为内容 TTFT。缺失缓存数据保持 unknown/null，不从排队、TTFT 或总耗时反推缓存命中；客户端 POST 区间与服务端实际推理数也分开。

## 最近实际经验与能力边界

| 真实工作 | 可复用经验 | 已验证范围 |
| --- | --- | --- |
| 模型输入无损候选别名 | 两候选数组只有在非空且结构严格相等时才用可重建别名；保未知字段、整数精度、顺序及原命令 SHA。真实 compiler 诊断能帮助模型补精确 API/cast | 实际 833 行整 DATA 可重建，已正式采用并运行装载；不是可随意删 proof 的许可 |
| Marriage 完整材料角色 | 新增明确 16MiB 角色入口并传播全部 7 个消费者，保原默认小预算和输出约束；不要抬全局上限掩盖角色错位 | 最终源码原样采用，严格编译和两必要测试通过；307352B 是软件材料，不冒充批次127未知原件 |
| M4 真实原码组合 | 模型能承担明确 API 的 producer、consumer、局部组件；完整 ABI/重定位/端口组合常需 owner 修正，必须保留各自责任 | 10RF/64例/33549完整Row40槽首次 Native→Java差分0；不外推真实allocator/CRT/EH或Game |
| M3 copy/release 边 | 小 callee 仍可能有对象 slot 转移、虚调用和 fresh load；不能凭名字生成 memcpy | 221B原码的新11例差分通过，保未知自然caller/vptr，模型首稿拒绝及owner补Hook分记 |
| 字符串与测试材料 | 提取 JSON 返回的源码后再判断转义；样本尺寸实测后再断言超过阈值 | 曾有 owner 转义误疑撤回，以及样本107352B未达262144B的真实模型错误；不能混算 |
| 参数与推理模式 | 看实际发出的 REQUEST，而不是输入 spec 或意图。当前维护 minimal-spec 白名单未转发 frequency_penalty | 旧0.3参数试验未实际发生；一次 enable_thinking=true 请求无服务模式生效证据，且上下文也变化，不是单变量A/B |

给模型完整 API、输入角色、实际诊断和明确验收标准，但不要把 owner 已写好的目标实现夹在提示里。多轮发明 API 或语义错误后，由 owner 接管该整段实现，另选真正未写、可独立验收的较窄方法继续探索；不是永久把模型限定为机械修改。更难任务隔离执行，不把能力探索设成当前游戏推进的前置。

输入文件数、字符和 token **不等于** 实际改写规模。分别记录模型轮数、提示程度、原样/修正/拒绝、owner 错误和返工、真实编译与行为结果、正式采用和运行装载。HTTP成功、JSON完整、严格编译、软件测试、正式提交、Native部署、实际运行决策、APPLIED与游戏日是不同事实，不能互相替代。

详细历史与逐阶段经验见 [可行性记录](local-model-executor-feasibility-2026-10-28.md)、[能力边界记录](local-model-capability-boundary-2026-10-28.md)和[当前运营页](autonomous-agent-progress/2026-10-31-resume91-models.md)。历史证据中的机器本地路径只标识原执行现场，其他 worker 不需要先取得那些文件才能使用服务。
