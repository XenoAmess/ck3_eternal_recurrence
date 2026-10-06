#include "xar_bridge/realm_law_12004_native.hpp"

#include <array>
#include <cstring>

// Value algorithms copied from the accepted law query. Actual .4 collection
// operands and final instruction spans are closed in the shared minimal20 map.
// The four actual policy enum contents are byte-equal at mapped parser targets.
// All native admission below uses the actual .4 SHA from the Root-owned Core
// header. Source closure does not confer build or paused-runtime qualification.

namespace xar::ck3_12004::private_law {
using ck3_12002::private_law::RealmLawActiveCollectionAccess;
using ck3_12002::private_law::RealmLawActiveKey;
using ck3_12002::private_law::RealmLawActiveCollection;
using ck3_12002::private_law::RealmLawActiveCollectionFailure;
using ck3_12002::private_law::kRealmLawActiveCollectionKeyCapacity;
using ck3_12002::private_law::kRealmLawActiveCollectionMaximumLaws;
using ck3_12002::private_law::ObserveRealmLawCandidate11906;
using ck3_12002::private_law::RealmLawRelevantGroup11906;
using ck3_12002::private_law::RealmLawCandidateCollectionFailure;
using ck3_12002::private_law::RealmLawCandidateCollection11906;
using ck3_12002::private_law::RealmLawFinalTerms12002Operations;
using ck3_12002::private_law::RealmLawFinalTerms12002Input;
using ck3_12002::private_law::RealmLawFinalTerms12002Result;
using ck3_12002::private_law::RealmLawFinalTerms12002Status;
namespace {

constexpr std::uintptr_t kCharacterLawContextOffset = kCharacterLawContextOffset12004;
constexpr std::uintptr_t kLawCollectionOffset = kLawCollectionOffset12004;
constexpr std::uintptr_t kLawKeyOffset = kLawNativeKeyOffset12004;
constexpr std::size_t kMsvcStringInlineCapacity = 15;

template <typename T>
bool Read(const RealmLawActiveCollectionAccess &access,
          std::uintptr_t address, T &output) noexcept {
  return access.read_memory(access.context, address, &output, sizeof(output));
}

bool CopyKey(const RealmLawActiveCollectionAccess &access,
             std::uintptr_t key_storage_address,
             RealmLawActiveKey &output) noexcept {
  std::array<std::byte, 32> storage{};
  if (!access.read_memory(access.context, key_storage_address,
                          storage.data(), storage.size())) {
    return false;
  }
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  std::memcpy(&size, storage.data() + 0x10, sizeof(size));
  std::memcpy(&capacity, storage.data() + 0x18, sizeof(capacity));
  if (size == 0 || size >= kRealmLawActiveCollectionKeyCapacity ||
      capacity < size) {
    return false;
  }
  if (capacity <= kMsvcStringInlineCapacity) {
    std::memcpy(output.bytes.data(), storage.data(),
                static_cast<std::size_t>(size));
  } else {
    std::uintptr_t data_address = 0;
    std::memcpy(&data_address, storage.data(), sizeof(data_address));
    if (data_address == 0 ||
        !access.read_memory(access.context, data_address, output.bytes.data(),
                            static_cast<std::size_t>(size))) {
      return false;
    }
  }
  output.size = static_cast<std::uint16_t>(size);
  return true;
}

} // namespace

static bool ReadRealmLawNativeKey12004(
    const RealmLawActiveCollectionAccess &access,
    std::uintptr_t key_storage_address,
    RealmLawActiveKey &output) noexcept {
  if (access.admitted_executable_sha256 !=
          ::xar::ck3_12004::kExecutableSha256 ||
      access.read_memory == nullptr || key_storage_address == 0) {
    return false;
  }
  return CopyKey(access, key_storage_address, output);
}

static bool ReadRealmLawActiveCollection12004(
    const RealmLawActiveCollectionAccess &access,
    RealmLawActiveCollection &output) noexcept {
  output = {};
  if (access.admitted_executable_sha256 !=
      ::xar::ck3_12004::kExecutableSha256) {
    output.failure = RealmLawActiveCollectionFailure::exact_build_mismatch;
    return false;
  }
  if (access.read_memory == nullptr) {
    output.failure = RealmLawActiveCollectionFailure::reader_unavailable;
    return false;
  }
  if (access.played_character_address == 0) {
    output.failure = RealmLawActiveCollectionFailure::actor_unavailable;
    return false;
  }
  std::uintptr_t law_context = 0;
  if (!Read(access, access.played_character_address +
                        kCharacterLawContextOffset,
            law_context) ||
      law_context == 0) {
    output.failure = RealmLawActiveCollectionFailure::law_context_unavailable;
    return false;
  }
  const auto collection = law_context + kLawCollectionOffset;
  std::uintptr_t law_slots = 0;
  std::int32_t count = -1;
  if (!Read(access, collection, law_slots) ||
      !Read(access, collection + 0x0C, count)) {
    output.failure = RealmLawActiveCollectionFailure::collection_unavailable;
    return false;
  }
  if (count < 0 ||
      count > static_cast<std::int32_t>(kRealmLawActiveCollectionMaximumLaws) ||
      (count != 0 && law_slots == 0)) {
    output.failure = RealmLawActiveCollectionFailure::count_invalid;
    return false;
  }
  for (std::int32_t i = 0; i < count; ++i) {
    std::uintptr_t law = 0;
    if (!Read(access, law_slots + static_cast<std::uintptr_t>(i) * 8,
              law) ||
        law == 0) {
      output.failure = RealmLawActiveCollectionFailure::law_unavailable;
      return false;
    }
    auto &key = output.keys[static_cast<std::size_t>(i)];
    if (!ReadRealmLawNativeKey12004(access, law + kLawKeyOffset, key)) {
      output.failure = RealmLawActiveCollectionFailure::key_invalid;
      return false;
    }
    for (std::int32_t j = 0; j < i; ++j) {
      if (output.keys[static_cast<std::size_t>(j)] == key) {
        output.failure = RealmLawActiveCollectionFailure::duplicate_key;
        return false;
      }
    }
  }
  output.count = static_cast<std::uint32_t>(count);
  output.failure = RealmLawActiveCollectionFailure::none;
  return true;
}

} // namespace xar::ck3_12004::private_law

