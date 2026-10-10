#include "xar_bridge/m4_count_28b71e0_12004.hpp"

#include <array>
#include <cstring>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

struct CopiedScalar {
  std::uintptr_t address = 0;
  std::size_t size = 0;
  std::array<std::uint8_t, 8> bytes{};
};

struct SourceCopies {
  const RawReceiverAccessV1 &underlying;
  std::vector<CopiedScalar> scalars;
  bool Read(std::uintptr_t address, void *out, std::size_t size) {
    if (size > 8 || !underlying.read_memory(underlying.context,
        reinterpret_cast<const void *>(address), out, size)) return false;
    CopiedScalar scalar;
    scalar.address = address;
    scalar.size = size;
    std::memcpy(scalar.bytes.data(), out, size);
    scalars.push_back(scalar);
    return true;
  }
  bool Unchanged() const {
    std::array<std::uint8_t, 8> after{};
    for (const auto &scalar : scalars)
      if (!underlying.read_memory(underlying.context,
          reinterpret_cast<const void *>(scalar.address), after.data(), scalar.size) ||
          std::memcmp(after.data(), scalar.bytes.data(), scalar.size) != 0)
        return false;
    return true;
  }
};

bool CopyMemory(void *context, const void *address, void *out, std::size_t size) {
  try { return static_cast<SourceCopies *>(context)->Read(
      reinterpret_cast<std::uintptr_t>(address), out, size); }
  catch (...) { return false; }
}
bool CopyForObject(void *context, std::uintptr_t address, void *out,
                   std::size_t size) noexcept {
  try { return static_cast<SourceCopies *>(context)->Read(address, out, size); }
  catch (...) { return false; }
}

template <typename T>
bool Field(const RawReceiverAccessV1 &access, std::uintptr_t base,
           std::size_t offset, std::optional<T> &out) noexcept {
  T value{};
  if (!RawReceiverReadV1(access, base, offset, value)) return false;
  out = value;
  return true;
}

} // namespace

