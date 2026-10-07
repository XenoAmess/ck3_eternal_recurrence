#pragma once

#include "xar_bridge/ck3_12004_phase_event_commander_trigger_conditions.hpp"
#include "xar_bridge/phase_event_commander_chance_weights_v1.hpp"
#include <bit>

namespace xar::ck3_12004 {
using PhaseCommanderChanceEvaluate12004 = std::int64_t *(*)(const void *, std::int64_t *, void *);
struct PhaseCommanderChanceBindings12004 {
  bool enabled = false;
  PhaseCommanderTriggerBindings12004 trigger{};
  PhaseCommanderChanceEvaluate12004 evaluate_chance = nullptr;
};
inline PhaseCommanderChanceBindings12004 BindPhaseCommanderChanceImage12004(
    std::uintptr_t base, std::string_view sha,
    const PhaseCommanderTriggerBindings12004 &trigger) noexcept {
  if (!base || sha != kPhaseRoleExecutableSha256 || !trigger.enabled) return {};
  // Actual selector suffix53 returns this CALL target. Full actual241 body
  // is already qualified by current4-ransom/support_owner_layout.
  return {true, trigger, reinterpret_cast<PhaseCommanderChanceEvaluate12004>(base + 0x3761680)};
}
inline std::int32_t PhaseCommanderSelectionWeight12004(std::int64_t raw) noexcept {
  // Actual signed MULHI/SAR14/sign correction implements truncation toward
  // zero by100000, then MOV stores only its low DWORD. Do not clamp.
  return std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(raw / 100000));
}
inline game::PhaseEventCommanderChanceWeightsV1 ReadPhaseCommanderChanceWeights12004(
    const PhaseCommanderChanceBindings12004 &b,
    const game::CombatSimulationInputsSnapshot &inputs) {
  game::PhaseEventCommanderChanceWeightsV1 out;
  out.chance_source_closed = b.enabled;
  if (!inputs.phase_event_commander_trigger_conditions_v1 || !inputs.phase_event_role_compatibility_v1) {
    out.unavailable_reason = "same_query_commander_role_trigger_inputs_not_published"; return out;
  }
  const auto &triggers = *inputs.phase_event_commander_trigger_conditions_v1;
  const auto &registry = inputs.phase_event_role_compatibility_v1->loaded_registry;
  const auto read = [&](std::uintptr_t address, auto &value) {
    return b.trigger.roles.read_bytes && b.trigger.roles.read_bytes(
        address, &value, sizeof(value), b.trigger.roles.read_context);
  };
  std::uintptr_t database = 0, array = 0;
  const bool receivers = b.enabled && read(b.trigger.roles.registry_pointer_slot, database) && database &&
      read(database + 0x50, array);
  const bool callbacks = b.trigger.root_construct && b.trigger.root_destroy &&
      b.trigger.named_scope_save && b.evaluate_chance;
  bool all_ready = true, any_known = false;
  for (const auto &source : triggers.occurrences) {
    game::PhaseEventCommanderChanceOccurrenceV1 row;
    row.occurrence_index = source.occurrence_index; row.character_id = source.character_id;
    row.source_public_cunit_id = source.source_public_cunit_id;
    row.source_native_carmy_id = source.source_native_carmy_id;
    row.encounter_role = source.encounter_role;
    row.actual_combat_full_id_raw = source.actual_combat_full_id_raw;
    row.actual_side_index = source.actual_side_index;
    row.loaded_named_side_key_raw = source.loaded_named_side_key_raw;
    row.current_commander_context_ready = b.enabled && callbacks && source.current_commander_context_ready &&
        row.actual_combat_full_id_raw && row.actual_side_index && row.loaded_named_side_key_raw;
    const bool registry_observed = registry.count_raw && *registry.count_raw >= 0 &&
        source.conditions.size() == static_cast<std::size_t>(*registry.count_raw);
    const auto collect = [&](void *scope) {
      for (const auto &condition : source.conditions) {
        game::PhaseEventCommanderChanceConditionV1 value;
        value.loaded_row_index = condition.loaded_row_index;
        value.role_and_trigger_valid = condition.role_and_trigger_valid;
        if (!condition.role_and_trigger_valid) {
          value.unavailable_reason = condition.unavailable_reason.empty()
              ? "current_commander_role_trigger_condition_unavailable" : condition.unavailable_reason;
          ++row.unknown_count;
        } else if (!*condition.role_and_trigger_valid) {
          // The original selector never evaluates chance for rejected rows.
          ++row.not_admitted_count; any_known = true;
        } else {
          ++row.admitted_count;
          std::uintptr_t event = 0;
          if (!scope) value.unavailable_reason = "native_current_commander_chance_context_unavailable";
          else if (!receivers || !array ||
                   !read(array + static_cast<std::uintptr_t>(condition.loaded_row_index) * 8, event) || !event)
            value.unavailable_reason = "loaded_event_chance_receiver_unavailable";
          else {
            std::int64_t raw = 0;
            // Actual caller passes row+110, caller-owned s64 output and the
            // exact same Character/physical Side scope used by its trigger.
            const auto *result = b.evaluate_chance(reinterpret_cast<const void *>(event + 0x110), &raw, scope);
            if (result) {
              value.chance_raw = *result;
              value.selection_weight_raw = PhaseCommanderSelectionWeight12004(*result);
              ++row.evaluated_count; any_known = true;
            } else value.unavailable_reason = "native_loaded_chance_value_unavailable";
          }
          if (!value.chance_raw) ++row.unknown_count;
        }
        row.conditions.push_back(std::move(value));
      }
    };
    const bool needs_scope = std::any_of(source.conditions.begin(), source.conditions.end(),
        [](const auto &condition) { return condition.role_and_trigger_valid == true; });
    if (row.current_commander_context_ready && needs_scope) {
      phase_commander_trigger_detail::Scope scope(b.trigger, row.character_id,
          *row.actual_combat_full_id_raw, *row.actual_side_index, *row.loaded_named_side_key_raw);
      collect(scope.get());
    } else collect(nullptr);
    row.chance_weight_observation_ready = registry_observed && row.unknown_count == 0;
    if (row.chance_weight_observation_ready) row.status = "available";
    else {
      row.status = row.evaluated_count || row.not_admitted_count ? "partial" : "unavailable";
      row.unavailable_reason = registry_observed ? "current_commander_chance_weights_incomplete"
                                                : "same_query_loaded_role_registry_unavailable";
      all_ready = false;
    }
    if (row.evaluated_count) out.native_chance_evaluation_observed = true;
    out.occurrences.push_back(std::move(row));
  }
  out.status = all_ready ? "available" : any_known ? "partial" : "unavailable";
  if (!all_ready) out.unavailable_reason = "current_commander_chance_weights_incomplete";
  return out;
}
inline void AttachPhaseCommanderChanceWeights12004(
    const PhaseCommanderChanceBindings12004 &bindings,
    game::CombatSimulationInputsSnapshot &inputs) noexcept {
  if (!bindings.enabled) return;
  try { inputs.phase_event_commander_chance_weights_v1 = ReadPhaseCommanderChanceWeights12004(bindings, inputs); }
  catch (...) { inputs.phase_event_commander_chance_weights_v1.reset(); }
}
} // namespace xar::ck3_12004
