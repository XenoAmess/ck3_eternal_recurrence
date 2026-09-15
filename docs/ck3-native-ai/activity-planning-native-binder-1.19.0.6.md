# Activity planning native binder (1.19.0.6)

This note freezes the private native binding beneath
`activity_planning_snapshot_v1_source_adapter`. It covers the P0 feast
planning observation only. It does not expose a public schema or MCP method,
perform an activity action, or claim a live paused capture.

## Exact-build binding

- CK3 build: `1.19.0.6`
- `ck3.exe` SHA-256:
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- PE image base: `0x140000000`
- RTTI dynamic cast: `0x3E631F4`; idler source/target type descriptors:
  `0x501EF28` / `0x501EF50`
- global interface root: `0x570F7B8`; root idler `+0x10`; graphics-idler
  handler `+0x88`
- `CIngameInterfaceIdlerGfx` vtable: `0x40B1D30`; handler vtable:
  `0x40AF630`
- handler activity-detail owner slot: `+0x3D8`
- `CActivityListDetailHostView` primary/secondary vtables:
  `0x4166528` / `0x4166620`; secondary vtable field `+0x10`
- HostView handler round trip `+0xD0`, bound owner ID `+0x100`, and current
  `CActivityType*` `+0x268`
- played-character ID global: `0x4FE7EE0`; character-storage/fallback slots:
  `0x570C130` / `0x570C138`; storage slots `+0x20`, capacity `+0x2C`, slot
  stride `0x10`, object `+0x08`, and character full ID `+0x18`
- `CActivityType` primary vtable: `0x440E308`; stable MSVC string `+0x18`
- HostView primary vtable slot 25: final `CanPlanActivity` at `0x15051F0`

Configuration checks the frozen instruction prefixes at the RTTI cast,
interface-handler install, idler handler owner, HostView constructor, activity
type setter, owner setter, and final `CanPlanActivity`. It also checks the
idler, handler, both HostView, activity-type, and slot-25 vtable targets. A bad
executable hash, prefix, slot, or required callback prevents configuration.

## Fresh owner and type resolution

Every operation starts again at the global interface root. The binder RTTI
casts the current idler, reads the current handler and its activity HostView,
then requires both HostView vtables and the `HostView+0xD0` handler round trip.
The bound ID at `+0x100`, played-character global, and character-storage object
must all resolve to the requested full character ID. The current activity type
must carry the exact `CActivityType` vtable and copy the stable definition key
`activity_feast` from either the small-string or heap-string layout.

Resolved handler, HostView, activity type, native strings, and character
objects are operation-local. The binder state retains only callbacks, fixed
copied values, a paused request whose key points into binder-owned storage, and
a monotonic non-pointer container token. A valid replacement HostView or type
can therefore be observed by the next resolution without reusing an old
address.

## Native semantic operation contract

The final evaluator wrapper receives the verified slot-25 address plus the
fresh HostView and activity type. It must attest that the HostView final
evaluator completed. A true result has typed `unknown/not_applicable` failure
display fields; a false result must copy both failure key and display text.

The required private semantic operation materializes a pointer-free sample in
the same paused transaction. Successful samples must provide:

- a complete native legal-location collection with stable IDs/keys, native
  weights, and final selectable flags;
- complete native selected option keys, host/guest intent keys, and invite
  rule key;
- complete authoritative configured costs, affordability, cooldown state and
  remaining days; UI predicted cost is rejected;
- final `shown` and `can_start` values;
- the exact frame, owner ID, and `activity_feast` definition key.

The callback is mandatory: an absent collector cannot configure the binder,
and incomplete or unknown-only provenance remains RED. This seam lets the
native operation own its calling convention and temporary CK3 containers
without exporting them through the Activity3 interface.

Opening a source container re-resolves the identity and takes the first fixed
semantic sample. Each Activity3 container read independently re-resolves and
resamples, then compares every P0 value with that first copy. Activity3 reads
the projected container twice per sample and compares two complete samples.
Frame, owner, activity key, provenance, row, configuration, cost, or boolean
drift fails closed. Release erases all fixed buffers and projections while
preserving any preceding RED failure reason.

## Static acceptance and live boundary

The standalone fixture builds the Activity2 observer, Activity3 source
adapter, and this binder together. MSVC normal `/Od /RTC1 /W4 /WX` and
optimized `/O2 /DNDEBUG /W4 /WX` runs are GREEN. Coverage includes exact image
and vtable admission, required native operations, global owner/storage round
trips, small and heap definition strings, all-known P0 semantics, typed final
failure data, replacement native identities, semantic and frame drift,
container token lifecycle, buffer erasure, deep-copy stability, and retained
RED failures.

Status: `static-ready private native binder`. ACTIVITY5 now composes this binder
through an activity-owned application-main glue, documented in
`activity-planning-application-glue-1.19.0.6.md`. Caller-supplied exact final
evaluator/semantic operations and a private application-main invocation entry
still precede the single-owner paused capture. No production wiring or live
claim follows from the static glue.
