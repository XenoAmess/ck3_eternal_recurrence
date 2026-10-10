#include "xar_bridge/trigger_descriptor_validator_372e0ae_12004.hpp"

#include <stdexcept>

namespace {
using namespace xar::ck3_12004;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

bool RejectAnyRead(void *opaque, const void *, void *, std::size_t) noexcept {
  ++*static_cast<unsigned *>(opaque);
  return false;
}

LifestyleTriggerFrontierInputs12004 Input() {
  LifestyleTriggerFrontierInputs12004 i{};
  i.read_frame.executable_sha256 =
      "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
  i.read_frame.module_base = 0x140000000ULL;
  i.read_frame.snapshot_identity = "opaque:descriptor:owned-copy";
  i.read_frame.query_sequence = 71;
  i.read_frame.caller_domain = "stock_perk_legality_12004";
  i.read_frame.caller_snapshot_confirmed = true;
  i.module_image_size = 0x61C5000;
  i.selected_perk_identity = 0x220000000ULL;
  i.receiver_identity = 0x220000080ULL;
  i.source_context_root_word = std::uint16_t{4};
  i.source_context_full_id_payload = 0xF8000012ULL;
  i.context_is_source_projection = true;
  TriggerScopeTableProviderRaw3795A6012004 p{};
  p.frame = i.read_frame;
  p.query_frame_ready = true;
  p.caller_copied_root_kind_raw_u16 = std::uint16_t{4};
  p.table_data_identity = 0x230000000ULL;
  p.count_raw_i32 = 8;
  p.selected_source_fallback = false;
  p.selected_descriptor_identity = *p.table_data_identity + 4 * 80;
  // Owned-memory operand only; this test does not qualify a native body.
  p.descriptor_validator_pointer10 = i.read_frame.module_base + 0x1234;
  p.descriptor_selection_inputs_copied = true;
  p.descriptor_validator_pointer_copied = true;
  i.descriptor_provider = p;
  return i;
}

LifestyleTriggerNaturalWitness12004 Witness(const LifestyleTriggerFrontierInputs12004 &i) {
  LifestyleTriggerNaturalWitness12004 w{};
  w.read_frame = i.read_frame;
  w.call_event = {0x240000000ULL, 200, 9};
  w.return_event = {0x240000000ULL, 201, 9};
  w.query_cursor = {0x240000000ULL, 199, 9};
  w.call_rva = kTriggerDescriptorValidatorCallerRva12004;
  w.return_rva = kTriggerDescriptorValidatorReturnRva12004;
  w.selected_perk_identity = i.selected_perk_identity;
  w.receiver_identity = *i.receiver_identity;
  w.target_identity = *i.descriptor_provider->descriptor_validator_pointer10;
  w.original_rcx = 0x250000000ULL;
  w.original_rdx = *i.descriptor_provider->selected_descriptor_identity;
  w.original_root_word = i.source_context_root_word;
  w.original_full_id_payload = i.source_context_full_id_payload;
  w.returned_raw_u8 = std::uint8_t{0};
  w.original_matching_call_count = 1;
  w.original_call_observed = true;
  w.original_return_observed = true;
  return w;
}
} // namespace

// No main and no native hooks. Central16/10 may call this once in the new
// common 16e compound; it is not a replay of the qualified16d fixture.
void RunLifestyleDescriptorFrontierFreshCases12004() {
  unsigned reads = 0;
  const SourceLeafReadOnlyAccess12004 access{&reads, &RejectAnyRead};
  auto i = Input();
  auto out = ReadLifestyleDescriptorFrontier12004(access, i);
  Require(out.raw_target_ready && out.target.target_rva == 0x1234 &&
      out.target.slot_identity == *i.descriptor_provider->selected_descriptor_identity + 0x10 &&
      !out.source_value_ready && !out.returned_raw_u8 && reads == 0,
      "descriptor copied target is admitted without output or reread");
  i.descriptor_provider->descriptor_validator_returned_raw_u8 = std::uint8_t{1};
  i.descriptor_provider->descriptor_validator_result_source_ready = true;
  i.descriptor_provider->native_callback_executed = true;
  out = ReadLifestyleDescriptorFrontier12004(access, i);
  Require(!out.source_value_ready && !out.returned_raw_u8,
      "provider flags cannot manufacture descriptor AL");
  auto w = Witness(i);
  out = QualifyLifestyleDescriptorNaturalWitness12004(i, w);
  Require(out.source_value_ready && out.returned_raw_u8 == 0 &&
      out.result_source == "natural_original_once",
      "natural original-once raw AL zero is an observed value");
  w.returned_raw_u8 = std::uint8_t{0x80};
  out = QualifyLifestyleDescriptorNaturalWitness12004(i, w);
  Require(out.source_value_ready && out.returned_raw_u8 == 0x80,
      "natural AL preserves nonboolean byte");
  w.query_cursor.clock_identity = 0;
  Require(!QualifyLifestyleDescriptorNaturalWitness12004(i, w).source_value_ready,
      "query cursor cannot be inferred from metadata ticket");
  w = Witness(i);
  w.return_event.thread_id = 10;
  Require(!QualifyLifestyleDescriptorNaturalWitness12004(i, w).source_value_ready,
      "natural call and return require same actual thread");
  w = Witness(i);
  w.original_matching_call_count = 2;
  Require(!QualifyLifestyleDescriptorNaturalWitness12004(i, w).source_value_ready,
      "multiple matching calls cannot qualify an original-once output");
  w = Witness(i);
  w.original_full_id_payload = 0x00000012ULL;
  Require(!QualifyLifestyleDescriptorNaturalWitness12004(i, w).source_value_ready,
      "full character generation payload is compared unchanged");
  i = Input();
  i.descriptor_provider->frame.module_base += 0x1000;
  out = ReadLifestyleDescriptorFrontier12004(access, i);
  Require(!out.raw_target_ready && !out.target.target_rva && out.target.target_identity,
      "mismatched provider frame retains pointer without inventing current RVA");
  i = Input();
  i.descriptor_provider->selected_descriptor_identity = *i.descriptor_provider->table_data_identity + 4 * 0x80;
  Require(!ReadLifestyleDescriptorFrontier12004(access, i).raw_target_ready,
      "actual descriptor stride is decimal 80, not 0x80");
  i = Input();
  i.descriptor_provider->count_raw_i32 = -1;
  i.descriptor_provider->selected_source_fallback = true;
  i.descriptor_provider->selected_descriptor_identity = i.read_frame.module_base + 0x54F5310;
  Require(ReadLifestyleDescriptorFrontier12004(access, i).raw_target_ready,
      "negative signed count uses literal fallback branch");
  i.descriptor_provider->descriptor_validator_pointer10 = 0;
  out = ReadLifestyleDescriptorFrontier12004(access, i);
  Require(!out.raw_target_ready && out.target.target_identity == 0 && !out.returned_raw_u8,
      "copied null fallback target remains null input without AL");
  i = Input();
  i.source_context_root_word = std::uint16_t{0};
  i.descriptor_provider->caller_copied_root_kind_raw_u16 = std::uint16_t{0};
  Require(!ReadLifestyleDescriptorFrontier12004(access, i).raw_target_ready,
      "kind zero bypasses descriptor call");
  i = Input();
  i.context_is_source_projection = false;
  Require(!ReadLifestyleDescriptorFrontier12004(access, i).raw_target_ready && reads == 0,
      "no physical context is invented and adapter performs no reads");
}
