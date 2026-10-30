#pragma once


namespace surrender15 {
World09 *active = nullptr;
std::array<std::byte, 0x48> government{};
std::array<std::byte, 0x28> relation{};
std::int32_t faith = 0;
int government_calls = 0, mask_calls = 0, pair_calls = 0;
void *Government(void *character) {
  m1_allocator_exec10::Require(character == active->fixture.characters[0].data(), "government actor receiver");
  ++government_calls;
  return government.data();
}
std::uint64_t Mask(const std::int32_t *identifier) {
  m1_allocator_exec10::Require(identifier && *identifier == faith, "faith identifier ABI");
  ++mask_calls;
  return 1;
}
void *Pair(void *leader, void *actor) {
  m1_allocator_exec10::Require(leader == active->fixture.characters[1].data() &&
      actor == active->fixture.characters[0].data(), "pair leader/actor ABI");
  ++pair_calls;
  return relation.data();
}
}

inline int SurrenderCase15(int argc, char **argv) {
  if (argc != 4) return 90;
  actor_id = 0x03000001U;
  recipient_id = static_cast<std::uint32_t>(std::stoull(argv[1]));
  if ((recipient_id != 0U && recipient_id != 0x80000000U)) return 91;
  const bool war_zero = std::string_view(argv[2]) == "war-zero";
  const std::filesystem::path output = argv[3];
  std::filesystem::create_directories(output);
  World09 world(source_id, false, false);
  surrender15::active = &world;
  auto &environment = world.fixture.factions;
  environment.surrender_observations_12003 = true;
  environment.government = &surrender15::Government;
  environment.government_allows_mask = &surrender15::Mask;
  environment.pair_relation = &surrender15::Pair;
  environment.state_faith_identifier = &surrender15::faith;
  Put(surrender15::relation.data(), 0x20, war_zero ? std::int32_t{0} : std::int32_t{-1});
  static constexpr std::string_view type = "populist_faction";
  Put(world.fixture.faction_type.data(), 0x18, type.data());
  Put(world.fixture.faction_type.data(), 0x28, std::uint64_t{type.size()});
  Put(world.fixture.faction_type.data(), 0x30, std::uint64_t{type.size()});
  const game::PlayerFactionAlertsFrameV1 frame{1, 53175816, true, true, true, true,
      std::bit_cast<std::int32_t>(actor_id)};
  CoreSnapshotPrefix core{};
  const bool core_ok = ck3_12004::ReadCoreSnapshot(world.fixture.b.interaction.core, core) &&
      core.played_character_id == std::bit_cast<std::int32_t>(actor_id);
  game::PlayerFactionAlertsV1 alerts{};
  const bool read_ok = Alerts09(&world, frame, alerts);
  const game::FactionSurrenderImpactV1 *impact = nullptr;
  if (read_ok && alerts.targeting_factions.size() == 1 &&
      alerts.targeting_factions[0].surrender_impact)
    impact = &*alerts.targeting_factions[0].surrender_impact;
  const bool callbacks_ok = surrender15::government_calls == 2 &&
      surrender15::mask_calls == 2 && surrender15::pair_calls == 2;
  const bool ordinary_ok = impact && impact->status == "available" &&
      impact->government_allows_state_faith == false && impact->leader_at_war_with_target == false &&
      impact->ordinary_branch_title_sets_ready && impact->county_loss_complete &&
      !impact->unavailable_reason && impact->member_counties.empty() &&
      impact->player_subrealm_county_title_ids.empty();
  const bool war_rejected = impact && impact->status == "unavailable" &&
      impact->unavailable_reason == "surrender_branch_predicates_unavailable" &&
      !impact->ordinary_branch_title_sets_ready;
  const auto wire = SerializePlayerFactionAlerts12004(alerts);
  WriteWire(output, "public-alerts.json", wire);
  RouterAdapter adapter;
  WriteWire(output, "public-alerts-whole.json", SerializePlayerFactionAlertsWhole12004(
      alerts, 1, "character-surrender15", adapter.descriptor()));
  const bool wire_ok = !wire.empty() && wire.find("\"surrender_impact\":") != std::string::npos;
  const bool pass = core_ok && read_ok && callbacks_ok && wire_ok &&
      (war_zero ? war_rejected : ordinary_ok);
  std::ofstream(output / "SUMMARY15.json")
      << "{\"machine_id\":\"xenoamess-full-tower-eb9d2c1186\",\"owned_character_fields\":true,"
      << "\"engine_callbacks_authored\":true,\"Character_allocator_executed\":false,"
      << "\"public_Handler_executed\":false,\"private_Handler_executed\":false,\"Game_operations\":0,"
      << "\"recipient_raw\":" << recipient_id << ",\"war_zero\":" << war_zero
      << ",\"Core\":" << core_ok << ",\"reader\":" << read_ok
      << ",\"government_calls\":" << surrender15::government_calls
      << ",\"mask_calls\":" << surrender15::mask_calls
      << ",\"pair_calls\":" << surrender15::pair_calls
      << ",\"ordinary_ready\":" << ordinary_ok << ",\"war_zero_rejected\":" << war_rejected
      << ",\"wire\":" << wire_ok << ",\"pass\":" << pass << "}\n";
  std::cout << "reader=" << read_ok << " callbacks=" << callbacks_ok
      << " ordinary=" << ordinary_ok << " war_rejected=" << war_rejected
      << " wire=" << wire_ok << '\n';
  return pass ? 0 : 1;
}
