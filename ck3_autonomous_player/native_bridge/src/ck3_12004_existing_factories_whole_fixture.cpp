#include "xar_bridge/ck3_12003_commander.hpp"
#include "xar_bridge/ck3_12003_commander_assignment.hpp"
#include "xar_bridge/ck3_12003_commander_assignment_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"
#include "xar_bridge/ck3_12004_commander_assignment.hpp"
#include "xar_bridge/ck3_12004_commander_mailbox.hpp"
#include "xar_bridge/ck3_12004_combat.hpp"
#include "xar_bridge/ck3_12004_military.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace xar::ck3_12003;
constexpr std::int32_t kPlayer = 29829;
constexpr std::int32_t kUnit = 83886367;
constexpr std::int32_t kArmy = 50331794;
constexpr std::int32_t kCandidate = 34333;
constexpr std::int32_t kOther = 34334;
constexpr std::int32_t kUnlisted = 34335;
constexpr std::uintptr_t kSecondaryVtable = 0x1200401;
int checks = 0;

template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
void Check(bool value, const char *label) {
  ++checks;
  if (!value) throw std::runtime_error(label);
}

struct Fixture {
  std::array<std::byte, 0x180> unit{}, army{};
  std::array<std::array<std::byte, 0x210>, 4> characters{};
  std::array<std::byte, 0x30> units{}, armies{}, character_store{};
  std::vector<std::byte> unit_slots = std::vector<std::byte>(288 * 0x10);
  std::vector<std::byte> army_slots = std::vector<std::byte>(147 * 0x10);
  std::vector<std::byte> character_slots = std::vector<std::byte>(34336 * 0x10);
  std::array<std::byte, 0x18> allocator_vtable{};
  std::array<std::byte, 0x08> allocator{};
  void *unit_storage = units.data();
  void *army_storage = armies.data();
  void *character_storage = character_store.data();
  void **allocated = nullptr;
  bool candidate_eligible = true;
  int collect_calls = 0, release_calls = 0, can_calls = 0;
  int factory_calls = 0, validator_calls = 0, clone_calls = 0;
  int queue_calls = 0, delete_calls = 0;
  bool source_valid = true, queue_accepted = true;
  std::array<std::uintptr_t, 9> command_vtable{};
  std::string callback_error;
  CommanderBindings reader{};
  xar::game::Snapshot scope{};
};
Fixture *active = nullptr;
using FixtureCommand = std::array<std::byte, 0x30>;

