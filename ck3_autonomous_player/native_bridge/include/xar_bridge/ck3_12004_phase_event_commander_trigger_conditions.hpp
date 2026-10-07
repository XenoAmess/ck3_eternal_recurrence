#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/ck3_12004_phase_event_role_compatibility.hpp"
#include "xar_bridge/phase_event_commander_trigger_conditions_v1.hpp"
#include <algorithm>
#include <array>

namespace xar::ck3_12004 {
// actual selector343 directly constructs these token operands, before trigger.
struct PhaseCommanderSideToken12004 {
  std::uint16_t kind = 11, auxiliary = 0;
  std::uint32_t reserved = 0;
  std::uint64_t payload = 0;
};
static_assert(sizeof(PhaseCommanderSideToken12004) == 16);
using PhaseCommanderRootConstruct12004 = void *(*)(void *);
using PhaseCommanderRootDestroy12004 = void (*)(void *);
using PhaseCommanderNamedScopeSave12004 = void (*)(void *, std::int32_t, const PhaseCommanderSideToken12004 *);
using PhaseCommanderTriggerEvaluate12004 = bool (*)(const void *, void *);
struct PhaseCommanderTriggerBindings12004 {
  bool enabled = false;
  PhaseEventRoleCompatibilityBindings12004 roles{};
  std::uintptr_t named_side_key_slot = 0;
  PhaseCommanderRootConstruct12004 root_construct = nullptr;
  PhaseCommanderRootDestroy12004 root_destroy = nullptr;
  PhaseCommanderNamedScopeSave12004 named_scope_save = nullptr;
  PhaseCommanderTriggerEvaluate12004 evaluate_trigger = nullptr;
};
inline PhaseCommanderTriggerBindings12004 BindPhaseCommanderTriggerImage12004(
    std::uintptr_t base, std::string_view sha,
    const PhaseEventRoleCompatibilityBindings12004 &roles) noexcept {
  if (!base || sha != kPhaseRoleExecutableSha256 || !roles.enabled) return {};
  PhaseCommanderTriggerBindings12004 out;
  out.enabled = true; out.roles = roles; out.named_side_key_slot = base + 0x5D4BD6C;
  // Reuse full actual4 callee qualification from religion/context migration.
  out.root_construct = reinterpret_cast<PhaseCommanderRootConstruct12004>(base + 0x889F60);
  out.root_destroy = reinterpret_cast<PhaseCommanderRootDestroy12004>(base + 0x87E0E0);
  out.named_scope_save = reinterpret_cast<PhaseCommanderNamedScopeSave12004>(base + 0x373A0F0);
  out.evaluate_trigger = reinterpret_cast<PhaseCommanderTriggerEvaluate12004>(base + 0x372DF10);
  return out;
}
namespace phase_commander_trigger_detail {
class Scope {
public:
  Scope(const PhaseCommanderTriggerBindings12004 &b, std::uint32_t character,
        std::uint32_t combat, std::uint32_t side, std::int32_t named_key) : bindings_(b) {
    (void)b.root_construct(bytes_.data());
    const std::uint64_t root_kind = 4, character_payload = character;
    std::memcpy(bytes_.data(), &root_kind, 8);
    std::memcpy(bytes_.data() + 8, &character_payload, 8);
    // Native MOVSXD signs Combat FullID; Character MOV zero-extends its DWORD.
    const auto signed_combat = static_cast<std::int32_t>(combat);
    const PhaseCommanderSideToken12004 token{11, static_cast<std::uint16_t>(side), 0,
        static_cast<std::uint64_t>(static_cast<std::int64_t>(signed_combat))};
    b.named_scope_save(bytes_.data() + 0x18, named_key, &token);
  }
  ~Scope() { bindings_.root_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  Scope(const Scope &) = delete;
  Scope &operator=(const Scope &) = delete;
private:
  alignas(8) std::array<std::byte, 0x168> bytes_{};
  const PhaseCommanderTriggerBindings12004 &bindings_;
};
} // namespace phase_commander_trigger_detail
inline game::PhaseEventCommanderTriggerConditionsV1 ReadPhaseCommanderTriggerConditions12004(
    const PhaseCommanderTriggerBindings12004 &b,
    const game::CombatSimulationInputsSnapshot &inputs) {
  game::PhaseEventCommanderTriggerConditionsV1 out;
  out.trigger_source_closed = b.enabled;
  if (!inputs.phase_event_role_compatibility_v1) {
    out.unavailable_reason = "same_query_loaded_role_inputs_not_published"; return out;
  }
  const auto &roles = *inputs.phase_event_role_compatibility_v1;
  const auto *identities = inputs.phase_event_commander_side_identity_v1
      ? &*inputs.phase_event_commander_side_identity_v1 : nullptr;
  const auto read = [&](std::uintptr_t address, auto &value) {
    return b.roles.read_bytes && b.roles.read_bytes(address, &value, sizeof(value), b.roles.read_context);
  };
  // Role DTO has already read count/role operands; reacquire only pointers
  // needed to obtain each demanded inline trigger receiver. No second query.
  std::uintptr_t database = 0, array = 0;
  const bool receivers = b.enabled && read(b.roles.registry_pointer_slot, database) && database &&
      read(database + 0x50, array);
  std::int32_t named_key = 0;
  const bool key_ready = b.enabled && read(b.named_side_key_slot, named_key);
  const bool callbacks = b.root_construct && b.root_destroy && b.named_scope_save && b.evaluate_trigger;
  bool all_ready = true, any_known = false;
  for (const auto &source : roles.occurrences) {
    if (source.phase_role != "commander") continue;
    game::PhaseEventCommanderTriggerOccurrenceV1 row;
    row.occurrence_index = source.occurrence_index; row.character_id = source.character_id;
    row.source_public_cunit_id = source.source_public_cunit_id;
    row.source_native_carmy_id = source.source_native_carmy_id;
    row.encounter_role = source.encounter_role;
    const game::PhaseEventCommanderSideIdentityOccurrenceV1 *identity = nullptr;
    if (identities) {
      const auto found = std::find_if(identities->occurrences.begin(), identities->occurrences.end(),
          [&](const auto &item) { return item.occurrence_index == source.occurrence_index; });
      if (found != identities->occurrences.end()) identity = &*found;
    }
    if (identity) {
      row.actual_combat_full_id_raw = identity->actual_selected_combat_full_id_raw;
      row.actual_side_index = identity->actual_side_index;
    }
    if (key_ready) row.loaded_named_side_key_raw = named_key;
    const bool current_identity = identity && identity->full_id_equal == true &&
        identity->actual_selected_combat_full_id_raw && identity->actual_side_index;
    row.current_commander_context_ready = b.enabled && source.native_role_argument_source_closed &&
        current_identity && key_ready && callbacks;
    const bool registry_observed = roles.loaded_registry.count_raw &&
        *roles.loaded_registry.count_raw >= 0 &&
        source.conditions.size() == static_cast<std::size_t>(*roles.loaded_registry.count_raw);
    const auto context_reason = !current_identity ? "v2_commander_not_current_side_commander" :
        !key_ready ? "loaded_combat_side_name_key_unavailable" : "native_trigger_scope_binding_unavailable";
    const auto collect = [&](void *scope) {
      for (const auto &condition : source.conditions) {
        game::PhaseEventCommanderTriggerConditionV1 value;
        value.loaded_row_index = condition.loaded_row_index;
        value.role_compatible = condition.role_compatible;
        if (!condition.role_compatible) {
          value.unavailable_reason = condition.unavailable_reason.empty()
              ? "loaded_event_role_operand_unavailable" : condition.unavailable_reason;
        } else if (!*condition.role_compatible) {
          value.role_and_trigger_valid = false;
        } else {
          ++row.role_compatible_count;
          std::uintptr_t event = 0;
          if (!scope) value.unavailable_reason = context_reason;
          else if (!receivers || !array ||
                   !read(array + static_cast<std::uintptr_t>(condition.loaded_row_index) * 8, event) || !event)
            value.unavailable_reason = "loaded_event_trigger_receiver_unavailable";
          else {
            value.native_trigger_valid = b.evaluate_trigger(reinterpret_cast<const void *>(event + 0x40), scope);
            value.role_and_trigger_valid = value.native_trigger_valid; ++row.evaluated_count;
          }
        }
        if (value.role_and_trigger_valid == true) ++row.admitted_count;
        if (!value.role_and_trigger_valid) ++row.unknown_count;
        else any_known = true;
        row.conditions.push_back(std::move(value));
      }
    };
    const bool needs_scope = std::any_of(source.conditions.begin(), source.conditions.end(),
        [](const auto &condition) { return condition.role_compatible == true; });
    if (row.current_commander_context_ready && needs_scope) {
      phase_commander_trigger_detail::Scope scope(b, row.character_id,
          *row.actual_combat_full_id_raw, *row.actual_side_index, named_key);
      collect(scope.get());
    } else collect(nullptr);
    row.role_trigger_observation_ready = registry_observed && row.unknown_count == 0;
    if (row.role_trigger_observation_ready) row.status = "available";
    else {
      row.status = row.conditions.size() > row.unknown_count ? "partial" : "unavailable";
      row.unavailable_reason = registry_observed ? "current_commander_trigger_conditions_incomplete"
                                                : "same_query_loaded_role_registry_unavailable";
      all_ready = false;
    }
    if (row.evaluated_count) out.native_role_and_trigger_evaluation_observed = true;
    out.occurrences.push_back(std::move(row));
  }
  out.status = all_ready ? "available" : any_known ? "partial" : "unavailable";
  if (!all_ready) out.unavailable_reason = "current_commander_trigger_conditions_incomplete";
  return out;
}
inline void AttachPhaseCommanderTriggerConditions12004(
    const PhaseCommanderTriggerBindings12004 &bindings,
    game::CombatSimulationInputsSnapshot &inputs) noexcept {
  if (!bindings.enabled) return;
  try { inputs.phase_event_commander_trigger_conditions_v1 = ReadPhaseCommanderTriggerConditions12004(bindings, inputs); }
  catch (...) { inputs.phase_event_commander_trigger_conditions_v1.reset(); }
}
} // namespace xar::ck3_12004
