// New scoped cached19F observations only. No old fixture command is executed.
struct OwnNestedModifierMemory {
  static OwnNestedModifierMemory *current;
  CurrentDynamicComponentsMemory selected;
  OppositeEffectEligibilityMemory retained;
  std::array<Bytes<0x100>, 2> character_aggregate{};
  std::array<std::int64_t, 2> side_amount{25'000, 0};
  std::array<std::int64_t, 2> character_amount{-5'000'000'001, -70'000};
  void *combat = nullptr;
  static void *CharacterAggregate(void *character) {
    for (std::size_t side = 0; side < 2; ++side)
      if (character == current->selected.expected_selected[side])
        return current->character_aggregate[side].data();
    throw std::runtime_error("own19F must use actual resolved selected Character");
  }
  static std::int64_t *Modifier(void *component, std::int64_t *output, std::int32_t id) {
    Require(output && id == 0x19F, "own19F output pointer and numeric modifier ID ABI");
    for (std::size_t side = 0; side < 2; ++side) {
      if (component == static_cast<std::byte *>(current->combat) + 0x198 + side * 0x348) {
        *output = current->side_amount[side];
        return output;
      }
      if (component == current->character_aggregate[side].data() + 0x68) {
        *output = current->character_amount[side];
        return output;
      }
    }
    throw std::runtime_error("2303700 must receive whole aggregate+68 sparse component");
  }
  template <std::size_t N>
  void Install(BattleBindings &bindings, Bytes<N> &actual, bool install_selection = true) {
    current = this;
    combat = actual.data();
    retained.Install(bindings, actual);
    selected.Install(bindings, actual, install_selection);
    bindings.current_dynamic_components.enabled = false;
    bindings.current_own_nested_modifier = {true, CharacterAggregate, Modifier};
  }
};
OwnNestedModifierMemory *OwnNestedModifierMemory::current = nullptr;

int RunOwnNestedModifierFixtures(const char *directory) {
  try {
    BattleBindings exact{}, older{};
    exact.enabled = older.enabled = true;
    EnableBattleRetainedRuleEffects12003(exact, 0x140000000, xar::ck3_12003::kExecutableSha256);
    EnableBattleRetainedRuleEffects12003(older, 0x140000000, kExecutableSha256);
    Require(exact.current_own_nested_modifier.enabled && !older.current_own_nested_modifier.enabled &&
                exact.current_own_nested_modifier.modifier == reinterpret_cast<ReadCharacterModifier>(
                    std::uintptr_t{0x140000000} + 0x2303700) &&
                exact.current_own_nested_modifier.character_aggregate == reinterpret_cast<GetCharacterModifierAggregator>(
                    std::uintptr_t{0x140000000} + 0x28C3AE0),
            "exact .3 current cached own19F bindings");
    for (int scenario = 0; scenario < 3; ++scenario) {
      ActualGeographyFixture fixture;
      OwnNestedModifierMemory memory;
      memory.Install(fixture.b, fixture.combat);
      if (scenario == 1) {
        memory.side_amount = {0, 0};
        memory.character_amount = {0, 0};
        Put<void *>(memory.retained.stored.defender, 0x10, nullptr);
      } else if (scenario == 2) fixture.b.current_dynamic_components.character_storage = nullptr;
      BattleTransitionSnapshot frame;
      Require(ReadBattleTransitionSnapshot(fixture.b, fixture.scope, {kActualCombat}, frame) ==
                  BattleTransitionSnapshotStatus::available && frame.battle_transition_ready,
              "new own19F leaf preserves foreign current lifecycle");
      const auto &own = *frame.actual_geography_v1->current_own_nested_modifier_v1;
      Require(own.sides[0].combat_side_aggregate.amount_raw == (scenario == 1 ? 0 : 25'000) &&
                  own.sides[1].combat_side_aggregate.amount_raw == 0,
              "actual side+110 cached zero and nonzero are independent observations");
      if (scenario == 2) {
        Require(!own.sides[0].selected_character_aggregate.amount_raw &&
                    !own.sides[0].resolved_character_id_raw &&
                    own.sides[0].selected_character_aggregate.unavailable_reason ==
                        "selected_character_storage_5C67568_unbound",
                "missing selection does not erase actual Combat side aggregate");
      } else Require(own.sides[0].resolved_character_id_raw == 0 &&
                         own.sides[0].used_native_fallback == false &&
                         own.sides[0].selected_character_aggregate.amount_raw ==
                             (scenario == 1 ? 0 : -5'000'000'001),
                     "selected actual Character19F scope and zero source lineage");
      Require(!frame.actual_geography_v1->current_dynamic_components_v1,
              "independent own amount observer does not require component totals");
      frame.snapshot_revision = 2;
      const auto wire = xar::ck3_11906::SerializeBattleTransitionV1(frame);
      Require(wire.find("\"current_own_nested_modifier_v1\"") != std::string::npos,
              "own19F real production transition serializer");
      const char *names[]{"own-values.json", "zero-shortcircuit.json", "missing-character.json"};
      if (*directory) WriteWire(directory, names[scenario], wire);
    }
    SelectedRollFixture fixture;
    OwnNestedModifierMemory memory;
    memory.Install(fixture.battle.b, fixture.battle.combat, false);
    fixture.battle.b.current_dynamic_components.character_storage = fixture.battle.b.character_storage_slot;
    memory.selected.expected_selected = {fixture.selected0.data(), fixture.selected1.data()};
    Put<std::int32_t>(fixture.battle.combat, 0x6B0, 2);
    BattleControlSnapshot frame;
    Require(ReadBattleControlSnapshot(fixture.battle.b, fixture.battle.scope, {0x1000001}, frame) ==
                BattleControlSnapshotStatus::available && frame.battle_control_ready,
            "owned own19F copy retains existing ownership gate");
    const auto &own = *frame.actual_geography_v1->current_own_nested_modifier_v1;
    Require(own.sides[0].resolved_character_id_raw == kRollSelected0 &&
                own.sides[1].resolved_character_id_raw == kRollSelected1 &&
                own.sides[0].combat_side_aggregate.amount_raw == 25'000 &&
                own.sides[0].selected_character_aggregate.amount_raw == -5'000'000'001,
            "owned copy preserves both independently named aggregate scopes");
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
    frame.snapshot_revision = 2;
    const auto wire = xar::ck3_11906::SerializeBattleControlSnapshotV1(frame);
    Require(!wire.empty(), "owned own19F production serializer");
    if (*directory) WriteWire(directory, "owned.json", wire);
#endif
    std::cout << "Actual own19F fixture GREEN: 4 new frames; actual=0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "Actual own19F fixture RED: " << error.what() << '\n';
    return 1;
  }
}
