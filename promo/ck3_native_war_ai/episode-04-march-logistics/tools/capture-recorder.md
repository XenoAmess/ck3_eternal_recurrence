# Episode 04 client-area recorder

`capture_recorder.py` records the actual CK3 client area at its native pixel
resolution. It derives that rectangle from the single owned `ck3.exe` process,
its creation time, the visible foreground Win32 HWND, `GetClientRect` and
`ClientToScreen`, using a temporary physical-pixel thread DPI context. No fixed
window size, title-bar height, display scale or screen origin is assumed.

The FFmpeg input is explicitly **`gdigrab` desktop capture restricted to the
client rectangle**, via `-offset_x`, `-offset_y` and `-video_size`. It is not
direct HWND capture and is not an isolated offscreen render of the game. The
metadata records `capture_source.kind = gdigrab-desktop-client-region` and
`direct_hwnd_capture = false`. The output excludes desktop pixels outside the
client area and the window border; the unmodified full desktop preflight image
is retained separately as evidence.

The owned CK3 window must be foreground, unminimized, entirely within the
primary desktop, with even client dimensions at least 640×360. The recorder
rejects unsupported geometry rather than silently cropping or scaling. An
additional visible window from another process above CK3 in Z order may not
intersect the client rectangle. A final geometry/ownership check runs within
the existing process-creation gate, immediately before FFmpeg starts.

A separate 250 ms watcher checks the PID and creation time, HWND, foreground,
client bounds, desktop size and visible occlusions while FFmpeg runs, including
while an SDK request is waiting. A change stops FFmpeg, preserves the container
and records `RED_CAPTURE_SOURCE_CHANGED`, even if normal FFmpeg shutdown
succeeds. It also fails the bootstrap's existing recorder health check.
Sampling has a finite detection delay; it cannot prove that every recorded
frame is clean. A normal recorder terminal result still requires a media probe,
frame review and the project's review/signoff process.

`intent.json`, `process-ready.json`, `capture-guard-failure.json` (when present)
and `result.json` preserve the actual source metadata and the prepared
`machine_id`. Historical captures are not reinterpreted by this change. The
offline tests exercise geometry admission, command construction, original
desktop preservation, ownership checks at process creation, source-change
rejection and the distinction between a readable container and a clean clip.
They do not claim live Windows or CK3 acceptance.

The session supervisor owns the actual session/capacity deadline and supplies
`OwnedRecorder(..., start_admission=guard)` with a callable taking the requested
recording seconds. Start requires that callable and its explicit deadline
facts. Admission is checked before consuming the recorder attempt or creating
its workdir, then checked again within the process-creation gate immediately
before FFmpeg starts. The first facts are preserved in `intent.json`, and the
second in `deadline-admission-at-spawn.json`, `process-ready.json` and the
terminal result. A denied second check preserves the attempted workdir and
failure receipt without starting FFmpeg.

Canonical bootstrap options:

- `--recording-capacity-admission PATH SHA256` supplies the exact capacity
  receipt, or the existing `--runtime-capacity-admission PATH SHA256` may be
  reused. Its JSON must have `admitted=true`, with `machine_id`, `scene_root`,
  `run_id` and `source_head` bound to the actual run, and a timezone-aware
  `quota_review_at_utc` cutoff.
- `--recording-deadline-utc` may shorten the existing cutoffs; it cannot extend
  either the session or the capacity admission.
- `--recording-close-reserve-seconds` defaults to 120 and cannot be lower.

The canonical supervisor's guard requires time for the requested clip and a
120-second normal shutdown reserve before both the session and capacity
cutoffs. Ordinary SDK requests do not depend on recorder admission. Missing
deadline wiring blocks recording. The recorder does not infer a new deadline
from its own start time or extend an existing capacity admission.
The session timeout includes warmup; the guard preserves the time consumed
before recording as `session_elapsed_before_recording_seconds`.

Failure-receipt writes cannot bypass the owned process cleanup. If publishing
`process-ready.json` fails after FFmpeg has started, the recorder still aborts
its Job and closes every stream, even if writing `start-failure.json` also
fails. The initial exception remains the raised business error; secondary
receipt or cleanup failures are retained in `cleanup_error` and exception
notes. A proven empty Job remains recorded in memory even if its terminal
receipt cannot be written. `close()` signals the geometry watcher and joins
it with a two-second bound after releasing recorder locks; the watcher never
joins itself.
