# MiniMax 克隆音色与 TTS 接入笔记

核对日期：2026-09-25。依据 MiniMax 开放平台官方的[复刻音频上传](https://platform.minimax.cn/docs/api-reference/voice-cloning-uploadcloneaudio)、[音色快速复刻](https://platform.minimax.cn/docs/api-reference/voice-cloning-clone)和[同步语音合成 HTTP](https://platform.minimax.cn/docs/api-reference/speech-t2a-http)接口文档。接口、可用模型与计费可能变动；每次新项目调用前重新核对官方页面。

## 三步请求链

1. `POST https://api.minimax.cn/v1/files/upload`，`Authorization: Bearer <API_KEY>`，请求体为 `multipart/form-data`，字段 `purpose=voice_clone` 与 `file=<二进制音频>`。只接受 `mp3/m4a/wav`，时长 **10 秒至 5 分钟**，文件 **不超过 20 MB**。响应同时检查 HTTP 状态和 `base_resp.status_code == 0`，保存 `file.file_id`；HTTP 200 本身不代表业务成功。
2. `POST https://api.minimax.cn/v1/voice_clone`，JSON 至少包含上述整数 `file_id` 和新的 `voice_id`。自定义 ID 长度为 8–256，以英文字母开头，只含字母、数字、`-`、`_`，末位不能是 `-` 或 `_`，不能与已有 ID 重复。创建前需完成平台个人或企业认证。可选 `clone_prompt` 需要另上传 **不足 8 秒**、不超过 20 MB 的示例音频，并与 `prompt_text` 一起提供；没有可靠逐字稿时省略。可选 `text_validation` 是参考音频的预期文本，最多 200 字符；服务用 ASR 相似度和 `accuracy`（默认 0.7）比较，低于阈值报 `1043`。可选试听 `text` 最多 1000 字符，且必须指定 `model`，会按 TTS 正常计费。`need_noise_reduction`、`need_volume_normalization` 默认都是 `false`。响应检查 `base_resp.status_code == 0`。**复刻后 7 天内未正式调用的音色会被删除**，所以创建后尽快用 TTS 正式调用并保存回执。
3. `POST https://api.minimax.cn/v1/t2a_v2`，JSON 使用克隆所得 `voice_id`：例如 `model=speech-2.8-hd`、`text`、`stream=false`、`voice_setting={voice_id,speed,vol,pitch,emotion}`、`audio_setting={sample_rate,bitrate,format,channel}`。单次文本小于 10,000 字符，超过 3,000 字符官方建议流式；本项目按镜头/句群拆分，保存每段请求与响应。非流式默认 `output_format=hex`，`data.audio` 是 **十六进制音频字节**，不是 base64；检查 `base_resp.status_code == 0`、`data` 非空、`data.status == 2` 后再解码。也可请求 `output_format=url`，但链接仅 24 小时，过程资产应及时下载并哈希保存。官方支持 `subtitle_enable` 和句级/词级时间戳，但成片仍须用实际音频时长做对齐验收。

## 本项目样稿调用约定

- 用户于 2026-09-19 提供的私人参考音频约 40.405 秒、1,002,914 字节，格式为 `m4a`，满足官方上传时长、大小和格式要求。原音频与 API Key 留在仓库外的私有 attempt；Git 中只记录来源哈希、请求参数、业务状态、生成音频哈希和审片结论，不提交原声、Bearer header、完整服务响应中的敏感字段。
- 本次数字演算样稿先用 `speech-2.8-hd`、`language_boost=Chinese`、自然平稳的 `emotion=calm`、`speed=0.95`、`vol=1`、`pitch=0` 试音。这是 **MiniMax 自身参数**，不能把 IndexTTS 的 `duration_factor=0.90` 解释成同一语速。试听通过后才可固定新系列配置。
- 一段旁白一次请求，绑定原稿 SHA、`voice_id`、模型、全部声线参数、服务 `trace_id`、音频 SHA 和实测时长。网络或业务 RED 保留本次 attempt，重试建新 attempt；不得把已收费响应覆盖掉。
- 视频交付顺序按用户 2026-09-25 指令：技术校验后，先只将成片复制入固定 OneDrive 客户端同步目录并核对客户端“已上传”；随后做本机画面审核，发现问题另起 attempt 与新文件名。自动检查不等于用户签核。

2026-09-25 首次私有实测：参考音频上传返回成功并取得 `file_id`，随后 `voice_clone` 返回 HTTP 200、业务状态码 **2061**，提示当前 `MINIMAX_API_KEY` 的 Token Plan 不支持 `voice_clone`。这是账户套餐/密钥能力门槛，不能通过重试相同请求、改写回执或改用示例 `voice_id` 消除。失败 attempt 和服务原始响应已留在仓库外；后续必须换用具有 Audio 音色复刻权限的 Key 再建新 attempt。当前尚未获得 MiniMax 合成音频，不得把样片标为已完成。

最小请求结构（占位符不是真实凭据）：

```json
{
  "model": "speech-2.8-hd",
  "text": "这里放已经审过的中文旁白。",
  "stream": false,
  "voice_setting": {
    "voice_id": "<已成功克隆的自定义 ID>",
    "speed": 0.95,
    "vol": 1,
    "pitch": 0,
    "emotion": "calm"
  },
  "audio_setting": {
    "sample_rate": 32000,
    "bitrate": 128000,
    "format": "mp3",
    "channel": 1
  },
  "language_boost": "Chinese",
  "subtitle_enable": false,
  "output_format": "hex"
}
```

实际调用时由 Python 从 `MINIMAX_API_KEY` 环境变量读取凭据，只检查是否存在，绝不打印值；上传用 `requests.post(..., data={"purpose":"voice_clone"}, files={"file": ...})`，克隆和合成用 `requests.post(..., json=payload)`。请先核对 `base_resp` 再读 `file_id` 或解码 `bytes.fromhex(response["data"]["audio"])`。不要把官方页面的示例 `file_id` 或系统声线 `voice_id` 当作本项目的真实值。
