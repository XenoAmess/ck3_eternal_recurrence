# Character interaction proposal payload source extension

Status: **static-ready, private and unwired** for CK3 `1.19.0.6`. This work did not launch CK3 and is not production-live evidence.

The DIPLO4 proposal core already defined typed semantics for eleven ordinary character interactions. Its first five actor/recipient-only rows were source-reachable, while six rows still lacked collector-backed typed payloads. This extension closes those six private sources from the finalized `CCharacterInteractionContext` that produced the preview:

| Interaction | Exact collector payload |
| --- | --- |
| `educate_child_interaction` | ward at secondary recipient; guardian at secondary actor |
| `offer_ward_interaction` | ward at secondary actor; guardian at secondary recipient |
| `offer_guardianship_interaction` | ward at secondary recipient; guardian at secondary actor |
| `grant_titles_interaction` | recipient plus the ordered full `LandedTitleID` vector owned by `CGrantTitlesOffer` |
| `grant_vassal_interaction` | transferred vassal at secondary actor; recipient is the new liege candidate |
| `ransom_interaction` | prisoner at secondary recipient plus the exact selected ransom option mask |

## Frozen native evidence

The frozen executable is `ck3.exe` `1.19.0.6`, size `95,206,008`, SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`. Static disassembly anchors are recorded and hash-checked in `character_interaction_proposal_payload_source_extension_v1_abi.json`.

The all-role context constructor at RVA `0x2C3F000` stores full signed `CharacterID` values at context offsets `0x2D8` through `0x2E8`. Selected option bytes are the vector at `0x300`, with capacity at `0x308` and count at `0x30C`; the canonical definition count at `0x2554` must agree. The special payload pointer is at `0x330`.

For grant titles, RTTI and the frozen vtable at RVA `0x4112BA8` identify `CGrantTitlesOffer`. Its ordered full `LandedTitleID` vector uses data at `+0x08`, capacity at `+0x10`, and count at `+0x14`. The factory at `0x1002B80` and ID reader at `0x24BA9E0` are frozen code anchors.

IDs are never reduced to a slot number. The low 24 bits select the object-storage slot, then the complete signed ID is compared with the object identity (`Character +0x18`, `LandedTitle +0x10`). This retains the generation byte for actor, recipient, secondary roles, intermediary, and selected titles.

## Frame and option contract

The collector returns the snapshot ID, public revision, native revision, proof epoch, and date. All five values must match the finalized paused preview. A fresh canonical definition lookup must also equal the pointer stored in the collector context. Any drift or malformed memory keeps the source unavailable.

The three education definitions author options in the order culture conversion, faith conversion, university, hook. Faith conversion remains explicitly deferred under the religion pause and returns a RED unavailable result. Ransom options use their exact seven-row authored order; a ransom payload without any selected row is invalid.

## Validation boundary

The native fixture covers every typed mapping with generation-bearing IDs, then exercises generation drift, frame proof/date drift, religious-option deferral, special-data vtable drift, selected-title generation drift, malformed options, and wrong-build rejection. Both MSVC `/Od /W4 /WX` and `/O2 /DNDEBUG /W4 /WX` pass. The Python source contract passes in normal and `-O` modes against the frozen executable and stock source hashes.

The extension is a private source seam. It is absent from shared CMake, `bridge.cpp`, public schema, and MCP; it contains no command or submit operation. A later integration owner can pair its complete payload with DIPLO4's same-frame preview stability and single-submit core, followed by CK3 live acceptance.
