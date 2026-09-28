#pragma once

#include "xar_bridge/realm_law_active_collection_11906.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906::private_law {

inline constexpr std::array<std::string_view, 2>
    kRealmLawRelevantFeudalGroups11906 = {
        "crown_authority", "succession_order_laws"};
inline constexpr std::size_t kRealmLawMaximumRelevantCandidates11906 = 8;
inline constexpr std::size_t kRealmLawMaximumNativeGroupCandidates11906 = 64;

enum class RealmLawCandidateCollectionFailure : std::uint8_t {
  none,
  active_collection_unavailable,
  module_base_unavailable,
  database_unavailable,
  database_groups_unavailable,
  database_group_count_invalid,
  group_unavailable,
  group_key_invalid,
  duplicate_relevant_group,
  relevant_group_missing,
  candidate_count_invalid,
  candidate_unavailable,
  candidate_group_mismatch,
  candidate_key_invalid,
  active_law_ambiguous,
  candidate_observer_failed,
  relevant_candidate_missing,
};

struct RealmLawCandidateCollectionRow11906 {
  RealmLawActiveKey key{};
  bool active = false;
};

struct RealmLawRelevantGroup11906 {
  RealmLawActiveKey key{};
  bool active_found = false;
  RealmLawActiveKey active_law_key{};
  std::uint32_t candidate_count = 0;
  std::array<RealmLawCandidateCollectionRow11906,
             kRealmLawMaximumRelevantCandidates11906> candidates{};
};

struct RealmLawCandidateCollection11906 {
  RealmLawCandidateCollectionFailure failure =
      RealmLawCandidateCollectionFailure::active_collection_unavailable;
  RealmLawActiveCollectionFailure active_failure =
      RealmLawActiveCollectionFailure::none;
  std::array<RealmLawRelevantGroup11906, 2> groups{};
};

std::string_view RealmLawCandidateCollectionFailureName(
    RealmLawCandidateCollectionFailure failure) noexcept;

// Invoked synchronously while the native CLaw* is known. The address must
// remain inside this paused application-main callback; it is not part of the
// value-only candidate collection or any durable snapshot.
using ObserveRealmLawCandidate11906 = bool (*)(
    void *context, std::size_t group_index, std::size_t candidate_index,
    std::uintptr_t native_law, const RealmLawCandidateCollectionRow11906 &row)
    noexcept;

bool ReadRealmLawCandidateCollectionWithObserver11906(
    const RealmLawActiveCollectionAccess &access, std::uintptr_t module_base,
    void *observer_context, ObserveRealmLawCandidate11906 observer,
    RealmLawCandidateCollection11906 &output) noexcept;

// Private paused-frame candidate enumeration for H3911's feudal governance
// decision. It reports native keys and enacted membership only. It does not
// evaluate can-have, can-pass, CanEnact, blocked reasons or currency costs.
bool ReadRealmLawCandidateCollection11906(
    const RealmLawActiveCollectionAccess &access, std::uintptr_t module_base,
    RealmLawCandidateCollection11906 &output) noexcept;

} // namespace xar::ck3_11906::private_law
