// Included inside the focused fixture namespace, reusing existing resolved
// foreign/owned Combat memory. This command executes only the new source cases.
struct StoredAdvantageMemory {
  LoadedEffectMemory effects{2};
  Bytes<0x30> attacker{};
  Bytes<0x20> defender{};
  template <std::size_t N>
  void Install(BattleBindings &bindings, Bytes<N> &combat) {
    bindings.stored_advantage_sources_enabled = true;
    Put(attacker, 0x00, effects.effects[0].data());
    Put<std::int64_t>(attacker, 0x08, 7'654'321);
    Put(attacker, 0x10, effects.effects[2].data());
    Put<std::int64_t>(attacker, 0x18, 0);
    Put(attacker, 0x20, effects.effects[1].data());
    Put<std::int64_t>(attacker, 0x28, -333'333);
    Put(defender, 0x00, effects.effects[1].data());
    Put<std::int64_t>(defender, 0x08, 125'000);
    Put<void *>(defender, 0x10, nullptr);
    Put<std::int64_t>(defender, 0x18, -987'654);
    Fixture::Array(combat, 0x98, attacker.data(), 3);
    Fixture::Array(combat, 0x3E0, defender.data(), 2);
    Put<std::int64_t>(combat, 0x6C8, 9'900'000);
    Put<std::int64_t>(combat, 0x710, -44'556'677);
  }
};

int RunStoredAdvantageSourceFixtures(const char *directory) {
  try {
    BattleBindings exact{}, older{};
    exact.enabled = older.enabled = true;
    EnableBattleRetainedRuleEffects12003(exact, 0x140000000, xar::ck3_12003::kExecutableSha256);
    EnableBattleRetainedRuleEffects12003(older, 0x140000000, kExecutableSha256);
    Require(exact.stored_advantage_sources_enabled && !older.stored_advantage_sources_enabled,
            "stored sources require exact .3 enable path");
    for (int scenario = 0; scenario < 3; ++scenario) {
      ActualGeographyFixture fixture;
      StoredAdvantageMemory memory;
      memory.Install(fixture.b, fixture.combat);
      if (scenario == 1) {
        Fixture::Array(fixture.combat, 0x98, nullptr, 0);
        Put<std::int64_t>(fixture.combat, 0x6C8, 0);
        Put<std::int64_t>(fixture.combat, 0x710, 0);
      } else if (scenario == 2) {
        Fixture::Array(fixture.combat, 0x98, nullptr, 1);
      }
      BattleTransitionSnapshot frame;
      Require(ReadBattleTransitionSnapshot(fixture.b, fixture.scope, {kActualCombat}, frame) ==
                  BattleTransitionSnapshotStatus::available && frame.battle_transition_ready,
              "foreign stored sources must preserve current lifecycle");
      const auto &stored = *frame.actual_geography_v1->stored_advantage_sources_v1;
      Require(stored.base_advantage_raw == (scenario == 1 ? 0 : 9'900'000) &&
                  stored.resolved_advantage_raw == (scenario == 1 ? 0 : -44'556'677),
              "stored base/resolved source offsets");
      Require(stored.sides[0].available == (scenario != 2) && stored.sides[1].available &&
                  stored.sides[1].rows[0].contribution_raw == 125'000 &&
                  stored.sides[1].rows[1].contribution_raw == -987'654 &&
                  !stored.sides[1].rows[1].effect_key &&
                  !stored.sides[1].rows[1].key_unavailable_reason.empty(),
              "key absence must preserve observed retained amount and other side");
      if (scenario == 0) {
        const auto &rows = stored.sides[0].rows;
        Require(rows.size() == 3 && rows[0].effect_key == "atk_custom" &&
                    rows[0].contribution_raw == 7'654'321 &&
                    rows[1].effect_key == "holding_defender_advantage" && rows[1].contribution_raw == 0 &&
                    rows[2].effect_key == "def_custom" && rows[2].contribution_raw == -333'333,
                "ordered 16B retained rows must not use current effect points");
      } else Require(stored.sides[0].rows.empty(), "empty or unavailable source vector rows");
      frame.snapshot_revision = 2;
      const auto wire = xar::ck3_11906::SerializeBattleTransitionV1(frame);
      Require(wire.find("\"stored_advantage_sources_v1\"") != std::string::npos,
              "new stored source production serializer missing");
      const char *names[]{"retained.json", "empty-side.json", "unavailable-side.json"};
      if (*directory) WriteWire(directory, names[scenario], wire);
    }
    SelectedRollFixture fixture;
    StoredAdvantageMemory memory;
    memory.Install(fixture.battle.b, fixture.battle.combat);
    Put<std::int32_t>(fixture.battle.combat, 0x6B0, 2);
    BattleControlSnapshot frame;
    Require(ReadBattleControlSnapshot(fixture.battle.b, fixture.battle.scope, {0x1000001}, frame) ==
                BattleControlSnapshotStatus::available && frame.battle_control_ready,
            "owned stored source copy must preserve existing control readiness");
    const auto &stored = *frame.actual_geography_v1->stored_advantage_sources_v1;
    Require(stored.base_advantage_raw == frame.base_advantage_raw &&
                stored.resolved_advantage_raw == frame.resolved_advantage_raw &&
                stored.sides[0].rows.size() == 3 && frame.attacker.participant_hard_ledger.empty(),
            "owned copy and separate 24B hard-casualty ledger");
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
    frame.snapshot_revision = 2;
    const auto wire = xar::ck3_11906::SerializeBattleControlSnapshotV1(frame);
    Require(!wire.empty(), "owned stored source production serializer failed");
    if (*directory) WriteWire(directory, "owned.json", wire);
#endif
    std::cout << "Actual stored advantage source fixture GREEN: 4 frames; actual=0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "Actual stored advantage source fixture RED: " << error.what() << '\n';
    return 1;
  }
}
