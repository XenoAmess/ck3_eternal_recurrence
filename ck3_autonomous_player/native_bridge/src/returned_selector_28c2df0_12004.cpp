#include "xar_bridge/returned_selector_28c2df0_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {
namespace {

constexpr std::uintptr_t kRegistrySlot = 0x5C67568; // MOV28C2DF4, next28C2DFB.
constexpr std::uintptr_t kReceiverFallbackSlot = 0x5C67570; // MOV28C2DFB.
constexpr std::uintptr_t kReturnedFallbackSlot = 0x5D1E2A8; // MOV28C2ED1.
constexpr std::uint32_t kReceiverMagic = 0x43686172; // CMP28C2E02.

template <typename T>
std::optional<T> Copy(const ReturnedSelector28C2DF0Bindings12004 &b,
                      std::uintptr_t address) {
  T value{};
  if (!b.read_bytes(b.read_context, address, &value, sizeof(value)))
    return std::nullopt;
  return value;
}

} // namespace

ReturnedSelector28C2DF0Bindings12004 BindReturnedSelector28C2DF012004(
    std::uintptr_t module_base, std::string_view version,
    std::string_view executable_sha256, ReturnedSelectorReadBytes12004 copy,
    void *context) noexcept {
  return {module_base != 0 && version == kGameVersion &&
              executable_sha256 == kExecutableSha256 && copy != nullptr,
          module_base, copy, context};
}

ReturnedObject28C2DF0Result12004 ResolveReturnedObject28C2DF012004(
    const ReturnedSelector28C2DF0Bindings12004 &b,
    std::uintptr_t actual_receiver, std::uint64_t frame_key) {
  ReturnedObject28C2DF0Result12004 out;
  out.input_receiver = actual_receiver;
  out.frame_key = frame_key;
  const auto fail = [&](std::string_view reason) {
    out.unavailable_reason = reason;
    return out;
  };
  if (!b.exact_build_ready || !b.read_bytes)
    return fail("exact4_source_binding_unavailable");
  if (!actual_receiver)
    return fail("actual_receiver_unavailable");

  // Native R8/R9 are copied once at function entry, before the receiver loop.
  const auto registry = Copy<std::uintptr_t>(b, b.module_base + kRegistrySlot);
  const auto receiver_fallback =
      Copy<std::uintptr_t>(b, b.module_base + kReceiverFallbackSlot);
  if (!registry || !receiver_fallback)
    return fail("entry_registry_or_receiver_fallback_unread");

  auto receiver = actual_receiver;
  std::optional<std::uintptr_t> selected;
  for (;;) {
    if (!receiver)
      return fail("resolved_receiver_unavailable");
    out.steps.emplace_back();
    auto &step = out.steps.back();
    step.receiver = receiver;
    step.magic_1c = Copy<std::uint32_t>(b, receiver + 0x1C);
    if (!step.magic_1c)
      return fail("receiver_magic_unread");
    bool invalid = *step.magic_1c != kReceiverMagic;
    if (!invalid) {
      step.full_id_18 = Copy<std::uint32_t>(b, receiver + 0x18);
      if (!step.full_id_18)
        return fail("receiver_full_id_unread");
      invalid = *step.full_id_18 == 0xFFFFFFFFU;
    }
    if (invalid) {
      out.return_path = "invalid_receiver_global_fallback";
      selected = Copy<std::uintptr_t>(b, b.module_base + kReturnedFallbackSlot);
      break;
    }
    step.context_1d0 = Copy<std::uintptr_t>(b, receiver + 0x1D0);
    if (!step.context_1d0)
      return fail("receiver_1d0_unread");
    if (*step.context_1d0) {
      out.return_path = "receiver_1d0_object_88";
      selected = Copy<std::uintptr_t>(b, *step.context_1d0 + 0x88);
      break;
    }
    step.context_1c0 = Copy<std::uintptr_t>(b, receiver + 0x1C0);
    if (!step.context_1c0)
      return fail("receiver_1c0_unread");
    if (*step.context_1c0) {
      out.return_path = "receiver_1c0_object_3f8";
      selected = Copy<std::uintptr_t>(b, *step.context_1c0 + 0x3F8);
      break;
    }
    step.related_1b8 = Copy<std::uintptr_t>(b, receiver + 0x1B8);
    if (!step.related_1b8)
      return fail("receiver_1b8_unread");
    step.related_full_id_c8 = *step.related_1b8
        ? Copy<std::uint32_t>(b, *step.related_1b8 + 0xC8)
        : std::optional<std::uint32_t>(0xFFFFFFFFU);
    if (!step.related_full_id_c8)
      return fail("related_full_id_unread");
    step.next_receiver = receiver_fallback;
    if (*registry) {
      const auto count = Copy<std::uint32_t>(b, *registry + 0x2C);
      if (!count)
        return fail("registry_count_unread");
      const auto index = *step.related_full_id_c8 & 0xFFFFFFU;
      if (index < *count) {
        const auto slots = Copy<std::uintptr_t>(b, *registry + 0x20);
        if (!slots)
          return fail("registry_slots_unread");
        step.candidate = Copy<std::uintptr_t>(b, *slots +
            static_cast<std::uintptr_t>(index) * 16 + 8);
        if (!step.candidate)
          return fail("registry_candidate_unread");
        if (*step.candidate) {
          step.candidate_full_id_18 = Copy<std::uint32_t>(b, *step.candidate + 0x18);
          if (!step.candidate_full_id_18)
            return fail("candidate_full_id_unread");
          if (*step.candidate_full_id_18 == *step.related_full_id_c8) {
            step.next_receiver = step.candidate;
            step.mapped_candidate_selected = true;
          }
        }
      }
    }
    receiver = *step.next_receiver; // Native jumps back to CMP28C2E02.
  }

  if (!selected)
    return fail("selected_return_object_unread");
  if (!*selected && out.return_path != "invalid_receiver_global_fallback") {
    // Native logs then returns this global. The read-only copy does not log.
    out.return_path = "selected_null_global_fallback";
    selected = Copy<std::uintptr_t>(b, b.module_base + kReturnedFallbackSlot);
    if (!selected)
      return fail("selected_null_fallback_unread");
  }
  out.returned_object = *selected;
  if (!out.returned_object)
    return fail("returned_object_null");
  out.source_ready = true;
  return out;
}

ReturnedSelector28C2DF0Result12004 ResolveReturnedSelector28C2DF012004(
    const ReturnedSelector28C2DF0Bindings12004 &b,
    std::uintptr_t actual_receiver, std::uint64_t frame_key) {
  ReturnedSelector28C2DF0Result12004 out;
  static_cast<ReturnedObject28C2DF0Result12004 &>(out) =
      ResolveReturnedObject28C2DF012004(b, actual_receiver, frame_key);
  if (!out.source_ready)
    return out;
  out.selector_byte_4d6 = Copy<std::uint8_t>(
      b, out.returned_object + kReturnedSelectorRawByteOffset12004);
  if (!out.selector_byte_4d6) {
    out.source_ready = false;
    out.unavailable_reason = "returned_selector_byte_4d6_unread";
  }
  return out;
}

} // namespace xar::ck3_12004
