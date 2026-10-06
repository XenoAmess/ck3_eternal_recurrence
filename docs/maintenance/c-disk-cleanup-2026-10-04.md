# C盘清理与占用记录（2026-10-04）

用户明确新增清理子任务；C盘476.63GiB，开始时空闲0B并造成写入截断。任务在白绮研发期间独立并行执行。
2026-10-04 09:37:50 UTC（北京时间17:37:50）达到20GiB空闲目标，后台压缩结束。
结束时实测空闲 **21,474,910,208B（20.00GiB）**；后续工作会继续改变实时值。

## 实际执行与完整性

- 删除超过7天的Chrome/Edge HTTP/Code Cache和NVIDIA DXCache：**6,381文件，逻辑998,421,417B（952.17MiB）**。2个被占用文件保留。
- 四阶段NTFS无损压缩成功 **139,889文件**，每文件前后SHA-256和修改时间保持，失败0；原始路径、内容和资产仍在。
- 前三阶段36,545文件，第四阶段103,344文件。第四阶段达到容量目标停止，其余40,555候选未改动。
- GetCompressedFileSizeW尺寸差合计17,688,047,748B（约16.47GiB）；这是API尺寸变化，**不等于全部物理释放量或空闲增长归因**。空闲量另实测，包含并发写入和文件系统回收。
- 项目源码/.git/虚拟环境、冻结输入、旧attempt、录像/截图/音频、存档、Steam/工坊、OneDrive和个人文件保留。媒体/存档/压缩包未重编码；系统组件、pagefile和驱动安装未改。

## 占用大头与后续释放方向

全盘元数据扫描2,198,871文件、315,190目录，访问限制和reparse均记录。以下是**逻辑大小**，不能当作物理占盘或可删除量。

| 路径 | 逻辑大小 | 后续处理 |
| --- | ---: | --- |
| C:/Program Files (x86)/Steam | 173.62GiB | 保留；不用的游戏经Steam正常卸载或迁移可提供大空间 |
| C:/workspace/ck3_uuii/_runtime | 121.85GiB | 过程资产永久保留；本轮已对合格历史文本/对象无损压缩 |
| C:/workspace/ck3_damengsan_suite/_runtime | 33.63GiB | 同上，不能当垃圾删除 |
| C:/Users | 35.65GiB | 只清理明确旧缓存，个人目录/账号配置保留 |
| C:/ck3-runs/uuii | 15.63GiB | 实机与研究资产保留 |
| C:/workspace/ck3-upgrade-20261001 | 10.01GiB | 已无损压缩历史大中型文件 |

进一步可评估NVIDIA OTA下载/解包缓存3.68GiB、Downloads驱动安装包约3.62GiB、pnpm约4.38GiB与已关闭Codex会话。
OTA版本616.92而当前驱动581.80，可能仍待安装；Downloads仅疑似重复，pnpm可能硬链接，均保留。
未把这些估计相加为可释放承诺。用户Temp约1.52GiB主要是近期VS安装材料和研究夹具，本轮保留。
目前只检测到C一个本地盘，未执行迁移。

## 证据与持续写入

