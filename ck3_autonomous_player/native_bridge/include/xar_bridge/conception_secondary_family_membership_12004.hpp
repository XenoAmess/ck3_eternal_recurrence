#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

using ConceptionSecondaryFamilyMembership12004ReadMemory =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct ConceptionSecondaryFamilyMembership12004Bindings {
  bool enabled = false;
  ConceptionSecondaryFamilyMembership12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
  std::size_t max_entries = 4096;
};

struct ConceptionSecondaryFamilyMembership12004Read {
  std::string_view status = "unavailable";
  std::string_view unavailable_reason =
      "native_conception_secondary_family_membership_binding_unavailable";
  std::optional<bool> second_family_present;
  // Native null Family bypass leaves all membership/list fields unconsulted.
  std::optional<bool> list_data_present;
  std::optional<std::int32_t> list_count_raw_i32;
  std::optional<std::uint64_t> list_span_bytes;
  std::vector<std::uint32_t> ordered_full_ids;
  std::optional<std::size_t> first_match_index;
  std::optional<bool> second_family20_contains_first;
};

inline ConceptionSecondaryFamilyMembership12004Bindings
BindConceptionSecondaryFamilyMembership12004(
    std::string_view build_version, std::string_view executable_sha256,
    ConceptionSecondaryFamilyMembership12004ReadMemory read_memory,
    void *read_context = nullptr, std::size_t max_entries = 4096) noexcept {
  if (build_version != kGameVersion || executable_sha256 != kExecutableSha256 ||
      read_memory == nullptr || max_entries == 0) return {};
  return {true, read_memory, read_context, max_entries};
}

namespace conception_secondary_family_membership_detail {
template <typename T>
inline bool Field(const ConceptionSecondaryFamilyMembership12004Bindings &b,
                  std::uintptr_t object, std::size_t offset,
                  T &output) noexcept {
  return object != 0 &&
      object <= std::numeric_limits<std::uintptr_t>::max() - offset &&
      b.read_memory(b.read_context,
          reinterpret_cast<const void *>(object + offset), &output, sizeof(T));
}
inline bool Identity(const ConceptionSecondaryFamilyMembership12004Bindings &b,
                     std::uintptr_t character, std::uint32_t expected) noexcept {
  std::uint32_t actual = 0, magic = 0;
  return expected != 0xFFFFFFFFU && Field(b, character, 0x18, actual) &&
      actual == expected && Field(b, character, 0x1C, magic) &&
      magic == 0x43686172U;
}
} // namespace conception_secondary_family_membership_detail

// Existing same-household query supplies already resolved second and first
// Characters with complete IDs and surrounds this read with its whole-frame
// guard. Actual provider2B9639B searches secondFamily20 for firstfullID; this
// independent equality reader calls no original880430/CPU-dispatch/getter.
inline ConceptionSecondaryFamilyMembership12004Read
ReadConceptionSecondaryFamilyMembershipForPair12004(
    const ConceptionSecondaryFamilyMembership12004Bindings &b,
    std::uintptr_t second_character, std::uint32_t second_full_id,
    std::uintptr_t first_character, std::uint32_t first_full_id) {
  using namespace conception_secondary_family_membership_detail;
  ConceptionSecondaryFamilyMembership12004Read result;
  if (!b.enabled || b.read_memory == nullptr) return result;
  if (!Identity(b, second_character, second_full_id) ||
      !Identity(b, first_character, first_full_id)) {
    result.unavailable_reason =
        "native_conception_secondary_family_membership_pair_identity_unavailable";
    return result;
  }
  static_assert(sizeof(std::uintptr_t) == 8);
  std::uintptr_t family = 0;
  if (!Field(b, second_character, 0x1A8, family)) {
    result.unavailable_reason =
        "native_conception_secondary_family_membership_family_pointer_unread";
    return result;
  }
  result.second_family_present = family != 0;
  if (family == 0) {
    // Actual2B96378/7B bypasses to final writer. Membership was not requested.
    result.status = "available";
    result.unavailable_reason = {};
    return result;
  }
  std::uintptr_t data = 0;
  std::int32_t count = 0;
  if (!Field(b, family, 0x20, data) || !Field(b, family, 0x2C, count)) {
    result.unavailable_reason =
        "native_conception_secondary_family_membership_array_unread";
    return result;
  }
  result.list_data_present = data != 0;
  result.list_count_raw_i32 = count;
  if (count < 0 || std::size_t(count) > b.max_entries) {
    result.unavailable_reason =
        "native_conception_secondary_family_membership_count_outside_read_budget";
    return result;
  }
  const auto bytes = std::uint64_t(count) * 4;
  result.list_span_bytes = bytes;
  if (count != 0 && (data == 0 ||
      data > std::numeric_limits<std::uintptr_t>::max() - bytes)) {
    result.unavailable_reason =
        "native_conception_secondary_family_membership_span_unavailable";
    return result;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    std::uint32_t id = 0;
    if (!Field(b, data, std::size_t(index) * 4, id)) {
      result.unavailable_reason =
          "native_conception_secondary_family_membership_id_unread";
      return result;
    }
    result.ordered_full_ids.push_back(id);
    if (id == first_full_id && !result.first_match_index)
      result.first_match_index = std::size_t(index);
  }
  result.second_family20_contains_first = result.first_match_index.has_value();
  result.status = "available";
  result.unavailable_reason = {};
  return result;
}

} // namespace xar::ck3_12004
