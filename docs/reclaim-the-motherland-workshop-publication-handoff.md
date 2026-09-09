# 重整河山：Steam Workshop 发布交接

状态：**公开发布完成，运行时上传、订阅缓存 L3、页面媒体与 DLC 依赖均已复核。**

## 公开产品

- 产品：\`mod_reclaim_the_motherland\`
- 版本：\`0.1.1\`
- Workshop item：[\`3798404599\`](https://steamcommunity.com/sharedfiles/filedetails/?id=3798404599)
- 应用：Crusader Kings III（App ID \`1158310\`）
- 依赖：\`Crusader Kings III: All Under Heaven\`；中文统一写作《溥天之下》
- 可见性：Public；Steam 匿名接口返回 \`result=1\`、\`visibility=0\`
- BBCode 权威源：\`workshop/reclaim_the_motherland_description.bbcode\`
- 截图来源与顺序：\`workshop/reclaim_the_motherland_screenshots.md\`

## 上传与缓存身份

- 上传用 staging：\`D:\workspace\reclaim-motherland-v0.1.1-publication\release\mod_reclaim_the_motherland\`
- ID-bearing manifest：\`D:\workspace\reclaim-motherland-v0.1.1-publication\release\mod_reclaim_the_motherland.manifest.json\`
- manifest SHA-256：\`f1d4f19816650267ad2ca181d9e18295c910623b88fe4b56ffd6bbc3cb5b6946\`
- deterministic ZIP SHA-256：\`b7096953d96ff2c5542fa7b18fc9a9a02536750969f9f5ef57a08bc65b96e962\`
- Steam 订阅缓存：\`D:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\3798404599\`
- 缓存核对：28/28 文件严格匹配 ID-bearing manifest
- 外层 launcher descriptor：\`C:\Users\1\Documents\Paradox Interactive\Crusader Kings III\mod\mod_reclaim_the_motherland.mod\`
- 内层正式 \`descriptor.mod\`：上传后已重建，不含 \`remote_file_id\`

启动器上传日志位于 \`C:\Users\1\AppData\Local\Paradox Interactive\launcher-v2\logs\launcher-2026-09-09.log\`。日志记录 2026-09-09 10:30:57 开始、10:31:05 上传成功。

## Workshop fresh-cache L3

- Run：\`D:\workspace\ck3_reclaim_the_motherland_design_process_assets\reclaim\runs\rqa_workshop_20260909_1952_capital_3798404599_v011\`
- Wrapper report SHA-256：\`6d5ad36cd296f61a83573b501a566c90ec918e9d811ab5b38eb41ade3513c6ab\`
- Cell report SHA-256：\`5859e13cdf06f8287cb2a28aa1f3d72669d4d33ff2cb50fb4ab691dee4938e30\`
- 结果：GREEN；19/19 markers；项目 diagnostics 为 0
- 时长：878.326 秒；CK3 槽位等待 0.165 秒
- runtime product tree SHA-256：\`9313dbd44116241f7bd4f22000068033778ad3c584a5933599915e5472dfe947\`
- 清理：source/runtime 与保护存储未改写，CK3 进程树已回收，隔离 userdir 已删除

个人领地断言检查每个原直辖伯爵领仍满足 \`holder = root\`，并非只检查旧天子仍是 top liege。产品分支仅销毁 \`h_china\`，跳过 \`force_step_down_landed_titles = yes\`，同时把旧天子排除在该轮弱势王/帝头衔裁剪之外。

## 开封中心镜头

宣传截图所在 run 在群雄割据后调用原生 MCP \`ck3_center_map_on_landed_title_v1("b_kaifeng")\`。返回的 title ID 为 \`13949\`，capital province 为 \`9822\`；相机 target/current 相同，\`settled\` 与 \`postcondition_verified\` 均为 true。

- 导航 JSON SHA-256：\`cc280aaadd48a2ab4fc3d8f193f3edcfe6e0afbb92042c1a832077e1e92acdde\`
- 开封地图 PNG SHA-256：\`772defc92ca9846758a5e42da554d5b5ec021b1e290c747d9736491a4cdc150a\`
- 视觉辅证命中“管城县”，排除了“教宗 / 教宗国 / 意大利 / 罗马 / 那波利 / 萨莱诺”与测试字样

这条门禁已经写入 runner 和媒体生成器；没有 GREEN 导航证据时，媒体生成器会拒绝产出商店 JPG。

## 页面资产

- Thumbnail：640×640，803,154 bytes，SHA-256 \`564a558d5dc280e9049fb6907db36418a9a29085802da2ce8bed0f1dff6e1c38\`
- Media 1：后宋立于开封，SHA-256 \`603071742f6d450fb9867f0d40b60108886769be2f67802640b9e726dea91f51\`
- Media 2：宣称复辟已就绪，SHA-256 \`00e307d670ebe8b2f73eb05c2b49c92adc14c901a1b97342a35713ebe06dea14\`
- Media 3：复辟诏告与效果，SHA-256 \`e3886bf3b385bbacf7d4b5b413c0e5e4ccf1c87de4735eeb05de14b459d08bca\`
- 公开页面证据：\`D:\workspace\ck3_reclaim_the_motherland_design_process_assets\reclaim\steam\public_page_final.png\`，SHA-256 \`f532f793a59fa9988823a97fa23c83f7258b6adbbcab6e4e9c81e27b3446405c\`
- DLC 勾选证据：\`required_dlc_saved.png\`，SHA-256 \`642bc89e737550eebb095c64dad2ad57cbace8326160d06891a780be899509c6\`

三张媒体只做确定性裁切和 JPEG 编码，没有生成或改写游戏内容；AI 生成主视觉仅作为 thumbnail，不冒充实机截图。

## 后续更新规则

1. 修改仓库源码后先重跑与风险相称的 L0，并用本脚本生成新的 release staging。
2. 只能上传 staging，不能上传开发树；上传前 staging 内层 descriptor 不得预置 \`remote_file_id\`。
3. 更新同一 Workshop item \`3798404599\`；成功后立即重建无 ID 的正式 staging。
4. 从全新订阅缓存执行 28/28 核对和 MCP-first L3；页面素材变更时同步更新入库 BBCode、媒体 ledger 与 changelog。
5. 任何地图宣传素材必须先以 MCP 定位 \`b_kaifeng\` 并通过错误地域负词门禁；不得复用意大利镜头。

