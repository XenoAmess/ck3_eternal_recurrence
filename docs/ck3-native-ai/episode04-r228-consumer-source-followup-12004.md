# R228：普通战役输入与后继 consumer 源码

2026-10-21 13:04 UTC；machine_id: desktop-3fevhd2-1c74096080。

R228 实测是钱包增加的净额，不是已核实的军费支付。a/b/c/d 原值为 384653/0/273262/0，原生结算 N=a-b-c-d=111391；钱包 25455910→25567301。c 的军费来源与净缺口分摊含义应同时读取，不能把 c 直接当作本次 gross 扣费。paid/payer/cadence 仍 null，旧 typed false 与 fullR08 false 保留。完整原件与实际关闭、GUI ACK 勘误见同批 R228 evidence。

普通存档的真实 snapshot 没有 episode_run_id。B 后继只在 episode_projection=native_campaign、managed_campaign_run_binding 五字段与当前 PID/generation/actor/pipe 一致时接受 runtime.episode=null；真实 run_id 不改称 episode，缺失/显式 null 的原 packet 不补字段。旧非空 episode 路径保留。schema_source 与生成 JSON 同步；生产入口仍须持有实际 runtime/source proof 的出生时间等证据。

war_generic_applied_net_12004 是独立标准库 consumer，未注册到普通 planner。财务净额证明与严格 date32 资格分开：新原 DLL 输出、原构建 wait/manifest 及真实 OS 侧证据缺失时返回 PENDING，不能拿重复调用方身份或 synthetic 闭包通过代替真实加载。其外置测试引用本地 R228 原件，仅作来源档案，不宣称可以从归档目录直接作为 CI 运行。

相机预算为可选 source guard：camera_root 必须等于该 take 的 workdir，raw_path 为其 raw.mkv；不把 Game 的 state/userdirs/driver 合并进 256MiB 相机预算。根不存在、遍历拒绝或其他测量错误均为 unavailable，不能当 0B 通过。外层 Game 容量与正常 Job/Finish/原 wait 仍独立保留。源码检查不证明录制、码率或完成时限。

date32 只改两个 native 文件中的三个日期读取点；修源码或后继编译不能追改 R228 原始大整数日期，也不自动追授新 Game/observer/付款资格。普通智能体可显式查阅本文与专题；没有自动加载或实机信用新增。
