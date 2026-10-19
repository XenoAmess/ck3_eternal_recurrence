# Driver state WAL experiment

This is **uninstalled, default-off research code**. Committing this directory does
not change the production SDK. No Game or native bridge acceptance is claimed.

`driver_state_wal_v1.py` is the prospective package module. The two patches are
complete, narrow diffs against the pinned source leaves in `SOURCE-PINS.json`:
`ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py` and
`ck3_autonomous_player/src/xar_autoplayer/native_session.py`. Before a controlled
SDK generation uses them, copy the helper to
`src/xar_autoplayer/bridge/driver_state_wal_v1.py`, rebase both patches against
that generation, run the tests, and keep the opt-in environment variable unset
until its startup and recovery contracts are reviewed. Neither patch belongs in
a running or frozen SDK tree.

The active base is a sealed v3 envelope. An old direct reader cannot extract its
pipe, checkpoint, or history and must reject it. A new reader accepts only the
bound base plus a contiguous, checksummed journal. SAVE, restore, noneligible
commands, and normal close write the original v2 full state. A closed-owner
materializer can create a v2 cold input at a new path after checking both source
hashes; it never edits the source directory. Missing, truncated, reordered,
duplicated, foreign-base, or uncommitted rows provide no action credit.

Only successful daily advances are candidates. The route-contact-horizon
literal uses its existing strict parser and requires the same result step,
one day and exactly 24 raw units, paused postcondition, no event/interaction,
and a native sentinel stopped solely at the date deadline with one tick and
zero overshoot. Early contact, event, or ambiguous clock falls back to full
state. Other gameplay policy is unchanged.

The writer hashes the base at activation or full barrier. Under its write lock,
later appends compare device, file ID, size, modification and creation times;
any mismatch rejects the hot append. Cold replay still hashes and parses the
whole base. This avoids re-reading and parsing the full base on every journal
append without using stat metadata as a cold recovery proof.

`test_portable.py` accepts `XAR_WAL_PUBLIC_REPO` or finds its containing checkout.
It copies only the two source leaves to a temporary directory, applies the
patches there, loads the real Driver and cold validator, and tests default-off,
strict route results, hot append and tamper rejection, reader rejection, SAVE,
normal close, materialization, and journal corruption. It does not contact CK3.
The actual-route microfixture records its immutable source file and SHA but
contains no machine path or process binding. The larger prior fault suite and
closed 33.5 MB benchmark remain in the external development packet.

The [2026-10-19 bounded qualification](../../../docs/ck3-native-ai/evidence/driver-wal-qualification-2026-10-19.json)
records the current helper and patch hashes against `dc4b7d56`; `SOURCE-PINS.json`
and `DELIVERY.json` retain their earlier historical identities. On
`machine_id: xenoamess-full-tower-eb9d2c1186`, the successor experiment completed
at `2026-10-19T02:37:39.210812Z`. A present journal with a missing base, or a
known journal read failure, now rejects recovery instead of returning fresh
state. All 144 synthetic history rows and field values survived replay,
materialization, strict reading, SAVE bookkeeping and normal close. JSON object
key order changed, so raw bytes did not match; the original failed assertion
was retained and the same pair was used for the remaining checks. Timing
samples were not retained and no speed improvement is claimed. This remains
default-off and was not installed into the current game SDK.
