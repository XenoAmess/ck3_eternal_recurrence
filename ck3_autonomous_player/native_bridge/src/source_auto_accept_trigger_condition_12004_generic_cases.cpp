#include "xar_bridge/source_auto_accept_trigger_condition_12004.hpp"
#include "xar_bridge/prisoner_trigger_root_scope_gate_12004.hpp"

#include <cstring>
#include <map>
#include <stdexcept>
#include <utility>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kModule = 0x100000, kScope = 0x2000, kTrigger = 0x3000, kVtable = 0x4000;
struct GenericMemory {
  std::map<std::uintptr_t, std::vector<std::uint8_t>> fields;
  std::size_t reads = 0;
  template <typename T> void Put(std::uintptr_t address, T value) {
    std::vector<std::uint8_t> bytes(sizeof(T));
    std::memcpy(bytes.data(), &value, sizeof(T)); fields[address] = std::move(bytes);
  }
};
bool GuardGeneric(void *context, const void *address, void *output, std::size_t size) noexcept {
  auto &memory = *static_cast<GenericMemory *>(context); ++memory.reads;
  const auto it = memory.fields.find(reinterpret_cast<std::uintptr_t>(address));
  if (it == memory.fields.end() || it->second.size() != size) return false;
  std::memcpy(output, it->second.data(), size); return true;
}
void RequireGeneric(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
SourceLeafFrame12004 GenericFrame() {
  SourceLeafFrame12004 frame{};
  frame.read_frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
  frame.read_frame.module_base = kModule;
  frame.read_frame.snapshot_identity = "m5/lifestyle/owned-source-copy";
  frame.read_frame.frame_identity = 0;
  frame.read_frame.native_revision = 31; frame.read_frame.query_sequence = 37;
  frame.read_frame.proof_epoch = 41; frame.read_frame.date_raw = 43;
  frame.read_frame.caller_domain = "lifestyle"; frame.read_frame.caller_snapshot_confirmed = true;
  frame.producer_rva = kPrisonerAutoAcceptTriggerWrapperRva12004;
  frame.receiver_identity = kTrigger; frame.primary_scope_identity = kScope;
  frame.primary_scope_root_word = std::uint16_t{4};
  return frame;
}
PrisonerQuoteInternalAliases12004 GenericAliases() {
  PrisonerQuoteInternalAliases12004 aliases{};
  aliases.primary_scope = kScope; aliases.secondary_scope = std::uintptr_t{0};
  aliases.tertiary_scope = kScope; aliases.evaluation_flag_raw_u8 = std::uint8_t{0};
  aliases.primary_scope_root_word = std::uint16_t{4};
  return aliases;
}
GenericMemory GenericFields() {
  GenericMemory memory;
  memory.Put(kScope, std::uint16_t{4}); memory.Put(kTrigger, kVtable);
  memory.Put(kTrigger + 0x38, std::uintptr_t{0});
  memory.Put(kVtable + 0x58, std::uintptr_t{0x5800});
  memory.Put(kVtable + 0x60, std::uintptr_t{0x6000});
  memory.Put(kVtable + 0xC8, std::uintptr_t{0xC800});
  const auto table = kModule + kTriggerScopeTableInlineRva3795A6012004;
  memory.Put(kModule + kTriggerScopeTableGuardRva3795A6012004, std::int32_t{0});
  memory.Put(table, std::uintptr_t{0}); memory.Put(table + 8, std::int32_t{1});
  memory.Put(table + 0xC, std::int32_t{1});
  memory.Put(kModule + kTriggerScopeFallbackRva3795A6012004 + 0x10, std::uintptr_t{0x8000});
  return memory;
}
} // namespace

void RunSourceAutoAcceptTriggerConditionGenericFocus12004() {
  const auto frame = GenericFrame();
  const auto aliases = GenericAliases();
  {
    auto memory = GenericFields();
    const SourceLeafReadOnlyAccess12004 access{&memory, GuardGeneric};
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, frame, aliases);
    auto child_frame = frame; child_frame.producer_rva = 0x372B4C0;
    const auto gate = ReadPrisonerTriggerRootScopeGate12004(access, child_frame);
    const auto condition = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, gate);
    RequireGeneric(raw.frame == frame && raw.query_frame_ready && raw.all_attempted_native_reads_complete &&
        raw.parent_alias_shape_matches == true && raw.source_leaf_scope_word_matches == true,
        "42generic original string snapshot and copied alias identity");
    RequireGeneric(raw.scope_table_provider.frame == frame.read_frame &&
        raw.scope_table_provider.selected_source_fallback == true &&
        raw.scope_table_provider.descriptor_validator_pointer10 == std::uintptr_t{0x8000} &&
        !raw.scope_table_provider.initialized_state && !raw.scope_table_provider.descriptor_validator_returned_raw_u8,
        "42generic retains shared30 raw table without validator truth");
    RequireGeneric(condition.helper_matches_query && condition.scope_table_matches_query &&
        !condition.source_value_ready && !condition.source_projected_returned_raw_u8 && !condition.accepted,
        "42generic no prisoner roles or fabricated native byte");
    child_frame.read_frame.snapshot_identity = "m5/foreign-snapshot";
    const auto foreign = ReadPrisonerTriggerRootScopeGate12004(access, child_frame);
    const auto rejected = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, foreign);
    RequireGeneric(!rejected.helper_matches_query && !rejected.accepted,
        "42generic exact original string identity rejects foreign helper");
  }
  {
    auto memory = GenericFields();
    const SourceLeafReadOnlyAccess12004 access{&memory, GuardGeneric};
    auto wrong_producer = frame; wrong_producer.producer_rva = 0x372DF10;
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, wrong_producer, aliases);
    RequireGeneric(memory.reads == 0 && !raw.query_frame_ready && !raw.any_native_field_read_attempted,
        "42generic rejects parent function tag before all native reads");
  }
  {
    auto memory = GenericFields();
    const SourceLeafReadOnlyAccess12004 access{&memory, GuardGeneric};
    auto different_word = aliases; different_word.primary_scope_root_word = std::uint16_t{3};
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, frame, different_word);
    auto child_frame = frame; child_frame.producer_rva = 0x372B4C0;
    const auto gate = ReadPrisonerTriggerRootScopeGate12004(access, child_frame);
    const auto rejected = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, gate);
    RequireGeneric(raw.source_leaf_scope_word_matches == false &&
        raw.scope_table_provider.caller_copied_root_kind_raw_u16 == std::uint16_t{3} &&
        !rejected.source_value_ready && !rejected.accepted,
        "42generic mismatched copied word stays raw and cannot qualify");
  }
}
} // namespace xar::ck3_12004
