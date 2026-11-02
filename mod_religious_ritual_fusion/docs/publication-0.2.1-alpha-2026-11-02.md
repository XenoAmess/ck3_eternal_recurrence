# 0.2.1 Alpha：已公开发布，下载与90文件校验通过

`machine_id: 4-8e1c2f1861`；发布与下载时间为2026-11-02 UTC，历史场次保留原时间。**00:14:31.810186Z已更新同一[Workshop条目3826756673](https://steamcommunity.com/sharedfiles/filedetails/?id=3826756673)，Submit EResult1。** 正式90文件、完整中英文说明与Notes已提交，封面及原19项gallery保持。真实Steam下载及安装缓存的90文件精确校验通过；本版R0066缓存主菜单与正常退出也已通过，不授完整产品业务通过。

## 内容来源与局部实机范围

正式内容Source A固定为`99462364158fc0165cd2cf2b2d4813bb572920f9`，tag为`religious-ritual-fusion-v0.2.1-alpha-publish1`。canonical manifest含90文件、1,290,146B，manifest自身17,020B，SHA`3508171773d8f4e91cfd376a7003c5a5b6c6fbcffcde0229281ab099acc321df`。相对0.2.0，实际只改`gui/rrf_fusion_window.gui`及版本`descriptor.mod`，其余88文件相同；内层descriptor不含remote_file_id。后继工具修复、文案与本发布记录不移动该tag，也不改变已上传包的来源身份。

热修复为核心信条、教义和融合影响三个直接页明确设置100%编辑区大小，解决默认100×100视口使正文和滚动条挤在左上角的问题。R0064／a76中Root已审三页全幅图，生产名单实际32个不同身份，完成首端→末端→返回首端的滚动检查；有限视口、右侧预览及底部控件保持。取消后钱包、日期、宗教、教义与信条保持，原被动`rrfa.30`一次PASS，无创建、付款、日期推进或保存。public0、独立verify0、Game OS0、Native清理0、host0、keeper0；SCREEN正常释放15131。此结果仅授该UI补验单元，不补成历史完整矩阵通过。

## 实际提交与匿名回读

使用现生产native publisher执行`update`，App1158310、唯一item3826756673、public0；没有CreateItem、追加预览或重传封面。最终冻结标题／说明／Notes原件为63／7,804／2,870B。完整标签为Religion、Gameplay、`1.20 'Crozier'`。

00:19:34.906081Z→00:19:37.064668Z，生产匿名回读PID21428原wait **1**：标题和完整BBCode说明精确相同，`change_notes_exact=false`。原1及原HTML完整保留。随后只消费同一次HTML、当前API时间1793578471对应的Notes条目和最终完整Notes，复用既有结构比较器：**40项事件、1,941个语义文本字符及全部顺序相同，零差异**。仅作HTML实体／显示换行及对应标题、列表、粗体的表示转换，普通空格、标点、内部换行均不忽略；不声称读回服务器原始BBCode字节。没有为此修补或重新提交Notes，也没有额外匿名重抓。

Root本次fresh native前后清单均19项，全部元数据与顺序精确相同。新匿名API的封面URL指纹与上次已逐字验证的CDN原件一致，当前正式thumbnail及保留原件同为696,215B、SHA`1f6b9353d4df99eb5e34a2482aef561731d2df75976a36ffa2a01f7f95f5d5ba`；本次未重新下载封面body。图片只证明各自记录范围，封面为AI宣传插画。

## 真实下载、离线恢复与资源记账

00:17:00.456275Z→00:17:18.958347Z，下载调用PID14880原wait0，隔离worker5644退出0。`DownloadItem`实际started=true，匹配回调3406／App1158310／item3826756673／EResult1，status=complete，installed=true，needs_update／downloading／pending均false。实际缓存位于`C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/3826756673`，安装size1,290,146B、timestamp1793578471；公共prepare独立核对90个路径、大小和SHA全等正式manifest，包含新descriptor和GUI。

本次保留既有缓存，使用`expected_cache_path=null`的原生更新路线；`fresh_cache_requested=false`，没有声称先前缓存不存在或做了冷缓存下载。未从staging复制冒充下载，未手改ACF、退订或改动三项长期禁回装屏障。

常规mode-offline原1及force-offline原1均因`expected one visible Steam window, found 0`拒绝，不能记成已恢复离线。打开Steam console后，mode-offline-b02于00:35:14.655959Z原wait0；00:36:23.583832Z后台原生读回`offline=true`，Steam PID13760／出生FILETIME`134378949641026140`／版本11.15.70.27。该观察是当时事实，后续Game仍需自己的新鲜离线凭据。

实际提交和下载均在当时新鲜网络SCREEN租约下完成。租约后续闲置到期，01:04:00.658345Z释放原wait0、序号15144，resources=[]、state=waiting，自动retirement记为`expired-own-claim-released`／`business_status=unresolved_red`，prior_sequence15142。该后到元数据保留，不把任务整体写成绿，也不将其解释成已完成Steam提交被撤销。

## R0065原失败与R0066缓存菜单通过

`menu_acceptance: PASS`，实际成功场为R0066；R0065原失败单独保留。

R0065/a77实际缓存90文件与原生稳定主菜单已观察，但Root错过人工退出期限，public/verify2、正常关闭未资格；host随后stop清理的Game退出1，资源闭合后释放15161，原失败保留。后继R0066/a78在独立普通profile复用同一下载缓存，重新逐项exact90并实际观察稳定主菜单。受委派操作者/root/resume_runtime_prepare查看全幅原图，以当场映射执行一次原版exit_game_button / FrontEndMainView.OnQuit；其真实reviewer被公共consumer接受。retained GameOS0、Native0、host0、public0、verify0、keeper0、allocator0，02:15:02Z闭证确认无Game/SCREEN，精确释放15168。未启动新游戏、加载业务存档或挂验收fixture；独立VFS路径仍UNKNOWN，业务和product_release_pass仍false。闭证 `W/cache-021-r66-a01/ALL-ORIGINAL-TERMINALS.actual.json` 为31529B / SHA `d6ffa10a77558efb4bd22cc34f8f605b19c9e5585fe9a9b0b4de38b77be97f33`。

准备初次原wait1源于PYTHONPATH缺实际Workshop包、无法导入compatibility_tags；仅补准备环境后，b02 prepare／plan／preflight原wait均0。初次以冻结副本入口分配原2，被“Machine-admission writer differs from the actual shared source peer”守卫挡在allocate前。改用实际生产源码入口的新操作b02进入READY，冻结runtime保持；这些准备／路由纠正不授菜单或全业务通过。

历史12／20完整业务矩阵仍incomplete；SDK续行资格、领地宗教地图实际颜色、跨宗教来源、100核心、完整拒绝矩阵、冷却到期、AI、多人及旧存档兼容仍有未验范围。[0.2.0的R0060缓存菜单通过](publication-0.2.0-alpha-2026-10-29.md)属于上一版本，不能直接抵扣本版；软件测试、局部UI、下载及菜单亦分别记账。永久版本正文见[0.2.1 changelog](../../docs/release-changelogs/religious-ritual-fusion/0.2.1.md)。

## 关键原件pins

本机外部证据根`W=C:/workspace/rrf-ui-release-20261102`；以下路径相对W，原件未由本文重建或改写。

| 原件 | 相对路径 | B | SHA256 |
| --- | --- | ---: | --- |
| 正式manifest | `publication/canonical-staging.manifest.json` | 17020 | `3508171773d8f4e91cfd376a7003c5a5b6c6fbcffcde0229281ab099acc321df` |
| Submit完成 | `network/CONTENT-UPDATE.receipt.json` | 656 | `d5e443221b75193deaca51e46dd42afa3a92254c11a2fe592db37881e95d82d3` |
| 下载结果 | `network/download.stdout.json` | 2593 | `a4e68e76b357e8aff5c626d8a95d4947c5116d926235597618b8b395a5de5ada` |
| 实际缓存exact90 | `cache-021-a01/metadata/runtime-preparation-a01/prepared-workshop-cache021-b02/workshop-cache-exact-formal.json` | 25065 | `bb98f33ce493d3da19bf4f424e13cf587a07f1212664d9910c52a451466c3ab3` |
| 匿名回读闭证 | `network/anonymous-review-a01/PUBLIC-READBACK-REVIEW-CLOSED.actual.json` | 5740 | `8696589c448177c3c856df6b3d5a39ba90defaa08a3858da4880a10da9702003` |
| Notes完整语义比较 | `network/anonymous-review-a01/NOTES-SEMANTIC.actual.json` | 1680 | `ecf4c41fd97d38ee24833967e473d01f307b947e599e53e1fc73ef43063693d3` |
| 后台恢复离线 | `network/STEAM-OFFLINE-AFTER-PUBLISH.actual.json` | 2436 | `2a0296648cf0a224de507c6a95e5115e3a06afc76d633daaab3641125c8079b9` |