Count28B71E0ObservationV1 ReadConstructionCount28B71E0V1(
    const RawReceiverAccessV1 &access, std::uintptr_t actual_receiver,
    std::uint64_t frame_key) {
  Count28B71E0ObservationV1 out;
  out.input_receiver = actual_receiver;
  out.frame_key = frame_key;
  const auto fail = [&](Count28B71E0FailureV1 failure) {
    out.failure = failure;
    out.observed = false;
    return out;
  };
  if (!access.exact_12004_bound) return fail(Count28B71E0FailureV1::exact_build);
  if (!access.read_memory) return fail(Count28B71E0FailureV1::read_callback);
  SourceCopies copies{access, {}};
  const RawReceiverAccessV1 observed_access{
      &copies, &CopyMemory, access.module_base, access.exact_12004_bound};
  if (!Field(observed_access, actual_receiver, 0x1C0, out.context_1c0))
    return fail(Count28B71E0FailureV1::collection);
  if (!RawReceiverAddV1(*out.context_1c0 ? *out.context_1c0 : access.module_base,
                       *out.context_1c0 ? 0x1E0 : 0x5459C88, out.descriptor) ||
      !Field(observed_access, out.descriptor, 0, out.data_pointer) ||
      !Field(observed_access, out.descriptor, 0x0C, out.count_raw_i32))
    return fail(Count28B71E0FailureV1::collection);
  // Native count is sign-extended before forming the end pointer, then the
  // loop compares only pointer equality. Negative is not an empty-list arm.
  if (*out.count_raw_i32 < 0)
    return fail(Count28B71E0FailureV1::negative_source_extent);
  // Shared13's sibling reader uses this finite readonly occurrence budget.
  // Exceeding it is unavailable capture, not native invalidity or empty zero.
  if (*out.count_raw_i32 > kCount28B71E0ReadonlyOccurrenceLimit12004)
    return fail(Count28B71E0FailureV1::native_copy_budget_exceeded);
  std::uint64_t count = 0;
  for (std::int32_t ordinal = 0; ordinal < *out.count_raw_i32; ++ordinal) {
    out.occurrences.emplace_back();
    auto &row = out.occurrences.back();
    row.ordinal = ordinal;
    std::uintptr_t registry = 0;
    if (!RawReceiverReadV1(observed_access, access.module_base, 0x5D1DAF8, registry))
      return fail(Count28B71E0FailureV1::title_resolution);
    if (registry != 0) {
      std::uintptr_t reloaded = 0;
      if (!Field(observed_access, *out.data_pointer,
                 static_cast<std::size_t>(ordinal) * 4, row.requested_full_id_u32) ||
          !RawReceiverReadV1(observed_access, access.module_base, 0x5D1DAF8, reloaded) ||
          reloaded == 0 ||
          !ReadRawReceiverRegistryV1(observed_access, reloaded,
                                     *row.requested_full_id_u32, 0x10, 0,
                                     row.selected_title, row.registry_matched))
        return fail(Count28B71E0FailureV1::title_resolution);
    }
    if (!row.registry_matched &&
        !RawReceiverReadV1(observed_access, access.module_base, 0x5D1DAE0,
                           row.selected_title))
      return fail(Count28B71E0FailureV1::title_resolution);
    std::uintptr_t rank_descriptor = 0;
    if (!RawReceiverReadV1(observed_access, row.selected_title, 0x48, rank_descriptor) ||
        !Field(observed_access, rank_descriptor, 0x64, row.rank_i32))
      return fail(Count28B71E0FailureV1::rank);
    if (*row.rank_i32 > 1) {
      row.path = Count28B71E0PathV1::skip_rank;
      continue;
    }
    // Reached230F8E0 starts by rereading this same rank. With its observed
    // unchanged rank<=1 it takes the direct title+338 arm; rank2 traversal
    // is outside this reached source condition and is never substituted.
    std::uintptr_t child_rank_descriptor = 0;
    std::int32_t child_rank = 0;
    if (!RawReceiverReadV1(observed_access, row.selected_title, 0x48, child_rank_descriptor) ||
        !RawReceiverReadV1(observed_access, child_rank_descriptor, 0x64, child_rank) ||
        child_rank_descriptor != rank_descriptor || child_rank != *row.rank_i32)
      return fail(Count28B71E0FailureV1::source_changed);
    if (!RawReceiverReadV1(observed_access, row.selected_title, 0x338, row.province))
      return fail(Count28B71E0FailureV1::direct_province);
    if (!Field(observed_access, row.province, 0x85C, row.province_magic_85c))
      return fail(Count28B71E0FailureV1::province_gate);
    if (*row.province_magic_85c != 0x50726F76U) {
      row.path = Count28B71E0PathV1::skip_province_magic;
      continue;
    }
    if (!Field(observed_access, row.province, 0x628, row.province_byte_628))
      return fail(Count28B71E0FailureV1::province_gate);
    if (*row.province_byte_628 == 0) {
      row.path = Count28B71E0PathV1::skip_province_byte;
      continue;
    }
    if (!Field(observed_access, row.selected_title, 0x130, row.title_byte_130))
      return fail(Count28B71E0FailureV1::title_gate);
    if (*row.title_byte_130 != 0) {
      row.path = Count28B71E0PathV1::skip_title_byte;
      continue;
    }
    if (!Field(observed_access, row.selected_title, 0x12C, row.title_dword_12c))
      return fail(Count28B71E0FailureV1::title_gate);
    if (*row.title_dword_12c != 0xFFFFFFFFU) {
      row.path = Count28B71E0PathV1::skip_title_sentinel;
      continue;
    }
    if (!Field(observed_access, row.province, 0x63C, row.province_dword_63c) ||
        !RawReceiverReadV1(observed_access, row.province, 0x620, row.province_pointer_620))
      return fail(Count28B71E0FailureV1::interface_source);
    if (*row.province_dword_63c != 0) {
      if (!Field(observed_access, row.province, 0x630, row.buffer_630) ||
          !RawReceiverReadV1(observed_access, *row.buffer_630, 0, row.interface_object))
        return fail(Count28B71E0FailureV1::interface_source);
    } else if (!RawReceiverReadV1(observed_access, access.module_base, 0x5D1E320,
                                  row.interface_object)) {
      return fail(Count28B71E0FailureV1::interface_source);
    }
    if (!Field(observed_access, row.interface_object, 0x38, row.interface_magic_38))
      return fail(Count28B71E0FailureV1::interface_source);
    if (*row.interface_magic_38 != 0x4744624FU) {
      row.path = Count28B71E0PathV1::count_interface_magic_mismatch;
    } else {
      if (!Field(observed_access, row.province, 0x630, row.buffer_630) ||
          !Field(observed_access, *row.buffer_630, 8, row.buffer_byte_8))
        return fail(Count28B71E0FailureV1::interface_source);
      if (*row.buffer_byte_8 == 0) {
        row.path = Count28B71E0PathV1::count_buffer_byte_zero;
      } else {
        if (!Field(observed_access, row.province_pointer_620, 0xBC, row.slots_byte_bc))
          return fail(Count28B71E0FailureV1::slots_source);
        if (*row.slots_byte_bc != 0) {
          row.path = Count28B71E0PathV1::count_slots_byte_nonzero;
        } else {
          const auto binding = BindReturnedSelector28C2DF012004(
              access.module_base, "1.20.0.4", kCount28B71E0SourcePin12004,
              &CopyForObject, &copies);
          row.returned_object_source = ResolveReturnedObject28C2DF012004(
              binding, actual_receiver, frame_key);
          const auto &object = *row.returned_object_source;
          if (!object.source_ready || object.input_receiver != actual_receiver ||
              object.frame_key != frame_key || object.returned_object == 0)
            return fail(Count28B71E0FailureV1::returned_object);
          if (!Field(observed_access, object.returned_object, 0x418, row.returned_member_418))
            return fail(Count28B71E0FailureV1::returned_member);
          if (*row.returned_member_418 != row.province_pointer_620) {
            row.path = Count28B71E0PathV1::skip_returned_member_unequal;
            continue;
          }
          row.path = Count28B71E0PathV1::count_returned_member_equal;
        }
      }
    }
    row.counted = true;
    ++count;
  }
  if (!copies.Unchanged()) return fail(Count28B71E0FailureV1::source_changed);
  out.eax_raw_u32 = static_cast<std::uint32_t>(count);
  std::int32_t signed_count = 0;
  const std::uint32_t raw_count = *out.eax_raw_u32;
  std::memcpy(&signed_count, &raw_count, sizeof(signed_count));
  out.eax_signed_i32 = signed_count;
  out.observed = true;
  return out;
}

bool ReadM4Count28B71E0Adapter12004(
    void *, const RawReceiverAccessV1 &access, std::uintptr_t actual_receiver,
    std::uint64_t frame_key, std::int32_t &out) noexcept {
  try {
    const auto observed = ReadConstructionCount28B71E0V1(access, actual_receiver, frame_key);
    if (!observed.observed || observed.failure != Count28B71E0FailureV1::none ||
        observed.input_receiver != actual_receiver || observed.frame_key != frame_key ||
        observed.source_pin != kCount28B71E0SourcePin12004 || !observed.eax_signed_i32)
      return false;
    out = *observed.eax_signed_i32;
    return true;
  } catch (...) { return false; }
}

} // namespace xar::ck3_12004::construction_owner_mode3
