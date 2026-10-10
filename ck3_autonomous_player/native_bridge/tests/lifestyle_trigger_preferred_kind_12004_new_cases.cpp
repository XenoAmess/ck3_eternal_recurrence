#include "xar_bridge/lifestyle_trigger_preferred_kind_12004.hpp"

#include <limits>
#include <stdexcept>
#include <string>

namespace {
using namespace xar::ck3_12004;
int checks = 0;
void Require(bool value) {
  if (!value) throw std::runtime_error("new preferred-kind source case failed");
  ++checks;
}
SourceTriggerPreferredKindCopiedInputs12004 CopyFixture() {
  SourceTriggerPreferredKindCopiedInputs12004 c{};
  auto &f = c.frame.read_frame;
  f.executable_sha256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
  f.module_base = std::uintptr_t{0x140000000ULL};
  f.snapshot_identity = "same-query:opaque\\snapshot\"key";
  f.caller_domain = "stock_perk_legality_12004"; f.caller_snapshot_confirmed = true;
  c.selected_perk_identity = std::uintptr_t{0x6000}; c.selected_perk_key = "fixture_perk_key";
  c.command_identity = std::uintptr_t{0x7000}; c.requested_full_character_id = std::uint32_t{0xF013ABCDU};
  c.selected_character_identity = std::uintptr_t{0x8000}; c.selected_character_full_id = c.requested_full_character_id;
  c.source_context_full_id_payload = std::uint64_t{0xF013ABCDULL}; c.context_is_source_projection = true;
  c.trigger_receiver = c.selected_perk_identity + 0x80;
  c.frame.producer_rva = 0x372B4C0; c.frame.receiver_identity = *c.trigger_receiver;
  c.frame.primary_scope_root_word = std::uint16_t{4}; c.root_kind_raw_u16 = std::uint16_t{4};
  c.trigger_vptr = f.module_base + 0x5000000; c.slot58_address = *c.trigger_vptr + 0x58;
  c.slot58_target_va = f.module_base + 0x1234567; c.slot58_target_rva = std::uint32_t{0x1234567};
  c.module_extent_bytes = std::uint64_t{0x6000000};
  c.source_kind = SourceTriggerPreferredKindSource12004::perk_allow_trigger_80;
  c.selection_source_qualified = true;
  PersonInstalledTransferEvent12004 event{}; event.clock_identity = std::uintptr_t{0xCA10};
  event.sequence = 71; event.thread_id = std::uint32_t{19}; c.validate_scope_entry_event = event;
  return c;
}
// These are declared contract premises in owned memory. They are not a real
// observer record, real getter target, source receipt, or current MCP output.
SourceTriggerPreferredKindNaturalReturn12004 NaturalFixture(const SourceTriggerPreferredKindRaw12004 &r) {
  SourceTriggerPreferredKindNaturalReturn12004 w{}; w.frame = r.frame;
  w.source_kind = r.source_kind; w.selected_perk_identity = r.selected_perk_identity; w.selected_perk_key = r.selected_perk_key;
  w.command_identity = r.command_identity; w.requested_full_character_id = r.requested_full_character_id;
  w.selected_character_identity = r.selected_character_identity; w.selected_character_full_id = r.selected_character_full_id;
  w.source_context_full_id_payload = r.source_context_full_id_payload;
  w.trigger_receiver = *r.trigger_receiver; w.trigger_vptr = *r.trigger_vptr; w.slot58_target_va = *r.slot58_target_va;
  w.actual_call_rva = 0x372B4D3; w.actual_return_rva = 0x372B4D6;
  w.validate_scope_entry_event = *r.validate_scope_entry_event;
  w.before_original_event = w.validate_scope_entry_event; ++w.before_original_event.sequence;
  w.returned_event = w.before_original_event; ++w.returned_event.sequence;
  w.returned_rax_bits = std::uint64_t{0xDEADBEEF00000004ULL};
  w.root_after_return_scope_identity = std::uintptr_t{0x9000}; w.root_after_return_raw_u16 = std::uint16_t{4};
  w.actual_validate_scope_observed = true; w.actual_slot58_original_once_observed = true;
  w.original_returned = true; w.live_observer_binding_verified = true; w.root_after_return_observed = true;
  return w;
}
int guarded_calls = 0;
bool RejectAnyMemory(void *, const void *, void *, std::size_t) noexcept { ++guarded_calls; return false; }
SourceTriggerPreferredKindPureValue12004 PureContractFixture(
    const SourceLeafReadOnlyAccess12004 &, const SourceTriggerPreferredKindRaw12004 &r) noexcept {
  return {r.root_kind_raw_u16, true};
}
SourceTriggerPreferredKindPureValue12004 PurePartialFixture(
    const SourceLeafReadOnlyAccess12004 &, const SourceTriggerPreferredKindRaw12004 &) noexcept { return {}; }
} // namespace

