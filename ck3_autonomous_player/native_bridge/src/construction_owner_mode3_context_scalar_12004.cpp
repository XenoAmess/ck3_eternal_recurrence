#include "xar_bridge/construction_owner_mode3_context_scalar_12004.hpp"

#include <bit>
#include <limits>
#include <utility>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

ContextScalarResultV1 Unavailable(ContextScalarResultV1 &result,
                                 ContextScalarFailureV1 failure) noexcept {
  result.observed = false;
  result.raw_qword.reset();
  result.failure = failure;
  return std::move(result);
}

bool ReadTitleGlobals(const RawReceiverAccessV1 &access,
                      std::uintptr_t &storage,
                      std::uintptr_t &fallback) noexcept {
  return RawReceiverReadV1(access, access.module_base, 0x5D1DAF8, storage) &&
      RawReceiverReadV1(access, access.module_base, 0x5D1DAE0, fallback);
}

bool ResolveCharacter(const RawReceiverAccessV1 &access,
                       std::uint32_t full_id,
                       std::uintptr_t &selected,
                       bool &matched) noexcept {
  // Actual82458/82612 compare, then82461/8261C independently load the slot.
  std::uintptr_t compared_storage = 0;
  if (!RawReceiverReadV1(access, access.module_base, 0x5C67568,
                        compared_storage)) return false;
  matched = false;
  selected = 0;
  if (compared_storage != 0) {
    std::uintptr_t storage = 0;
    if (!RawReceiverReadV1(access, access.module_base, 0x5C67568, storage) ||
        storage == 0 ||
        !ReadRawReceiverRegistryV1(access, storage, full_id, 0x18, 0,
                                  selected, matched)) return false;
  }
  if (!matched &&
      !RawReceiverReadV1(access, access.module_base, 0x5C67570, selected))
    return false;
  return true;
}

} // namespace

