#include "xar_bridge/lifestyle_trigger_scope_mask_12004.hpp"

#include <array>
#include <limits>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kCallRva = 0x372B4EE, kReturnRva = 0x372B4F1;

bool InModule(const LifestyleTriggerFrontierInputs12004 &in,
              std::uintptr_t address, std::size_t width) noexcept {
  if (!in.module_image_size || *in.module_image_size == 0 || width == 0 ||
      address < in.read_frame.module_base ||
      address > (std::numeric_limits<std::uintptr_t>::max)() - (width - 1)) return false;
  const auto rva = address - in.read_frame.module_base;
  return rva < *in.module_image_size &&
      width <= static_cast<std::size_t>(*in.module_image_size) - rva;
}

const char *RawMissing(const LifestyleTriggerFrontierInputs12004 &in) noexcept {
  if (!SourceReadFrameReady12004(in.read_frame) ||
      in.read_frame.query_sequence == 0 ||
      in.read_frame.caller_domain != "stock_perk_legality_12004" ||
      !in.caller_before_after_confirmed ||
      (in.mailbox_before_accepted && !*in.mailbox_before_accepted) ||
      (in.mailbox_after_accepted && !*in.mailbox_after_accepted))
    return "root_mask_current_query_frame_unconfirmed";
  if (in.command_identity == 0 || in.target_key.empty() ||
      in.selected_perk_identity == 0 ||
      in.selected_perk_identity > (std::numeric_limits<std::uintptr_t>::max)() - 0x80 ||
      !in.receiver_identity || *in.receiver_identity != in.selected_perk_identity + 0x80)
    return "root_mask_perk80_receiver_binding_unavailable";
  if (!in.vtable_identity || !InModule(in, *in.vtable_identity, 0xD0) ||
      !in.vtable_rva || *in.vtable_rva != *in.vtable_identity - in.read_frame.module_base)
    return "root_mask_copied_vtable_module_binding_unavailable";
  if (!in.slot60.copied || !in.slot60.slot_identity ||
      *in.slot60.slot_identity != *in.vtable_identity + 0x60 ||
      !InModule(in, *in.slot60.slot_identity, sizeof(std::uint64_t)))
    return "root_mask_copied_slot60_binding_unavailable";
  if (!in.slot60.target_identity || !in.slot60.target_rva ||
      !InModule(in, *in.slot60.target_identity, 1) ||
      *in.slot60.target_rva != *in.slot60.target_identity - in.read_frame.module_base)
    return "root_mask_copied_slot60_target_unavailable";
  return nullptr;
}

bool EventReady(const LifestyleTriggerNaturalEvent12004 &e) noexcept {
  return e.clock_identity != 0 && e.sequence != 0 && e.thread_id && *e.thread_id != 0;
}
bool Before(const LifestyleTriggerNaturalEvent12004 &a,
            const LifestyleTriggerNaturalEvent12004 &b) noexcept {
  return EventReady(a) && EventReady(b) && a.clock_identity == b.clock_identity &&
      a.thread_id == b.thread_id && a.sequence < b.sequence;
}

const char *NaturalMissing(const LifestyleTriggerFrontierInputs12004 &in,
                           const LifestyleTriggerNaturalWitness12004 &w,
                           bool require_output) noexcept {
  if (const auto *reason = RawMissing(in)) return reason;
  if (w.read_frame != in.read_frame ||
      w.selected_perk_identity != in.selected_perk_identity ||
      w.receiver_identity != *in.receiver_identity ||
      w.original_rcx != *in.receiver_identity ||
      w.target_identity != *in.slot60.target_identity)
    return "root_mask_natural_same_query_receiver_target_mismatch";
  if (w.call_rva != kCallRva || w.return_rva != kReturnRva ||
      !w.original_call_observed || !w.original_return_observed ||
      w.original_matching_call_count != 1)
    return "root_mask_natural_original_once_boundary_unavailable";
  if (!Before(w.query_cursor, w.call_event) || !Before(w.call_event, w.return_event))
    return "root_mask_natural_shared_clock_thread_order_unavailable";
  if (w.original_rdx == 0 ||
      w.original_rdx > (std::numeric_limits<std::uintptr_t>::max)() - 15)
    return "root_mask_natural_original_output_buffer_unavailable";
  if (in.source_context_root_word && w.original_root_word &&
      in.source_context_root_word != w.original_root_word)
    return "root_mask_natural_copied_root_word_mismatch";
  if (in.source_context_full_id_payload && w.original_full_id_payload &&
      in.source_context_full_id_payload != w.original_full_id_payload)
    return "root_mask_natural_copied_full_id_payload_mismatch";
  if (w.returned_raw_u8 || w.returned_raw_u16)
    return "root_mask_natural_output_width_mismatch";
  if (require_output && (!w.returned_qword0 || !w.returned_qword1))
    return "root_mask_natural_owned_16byte_output_unavailable";
  return nullptr;
}

