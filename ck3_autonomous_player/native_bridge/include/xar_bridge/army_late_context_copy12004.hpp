#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace xar::ck3_12004 {
using ArmyLateContextReadMemory12004 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
inline constexpr std::size_t kArmyLateContextCopiedRows12004 = 32;
struct ArmyLateContextCopiedRow12004 {
  std::uint32_t key_raw_u32 = 0;
  std::uint16_t kind_raw_u16 = 0, subtype_raw_u16 = 0;
  std::uint64_t payload_raw_u64 = 0;
};
struct ArmyLateContextCopy12004 {
  bool root_copy_ready = false, named_header_copy_ready = false;
  bool named_header_unchanged = false, named_rows_copy_ready = false;
  bool named_rows_truncated = false;
  std::optional<std::uint16_t> root_kind_raw_u16, root_subtype_raw_u16;
  std::optional<std::uint64_t> root_payload_raw_u64;
  // Seed is copied as a DWORD; its producer interpretation remains with64.
  std::optional<std::uint32_t> context_seed_10_raw_u32;
  std::optional<std::int32_t> named_capacity_raw_i32, named_count_raw_i32;
  std::size_t copied_row_count = 0;
  std::array<ArmyLateContextCopiedRow12004, kArmyLateContextCopiedRows12004> rows{};
  const char *unavailable_reason = "incoming_context_unavailable";
  std::optional<bool> builder_called;
  std::optional<std::uint64_t> builder_callsite_rva, parent_pc_rva;
};
struct ArmyLateContextSourceRole12004 {
  std::uint16_t expected_kind_raw_u16 = 0;
  std::uint32_t loaded_key_raw_u32 = 0;
  std::size_t matching_key_count = 0;
  std::optional<bool> token_kind_and_subtype_match;
  std::optional<std::uint64_t> payload_raw_u64;
};
struct ArmyLateContextSourceRoles12004 {
  std::optional<bool> root_kind27_subtype0_matches;
  bool named_keys_loaded = false, complete_named_input_shape_matches = false;
  std::array<ArmyLateContextSourceRole12004, 3> roles{{{4, 0, 0, {}, {}}, {5, 0, 0, {}, {}}, {5, 0, 0, {}, {}}}};
};

// Same callback as64's natural dispatcher reader. Reads only the actual R8
// context, caps its copied named rows at32, and rereads its exact16B header.
// It constructs no scope and never invokes the context builder/named save.
ArmyLateContextCopy12004 CopyActualArmyLateContext12004(const void *incoming_context,
    ArmyLateContextReadMemory12004 read_memory, void *read_context) noexcept;

// Keys are the three actual loaded DWORDs at5D4C27C/5D4BE20/5D4BE1C.
// A matching shape identifies source-compatible roles; it proves neither the
//2C44580 call nor its parentPC. The copied rows are always retained separately.
ArmyLateContextSourceRoles12004 ClassifyActualArmyLateContextRoles12004(
    const ArmyLateContextCopy12004 &, std::span<const std::uint32_t, 3> loaded_keys) noexcept;
} // namespace xar::ck3_12004
