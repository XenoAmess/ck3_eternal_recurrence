#include "xar_bridge/prisoner_auto_accept_trigger_condition_12004.hpp"
#include "xar_bridge/prisoner_trigger_root_scope_gate_12004.hpp"

#include <array>
#include <cstring>
#include <map>
#include <stdexcept>
#include <utility>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kRoot = 0x2000;
constexpr std::uintptr_t kTrigger = 0x3000;
constexpr std::uintptr_t kVtable = 0x4000;
struct Memory {
  std::map<std::uintptr_t, std::vector<std::uint8_t>> fields;
  std::size_t reads = 0;
  template <typename T> void Put(std::uintptr_t address, T value) {
    std::vector<std::uint8_t> bytes(sizeof(T));
    std::memcpy(bytes.data(), &value, sizeof(T));
    fields[address] = std::move(bytes);
  }
};
bool Guard(void *context, const void *address, void *output, std::size_t size) noexcept {
  auto &memory = *static_cast<Memory *>(context); ++memory.reads;
  const auto it = memory.fields.find(reinterpret_cast<std::uintptr_t>(address));
  if (it == memory.fields.end() || it->second.size() != size) return false;
  std::memcpy(output, it->second.data(), size); return true;
}
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
PrisonerQuoteSourceFrame12004 Frame() {
  PrisonerQuoteSourceFrame12004 frame{};
  frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
  frame.module_base = 0x100000; frame.native_revision = 7;
  frame.query_sequence = 11; frame.proof_epoch = 13; frame.date_raw = 29;
  frame.jailer_full_id = 0x01000123U; frame.prisoner_full_id = 0x02000456U;
  frame.recipient_full_id = 0x03000789U; frame.definition_identity = 0x5000;
  frame.interaction_context_identity = kRoot - 8; frame.original_scope_identity = kRoot;
  frame.roles_verified_in_owned_context = true; frame.same_frame_confirmed = true;
  return frame;
}
PrisonerQuoteInternalAliases12004 Aliases(std::uint16_t kind) {
  PrisonerQuoteInternalAliases12004 aliases{};
  aliases.primary_scope = kRoot; aliases.secondary_scope = std::uintptr_t{0};
  aliases.tertiary_scope = kRoot; aliases.primary_scope_root_word = kind;
  aliases.evaluation_flag_raw_u8 = std::uint8_t{0};
  // The support storage/internal pointer are not supplied by this copied shape.
  return aliases;
}
Memory Fields(std::uint16_t kind) {
  Memory memory;
  memory.Put(kRoot, kind); memory.Put(kTrigger, kVtable);
  memory.Put(kTrigger + 0x38, std::uintptr_t{0});
  memory.Put(kVtable + 0x58, std::uintptr_t{0x5800});
  memory.Put(kVtable + 0x60, std::uintptr_t{0x6000});
  memory.Put(kVtable + 0xC8, std::uintptr_t{0xC800});
  return memory;
}
PrisonerTriggerRootScopeGateResult12004 ConditionalGate(
    const PrisonerQuoteSourceFrame12004 &frame, std::uint16_t kind, bool empty_mask) {
  PrisonerTriggerRootScopeGateConditionalInput12004 input{};
  input.frame = frame; input.trigger_identity = kTrigger; input.primary_scope_identity = kRoot;
  input.root_scope_kind_raw_u16 = kind; input.preferred_kind_return_ax_raw_u16 = std::uint16_t{0};
  input.mask_return_words_raw_u64 = std::array<std::uint64_t, 2>{empty_mask ? 0ULL : 1ULL, 0ULL};
  return ProjectPrisonerTriggerRootScopeGate12004(input);
}
} // namespace

