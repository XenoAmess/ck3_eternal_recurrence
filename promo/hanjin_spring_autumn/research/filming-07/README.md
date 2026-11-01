# 第二期曹操实拍记录

machine_id：`4-8e1c2f1861`。片名《帮过我的朋友，挡住了我的去路》，取材范围为**190.1.1至193.10.6**。曹操7164，episode为`native-7164-2df1dba0c466`，Game PID为424。本期使用独立曹操新档。

原始证据位于`C:/workspace/hanjin-spring-autumn-20261031/shooting-04-cao-cao/`，制作工程位于同根`edit-07-cao-cao/`；下文原件路径相对原始证据目录。这里只入库小型记录与索引，原片和配音留在外置工作包。

## 完整实拍结局

曹操34岁从己吾、襄邑、雍丘三县开局，约6023金、4358兵，选择“一统天下”。讨董期间在市丘以4358接战25002，援军加入后约29934对23584；曹玉战死，本军撤出。191.6.1董卓在长安被杀，讨董战争以“无效”结束，不是曹操打赢或杀死董卓。

群雄并起后本局九县。191.6.12“陈留之谋”实际选即日进兵，没有因张邈旧恩选择从缓。首战3486对472、六日后战分18，随后两边换家：陈留占过又失，雍丘、襄邑也丢了。第一次完整目标69点，接受度−87；加1000金的草案仅到−80，没有提交或付款。

“济北受降”第一项带来22000青州军，实际任命曹仁。原军回保、新军攻城；补给与战事损耗很重，后来约11000，不能写作青州军全灭。193年九月曹仁在陈留击败张邈，张邈被俘。9.25战分50、完整目标66点；4000金草案把接受度从−25推到+5，**实际提交一次即战争结束**，胜利窗口与地图变化均已拍到。金钱6086.35577→2086.35577，直辖9→27，净增18处，不是等到100战分或统一整个兖州。

193.10.6出现`hd190.0103`“东略兖州”，实际选择第二项“兵已疲敝，暂且休整”。实例26消失，选后无当前事件，本轮停止继续征服。片尾直接介绍Mod和下载入口，不留后续预告。

主要结尾证据为`settlement-after-submit-response.json`、`settlement-root-before-response.json`、`settlement-root-after-response.json`、同期和约与胜利截图，以及`ending-advance-1-event-context-response.json`、`ending-choose-rest-response.json`与后态。五组既有离线研究和结尾事件见[event-index.json](event-index.json)；它们各自的旧截止时点保留，不拿源码效果替代后来实际执行。

## 两段录像缺口

| UTC缺口 | 内容与补画 |
| --- | --- |
| 2026-11-01 09:20:17.4657672Z至09:43:32.9777352Z | 成军4358与市丘方向出发，用当时`gathering-01.png`、`sortie-progress-01.png`等真实截图补齐，再接take02战场。 |
| 2026-11-01 11:34:18.9674577Z至12:35:38.9894409Z | 部分换家后态、济北受降和曹仁任命，用`counter-clockwave-5-event-hd_huangjin-10.jpg`、`qingzhou-army-before-assign-screen.jpg`、`qingzhou-commander-assign-screen.jpg`、`qingzhou-commander-person-screen.jpg`等同期截图补齐。后续take04说明已成军状态，不能冒充当时任命点击。 |

截图与录像保留真实来源。另有少量真实录像定格用于读字和避开无关弹窗，不把定格说成新录屏。具体切点与比例以最终EDL和交付记录为准。

## 配音、剪辑和审核状态

最终二十场口播见[实拍导演稿](../../episode-02-cao-cao.md)，与制作工程当前`front-production.json`逐字同步。第4至6场已精简重配；初稿和旧音频保留。Edge TTS为7.3.1，`zh-CN-YunjianNeural`、rate `-12%`、pitch `-8Hz`。

当前成片实测**553.556秒（9分13秒）**，1920×1080，H.264视频、AAC立体声，已烧录中文字幕，另附SRT。文件58,790,308字节，SHA-256为`b82c4cb69b91a3e12eaab4ec99fb4a012fcd3b6f773af5588646b3ce29de6b3b`。本机交付为`C:/workspace/hanjin-spring-autumn-20261031/episode02-caocao-review.mp4`，配套同名前缀字幕、配音和简介。

最终二十场台词与字幕文字一致，所选录像片段均在原片EOF以内；录像来源约占81.1%时长，其中也包括暂停的地图、界面与人物动画，不能说成81.1%都在推进游戏。其余为真实截图／定格及宣传尾卡。完整解码exit0；正式xar-promo 0.3.0完成plan/build与20帧证据绑定自动审计，另产出41帧待审片包。抽查了全片联系图和最终报价、胜利、直辖、休整前后、尾卡六个画面，没有将抽帧说成全片1倍速人工审阅。**人工签核为`null`，等待用户审片，没有外部投稿。**

精确交付见[delivery-snapshot.json](delivery-snapshot.json)，技术审计见[automated-audit.json](automated-audit.json)，口播／镜头检查见[editorial-check.json](editorial-check.json)，切点见[edit-decision-list.json](edit-decision-list.json)。`cao-ep02-001`保留初次选片；核实战斗及休整片段后，正式交付绑定独立`cao-ep02-002`，不追改旧run。简介与三个Workshop链接见[description.txt](description.txt)。

## 保存与正常闭场

SDK保存已提交，但错误地等待`launcher/state/native-session/profile/save games/xar_checkpoint.ck3`，返回文件未出现错误，见`ending-save-checkpoint-response.json`。真实Game profile为`launcher/state/profile`，没有为此重放保存。

`ending-real-save-evidence.json`在2026-11-01T13:46:15.666001Z记录实际`launcher/state/profile/save games/xar_checkpoint.ck3`存在，49,805,919字节，SHA-256为`9ba6bf78423062fd2d05eafcf1fcc44a2a7acc9c166a60df07fa83a445e9e9da`。保留SDK错误与实际文件证据，**不授予`SAVE_CONFIRMED`**，不由文件存在推断完整重载验收。

`launcher/exit.json`记录Game424于2026-11-01T13:57:38.7000579Z正常退出，exit_code为0。退出成功与保存资格分别记录。

## 制作分工与保留

主拍摄负责同一场游戏动作、录制、选片及最终编排；并行配音岗完成初稿和文档，独立素材岗核四段原片与事件时间。战斗三场精简后重新调用Edge，最终以二十场当前稿为准。初稿、首次选片和交付分别保留，不混记为用户批准。

正常退出后停止录制和keeper，按准确序号CAS释放屏幕；另领取短租约将显示恢复至原1024×768@60后立即释放。[闭场证据](closed-session.json)保留机器、Game出生身份、实际退出及保存诊断。拍摄包2.27GB、剪辑包0.67GB，容量与复核期限见[存储闭场](storage-closure.json)；没有复制原片进Git或声称自动清理已部署。
