// This command runs only the new component group ABI/source cases.
struct CurrentDynamicComponentsMemory {
  static CurrentDynamicComponentsMemory *current;
  Bytes<0x40> storage{};
  Bytes<0x20> rows{}, selected0{}, selected1{}, fallback{};
  void *storage_pointer = storage.data();
  void *fallback_pointer = fallback.data();
  void *combat = nullptr;
  std::array<void *, 2> expected_selected{selected0.data(), selected1.data()};
  std::array<int, 2> commander_calls{}, aggregate_calls{};
  std::int32_t missing_commander_side = -1;
  static std::int32_t Relation(void *actual, std::int32_t side) {
    Require(actual == current->combat && side >= 0 && side < 2, "actual relation getter ABI");
    return side == 0 ? 0 : 2;
  }
  static std::int64_t *Commander(void *actual, std::int64_t *output, void *selected,
                                  std::int32_t side, std::int32_t relation, void *explanation) {
    Require(actual == current->combat && side >= 0 && side < 2 && output && !explanation &&
                relation == (side == 0 ? 0 : 2) && selected == current->expected_selected[static_cast<std::size_t>(side)],
            "commander getter must use actual resolved selected/fallback and null explanation");
    ++current->commander_calls[static_cast<std::size_t>(side)];
    if (side == current->missing_commander_side) return nullptr;
    *output = side == 0 ? 3'300'000 : 2'100'000;
    return output;
  }
  static std::int64_t *Aggregate(void *actual, std::int64_t *output, void *aggregate,
                                  std::int32_t side, std::int32_t relation, void *explanation) {
    Require(actual == current->combat && side >= 0 && side < 2 && output && !explanation &&
                relation == (side == 0 ? 0 : 2) &&
                aggregate == static_cast<std::byte *>(actual) + 0x130 + static_cast<std::size_t>(side) * 0x348,
            "side getter must use actual side+110, not selected Character aggregate");
    ++current->aggregate_calls[static_cast<std::size_t>(side)];
    *output = side == 0 ? 0 : -100'000;
    return output;
  }
  template <std::size_t N>
  void Install(BattleBindings &bindings, Bytes<N> &actual, bool install_selection = true) {
    current = this;
    combat = actual.data();
    auto &b = bindings.current_dynamic_components;
    b = {true, &storage_pointer, &fallback_pointer, Relation, Commander, Aggregate};
    Put<std::int32_t>(actual, 0x6D0, -3);
    Put<std::int32_t>(actual, 0x6D4, 0);
    Put<std::int32_t>(selected0, 0x18, 0);
    Put<std::int32_t>(selected1, 0x18, 0x01000001);
    Put<std::int32_t>(fallback, 0x18, -1);
    Put(storage, 0x20, rows.data());
    Put<std::uint32_t>(storage, 0x2C, 2);
    Put(rows, 0x08, selected0.data());
    Put(rows, 0x18, selected1.data());
    if (install_selection) {
      Put<std::int32_t>(actual, 0x94, 0);
      Put<std::int32_t>(actual, 0x3DC, 0x01000001);
    }
  }
};
CurrentDynamicComponentsMemory *CurrentDynamicComponentsMemory::current = nullptr;