void RequireCallback(bool value, const char *label) {
  if (!value && active->callback_error.empty()) active->callback_error = label;
}
void Release(void *allocator, void *data, std::uint64_t alignment) {
  RequireCallback(allocator == active->allocator.data() && data == active->allocated &&
                      alignment == 8,
                  "native candidate collection uses its actual allocator");
  delete[] static_cast<void **>(data);
  active->allocated = nullptr;
  ++active->release_calls;
}
void Collect(void *owner, CommanderPointerVector *output, bool filter_now, bool allow_guests) {
  RequireCallback(owner == active->characters[0].data() && !filter_now && allow_guests,
                  "assignment candidate source is current owner's native collection");
  RequireCallback(output->allocator == active->allocator.data() && output->data == nullptr &&
                      output->count == 0 && output->capacity == 0 && active->allocated == nullptr,
                  "assignment observes a fresh candidate vector");
  active->allocated = new void *[2];
  active->allocated[0] = active->characters[1].data();
  active->allocated[1] = active->characters[2].data();
  output->data = active->allocated;
  output->count = output->capacity = 2;
  ++active->collect_calls;
}
bool CanAssign(std::int32_t mode, void *candidate, void *army, void *reason) {
  RequireCallback(mode == 1 && army == active->army.data() && reason == nullptr,
                  "manual final eligibility uses mode 1 and native CArmy");
  RequireCallback(candidate == active->characters[1].data() ||
                      candidate == active->characters[2].data(),
                  "unlisted candidate cannot reach native eligibility");
  ++active->can_calls;
  return candidate == active->characters[1].data() && active->candidate_eligible;
}
std::int32_t BaseQuality(void *candidate) {
  return candidate == active->characters[1].data() ? 125 : 90;
}
std::int32_t GenericAdvantage(void *, std::int32_t context, bool flag) {
  RequireCallback(context == -1 && !flag, "existing commander reader exact generic context");
  return 0;
}
void *CurrentCommander(void *army) {
  RequireCallback(army == active->army.data(), "independent commander getter uses native CArmy");
  return Get<std::int32_t>(army, 0x120) == kCandidate ? active->characters[1].data() : nullptr;
}
void *Delete(void *owned, std::uint32_t flags) {
  RequireCallback(flags == 1, "native scalar deleting destructor receives owning flag");
  ++active->delete_calls;
  delete static_cast<FixtureCommand *>(owned);
  return nullptr;
}
void **Clone(const void *source, void **result_storage) {
  RequireCallback(source != nullptr && result_storage != nullptr && *result_storage == nullptr,
                  "clone receives caller-owned source and fresh hidden result storage");
  ++active->clone_calls;
  auto *owned = new FixtureCommand;
  std::memcpy(owned->data(), source, owned->size());
  *result_storage = owned;
  return result_storage;
}
void *CreateDefault() {
  ++active->factory_calls;
  auto *source = new FixtureCommand{};
  Put(source->data(), 0, active->command_vtable.data());
  Put(source->data(), 0x08, std::uint8_t{0x20});
  Put(source->data(), 0x18, kSecondaryVtable);
  Put(source->data(), 0x20, std::int32_t{-1});
  Put(source->data(), 0x24, std::int32_t{-1});
  Put(source->data(), 0x28, std::int32_t{-1});
  return source;
}
bool ValidateSource(const void *source, void *reason) {
  RequireCallback(source != nullptr && reason == nullptr,
                  "actual native command validator receives null reason buffer");
  RequireCallback(Get<std::int32_t>(source, 0x20) == 1 &&
                      Get<std::int32_t>(source, 0x24) == kCandidate &&
                      Get<std::int32_t>(source, 0x28) == kArmy,
                  "validator receives actual primary command with mode, character and internal CArmy IDs");
  RequireCallback(Get<const void *>(source, 0) == active->command_vtable.data() &&
                      Get<std::uintptr_t>(source, 0x18) == kSecondaryVtable &&
                      Get<std::uint8_t>(source, 0x08) == 0x20,
                  "native constructor's two interfaces and metadata remain intact");
  ++active->validator_calls;
  return active->source_valid;
}
bool Queue(void *manager, void **owned, std::uint32_t channel) {
  RequireCallback(manager == &active->queue_calls && owned != nullptr && *owned != nullptr &&
                      channel == kCommanderAssignmentChannelFlags,
                  "owned command submitted to selected native manager on exact channel 0x0E");
  ++active->queue_calls;
  RequireCallback(Get<std::int32_t>(*owned, 0x20) == 1 &&
                      Get<std::int32_t>(*owned, 0x24) == kCandidate &&
                      Get<std::int32_t>(*owned, 0x28) == kArmy &&
                      Get<std::int32_t>(*owned, 0x28) != kUnit,
                  "owned clone preserves internal CArmy ID rather than public CUnit ID");
  RequireCallback(Get<std::uintptr_t>(*owned, 0x18) == kSecondaryVtable &&
                      Get<std::uint8_t>(*owned, 0x08) == 0x20,
                  "owned queue receives constructor metadata intact");
  // Consume the owned clone while leaving the independent Army unchanged.
  if (!active->queue_accepted) return false;
  Delete(*owned, 1);
  *owned = nullptr;
  return true;
}
void *NoModifier(void *) { return nullptr; }
std::int64_t *ZeroModifier(void *, std::int64_t *out, std::int32_t) {
  *out = 0; return out;
}
std::int64_t *ZeroMovement(void *unit, std::int64_t *out) {
  RequireCallback(unit == active->unit.data(), "typed CUnit movement receiver");
  *out = 0; return out;
}
std::int32_t ZeroSkill(void *, std::int32_t) { return 0; }

