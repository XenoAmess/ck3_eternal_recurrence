#include "xar_bridge/construction_owner_mode3_m4_12004.hpp"

#include "xar_bridge/m4_count_28b71e0_12004.hpp"
#include "xar_bridge/m4_subobject_predicate_12004.hpp"
#include "xar_bridge/returned_selector_28c2df0_12004.hpp"

#include <bit>
#include <limits>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

constexpr std::string_view kActualSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

bool ReadBytes(const RawReceiverAccessV1 &access, std::uintptr_t source,
               void *destination, std::size_t bytes) noexcept {
  if (access.read_memory == nullptr || source == 0 || destination == nullptr ||
      bytes > std::numeric_limits<std::uintptr_t>::max() - source)
    return false;
  try {
    return access.read_memory(access.context,
        reinterpret_cast<const void *>(source), destination, bytes);
  } catch (...) {
    return false;
  }
}

template <typename T>
bool Copy(const RawReceiverAccessV1 &access, std::uintptr_t base,
          std::size_t offset, T &out) noexcept {
  std::uintptr_t source = 0;
  return RawReceiverAddV1(base, offset, source) &&
      ReadBytes(access, source, &out, sizeof(out));
}

bool SelectorCopy(void *context, std::uintptr_t source, void *destination,
                  std::size_t bytes) noexcept {
  return context != nullptr && ReadBytes(
      *static_cast<const RawReceiverAccessV1 *>(context), source,
      destination, bytes);
}

// The same literal low24/stride16/fullID lookup occurs in the two owned count
// functions. The default pointer is loaded only when the actual lookup fails.
bool Registry(const RawReceiverAccessV1 &access, std::uintptr_t storage,
              std::uint32_t full_id, std::size_t identity_offset,
              std::size_t fallback_global, std::uintptr_t &selected,
              bool &matched) noexcept {
  matched = false;
  if (storage != 0) {
    std::uint32_t count = 0;
    if (!Copy(access, storage, 0x2C, count)) return false;
    const std::uint32_t index = full_id & 0x00FFFFFFu;
    if (index < count) {
      std::uintptr_t table = 0, candidate = 0;
      if (!Copy(access, storage, 0x20, table) ||
          !Copy(access, table, static_cast<std::size_t>(index) * 16 + 8,
                candidate)) return false;
      if (candidate != 0) {
        std::uint32_t observed = 0;
        if (!Copy(access, candidate, identity_offset, observed)) return false;
        if (observed == full_id) {
          selected = candidate;
          matched = true;
          return true;
        }
      }
    }
  }
  return Copy(access, access.module_base, fallback_global, selected);
}

