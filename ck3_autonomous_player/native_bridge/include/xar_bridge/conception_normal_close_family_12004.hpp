#pragma once

#include "xar_bridge/ck3_12004_family_abi.hpp"
#include "xar_bridge/ck3_12004_family_break_penalty.hpp"

#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

// Reuse the already-qualified getter ABI. The conception caller tests AL;
// this typed result records that branch value, not an invented integer AL ABI.
using ConceptionNormalCloseFamily12004Getter =
    ck3_12002::family_break_penalty::FamilyPredicate;
using ConceptionNormalCloseFamily12004GuardedRead =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct ConceptionNormalCloseFamily12004Bindings {
  bool enabled = false;
  ConceptionNormalCloseFamily12004Getter close_family = nullptr;
  ConceptionNormalCloseFamily12004GuardedRead read_memory = nullptr;
  void *read_context = nullptr;
};

// This constructs the existing qualified bindings; it never executes the
// obligations/penalty reader or any other getter from that binding object.
inline ConceptionNormalCloseFamily12004Bindings
BindConceptionNormalCloseFamily12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    ConceptionNormalCloseFamily12004GuardedRead read_memory,
    void *read_context) noexcept {
  ConceptionNormalCloseFamily12004Bindings result;
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      read_memory == nullptr ||
      image_base > std::numeric_limits<std::uintptr_t>::max() -
                       kFamilyCloseFamilyRva)
    return result;
  const auto qualified =
      BindFamilyBreakPenaltyImage(image_base, executable_sha256);
  if (!qualified.enabled || qualified.close_family == nullptr) return result;
  result.enabled = true;
  result.close_family = qualified.close_family;
  result.read_memory = read_memory;
  result.read_context = read_context;
  return result;
}

struct ConceptionNormalCloseFamily12004Read {
  std::string_view source = "ck3_1_20_0_4_native_normal_close_family_2912080";
  std::string_view status = "unavailable";
  std::string_view unavailable_reason =
      "native_conception_normal_close_family_binding_unavailable";
  // Only this optional enters ConceptionPairProviderInputs12004.
  std::optional<bool> normal_close_family;
  // Raw typed getter return can survive a failed post-call identity guard.
  // It does not become a usable provider input until all guards succeed.
  std::optional<bool> native_return_value;
  bool native_call_attempted = false;
  std::optional<std::uint32_t> first_full_id_before;
  std::optional<std::uint32_t> second_full_id_before;
  std::optional<std::uint32_t> first_full_id_after;
  std::optional<std::uint32_t> second_full_id_after;
};

namespace conception_normal_close_family_detail {

inline bool ReadFullId(const ConceptionNormalCloseFamily12004Bindings &b,
                       std::uintptr_t character,
                       std::uint32_t &value) noexcept {
  if (character == 0 ||
      character > std::numeric_limits<std::uintptr_t>::max() -
                      kCharacterFullIdOffset)
    return false;
  return b.read_memory(b.read_context,
      reinterpret_cast<const void *>(character + kCharacterFullIdOffset),
      &value, sizeof(value));
}

// Keep this SEH boundary free of objects requiring C++ unwinding. The Windows
// production bridge catches native faults; portable compound fixtures catch
// C++ exceptions and do not claim to validate Windows hardware-fault handling.
inline bool Invoke(ConceptionNormalCloseFamily12004Getter getter,
                   std::uintptr_t first, std::uintptr_t second,
                   bool *returned) noexcept {
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
    *returned = getter(reinterpret_cast<void *>(first),
                       reinterpret_cast<void *>(second));
    return true;
  } __except (1) {
    return false;
  }
#else
  try {
    *returned = getter(reinterpret_cast<void *>(first),
                       reinterpret_cast<void *>(second));
    return true;
  } catch (...) {
    return false;
  }
#endif
}

} // namespace conception_normal_close_family_detail

// The caller already resolved these same-query household characters. This
// reader neither resolves a second pair nor substitutes the 0x2912210 related
// predicate. Native argument order is first in RCX, second in RDX at 2B962D0.
inline ConceptionNormalCloseFamily12004Read
ReadConceptionNormalCloseFamilyForPair12004(
    const ConceptionNormalCloseFamily12004Bindings &b,
    std::uintptr_t first, std::uint32_t expected_first_full_id,
    std::uintptr_t second, std::uint32_t expected_second_full_id,
    std::optional<bool> first_alternate_selector,
    std::optional<bool> second_alternate_selector) noexcept {
  ConceptionNormalCloseFamily12004Read result;
  // Preserve the actual first-then-second demand order. Unknown first cannot
  // be bypassed by a known true second selector.
  if (!first_alternate_selector) {
    result.unavailable_reason =
        "native_conception_normal_close_family_first_selector_unavailable";
    return result;
  }
  if (*first_alternate_selector) {
    result.status = "not_required";
    result.unavailable_reason =
        "native_conception_normal_close_family_skipped_by_first_selector";
    return result;
  }
  if (!second_alternate_selector) {
    result.unavailable_reason =
        "native_conception_normal_close_family_second_selector_unavailable";
    return result;
  }
  if (*second_alternate_selector) {
    result.status = "not_required";
    result.unavailable_reason =
        "native_conception_normal_close_family_skipped_by_second_selector";
    return result;
  }
  if (!b.enabled || b.close_family == nullptr || b.read_memory == nullptr)
    return result;
  if (expected_first_full_id == std::numeric_limits<std::uint32_t>::max() ||
      expected_second_full_id == std::numeric_limits<std::uint32_t>::max()) {
    result.unavailable_reason =
        "native_conception_normal_close_family_invalid_full_id";
    return result;
  }

  std::uint32_t id = 0;
  if (!conception_normal_close_family_detail::ReadFullId(b, first, id)) {
    result.unavailable_reason =
        "native_conception_normal_close_family_first_id_read_unavailable";
    return result;
  }
  result.first_full_id_before = id;
  if (id != expected_first_full_id) {
    result.unavailable_reason =
        "native_conception_normal_close_family_first_generation_mismatch";
    return result;
  }
  if (!conception_normal_close_family_detail::ReadFullId(b, second, id)) {
    result.unavailable_reason =
        "native_conception_normal_close_family_second_id_read_unavailable";
    return result;
  }
  result.second_full_id_before = id;
  if (id != expected_second_full_id) {
    result.unavailable_reason =
        "native_conception_normal_close_family_second_generation_mismatch";
    return result;
  }

  bool returned = false;
  result.native_call_attempted = true;
  if (!conception_normal_close_family_detail::Invoke(
          b.close_family, first, second, &returned)) {
    result.unavailable_reason =
        "native_conception_normal_close_family_getter_failed";
    return result;
  }
  result.native_return_value = returned;

  if (!conception_normal_close_family_detail::ReadFullId(b, first, id)) {
    result.unavailable_reason =
        "native_conception_normal_close_family_first_id_recheck_unavailable";
    return result;
  }
  result.first_full_id_after = id;
  if (id != expected_first_full_id) {
    result.unavailable_reason =
        "native_conception_normal_close_family_first_generation_changed";
    return result;
  }
  if (!conception_normal_close_family_detail::ReadFullId(b, second, id)) {
    result.unavailable_reason =
        "native_conception_normal_close_family_second_id_recheck_unavailable";
    return result;
  }
  result.second_full_id_after = id;
  if (id != expected_second_full_id) {
    result.unavailable_reason =
        "native_conception_normal_close_family_second_generation_changed";
    return result;
  }
  result.status = "available";
  result.unavailable_reason = {};
  result.normal_close_family = returned;
  return result;
}

} // namespace xar::ck3_12004
