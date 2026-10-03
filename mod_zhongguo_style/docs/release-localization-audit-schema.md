# 发布本地化审计报告契约

正式 `--release` 构建必须读取 `docs/release-localization-audit.json`。该文件不是“翻译已经做过”的人工备注，而是
`prepare_release_localization.py audit` 在全部格式检查 GREEN 后写出的确定性哈希快照。实机验收仅用简体中文，英文和其他语言不要求语义、术语、文字种类或游戏内签核。它只留在开发树，release staging
不会包含 `docs/`。

生成命令：

```text
py mod_zhongguo_style/tools/prepare_release_localization.py audit --write-report mod_zhongguo_style/docs/release-localization-audit.json
```

## Schema v1

顶层字段必须恰好为：

```json
{
  "format_version": 1,
  "product_id": "mod_zhongguo_style",
  "result": "GREEN",
  "checks": [
    "utf8_bom",
    "header",
    "syntax",
    "key_order",
    "protected_tokens",
    "value_encoding"
  ],
  "source_files": [],
  "target_files": []
}
```

`source_files` 必须按 POSIX 仓库相对路径排序，精确覆盖 4 个权威源文件：简体中文、英文各自的 core 与 361 政策卡。
`target_files` 同样排序，精确覆盖法、德、日、韩、波、俄、西七种发布语言各自的 core 与政策卡，共 14 个文件。
每个元素只能包含：

```json
{
  "path": "mod_zhongguo_style/localization/french/zg361_l_french.yml",
  "size": 12345,
  "sha256": "64-character-lowercase-hex"
}
```

报告不含时间戳、机器路径或 API 信息，因此相同输入会产生相同字节。正式构建器会重新计算全部 18 个文件的大小和
SHA-256；缺文件、多文件、乱序、非 GREEN、检查项变化或任一翻译/源文案在审计后发生变化都会拒绝发布。普通开发构建与
`--check` 不要求该报告，以免日常简中/英文开发被发布级七语言门禁阻断。

2026-10-03 起，上述六项格式标签替代旧 `quality`、`no_english_placeholders` 和 `target_script` 合同。旧 canonical snapshot 保留历史字节，不得只改标签假冒新 audit；当前七语各缺 37 个 key 的格式 RED 见[专属范围说明](release-localization-format-policy-2026-10-03.md)，该产品正式发布前仍须修复并重新生成当前格式报告。
