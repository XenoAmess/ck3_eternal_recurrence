# 第一期配乐与实测时长配置

用户于2026-10-18明确指定使用战争系列的 `promo/ck3_native_war_ai/assets/music/quiet-courtly-tension.wav`。生产输入的 `background_music` 必须绑定这份原文件，30,726,160字节，SHA-256 `fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f`，直接引用，不复制音乐。旁白0dB、音乐−17dB，循环同一原曲，开头2秒淡入、结尾8秒淡出，关闭ducking及自动归一化。

已有full/formal入口继续使用。最后一次concat通过工具链公开 `AudioMixSpec` / `plan_audio_mix` 实际混音，复制H264视频、将最终声音编码为192kbps AAC/48kHz双声道；不额外输出一份无音乐整片、WAV或AAC临时文件。实际混音argv、严格AV解码、全部视频PTS、声音信号和有限音乐存在性检查进入结果回执。配置中有音乐文件不代表混入成功。

默认配置仍为1860秒、168段、2560×1440/30fps、3Mbps maxrate/3Mbit VBV、CRF21/veryfast及192kbps声音。额外配置只通过SHA绑定JSON显式选择；降低画质、更改码率或任意扩大上限都会拒绝。`episode01-2101s-1440p30-v1` 用于本轮115段实测后超过2100秒八帧的情况，不剪声、不重新配音；实际原生ProjectConfig上限必须覆盖选择的真实时间线。

`machine_id: 4-8e1c2f1861`；本轮语音开始于 `2026-10-18T03:05:42.541102Z`，实际115段成功、失败0，纯声2048.64秒，按帧编排2100.2666667秒（63008帧）。同批预算仍为3,079,062,160字节；只按实际115段/实际时长计算的合成峰2,977,034,353字节准入。2101秒/168段的理论峰3,080,293,810字节**不是本次获准额度**。语音已花分配及后续future只计一次，具体实际机器准入另存外置回执。

正式来源：外置 `episode01/revision-v4-20261018/narrative/renderer-candidate-a02/SOURCE-FREEZE.json`，SHA-256 `5a5f827e1f68f076287f7189338f8fc95f51f3bb69cc04be3fb0d8f98c472067`。八项可移植单元测试已通过，包括原默认预算、不可变profile、实际音频planner命令、缺音乐/双音乐反例、固定lag，以及仅持精确图解回执时避免重复来源标签。测试由静态CI既有integration discover入口执行，不读媒体、不访问机器路径或运行FFmpeg。实际新片混音与完整听审仍待生产结果，不能用这些离线测试授予。

2026-10-18T04:56:45Z后继，`machine_id: 4-8e1c2f1861`：[v4实际交付](../../../docs/ck3-native-ai/faith-and-power-episode01-value-v4-delivery.md)已产出。指定WAV实际混入最终AAC；同一电影五个固定4秒窗口的残差证明通过原阈值，完整人工听审仍待完成。

原生产session92713实际exit1，失败停在音乐证明。原算法用相对`-ss`读取dry concat，受到AAC priming产生的输入时间基影响；随后学得的−171／8000秒lag又把最终信号中的音乐一并移离原曲。单窗诊断确认仅对dry输入使用`-seek_timestamp 1`即可对齐。后继五窗保持final/theme原时刻、global lag固定0、原阈值不变，相关性0.996978–0.999624、增益0.996802–0.999050、误差比0.027433–0.077731。源码据此去掉padding与lag拟合，仅dry按绝对PTS seek；两项新增纯回归覆盖独立参考偏移与五窗命令，不重复旧测试。

原RED、原run和电影字节均保留；独立后继证明、metadata恢复各exit0，不把原exit1改成0，不重编码或重复AV／PTS。实际MP4为94,478,369字节、SHA-256 `3b6586ec511eb29823d43589092f7ca10ea05c0c01d10882422dda727a0714fa`。精确请求、窗口指标、原失败和后继run见交付JSON；上文“固定lag”测试属于初版历史，不再描述新生产证明行为。
