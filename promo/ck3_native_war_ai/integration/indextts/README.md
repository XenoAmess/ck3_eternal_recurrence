# 本机 IndexTTS 推理入口快照

`local_infer.py` 是本次安装时实际运行脚本的精确副本，9,188 bytes，SHA-256 `14d40a7fe9933cc6c74c887fc90ac82c4061fac3191914f5e0521e5e4622bca5`。它用于保存项目新增入口，未包含或修改上游模型实现。

**执行安装目录中的副本**：`D:/workspace/index-tts/local_infer.py`，使用同目录 `.venv/Scripts/python.exe`。脚本按自身所在目录寻找上游 `indextts/`、`checkpoints/` 与本地缓存；仓库中的归档副本不能直接在本目录调用。它所引用的 `LOCAL_INSTALL.md` 位于实际安装目录。

单句输入使用 `--text-file`、`--reference`、`--output`；批量使用 `--batch-file` 替代 `--text-file / --output`，每项格式为 `{ "id": "唯一标识", "text": "旁白", "output": "全新.wav" }`。相对输出路径基于批量 JSON 所在目录解析，目录须已存在；已有输出或 sidecar 拒绝覆盖。

请求、WAV、波形与耗时收据独立保存。脚本没有自动替换影片中的 EdgeTTS 音频，也不会把波形检查当作听感审阅。本轮 EdgeTTS 样片和 IndexTTS 安装验证是两个独立交付物。
