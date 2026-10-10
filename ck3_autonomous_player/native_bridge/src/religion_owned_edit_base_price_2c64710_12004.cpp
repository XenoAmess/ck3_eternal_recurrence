#include "xar_bridge/religion_owned_edit_base_price_2c64710_12004.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {
namespace raw = construction_owner_mode3;
static_assert(sizeof(std::uintptr_t) == 8, "Actual12004 requires x64 QWORDs");

template <typename T>
bool Read(const OwnedEditReadAccess12004 &access, std::uintptr_t base,
          std::size_t offset, T &value) noexcept {
  std::uintptr_t address = 0;
  if (access.read_memory == nullptr ||
      !raw::RawReceiverAddV1(base, offset, address)) return false;
  try {
    return access.read_memory(access.context,
        reinterpret_cast<const void *>(address), &value, sizeof(value));
  } catch (...) {
    return false;
  }
}

bool ValidExtent(std::uintptr_t pointer, std::size_t entries) noexcept {
  return entries <= std::numeric_limits<std::uintptr_t>::max() / 8 &&
      entries * std::uintptr_t{8} <=
          std::numeric_limits<std::uintptr_t>::max() - pointer &&
      (entries == 0 || pointer != 0);
}

std::uintptr_t NativeEnd(std::uintptr_t pointer, std::int32_t count) noexcept {
  return pointer + static_cast<std::uintptr_t>(static_cast<std::int64_t>(count)) *
      std::uintptr_t{8};
}

std::int64_t SignedBits(std::uint64_t bits) noexcept {
  std::int64_t value = 0;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

bool SecondMembership(const OwnedEditBasePriceBindings12004 &bindings,
                      OwnedEditPriceContribution12004 &row,
                      OwnedEditBasePriceFailure12004 &failure) {
  const auto collection = row.current_collection_identity;
  // Actual2C665EB..F2 reads pointer before signed count.
  std::uintptr_t pointer = 0;
  std::int32_t count = 0;
  if (!Read(bindings.access, collection, 0, pointer) ||
      !Read(bindings.access, collection, 12, count)) {
    failure = OwnedEditBasePriceFailure12004::second_membership_header;
    return false;
  }
  if (count < 0) {
    failure = OwnedEditBasePriceFailure12004::negative_membership_count;
    return false;
  }
  const auto entries = static_cast<std::size_t>(count);
  if (entries > bindings.maximum_entries) {
    failure = OwnedEditBasePriceFailure12004::copy_bound;
    return false;
  }
  if (!ValidExtent(pointer, entries)) {
    failure = OwnedEditBasePriceFailure12004::membership_extent;
    return false;
  }
  std::vector<std::uint64_t> values;
  values.reserve(entries);
  for (std::size_t index = 0; index < entries; ++index) {
    std::uint64_t value = 0;
    if (!Read(bindings.access, pointer, index * 8, value)) {
      failure = OwnedEditBasePriceFailure12004::membership_element;
      return false;
    }
    values.push_back(value);
  }
  const auto found = FindCompleteQwordIteratorA11F6012004(
      values, true, pointer, NativeEnd(pointer, count), row.definition_qword);
  if (!found) {
    failure = OwnedEditBasePriceFailure12004::second_membership_model;
    return false;
  }
  row.membership_iterator_raw = *found;
  // Actual2C66603..18 reloads count then pointer. Preserve final endpoint
  // arithmetic separately; an observed header change is not a false result.
  std::int32_t reloaded_count = 0;
  std::uintptr_t reloaded_pointer = 0;
  if (!Read(bindings.access, collection, 12, reloaded_count) ||
      !Read(bindings.access, collection, 0, reloaded_pointer)) {
    failure = OwnedEditBasePriceFailure12004::second_membership_reload;
    return false;
  }
  const auto end = NativeEnd(reloaded_pointer, reloaded_count);
  row.membership_reloaded_end_raw = end;
  row.skip = *found != end && *found != 0;
  return true;
}
} // namespace

