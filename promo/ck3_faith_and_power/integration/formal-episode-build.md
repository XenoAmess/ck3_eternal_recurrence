# 正式一期可复现制作入口

`episode01_formal.py plan|build` 接受 `ck3-faith-power-formal-edit-v1`。输入绑定旧稿及delta、多个独立新声文本冻结/实测音轨批次、claim/原生字段读回、每句画面与顺序，以及明确未闭合或省略的结果槽。正式剪辑无需照读158句研究稿；保留与删除均由具体内容决定。20–40分钟是导演偏好，短于20分钟只作编辑提示，不能用留白、静帧或原片循环补时长。

`diagram` 为短源码图，`native-readback` 为实际查询数据图，`raw` 为全解码并有原始VFR帧PTS的真实录制。`mechanism-motion` 则绑定本机源码窄段与逐步语义、已完整解码/核CFR的说明视频，永久标注源码图解，不计为实机或业务结果。每种图层均有可见来源说明；原片和说明视频的同区间重复均拒绝。

`episode01_source_motion.py` 和批量入口 `episode01_source_motion_batch.py` 仅制作有来源的机制动画，不访问游戏、桌面或TTS。每步新增实际语义；文字和进度线留在1120像素上方，给正式双语字幕保留区域。输入显式传当次官方latest正式Release查询/精确wheel和已安装解释器的资格SHA，代码不固定某机器或某一版本资格。

共同复用现有有界2560×1440/30fps渲染器、VBV/文件大小限制、原生xar_promo run、直接制品登记、全AV解码/逐帧PTS/字幕与音轨检查。媒体不经CAS复制，已有原片/MP3按外部SHA引用。adapter和storage helper的精确源文本随小型输入保全；实际外置动画producer来源由每条receipt继续保留，发布时的包导入路径调整不追认成旧渲染来源。

`--v3-helper` 指向本仓库 `src/faith_power_promo/storage_carry_v3.py`，`--allocation-reader` 显式指向本机获准只读FileStandardInfo实现。v3按原始增长时点后的实际allocated path sum计正增长；不重复扣v2、不补满cap。每次重型制作仍重新核容量、同机器身份和实际工具链。输出始终待人工听审与完整1倍速签核。
