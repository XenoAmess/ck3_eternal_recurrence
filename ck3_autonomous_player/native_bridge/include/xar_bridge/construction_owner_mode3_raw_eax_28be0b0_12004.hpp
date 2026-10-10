#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::string_view kRaw28BE0B0SourcePin12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::uint32_t kRaw28BE0B0BeginRva12004 = 0x28BE0B0;
inline constexpr std::uint32_t kRaw28BE0B0EndRva12004 = 0x28BE106;
inline constexpr std::uint32_t kRaw28BE0B0CallerRva12004 = 0x2468F77;

enum class Raw28BE0B0Failure12004 : std::uint8_t {
  none,
  exact_build,
  read_callback,
  receiver_carrier,
  threshold_count,
  carrier_cap,
  carrier_score,
  threshold_array,
  threshold_element,
};

// Observed means all memory demanded by the actual branch was copied and
// its EAX was projected. It does not mean the native producer was invoked.
struct Raw28BE0B0Eax12004 {
  bool observed = false;
  Raw28BE0B0Failure12004 failure = Raw28BE0B0Failure12004::none;
  std::uintptr_t receiver_pointer = 0;
  std::uint64_t snapshot_revision = 0;
  std::optional<std::uintptr_t> carrier_pointer;
  std::optional<std::int32_t> threshold_count;
  std::optional<std::int32_t> cap_signed;
  std::optional<std::int64_t> score_signed;
  std::optional<std::uintptr_t> threshold_array_pointer;
  std::uint32_t threshold_reads = 0;
  std::optional<std::int64_t> last_threshold_signed;
  std::optional<std::int32_t> eax_signed;
  std::uint32_t source_return_rva = 0;
  bool observed_native_producer_call = false;
};

// RCX is the actual2467660 returned receiver supplied by the same paused
// query. No Character identity, Model, property key or title is demanded.
inline Raw28BE0B0Eax12004 ReadRaw28BE0B0Eax12004(
    const RawReceiverAccessV1 &access, std::uintptr_t actual_receiver,
    std::uint64_t snapshot_revision) noexcept {
  Raw28BE0B0Eax12004 result{};
  result.receiver_pointer = actual_receiver;
  result.snapshot_revision = snapshot_revision;
  const auto fail = [&](Raw28BE0B0Failure12004 failure) {
    result.failure = failure;
    return result;
  };
  if (!access.exact_12004_bound)
    return fail(Raw28BE0B0Failure12004::exact_build);
  if (access.read_memory == nullptr)
    return fail(Raw28BE0B0Failure12004::read_callback);
  std::uintptr_t carrier = 0;
  if (!RawReceiverReadV1(access, actual_receiver, 0x1B0, carrier))
    return fail(Raw28BE0B0Failure12004::receiver_carrier);
  result.carrier_pointer = carrier;
  // The load placed zero in RAX; the actual null branch returns at28BE105.
  if (carrier == 0) {
    result.eax_signed = 0;
    result.source_return_rva = 0x28BE105;
    result.observed = true;
    return result;
  }
  std::int32_t count = 0;
  std::int32_t cap = 0;
  std::int64_t score = 0;
  // Actual load order is count -> cap -> score, even for count <= 0.
  if (!RawReceiverReadV1(access, access.module_base, 0x54582E4, count))
    return fail(Raw28BE0B0Failure12004::threshold_count);
  result.threshold_count = count;
  if (!RawReceiverReadV1(access, carrier, 0x120, cap))
    return fail(Raw28BE0B0Failure12004::carrier_cap);
  result.cap_signed = cap;
  if (!RawReceiverReadV1(access, carrier, 0x118, score))
    return fail(Raw28BE0B0Failure12004::carrier_score);
  result.score_signed = score;
  std::int32_t rank = 0;
  if (count > 0) {
    std::uintptr_t thresholds = 0;
    if (!RawReceiverReadV1(access, access.module_base, 0x54582D8, thresholds))
      return fail(Raw28BE0B0Failure12004::threshold_array);
    result.threshold_array_pointer = thresholds;
    while (rank < count) {
      std::int64_t threshold = 0;
      const auto index = static_cast<std::size_t>(rank);
      if (index > std::numeric_limits<std::size_t>::max() /
                      sizeof(std::int64_t) ||
          !RawReceiverReadV1(access, thresholds,
                             index * sizeof(std::int64_t), threshold))
        return fail(Raw28BE0B0Failure12004::threshold_element);
      ++result.threshold_reads;
      result.last_threshold_signed = threshold;
      // Signed compare, ordered prefix: equality increments the rank.
      if (score < threshold) break;
      ++rank;
    }
  }
  // Negative cap is ignored; nonnegative cap returns signed min(rank, cap).
  result.eax_signed = cap >= 0 && cap < rank ? cap : rank;
  result.source_return_rva = 0x28BE104;
  result.observed = true;
  return result;
}

// Exact Mode3SignedEaxChildV1 software-reader ABI; context is not a getter.
inline bool ReadRaw28BE0B0EaxAdapter12004(
    void *, const RawReceiverAccessV1 &access,
    std::uintptr_t actual_receiver, std::uint64_t snapshot_revision,
    std::int32_t &out) noexcept {
  const auto result =
      ReadRaw28BE0B0Eax12004(access, actual_receiver, snapshot_revision);
  if (!result.observed || !result.eax_signed.has_value()) return false;
  out = *result.eax_signed;
  return true;
}

} // namespace xar::ck3_12004::construction_owner_mode3
