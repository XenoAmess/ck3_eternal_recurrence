// New command only: actual Combat/direct getter ABI and production wire.
struct CurrentDynamicAdvantageMemory {
  static CurrentDynamicAdvantageMemory *current;
  void *combat = nullptr;
  std::array<std::int64_t, 2> totals{7'654'321, -987'654};
  std::array<int, 2> calls{};
  std::int32_t unavailable_side = -1;
  static std::int64_t *Read(void *actual, std::int64_t *output,
                            std::int32_t side, void *explanation) {
    Require(actual == current->combat && output && side >= 0 && side < 2 && !explanation,
            "258A470 requires actual Combat/local output/native side/null explanation");
    const auto index = static_cast<std::size_t>(side);
    ++current->calls[index];
    if (side == current->unavailable_side) return nullptr;
    *output = current->totals[index];
    return output;
  }
  template <std::size_t N>
  void Install(BattleBindings &bindings, Bytes<N> &actual) {
    current = this;
    combat = actual.data();
    bindings.current_dynamic_advantage_enabled = true;
    bindings.current_read_side_dynamic = Read;
    Put<std::int64_t>(actual, 0x6C8, 9'900'000);
    Put<std::int64_t>(actual, 0x710, -44'556'677);
    Put<std::int32_t>(actual, 0x6D0, -3);
    Put<std::int32_t>(actual, 0x6D4, 0);
  }
};
CurrentDynamicAdvantageMemory *CurrentDynamicAdvantageMemory::current = nullptr;

int RunCurrentDynamicAdvantageFixtures(const char *directory) {
  try {
    BattleBindings exact{}, older{};
    exact.enabled = older.enabled = true;
    EnableBattleRetainedRuleEffects12003(exact, 0x140000000, xar::ck3_12003::kExecutableSha256);
    EnableBattleRetainedRuleEffects12003(older, 0x140000000, kExecutableSha256);
    Require(exact.current_dynamic_advantage_enabled && !older.current_dynamic_advantage_enabled &&
                exact.current_read_side_dynamic == reinterpret_cast<ReadPhaseDynamic>(
                    std::uintptr_t{0x140000000} + kReadPhaseDynamicRva),
            "current direct getter exact .3 binding must reuse 258A470");
    for (int scenario = 0; scenario < 3; ++scenario) {
      ActualGeographyFixture fixture;
      CurrentDynamicAdvantageMemory memory;
      memory.Install(fixture.b, fixture.combat);
      Put<std::int32_t>(fixture.combat, 0x94, 0);
      Put<std::int32_t>(fixture.combat, 0x3DC, -1);
      if (scenario == 1) memory.totals[0] = 0;
      if (scenario == 2) memory.unavailable_side = 0;
      BattleTransitionSnapshot frame;
      Require(ReadBattleTransitionSnapshot(fixture.b, fixture.scope, {kActualCombat}, frame) ==
                  BattleTransitionSnapshotStatus::available && frame.battle_transition_ready,
              "foreign direct totals must preserve current lifecycle");
      const auto &value = *frame.actual_geography_v1->current_dynamic_advantage_v1;
      Require(value.base_advantage_raw == 9'900'000 && value.stored_resolved_advantage_raw == -44'556'677 &&
                  value.sides[0].current_roll_points == -3 && value.sides[1].current_roll_points == 0 &&
                  value.sides[0].selected_character_id_raw == 0 && value.sides[1].selected_character_id_raw == -1,
              "direct input scalars retain signed current values and raw full IDs");
      Require(memory.calls[0] == 2 && memory.calls[1] == 2 &&
                  value.sides[1].side_dynamic_total_raw == memory.totals[1] &&
                  value.sides[0].side_dynamic_total_raw ==
                      (scenario == 2 ? std::optional<std::int64_t>{} : std::optional<std::int64_t>{memory.totals[0]}),
              "paired read uses independently nullable actual direct totals");
      frame.snapshot_revision = 2;
      const auto wire = xar::ck3_11906::SerializeBattleTransitionV1(frame);
      Require(wire.find("\"current_dynamic_advantage_v1\"") != std::string::npos,
              "current direct totals production transition serializer missing");
      const char *names[]{"current-values.json", "zero-total.json", "unavailable-side.json"};
      if (*directory) WriteWire(directory, names[scenario], wire);
    }
    SelectedRollFixture fixture;
    CurrentDynamicAdvantageMemory memory;
    memory.Install(fixture.battle.b, fixture.battle.combat);
    Put<std::int32_t>(fixture.battle.combat, 0x6B0, 2);
    BattleControlSnapshot frame;
    Require(ReadBattleControlSnapshot(fixture.battle.b, fixture.battle.scope, {0x1000001}, frame) ==
                BattleControlSnapshotStatus::available && frame.battle_control_ready,
            "owned direct totals must preserve existing ownership/control gate");
    const auto &value = *frame.actual_geography_v1->current_dynamic_advantage_v1;
    Require(value.base_advantage_raw == frame.base_advantage_raw &&
                value.stored_resolved_advantage_raw == frame.resolved_advantage_raw &&
                value.sides[0].side_dynamic_total_raw == memory.totals[0] &&
                value.sides[1].side_dynamic_total_raw == memory.totals[1],
            "owned actual direct value copy must remain separate from stored710");
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
    frame.snapshot_revision = 2;
    const auto wire = xar::ck3_11906::SerializeBattleControlSnapshotV1(frame);
    Require(!wire.empty(), "owned direct totals production serializer failed");
    if (*directory) WriteWire(directory, "owned.json", wire);
#endif
    const auto unbound = ReadCurrentDynamicAdvantage12003(fixture.battle.combat.data(), nullptr);
    Require(!unbound.sides[0].side_dynamic_total_raw && !unbound.sides[1].side_dynamic_total_raw &&
                unbound.sides[0].unavailable_reason == "current_side_dynamic_getter_258A470_unbound",
            "missing direct binding must be independently unavailable with its concrete RVA");
    std::cout << "Actual current dynamic advantage fixture GREEN: 4 frames; actual=0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "Actual current dynamic advantage fixture RED: " << error.what() << '\n';
    return 1;
  }
}
