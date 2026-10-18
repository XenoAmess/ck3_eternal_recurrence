# Exact 1.20.0.4 Rite creation controller candidate

`machine_id: 4-8e1c2f1861`. Root integrated this source on
`2026-10-18T07:20:09Z`; it has not yet been built, registered or live-qualified.
The source delivery is `episode01/revision-v5-20261018/mcp/native-entry/`
under the external production root. `NATIVE-DELIVERY-a02.json` binds all 14
files and the unchanged patch SHA-256
`2f2e209b8c44e5b1011c83d498837a099d6bd37ce1873d688d1649f2452fb232`.
The original a01 delivery confused two physical CRLF candidate hashes with
their LF patch output hashes; Root rejected it before writing the checkout.
The successor freezes distinct LF views and verifies both byte scopes. This
packaging correction does not requalify native behavior.

The finite request and result contract is in
`include/xar_bridge/rite_creation_actions12004.hpp`. The proposed private step is
`player-rite-creation-action-v1`, domain `player_rite_creation_action_v1`, result
leaf `rite_creation_action`, schema `ck3_12004_rite_creation_action_v1`. It does
not accept a player override, native pointer, arbitrary decision key or callback.
The actual player and full-generation source Rite come from the existing exact
.4 core/context reader. Expected outcome is an assertion on the native branch.

The source installs real original controller calls for view 3C through the typed
Rite reference Any, materialization and selection of actual parent-owned rows,
and the five original name setters. Selection retains native CanPick plus
knowledge/prophet gates, complete source IDs, row identity and post-readback.
Names use an explicit 32-byte borrowed native CUTF8String; this is never a cast
of std::string and is never passed to a native destructor. Inputs retain stock
30/240 character limits, valid UTF-8 and NUL rejection. Controller callbacks have
void contracts; actual readback determines a changed selection or name.

Opening requires the original FaithWindow current source and one of the fixed
original buttons `edit_rite`, `create_rite`, `create_rite_puppet`, including its
effective ancestor visibility/enabled state. Original FaithWindow predicates
14C5B40/14C5B90 are separate from full draft CanCreate/CanEdit. The provider must
adapt the existing named-GUI observer into Admission; no arbitrary GUI path is
accepted over the protocol.

Original prepare callbacks are 14F5130/Create and 14F49C0/Edit. They open a
confirmation modal and do not queue a gameplay command. The actual popup manager
C45DF0 owns a vector of unique_ptr<GameDialog> at +18/count+24. The candidate
enumerates that bounded vector, selects a unique exact Create/Edit type with
+130 matching the current window and the actual visible basic confirmation
root, and reads its closed byte and full Can. It never chooses the queue head.
Modal +78 is a lifecycle observation; its equality to the global owner is not
asserted. Generic GUI CanAccept virtual+40 returns true and cannot replace
the modal's full Can at +38 or window CanCreate/CanEdit. C46400 is an update
with cancellation effects and is never called as a reader.

Original Confirm C46380 calls Accept virtual+48 and then closes the modal.
Calling Accept alone omits original behavior. Create/Edit Accept uses the
borrowed current window, then constructs a command from current window+8E8.
The modal does not hold an immutable draft copy. Original command queue flags
are 14 decimal (0x0E); this candidate never calls the command queue directly.

The original command serialization chain establishes the payload boundary:
CCommand envelope 37EB3A0 calls virtual+80; Create 29A3120 writes actor+20,
Edit 29A2AC0 writes source Rite+20 and actor+24, then both serialize draft+28.
SFaithTemplateData wrapper 3F7E2B0 reaches serializer 243B710, including its
embedded core at +240. The omitted editor/cache fields are not automatically
requirements for the command's semantic identity. The original 37F2060 helper
creates its own original text writer and memory stream and returns an owned
CString. The candidate uses original Create29A98D0 / Edit29A9930 factories,
destroys the default draft, then placement-copies the actual draft through
29A1EF0. It performs the original Accept caller's finalization on that private
clone: actual ordered selected definitions, flags1039/103A, source Faith
text/status and religion-type vectors are copied through original helpers
before recomputation. Two original command texts must match byte for byte.
The original CString and command destructors must finish before proof is granted.
No command queue, original gameplay writer, UI or game-world write is used for
preview. Native helpers retain their original diagnostic/allocation effects.

The native SHA covers that text plus typed actual actor/source/outcome, quote,
full Can, selected input keys/flags and modal stage. Raw object bytes, pointers,
allocators and partial DTOs are not substitutes for original command input.
Confirm requires a fresh post-modal preview. A temporary copy/cleanup failure
keeps proof unavailable; a partially constructed draft is never fully destroyed.

The source candidate includes a narrow normal dispatcher/mailbox case,
default-off private option, finite JSON parser/formatter and existing named-GUI
adapter, paired with the parent Python durable once module. The build option is
`XAR_ENABLE_RITE_CREATION_ACTIONS12004=1`. Reuse the existing
`xar_ck3_12002_runtime` .4 religion bindings and `xar_bridge_protocol` rather than
a new agent or runner. The existing .4 reform context/choices/costs/eligibility
providers must be enabled. A future request fixture source is supplied under
`tests/`; it has not been compiled or executed in this V5 round.

Native output is an ACK with verification_pending. After a confirmed command,
read current player Faith/Rite full references and the actual new/edit target,
names, selected core Tenets/Doctrines, piety and original draft/modal lifecycle
independently. No callback return means a new Faith/Rite was created. Unknown
writer outcomes retain the same durable action identity and must not be retried.
