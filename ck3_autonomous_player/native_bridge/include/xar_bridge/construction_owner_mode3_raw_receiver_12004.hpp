#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>

namespace xar::ck3_12004::construction_owner_mode3 {

struct RawReceiverAccessV1 {
  void *context = nullptr;
  bool (*read_memory)(void *, const void *, void *, std::size_t) = nullptr;
  std::uintptr_t module_base = 0;
  bool exact_12004_bound = false;
};

// Bind only continuation-38d's actual read-only2C42930 memory resolver.
// This ABI takes the same read access and the actual selected Title pointer;
// it is not a native getter ABI. A missing child remains unavailable.
struct ReadActualTitleReturnV1 {
  void *context = nullptr;
  bool (*read_actual_2c42930_return)(void *, const RawReceiverAccessV1 &,
                                   std::uintptr_t,
                                   std::uintptr_t &) noexcept = nullptr;
};

enum class RawReceiverFailureV1 : std::uint8_t {
  none,
  exact_build,
  read_callback,
  province_identity,
  title_globals,
  context,
  title_registry,
  child_return,
  child_guard,
  secondary_title,
  character_registry,
};

enum class RawReceiverRouteV1 : std::uint8_t {
  unavailable,
  direct_child,
  character_registry,
  character_fallback,
};

// These are raw pointers, source IDs and source branch observations. The
// returned object is an operand of2468DA0, without attributed holder/yield.
struct AggregateRawReceiverV1 {
  bool observed = false;
  RawReceiverFailureV1 failure = RawReceiverFailureV1::none;
  RawReceiverRouteV1 route = RawReceiverRouteV1::unavailable;
  std::int32_t province_id = -1;
  std::uintptr_t province_pointer = 0;
  std::uintptr_t slots_pointer = 0;
  std::uintptr_t context_pointer = 0;
  std::uintptr_t title_storage_pointer = 0;
  std::uintptr_t title_fallback_pointer = 0;
  bool context_title_id_observed = false;
  std::uint32_t context_title_id_raw = 0;
  std::uintptr_t first_title_pointer = 0;
  std::uintptr_t child_return_pointer = 0;
  bool child_id_observed = false;
  std::uint32_t child_id_raw = 0;
  std::uint32_t child_tag_raw = 0;
  bool secondary_title_id_observed = false;
  std::uint32_t secondary_title_id_raw = 0;
  std::uintptr_t secondary_title_pointer = 0;
  bool character_id_observed = false;
  std::uint32_t character_id_raw = 0;
  std::uintptr_t character_storage_pointer = 0;
  std::uintptr_t returned_receiver_pointer = 0;
  bool returned_identity_observed = false;
  std::uint32_t returned_id_raw = 0;
  std::uint32_t returned_tag_raw = 0;
};

inline bool RawReceiverAddV1(std::uintptr_t base, std::size_t offset,
                             std::uintptr_t &address) noexcept {
  if (base == 0 || offset >
      std::numeric_limits<std::uintptr_t>::max() - base) return false;
  address = base + offset;
  return true;
}

template <typename T>
inline bool RawReceiverReadV1(const RawReceiverAccessV1 &access,
                              std::uintptr_t base, std::size_t offset,
                              T &value) noexcept {
  std::uintptr_t address = 0;
  return access.read_memory != nullptr &&
      RawReceiverAddV1(base, offset, address) &&
      access.read_memory(access.context,
                         reinterpret_cast<const void *>(address),
                         &value, sizeof(value));
}

// Actual2467660 registry rule: uint32 low24 index, stride16 pointer+8,
// full uint32 identity. Zero/high-bit/all-ones IDs have no added ID gate.
inline bool ReadRawReceiverRegistryV1(const RawReceiverAccessV1 &access,
                                      std::uintptr_t storage,
                                      std::uint32_t full_id,
                                      std::size_t identity_offset,
                                      std::uintptr_t fallback,
                                      std::uintptr_t &selected,
                                      bool &matched) noexcept {
  selected = fallback;
  matched = false;
  if (storage == 0) return true;
  const std::uint32_t index = full_id & 0x00FFFFFFu;
  std::uint32_t count = 0;
  if (!RawReceiverReadV1(access, storage, 0x2C, count)) return false;
  if (index >= count) return true;
  std::uintptr_t table = 0;
  std::uintptr_t object = 0;
  std::uint32_t observed_id = 0;
  if (!RawReceiverReadV1(access, storage, 0x20, table) ||
      !RawReceiverReadV1(access, table,
                        static_cast<std::size_t>(index) * 16 + 8, object))
    return false;
  if (object == 0) return true;
  if (!RawReceiverReadV1(access, object, identity_offset, observed_id))
    return false;
  if (observed_id == full_id) {
    selected = object;
    matched = true;
  }
  return true;
}

inline void ObserveRawReceiverIdentityV1(
    const RawReceiverAccessV1 &access,
    AggregateRawReceiverV1 &result) noexcept {
  // The fallback return has no tag/full-ID guard in2467660. Metadata is
  // optional evidence, never a rejection of its actual returned pointer.
  result.returned_identity_observed =
      RawReceiverReadV1(access, result.returned_receiver_pointer, 0x18,
                        result.returned_id_raw) &&
      RawReceiverReadV1(access, result.returned_receiver_pointer, 0x1C,
                        result.returned_tag_raw);
}

inline AggregateRawReceiverV1 ReadAggregateRawReceiverFromSlotsV1(
    const RawReceiverAccessV1 &access, std::uintptr_t slots,
    const ReadActualTitleReturnV1 &child) noexcept {
  AggregateRawReceiverV1 result{};
  result.slots_pointer = slots;
  const auto fail = [&](RawReceiverFailureV1 failure) {
    result.failure = failure;
    return result;
  };
  if (!access.exact_12004_bound)
    return fail(RawReceiverFailureV1::exact_build);
  if (access.read_memory == nullptr)
    return fail(RawReceiverFailureV1::read_callback);
  if (!RawReceiverReadV1(access, access.module_base, 0x5D1DAF8,
                        result.title_storage_pointer) ||
      !RawReceiverReadV1(access, access.module_base, 0x5D1DAE0,
                        result.title_fallback_pointer))
    return fail(RawReceiverFailureV1::title_globals);
  result.first_title_pointer = result.title_fallback_pointer;
  bool matched = false;
  if (result.title_storage_pointer != 0) {
    if (!RawReceiverReadV1(access, slots, 0xF0, result.context_pointer) ||
        !RawReceiverReadV1(access, result.context_pointer, 0x738,
                          result.context_title_id_raw))
      return fail(RawReceiverFailureV1::context);
    result.context_title_id_observed = true;
    if (!ReadRawReceiverRegistryV1(access, result.title_storage_pointer,
                                  result.context_title_id_raw, 0x10,
                                  result.title_fallback_pointer,
                                  result.first_title_pointer, matched))
      return fail(RawReceiverFailureV1::title_registry);
  }
  if (child.read_actual_2c42930_return == nullptr ||
      !child.read_actual_2c42930_return(child.context, access,
                                      result.first_title_pointer,
                                      result.child_return_pointer))
    return fail(RawReceiverFailureV1::child_return);
  if (!RawReceiverReadV1(access, result.child_return_pointer, 0x1C,
                        result.child_tag_raw))
    return fail(RawReceiverFailureV1::child_guard);
  if (result.child_tag_raw == 0x43686172u) {
    if (!RawReceiverReadV1(access, result.child_return_pointer, 0x18,
                          result.child_id_raw))
      return fail(RawReceiverFailureV1::child_guard);
    result.child_id_observed = true;
    if (result.child_id_raw != 0xFFFFFFFFu) {
      result.route = RawReceiverRouteV1::direct_child;
      result.returned_receiver_pointer = result.child_return_pointer;
      result.returned_id_raw = result.child_id_raw;
      result.returned_tag_raw = result.child_tag_raw;
      result.returned_identity_observed = true;
      result.observed = true;
      return result;
    }
  }
  // R11 is the initially loaded fallback, not the first selected Title.
  result.secondary_title_pointer = result.title_fallback_pointer;
  if (result.title_storage_pointer != 0) {
    if (!RawReceiverReadV1(access, result.first_title_pointer, 0xE8,
                          result.secondary_title_id_raw))
      return fail(RawReceiverFailureV1::secondary_title);
    result.secondary_title_id_observed = true;
    if (!ReadRawReceiverRegistryV1(access, result.title_storage_pointer,
                                  result.secondary_title_id_raw, 0x10,
                                  result.title_fallback_pointer,
                                  result.secondary_title_pointer, matched))
      return fail(RawReceiverFailureV1::secondary_title);
  }
  if (!RawReceiverReadV1(access, access.module_base, 0x5C67568,
                        result.character_storage_pointer))
    return fail(RawReceiverFailureV1::character_registry);
  matched = false;
  if (result.character_storage_pointer != 0) {
    if (!RawReceiverReadV1(access, result.secondary_title_pointer, 0x128,
                          result.character_id_raw))
      return fail(RawReceiverFailureV1::character_registry);
    result.character_id_observed = true;
    if (!ReadRawReceiverRegistryV1(access, result.character_storage_pointer,
                                  result.character_id_raw, 0x18, 0,
                                  result.returned_receiver_pointer, matched))
      return fail(RawReceiverFailureV1::character_registry);
  }
  if (matched) {
    result.route = RawReceiverRouteV1::character_registry;
  } else {
    if (!RawReceiverReadV1(access, access.module_base, 0x5C67570,
                          result.returned_receiver_pointer))
      return fail(RawReceiverFailureV1::character_registry);
    result.route = RawReceiverRouteV1::character_fallback;
  }
  ObserveRawReceiverIdentityV1(access, result);
  result.observed = true;
  return result;
}

// Province identity is the already used03 consumer binding. It does not
// impose an additional validity rule on source uint32 Title/Character IDs.
inline AggregateRawReceiverV1 ReadAggregateRawReceiverV1(
    const RawReceiverAccessV1 &access, std::uintptr_t province,
    std::int32_t expected_province_id,
    const ReadActualTitleReturnV1 &child) noexcept {
  AggregateRawReceiverV1 result{};
  result.province_pointer = province;
  result.province_id = expected_province_id;
  std::int32_t observed_id = -1;
  if (!access.exact_12004_bound) {
    result.failure = RawReceiverFailureV1::exact_build;
    return result;
  }
  if (access.read_memory == nullptr) {
    result.failure = RawReceiverFailureV1::read_callback;
    return result;
  }
  std::uintptr_t slots = 0;
  if (expected_province_id <= 0 ||
      !RawReceiverReadV1(access, province, 0x10, observed_id) ||
      observed_id != expected_province_id ||
      !RawReceiverAddV1(province, 0x620, slots)) {
    result.failure = RawReceiverFailureV1::province_identity;
    return result;
  }
  result = ReadAggregateRawReceiverFromSlotsV1(access, slots, child);
  result.province_pointer = province;
  result.province_id = expected_province_id;
  return result;
}

} // namespace xar::ck3_12004::construction_owner_mode3
