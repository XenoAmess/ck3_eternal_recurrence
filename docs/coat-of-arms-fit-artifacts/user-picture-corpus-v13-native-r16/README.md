# user-picture-corpus-v13-native-r16

Status: **navigation RED; no picture case executed**. This is preserved as a
failed predecessor of `user-picture-corpus-v13-native-r17`, not as native image
evidence.

The run used repository commit `fc27c72c`, Steam Offline Mode, and the managed
structured MCP path only. It reached `main_menu`, invoked New Game, and proved
the `bookmarks` route. The `prepare_custom_ruler` composite then acknowledged
the native selection action, but the lobby tree predicate did not become ready
before its bounded deadline. CK3's log independently records bookmark world
generation from 10:29:08 through 10:29:30, so this was a frontend transition
race rather than an image parser, payload, or renderer failure.

The report contains zero picture cases and therefore supports no browser/CK3
pixel conclusion. Cleanup is GREEN: the CK3 process tree and watchdog both
reached zero and the shared locks were released. The ignored raw report is
121,589 bytes, SHA-256
`AC3B463696FA240BAE3ADE162953593EB976AD55D71D5FF09BD520628DD5E6DC`.

The immediately following independent r17 run used the same source commit,
binary hashes, corpus and MCP contract, completed all seven cases, and is the
superseding evidence.