void Initialize(Fixture &fixture) {
  active = &fixture;
  Put(fixture.unit.data(), 0x10, kUnit);
  Put(fixture.unit.data(), 0x174, kPlayer);
  Put(fixture.unit.data(), 0x178, kArmy);
  Put(fixture.army.data(), 0x10, kArmy);
  Put(fixture.army.data(), 0x14, std::uint32_t{0x41726D79});
  Put(fixture.army.data(), 0x120, std::int32_t{-1});
  Put(fixture.army.data(), 0x124, kUnit);
  Put(fixture.unit_slots.data(), 287 * 0x10 + 8, fixture.unit.data());
  Put(fixture.army_slots.data(), 146 * 0x10 + 8, fixture.army.data());
  Put(fixture.units.data(), 0x20, fixture.unit_slots.data());
  Put(fixture.units.data(), 0x2C, std::int32_t{288});
  Put(fixture.armies.data(), 0x20, fixture.army_slots.data());
  Put(fixture.armies.data(), 0x2C, std::int32_t{147});
  const std::array<std::int32_t, 4> ids{kPlayer, kCandidate, kOther, kUnlisted};
  for (std::size_t index = 0; index < ids.size(); ++index) {
    Put(fixture.characters[index].data(), 0x18, ids[index]);
    Put(fixture.characters[index].data(), 0x1C, std::uint32_t{0x43686172});
    Put(fixture.character_slots.data(), static_cast<std::size_t>(ids[index]) * 0x10 + 8,
        fixture.characters[index].data());
  }
  Put(fixture.character_store.data(), 0x20, fixture.character_slots.data());
  Put(fixture.character_store.data(), 0x2C, std::int32_t{34336});
  Put(fixture.allocator_vtable.data(), 0x10, &Release);
  Put(fixture.allocator.data(), 0, fixture.allocator_vtable.data());
  fixture.reader = xar::ck3_12004::BindCommanderImage12004(
      0x140000000, xar::ck3_12004::kExecutableSha256);
  fixture.reader.armies.unit_storage_slot = &fixture.unit_storage;
  fixture.reader.armies.internal_army_storage_slot = &fixture.army_storage;
  fixture.reader.character_storage_slot = &fixture.character_storage;
  fixture.reader.vector_allocator = fixture.allocator.data();
  fixture.reader.collect_candidates = Collect;
  fixture.reader.can_set_commander = CanAssign;
  fixture.reader.get_native_ai_base_quality = BaseQuality;
  fixture.reader.get_generic_advantage = GenericAdvantage;
  fixture.reader.get_army_commander = CurrentCommander;
  fixture.reader.get_character_modifier_aggregator = NoModifier;
  fixture.reader.read_character_modifier = ZeroModifier;
  fixture.reader.read_unit_land_movement_rate = ZeroMovement;
  fixture.reader.read_unit_naval_movement_rate = ZeroMovement;
  fixture.reader.read_unit_current_edge_movement_rate = ZeroMovement;
  fixture.reader.get_current_total_skill = ZeroSkill;
  fixture.scope.paused = fixture.scope.map_ready = fixture.scope.has_played_character =
      fixture.scope.played_character_alive = true;
  fixture.scope.played_character_id = kPlayer;
  fixture.scope.date_raw = 10000;
  xar::game::ArmySnapshot row{};
  row.army_id = kUnit;
  row.owner_character_id = kPlayer;
  row.controllable = true;
  row.route_read_status = xar::game::ArmyRouteReadStatus::complete_empty;
  row.route_source_count = 0;
  row.army_state = "regular";
  fixture.scope.player_armies.push_back(row);
  fixture.command_vtable[0] = reinterpret_cast<std::uintptr_t>(&Delete);
  fixture.command_vtable[8] = reinterpret_cast<std::uintptr_t>(&Clone);
}

std::string Frame(std::string_view request_id, const std::string &body) {
  return std::string("{\"type\":\"command_result\",\"protocol_version\":1,") +
      "\"request_id\":\"" + std::string(request_id) +
      "\",\"ok\":true,\"result\":" + body + "}";
}

void Write(const std::filesystem::path &path, const std::string &body) {
  std::ofstream file(path, std::ios::binary);
  file << body << '\n';
  Check(bool(file), "complete production command-result written");
}