ContextScalarResultV1 ReadContextScalar2C82340V1(
    const RawReceiverAccessV1 &access, std::uintptr_t context,
    std::uint16_t key, std::uintptr_t detail,
    const ReadContextScalarChild2C4D1D0V1 &child,
    std::size_t maximum_occurrences) noexcept {
  ContextScalarResultV1 result{};
  result.context_pointer = context;
  result.key_u16 = key;
  result.detail_pointer = detail;
  if (!access.exact_12004_bound)
    return Unavailable(result, ContextScalarFailureV1::exact_build);
  if (access.read_memory == nullptr)
    return Unavailable(result, ContextScalarFailureV1::read_callback);
  if (detail != 0)
    return Unavailable(result, ContextScalarFailureV1::detail_route);
  try {
    std::int32_t count = 0;
    if (!RawReceiverReadV1(access, context, 0x28,
                          result.collection_data_pointer) ||
        !RawReceiverReadV1(access, context, 0x34, count))
      return Unavailable(result, ContextScalarFailureV1::collection);
    result.collection_count = count;
    if (count < 0 || static_cast<std::size_t>(count) > maximum_occurrences)
      return Unavailable(result, ContextScalarFailureV1::occurrence_limit);
    if (count != 0) {
      std::uintptr_t end = 0;
      if (!RawReceiverAddV1(result.collection_data_pointer,
                            static_cast<std::size_t>(count) * 8, end))
        return Unavailable(result, ContextScalarFailureV1::collection);
    }
    std::uintptr_t title_storage = 0;
    std::uintptr_t title_fallback = 0;
    if (count != 0 && !ReadTitleGlobals(access, title_storage, title_fallback))
      return Unavailable(result, ContextScalarFailureV1::title_globals);
    for (std::int32_t index = 0; index < count; ++index) {
      result.occurrences.emplace_back();
      auto &occurrence = result.occurrences.back();
      occurrence.index = static_cast<std::size_t>(index);
      if (!RawReceiverReadV1(access, result.collection_data_pointer,
                            static_cast<std::size_t>(index) * 8,
                            occurrence.referenced_pointer) ||
          !RawReceiverReadV1(access, occurrence.referenced_pointer, 0x738,
                            occurrence.requested_title_full_id))
        return Unavailable(result, ContextScalarFailureV1::title_fields);
      bool matched = false;
      if (!ReadRawReceiverRegistryV1(access, title_storage,
                                    occurrence.requested_title_full_id, 0x10,
                                    title_fallback, occurrence.title_pointer,
                                    matched))
        return Unavailable(result, ContextScalarFailureV1::title_registry);
      if (!RawReceiverReadV1(access, occurrence.title_pointer, 0x130,
                            occurrence.title_branch_byte))
        return Unavailable(result, ContextScalarFailureV1::title_fields);
      std::uint32_t candidate = 0;
      bool first_title_candidate = false;
      if (occurrence.title_branch_byte != 0) {
        std::uint32_t character_id = 0;
        std::uintptr_t character = 0;
        if (!RawReceiverReadV1(access, occurrence.title_pointer, 0x128,
                              character_id))
          return Unavailable(result, ContextScalarFailureV1::title_fields);
        occurrence.character_full_id = character_id;
        if (!ResolveCharacter(access, character_id, character, matched))
          return Unavailable(result, ContextScalarFailureV1::character_registry);
        occurrence.character_pointer = character;
        std::uintptr_t domain = 0;
        if (!RawReceiverReadV1(access, character, 0x1C0, domain))
          return Unavailable(result, ContextScalarFailureV1::character_fields);
        occurrence.domain_pointer = domain;
        if (domain == 0) {
          first_title_candidate = true;
        } else if (!RawReceiverReadV1(access, domain, 0x1B8, candidate)) {
          return Unavailable(result, ContextScalarFailureV1::character_fields);
        }
      } else {
        std::uint32_t secondary_id = 0;
        std::uintptr_t secondary = 0;
        if (!RawReceiverReadV1(access, occurrence.title_pointer, 0x12C,
                              secondary_id))
          return Unavailable(result, ContextScalarFailureV1::title_fields);
        occurrence.secondary_title_full_id = secondary_id;
        if (!ReadRawReceiverRegistryV1(access, title_storage, secondary_id,
                                      0x10, title_fallback, secondary, matched))
          return Unavailable(result, ContextScalarFailureV1::title_registry);
        occurrence.secondary_title_pointer = secondary;
        if (!RawReceiverReadV1(access, secondary, 0x128, candidate))
          return Unavailable(result, ContextScalarFailureV1::title_fields);
      }
      if (first_title_candidate || candidate == 0xFFFFFFFFu) {
        occurrence.used_first_title_candidate = true;
        if (!RawReceiverReadV1(access, occurrence.title_pointer, 0x128,
                              candidate))
          return Unavailable(result, ContextScalarFailureV1::title_fields);
      }
      occurrence.candidate_full_id = candidate;
      if (candidate == 0xFFFFFFFFu) {
        occurrence.skipped_sentinel = true;
        continue; // actual82501 ->825E2 skips825D4/DB global reloads.
      }
      // Reuse49's closed880430 equality proposition. No compiler/native
      // dispatch is invoked and high generation bits participate in equality.
      std::size_t unique_index = 0;
      for (; unique_index < result.ordered_unique_full_ids.size(); ++unique_index)
        if (result.ordered_unique_full_ids[unique_index] == candidate) break;
      if (unique_index == result.ordered_unique_full_ids.size())
        result.ordered_unique_full_ids.push_back(candidate);
      occurrence.unique_index = unique_index;
      if (!ReadTitleGlobals(access, title_storage, title_fallback))
        return Unavailable(result, ContextScalarFailureV1::title_globals);
    }
    std::uint64_t sum = 0;
    for (const auto full_id : result.ordered_unique_full_ids) {
      result.child_operands.emplace_back();
      auto &operand = result.child_operands.back();
      operand.requested_character_full_id = full_id;
      if (!ResolveCharacter(access, full_id, operand.character_pointer,
                            operand.registry_matched))
        return Unavailable(result, ContextScalarFailureV1::character_registry);
      if (!child.actual_12004_source_closed || child.read_raw_qword == nullptr)
        return Unavailable(result, ContextScalarFailureV1::child_unavailable);
      std::int64_t value = 0;
      if (!child.read_raw_qword(child.context, access, operand.character_pointer,
                                key, detail, 100000, value))
        return Unavailable(result, ContextScalarFailureV1::child_unavailable);
      operand.raw_qword = value;
      sum += std::bit_cast<std::uint64_t>(value);
    }
    result.raw_qword = std::bit_cast<std::int64_t>(sum);
    result.observed = true;
    return result;
  } catch (...) {
    return Unavailable(result, ContextScalarFailureV1::allocation);
  }
}

} // namespace xar::ck3_12004::construction_owner_mode3
