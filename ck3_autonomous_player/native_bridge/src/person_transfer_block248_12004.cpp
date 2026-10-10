#include "xar_bridge/person_transfer_block248_12004.hpp"
#include "xar_bridge/person_installed_transfer_stage_12004.hpp"

#include <limits>
#include <new>
#include <stdexcept>
#include <utility>

namespace xar::ck3_12004 {
namespace {

static_assert(sizeof(std::uintptr_t) == 8);

std::optional<std::uintptr_t> Add(std::uintptr_t base,
                                  std::uintptr_t offset) noexcept {
  if (base > std::numeric_limits<std::uintptr_t>::max() - offset)
    return std::nullopt;
  return base + offset;
}

template <class T>
std::optional<T> Copy(const PersonTransferBlock248Bindings12004 &bindings,
                     std::uintptr_t block, std::uintptr_t offset) noexcept {
  const auto address = Add(block, offset);
  T value{};
  if (!address || !bindings.read ||
      !bindings.read(bindings.read_context, *address, &value, sizeof(value)))
    return std::nullopt;
  return value;
}

std::optional<bool> PayloadEqual(
    const PersonTransferBlock248Snapshot12004 &left,
    const PersonTransferBlock248Snapshot12004 &right) {
  if (!left.payload_ready || !right.payload_ready ||
      !left.ordered_payload_raw64 || !right.ordered_payload_raw64)
    return std::nullopt;
  return *left.ordered_payload_raw64 == *right.ordered_payload_raw64;
}

} // namespace

PersonTransferBlock248Snapshot12004 ReadPersonTransferBlock24812004(
    const PersonTransferBlock248Bindings12004 &bindings,
    std::uintptr_t actual_model) {
  PersonTransferBlock248Snapshot12004 result;
  result.model_identity = actual_model;
  if (actual_model == 0) {
    result.reason = "model_absent";
    return result;
  }
  result.block_identity = Add(actual_model, kPersonTransferBlock248Offset12004);
  if (!result.block_identity) {
    result.reason = "block_address_unrepresentable";
    return result;
  }
  const auto block = *result.block_identity;
  result.data_identity = Copy<std::uintptr_t>(bindings, block, 0);
  result.capacity_i32 = Copy<std::int32_t>(bindings, block, 8);
  result.count_i32 = Copy<std::int32_t>(bindings, block, 0xC);
  result.allocator_identity = Copy<std::uintptr_t>(bindings, block, 0x10);
  result.allocator_dispatch_vtable_identity =
      Copy<std::uintptr_t>(bindings, block, 0x18);
  if (!result.count_i32) {
    result.reason = "payload_count_unread";
    return result;
  }
  if (*result.count_i32 < 0) {
    result.reason = "payload_count_negative";
    return result;
  }
  if (*result.count_i32 == 0) {
    result.ordered_payload_raw64.emplace();
    result.payload_ready = true;
    return result;
  }
  if (!result.data_identity) {
    result.reason = "payload_data_identity_unread";
    return result;
  }
  if (*result.data_identity == 0) {
    result.reason = "positive_payload_data_absent";
    return result;
  }
  const auto count = static_cast<std::size_t>(*result.count_i32);
  if (count > std::numeric_limits<std::size_t>::max() / sizeof(std::uint64_t)) {
    result.reason = "payload_byte_count_unrepresentable";
    return result;
  }
  const auto bytes = count * sizeof(std::uint64_t);
  if (!Add(*result.data_identity, bytes - 1)) {
    result.reason = "payload_end_address_unrepresentable";
    return result;
  }
  try {
    std::vector<std::uint64_t> values(count);
    if (!bindings.read || !bindings.read(bindings.read_context,
                                        *result.data_identity,
                                        values.data(), bytes)) {
      result.reason = "ordered_payload_unread";
      return result;
    }
    result.ordered_payload_raw64 = std::move(values);
  } catch (const std::bad_alloc &) {
    result.reason = "payload_copy_allocation_failed";
    return result;
  } catch (const std::length_error &) {
    result.reason = "payload_copy_size_unrepresentable";
    return result;
  }
  result.payload_ready = true;
  return result;
}

PersonTransferBlock248Postimage12004 ComparePersonTransferBlock24812004(
    const PersonInstalledTransferStage12004 &transfer,
    const PersonTransferBlock248Snapshot12004 &pre_a,
    const PersonTransferBlock248Snapshot12004 &pre_b,
    const PersonTransferBlock248Snapshot12004 &post_a,
    const PersonTransferBlock248Snapshot12004 &post_b) {
  PersonTransferBlock248Postimage12004 result;
  result.original_transfer_returned = transfer.observed &&
      transfer.original_called && transfer.original_returned;
  result.copied_model_pair_matches_transfer =
      transfer.model_a_identity != 0 && transfer.model_b_identity != 0 &&
      pre_a.model_identity == transfer.model_a_identity &&
      post_a.model_identity == transfer.model_a_identity &&
      pre_b.model_identity == transfer.model_b_identity &&
      post_b.model_identity == transfer.model_b_identity;
  if (transfer.event_clock_and_thread_match &&
      transfer.completion_ordered_after_begin) {
    result.completion_event_order_proven =
        *transfer.event_clock_and_thread_match &&
        *transfer.completion_ordered_after_begin;
  }
  if (!result.original_transfer_returned) {
    result.reason = "original_transfer_return_unobserved";
    return result;
  }
  if (!result.copied_model_pair_matches_transfer) {
    result.reason = "copied_model_pair_differs_from_transfer";
    return result;
  }
  result.post_a_equals_pre_b = PayloadEqual(post_a, pre_b);
  result.post_b_equals_pre_a = PayloadEqual(post_b, pre_a);
  if (result.post_a_equals_pre_b && result.post_b_equals_pre_a) {
    result.two_way_payload_equality = *result.post_a_equals_pre_b &&
                                     *result.post_b_equals_pre_a;
    result.payload_comparison_ready = true;
  } else {
    result.reason = "one_or_more_ordered_payloads_unread";
  }
  return result;
}

} // namespace xar::ck3_12004