// Admission checks for the restored default factories are added below. They
// inspect returned addresses without calling an actual game-image address.
void QualifyRestoredFactories();

} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--emit-wire",
          "--emit-wire fresh-output-directory required");
    const std::filesystem::path output(argv[2]);
    std::filesystem::create_directories(output);
    constexpr std::uintptr_t image = 0x140000000;
    const auto commanders = xar::ck3_12004::BindCommanderImage12004(
        image, xar::ck3_12004::kExecutableSha256);
    const auto commands = xar::ck3_12004::BindCommandImage12004(
        image, xar::ck3_12004::kExecutableSha256);
    const auto selected = xar::ck3_12004::BindCommanderAssignmentImage12004(
        image, xar::ck3_12004::kExecutableSha256, commanders, commands);
    Check(selected.enabled &&
        reinterpret_cast<std::uintptr_t>(selected.create_default) ==
            image + xar::ck3_12004::kCommanderAssignmentDefaultFactoryRva12004 &&
        reinterpret_cast<std::uintptr_t>(selected.validate_source) ==
            image + xar::ck3_12004::kCommanderAssignmentValidatorRva12004,
        "actual .4 constructor and vtable-resolved validator selected");
    QualifyRestoredFactories();

    Fixture fixture{};
    Initialize(fixture);
    auto bindings = selected;
    bindings.commanders = fixture.reader;
    bindings.commands.command_manager = &fixture.queue_calls;
    bindings.commands.queue_owned_command = Queue;
    bindings.create_default = CreateDefault;
    bindings.validate_source = ValidateSource;
    const std::string query_step =
        "query-army-commander-candidates-v1-for-army-" + std::to_string(kUnit);
    const std::string assignment_step =
        "assign-army-commander-v1-army-" + std::to_string(kUnit) +
        "-to-character-" + std::to_string(kCandidate);
    ArmyCommanderCandidatesSnapshot before{}, after{};
    const auto before_status = ReadArmyCommanderCandidates(
        bindings.commanders, fixture.scope, kUnit, before);
    CommanderAssignmentResult assignment{};
    const auto status = ApplyArmyCommanderAssignment(
        bindings, fixture.scope, kUnit, kCandidate, assignment);
    const auto after_status = ReadArmyCommanderCandidates(
        bindings.commanders, fixture.scope, kUnit, after);
    Check(before_status == CommanderCandidatesReadResult::available &&
              after_status == CommanderCandidatesReadResult::available &&
              before.current_commander_status == "absent" &&
              after.current_commander_status == "absent" &&
              status == CommanderAssignmentStatus::submitted &&
              assignment.command_submitted && assignment.verification_pending,
          "whole native readback remains pending after queue ACK");
    Check(fixture.factory_calls == 1 && fixture.validator_calls == 1 &&
              fixture.clone_calls == 1 && fixture.queue_calls == 1 &&
              fixture.delete_calls == 2 && fixture.collect_calls == 3 &&
              fixture.release_calls == 3 && fixture.can_calls == 6 &&
              fixture.allocated == nullptr && fixture.callback_error.empty() &&
              Get<std::int32_t>(fixture.army.data(), 0x120) == -1,
          "three whole reads share exact callbacks and preserve independent state");
    const auto before_frame = Frame("existing-factory-before",
        xar::ck3_12004::SerializeArmyCommanderCandidates12004(
            before, before_status, 1, 7, 10000, query_step));
    const auto assignment_frame = Frame("existing-factory-assignment",
        SerializeArmyCommanderAssignment(
            assignment, status, 1, 7, 10000, assignment_step));
    const auto after_frame = Frame("existing-factory-after",
        xar::ck3_12004::SerializeArmyCommanderCandidates12004(
            after, after_status, 2, 7, 10000, query_step));
    Write(output / "before.command-result.json", before_frame);
    Write(output / "assignment.command-result.json", assignment_frame);
    Write(output / "after.command-result.json", after_frame);
    Write(output / "existing-factories-12004-whole.json",
        "{\"schema_version\":1,\"scene_order\":[\"before\",\"assignment\",\"after\"],"
        "\"samples\":{\"before\":" + before_frame +
        ",\"assignment\":" + assignment_frame + ",\"after\":" + after_frame + "}}");
    Write(output / "producer-provenance.json",
        "{\"schema_version\":1,\"native_version\":\"1.20.0.4\","
        "\"executable_sha256\":\"" + std::string(xar::ck3_12004::kExecutableSha256) +
        "\",\"callbacks\":\"fixture-owned ABI implementations after actual factory admission\","
        "\"producer\":\"ReadArmyCommanderCandidates/ApplyArmyCommanderAssignment/production serializers\","
        "\"game_started\":false,\"observed_application\":false}");
    std::cout << "GREEN whole_frames=3 queue_submissions=1 checks=" << checks << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}

