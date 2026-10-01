# Temporary Unicode clipboard text

`tools/windows_unicode_clipboard.py` is the authoritative generic owner of
`temporary_unicode_text(text: str)`. A project imports this internal context
helper; it does not expose a new MCP endpoint, arbitrary-key tool, paste action,
window navigation, Steam command or target identity.

Ownership review found an inline `pyperclip.paste/copy/finally` in
`ck3_autonomous_player/src/xar_autoplayer/opening_smoke.py`, and native
coat-of-arms clipboard operations. Neither is a reusable Python context for a
Steam console consumer. The suite keeps only its project-specific allowlist,
focus checks, paste and control-value readback.

The actual 2026-10-02 suite download attempt failed before ENTER with
`(0, 'GetClipboardData', 'No error message is available')`. Its original RED is
`_runtime/update-20261002/download-core-ack-001.json` in the suite. Its current
helper already checked `IsClipboardFormatAvailable`; that check alone did not
prevent the observed read failure. The new context skips an absent Unicode
format, and treats only this exact API/code-zero read failure as no retrievable
prior Unicode text. Other API errors propagate before replacement. This does
not establish why an advertised format was unreadable.

The context opens the clipboard, saves readable Unicode text, writes the
temporary text, then closes the clipboard before yielding. On normal return or
consumer failure it restores the original Unicode text, including an empty
Unicode string. If no readable Unicode text existed, it empties the clipboard
again. Non-text formats are outside this text-only contract, matching the
consumer's former scope. It also restores saved text if replacement fails. No
clipboard retry, keyboard operation, UI action or automatic command replay is
introduced.

```python
from windows_unicode_clipboard import temporary_unicode_text

with temporary_unicode_text(command):
    # Existing authorized consumer: focus, paste, and read back the edit value.
    readback = existing_paste_and_readback()
```

The thin consumer loads this module from a pinned authoritative main checkout;
it must preserve its existing command allowlist and require exact edit-value
readback before ENTER. Context success is not proof of paste, command execution,
download, network connectivity or Steam's offline state. `WantsOfflineMode=0`
alone does not prove an internet connection.

Seven focused tests use an injected API and never read or write the real
clipboard: absent format, Unicode/empty-text restoration, actual code-zero
failure, other-error propagation, consumer failure, replacement failure and
non-text input rejection. Run from `tools` with
`python -m unittest test_windows_unicode_clipboard`. No CK3/DLL operation or live
Steam action was performed for this package; `open_kaishek` does not apply to
this Python clipboard context.
