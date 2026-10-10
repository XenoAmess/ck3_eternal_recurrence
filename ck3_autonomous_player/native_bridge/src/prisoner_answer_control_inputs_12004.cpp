#include "xar_bridge/prisoner_answer_control_inputs_12004.hpp"

namespace xar::ck3_12004 {
namespace {
std::optional<std::uintptr_t> ImageAddress(
    const PrisonerQuoteSourceFrame12004 &frame, std::uintptr_t rva) noexcept {
  if (!frame.module_base || frame.module_base >
      (std::numeric_limits<std::uintptr_t>::max)() - rva) return {};
  return frame.module_base + rva;
}
} // namespace

PrisonerControlMembershipRaw12004 ReadPrisonerControlMembershipRaw12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame,
    std::optional<std::uint32_t> key) {
  PrisonerControlMembershipRaw12004 out;
  out.frame = frame;
  out.context_2d8_raw_u32 = key;
  if (!PrisonerQuoteSourceFrameReady12004(frame) || !key) {
    out.unavailable_reason = "control_current_frame_or_actual_key_unavailable";
    return out;
  }
  const auto slot = ImageAddress(frame, kPrisonerControlCollectionSlotRva12004);
  if (!slot) { out.unavailable_reason = "control_collection_slot_unavailable"; return out; }
  out.instance = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, *slot);
  if (!out.instance || !*out.instance) {
    out.unavailable_reason = "control_instance_unavailable"; return out;
  }
  out.collection_object = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, *out.instance, 0xA0);
  if (!out.collection_object || !*out.collection_object) {
    out.unavailable_reason = "control_collection_object_unavailable"; return out;
  }
  out.list_data = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, *out.collection_object, 0x22358);
  out.list_count_i32 = ReadPrisonerQuoteSource12004<std::int32_t>(access, *out.collection_object, 0x22364);
  if (!out.list_data || !out.list_count_i32 || *out.list_count_i32 < 0 ||
      static_cast<std::size_t>(*out.list_count_i32) > access.maximum_modifier_occurrences ||
      (*out.list_count_i32 > 0 && !*out.list_data)) {
    out.unavailable_reason = "control_list_input_or_budget_unavailable"; return out;
  }
  const auto count = static_cast<std::size_t>(*out.list_count_i32);
  if (count > ((std::numeric_limits<std::uintptr_t>::max)() - *out.list_data) / 4) {
    out.unavailable_reason = "control_list_extent_unavailable"; return out;
  }
  for (std::size_t index = 0; index < count; ++index) {
    auto value = ReadPrisonerQuoteSource12004<std::uint32_t>(access, *out.list_data, index * 4);
    if (!value) { out.unavailable_reason = "control_required_list_element_unavailable"; return out; }
    out.copied_prefix.push_back(*value);
    if (*value == *key) break; // Source-closed scalar/SSE complete DWORD equality.
  }
  return out;
}

PrisonerAnswerByteChild12004 ProjectPrisonerControlMembership12004(
    const PrisonerControlMembershipRaw12004 &raw) {
  PrisonerAnswerByteChild12004 out;
  out.frame = raw.frame;
  out.actual_callee_rva = 0x2BAA6F0;
  out.full_id_argument = raw.context_2d8_raw_u32;
  if (!PrisonerQuoteSourceFrameReady12004(raw.frame) || !raw.context_2d8_raw_u32 ||
      !raw.instance || !*raw.instance || !raw.collection_object || !*raw.collection_object ||
      !raw.list_data || !raw.list_count_i32 || *raw.list_count_i32 < 0 ||
      (!*raw.list_data && *raw.list_count_i32 > 0) ||
      raw.copied_prefix.size() > static_cast<std::size_t>(*raw.list_count_i32)) return out;
  for (const auto value : raw.copied_prefix) {
    if (value == *raw.context_2d8_raw_u32) {
      out.raw_al = std::uint8_t{1};
      out.reached_effects_source_ready = true;
      return out;
    }
  }
  if (raw.copied_prefix.size() == static_cast<std::size_t>(*raw.list_count_i32) &&
      raw.unavailable_reason.empty()) {
    out.raw_al = std::uint8_t{0};
    out.reached_effects_source_ready = true;
  }
  return out;
}

PrisonerControlDebugRaw12004 ReadPrisonerControlDebugRaw12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame) {
  PrisonerControlDebugRaw12004 out;
  out.frame = frame;
  if (!PrisonerQuoteSourceFrameReady12004(frame)) return out;
  const auto object = ImageAddress(frame, kPrisonerControlDebugObjectRva12004);
  const auto guard = ImageAddress(frame, kPrisonerControlDebugGuardRva12004);
  if (!object || !guard) return out;
  out.static_object_identity = *object;
  out.initialization_guard_i32 = ReadPrisonerQuoteSource12004<std::int32_t>(access, *guard);
  out.observed_byte0 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, *object);
  out.observed_byte1 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, *object, 1);
  return out;
}

PrisonerAnswerDebugFlags12004 ProjectPrisonerControlDebugFlags12004(
    const PrisonerControlDebugRaw12004 &raw,
    const std::optional<PrisonerControlTlsEpoch12004> &epoch) {
  PrisonerAnswerDebugFlags12004 out;
  out.frame = raw.frame;
  out.actual_callee_rva = 0xA75D00;
  const auto expected = ImageAddress(raw.frame, kPrisonerControlDebugObjectRva12004);
  if (!PrisonerQuoteSourceFrameReady12004(raw.frame) || !expected ||
      raw.static_object_identity != *expected || !raw.initialization_guard_i32 ||
      !epoch || !(epoch->frame == raw.frame) ||
      !epoch->copied_from_current_query_thread || !epoch->literal_tls_epoch_i32 ||
      *raw.initialization_guard_i32 > *epoch->literal_tls_epoch_i32) return out;
  // Actual signed JG is not taken: A75D26 returns this static pointer directly.
  // Raw flags are independently optional; unread byte1 need not block byte0.
  out.byte0_raw_u8 = raw.observed_byte0;
  out.byte1_raw_u8 = raw.observed_byte1;
  out.reached_effects_source_ready = true;
  return out;
}

PrisonerAnswerControlPackage12004 ReadPrisonerAnswerControlPackage12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame,
    std::optional<std::uint32_t> key,
    const std::optional<PrisonerControlTlsEpoch12004> &epoch) {
  PrisonerAnswerControlPackage12004 out;
  out.membership_raw = ReadPrisonerControlMembershipRaw12004(access, frame, key);
  out.id_2baa6f0 = ProjectPrisonerControlMembership12004(out.membership_raw);
  out.debug_raw.frame = frame;
  if (out.id_2baa6f0.raw_al && *out.id_2baa6f0.raw_al != 0)
    out.debug_raw = ReadPrisonerControlDebugRaw12004(access, frame);
  out.debug_a75d00 = ProjectPrisonerControlDebugFlags12004(out.debug_raw, epoch);
  return out;
}

} // namespace xar::ck3_12004
