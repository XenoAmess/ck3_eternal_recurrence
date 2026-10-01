#pragma once

#include "xar_bridge/marriage_candidate_alliance_projection_v1.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kFamilyProjectionPairWrapperRva = 0x2505570;
inline constexpr std::uintptr_t kFamilyProjectionPairGeneratorRva = 0x2C7C4A0;
inline constexpr std::uintptr_t kFamilyProjectionOwnerVtableRva = 0x454E6E8;
inline constexpr std::uintptr_t kFamilyProjectionReadOptionRva = 0x3078880;
inline constexpr std::uintptr_t kFamilyProjectionSetOptionRva = 0x30788E0;
inline constexpr std::uintptr_t kFamilyProjectionMatrilinealSlotRva = 0x5D4BDBC;
inline constexpr std::uintptr_t kFamilyProjectionIsAlliedRva = 0x2911DF0;
inline constexpr std::size_t kFamilyProjectionRealmDataOffset = 0x1C0;

// The output structs remain wire-compatible with FAMILY38/FAMILY48. No
// 1.19 native function or context layout is admitted by this provider.
struct FamilyProjectionBindings {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  void *memory_context = nullptr;
  bridge::MarriageSourceAdapterMemoryReadV1 read_memory = nullptr;
  bridge::ProjectMarriageCandidateAlliancePairsV1 project_pairs = nullptr;
  bridge::ReadMarriageCandidateBooleanOptionV1 read_boolean_option = nullptr;
  bridge::SetMarriageCandidateBooleanOptionV1 set_boolean_option = nullptr;
  bridge::ReadMarriageCandidateIsAlliedV1 is_allied = nullptr;
  std::uintptr_t matrilineal_option_id_slot = 0;
  std::uintptr_t native_owner_vtable = 0;
};

FamilyProjectionBindings BindFamilyProjectionImage(
    std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

// Uses the native stock pair producer also consumed by the actual accepted
// marriage effect. The caller supplies a disposable, finalized six-role
// context and independently evaluated final legality on the paused thread.
bridge::MarriageCandidateAllianceProjectionFailureV1
ReadFamilyAllianceProjectionV1(
    const FamilyProjectionBindings &, const void *finalized_context,
    std::uint32_t actor_character_id, std::uint32_t recipient_character_id,
    std::uint32_t subject_character_id, std::uint32_t candidate_character_id,
    bridge::MarriageCandidateAllianceProjectionV1 &) noexcept;

// Stock option predicate plus setter on a disposable context, with readback.
// This never submits an interaction or changes a world relationship.
bool SelectFamilyMatrilinealOptionV1(
    const FamilyProjectionBindings &, void *disposable_context) noexcept;

} // namespace xar::ck3_12002