LifestyleTriggerLaneSource12004 RawLane(const LifestyleTriggerFrontierInputs12004 &in) {
  LifestyleTriggerLaneSource12004 out{};
  out.lane = "root_mask_qwords";
  out.call_rva = kCallRva; out.return_rva = kReturnRva;
  out.target = in.slot60;
  if (const auto *reason = RawMissing(in)) out.unavailable_reason = reason;
  else {
    out.raw_target_ready = true;
    out.unavailable_reason = "root_mask_concrete_target_source_or_natural_output_unavailable";
  }
  return out;
}

std::uint64_t Qword(const std::array<std::uint8_t, 16> &bytes,
                    std::size_t offset) noexcept {
  std::uint64_t value = 0;
  for (std::size_t i = 0; i != 8; ++i)
    value |= static_cast<std::uint64_t>(bytes[offset + i]) << (i * 8);
  return value;
}
} // namespace

LifestyleTriggerLaneSource12004 ReadLifestyleRootMaskFrontier12004(
    const SourceLeafReadOnlyAccess12004 &access,
    const LifestyleTriggerFrontierInputs12004 &in) noexcept {
  // A concrete pure target is added only after an actual same-query target
  // claim and complete exact-body closure. Copied addresses are not outputs.
  (void)access;
  try { return RawLane(in); }
  catch (...) { return {}; }
}

LifestyleTriggerLaneSource12004 AdmitLifestyleRootMaskNaturalWitness12004(
    const LifestyleTriggerFrontierInputs12004 &in,
    const LifestyleTriggerNaturalWitness12004 &w) noexcept {
  try {
    auto out = RawLane(in);
    if (const auto *reason = NaturalMissing(in, w, true)) {
      out.unavailable_reason = reason;
      return out;
    }
    out.natural_witness = w;
    out.returned_qword0 = w.returned_qword0;
    out.returned_qword1 = w.returned_qword1;
    out.source_value_ready = true;
    out.result_source = "natural_original_once";
    out.unavailable_reason.clear();
    return out;
  } catch (...) { return {}; }
}

LifestyleTriggerLaneSource12004 CaptureLifestyleRootMaskNaturalReturn12004(
    const SourceLeafReadOnlyAccess12004 &access,
    const LifestyleTriggerFrontierInputs12004 &in,
    const LifestyleRootMaskNaturalReturnBoundary12004 &boundary) noexcept {
  try {
    auto out = RawLane(in);
    auto witness = boundary.occurrence;
    witness.returned_qword0.reset(); witness.returned_qword1.reset();
    if (const auto *reason = NaturalMissing(in, witness, false)) {
      out.unavailable_reason = reason;
      return out;
    }
    if (!boundary.actual_original_return_boundary ||
        !boundary.output_buffer_valid_at_return || !boundary.copied_read_frame_unchanged ||
        boundary.receiver_vtable_identity != *in.vtable_identity ||
        boundary.slot_identity != *in.slot60.slot_identity) {
      out.unavailable_reason = "root_mask_original_return_output_lifetime_unconfirmed";
      return out;
    }
    std::array<std::uint8_t, 16> bytes{};
    if (!access.read_memory || !access.read_memory(access.context,
        reinterpret_cast<const void *>(witness.original_rdx), bytes.data(), bytes.size())) {
      out.unavailable_reason = "root_mask_original_return_16byte_copy_incomplete";
      return out;
    }
    witness.returned_qword0 = Qword(bytes, 0);
    witness.returned_qword1 = Qword(bytes, 8);
    return AdmitLifestyleRootMaskNaturalWitness12004(in, witness);
  } catch (...) { return {}; }
}

} // namespace xar::ck3_12004
