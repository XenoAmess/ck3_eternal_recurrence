#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004 { struct SourceReadFrame12004; }

namespace xar::ck3_12004::lifestyle {

struct LifestylePerkReadonlyAccess12004 {
  std::uintptr_t module_base = 0;
  void *read_context = nullptr;
  bool (*read_memory)(void *, std::uintptr_t, void *, std::size_t) = nullptr;
  // Actual current application-thread GS58 operand for2919340's null branch.
  // The nonnull Character extension branch does not require this input.
  std::optional<std::uintptr_t> current_thread_tls_array_identity{};
  // Existing caller's copied current-query metadata; only reached truth uses
  // this companion. Context projection alone does not confirm a caller frame.
  const ::xar::ck3_12004::SourceReadFrame12004 *current_query_source_frame = nullptr;
};

struct LifestylePerkReadonlyPredicate12004 {
  std::optional<bool> value{};
  std::string unavailable_reason{};
};

// Actual288B1B0 reads are retained independently. Source-rejected paths do
// not fill later operands. The accepted prefix has a separate tail predicate.
struct LifestylePerkPredicateInputs12004 {
  std::uintptr_t command_identity = 0;
  std::optional<std::uintptr_t> registry_identity{};
  std::optional<std::uint32_t> requested_full_character_id_u32{};
  std::optional<std::uint32_t> registry_capacity_u32{};
  std::optional<std::uintptr_t> indexed_character_identity{};
  std::optional<std::uint32_t> indexed_character_full_id_u32{};
  std::optional<bool> used_fallback{};
  std::optional<std::uintptr_t> selected_character_identity{};
  std::optional<std::uint32_t> selected_character_magic_u32{};
  std::optional<std::uint32_t> selected_character_full_id_u32{};
  std::optional<std::uint64_t> selected_character_field_1d0_u64{};
  std::optional<std::uintptr_t> selected_perk_identity{};
  std::optional<std::uint32_t> selected_perk_magic_u32{};
  std::optional<bool> prefix_admitted{};
  std::string unavailable_reason{};
};

LifestylePerkPredicateInputs12004 ReadLifestylePerkPredicateInputs288B1B012004(
    const LifestylePerkReadonlyAccess12004 &, std::uintptr_t command_identity) noexcept;

} // namespace xar::ck3_12004::lifestyle
