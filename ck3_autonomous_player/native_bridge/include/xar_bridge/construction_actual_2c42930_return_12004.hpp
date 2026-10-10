#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>

namespace xar::ck3_12004::construction_owner_mode3 {

// This child callback is continuation-22c's source-derived read-only
// ReadTitleSelectedFullIdAdapter12004, never the native function at2C42820.
struct RawTitleReturnAccessV1 {
  void *context = nullptr;
  bool (*read_memory)(void *, const void *, void *, std::size_t) = nullptr;
  std::uintptr_t module_base = 0;
  bool exact_12004_bound = false;
  void *child_context = nullptr;
  bool (*read_2c42820_out)(void *, std::uintptr_t,
                          std::uint32_t &) noexcept = nullptr;
};

enum class ActualTitleReturnFailureV1 : std::uint8_t {
  none,
  exact_build,
  read_callback,
  child_callback,
  child_out,
  title_128,
  registry_global,
  registry_count,
  registry_table,
  registry_candidate,
  candidate_identity,
  fallback_global,
};

enum class ActualTitleReturnRouteV1 : std::uint8_t {
  unavailable,
  character_registry,
  character_fallback,
};

enum class ActualTitleReturnFallbackV1 : std::uint8_t {
  none,
  registry_null,
  index_out_of_range,
  candidate_null,
  generation_mismatch,
};

// Values are copied raw inputs and the returned pointer of the actual95B
// source. There is no holder, tax, yield, magic or extra ID validity rule.
// Flags distinguish unread fields from observed zero/all-ones values.
struct ActualTitleReturnV1 {
  bool observed = false;
  ActualTitleReturnFailureV1 failure = ActualTitleReturnFailureV1::none;
  ActualTitleReturnRouteV1 route = ActualTitleReturnRouteV1::unavailable;
  ActualTitleReturnFallbackV1 fallback = ActualTitleReturnFallbackV1::none;
  std::uintptr_t title_pointer = 0;
  bool child_out_observed = false;
  std::uint32_t child_out_full_id_u32 = 0;
  bool used_title_128_fallback = false;
  bool requested_full_id_observed = false;
  std::uint32_t requested_full_id_u32 = 0;
  std::uint32_t registry_index_u32 = 0;
  bool registry_pointer_observed = false;
  std::uintptr_t registry_pointer = 0;
  bool registry_count_observed = false;
  std::uint32_t registry_count_u32 = 0;
  bool registry_table_observed = false;
  std::uintptr_t registry_table_pointer = 0;
  bool registry_candidate_observed = false;
  std::uintptr_t registry_candidate_pointer = 0;
  bool candidate_full_id_observed = false;
  std::uint32_t candidate_full_id_u32 = 0;
  bool used_character_fallback = false;
  std::uintptr_t returned_pointer = 0;
};

inline bool ActualTitleReturnAddV1(std::uintptr_t base, std::size_t offset,
                                  std::uintptr_t &address) noexcept {
  if (base == 0 || offset >
      (std::numeric_limits<std::uintptr_t>::max)() - base) return false;
  address = base + offset;
  return true;
}

template <typename T>
inline bool ActualTitleReturnReadV1(const RawTitleReturnAccessV1 &access,
                                   std::uintptr_t base, std::size_t offset,
                                   T &value) noexcept {
  std::uintptr_t address = 0;
  return access.read_memory != nullptr &&
      ActualTitleReturnAddV1(base, offset, address) &&
      access.read_memory(access.context,
                         reinterpret_cast<const void *>(address),
                         &value, sizeof(value));
}

// Actual1.20.0.4 source [2C42930,2C4298F),95B, SHA256
// b6f45709084364156e00538b9fc69be9895627a493317c8ad754d0ba6ca39d11.
// Sole child CALL2C4293F writes uint32 out; the native child RAX is unused.
inline ActualTitleReturnV1 ReadActual2C42930ReturnV1(
    const RawTitleReturnAccessV1 &access,
    std::uintptr_t title) noexcept {
  ActualTitleReturnV1 result{};
  result.title_pointer = title;
  const auto fail = [&](ActualTitleReturnFailureV1 failure) {
    result.failure = failure;
    return result;
  };
  if (!access.exact_12004_bound)
    return fail(ActualTitleReturnFailureV1::exact_build);
  if (access.read_memory == nullptr)
    return fail(ActualTitleReturnFailureV1::read_callback);
  if (access.read_2c42820_out == nullptr)
    return fail(ActualTitleReturnFailureV1::child_callback);
  if (!access.read_2c42820_out(access.child_context, title,
                             result.child_out_full_id_u32))
    return fail(ActualTitleReturnFailureV1::child_out);
  result.child_out_observed = true;
  result.requested_full_id_u32 = result.child_out_full_id_u32;
  if (result.child_out_full_id_u32 == 0xFFFFFFFFu) {
    result.used_title_128_fallback = true;
    if (!ActualTitleReturnReadV1(access, title, 0x128,
                                result.requested_full_id_u32))
      return fail(ActualTitleReturnFailureV1::title_128);
  }
  result.requested_full_id_observed = true;
  result.registry_index_u32 = result.requested_full_id_u32 & 0x00FFFFFFu;
  if (!ActualTitleReturnReadV1(access, access.module_base, 0x5C67568,
                              result.registry_pointer))
    return fail(ActualTitleReturnFailureV1::registry_global);
  result.registry_pointer_observed = true;
  if (result.registry_pointer == 0) {
    result.fallback = ActualTitleReturnFallbackV1::registry_null;
  } else {
    if (!ActualTitleReturnReadV1(access, result.registry_pointer, 0x2C,
                                result.registry_count_u32))
      return fail(ActualTitleReturnFailureV1::registry_count);
    result.registry_count_observed = true;
    if (result.registry_index_u32 >= result.registry_count_u32) {
      result.fallback = ActualTitleReturnFallbackV1::index_out_of_range;
    } else {
      if (!ActualTitleReturnReadV1(access, result.registry_pointer, 0x20,
                                  result.registry_table_pointer))
        return fail(ActualTitleReturnFailureV1::registry_table);
      result.registry_table_observed = true;
      // There is no native table-null fallback. A missing table read stays
      // unavailable rather than becoming the source's fallback branch.
      if (!ActualTitleReturnReadV1(
              access, result.registry_table_pointer,
              static_cast<std::size_t>(result.registry_index_u32) * 16 + 8,
              result.registry_candidate_pointer))
        return fail(ActualTitleReturnFailureV1::registry_candidate);
      result.registry_candidate_observed = true;
      if (result.registry_candidate_pointer == 0) {
        result.fallback = ActualTitleReturnFallbackV1::candidate_null;
      } else {
        if (!ActualTitleReturnReadV1(access,
                                    result.registry_candidate_pointer, 0x18,
                                    result.candidate_full_id_u32))
          return fail(ActualTitleReturnFailureV1::candidate_identity);
        result.candidate_full_id_observed = true;
        if (result.candidate_full_id_u32 == result.requested_full_id_u32) {
          result.route = ActualTitleReturnRouteV1::character_registry;
          result.returned_pointer = result.registry_candidate_pointer;
          result.observed = true;
          return result;
        }
        result.fallback = ActualTitleReturnFallbackV1::generation_mismatch;
      }
    }
  }
  // Source2C42983 reads this global only on an actual fallback branch.
  // The source returns its raw value including zero, without object guards.
  result.used_character_fallback = true;
  if (!ActualTitleReturnReadV1(access, access.module_base, 0x5C67570,
                              result.returned_pointer))
    return fail(ActualTitleReturnFailureV1::fallback_global);
  result.route = ActualTitleReturnRouteV1::character_fallback;
  result.observed = true;
  return result;
}

} // namespace xar::ck3_12004::construction_owner_mode3
