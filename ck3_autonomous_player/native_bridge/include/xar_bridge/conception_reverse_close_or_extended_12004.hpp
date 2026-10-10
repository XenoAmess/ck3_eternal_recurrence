#pragma once

#include "xar_bridge/ck3_12002_family_obligations_break_penalty.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

// Reuse the qualified Family ABI, including its Boolean return convention.
using ConceptionReverseCloseOrExtended12004Getter =
    ck3_12002::family_break_penalty::FamilyPredicate;
using ConceptionReverseCloseOrExtended12004ReadMemory =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct ConceptionReverseCloseOrExtended12004Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ConceptionReverseCloseOrExtended12004Getter getter = nullptr;
  ConceptionReverseCloseOrExtended12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
};

struct ConceptionReverseCloseOrExtended12004Read {
  std::string_view source = "native_reverse_close_or_extended_family";
  std::string_view status = "unavailable";
  std::string_view unavailable_reason =
      "native_reverse_close_or_extended_binding_unavailable";
  // Matches the full provider's independent alternate-branch input. Known
  // false requires a real getter return and stable owned full IDs.
  std::optional<bool> alternate_close_or_extended;
};

ConceptionReverseCloseOrExtended12004Bindings
BindConceptionReverseCloseOrExtended12004(
    std::uintptr_t module_base, std::string_view executable_sha256,
    ConceptionReverseCloseOrExtended12004ReadMemory read_memory,
    void *read_context = nullptr) noexcept;

// Actual2B963C7 calls2912270 with RCX=second and RDX=first. The current
// household collector supplies both already-resolved owned pointers and full
// IDs. Its existing enclosing application-thread frame/receiver guards remain
// authoritative. The reader checks each full identity before/after this one
// qualified read-only getter, independent of the separate2912210 predicate.
ConceptionReverseCloseOrExtended12004Read
ReadConceptionReverseCloseOrExtended12004(
    const ConceptionReverseCloseOrExtended12004Bindings &bindings,
    std::uintptr_t second_character, std::uint32_t expected_second_full_id,
    std::uintptr_t first_character,
    std::uint32_t expected_first_full_id) noexcept;

} // namespace xar::ck3_12004
