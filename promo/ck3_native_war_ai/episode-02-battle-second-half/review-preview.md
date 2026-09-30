# Episode 2 narrated review preview

`review_preview.py` is a separate, pending review compositor for existing media.
It creates an actual single MP4 with six existing EdgeTTS chapters, aligned
Chinese/English ASS, nine current calculation cards, and candidate gameplay.
It never admits a production reel or writes human signoff.

The first run is external on C: at
`C:/Users/1/AppData/Local/ck3-review-render/episode02-20260930-a01`.
The selected main venv is explicitly
`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`.
Preparation checks the latest formal wheel release, retains version/help output,
starts a native run, and freezes narration and card sources. Every FFmpeg call
retains argv, stdout, stderr, exit code, and elapsed time. All previous attempts,
including failed filters and the superseded first assembled preview, are kept.

The final timeline has 1365.552 seconds of unchanged narration, 182 seconds of
card reading, and twelve seconds of chapter transitions: 1559.552 seconds.
Card changes follow the narration's example boundaries. Historical knight
examples remain visibly historical; current interface shots are labeled as
illustrations. Missing shots are briefly marked `此处待补拍`.

Raw windows keep their source timestamps. Static illustration frames are
30 fps; the resulting preview can be variable frame rate where source frames
were lost. No raw loops, tail clones, or production clean-span claim are used.
Subtitles are generated independently from provider sentence boundaries and
explicit English semantic mappings, with the full source text retained.

The project config is review intent only. The production project and its reel,
capture, human raw review, and final signoff gates remain separate.
The viewer should review the story, narration, subtitles, and editing rhythm.
An automatic decode/probe/frame check cannot approve the film on their behalf.
