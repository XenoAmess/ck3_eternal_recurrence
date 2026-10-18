# Episode04 Review02 69 段方法审阅版：实际影片与边界

`machine_id: desktop-3fevhd2-1c74096080`。2026-10-18 07:44 UTC，本机完成新的 Review02 方法审阅版：69 段、58,406 帧、1946.866667 秒，影片 89,450,267 B，SHA-256 `8f7496f357b392504ee18c842b7a6b29f31eae81e8475ff8ec7c31ad3bed946b`。本机媒体输入 source HEAD `65ce6ae5e55c0e8a855bebb6da3a1ccef08a711f`；原 69 段编码源 `6a5a42eb563aa12951f9a0d16141146a9fdeec1d`。机器上的具体 MP4 和原件位置由 [小型原始交接](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/full69-method-preview-a02/evidence/ROOT-DELIVERY.final-a02.json)精确记录，其路径不构成其他机器的安装或素材事实。

本版按 [复用索引和源码](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/full69-method-preview-a02/README.md)原样复用 66 个编码片段，只对 C05-09、C05-10、C05-14 重编。C05-09 的 `1/1` 改以明显画面说明限定为记录的界面显示值；C05-14 的“新增一人”限定为新 1/1 角色记录，不暗示实体兵员增加；C05-10 明示未拍到途中会合或合并按钮瞬间，R194 只支持同地拆合后的读回。三处注释放在卡片下方与旁白之间，C05-10 顶部通用 PARTIAL 横标移离卡片小标题；旧配音原字节保留。

正式 `xar_promo` 构建及 postbuild validate 均返回 0。机器 QA 对真正的成片做了绑定 FFprobe、58,406 帧严格递增且符合 30fps 网格的时间戳检查、全片 FFmpeg strict decode，并抽取三处**最终编码**画面直接查看，结论仅为三帧排版 PASS。首个 QA attempt 因预审 ASS 的 Windows CRLF 与工具链产物 LF 原始哈希不同而失败；原失败保留，独立 a03 QA 用规范化文本精确绑定正式 ASS 后通过。旧版三处叠字的视觉 RED 也保留，不能追认为曾通过。

这是一份 **PARTIAL METHOD REVIEW / NO SIGNOFF** 方法预览。45 处关键动态镜头仍待拍摄及原生审阅，正式动态信用为 0；没有完成整片人工 1 倍速观看、正式成片签核、导出或上传。不能用这份方法片证明 R05/R06/ABC 现场机制已验收。后续剪辑选择、研究判断和跨机开发可使用目录内的段落哈希映射与 composer；跨机重放前必须在目标机器重新绑定实际原件、运行环境、最新正式工具链与容量。
