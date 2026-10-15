# R0174便携证据包

本目录保存新派生portable manifest、索引和精确原始JSON ZIP。原始完整manifest、prepared、snapshot、现金、Arm/Resume/status、Halt、事件及完整Driver sidecar的字节都在ZIP内保持不变。路径字符串为来源标签；派生manifest通过显式prefixmap解析到本次临时archive root。

- 新ZIP：5051824B/SHA719cfb636504b52de2f1be5d8a43c939e588fad952d0f8dba2484fd6df84026d。
- 231个原件、108459029B展开，22个fullsidecar共93414207B；全部原件有逐项SHA。
- 复用相邻episode04-r0173-20261015中的既有18files ZIP，不重复打包；索引钉其manifest与ZIP。
- 没有视频、.ck3、EXE/DLL、profile cache、mutable driver-state或游戏依赖。

在仓库和项目Python依赖齐备时：

```text
python -B -X utf8 promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/replay_r0174_archive.py --work-dir <新的外置临时目录>
```

可显式加`--repo <clone根>`和`--bundle-dir <本目录>`。不得使用已存在的work-dir。程序只写这个新临时目录，不启动游戏/SDK，不复制或打开旧C/D数据根。

程序流式核所有231个ZIP原件SHA，提取除21个daily大sidecar之外的210项/18426238B。日sidecar保全在ZIP，想做其他研究可按index显式另行提取；当前pair checker只读baseline完整sidecar。重放调用现有checker --phase pair，相对manifest/path均从新根读取；再调用既有R0173 verifier重算历史3金币源链。原始源盘路径或可执行文件在receipt内出现，不代表依赖它们存在。

范围：21日saved-T0 continuation control对历史处理组保存后续行；原R0173没有load9ab3，新控制observer源码1463与旧处理组8dd分别记录。原R07≤7日/避开经济结算/静止T0新Move仍false。空qualified不是零费，maintenance仍unclosed，R01 commander/ABC仍pending。新机归档复验不授实机资格。

validation包含真实相对重放PASS和单项template-source测试旧失败/新通过。Git source projection遵从eol=lf，canonical freeze13320B/SHA1d359...；原CRLF字节保留外置，原始游戏回包通过ZIP避开Git换行转换。

本轮临时作业/展开准入截止2026-10-16T07:45:01.597000+00:00，计既有shared512MiB，无延长。持久知识与归档后续按统一存储策略复核。
