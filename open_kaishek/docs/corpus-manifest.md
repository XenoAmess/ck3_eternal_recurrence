# Phase 0 corpus manifest

`corpus-manifest.json` is the reproducible Phase 0 inventory for the
`ck3-1.19.0.6/mod_zhongguo_style` profile. It stores only relative paths,
byte counts, SHA-256 hashes, and a lightweight syntax census; CK3/mod source
contents are never copied into the project.

From the repository root:

```powershell
& tools/.venv/Scripts/python.exe open_kaishek/tools/generate_corpus_manifest.py `
  --root mod_zhongguo_style --output open_kaishek/docs/corpus-manifest.json
```

The inventory includes all `.txt` and `.gui` files, sorted by POSIX relative
path. Each entry records `sha256`, size, line/comment counts, BOM presence,
construct counts, and preliminary assignment/block frequencies. Frequencies
are case-folded identifier counts after line-comment removal; they are useful
for parser-spike sampling only, not a semantic opcode registry. Profile
validation remains authoritative for supported semantics.

Regenerate and review path/hash diffs whenever corpus bytes change, and record
the resulting manifest hash in later Phase 0/1 test artifacts.
