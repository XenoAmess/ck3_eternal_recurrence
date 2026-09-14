# Activity planning private source adapter (1.19.0.6)

This note freezes the static boundary used by the private P0 feast planning
source adapter. It does not claim a public query, a live paused snapshot, or an
activity action.

## Exact-build evidence

- CK3 build: `1.19.0.6`
- `ck3.exe` SHA-256:
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- image base used by the RVA analysis: `0x140000000`
- `CActivityListDetailHostView` type descriptor RVA: `0x52B2438`
- primary COL / vtable RVA: `0x4722EF0` / `0x4166528`
- secondary COL / vtable RVA: `0x4722EA0` / `0x4166620`
- the constructor at `0xA90740..0xA908A1` allocates `0x270` bytes, installs
  those vtables, and initializes the current activity-type field at `+0x268`
- primary vtable slot 25 is `0x15051F0..0x150522C`; its body SHA-256 is
  `5D21CBE7EB76649F2D6F6960097A3C99031B2B0273C3C91B3B5F34A0C868CC64`
- that method reads the `CActivityType*` at `HostView+0x268`; the regular path
  calls final evaluator `0x28CFC50..0x28CFDE0` (body SHA-256
  `E3EB519FC8E66A4DAEEA705522B14CFFC73A31AB37D23C0CC7335EF952D0F948`)
- the adjacent reflected strings are `CanPlanActivity` at RVA `0x4096760` and
  `GetCanPlanActivityTooltip` at RVA `0x4096778`

The adapter therefore admits only this executable hash, re-resolves the
played-character HostView for every sample, checks its primary vtable and slot
25, reads the activity-type pointer anew, and verifies that the copied stable
definition key is `activity_feast` before requesting any planning inputs.

## Transient collector contract

The exact-build collector supplies a short-lived container token. Its rows are
plain read-only views for:

- legal location ID/key, native weight, and final selectable value;
- selected option stable keys;
- host intent, guest intent, and invite-rule stable keys;
- authoritative configured resource costs, affordability, and cooldown;
- `shown` and `can_start` final values.

`CanPlanActivity` is requested separately through the exact slot-25 entry point
and includes copied failure display key/text when false. A true result represents
failure display fields as typed `unknown/not_applicable`; missing collectors,
bad strings, oversized rows, or failed native evaluation fail the whole capture
instead of returning a field set made only of unknown values. UI predicted cost
is absent from this contract.

Each observer read performs two complete samples. Every sample re-resolves the
HostView, activity type, definition key, evaluator, and input container; reads
the container view before and after copying; releases it; and verifies the same
paused frame before and after. The two copied samples must be semantically
identical. Only fixed-capacity values survive `EndCapture`; native HostView,
activity-type, row, string, and container addresses are never retained.

## Acceptance boundary

Standalone normal and optimized MSVC `/W4 /WX` fixtures cover two different
HostView/activity-type/container identities across the two same-frame samples,
all known feast inputs, known-false failure display data, deep-copy stability,
repeat-query re-resolution, exact-build/vtable/key rejection, container drift,
semantic sample drift, frame drift, release failure, and session recovery.

Status: `static-ready private source adapter`. Shared bridge/schema/MCP wiring
and a real paused artifact remain separate work. A fixture GREEN result must not
be reported as production-live.
