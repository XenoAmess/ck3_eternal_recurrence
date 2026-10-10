#include "xar_bridge/construction_numeric_child_24cef10_12004.hpp"

#include <cstring>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

constexpr std::uintptr_t kFirstRegistrySlot = 0x5D1DAF8;
constexpr std::uintptr_t kFirstFallbackSlot = 0x5D1DAE0;
constexpr std::uintptr_t kSecondRegistrySlot = 0x5C67568;
constexpr std::uintptr_t kSecondFallbackSlot = 0x5C67570;

template <typename T>
bool CopyField(const LoadedInputAccessV1 &access, std::uintptr_t base,
               std::size_t offset, std::optional<T> &out) noexcept {
  T value{};
  if (!ReadOffsetV1(access, base, offset, value)) return false;
  out = value;
  return true;
}

bool Resolve(const LoadedInputAccessV1 &access, std::uintptr_t image_base,
             std::uintptr_t receiver, std::size_t requested_offset,
             std::uintptr_t registry_rva, std::uintptr_t fallback_rva,
             std::size_t identity_offset,
             Numeric24CEF10ResolutionV1 &out) noexcept {
  out.registry_slot_rva = registry_rva;
  out.fallback_slot_rva = fallback_rva;
  if (!CopyField(access, image_base, registry_rva, out.registry_pointer))
    return false;
  if (*out.registry_pointer != 0) {
    if (!CopyField(access, receiver, requested_offset, out.requested_full_id_u32) ||
        !CopyField(access, *out.registry_pointer, 0x2C, out.registry_count_u32))
      return false;
    // CMP index,count; JAE uses an unsigned DWORD count and preserves the
    // full generation in the later equality. There is no sentinel branch.
    const auto index = *out.requested_full_id_u32 & 0xFFFFFFU;
    if (index < *out.registry_count_u32) {
      if (!CopyField(access, *out.registry_pointer, 0x20, out.slots_pointer) ||
          !CopyField(access, *out.slots_pointer,
                     static_cast<std::size_t>(index) * 16 + 8,
                     out.candidate_pointer))
        return false;
      if (*out.candidate_pointer != 0) {
        if (!CopyField(access, *out.candidate_pointer, identity_offset,
                       out.candidate_full_id_u32))
          return false;
        if (*out.candidate_full_id_u32 == *out.requested_full_id_u32) {
          out.selected_pointer = *out.candidate_pointer;
          out.observed = true;
          return true;
        }
      }
    }
  }
  // A captured zero fallback remains a raw pointer. A later source read
  // that requires this receiver determines whether the result is available.
  if (!CopyField(access, image_base, fallback_rva, out.fallback_pointer))
    return false;
  out.used_fallback = true;
  out.selected_pointer = *out.fallback_pointer;
  out.observed = true;
  return true;
}

bool SameResolution(const Numeric24CEF10ResolutionV1 &a,
                    const Numeric24CEF10ResolutionV1 &b) noexcept {
  return a.observed == b.observed && a.used_fallback == b.used_fallback &&
      a.registry_slot_rva == b.registry_slot_rva &&
      a.fallback_slot_rva == b.fallback_slot_rva &&
      a.registry_pointer == b.registry_pointer &&
      a.requested_full_id_u32 == b.requested_full_id_u32 &&
      a.registry_count_u32 == b.registry_count_u32 &&
      a.slots_pointer == b.slots_pointer &&
      a.candidate_pointer == b.candidate_pointer &&
      a.candidate_full_id_u32 == b.candidate_full_id_u32 &&
      a.fallback_pointer == b.fallback_pointer &&
      a.selected_pointer == b.selected_pointer;
}

bool ReadForReturnedObject(void *context, std::uintptr_t address, void *out,
                           std::size_t bytes) noexcept {
  const auto &access = *static_cast<const LoadedInputAccessV1 *>(context);
  return access.read_memory != nullptr && access.read_memory(
      access.context, reinterpret_cast<const void *>(address), out, bytes);
}

bool SameReturnedObject(const ReturnedObject28C2DF0Result12004 &a,
                        const ReturnedObject28C2DF0Result12004 &b) noexcept {
  if (!a.source_ready || !b.source_ready || a.input_receiver != b.input_receiver ||
      a.frame_key != b.frame_key || a.returned_object != b.returned_object ||
      a.return_path != b.return_path || a.steps.size() != b.steps.size())
    return false;
  for (std::size_t i = 0; i < a.steps.size(); ++i) {
    const auto &x = a.steps[i];
    const auto &y = b.steps[i];
    if (x.receiver != y.receiver || x.magic_1c != y.magic_1c ||
        x.full_id_18 != y.full_id_18 || x.context_1d0 != y.context_1d0 ||
        x.context_1c0 != y.context_1c0 || x.related_1b8 != y.related_1b8 ||
        x.related_full_id_c8 != y.related_full_id_c8 ||
        x.candidate != y.candidate || x.candidate_full_id_18 != y.candidate_full_id_18 ||
        x.next_receiver != y.next_receiver ||
        x.mapped_candidate_selected != y.mapped_candidate_selected)
      return false;
  }
  return true;
}

} // namespace