bool Predicate7370(const RawReceiverAccessV1 &access,
                   std::uint64_t snapshot_revision,
                   const Mode3M4ReadBindingsV1 &bindings,
                   Mode3M4OccurrenceV1 &occurrence) noexcept {
  const auto unavailable = [&](std::string_view reason) {
    occurrence.unavailable_reason = reason;
    return false;
  };
  const auto observed_false = [&]() {
    occurrence.raw_predicate_byte = std::uint8_t{0};
    occurrence.counted = false;
    return true;
  };
  std::uintptr_t character_storage = 0;
  if (!Copy(access, access.module_base, 0x5C67568, character_storage))
    return unavailable("character_storage_global_unavailable");
  std::uint32_t character_id = 0;
  if (character_storage != 0 &&
      !Copy(access, occurrence.selected_title, 0x128, character_id))
    return unavailable("title_character_full_id_unavailable");
  if (!Registry(access, character_storage, character_id, 0x18, 0x5C67570,
                occurrence.selected_character,
                occurrence.character_registry_matched))
    return unavailable("character_registry_or_fallback_unavailable");

  std::uintptr_t rank_object = 0;
  std::int32_t rank = 0;
  if (!Copy(access, occurrence.selected_title, 0x48, rank_object) ||
      !Copy(access, rank_object, 0x64, rank))
    return unavailable("title_rank_unavailable");
  if (rank > 1) return observed_false();

  // 230F8E0 compares that same rank against2. The caller's signed rank<=1
  // proves its direct Title+338 return; no parent-title loop/getter is run.
  std::uintptr_t direct_rank_object = 0;
  std::int32_t direct_rank = 0;
  if (!Copy(access, occurrence.selected_title, 0x48, direct_rank_object) ||
      !Copy(access, direct_rank_object, 0x64, direct_rank) ||
      direct_rank_object != rank_object || direct_rank != rank)
    return unavailable("direct_province_rank_source_changed");
  if (!Copy(access, occurrence.selected_title, 0x338, occurrence.province))
    return unavailable("title_direct_province_unavailable");
  std::uint32_t province_magic = 0;
  if (!Copy(access, occurrence.province, 0x85C, province_magic))
    return unavailable("province_magic_unavailable");
  if (province_magic != 0x50726F76u) return observed_false();
  std::uint8_t active = 0;
  if (!Copy(access, occurrence.province, 0x628, active))
    return unavailable("province_byte628_unavailable");
  if (active == 0) return observed_false();
  std::uint8_t title_130 = 0;
  if (!Copy(access, occurrence.selected_title, 0x130, title_130))
    return unavailable("title_byte130_unavailable");
  if (title_130 != 0) return observed_false();
  std::uint32_t title_12c = 0;
  if (!Copy(access, occurrence.selected_title, 0x12C, title_12c))
    return unavailable("title_dword12c_unavailable");
  if (title_12c != 0xFFFFFFFFu) return observed_false();

  std::uintptr_t subobject = 0, province_620_pointer = 0;
  if (!RawReceiverAddV1(occurrence.province, 0x620, subobject) ||
      !Copy(access, subobject, 0, province_620_pointer))
    return unavailable("province_subobject_or_qword620_unavailable");
  if (!bindings.subobject_predicate_source_closed ||
      bindings.read_subobject_2c39ee0 == nullptr)
    return unavailable("subobject_predicate_source_unavailable");
  bool subobject_predicate = false;
  if (!bindings.read_subobject_2c39ee0(bindings.predicate_context, access,
                                    subobject, snapshot_revision,
                                    subobject_predicate))
    return unavailable("subobject_predicate_input_unavailable");
  occurrence.subobject_predicate = subobject_predicate;
  if (subobject_predicate) {
    std::uint8_t byte_bc = 0;
    if (!Copy(access, province_620_pointer, 0xBC, byte_bc))
      return unavailable("province620_pointer_bytebc_unavailable");
    if (byte_bc == 0) {
      const auto selector = BindReturnedSelector28C2DF012004(
          access.module_base, "1.20.0.4", kActualSha, SelectorCopy,
          const_cast<RawReceiverAccessV1 *>(&access));
      try {
        const auto returned = ResolveReturnedObject28C2DF012004(
            selector, occurrence.selected_character, snapshot_revision);
        if (!returned.source_ready)
          return unavailable("returned_object_path_unavailable");
        std::uintptr_t returned_418 = 0;
        if (!Copy(access, returned.returned_object, 0x418, returned_418))
          return unavailable("returned_object_field418_unavailable");
        if (returned_418 != province_620_pointer) return observed_false();
      } catch (...) {
        return unavailable("returned_object_copy_failed");
      }
    }
  }
  // The second actual230F8E0 on the same Title reaches the same direct path.
  std::uintptr_t final_province = 0;
  std::uint8_t byte_728 = 0;
  if (!Copy(access, occurrence.selected_title, 0x48, direct_rank_object) ||
      !Copy(access, direct_rank_object, 0x64, direct_rank) ||
      direct_rank_object != rank_object || direct_rank != rank)
    return unavailable("final_direct_province_rank_source_changed");
  if (!Copy(access, occurrence.selected_title, 0x338, final_province) ||
      !Copy(access, final_province, 0x728, byte_728))
    return unavailable("province_byte728_unavailable");
  occurrence.raw_predicate_byte = byte_728;
  occurrence.counted = byte_728 != 0;
  return true;
}

std::int32_t WrappedSubtract(std::int32_t left, std::int32_t right) noexcept {
  const auto bits = std::bit_cast<std::uint32_t>(left) -
                    std::bit_cast<std::uint32_t>(right);
  return std::bit_cast<std::int32_t>(bits);
}

} // namespace

Mode3M4ReadBindingsV1 BindMode3M4ReadonlyChildrenV1() noexcept {
  Mode3M4ReadBindingsV1 result;
  result.read_count_28b71e0 = ReadM4Count28B71E0Adapter12004;
  result.count_71e0_source_closed = true;
  result.read_subobject_2c39ee0 = ReadM4SubobjectPredicateAdapter12004;
  result.subobject_predicate_source_closed = true;
  return result;
}

