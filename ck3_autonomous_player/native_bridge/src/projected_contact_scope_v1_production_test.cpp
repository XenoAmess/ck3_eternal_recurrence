// Focused production-reader fixture. The runner imports only the established
// native memory layout helpers, excluding the previous matrix's main.
#include "projected_contact_memory_fixture.hpp"

#include "xar_bridge/projected_contact_scope_v1_serializer.hpp"

#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <tuple>

namespace {
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

struct ProjectedFixture : Fixture {
  static constexpr std::int32_t friend1_id = 0x1000004;
  static constexpr std::int32_t friend2_id = 0x1000005;
  std::array<Unit, 2> friend_unit{};
  std::array<Army, 2> friend_army{};
  std::array<std::int32_t, 4> target_units{enemy_id, enemy2_id,
                                            friend1_id, friend2_id};
  std::array<std::byte, 0x30> battle_result{};

  ProjectedFixture() {
    // Actual incoming is at province 2. Actual target contains no incoming ID.
    Put(province[1], 0x740, target_units.data());
    Put(province[1], 0x74C, std::int32_t{2});
    // Native contact constructor reads target -> supplied entry. Deliberately
    // distinguish the route/v2 direction entry -> target in this fixture.
    Put(adjacency[1], 0, std::int32_t{2});
    Put(adjacency[0], 0, std::int32_t{1});
  }

  void FriendsInSelectedCombat(std::int32_t combat_id) {
    for (std::size_t i = 0; i < friend_unit.size(); ++i) {
      const auto id = friend1_id + static_cast<std::int32_t>(i);
      units.Add(id, friend_unit[i], 0x10);
      armies.Add(id, friend_army[i], 0x10);
      Put(friend_unit[i], 0x20, province[1].data());
      Put(friend_unit[i], 0x174, subject_id);
      Put(friend_unit[i], 0x178, id);
      Put(friend_army[i], 0x124, id);
      Put(friend_army[i], 0x128, combat_id);
    }
    Put(province[1], 0x74C, std::int32_t{4});
  }

  auto RealMemory() const {
    return std::tuple{state, jomini, data, units.object, units.slots,
                      armies.object, armies.slots, unit, army, province,
                      node, info, adjacency, province_units, province_combats,
                      combat, attacker_ids, defender_ids, friend_unit,
                      friend_army, target_units, battle_result};
  }

  game::ProjectedContactScopeSnapshot Query(
      const game::ProjectedContactScopeRequest &request,
      game::ProjectedContactScopeStatus expected) {
    const auto before = RealMemory();
    game::ProjectedContactScopeSnapshot result{};
    const auto status = ck3_12002::ReadProjectedContactScope(
        binding, scope, request, result);
    Require(status == expected && result.status == expected,
            "projected native status differs from expected");
    Require(RealMemory() == before,
            "projected query mutated actual unit/province/combat fixture memory");
    // The production bridge binds this transport revision after the reader.
    result.snapshot_revision = 41;
    return result;
  }
};

void Save(const std::filesystem::path &directory, const char *name,
          const game::ProjectedContactScopeSnapshot &scope) {
  std::ofstream output(directory / (std::string{name} + ".json"),
                       std::ios::binary);
  Require(output.good(), "cannot open native wire output");
  output << game::SerializeProjectedContactScopeV1Snapshot(scope) << '\n';
  Require(output.good(), "cannot write native wire output");
  std::cout << name << " GREEN\n";
}
} // namespace

