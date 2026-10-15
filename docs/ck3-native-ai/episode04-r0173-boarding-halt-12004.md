# Episode04：1.20.0.4 登船实付与未锁定 Halt

2026-10-15，来源机器 **`desktop-3fevhd2-1c74096080`**，run
`desktop-3fevhd2-1c74096080--vanilla--R0173`。本记录是历史实证，不能代替其他机器或下一进程的实机验收。

## 已取得的结果

- Army18 正常行军到海区1036，原生状态变为 `embarked/4`。独立现金查询与完整自然父链重联出一笔 **3金币** personal SUB：账户31254余额 **25448407→25148407**，scale100000，requested300000。
- 严格生产消费者重新计算通过：writer publication16、gateway17、transition18。同一进程、创建时间、generation、window1/epoch1及自然父调用均匹配。publication序号在返回后追加，不能用16<17<18推调用入口顺序。
- 这是源链限定的 **整个原回调入口/返回余额核销**，没有指令局部写入采样。该笔费用不能当作所有军队的通用费率；generic ADD282364、monthly rate、钱包净差均不能归因已付军事维护。
- 登船后实际首边进度 **9799/100000**、同帧实际loaded cutoff **50000/100000**。一次原版Halt提交后，独立后态清空完整route及target；再推进一个精确自然日仍在1036、route empty、target null。只关闭这次未锁定Halt后果，不授已锁定Halt、50%等号或改道。

研究整卡由R00、R02增加R11，严格计 **3/14＝21.4%**。R07实际扣款正例通过，但原卡的同T0无登船对照尚缺，整卡仍部分闭合。主片还需Halt镜头和其他研究卡；Review02全文/TTS/重剪仍未完成。

## 可在其他机器读取、重算的原件

[证据清单](evidence/episode04-r0173-20261015/manifest.json)与
[原始文本回执ZIP](evidence/episode04-r0173-20261015/original-receipts.zip)
保存18份已完成回执的精确字节，共1,343,616B，ZIP145,050B；每份原件及ZIP均有SHA-256。
含现金及独立before snapshot、海上后态、一次Halt请求及异步后态、次日后态/时钟、构建与身份、录像媒体检查、正常退出及屏幕释放。
其中本机绝对路径只用于来源追溯，重算直接读ZIP，不要求另一台机器存在C盘原路径。

在本仓库已具备项目Python依赖的解释器运行：

```text
python -B -X utf8 promo/ck3_native_war_ai/episode-04-march-logistics/tools/verify_r0173_evidence.py
```

[验证脚本](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/verify_r0173_evidence.py)
调用同一生产`normalize_journal`，显式使用归档的来源machine ID；不会将当前机器伪装成原机，也不削弱实时入口的本机绑定。它校验归档bytes/SHA、SDK与body一致、正额付款源链及Halt/次日后态。不启动游戏、SDK或桌面，不写审批。文件被改后拒绝旧pins。

## 运行与镜头边界

实际游戏tuple为 **1.20.0.4 / Steam25734779 / EXE SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`**。
现场源码冻结在`8dd6d84a60aa246f527a72173117e42a6c107dc2`；a04 DLL SHA
`5d9a4029797a5dc404f084279159f152e306413c7a8e62e2f2453a0334cc0c73`。
PID14544、创建FILETIME134365403777766761、generation1、episode
`native-31254-3072c36153e4`、runtime actor31254均只属于此场。
新机器应重新核自己的Steam离线、EXE、正常人物来源、PID/create-time/generation与窗口，不能复制这些runtime IDs。

22个连续精确自然日 **53145048→53145576**，每日+24、单tick、overshoot0并暂停。
终态payment retained18、natural44，无报告覆盖/failedappend。仅natural_phase启用，其余8族关闭；不授损耗/补员因果资格。
首日窗口保留通过；旧R0172首日失窗及所有旧失败回执不变。
day15的bookmark.1070事件读取原生选项后按原政策选择第一个可用项，未重放该日Arm/Resume。

唯一原片 **360秒、10,800帧、2560×1440/30fps、H264/yuv420p、无音轨**，461,374,695B，
SHA `de5599ae3d5fc3bad714317b7723fc17fcbc49793d47f96d7307bbbbcfbd922b`。
一次全片严格解码通过，未重编码原件。Root查看169.9秒抽帧，确见船模和军队面板“登船”；这不证明精确转换帧、clean span或人工1×全片签核。
Halt于13:03:36.960908Z，晚于360秒录像名义片尾13:03:25.875534Z，**Halt没有入镜**。
原片留本机外置资产根，不随知识ZIP入库或上传。

正常checkpoint保存于date53145576：69,722,705B，SHA
`6f98c7b9c566057c3b267911b46f522ba5eab1889a3dffc3b6774025751fd36c`。
13:14:38Z实际game exit0、Job已空、tree gone，SDK与keeper均已结束；随后CAS释放屏幕并恢复原1024×768。
单独60秒退出观察器曾先超时，不能把它写成signaled；正常exit0取自bootstrap持有的进程生命周期回执。