// Only the new35c connected compound calls this no-main fragment.
void RunPrisonerAutoAcceptTriggerConditionFocus12004() {
  const auto frame = Frame();
  {
    auto memory = Fields(std::uint16_t{4});
    const PrisonerQuoteReadOnlyAccess12004 access{&memory, Guard};
    const auto aliases = Aliases(std::uint16_t{4});
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, frame, aliases, kTrigger);
    const auto gate = ReadPrisonerTriggerRootScopeGate12004(access, frame, kTrigger, kRoot);
    const auto condition = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, gate);
    Require(raw.all_attempted_native_reads_complete && raw.evaluator_slotc8 == std::uintptr_t{0xC800}, "42c exact raw slot copy");
    Require(raw.support_report_identity38 == std::uintptr_t{0} && !raw.aliases.support118_identity &&
        !raw.aliases.physical_aliases_copied, "42c copied-null versus absent support");
    Require(condition.helper_matches_query && condition.root_validator_bypassed == false &&
        !condition.root_scope_source_valid && !condition.accepted && !condition.source_value_ready,
        "42c nonzero root validator remains unknown");
  }
  {
    auto memory = Fields(std::uint16_t{0});
    const PrisonerQuoteReadOnlyAccess12004 access{&memory, Guard};
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, frame, Aliases(std::uint16_t{0}), kTrigger);
    const auto condition = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, ConditionalGate(frame, std::uint16_t{0}, true));
    Require(condition.root_scope_source_valid == true && condition.conditional_reaches_virtual_c8 == true,
        "42c zero-kind conditional progression");
    Require(!condition.source_projected_returned_raw_u8 && !condition.accepted &&
        !condition.final_virtual_evaluator_source_ready && !condition.actual_trigger_evaluation_observed &&
        !condition.native_callback_executed, "42c conditional permission never accepts");
    const auto blocked = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, ConditionalGate(frame, std::uint16_t{0}, false));
    Require(blocked.helper_conditional_allows == false && blocked.conditional_reaches_virtual_c8 == false &&
        !blocked.accepted && !blocked.source_projected_returned_raw_u8,
        "42c supplied conditional failure does not qualify a native return");
    auto other_frame = frame; ++other_frame.query_sequence;
    const auto mismatched = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, ConditionalGate(other_frame, std::uint16_t{0}, true));
    Require(!mismatched.helper_matches_query && !mismatched.helper_conditional_allows && !mismatched.accepted,
        "42c foreign query result rejected");
  }
  {
    auto memory = Fields(std::uint16_t{0}); memory.fields.erase(kTrigger);
    const PrisonerQuoteReadOnlyAccess12004 access{&memory, Guard};
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, frame, Aliases(std::uint16_t{0}), kTrigger);
    Require(!raw.trigger_vtable && !raw.evaluator_slotc8 && raw.support_report_identity38 == std::uintptr_t{0} &&
        !raw.all_attempted_native_reads_complete && !raw.missing_fields.empty(), "42c partial reads retain other fields");
  }
  {
    auto memory = Fields(std::uint16_t{0});
    const PrisonerQuoteReadOnlyAccess12004 access{&memory, Guard};
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, frame, Aliases(std::uint16_t{0}), std::uintptr_t{0});
    const auto condition = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, {});
    Require(memory.reads == 0 && raw.trigger_identity == std::uintptr_t{0} &&
        !raw.actual_trigger_evaluation_observed && !condition.accepted, "42c null trigger stays parent scalar branch");
  }
  {
    auto memory = Fields(std::uint16_t{0});
    const PrisonerQuoteReadOnlyAccess12004 access{&memory, Guard};
    auto aliases = Aliases(std::uint16_t{0}); aliases.primary_scope = kRoot + 1;
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, frame, aliases, kTrigger);
    const auto condition = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, ConditionalGate(frame, std::uint16_t{0}, true));
    Require(raw.parent_alias_shape_matches == false && !condition.helper_matches_query && !condition.accepted,
        "42c mismatched alias receiver cannot progress");
  }
  {
    auto memory = Fields(std::uint16_t{0});
    const PrisonerQuoteReadOnlyAccess12004 access{&memory, Guard};
    auto unready = frame; unready.proof_epoch = 0;
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, unready, Aliases(std::uint16_t{0}), kTrigger);
    Require(memory.reads == 0 && !raw.query_frame_ready && !raw.any_native_field_read_attempted,
        "42c source admission precedes native reads");
  }
  {
    auto memory = Fields(std::uint16_t{0}); memory.Put(kTrigger, std::uintptr_t{0});
    const PrisonerQuoteReadOnlyAccess12004 access{&memory, Guard};
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(access, frame, Aliases(std::uint16_t{0}), kTrigger);
    const auto gate = ReadPrisonerTriggerRootScopeGate12004(access, frame, kTrigger, kRoot);
    const auto condition = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, gate);
    Require(raw.trigger_vtable == std::uintptr_t{0} && raw.all_attempted_native_reads_complete &&
        !raw.evaluator_slotc8 && !condition.accepted, "42c known-null vtable never supplies an output");
  }
}
} // namespace xar::ck3_12004