namespace {
bool QualifyMilitaryMaaFactories12004() {
  constexpr std::uintptr_t base = 0x140000000;
  constexpr std::string_view sha = xar::ck3_12004::kExecutableSha256;
  const auto commands = xar::ck3_12004::BindCommandImage12004(base, sha);
  const auto military = xar::ck3_12004::BindMilitaryImage12004(base, sha, commands);
  const auto recruitment =
      xar::ck3_12004::BindNativeMaaRecruitmentImage12004(base, sha);
  const auto create = xar::ck3_12004::BindNativeMaaCreateImage12004(base, sha);
  const auto address = [](auto pointer) {
    return reinterpret_cast<std::uintptr_t>(pointer);
  };
  if (!commands.enabled || !military.enabled || !recruitment.enabled ||
      !create.enabled || military.submit_context != &commands ||
      military.submit_copy != &xar::ck3_12002::SubmitCommandCopyCompat ||
      military.raise_primary != base + 0x45345D0 ||
      military.raise_secondary != base + 0x4534668 ||
      military.move_primary != base + 0x476B178 ||
      military.halt_primary != base + 0x476B080 ||
      military.merge_primary != base + 0x476AB30 ||
      address(military.construct_raise) != base + 0x298C110 ||
      address(military.validate_raise) != base + 0x298C2A0 ||
      address(military.build_route) != base + 0x2648130 ||
      address(military.read_move_progress) != base + 0x24AB2D0 ||
      address(military.append_int_range) != base + 0x9E3790 ||
      address(military.validate_start) != base + 0x29738A0 ||
      address(military.validate_stop) != base + 0x2973A50 ||
      address(recruitment.type_registry_slot) != base + 0x5C67558 ||
      address(recruitment.regular_personal_can_create) != base + 0x296F9D0 ||
      address(recruitment.regular_final_raw_quote) != base + 0x30BCE00 ||
      address(create.current_player_full_id_slot) != base + 0x54DBC00 ||
      address(create.type_lookup) != base + 0x1AD5520 ||
      address(create.regular_personal_constructor) != base + 0x1338F70 ||
      address(create.regular_personal_can_create) != base + 0x296F9D0 ||
      create.command_manager != commands.command_manager ||
      address(create.submit) != address(commands.queue_owned_command)) {
    return false;
  }
  constexpr std::string_view old_sha =
      "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
  return !xar::ck3_12004::BindMilitaryImage12004(base, old_sha, commands).enabled &&
      !xar::ck3_12004::BindNativeMaaRecruitmentImage12004(base, old_sha).enabled &&
      !xar::ck3_12004::BindNativeMaaCreateImage12004(base, old_sha).enabled &&
      !xar::ck3_12004::BindMilitaryImage12004(base, sha, {}).enabled;
}

void QualifyRestoredFactories() {
  Check(QualifyMilitaryMaaFactories12004(),
        "actual4 default Military and personal MAA factories preserve their ABI");
  constexpr std::uintptr_t base = 0x140000000;
  const auto combat = xar::ck3_12004::BindCombatImage12004(
      base, xar::ck3_12004::kExecutableSha256);
  Check(combat.enabled && combat.ordinary_stat_inputs_enabled &&
            combat.maa_stat_inputs_enabled && combat.knight_model_association_enabled &&
            combat.phase_rite_parameters.enabled && combat.phase_warmonger_core.enabled &&
            combat.phase_berserker_validity_inputs.enabled &&
            combat.phase_berserker_chance_inputs.enabled &&
            reinterpret_cast<std::uintptr_t>(combat.maa_get_piety_rank) ==
                base + 0x28BE0B0 &&
            reinterpret_cast<std::uintptr_t>(combat.evaluate_regiment_stats_at_province) ==
                base + 0x26344A0 &&
            reinterpret_cast<std::uintptr_t>(combat.read_counter_current_chunk) ==
                base + 0x2657950 &&
            reinterpret_cast<std::uintptr_t>(combat.commander_min_roll) ==
                base + 0x5C699BC &&
            reinterpret_cast<std::uintptr_t>(combat.commander_max_roll) ==
                base + 0x5C699B8,
        "actual4 GeneralCombat preserves all adopted default stat/phase fields");
}

} // namespace
