# R0002 physical console execution v3

V3 supersedes the three-rounds execution command in V2. Root confirmed physical
scan 0x29 opened the console with actual input caret. Root already initialized
the fixture through its player decision and observed INITIALIZE_PASS. Current
paused native date is 1066.12.24 / raw 53146728, current player 31254.

The V2 three-rounds attempt at `live-attempt-002/console-three-rounds-001/`
returned RED with its sentinel unchanged and **Enter not attempted**. The actual
console field remained blank. Its receipt, screenshots and once-only claim are
preserved. V3 uses a new claim namespace; it never repeats initialization or
opens/closes the console. The sole allowed command is `event lyd_np.9000` using
the current local player; no character-ID argument is supplied.

All action keys now reuse the existing repository physical SendInput functions
in `ck3_autonomous_player/src/xar_autoplayer/control/executor.py`:

| Action | Physical scan codes | Existing function |
| --- | --- | --- |
| Ctrl+A | left Ctrl 0x1D, A 0x1E | `_prepare_key_chord_batch` at line 165 |
| Ctrl+V | left Ctrl 0x1D, V 0x2F | same |
| Ctrl+C | left Ctrl 0x1D, C 0x2E | same |
| Enter | 0x1C | `_prepare_key_press_batch` at line 140 |

No PyAutoGUI virtual-key press/hotkey calls remain. PyAutoGUI is used only by
the existing capture/dimension observation helpers. The shared Unicode
clipboard context manager still preserves prior Unicode text. After physical
paste, the helper replaces its clipboard seed with a fresh nonce before copying
the whole text from the actual control. An unchanged nonce, unsupported copying
or any exact-text mismatch yields RED and refuses Enter. Physical SendInput ACK
counts establish dispatch only; every action records its exact sent count.

The root operator obtains a new actual standalone native snapshot receipt via
the already attached provider, confirms current player 31254 and a paused map,
then directly reviews a new raw screenshot showing the console input caret.
Replace `SNAPSHOT_JSON`, `CONSOLE_FRESH.png`, and `SHA_FRESH` with those actual
paths and exact reviewed-image digest. Both native receipt and reviewed frame
must be at most 180 seconds old.

```text
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe -B -X utf8 C:/workspace/ck3_lyd_runtime_20261004/console_input_helper_v3.py --action execute --step three-rounds --guard-profile C:/workspace/ck3_lyd_runtime_20261004/live-attempt-002/profile-attempt-001/guard-profile.json --native-snapshot-receipt SNAPSHOT_JSON --output C:/workspace/ck3_lyd_runtime_20261004/live-attempt-002/console-three-rounds-v3-001 --console-reviewed-image CONSOLE_FRESH.png --reviewed-sha256 SHA_FRESH --console-focused-reviewed
```

The helper retains existing exact process/window/thread/userdir, Steam offline,
exclusive fresh lease, native player/build/profile and English layout guards.
It requires exactly one INITIALIZE_PASS and no fixture FAIL/REJECTED before the
test. It preserves before/readback/after raw screenshots and actual copied text.
The preparing agent ran only AST/help/import checks, not a desktop action.

After successful submission, resume/observe/pause/save through existing native
capabilities. Acceptance requires three each JOIN_APPLIED/DETACH_APPLIED,
JOIN_D1/D30_PASS and DETACH_D1/D30_PASS, one THREE_ROUNDS_PASS and no fixture
failure/rejection, new engine errors or crash. Those are in-engine scripted
assertions; copied text plus Enter ACK is not proof of faith-state transitions
or UI display. The previously documented natural cooldown, main/last detach,
divergence >=100, dynamic-faith lifetime, save/reload and AI checks remain separate.
