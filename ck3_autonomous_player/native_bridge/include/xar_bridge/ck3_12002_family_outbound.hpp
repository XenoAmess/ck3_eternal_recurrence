#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/marriage_proposal_resolution_journal_v1.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kFamilyOutboundPendingStorageSlotRva = 0x5D1EC80;
inline constexpr std::uintptr_t kFamilyOutboundInteractionDatabaseSlotRva = 0x5C67538;
inline constexpr std::uintptr_t kFamilyOutboundComponentAliveRva = 0x1731C10;
inline constexpr std::uintptr_t kFamilyOutboundPendingVtableRva = 0x4759240;
inline constexpr std::uintptr_t kFamilyOutboundMarriageSpecialVtableRva = 0x44B9928;
inline constexpr std::size_t kFamilyOutboundArrangeDefinitionOffset = 0xF30;
inline constexpr std::size_t kFamilyOutboundPendingIdentityOffset = 0x10;
inline constexpr std::size_t kFamilyOutboundPendingDefinitionOffset = 0x18;
inline constexpr std::size_t kFamilyOutboundPendingActorOffset = 0x2F0;
inline constexpr std::size_t kFamilyOutboundPendingRecipientOffset = 0x2F4;
inline constexpr std::size_t kFamilyOutboundPendingSubjectOffset = 0x2F8;
inline constexpr std::size_t kFamilyOutboundPendingCandidateOffset = 0x2FC;
inline constexpr std::size_t kFamilyOutboundPendingIntermediaryOffset = 0x300;
inline constexpr std::size_t kFamilyOutboundPendingSpecialOffset = 0x348;
inline constexpr std::size_t kFamilyOutboundPendingAgeOffset = 0x5B8;
inline constexpr std::size_t kFamilyOutboundPendingCutoffOffset = 0x5BC;
inline constexpr std::size_t kFamilyOutboundPendingRouteOffset = 0x5C0;

struct FamilyOutboundBindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  void **pending_storage_slot = nullptr;
  void **interaction_database_slot = nullptr;
  bridge::MarriagePendingComponentAliveV1 component_alive = nullptr;
  std::uintptr_t pending_vtable = 0;
  std::uintptr_t marriage_special_vtable = 0;
};

// No hook/journal installation is required for this read-only cold snapshot.
FamilyOutboundBindings BindFamilyOutboundImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Same wire value as the previous version. A completed storage scan with no
// matching active native object is absent; absence cannot classify refusal,
// expiration or another terminal cause. This never consumes a command ACK.
bool ReadMarriageOutboundPendingSnapshotV1(
    const FamilyOutboundBindings &, std::int32_t actor_character_id,
    std::int32_t recipient_character_id, std::int32_t subject_character_id,
    std::int32_t candidate_character_id,
    bridge::MarriageOutboundPendingSnapshotV1 &output) noexcept;

// Shared production scanner exercised by fixture-owned slots and native gate.
bool InspectFamilyOutboundPendingSlotsV1(
    const FamilyOutboundBindings &, const void *slots, std::int32_t capacity,
    const bridge::MarriageProposalResolutionIdentityV1 &identity,
    bridge::MarriageOutboundPendingSnapshotV1 &output) noexcept;

} // namespace xar::ck3_12002