原件在 `C:/workspace/c-disk-cleanup-20261004-01/`：两个逐路径cache删除报告、四阶段plan/result/journal、完整metadata inventory和20秒IO观察。
第四阶段脚本SHA `dec3ce8f5b8bf92a6a6a3583adfed3b891c0bd367a16eb9a4b6cc5b14f18e817`，
精确候选清单SHA `9052215bbbfbfdb4c455a40fb234269a2f3a92fe46055ebb38bbe35398dd8a6c`。
最终 `ntfs-compression-result-04.json`记录capacity_target_20_GiB、成功103,344/失败0及上述结束时间。
root逐行核验第四阶段103,344份收据：全部before/after SHA一致、bytes-identical与mtime-unchanged为true，后台PID/create-time身份已退场、stderr0。
journal SHA `65cb16a18252bf9f7ec0aae8ad6665e085dbfce23540f0f5b6db28575dbfef50`，
最终result SHA `20235511b2ec1cba9b4f56a047769d12ceea5ed91a91fc7a5ff72c8f4aa7ad11`；独立审计回执为外置 `root-final-close-audit-01.json`。
初期回收空间曾再次耗尽，.git临时pack约510.9MiB是增长线索，未删.git；后续20秒监视未见持续大写入，不作确定根因判断。
满盘失败的0B报告和脚本partial保留，主仓harness从预先保全的完整候选精确恢复，见[白绮事故记录](../ck3-1.20.0.3-vivhite-compatibility-2026-10-04.md#满盘事故与最小恢复2026-10-04)。

## 2026-10-05 新闭场文本无损压缩（精确19文件）

2026-10-05 **00:44:04.946103 UTC（北京时间08:44:04）**，root 实际执行新的精确19文件 NTFS 压缩，最终状态 `COMPLETE_ALL19_PRESERVED`：19文件全部完成，失败0、剩余0、跳过0。来源为已闭牛来R2、肃清曼荼罗R2、自动升级建筑R14与体验优化R6；原验收报告的GREEN/RED状态保持，不能把压缩完整性结果当作模组验收通过。

- 全部19份逐文件回执证明前后完整SHA-256相等、逻辑size相等、原mtime_ns相等、路径与handle文件身份保持、单硬链接且非reparse。原生句柄在SHA–FSCTL–SHA全过程拒绝并发写入与删除；关闭后再复核原metadata及闭场报告。原内容没有删除、移动、重编码或覆盖，媒体、存档和当前活跃运行不在清单。
- 压缩前GetCompressedFileSizeW API尺寸合计 **194,039,964 B**，压缩后 **75,931,648 B**，API尺寸差 **118,108,316 B（112.64 MiB）**。这只记录本次新操作，不与上文历史952.17MiB缓存删除或16.47GiB API差重复计数；不把API尺寸差当作实际物理释放量。
- C盘空闲独立实测：开始 **11,612,803,072 B**，结束 **11,730,739,200 B（10.93 GiB）**。并发写入、回收与本轮输出均会影响空闲值，回执明确 `free_change_attributed_to_compression=false`、`physical_reclaim_bytes=null`，不作增长归因。
- 进程优先级BELOW_NORMAL经过实际读回，hash读取按每MiB节流，逐文件节流；每个FSCTL只有一次，先持久记录intent，再核实实际完整性。未启用任何删除流程，也没有Steam账号、桌面、OneDrive或系统服务变更。

永久外置原件：`C:/workspace/ck3-upgrade-20261005/c-drive-exact19-ntfs-compression-root-01/`，包含精确输入快照、实际runner源码、execution-start、全部句柄guard、append-only journal及result。`result.json` 为53,399B，SHA-256 `9e0a01394b09579343934c8a3eb08fc63ae0ce09813527f6a1079b3cfa92c4aa`。实际runner SHA-256 `9516d5b0d6753591df0ecd32e5760c493c05bcd9bbd212f9e3b3ee1436240700`；冻结19文件plan SHA-256 `e1ef3d29f181ead0c45a2c83783edb7dac37befa4ec20be77d9120a39d4a2bea`。

独立逐字段核对位于 `C:/workspace/ck3-upgrade-20261005/c-drive-incremental-audit-agent-01/exact19-master-record-prep-10/actual-exact19-record-validation-01.json`；该核对只读取小型执行回执，没有重复读取或解析原大日志。旧第四阶段剩余40,555条精确路径继续只读复核；没有闭场归属证据、当前活跃资源、源码、shader对象或媒体的条目不会进入后续压缩清单。

同日 **01:15:14 UTC（北京时间09:15:14）**，Root另对已闭Main R10的5份精确文本执行相同无损流程，实际 `COMPLETE_ALL5_PRESERVED`、完成5、error=null；API尺寸差 **7,827,496 B（7.46 MiB）**。原内容SHA、size与mtime保持，原R10验收RED不变；不包含当前QOL场景、profile或mod源码。[实际result](C:/workspace/ck3-upgrade-20261005/c-drive-exact5-ntfs-compression-root-01/result.json)为14,848B，SHA `9a96e9aac1510221c3e7836d2ddd47ab8ac1dfb3121ba9ae4f9498ef358fd4b3`；精确plan SHA `9a3ea2caa5b5c376f95871cb3601690384cc5e6460edd780640060e5be62d199`。本轮两次新操作合计24文件、API差125,935,812B（120.10MiB），不重复累计历史记录或声称物理回收。此次结束C盘空闲12,916,170,752B，仅为当时实测。

## 2026-10-06 体验优化 R13–R15 闭场窄复核（新增释放0）

2026-10-06T03:08:08.019891+00:00（UTC）低优先级只读复核指定三轮18份 LIVE 文本及12份 native observer 原始副本：LIVE 文本全部已有NTFS压缩属性；副本实际均不足1MiB，完整SHA与各自sidecar记录一致。本轮合资格候选0、FSCTL调用0、删除/移动/重编码0，新增API占用差0B；全部过程资产保留，未重复读取大原始流。

R15副本 native-state-003.jsonl 实际9,204B、-004.jsonl实际9,216B；sidecar的 wire_observed_bytes 5,283,390B / 27,038,557B记录原LIVE流当时被观察的总长度，不是副本大小。副本与来源流各自保全，不将字段值当作本轮可释放量。

结束C盘空闲2,595,057,664B（2.42GiB），为并发工作期间实测，不作释放归因，也不重复累计此前19/5文件或历史清理。薄回执：[thin-result-01.json](C:/workspace/ck3-upgrade-20261006/c-drive-closed-qol-r13-r15-audit-agent-01/thin-result-01.json)，25,286B，SHA-256 `e748698bc1e04d1e32f4376cbcc72d2989dcf789c8b87a0d8b15ad1a7dc79f12`。原验收GREEN/RED和业务边界保持。