ConstructionNumericChild24CEF10ObservationV1 ReadConstructionNumericChild24CEF10V1(
    const LoadedInputAccessV1 &access, std::uintptr_t image_base,
    std::uintptr_t original_receiver, std::uint64_t frame_key) {
  ConstructionNumericChild24CEF10ObservationV1 out;
  out.receiver_pointer = original_receiver;
  out.frame_key = frame_key;
  const auto fail = [&](Numeric24CEF10FailureV1 failure) {
    out.failure = failure;
    out.observed = false;
    return out;
  };
  if (!access.exact_12004_bound) return fail(Numeric24CEF10FailureV1::exact_build);
  if (!access.read_memory) return fail(Numeric24CEF10FailureV1::read_callback);
  std::uintptr_t address = 0;
  // Include04's furthest referenced global in the same exact image binding.
  if (!AddOffsetV1(image_base, 0x5D1E2A8, address))
    return fail(Numeric24CEF10FailureV1::image_base);
  if (!Resolve(access, image_base, original_receiver, 0x18,
               kFirstRegistrySlot, kFirstFallbackSlot, 0x10, out.first_resolution))
    return fail(Numeric24CEF10FailureV1::first_resolution);
  if (!Resolve(access, image_base, out.first_resolution.selected_pointer, 0x128,
               kSecondRegistrySlot, kSecondFallbackSlot, 0x18, out.second_resolution))
    return fail(Numeric24CEF10FailureV1::second_resolution);

  const auto object_binding = BindReturnedSelector28C2DF012004(
      image_base, "1.20.0.4", kConstructionNumeric24CEF10SourcePin12004,
      &ReadForReturnedObject,
      const_cast<void *>(static_cast<const void *>(&access)));
  out.returned_object_source = ResolveReturnedObject28C2DF012004(
      object_binding, out.second_resolution.selected_pointer, frame_key);
  if (!out.returned_object_source.source_ready ||
      out.returned_object_source.input_receiver != out.second_resolution.selected_pointer ||
      out.returned_object_source.frame_key != frame_key ||
      out.returned_object_source.returned_object == 0)
    return fail(Numeric24CEF10FailureV1::returned_object);
  if (!CopyField(access, out.returned_object_source.returned_object, 0x40,
                 out.flags_qword_40))
    return fail(Numeric24CEF10FailureV1::flags_read);
  out.gate_bit35 = ((*out.flags_qword_40 >> 35) & 1U) != 0;
  if (*out.gate_bit35) {
    if (!CopyField(access, original_receiver, 0x38C, out.eax_raw_u32))
      return fail(Numeric24CEF10FailureV1::value_read);
  } else {
    out.eax_raw_u32 = 0;
  }
  std::int32_t signed_value = 0;
  const std::uint32_t raw_value = *out.eax_raw_u32;
  std::memcpy(&signed_value, &raw_value, sizeof(signed_value));
  out.eax_signed_i32 = signed_value;

  Numeric24CEF10ResolutionV1 after_first, after_second;
  if (!Resolve(access, image_base, original_receiver, 0x18,
               kFirstRegistrySlot, kFirstFallbackSlot, 0x10, after_first) ||
      !Resolve(access, image_base, after_first.selected_pointer, 0x128,
               kSecondRegistrySlot, kSecondFallbackSlot, 0x18, after_second) ||
      !SameResolution(out.first_resolution, after_first) ||
      !SameResolution(out.second_resolution, after_second))
    return fail(Numeric24CEF10FailureV1::source_changed);
  const auto after_object = ResolveReturnedObject28C2DF012004(
      object_binding, after_second.selected_pointer, frame_key);
  if (!SameReturnedObject(out.returned_object_source, after_object))
    return fail(Numeric24CEF10FailureV1::source_changed);
  std::uint64_t after_flags = 0;
  std::uint32_t after_value = 0;
  if (!ReadOffsetV1(access, after_object.returned_object, 0x40, after_flags) ||
      after_flags != *out.flags_qword_40 ||
      (*out.gate_bit35 &&
       (!ReadOffsetV1(access, original_receiver, 0x38C, after_value) ||
        after_value != *out.eax_raw_u32)))
    return fail(Numeric24CEF10FailureV1::source_changed);
  out.observed = true;
  return out;
}

} // namespace xar::ck3_12004::construction_owner_mode3