int RunCurrentDynamicComponentFixtures(const char *directory) {
  try {
    BattleBindings exact{}, older{};
    exact.enabled = older.enabled = true;
    EnableBattleRetainedRuleEffects12003(exact, 0x140000000, xar::ck3_12003::kExecutableSha256);
    EnableBattleRetainedRuleEffects12003(older, 0x140000000, kExecutableSha256);
    Require(exact.current_dynamic_components.enabled && !older.current_dynamic_components.enabled &&
                exact.current_dynamic_components.commander == reinterpret_cast<PhaseCommanderDynamic>(
                    std::uintptr_t{0x140000000} + kPhaseCommanderDynamicRva) &&
                exact.current_dynamic_components.side_aggregate == reinterpret_cast<PhaseSideModifier>(
                    std::uintptr_t{0x140000000} + kPhaseSideModifierRva),
            "exact .3 current component getter binding");
    for (int scenario = 0; scenario < 3; ++scenario) {
      ActualGeographyFixture fixture;
      CurrentDynamicComponentsMemory memory;
      memory.Install(fixture.b, fixture.combat);
      if (scenario == 1) {
        // Same slot, wrong generation: must use canonical fallback.
        Put<std::int32_t>(fixture.combat, 0x3DC, 0x02000001);
        memory.expected_selected[1] = memory.fallback.data();
      } else if (scenario == 2) memory.missing_commander_side = 0;
      BattleTransitionSnapshot frame;
      Require(ReadBattleTransitionSnapshot(fixture.b, fixture.scope, {kActualCombat}, frame) ==
                  BattleTransitionSnapshotStatus::available && frame.battle_transition_ready,
              "current component leaf preserves foreign lifecycle readiness");
      const auto &value = *frame.actual_geography_v1->current_dynamic_components_v1;
      Require(value.sides[0].resolved_character_id_raw == 0 && value.sides[0].used_native_fallback == false &&
                  value.sides[0].relation_kind_raw == 0 && value.sides[0].side_aggregate_dynamic_raw == 0 &&
                  value.sides[1].resolved_character_id_raw == (scenario == 1 ? -1 : 0x01000001) &&
                  value.sides[1].used_native_fallback == (scenario == 1) &&
                  value.sides[1].commander_dynamic_raw == 2'100'000,
              "validID0/zero relation/zero group versus wrong-generation fallback");
      Require(value.sides[0].commander_dynamic_raw.has_value() == (scenario != 2) &&
                  memory.commander_calls[0] == 2 && memory.aggregate_calls[0] == 2 &&
                  !frame.actual_geography_v1->current_dynamic_advantage_v1,
              "independent component failure must not require the old direct leaf");
      frame.snapshot_revision = 2;
      const auto wire = xar::ck3_11906::SerializeBattleTransitionV1(frame);
      Require(wire.find("\"current_dynamic_components_v1\"") != std::string::npos,
              "new components production transition wire");
      const char *names[]{"native-groups.json", "native-fallback.json", "missing-commander.json"};
      if (*directory) WriteWire(directory, names[scenario], wire);
    }
    SelectedRollFixture fixture;
    CurrentDynamicComponentsMemory memory;
    memory.Install(fixture.battle.b, fixture.battle.combat, false);
    fixture.battle.b.current_dynamic_components.character_storage = fixture.battle.b.character_storage_slot;
    memory.expected_selected = {fixture.selected0.data(), fixture.selected1.data()};
    Put<std::int32_t>(fixture.battle.combat, 0x6B0, 2);
    BattleControlSnapshot frame;
    Require(ReadBattleControlSnapshot(fixture.battle.b, fixture.battle.scope, {0x1000001}, frame) ==
                BattleControlSnapshotStatus::available && frame.battle_control_ready,
            "current components owned copy preserves control ownership gate");
    const auto &value = *frame.actual_geography_v1->current_dynamic_components_v1;
    Require(value.sides[0].resolved_character_id_raw == kRollSelected0 &&
                value.sides[1].resolved_character_id_raw == kRollSelected1 &&
                value.sides[0].commander_dynamic_raw == 3'300'000 &&
                value.sides[1].side_aggregate_dynamic_raw == -100'000,
            "owned component leaf uses actual selected identities");
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
    frame.snapshot_revision = 2;
    const auto wire = xar::ck3_11906::SerializeBattleControlSnapshotV1(frame);
    Require(!wire.empty(), "owned components production wire");
    if (*directory) WriteWire(directory, "owned.json", wire);
#endif
    std::cout << "Actual current dynamic component fixture GREEN: 4 new frames; actual=0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "Actual current dynamic component fixture RED: " << error.what() << '\n';
    return 1;
  }
}
