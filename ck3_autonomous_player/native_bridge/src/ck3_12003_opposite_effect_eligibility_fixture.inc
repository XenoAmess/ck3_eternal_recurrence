// Only new eligibility frames: current flag bytes with retained row+8 amounts.
struct OppositeEffectEligibilityMemory {
  StoredAdvantageMemory stored;
  Bytes<0x90> key_unavailable_effect{};
  template <std::size_t N>
  void Install(BattleBindings &bindings, Bytes<N> &combat) {
    stored.Install(bindings, combat);
    Put<std::uint8_t>(stored.effects.effects[0], 0x88, 0);
    Put<std::uint8_t>(stored.effects.effects[0], 0x89, 0);
    Put<std::uint8_t>(stored.effects.effects[1], 0x88, 2);
    Put<std::uint8_t>(stored.effects.effects[1], 0x89, 0);
    Put<std::uint8_t>(stored.effects.effects[2], 0x88, 0);
    Put<std::uint8_t>(stored.effects.effects[2], 0x89, 255);
    Put<std::uint32_t>(key_unavailable_effect, 0x38, 0x4744624F);
    Put<std::size_t>(key_unavailable_effect, 0x30, 15);
    Put<std::uint8_t>(key_unavailable_effect, 0x88, 0);
    Put<std::uint8_t>(key_unavailable_effect, 0x89, 3);
    Put(stored.defender, 0x10, key_unavailable_effect.data());
  }
};

int RunOppositeEffectEligibilityFixtures(const char *directory) {
  try {
    for (int scenario = 0; scenario < 3; ++scenario) {
      ActualGeographyFixture fixture;
      OppositeEffectEligibilityMemory memory;
      memory.Install(fixture.b, fixture.combat);
      if (scenario == 1) Fixture::Array(fixture.combat, 0x98, nullptr, 0);
      else if (scenario == 2) Put<void *>(memory.stored.defender, 0x10, nullptr);
      BattleTransitionSnapshot frame;
      Require(ReadBattleTransitionSnapshot(fixture.b, fixture.scope, {kActualCombat}, frame) ==
                  BattleTransitionSnapshotStatus::available && frame.battle_transition_ready,
              "new flag source preserves current foreign lifecycle");
      const auto &stored = *frame.actual_geography_v1->stored_advantage_sources_v1;
      const auto &row = stored.sides[1].rows[1];
      Require(!row.effect_key && row.contribution_raw == -987'654 && row.effect_flags_v1 &&
                  row.effect_flags_v1->flag89_raw ==
                      (scenario == 2 ? std::optional<std::uint8_t>{} : std::optional<std::uint8_t>{3}),
              "key absence must preserve independent observed flags and retained amount");
      if (scenario == 1) Require(stored.sides[0].rows.empty(), "available empty ledger");
      else Require(stored.sides[0].rows[0].effect_flags_v1->flag88_raw == 0 &&
                       stored.sides[0].rows[1].effect_flags_v1->flag89_raw == 255 &&
                       stored.sides[0].rows[2].effect_flags_v1->flag88_raw == 2,
                   "raw uint8 values preserve both eligibility sources and native row order");
      frame.snapshot_revision = 2;
      const auto wire = xar::ck3_11906::SerializeBattleTransitionV1(frame);
      Require(wire.find("\"effect_flags_v1\"") != std::string::npos, "production stored flag wire");
      const char *names[]{"observed-eligibility.json", "empty-opposite.json", "missing-flags.json"};
      if (*directory) WriteWire(directory, names[scenario], wire);
    }
    SelectedRollFixture fixture;
    OppositeEffectEligibilityMemory memory;
    memory.Install(fixture.battle.b, fixture.battle.combat);
    Put<std::int32_t>(fixture.battle.combat, 0x6B0, 2);
    BattleControlSnapshot frame;
    Require(ReadBattleControlSnapshot(fixture.battle.b, fixture.battle.scope, {0x1000001}, frame) ==
                BattleControlSnapshotStatus::available && frame.battle_control_ready,
            "owned current eligibility copy preserves ownership gate");
    const auto &row = frame.actual_geography_v1->stored_advantage_sources_v1->sides[1].rows[1];
    Require(row.effect_flags_v1->flag89_raw == 3 && row.contribution_raw == -987'654,
            "owned flag and retained amount copy");
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
    frame.snapshot_revision = 2;
    const auto wire = xar::ck3_11906::SerializeBattleControlSnapshotV1(frame);
    Require(!wire.empty(), "owned flag production serializer");
    if (*directory) WriteWire(directory, "owned.json", wire);
#endif
    std::cout << "Actual opposite effect eligibility fixture GREEN: 4 new frames; actual=0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "Actual opposite effect eligibility fixture RED: " << error.what() << '\n';
    return 1;
  }
}
