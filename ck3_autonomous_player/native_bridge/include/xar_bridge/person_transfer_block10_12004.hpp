#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::size_t kPersonTransferBlock10RowBytes12004 = 16;
using PersonTransferBlock10Row12004 =
    std::array<std::uint8_t, kPersonTransferBlock10RowBytes12004>;
using PersonTransferBlock10ReadMemory12004 =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct PersonTransferBlock10Bindings12004 {
  bool enabled = false;
  PersonTransferBlock10ReadMemory12004 read_memory = nullptr;
  void *read_context = nullptr;
};

// Owned raw row material, not a PC key/value copy or native branch emulator.
// The first/second qwords remain intact even if a PC pointer is null or a
// weight has its sign bit set. Root owns invocation/owner/stage attribution.
struct PersonTransferBlock10Snapshot12004 {
  std::string_view source = "native_person_block10_owned_snapshot";
  bool configured = false;
  bool rows_ready = false;
  bool descriptor_ready = false;
  std::string_view reason = "person_block10_binding_unavailable";
  std::uintptr_t model_identity = 0;
  std::uintptr_t block_identity = 0;
  std::size_t row_copy_budget = 0;
  std::optional<std::uintptr_t> data_identity;
  std::optional<std::int32_t> capacity_i32;
  std::optional<std::int32_t> count_i32;
  std::optional<std::vector<PersonTransferBlock10Row12004>> rows;
};

struct PersonTransferBlock10Comparison12004 {
  bool receiver_pair_matches = false;
  bool row_comparison_ready = false;
  bool descriptor_comparison_ready = false;
  std::string_view reason = "person_block10_receiver_pair_mismatch";
  std::optional<bool> a_after_rows_equal_b_before;
  std::optional<bool> b_after_rows_equal_a_before;
  // Equality of observed postimages only, not a causal completion witness.
  std::optional<bool> row_postimage_matches_exchange;
  // Optional diagnostic: in-place exchange need not swap these descriptors.
  // Equality never identifies which native source branch executed.
  std::optional<bool> descriptor_postimage_matches_swap;
};

PersonTransferBlock10Bindings12004 BindPersonTransferBlock10Inputs12004(
    std::string_view build_version, std::string_view executable_sha256,
    PersonTransferBlock10ReadMemory12004 read_memory,
    void *read_context = nullptr) noexcept;

// Root calls this at its same original291CF30 before/after boundary. Only
// Model+10 pointer0/capacity8/countC and count*16 row bytes are copied. The
// caller's explicit budget is observer scope, not a native admission rule.
// No owner/PC/virtual slot/delegate is dereferenced or invoked.
PersonTransferBlock10Snapshot12004 ReadPersonTransferBlock10ForModel12004(
    const PersonTransferBlock10Bindings12004 &bindings,
    std::uintptr_t actual_model, std::size_t row_copy_budget) noexcept;

PersonTransferBlock10Comparison12004 ComparePersonTransferBlock10Postimage12004(
    const PersonTransferBlock10Snapshot12004 &a_before,
    const PersonTransferBlock10Snapshot12004 &b_before,
    const PersonTransferBlock10Snapshot12004 &a_after,
    const PersonTransferBlock10Snapshot12004 &b_after) noexcept;

} // namespace xar::ck3_12004
