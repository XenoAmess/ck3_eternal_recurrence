# H3937 local Province siege read port

The existing exact-build reader `ReadWarObjectiveProvinceState` already knows
the CK3 1.19.0.6 occupation and local siege layout. Ordinary snapshots publish
its rows only for active-war objective Provinces, subject to a shared row
budget. `query-province-local-siege-v1-<ProvinceID>` reads exactly one selected
Province independently of that objective list and budget. It uses the same
`WarObjectiveProvinceState` fields, observable flags, null serialization and
native pointer checks; it does not construct or submit a game command.

The query requires a ready, paused map and a living played character. The
bridge binds the request to the current snapshot revision, compares its
admission and completion snapshots, and the exact adapter compares two direct
Province reads. `available` requires observable occupation, fort, garrison,
besieging strength and siege presence; otherwise `partial` preserves the
unavailable fields. An unobservable siege must never be interpreted as no
active siege. This query does **not** enumerate hostile armies, establish a
route/contact horizon, or authorize date advance, movement, attack, spending
or termination.

H3937's persisted paused source report at raw date `53219928` has only
`active_context.war_ids=[16777231]` and `army_ids=[83886367]`; it contains no
Province 2610 row. The source excerpt
`SOURCE-H3937-PAUSED-WAR-SCOPE-EXCERPT-v1.json` is 5,330 bytes, SHA-256
`75DE8BF9E818FAA8614FA85EE52FF73F476D2A0C39473C951A4C0063CD35258E`,
and explicitly marks local siege/occupation `not_observed`. No value for 2610
is inferred from the older H3928 frame or binary save.

The transferred H3937 DLL is SHA-256
`A8EAC0CD5BEEDF90778C76C14679629A96EDD4F7E7B398EB035B865F776786E9`.
It does not implement this port. Any receiver use needs a newly built exact
DLL, its own SHA and ordinary rebind, and a fresh no-action receiver attempt
against the exact H3937 save/driver/sidecars. Results observed in separate
old/new DLL sessions cannot be joined as one simultaneous war scope. A formal
combined assessment must observe every required field in one qualified new
session; this patch alone does not make the war/date gate green.
