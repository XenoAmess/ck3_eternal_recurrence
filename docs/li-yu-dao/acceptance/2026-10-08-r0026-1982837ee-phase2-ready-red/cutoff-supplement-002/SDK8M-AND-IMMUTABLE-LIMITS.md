# R26 截止点追加说明：SDK 8 MiB 与不可变副本

当前截止仍是 SDK89 SAVE；没有在归档过程中补造 R4 B3 author/资格、B4/B5、退出或CAS成功。原SDK89为8552387字节/SHA ada1d5d525b9e439cd912916dd5778b8ff693970caef1849392d046baf0b0f93；native89为4053918字节/SHA7c855308f464a78600dde9b5930d734f20ecdf943b994c130db074b0dc863a24。两原件在第一包raw-evidence.zip中完整保留，未截取structured/text或沿用旧8MiB JSON门禁。

首次SPEC作者失败原ROOTwrapper：r26-root-r4-b3-spec-author-original-exec-20261008-001/RESULT.actual.json3104B/SHA8773855e88bb558678256341a411923e2200996eb35aa28cfb73a9c4e1117a7e，stdout/stderr均在本追加ZIP。ROOT明确报告该失败发生在SPEC/body0；旧失败保持。CP004256d…/CAP004ca191…及下一argv8b6f…仅是新源码/显式待执行入口，本截止点不预写成功。

0048的不可变副本由 checkpoints/round-3-withdrawal/COPY.actual.json2112B/SHA31dc6313d6f58bd8147eb42aeb52b359c3949951dd858be6f94201be00a2534f 绑定。其它已解析B1/B2/B3窗口的CAPTURE回执也在本追加ZIP。大.ck3副本永久留外置，归档没读正文、重哈希或复制。第一包清单中的 userdir/save games/xar_checkpoint.ck3 是各历史SAVE的来源descriptor；它会被后续SAVE覆盖，不证明当前该路径仍匹配旧SHA。应以原不可变副本及CAPTURE/COPY回执复核历史内容，不能拿最新live save替代它。

本追加包没有重读/重压第一包的105381938字节原料或6.8MB ZIP。第一包原INDEX/REPORT/ZIP保持原SHA，追加包只是16个小回执/索引，29612B ZIP。archiver验证仅针对字节归档；当前 .4 trigger修复、正式业务、继承保护与后续退出均未因此获得信用。
