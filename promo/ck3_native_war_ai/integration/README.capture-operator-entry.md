# Managed Episode2 capture operator

The capture process owns one `ScreenLeaseKeeper` throughout both CK3 sessions
and the explicit gameplay recorder. The runtime must provide
`require_screen_process_provider()` and both native-session callbacks. CK3,
injector and recorder creation run through the keeper's process-create gate;
the Windows Jobs retain process ownership until directly queried empty.

`record_bounded_gameplay.py record` validates the loaded checkpoint, reviewed
offline receipt, native display geometry, executable bytes and a fresh sibling
workdir. It records the immutable intent, then sends `gameplay_recorder/start`
to the capture's existing hot service. It does not start another keeper or
launch FFmpeg in its own process. Only one 600-second native desktop recorder
is admitted per capture. Explicit `status` requests collect the natural exit
and `NORMAL_TREE_EMPTY` receipt before media probing. The legacy intent,
start/end and marks files remain available to `remaining_live_step.py`.

Loss of the screen lease or capture shutdown aborts the recorder Job before
closing its stdio and stopping the keeper. Failed attempts, raw partials,
requests, responses and unsafe markers remain preserved. An encoded raw file
and successful probe do not certify clean spans or human approval.

J-d11 keeps its immutable d11 save and sidecar, GUI source block and native
binary pair. A new source HEAD requires a new no-launch attempt and byte seal.
New attempts may use the explicit C-drive capture root
`C:/Users/1/AppData/Local/ck3-capture-preparation/`; historical D-drive source
assets and seals retain their original meaning. The root screen operator
must independently obtain current Steam-offline evidence and exclusive screen
admission before the live command.
