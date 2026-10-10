#include "xar_bridge/person_transfer_block10_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <utility>

namespace xar::ck3_12004 {
namespace {

// Actual291D003/291D007 select Model+10. Complete2439670 uses
// pointer0, signed capacity8/countC and row byte ranges count<<4.
constexpr std::uintptr_t kBlockOffset = 0x10;

template <typename T>
std::optional<T> Copy(const PersonTransferBlock10Bindings12004 &bindings,
                      std::uintptr_t address) noexcept {
  T value{};
  if (!bindings.read_memory(bindings.read_context,
                           reinterpret_cast<const void *>(address),
                           &value, sizeof(value))) return std::nullopt;
  return value;
}

bool SameReceiver(const PersonTransferBlock10Snapshot12004 &before,
                  const PersonTransferBlock10Snapshot12004 &after) noexcept {
  return before.model_identity != 0 && before.block_identity != 0 &&
         before.model_identity == after.model_identity &&
         before.block_identity == after.block_identity;
}

bool HasRows(const PersonTransferBlock10Snapshot12004 &state) noexcept {
  return state.configured && state.rows_ready && state.rows.has_value();
}

bool HasDescriptor(const PersonTransferBlock10Snapshot12004 &state) noexcept {
  return state.configured && state.descriptor_ready &&
         state.data_identity && state.capacity_i32 && state.count_i32;
}

bool DescriptorEqual(const PersonTransferBlock10Snapshot12004 &left,
                     const PersonTransferBlock10Snapshot12004 &right) noexcept {
  return left.data_identity == right.data_identity &&
         left.capacity_i32 == right.capacity_i32 &&
         left.count_i32 == right.count_i32;
}

} // namespace

PersonTransferBlock10Bindings12004 BindPersonTransferBlock10Inputs12004(
    std::string_view build_version, std::string_view executable_sha256,
    PersonTransferBlock10ReadMemory12004 read_memory,
    void *read_context) noexcept {
  if (build_version != kGameVersion || executable_sha256 != kExecutableSha256 ||
      read_memory == nullptr) return {};
  return {true, read_memory, read_context};
}

PersonTransferBlock10Snapshot12004 ReadPersonTransferBlock10ForModel12004(
    const PersonTransferBlock10Bindings12004 &bindings,
    std::uintptr_t actual_model, std::size_t row_copy_budget) noexcept {
  static_assert(sizeof(std::uintptr_t) == 8);
  static_assert(sizeof(PersonTransferBlock10Row12004) == 16);
  PersonTransferBlock10Snapshot12004 result;
  result.model_identity = actual_model;
  result.row_copy_budget = row_copy_budget;
  if (!bindings.enabled || bindings.read_memory == nullptr) return result;
  result.configured = true;
  if (actual_model == 0) {
    result.reason = "person_block10_model_unavailable";
    return result;
  }
  const auto block = actual_model + kBlockOffset;
  result.block_identity = block;
  result.data_identity = Copy<std::uintptr_t>(bindings, block);
  result.capacity_i32 = Copy<std::int32_t>(bindings, block + 8);
  result.count_i32 = Copy<std::int32_t>(bindings, block + 0xC);
  result.descriptor_ready = result.data_identity.has_value() &&
      result.capacity_i32.has_value() && result.count_i32.has_value();
  if (!result.count_i32) {
    result.reason = "person_block10_count_unread";
    return result;
  }
  if (*result.count_i32 < 0) {
    result.reason = "person_block10_count_negative";
    return result;
  }
  const auto count = static_cast<std::size_t>(*result.count_i32);
  if (count > row_copy_budget) {
    result.reason = "person_block10_row_copy_budget_exceeded";
    return result;
  }
  if (count > 0 && (!result.data_identity || *result.data_identity == 0)) {
    result.reason = "person_block10_row_pointer_unavailable";
    return result;
  }
  try {
    std::vector<PersonTransferBlock10Row12004> rows(count);
    if (count > 0 && !bindings.read_memory(bindings.read_context,
          reinterpret_cast<const void *>(*result.data_identity), rows.data(),
          count * kPersonTransferBlock10RowBytes12004)) {
      result.reason = "person_block10_rows_unread";
      return result;
    }
    result.rows = std::move(rows);
    result.rows_ready = true;
    result.reason = {};
  } catch (...) {
    result.reason = "person_block10_rows_copy_failed";
  }
  return result;
}

PersonTransferBlock10Comparison12004 ComparePersonTransferBlock10Postimage12004(
    const PersonTransferBlock10Snapshot12004 &a_before,
    const PersonTransferBlock10Snapshot12004 &b_before,
    const PersonTransferBlock10Snapshot12004 &a_after,
    const PersonTransferBlock10Snapshot12004 &b_after) noexcept {
  PersonTransferBlock10Comparison12004 result;
  if (!SameReceiver(a_before, a_after) || !SameReceiver(b_before, b_after))
    return result;
  result.receiver_pair_matches = true;
  if (HasRows(a_after) && HasRows(b_before))
    result.a_after_rows_equal_b_before = *a_after.rows == *b_before.rows;
  if (HasRows(b_after) && HasRows(a_before))
    result.b_after_rows_equal_a_before = *b_after.rows == *a_before.rows;
  result.row_comparison_ready = result.a_after_rows_equal_b_before.has_value() &&
      result.b_after_rows_equal_a_before.has_value();
  if (result.row_comparison_ready)
    result.row_postimage_matches_exchange =
        *result.a_after_rows_equal_b_before && *result.b_after_rows_equal_a_before;
  if (HasDescriptor(a_before) && HasDescriptor(b_before) &&
      HasDescriptor(a_after) && HasDescriptor(b_after)) {
    result.descriptor_comparison_ready = true;
    result.descriptor_postimage_matches_swap = DescriptorEqual(a_after, b_before) &&
                                               DescriptorEqual(b_after, a_before);
  }
  result.reason = result.row_comparison_ready
      ? std::string_view{} : "person_block10_rows_partial";
  return result;
}

} // namespace xar::ck3_12004