OwnedEditBasePrice12004 ReadOwnedEditBasePrice2C6471012004(
    const OwnedEditBasePriceBindings12004 &bindings, std::uintptr_t draft,
    std::uintptr_t current_rite, std::uint64_t revision) noexcept {
  OwnedEditBasePrice12004 result{};
  result.draft_identity = draft;
  result.current_rite_identity = current_rite;
  result.unchanged_snapshot_revision = revision;
  if (!bindings.access.exact_12004_bound) {
    result.failure = OwnedEditBasePriceFailure12004::exact_build;
    return result;
  }
  if (bindings.access.read_memory == nullptr) {
    result.failure = OwnedEditBasePriceFailure12004::read_callback;
    return result;
  }
  try {
    for (std::size_t array_index = 0; array_index < 2; ++array_index) {
      const bool first = array_index == 0;
      result.reached_array = first ? OwnedEditPriceArray12004::first :
                                    OwnedEditPriceArray12004::second;
      auto &header = first ? result.first_header : result.second_header;
      std::uintptr_t pointer = 0;
      std::int32_t count = 0;
      // Literal first2C6481B/1F and second2C64A0C/10 load pointer then count.
      if (!Read(bindings.access, draft, first ? 8 : 0x50, pointer)) {
        result.failure = OwnedEditBasePriceFailure12004::draft_header;
        return result;
      }
      header.pointer_raw = pointer;
      if (!Read(bindings.access, draft, first ? 0x14 : 0x5C, count)) {
        result.failure = OwnedEditBasePriceFailure12004::draft_header;
        return result;
      }
      header.count_raw = count;
      if (count < 0) {
        result.failure = OwnedEditBasePriceFailure12004::negative_draft_count;
        return result;
      }
      const auto entries = static_cast<std::size_t>(count);
      if (entries > bindings.maximum_entries) {
        result.failure = OwnedEditBasePriceFailure12004::copy_bound;
        return result;
      }
      if (!ValidExtent(pointer, entries)) {
        result.failure = OwnedEditBasePriceFailure12004::draft_extent;
        return result;
      }
      for (std::size_t index = 0; index < entries; ++index) {
        OwnedEditPriceContribution12004 row{};
        row.array = result.reached_array;
        row.index = index;
        if (!Read(bindings.access, pointer, index * 8, row.definition_qword)) {
          result.failure = OwnedEditBasePriceFailure12004::draft_element;
          return result;
        }
        result.reached_occurrences.push_back(row);
        auto &reached = result.reached_occurrences.back();
        if (!raw::RawReceiverAddV1(current_rite, first ? 0x758 : 0x7A0,
                                  reached.current_collection_identity)) {
          result.failure =
              OwnedEditBasePriceFailure12004::current_collection_address;
          return result;
        }
        if (first) {
          raw::ContextPredicateInputsV1 inputs{};
          inputs.frame_key = revision;
          inputs.first_pointer = static_cast<std::uintptr_t>(row.definition_qword);
          const auto membership = raw::ReadConstructionCollectionPredicateA11CC0V1(
              bindings.access, inputs, reached.current_collection_identity,
              inputs.first_pointer, bindings.maximum_entries);
          reached.membership_iterator_raw = membership.found_pointer;
          reached.membership_reloaded_end_raw = membership.reloaded_end_pointer;
          reached.skip = membership.value;
          if (!reached.skip) {
            result.failure = OwnedEditBasePriceFailure12004::first_membership;
            return result;
          }
        } else if (!SecondMembership(bindings, reached, result.failure)) {
          return result;
        }
        if (*reached.skip) continue;
        const auto scalar = first ? bindings.read_31d9930 : bindings.read_31df3b0;
        void *context = first ? bindings.first_scalar_context :
                                bindings.second_scalar_context;
        std::int32_t eax = 0;
        if (scalar == nullptr ||
            !scalar(context, bindings.access,
                    static_cast<std::uintptr_t>(row.definition_qword),
                    current_rite, revision, eax)) {
          result.failure = first ? OwnedEditBasePriceFailure12004::scalar_31d9930 :
                                   OwnedEditBasePriceFailure12004::scalar_31df3b0;
          return result;
        }
        reached.scalar_native_eax_raw = eax;
        const auto scaled = static_cast<std::int64_t>(eax) * std::int64_t{100000};
        reached.scaled_raw_q64 = scaled;
        result.completed_prefix_sum_bits += static_cast<std::uint64_t>(scaled);
      }
    }
    result.base_price_raw_q64 = SignedBits(result.completed_prefix_sum_bits);
    result.complete = true;
    return result;
  } catch (...) {
    result.failure = OwnedEditBasePriceFailure12004::copy_exception;
    return result;
  }
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
