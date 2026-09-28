#include "xar_bridge/realm_law_candidate_collection_11906.hpp"

#include <cstring>

namespace xar::ck3_11906::private_law {
namespace {

constexpr std::uintptr_t kLawDatabaseSingletonRva = 0x57C0508;
constexpr std::uintptr_t kDatabaseGroupArrayOffset = 0x68;
constexpr std::uintptr_t kDatabaseGroupCountOffset = 0x74;
constexpr std::uintptr_t kGroupKeyOffset = 0x18;
constexpr std::uintptr_t kGroupCandidateArrayOffset = 0x50;
constexpr std::uintptr_t kGroupCandidateCountOffset = 0x5C;
constexpr std::uintptr_t kLawKeyOffset = 0x18;
constexpr std::uintptr_t kLawGroupPointerOffset = 0x38;

template <typename T>
bool Read(const RealmLawActiveCollectionAccess &access,
          std::uintptr_t address, T &output) noexcept {
  return access.read_memory(access.context, address, &output, sizeof(output));
}

std::string_view KeyText(const RealmLawActiveKey &key) noexcept {
  return {key.bytes.data(), key.size};
}

bool IsActiveKey(const RealmLawActiveCollection &active,
                 const RealmLawActiveKey &key) noexcept {
  for (std::uint32_t i = 0; i < active.count; ++i) {
    if (active.keys[i] == key) return true;
  }
  return false;
}

bool ReadGroup(const RealmLawActiveCollectionAccess &access,
               std::uintptr_t group_address,
               const RealmLawActiveCollection &active,
               std::size_t group_index, void *observer_context,
               ObserveRealmLawCandidate11906 observer,
               RealmLawRelevantGroup11906 &group,
               RealmLawCandidateCollectionFailure &failure) noexcept {
  if (!ReadRealmLawNativeKey11906(access, group_address + kGroupKeyOffset,
                                 group.key)) {
    failure = RealmLawCandidateCollectionFailure::group_key_invalid;
    return false;
  }
  std::uintptr_t candidate_slots = 0;
  std::int32_t candidate_count = -1;
  if (!Read(access, group_address + kGroupCandidateArrayOffset,
            candidate_slots) ||
      !Read(access, group_address + kGroupCandidateCountOffset,
            candidate_count)) {
    failure = RealmLawCandidateCollectionFailure::group_unavailable;
    return false;
  }
  if (candidate_count < 1 ||
      candidate_count >
          static_cast<std::int32_t>(kRealmLawMaximumRelevantCandidates11906) ||
      candidate_slots == 0) {
    failure = RealmLawCandidateCollectionFailure::candidate_count_invalid;
    return false;
  }
  for (std::int32_t i = 0; i < candidate_count; ++i) {
    std::uintptr_t law_address = 0;
    if (!Read(access, candidate_slots + static_cast<std::uintptr_t>(i) * 8,
              law_address) ||
        law_address == 0) {
      failure = RealmLawCandidateCollectionFailure::candidate_unavailable;
      return false;
    }
    std::uintptr_t law_group = 0;
    if (!Read(access, law_address + kLawGroupPointerOffset, law_group) ||
        law_group != group_address) {
      failure = RealmLawCandidateCollectionFailure::candidate_group_mismatch;
      return false;
    }
    auto &candidate = group.candidates[static_cast<std::size_t>(i)];
    if (!ReadRealmLawNativeKey11906(access, law_address + kLawKeyOffset,
                                   candidate.key)) {
      failure = RealmLawCandidateCollectionFailure::candidate_key_invalid;
      return false;
    }
    candidate.active = IsActiveKey(active, candidate.key);
    if (candidate.active) {
      if (group.active_found) {
        failure = RealmLawCandidateCollectionFailure::active_law_ambiguous;
        return false;
      }
      group.active_found = true;
      group.active_law_key = candidate.key;
    }
    if (observer != nullptr &&
        !observer(observer_context, group_index, static_cast<std::size_t>(i),
                  law_address, candidate)) {
      failure = RealmLawCandidateCollectionFailure::candidate_observer_failed;
      return false;
    }
  }
  group.candidate_count = static_cast<std::uint32_t>(candidate_count);
  return true;
}

} // namespace

bool ReadRealmLawCandidateCollectionWithObserver11906(
    const RealmLawActiveCollectionAccess &access, std::uintptr_t module_base,
    void *observer_context, ObserveRealmLawCandidate11906 observer,
    RealmLawCandidateCollection11906 &output) noexcept {
  output = {};
  RealmLawActiveCollection active{};
  if (!ReadRealmLawActiveCollection11906(access, active)) {
    output.failure =
        RealmLawCandidateCollectionFailure::active_collection_unavailable;
    return false;
  }
  if (module_base == 0) {
    output.failure = RealmLawCandidateCollectionFailure::module_base_unavailable;
    return false;
  }
  std::uintptr_t database = 0;
  if (!Read(access, module_base + kLawDatabaseSingletonRva, database) ||
      database == 0) {
    output.failure = RealmLawCandidateCollectionFailure::database_unavailable;
    return false;
  }
  std::uintptr_t group_slots = 0;
  std::int32_t group_count = -1;
  if (!Read(access, database + kDatabaseGroupArrayOffset, group_slots) ||
      !Read(access, database + kDatabaseGroupCountOffset, group_count)) {
    output.failure =
        RealmLawCandidateCollectionFailure::database_groups_unavailable;
    return false;
  }
  if (group_count < 1 || group_count > 1024 || group_slots == 0) {
    output.failure =
        RealmLawCandidateCollectionFailure::database_group_count_invalid;
    return false;
  }
  std::array<bool, 2> found{};
  for (std::int32_t i = 0; i < group_count; ++i) {
    std::uintptr_t group_address = 0;
    if (!Read(access, group_slots + static_cast<std::uintptr_t>(i) * 8,
              group_address) ||
        group_address == 0) {
      output.failure = RealmLawCandidateCollectionFailure::group_unavailable;
      return false;
    }
    RealmLawActiveKey key{};
    if (!ReadRealmLawNativeKey11906(access, group_address + kGroupKeyOffset,
                                   key)) {
      output.failure = RealmLawCandidateCollectionFailure::group_key_invalid;
      return false;
    }
    for (std::size_t relevant = 0;
         relevant < kRealmLawRelevantFeudalGroups11906.size(); ++relevant) {
      if (KeyText(key) != kRealmLawRelevantFeudalGroups11906[relevant]) continue;
      if (found[relevant]) {
        output.failure =
            RealmLawCandidateCollectionFailure::duplicate_relevant_group;
        return false;
      }
      found[relevant] = true;
      if (!ReadGroup(access, group_address, active, relevant,
                     observer_context, observer, output.groups[relevant],
                     output.failure)) {
        return false;
      }
    }
  }
  if (!found[0] || !found[1]) {
    output.failure = RealmLawCandidateCollectionFailure::relevant_group_missing;
    return false;
  }
  output.failure = RealmLawCandidateCollectionFailure::none;
  return true;
}

bool ReadRealmLawCandidateCollection11906(
    const RealmLawActiveCollectionAccess &access, std::uintptr_t module_base,
    RealmLawCandidateCollection11906 &output) noexcept {
  return ReadRealmLawCandidateCollectionWithObserver11906(
      access, module_base, nullptr, nullptr, output);
}

} // namespace xar::ck3_11906::private_law
