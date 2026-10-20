# E04 原方法版与后续实录补充：34 分 37 秒整长审阅电影

`machine_id: desktop-3fevhd2-1c74096080`；2026-10-20 UTC 实际生成。此版把已纠错的 69 段历史方法审阅版与当天生成的 130 秒实录组合章顺接，给出一个可连续播放的整长审阅文件。方法版保留其录制时的待验状态；四个补充片段来自独立回放，不能拼作同一场因果，也不把本文件称为战争四期最终实片。

本机影片：`C:/ck3-e04-resume-20261020-a01/full-review-a01/work-a01/E04-METHOD69-PLUS-INDEPENDENT-EVIDENCE-34m37s-REVIEW-a01.mp4`。101,671,823 B；SHA-256 `473ea068e33026de746954880e4388c88ac2b6731daa34a8a19c4d53446054d7`；容器 2076.940104 秒（34:36.940）、62,305 帧、1920×1080、名义 30fps、AAC 48kHz 双声道。

播放器章节导航依次为：历史方法版；分兵合军与登船；受控零库存；月界净增 10；县边净减 236。后四段明确为实录补充，R06 物理闭包和 R04 损失归因继续标为未闭。文件中第一部分约 32:26.888，后续补充章约 2:10.052；没有新增原始取材时长。

只对本次新文件执行一次严格全 AV 解码、包时间戳检查，以及开头、两部分交界和结尾的四张稀疏抽帧。旧输入的已过 QA 未重跑。视频/音频 DTS 严格递增，全部 62,305 帧保留；AAC 尾部使接缝有不足一帧的时间偏移，文件仅称名义 30fps。完整人工 1×、continuous-clean 与 human signoff 均未完成；正式动态仍 0/11，A/B/C 仍 0/3，未上传。

当次查询最新正式 xar-promo-toolchain 为 v0.3.0；wheel SHA-256 `f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`。使用核验后的主工作树 `tools/.venv/Scripts/python.exe`。安装来源、CLI 与独立 skill 的实际路径绑定见 `INTAKE.actual.json`。公开 `plan_concat`/`execute_render_plan` 进行无损封装，原生 CLI start-run/preserve/validate 登记精确产物；没有虚报 native build 或 generic audit。

pending review 使用公开 review API，并先执行 CLI `review --plan-only`。四张实际命令将输入前精确 seek 写入真实 argv，避免为每张分界帧再从头解码 32 分钟；未修改安装包，没有将自动结果变成人工 approval。实际命令与 pending 模板均留在本机新 run。

旧的两个 work 电影副本已经精确删除，本版真实消费的是保留下来的 typography CAS；`INTAKE.actual.json` 绑定本轮删除回执及可读 keeper 身份。没有把已经删除的旧 work 路径当作可读输入。本包的机器路径仅证明该机器当时的状态；跨机器须重绑。

`DELIVERY.actual.json` 给出最终原生 manifest、影片、QA、pending review 与期限。影片、CAS、PNG 和完整进程输出留本机，不入 Git。本目录只保存可复用小型配方与精确身份记录。