int RunLifestyleTriggerPreferredKind12004NewCases() {
  using namespace xar::ck3_12004;
  checks = 0; guarded_calls = 0;
  const auto copied = CopyFixture(); const auto raw = BindSourceTriggerPreferredKindCopiedInputs12004(copied);
  Require(raw.raw_source_ready && !raw.frame.primary_scope_identity && raw.context_is_source_projection);
  Require(raw.frame.read_frame.frame_identity == 0 && raw.frame.read_frame.query_sequence == 0 &&
      raw.frame.read_frame.proof_epoch == 0 && raw.frame.read_frame.snapshot_identity == copied.frame.read_frame.snapshot_identity);
  auto bad = copied; bad.selection_source_qualified = false;
  Require(!BindSourceTriggerPreferredKindCopiedInputs12004(bad).raw_source_ready);
  bad = copied; bad.selected_character_full_id = std::uint32_t{0x0013ABCDU};
  Require(!BindSourceTriggerPreferredKindCopiedInputs12004(bad).raw_source_ready);
  bad = copied; bad.source_context_full_id_payload = std::uint64_t{0xFFFFFFFFF013ABCDULL};
  Require(!BindSourceTriggerPreferredKindCopiedInputs12004(bad).raw_source_ready);
  bad = copied; bad.trigger_receiver = *bad.trigger_receiver + 8;
  Require(!BindSourceTriggerPreferredKindCopiedInputs12004(bad).raw_source_ready);
  bad = copied; bad.source_kind = SourceTriggerPreferredKindSource12004::unknown;
  Require(!BindSourceTriggerPreferredKindCopiedInputs12004(bad).raw_source_ready);
  bad = copied; bad.module_extent_bytes.reset();
  Require(!BindSourceTriggerPreferredKindCopiedInputs12004(bad).raw_source_ready);
  bad = copied; bad.slot58_target_va = bad.frame.read_frame.module_base + *bad.module_extent_bytes;
  Require(!BindSourceTriggerPreferredKindCopiedInputs12004(bad).raw_source_ready);
  bad = copied; bad.slot58_target_rva = std::uint32_t{0x1234568};
  Require(!BindSourceTriggerPreferredKindCopiedInputs12004(bad).raw_source_ready);
  bad = copied; bad.trigger_vptr = (std::numeric_limits<std::uintptr_t>::max)();
  Require(!BindSourceTriggerPreferredKindCopiedInputs12004(bad).raw_source_ready);

  const auto w = NaturalFixture(raw); const auto observed = QualifySourceTriggerPreferredKindNaturalReturn12004(raw, w);
  const auto gate = ProjectSourceTriggerPreferredKindGate12004(observed);
  Require(observed.preferred_kind_source_ready && observed.preferred_kind_ax_u16 == std::uint16_t{4} &&
      gate.qualified_ready && gate.returned_byte == std::uint8_t{1});
  auto changed = w; changed.returned_rax_bits = std::uint64_t{0};
  const auto zero = QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed);
  Require(zero.preferred_kind_source_ready && zero.preferred_kind_ax_u16 == std::uint16_t{0} &&
      !ProjectSourceTriggerPreferredKindGate12004(zero).returned_byte);
  changed = w; changed.returned_rax_bits = std::uint64_t{7};
  Require(!ProjectSourceTriggerPreferredKindGate12004(QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed)).qualified_ready);
  changed = w; changed.returned_event.clock_identity = std::uintptr_t{0xCA11};
  Require(!QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed).preferred_kind_source_ready);
  changed = w; changed.returned_event.thread_id.reset();
  Require(!QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed).preferred_kind_source_ready);
  changed = w; changed.returned_event.sequence = changed.before_original_event.sequence;
  Require(!QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed).preferred_kind_source_ready);
  changed = w; changed.actual_return_rva = 0x372B4F1;
  Require(!QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed).preferred_kind_source_ready);
  changed = w; changed.frame.read_frame.snapshot_identity += "different";
  Require(!QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed).preferred_kind_source_ready);
  changed = w; changed.slot58_target_va += 1;
  Require(!QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed).preferred_kind_source_ready);
  changed = w; changed.root_after_return_raw_u16 = std::uint16_t{7};
  const auto changed_caller_word = QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed);
  Require(changed_caller_word.preferred_kind_source_ready && changed_caller_word.caller_root_word_source_ready &&
      ProjectSourceTriggerPreferredKindGate12004(changed_caller_word).root_kind_raw_u16 == std::uint16_t{7} &&
      !ProjectSourceTriggerPreferredKindGate12004(changed_caller_word).qualified_ready);
  changed = w; changed.root_after_return_raw_u16.reset();
  const auto missing_caller_word = QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed);
  Require(missing_caller_word.preferred_kind_source_ready && !missing_caller_word.caller_root_word_source_ready &&
      !ProjectSourceTriggerPreferredKindGate12004(missing_caller_word).qualified_ready);
  changed = w; changed.original_returned = false;
  Require(!QualifySourceTriggerPreferredKindNaturalReturn12004(raw, changed).preferred_kind_source_ready);
  auto no_event = raw; no_event.validate_scope_entry_event.reset();
  Require(!QualifySourceTriggerPreferredKindNaturalReturn12004(no_event, w).preferred_kind_source_ready);

  SourceLeafReadOnlyAccess12004 access{}; access.read_memory = &RejectAnyMemory;
  SourceTriggerPreferredKindClosedTarget12004 target{}; target.actual_target_rva = *raw.slot58_target_rva;
  target.complete_source_sha256.assign(64, 'c'); target.source_kind = raw.source_kind;
  target.exact_target_source_closed = true; target.native_invocation_free = true; target.read_pure = &PureContractFixture;
  const auto pure = ReadSourceTriggerPreferredKindClosedTarget12004(access, raw, target);
  Require(pure.preferred_kind_source_ready && !pure.actual_native_original_observed &&
      ProjectSourceTriggerPreferredKindGate12004(pure).returned_byte == std::uint8_t{1});
  ++target.actual_target_rva;
  Require(!ReadSourceTriggerPreferredKindClosedTarget12004(access, raw, target).preferred_kind_source_ready);
  --target.actual_target_rva; target.read_pure = &PurePartialFixture;
  Require(!ReadSourceTriggerPreferredKindClosedTarget12004(access, raw, target).preferred_kind_source_ready);
  target.read_pure = &PureContractFixture; target.complete_source_sha256.assign(64, 'q');
  Require(!ReadSourceTriggerPreferredKindClosedTarget12004(access, raw, target).preferred_kind_source_ready);

  LifestyleTriggerFrontierInputs12004 input{}; input.read_frame = copied.frame.read_frame;
  input.module_image_size = std::uint32_t{0x6000000}; input.target_key = copied.selected_perk_key;
  input.command_identity = copied.command_identity; input.selected_perk_identity = copied.selected_perk_identity;
  input.requested_full_character_id = copied.requested_full_character_id;
  input.selected_character_identity = copied.selected_character_identity; input.selected_character_full_id = copied.selected_character_full_id;
  input.receiver_identity = copied.trigger_receiver; input.vtable_identity = copied.trigger_vptr;
  input.slot58.slot_identity = copied.slot58_address; input.slot58.target_identity = copied.slot58_target_va;
  input.slot58.target_rva = std::uintptr_t{0x1234567}; input.slot58.copied = true;
  input.source_context_root_word = copied.root_kind_raw_u16; input.source_context_full_id_payload = copied.source_context_full_id_payload;
  input.context_is_source_projection = true; input.caller_before_after_confirmed = true;
  input.repeated_raw_match = false; input.mailbox_before_accepted = true;
  const auto lane = ReadLifestyleRootKindFrontier12004(access, input);
  Require(lane.raw_target_ready && !lane.source_value_ready && !lane.returned_raw_u16 && !lane.closed_target_proof && !lane.natural_witness);
  Require(guarded_calls == 0 && lane.call_rva == 0x372B4D3 && lane.return_rva == 0x372B4D6);
  input.slot58.target_rva = std::uintptr_t{0x100000000ULL};
  Require(!ReadLifestyleRootKindFrontier12004(access, input).raw_target_ready);
  return checks;
}
