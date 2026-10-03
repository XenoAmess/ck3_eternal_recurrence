# 《超人强》首发实机图片清单

状态：**干净实机媒体已准备，待上传与公开回读**。本图来自 CK3 `1.20.0.3` 的 R0013 production-only 正常角色交互，并已通过真正原版旧档安装及查看后只读保存复核。Steam media strip 尚未上传；本文件不能证明首发完成。

工坊标题固定为《超人强：越超人越强》。`mod_superman_qiang/thumbnail.png`为主封面，与这里要求的真实玩法截图是不同交付物。

## 权威来源

- Run：`desktop-3fevhd2-1c74096080--superman-qiang--R0013`。
- 外置实机证据：`C:/ck3-superman-qiang-20261004/acceptance/desktop-3fevhd2-1c74096080--superman-qiang--R0013`。
- GREEN 门禁：`existing-save-installation-gate-a01.json`，2,571 bytes，SHA-256 `070a7e9cb4a747bd5ff0d5e83f438eb0cd9c0bb201f1dbef0f1898ea179b6367`，实际 `ok=true`。
- 游戏：CK3 `1.20.0.3`；EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。
- 正式候选：L0-A0004 的 22 文件 production projection。其 [manifest](../mod_superman_qiang/docs/build-evidence-2026-10-04-L0-A0004/mod_superman_qiang.manifest.json) SHA-256 `63b0bc75a4c13bfdb343d77d621617eb425c204af081f00658454b193f261aac`；R0013 preparation 所记录的 22 个实际加载文件 SHA 均与该 manifest 一致。
- R0012 真正原版加载 `enabled_mods=[]`，保存普通 Robert 旧档；R0013 只加载 `['mod/sxad_product.mod']`，`fixture_source=null`。原版输入 checkpoint SHA-256 `b6f341c9879b572a0eb4325f96fd0338433d0fc4c9fa36fa4dfc0fbebb61506e`；正常查看后 checkpoint SHA-256 `6c70b6b1c2ab0b7ea49e1c8960505440e16118b79a68a85d2c4bd36fbc9154f8`。
- 原版角色 `31254` 与对照角色 `50601` 的六项基础属性、特质、SXAD 变量及修正逐字段比较均无变化，原本缺失的经验与净变化字段仍缺失；事件将缺省值显示为 0。`error.log` 为 0 bytes。
- 门禁范围：旧档安装与正常经验查看的只读行为。R0013 没有执行性行为；属性转移机制证据另见 [R0009 实机矩阵](../mod_superman_qiang/docs/live-R0009-and-R0010.md)。
- 原始 PNG：`C:/ck3-superman-qiang-20261004/acceptance/r13-ui-production-only-event-a01/screen.png`，1024×768，1,071,131 bytes，SHA-256 `dbb4b4085b775fcc93b9b2a1f13de82a2a6f4b562886f4409356a0561450e5cf`。仓库保留同字节 [原图](../images/superman_qiang_gameplay_experience.png)。
- 机器清单：[provenance.json](superman_qiang_media/provenance.json)，绑定原图、GREEN 门禁、manifest、保存、投影脚本及实际审图。

## 上传顺序

| 顺序 | 玩家可见内容 | 实机编号 | 裁切 `(left, top, right, bottom)` | 上传副本 | 尺寸 | JPEG bytes | SHA-256 |
|---:|---|---|---|---|---|---:|---|
| 1 | 普通 Robert 的中文性经验记录：经验 0、六项当前属性及净变化 | R0013 | `0,0,1024,768`，完整画面 | [01_experience_view.jpg](superman_qiang_media/01_experience_view.jpg) | 1024×768 | 170,086 | `d0d0adbaf28445d0aa1ced1de5351374337c6921a67919a9743bbf2dbb2eaa8d` |

推荐标题：`查看角色性经验 / View a character's experience`。

## 投影与审阅

原图比 native 追加媒体的严格 1 MiB 上限高 22,555 bytes，因此使用现有项目媒体编码合同：Pillow JPEG quality 90、optimized progressive、4:4:4（`subsampling=0`）。保留真实 1024×768 尺寸及完整画面，无裁切、缩放、合成或生成式修改。原图、未通过字节上限的保留原图 attempt 和 JPEG 候选均继续保全在 C 盘外置目录。

由 [投影脚本](../tools/compose_superman_qiang_workshop_media.py) 从仓库原图确定性重建，并验证输出与已审阅 JPEG 逐字节一致：

```text
tools\.venv\Scripts\python.exe tools/compose_superman_qiang_workshop_media.py --gate C:/ck3-superman-qiang-20261004/acceptance/desktop-3fevhd2-1c74096080--superman-qiang--R0013/existing-save-installation-gate-a01.json --check
```

本次实际重建退出码为 0；stdout、stderr、完整 argv 与回执保全于 `C:/ck3-superman-qiang-20261004/workshop-media-r13-a03/rebuild-check.*`。

root 与 media agent 均直接查看原始 PNG 和精确 JPEG 输出：标题“超人强·性经验记录”、经验 0、当前六属性 `5/24/11/11/7/21`、六项净变化 0、完整规则说明及“知道了”按钮可读，普通 51 岁角色窗口可见。未见测试按钮、夹具标记、调试控制台、缺图或拉伸。

截图、媒体清单与投影工具不进入正式 mod staging。原始素材和失败 attempt 不覆盖、不删除。

## 发布读回门

先创建本产品自己的新Workshop item并耐久记录ID，再调用`workshop_native_previews`冻结该item的现有strip，使用独立update追加选定图片。native媒体接口当前要求绝对路径、精确大小和SHA-256，图片严格小于1MiB。发布后重新查询预览列表，再匿名读取公开页，核对`highlight_strip_item`数量、顺序和放大图URL；下载公开CDN原图，比较字节、解码尺寸与像素，并直接审阅图片。

`SubmitItemUpdate`成功或页面出现缩略图不足以证明真实玩法图已公开。只有以上记录补齐才能把media gate标记为通过。
