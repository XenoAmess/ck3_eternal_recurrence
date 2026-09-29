# H3937 phase-0 paused war scope: disabled native observation candidate

Status: **static candidate only; CK3 launch, date, movement, attack and spending RED**.
The CLI `native-observe-h3937-paused-war-scope-v1` has a hard false gate before
environment access, state preparation or process launch. It does not change the
two hard false gates in the separate H3937 route-contact candidate.

The fixed WAR source response `SOURCE-H3937-PAUSED-WAR-SCOPE-EXCERPT-v1.json`
(5,330 bytes; SHA-256
`75DE8BF9E818FAA8614FA85EE52FF73F476D2A0C39473C951A4C0063CD35258E`)
reports `not_observed`: the existing R0357 final paused report has only active
War/Army IDs. Earlier H3928 positions cannot be substituted for H3937.

## Frozen input and output contract

The producer uses the independently received H3937 save
`92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6`,
raw driver `2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722`,
Release DLL `A8EAC0CD5BEEDF90778C76C14679629A96EDD4F7E7B398EB035B865F776786E9`,
injector `8C8277EC27602C35A3868E17DD60A954151E13E38DCA1456B6F3B34D60EB3544`
and pending child sidecar
`798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7`.
It requires a **new** official raw-to-prepared rebind receipt at the actual state,
profile, save and driver paths, a target environment SHA, exact actor 29829,
episode `native-29829-2bc2d599f7f9`, save date raw 53219928 and history index
3937. The source machine's historical prepared receipt is rejected.

Once a separately reviewed change opens the producer gate, a single managed
native session would cold load that save, wait for paused readiness, and take
two snapshots with **zero gameplay/query steps**. The entry gate binds the
single active War 16777231 and controllable Army 83886367 at province 2610;
it does not require any inherited hostile IDs, positions or routes. The
projection demands unique, typed current positions and complete published
route arrays for every listed enemy and player army. It records both the full
published enemy list and the dynamically selected nonretreating query set.
It fails closed above 64 enemies, 64 combined allies/player rows, or 4,096
combined route entries so the receipt stays bounded.
Revision, snapshot ID, date, episode and connection generation must remain
identical; no command may append to history. Changed army rows, assets, or
unproven session cleanup make the report RED. Reports include a bounded scope
projection and `action_authorized=false`, `date_advance_authorized=false`.

`GREEN_READ_ONLY_ROSTER` would mean the **native-published observable** roster
was read consistently. The native bridge silently returns an empty army list
on invalid storage bindings/capacity and does not publish an independent
physical-army completeness bit; the candidate therefore requires an exact war,
own army and nonempty enemy list, and still reports
`complete_physical_army_inventory_proven=false`. The route-contact mailbox
later rescans its native snapshot and refuses a hostile-ID set mismatch, but
that does not prove no unobservable army exists. The current `ReadUnitRoute`
publishes an empty route both for a valid zero-length route and several read
failures, so the report also sets `route_read_completeness_proven=false`.
Per-army valid-empty versus failed-read status is a minimal native ABI gap for
full route proof. Province 2610 occupation is
`not_observed` unless an explicit same-frame native province read is added;
the current war snapshot only carries objective province states. Neither
roster observation nor a later route-contact result supplies one-day or
seven-day date credit on its own.

## Offline diagnostic, with separate evidence status

The receiver verified the exact binary save hash above and the local Rakaly
0.8.19 executable SHA-256
`E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D`.
An offline melt was preserved at
`D:\ck3-research-artifacts\war-h3937-save-offline-001\h3937-melted.ck3`
(124,431,436 bytes; SHA-256
`2ADBC0B824C1DD9656CC469DEA40A72565F04326DA05B1ED964E890A4978E909`).
It records War 16777231 attackers 30097/35357 and defender 29829; public
units 50331920 and 83886484 at 2629 and 83886367 at 2610, each with no
saved `path` field. This narrows the source hypothesis but is **not** a native
paused snapshot, route timeline or future-contact proof. The producer admits
any valid same-frame observed hostile roster rather than pinning these values.

## Future controlled use

No command in this document authorizes launch. Before a separate run, the
owner must freeze the exact reviewed checkout, fresh Steam-offline screen and
single-instance ownership evidence, create a new official H3937 prepared state
with `rebind-ordinary-seed-v1`, and pass
`native-one-generation-preflight` against that exact prepared driver. Only a
new reviewed enablement commit can make the CLI runnable. The native CLI
requires `--cold-start-checkpoint` and a monotonic `--ownership-round-id`.
Any phase-0 report and its bounded same-frame roster projection must be
checked with the cleanup receipt before designing a separate route-contact
query. The existing R0357 report does not expose the native
`pending_character_interaction` modal field; the phase-0 gate requires it to
be explicitly observed as null. A different live value fails closed pending
fresh semantic review, independently of the outbound child proposal sidecar.