Mode3M4Count7450V1 ReadMode3M4Count7450V1(
    const RawReceiverAccessV1 &access, std::uintptr_t actual_receiver,
    std::uint64_t snapshot_revision, const Mode3M4ReadBindingsV1 &bindings,
    std::size_t maximum_occurrences) noexcept {
  Mode3M4Count7450V1 result;
  result.actual_receiver = actual_receiver;
  result.snapshot_revision = snapshot_revision;
  const auto unavailable = [&](std::string_view reason) {
    result.unavailable_reason = reason;
  };
  if (!access.exact_12004_bound || access.module_base == 0) {
    unavailable("exact_build_unavailable");
    return result;
  }
  try {
    std::uintptr_t nested = 0, descriptor = 0, data = 0;
    std::int32_t count = 0;
    if (!Copy(access, actual_receiver, 0x1C0, nested)) {
      unavailable("receiver_nested1c0_unavailable");
      return result;
    }
    result.nested_1c0 = nested;
    if (!RawReceiverAddV1(nested != 0 ? nested : access.module_base,
                         nested != 0 ? 0x1E0 : 0x5459C88, descriptor)) {
      unavailable("list_descriptor_unavailable");
      return result;
    }
    result.list_descriptor = descriptor;
    if (!Copy(access, descriptor, 0, data) ||
        !Copy(access, descriptor, 0xC, count)) {
      unavailable("list_header_unavailable");
      return result;
    }
    result.list_data = data;
    result.declared_count = count;
    if (count < 0 || static_cast<std::size_t>(count) > maximum_occurrences) {
      unavailable(count < 0 ? "negative_native_list_extent_unavailable" :
                              "native_list_copy_budget_exceeded");
      return result;
    }
    result.occurrences.reserve(static_cast<std::size_t>(count));
    std::uint32_t counted = 0;
    bool all_observed = true;
    for (std::uint32_t index = 0; index < static_cast<std::uint32_t>(count);
         ++index) {
      Mode3M4OccurrenceV1 occurrence;
      occurrence.stored_index = index;
      if (!Copy(access, data, static_cast<std::size_t>(index) * 4,
                occurrence.raw_full_id)) {
        occurrence.unavailable_reason = "ordered_full_id_unavailable";
      } else {
        std::uintptr_t title_storage = 0;
        if (!Copy(access, access.module_base, 0x5D1DAF8, title_storage) ||
            !Registry(access, title_storage, occurrence.raw_full_id, 0x10,
                      0x5D1DAE0, occurrence.selected_title,
                      occurrence.title_registry_matched)) {
          occurrence.unavailable_reason = "title_registry_or_fallback_unavailable";
        } else {
          Predicate7370(access, snapshot_revision, bindings, occurrence);
        }
      }
      if (!occurrence.counted) {
        all_observed = false;
      } else if (*occurrence.counted) {
        ++counted;
      }
      result.occurrences.push_back(occurrence);
    }
    if (!all_observed) {
      unavailable("ordered_occurrence_predicate_unavailable");
      return result;
    }
    result.signed_eax = std::bit_cast<std::int32_t>(counted);
    result.source_ready = true;
    return result;
  } catch (...) {
    unavailable("owned_occurrence_copy_failed");
    return result;
  }
}

Mode3M4ReductionV1 ReadMode3M4ReductionV1(
    const RawReceiverAccessV1 &access, std::uintptr_t actual_receiver,
    std::uint64_t snapshot_revision,
    const Mode3M4ReadBindingsV1 &bindings) noexcept {
  Mode3M4ReductionV1 result;
  result.actual_receiver = actual_receiver;
  result.snapshot_revision = snapshot_revision;
  if (!access.exact_12004_bound || access.module_base == 0) {
    result.unavailable_reason = "exact_build_unavailable";
    return result;
  }
  result.count_7450 = ReadMode3M4Count7450V1(
      access, actual_receiver, snapshot_revision, bindings);
  if (bindings.count_71e0_source_closed &&
      bindings.read_count_28b71e0 != nullptr) {
    std::int32_t count = 0;
    if (bindings.read_count_28b71e0(bindings.count_context, access,
                                 actual_receiver, snapshot_revision, count))
      result.count_71e0_signed_eax = count;
  }
  std::uintptr_t nested = 0;
  if (Copy(access, actual_receiver, 0x1C0, nested)) {
    result.minimum_nested_1c0 = nested;
    if (nested == 0) {
      result.minimum_signed = 1;
    } else {
      std::int32_t field = 0;
      if (Copy(access, nested, 0x3D8, field)) {
        result.minimum_raw_3d8 = field;
        result.minimum_signed = field > 1 ? field : 1;
      }
    }
  }
  if (!result.count_7450.source_ready || !result.count_7450.signed_eax ||
      !result.count_71e0_signed_eax || !result.minimum_signed) {
    result.unavailable_reason = !result.count_7450.source_ready ?
        "count7450_input_unavailable" : !result.count_71e0_signed_eax ?
        "count71e0_input_or_source_unavailable" : "minimum_input_unavailable";
    return result;
  }
  result.difference_signed = WrappedSubtract(
      *result.count_71e0_signed_eax, *result.count_7450.signed_eax);
  result.after_minimum_signed = WrappedSubtract(
      *result.difference_signed, *result.minimum_signed);
  result.signed_eax = *result.after_minimum_signed > 0 ?
      *result.after_minimum_signed : 0;
  result.source_ready = true;
  return result;
}

Mode3M4ReductionV1 ReadMode3M4ReductionV1(
    const RawReceiverAccessV1 &access, std::uintptr_t actual_receiver,
    std::uint64_t snapshot_revision) noexcept {
  return ReadMode3M4ReductionV1(access, actual_receiver, snapshot_revision,
                              BindMode3M4ReadonlyChildrenV1());
}

bool ReadMode3M4SignedEaxChildV1(
    void *context, const RawReceiverAccessV1 &access,
    std::uintptr_t actual_receiver, std::uint64_t snapshot_revision,
    std::int32_t &out) noexcept {
  const auto result = context != nullptr ? ReadMode3M4ReductionV1(
      access, actual_receiver, snapshot_revision,
      *static_cast<const Mode3M4ReadBindingsV1 *>(context)) :
      ReadMode3M4ReductionV1(access, actual_receiver, snapshot_revision);
  if (!result.source_ready || !result.signed_eax) return false;
  out = *result.signed_eax;
  return true;
}

} // namespace xar::ck3_12004::construction_owner_mode3
