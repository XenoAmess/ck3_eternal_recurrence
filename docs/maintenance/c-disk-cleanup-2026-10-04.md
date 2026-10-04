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
