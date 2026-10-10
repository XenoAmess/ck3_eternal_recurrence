#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

using ConceptionSecondTitleStateReadMemory12004 =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct ConceptionSecondTitleStateBindings12004 {
  bool enabled = false;
  ConceptionSecondTitleStateReadMemory12004 read_memory = nullptr;
  void *read_context = nullptr;
};

inline ConceptionSecondTitleStateBindings12004
BindConceptionSecondTitleState12004(
    std::string_view build, std::string_view executable_sha256,
    ConceptionSecondTitleStateReadMemory12004 read_memory,
    void *read_context = nullptr) noexcept {
  constexpr std::string_view pin =
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  return {build == "1.20.0.4" && executable_sha256 == pin &&
              read_memory != nullptr,
          read_memory, read_context};
}

struct ConceptionSecondTitleStatePresence12004Read {
  std::string_view status = "unavailable";
  std::string_view unavailable_reason =
      "second_title_state_binding_unavailable";
  std::optional<std::uint64_t> second_1c0_raw_u64{};
  std::optional<bool> second_title_state_present{};
};

namespace conception_second_title_state_detail {
template <typename T>
inline bool Field(const ConceptionSecondTitleStateBindings12004 &b,
                  std::uintptr_t object, std::size_t offset,
                  T &output) noexcept {
  constexpr auto maximum = std::numeric_limits<std::uintptr_t>::max();
  return b.enabled && b.read_memory != nullptr && object != 0 &&
      offset <= maximum - (sizeof(T) - 1) &&
      object <= maximum - offset - (sizeof(T) - 1) &&
      b.read_memory(b.read_context,
                    reinterpret_cast<const void *>(object + offset),
                    &output, sizeof(output));
}
} // namespace conception_second_title_state_detail

// The current household owner supplies its already resolved second Character
// and complete generation-bearing ID. Its existing paused frame, relationship
// and receiver checks surround this read. No resolver or first-role proxy runs.
inline ConceptionSecondTitleStatePresence12004Read
ReadConceptionSecondTitleStatePresenceForCharacter12004(
    const ConceptionSecondTitleStateBindings12004 &b,
    std::uintptr_t second, std::uint32_t second_full_id) noexcept {
  using conception_second_title_state_detail::Field;
  ConceptionSecondTitleStatePresence12004Read result{};
  if (!b.enabled || b.read_memory == nullptr) return result;
  if (second == 0 ||
      second_full_id == std::numeric_limits<std::uint32_t>::max()) {
    result.unavailable_reason = "second_title_state_receiver_unavailable";
    return result;
  }

  constexpr std::uint32_t character_magic = 0x43686172;
  std::uint32_t before_id = 0, before_magic = 0;
  if (!Field(b, second, 0x18, before_id) ||
      !Field(b, second, 0x1C, before_magic)) {
    result.unavailable_reason = "second_title_state_character_header_unreadable";
    return result;
  }
  if (before_id != second_full_id || before_magic != character_magic) {
    result.unavailable_reason = "second_title_state_character_identity_mismatch";
    return result;
  }

  // Actual provider compares Q64 [second+0x1C0] at 0x2B960E0/0x2B960FB.
  // Retain the opaque bits; never dereference or interpret the referent.
  std::uint64_t raw = 0;
  if (!Field(b, second, 0x1C0, raw)) {
    result.unavailable_reason = "second_title_state_q64_unreadable";
    return result;
  }

  std::uint32_t after_id = 0, after_magic = 0;
  if (!Field(b, second, 0x18, after_id) ||
      !Field(b, second, 0x1C, after_magic)) {
    result.unavailable_reason =
        "second_title_state_character_header_recheck_unreadable";
    return result;
  }
  if (after_id != second_full_id || after_magic != character_magic) {
    result.unavailable_reason = "second_title_state_character_identity_changed";
    return result;
  }
  result.status = "available";
  result.unavailable_reason = {};
  result.second_1c0_raw_u64 = raw;
  result.second_title_state_present = raw != 0;
  return result;
}

} // namespace xar::ck3_12004
