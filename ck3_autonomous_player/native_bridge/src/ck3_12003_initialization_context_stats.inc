// Frozen-current first initialization input: 24E0EB0 ->264DE30->2657AC0.
// A later whole-side refresh under changed battle context is a separate stage.
void ReadInitializationContextStats12003(
    const CombatBindings &bindings, void *regiment,
    void *validated_current_province, std::int32_t current_province_id,
    std::int32_t target_province_id, CombatRegimentSnapshot &output) noexcept {
  if (validated_current_province == nullptr ||
      current_province_id == target_province_id) {
    return;
  }
  output.initialization_context_stats.emplace();
  ReadEncounterEffectiveStats(bindings, regiment, validated_current_province,
                             output.regiment_id, current_province_id,
                             *output.initialization_context_stats);
}
