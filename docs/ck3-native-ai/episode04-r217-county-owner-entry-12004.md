# R217: county arrival, missing invocation owner and normal close

## R0213 本机县 writer 完整窗口与 owner 缺键（2026-10-19）

`machine_id: desktop-3fevhd2-1c74096080`，运行源码 `ba3528fc04621529ed528930623b5d34826a46a4`，CK3 1.20.0.4，William 33388/Army0。R217 actor 只做一次 Move，七个准确自然日后到 1513、日期 raw53147544；采样 OFF/clear、原生 Save 与 actor exit0。独立正常 GUI Quit 后 CK3/native 0、原 public/host/allocator wait0、keeper last6802 且线程已退，Root bus seq6803 done/resources[]，均由独立小原件绑定，不能只凭 actor Save 推正常闭场。

到达日新 writer 窗口全局 delta195（容量512），窗口连续。23 条同日期县首选 physical writer 有 17 正/6 合法零，保留 debit 合计236；但原 native q3 响应的 23 条**全部没有 owner child**，不是 Python normalizer 漏掉。生产 consumer 因 `invocation_owner_not_captured` 排除23条，qualified owner positive0、Army 调用时归属未证、县总额 null。查询时 Army0 兵数端点及数值相等不能补过去的 R13/TID/父事件；同 host 新 query 也不能回收过去寄存器。即使全局窗口连续，R04 原卡仍开放，研究10/14、业务7/11不增加。

B 机会只读提取见 [B opportunity extract](evidence/episode04-r217-county-owner-entry-12004/analysis/b-stock-opportunity.json)：当前库存有余量，但当前总速率为负；将来 positive stock growth、future callback 均未观察，B 合格站点仍0/2。窗口 Take01 原片 179.033 秒、H.264 1280×720/30 fps，三张原尺寸稀疏帧经 Root 直接审阅是 Jan26/6746→Jan27/6510；先前把首帧写作 Jan20 已更正。该媒体 QA **没有完整解码**、连续 clean 或人类1×签核，正式动态仍0/11，ABC0/3；不能因兵数下降给出县损耗归属口播。

在下次源码施工前保留 [owner-at-writer合同](county-primary-owner-at-writer-12004.md)的严格返回阶段连接。缺键原因仍未完全定位：静态假设“县调用发生在 active pre-date TLS 之外”与事实相容但未证实；未来需要源端在没有 owner child 时给明确 diagnostic，并在新 DLL/冷测/实机中独立验收，不能改写本场结果。

[Exact portable index](evidence/episode04-r217-county-owner-entry-12004/index.json) preserves actor-stage close-pending history separately from the later normal-close and Root release records. Original records without a machine ID remain marked unknown in the index; paths do not prove machine identity.

```mermaid
flowchart LR
  M[One typed Move] --> D[Seven exact days and arrival1513]
  D --> W[Continuous global writer window]
  W -. native owner child absent23of23 .-> O[Army invocation ownership unknown]
  Q[Independent GUI close and original process waits] --> C[OS0 and Root bus6803 resources empty]
```

## 27 秒研究插片已完成技术制作（2026-10-19 UTC 补录）

来源机器仍为 `desktop-3fevhd2-1c74096080`。02:32 UTC 的[独立交付](evidence/episode04-r217-county-owner-entry-12004/editorial-27s/delivery.actual.json)记录新 27 秒、810 帧 rough insert；24 秒原片窗口 51–75 秒后接 3 秒卡片。影片 1,698,188 B，SHA-256 `4b7f762d37c2c6e961e7284a7db26d24634dfcbe1970eb8043e2428611619e33`，仅保留来源机器路径引用，不重复入库媒体本体，也未改旧 Full71。

[冻结编辑输入](evidence/episode04-r217-county-owner-entry-12004/editorial-27s/insert.candidate.json)保留当时 candidate 状态；[实际 build](evidence/episode04-r217-county-owner-entry-12004/editorial-27s/build-result.actual.json)、[probe/decode/PTS QA](evidence/episode04-r217-county-owner-entry-12004/editorial-27s/media-qa.actual.json)及[用途闭场](evidence/episode04-r217-county-owner-entry-12004/editorial-27s/purpose-closed.actual.json)是后续独立事实。技术 QA 通过不替代其原记录中尚待的稀疏视觉审阅、人类1×或签核。

可复用口播只说地图6746→6510、物理6741→6505均少236，损失来源仍待验证。原生23条缺 owner child 的结果不变；数值吻合不补 invocation Army 因果，不能说“236 已证全部县界损耗”。新插片没有 formal R04、动态镜头或 ABC 信用；换机器制作须重新绑定输入和运行来源，不能把原机绝对路径当公共协议。