int main(int argc, char **argv) {
  using game::ProjectedContactScopeRequest;
  using game::ProjectedContactScopeStatus;
  try {
    Require(argc == 2 || argc == 3, "pass native wire output directory and optional case name");
    const std::filesystem::path directory{argv[1]};
    std::filesystem::create_directories(directory);
    const ProjectedContactScopeRequest remote{Fixture::subject_id, 3, 2};
    const auto Want = [argc, argv](const char *name) {
      return argc == 2 || std::string_view{argv[2]} == name;
    };

    if (Want("remote-create-new")) {
      ProjectedFixture f;
      auto result = f.Query(remote, ProjectedContactScopeStatus::available);
      Require(result.transition_kind == "create_new" &&
                  result.projected_subject_side == "attacker" &&
                  result.projected_initiator_is_defender_observable &&
                  !result.projected_initiator_is_defender &&
                  result.subject_current_province_id == 2 &&
                  result.incoming_adjacency_kind_raw == 2 &&
                  result.observed_target_public_cunit_ids ==
                      std::vector<std::int32_t>{Fixture::enemy_id,
                                                Fixture::enemy2_id} &&
                  result.projected_attacker_army_ids ==
                      std::vector<std::int32_t>{Fixture::subject_id} &&
                  result.projected_defender_army_ids ==
                      std::vector<std::int32_t>{Fixture::enemy_id,
                                                Fixture::enemy2_id} &&
                  result.contact_projection_inputs_complete,
              "remote create-new projection or incoming edge mismatch");
      const auto before = f.RealMemory();
      game::ActualContactScopeSnapshot actual{};
      Require(ck3_12002::ReadActualContactScope(
                  f.binding, f.scope, {Fixture::subject_id, 3}, actual) ==
                  game::ActualContactScopeStatus::subject_not_at_target,
              "actual contact query lost real-arrival semantics");
      Require(f.RealMemory() == before, "actual query mutated fixture memory");
      Save(directory, "remote-create-new", result);
    }
    if (Want("remote-holder-defender")) {
      ProjectedFixture f;
      Put(f.province[1], 0x850, std::int32_t{1});
      g_fort_defender = true;
      auto result = f.Query(remote, ProjectedContactScopeStatus::available);
      Require(result.transition_kind == "create_new" &&
                  result.projected_subject_side == "defender" &&
                  result.projected_initiator_is_defender_observable &&
                  result.projected_initiator_is_defender &&
                  result.projected_attacker_army_ids ==
                      std::vector<std::int32_t>{Fixture::enemy_id,
                                                Fixture::enemy2_id} &&
                  result.projected_defender_army_ids ==
                      std::vector<std::int32_t>{Fixture::subject_id} &&
                  result.incoming_adjacency_kind_raw == 2,
              "holder-defender role or incoming edge attribution mismatch");
      Save(directory, "remote-holder-defender", result);
    }
    if (Want("compatible-join-stored-order")) {
      ProjectedFixture f;
      f.AddCombat(0, Fixture::enemy_id);
      f.AddCombat(1, Fixture::enemy2_id);
      const auto selected = Fixture::enemy_id;
      f.FriendsInSelectedCombat(selected);
      f.attacker_ids[1] = {ProjectedFixture::friend2_id,
                           ProjectedFixture::friend1_id};
      f.defender_ids[1] = {Fixture::enemy2_id, Fixture::enemy_id};
      Put(f.combat[1], 0x3C, std::int32_t{2});
      Put(f.combat[1], 0x384, std::int32_t{2});
      Put(f.army[1], 0x128, selected);
      Put(f.army[2], 0x128, selected);
      Put(f.province[1], 0x764, std::int32_t{2});
      auto result = f.Query(remote, ProjectedContactScopeStatus::available);
      Require(result.transition_kind == "join_existing" &&
                  result.selected_current_combat_id == selected &&
                  result.selected_current_combat_array_index == 1 &&
                  result.projected_subject_side == "attacker" &&
                  !result.projected_initiator_is_defender_observable &&
                  result.projected_attacker_army_ids ==
                      std::vector<std::int32_t>{ProjectedFixture::friend2_id,
                                                ProjectedFixture::friend1_id,
                                                Fixture::subject_id} &&
                  result.projected_defender_army_ids ==
                      std::vector<std::int32_t>{Fixture::enemy2_id,
                                                Fixture::enemy_id},
              "last compatible combat or stored-side append order mismatch");
      Save(directory, "compatible-join-stored-order", result);
    }
    if (Want("both-hostile-xor-none")) {
      ProjectedFixture f;
      f.AddCombat(0, Fixture::enemy2_id);
      Put(f.combat[0], 0x90, Fixture::enemy_id);
      f.attacker_ids[0][0] = Fixture::enemy_id;
      f.defender_ids[0][0] = Fixture::enemy2_id;
      Put(f.army[1], 0x128, Fixture::subject_id);
      Put(f.army[2], 0x128, Fixture::subject_id);
      Put(f.province[1], 0x764, std::int32_t{1});
      auto result = f.Query(remote, ProjectedContactScopeStatus::available);
      Require(result.transition_kind == "none" &&
                  result.projected_subject_side == "none" &&
                  result.projected_attacker_army_ids.empty() &&
                  result.projected_defender_army_ids.empty() &&
                  result.selected_current_combat_id == -1 &&
                  !result.projected_initiator_is_defender_observable &&
                  result.contact_projection_inputs_complete,
              "both-hostile XOR must yield legitimate complete none");
      Save(directory, "both-hostile-xor-none", result);
    }
    if (Want("retreating-opponent-excluded")) {
      ProjectedFixture f;
      Put(f.unit[1], 0x170, std::int32_t{1});
      auto result = f.Query(remote, ProjectedContactScopeStatus::available);
      Require(result.transition_kind == "create_new" &&
                  result.projected_defender_army_ids ==
                      std::vector<std::int32_t>{Fixture::enemy2_id},
              "retreating opponent must be excluded by native predicate");
      Save(directory, "retreating-opponent-excluded", result);
    }
    if (Want("finalized-losers-excluded-none")) {
      ProjectedFixture f;
      f.AddCombat(0, Fixture::enemy_id);
      Put(f.combat[0], 0x704, std::uint8_t{1});
      Put(f.combat[0], 0x708, Fixture::subject_id);
      Put(f.combat[0], 0x6E0, std::int32_t{0});
      f.defender_ids[0] = {Fixture::enemy_id, Fixture::enemy2_id};
      Put(f.combat[0], 0x384, std::int32_t{2});
      f.results.Add(Fixture::subject_id, f.battle_result, 8);
      Put(f.battle_result, 0x0C, std::uint32_t{0x43625273});
      Put(f.battle_result, 0x28, std::uint8_t{1});
      Put(f.province[1], 0x764, std::int32_t{1});
      auto result = f.Query(remote, ProjectedContactScopeStatus::available);
      Require(result.transition_kind == "none" &&
                  result.projected_attacker_army_ids.empty() &&
                  result.projected_defender_army_ids.empty() &&
                  result.contact_projection_inputs_complete,
              "finalized losers must be excluded from new contact seed");
      Save(directory, "finalized-losers-excluded-none", result);
    }
    if (Want("public-cunit-zero")) {
      ProjectedFixture f;
      f.units.Add(0, f.unit[0], 0x10);
      Put(f.army[0], 0x124, std::int32_t{0});
      f.scope.player_armies[0].army_id = 0;
      const ProjectedContactScopeRequest zero{0, 3, 2};
      auto result = f.Query(zero, ProjectedContactScopeStatus::available);
      Require(result.subject_army_id == 0 &&
                  result.subject_native_carmy_id == Fixture::subject_id &&
                  result.projected_attacker_army_ids ==
                      std::vector<std::int32_t>{0},
              "public CUnitID zero was rejected or confused with native CArmyID");
      game::ProjectedContactScopeRequest parsed{};
      Require(game::ParseProjectedContactScopeV1Step(
                  "query-projected-contact-scope-v1-0-to-3-from-2", parsed) &&
                  parsed == zero,
              "production query parser rejected public CUnitID zero");
      Save(directory, "public-cunit-zero", result);
    }
    if (Want("full-generation-mismatch")) {
      ProjectedFixture f;
      Put(f.unit[0], 0x10, std::int32_t{0x2000001});
      auto result = f.Query(remote,
                           ProjectedContactScopeStatus::subject_army_not_found);
      Require(!result.contact_projection_inputs_complete,
              "full-generation identity mismatch became available");
      Save(directory, "full-generation-mismatch", result);
    }
    if (Want("invalid-entry-edge")) {
      ProjectedFixture f;
      Put(f.node[1], 0x5C, std::int32_t{0});
      auto result = f.Query(remote,
                           ProjectedContactScopeStatus::invalid_entry_target_adjacency);
      Require(!result.contact_projection_inputs_complete,
              "missing native entry edge became a complete projection");
      Save(directory, "invalid-entry-edge", result);
    }
    if (Want("unavailable-native-bindings")) {
      ProjectedFixture f;
      f.binding.is_character_hostile = nullptr;
      auto result = f.Query(remote, ProjectedContactScopeStatus::unavailable);
      Require(!result.contact_projection_inputs_complete,
              "unreadable relation bindings became valid none");
      Save(directory, "unavailable-native-bindings", result);
    }
    std::cout << "focused production projected contact; old matrix invocations 0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "projected contact fixture RED: " << error.what() << '\n';
    return 1;
  }
}