namespace xar::ck3_12004::private_law {
using ck3_11906::private_law::kRealmLawRelevantFeudalGroups11906;
using ck3_11906::private_law::kRealmLawMaximumRelevantCandidates11906;
using ck3_11906::private_law::kRealmLawMaximumNativeGroupCandidates11906;
namespace {

constexpr std::uintptr_t kLawDatabaseSingletonRva = kLawGroupDatabaseSingletonRva12004;
constexpr std::uintptr_t kDatabaseGroupArrayOffset = kLawGroupDatabaseArrayOffset12004;
constexpr std::uintptr_t kDatabaseGroupCountOffset = kLawGroupDatabaseCountOffset12004;
constexpr std::uintptr_t kGroupKeyOffset = 0x18;
constexpr std::uintptr_t kGroupCandidateArrayOffset = kLawGroupCandidateArrayOffset12004;
constexpr std::uintptr_t kGroupCandidateCountOffset = kLawGroupCandidateCountOffset12004;
constexpr std::uintptr_t kLawGroupPointerOffset = kLawOwningGroupOffset12004;

std::string_view KeyText(const RealmLawActiveKey &key) noexcept {
  return {key.bytes.data(), key.size};
}

bool IsRelevantCandidate(std::size_t group_index, std::string_view key,
                         bool active) noexcept {
  if (active) return true;
  constexpr std::array<std::string_view, 4> crown{
      "crown_authority_0", "crown_authority_1", "crown_authority_2",
      "crown_authority_3"};
  constexpr std::array<std::string_view, 4> succession{
      "confederate_partition_succession_law", "partition_succession_law",
      "high_partition_succession_law", "single_heir_succession_law"};
  const auto &allowlist = group_index == 0 ? crown : succession;
  for (const auto admitted : allowlist) {
    if (key == admitted) return true;
  }
  return false;
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
  if (!ReadRealmLawNativeKey12004(access, group_address + kGroupKeyOffset,
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
      candidate_count > static_cast<std::int32_t>(
                            kRealmLawMaximumNativeGroupCandidates11906) ||
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
    RealmLawActiveKey key{};
    if (!ReadRealmLawNativeKey12004(access, law_address + kLawKeyOffset, key)) {
      failure = RealmLawCandidateCollectionFailure::candidate_key_invalid;
      return false;
    }
    const bool is_active = IsActiveKey(active, key);
    if (!IsRelevantCandidate(group_index, KeyText(key), is_active)) continue;
    if (group.candidate_count >= kRealmLawMaximumRelevantCandidates11906) {
      failure = RealmLawCandidateCollectionFailure::candidate_count_invalid;
      return false;
    }
    const auto output_index = static_cast<std::size_t>(group.candidate_count++);
    auto &candidate = group.candidates[output_index];
    candidate.key = key;
    candidate.active = is_active;
    if (candidate.active) {
      if (group.active_found) {
        failure = RealmLawCandidateCollectionFailure::active_law_ambiguous;
        return false;
      }
      group.active_found = true;
      group.active_law_key = candidate.key;
    }
    if (observer != nullptr &&
        !observer(observer_context, group_index, output_index,
                  law_address, candidate)) {
      failure = RealmLawCandidateCollectionFailure::candidate_observer_failed;
      return false;
    }
  }
  if (group.candidate_count == 0) {
    failure = RealmLawCandidateCollectionFailure::relevant_candidate_missing;
    return false;
  }
  return true;
}

} // namespace

bool ReadRealmLawCandidateCollectionWithObserver12004(
    const RealmLawActiveCollectionAccess &access, std::uintptr_t module_base,
    void *observer_context, ObserveRealmLawCandidate11906 observer,
    RealmLawCandidateCollection11906 &output) noexcept {
  output = {};
  RealmLawActiveCollection active{};
  if (!ReadRealmLawActiveCollection12004(access, active)) {
    output.failure =
        RealmLawCandidateCollectionFailure::active_collection_unavailable;
    output.active_failure = active.failure;
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
    if (!ReadRealmLawNativeKey12004(access, group_address + kGroupKeyOffset,
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

} // namespace xar::ck3_12004::private_law

namespace xar::ck3_12004::private_law {

RealmLawFinalTerms12002Result ReadRealmLawFinalTerms12004(
    const RealmLawFinalTerms12002Input &input,
    const RealmLawFinalTerms12002Operations &operations) noexcept {
  RealmLawFinalTerms12002Result result{};
  const auto &op = operations.terms;
  if (input.law == nullptr || input.actor == nullptr ||
      input.full_actor_id == 0xFFFFFFFFu || op.candidate_kind_allowed == nullptr ||
      op.is_active == nullptr || op.engine_final_can_enact == nullptr ||
      op.read_cost_q100000 == nullptr ||
      operations.full_can_enact_with_reason == nullptr ||
      operations.destroy_native_reason == nullptr) return result;
  try {
    const bool kind = op.candidate_kind_allowed(input.law);
    const bool active = kind && op.is_active(input.actor, input.law);
    const bool can_enact = kind && !active &&
        op.engine_final_can_enact(input.law, input.actor, nullptr);
    const auto *cost = static_cast<const std::byte *>(input.law) + kRealmLawCompiledCostOffset12004;
    if (op.read_cost_q100000(result.terms.cost_raw.data(), cost, input.full_actor_id) !=
        result.terms.cost_raw.data()) return {};
    result.terms.cost_available = true;
    result.terms.status = !kind ? RealmLawFinalTerms12002Status::candidate_kind_rejected
        : active ? RealmLawFinalTerms12002Status::already_active
        : can_enact ? RealmLawFinalTerms12002Status::can_enact
                    : RealmLawFinalTerms12002Status::engine_blocked;

    // The engine expects its 32-byte MSVC string in empty inline mode.
    alignas(8) std::array<std::byte, 32> reason{};
    const std::uint64_t inline_capacity = 15;
    std::memcpy(reason.data() + 0x18, &inline_capacity, sizeof(inline_capacity));
    const bool full_can_enact = operations.full_can_enact_with_reason(input.law, input.actor, reason.data());
    std::uint64_t size = 0, capacity = 0;
    std::memcpy(&size, reason.data() + 0x10, sizeof(size));
    std::memcpy(&capacity, reason.data() + 0x18, sizeof(capacity));
    const char *characters = reinterpret_cast<const char *>(reason.data());
    if (capacity > 15) std::memcpy(&characters, reason.data(), sizeof(characters));
    const bool valid = size <= 4096 && capacity >= size && characters != nullptr;
    try {
      if (valid) result.native_reason.assign(characters, static_cast<std::size_t>(size));
    } catch (...) {
      operations.destroy_native_reason(reason.data());
      return {};
    }
    operations.destroy_native_reason(reason.data());
    if (!valid || full_can_enact != can_enact) return {};
    result.native_reason_available = true;
    return result;
  } catch (...) {
    return {};
  }
}

RealmLawFinalTerms12002Operations BindRealmLawFinalTermsImage12004(
    std::uintptr_t base, std::string_view actual_executable_sha256) noexcept {
  RealmLawFinalTerms12002Operations out{};
  if (base == 0 || actual_executable_sha256 !=
          ::xar::ck3_12004::kExecutableSha256) return out;
  out.terms.candidate_kind_allowed =
      reinterpret_cast<decltype(out.terms.candidate_kind_allowed)>(
          base + kRealmLawCandidateKindRva12004);
  out.terms.is_active = reinterpret_cast<decltype(out.terms.is_active)>(
      base + kRealmLawAlreadyActiveRva12004);
  out.terms.engine_final_can_enact =
      reinterpret_cast<decltype(out.terms.engine_final_can_enact)>(
          base + kRealmLawFinalCanEnactRva12004);
  out.terms.read_cost_q100000 =
      reinterpret_cast<decltype(out.terms.read_cost_q100000)>(
          base + kRealmLawNumericCostRva12004);
  out.full_can_enact_with_reason =
      reinterpret_cast<decltype(out.full_can_enact_with_reason)>(
          base + kRealmLawFinalCanEnactReasonRva12004);
  out.destroy_native_reason =
      reinterpret_cast<decltype(out.destroy_native_reason)>(
          base + kRealmLawReasonDestructorRva12004);
  return out;
}

ck3_12003::private_law::RealmLawSuccessionProfile12003
ReadRealmLawSuccessionProfile12004(
    const RealmLawActiveCollectionAccess &access, std::uintptr_t native_law,
    std::string_view actual_executable_sha256) noexcept {
  using ck3_12003::private_law::RealmLawSuccessionProfile12003;
  using ck3_12003::private_law::RealmLawSuccessionProfile12003Status;
  RealmLawSuccessionProfile12003 output{};
  if (actual_executable_sha256 != ::xar::ck3_12004::kExecutableSha256 ||
      access.admitted_executable_sha256 != ::xar::ck3_12004::kExecutableSha256 ||
      native_law == 0 || access.read_memory == nullptr) return output;

  // Only copied values enter the existing C++ shape mapping. Actual .4 parser,
  // constructor and enum bytes prove the same layout/ordinal meanings. This
  // does not call a .2 binder, pass an old SHA, or evaluate compiled conditions.
  constexpr auto shape_value_offset =
      ck3_12002::private_law::kRealmLawSuccessionPolicyOffset;
  std::array<std::byte,
      shape_value_offset + kRealmLawSuccessionPolicyBytes12004> copied_law{};
  auto *copied_policy = copied_law.data() + shape_value_offset;
  if (!access.read_memory(access.context,
          native_law + kRealmLawSuccessionPolicyOffset12004,
          copied_policy, kRealmLawSuccessionPolicyBytes12004) ||
      !ck3_12002::private_law::ReadRealmLawSuccessionShape12002(
          copied_law.data(), output.shape)) return output;

  output.create_primary_tier_titles =
      std::to_integer<std::uint8_t>(
          copied_policy[kRealmLawCreatePrimaryTierTitlesOffset12004]) != 0;
  output.status =
      output.shape.presence == bridge::RealmLawGovernancePresenceV1::absent &&
              !output.create_primary_tier_titles
          ? RealmLawSuccessionProfile12003Status::absent
          : RealmLawSuccessionProfile12003Status::available;
  return output;
}

} // namespace xar::ck3_12004::private_law
