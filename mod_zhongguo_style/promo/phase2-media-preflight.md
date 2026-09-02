# Phase-two media environment preflight

Run this immediately before the first real phase-two candidate build, after
updating the standalone promo-toolchain checkout to remote `main`. It verifies
the exact local production path without starting CK3 or synthesizing speech:

- the imported `xar-promo-toolchain` is version `0.2.1`, comes from an explicit
  clean checkout, and its `HEAD` equals the checkout's `origin/main`;
- `edge-tts==7.2.8` can currently list `zh-CN-XiaoxiaoNeural`;
- the Microsoft YaHei UI and Segoe UI files load with Pillow 12.3.0;
- measured Simplified-Chinese/English wrapping stays inside the 1920x1080
  subtitle safe area; and
- one disposable FFmpeg render exercises libass, libx264, yuv420p, AAC,
  48 kHz, and stereo. The temporary ASS and null-mux render are deleted. Only
  the JSON environment receipt is retained.

```powershell
$promo = "Z:\workspace\xar_promo_toolchain"
git -C $promo fetch origin
git -C $promo merge --ff-only origin/main
$env:XAR_PROMO_SOURCE = $promo
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$receipt = "Z:\ck3_mod_rewrite_process_assets\zg361\promo\media-preflight-$stamp.json"
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" `
  mod_zhongguo_style\tools\preflight_phase2_media.py `
  --output $receipt
Get-FileHash $receipt -Algorithm SHA256
```

A GREEN receipt is environment evidence only. It is not a capture, narration,
candidate video, human review, release approval, or publication claim. Every
real production session must use a new receipt path; the command refuses to
overwrite an earlier result.
