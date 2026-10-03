#include "xar_bridge/ck3_12003_commander.hpp"
#include "xar_bridge/ck3_12003_commander_assignment.hpp"
#include "xar_bridge/ck3_12003_commander_assignment_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12003.hpp"

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
constexpr std::uintptr_t kSecondaryVtable = 0x1200301;
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
  // Queue ACK is deliberately independent of the simulated game state. Keep
  // residual ownership here to exercise the production helper's destructor.
  return active->queue_accepted;
}
void Initialize(Fixture &fixture) {
  active = &fixture;
  Put(fixture.unit.data(), 0x10, kUnit);
  Put(fixture.unit.data(), 0x174, kPlayer);
  Put(fixture.unit.data(), 0x178, kArmy);
  Put(fixture.army.data(), 0x10, kArmy);
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
  fixture.reader.enabled = fixture.reader.armies.enabled = true;
  fixture.reader.armies.unit_storage_slot = &fixture.unit_storage;
  fixture.reader.armies.internal_army_storage_slot = &fixture.army_storage;
  fixture.reader.character_storage_slot = &fixture.character_storage;
  fixture.reader.vector_allocator = fixture.allocator.data();
  fixture.reader.collect_candidates = Collect;
  fixture.reader.can_set_commander = CanAssign;
  fixture.reader.get_native_ai_base_quality = BaseQuality;
  fixture.reader.get_generic_advantage = GenericAdvantage;
  fixture.reader.get_army_commander = CurrentCommander;
  fixture.scope.paused = fixture.scope.map_ready = fixture.scope.has_played_character =
      fixture.scope.played_character_alive = true;
  fixture.scope.played_character_id = kPlayer;
  xar::game::ArmySnapshot row{};
  row.army_id = kUnit;
  row.owner_character_id = kPlayer;
  row.controllable = true;
  fixture.scope.player_armies.push_back(row);
  fixture.command_vtable[0] = reinterpret_cast<std::uintptr_t>(&Delete);
  fixture.command_vtable[8] = reinterpret_cast<std::uintptr_t>(&Clone);
}

void EmitObserver(const std::filesystem::path &path,
                  const ArmyCommanderCandidatesSnapshot &output,
                  CommanderCandidatesReadResult result) {
  std::ofstream file(path, std::ios::binary);
  file << "{\"type\":\"command_result\",\"protocol_version\":1,\"ok\":true,\"result\":"
       << SerializeArmyCommanderCandidates(output, result, 7, 11, 53236608,
              "query-army-commander-candidates-v1-for-army-" + std::to_string(kUnit))
       << "}\n";
  Check(bool(file), "genuine production observer packet written");
}

void EmitAssignment(const std::filesystem::path &path,
                    const CommanderAssignmentResult &output,
                    CommanderAssignmentStatus status) {
  std::ofstream file(path, std::ios::binary);
  file << "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":1,"
          "\"ok\":true,\"result\":"
       << SerializeArmyCommanderAssignment(output, status, 7, 11, 53236608,
              "assign-army-commander-v1-army-" + std::to_string(kUnit) +
              "-to-character-" + std::to_string(output.requested_commander_character_id))
       << "}\n";
  Check(bool(file), "genuine production assignment packet written");
}

} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire output directory required");
    const std::filesystem::path wire(argv[1]);
    constexpr std::uintptr_t image = 0x140000000;
    const auto qualified = BindCommanderAssignmentImage(image, kExecutableSha256);
    Check(qualified.enabled &&
              reinterpret_cast<std::uintptr_t>(qualified.create_default) == image + 0x297BB00 &&
              reinterpret_cast<std::uintptr_t>(qualified.validate_source) == image + 0x2971480,
          "exact .3 binder uses reviewed native factory and primary command validator");
    Check(!BindCommanderAssignmentImage(image, "old-build").enabled,
          "exact .3 command constructor cannot be borrowed by another executable");

    Fixture fixture{};
    Initialize(fixture);
    CommanderAssignmentBindings bindings{};
    bindings.enabled = true;
    bindings.commanders = fixture.reader;
    bindings.commands.enabled = true;
    bindings.commands.command_manager = &fixture.queue_calls;
    bindings.commands.queue_owned_command = Queue;
    bindings.create_default = CreateDefault;
    bindings.validate_source = ValidateSource;
    CommanderAssignmentResult output{};
    using Status = CommanderAssignmentStatus;

    fixture.candidate_eligible = false;
    auto status = ApplyArmyCommanderAssignment(bindings, fixture.scope, kUnit, kCandidate, output);
    Check(status == Status::rejected && output.final_eligibility_observable &&
              !output.can_assign && !output.command_submitted && !output.verification_pending &&
              output.unavailable_reason == "native_final_commander_eligibility_false",
          "native mode 1 eligibility false is observable and does not submit");
    Check(fixture.factory_calls == 0 && fixture.queue_calls == 0 && fixture.collect_calls == 1,
          "native eligibility rejection occurs before command construction");
    EmitAssignment(wire / "eligibility-rejected.json", output, status);

    fixture.candidate_eligible = true;
    status = ApplyArmyCommanderAssignment(bindings, fixture.scope, kUnit, kUnlisted, output);
    Check(status == Status::rejected && !output.final_eligibility_observable &&
              output.unavailable_reason == "candidate_not_observed_in_native_collection" &&
              fixture.factory_calls == 0 && fixture.queue_calls == 0,
          "an existing but unlisted character cannot be selected without native candidate observation");
    EmitAssignment(wire / "unlisted-rejected.json", output, status);

    const auto prior_collections = fixture.collect_calls;
    Put(fixture.unit.data(), 0x174, kOther);
    status = ApplyArmyCommanderAssignment(bindings, fixture.scope, kUnit, kCandidate, output);
    Check(status == Status::unavailable &&
              output.unavailable_reason == "native_carmy_or_owner_unavailable" &&
              fixture.factory_calls == 0 && fixture.queue_calls == 0 &&
              fixture.collect_calls == prior_collections,
          "public player row cannot override the native CUnit owner");
    EmitAssignment(wire / "owner-unavailable.json", output, status);
    Put(fixture.unit.data(), 0x174, kPlayer);

    Put(fixture.army.data(), 0x124, std::int32_t{0});
    status = ApplyArmyCommanderAssignment(bindings, fixture.scope, kUnit, kCandidate, output);
    Check(status == Status::unavailable &&
              output.unavailable_reason == "native_carmy_or_owner_unavailable" &&
              fixture.factory_calls == 0 && fixture.queue_calls == 0 &&
              fixture.collect_calls == prior_collections,
          "current public CUnit must match the internal CArmy back reference");
    EmitAssignment(wire / "carmy-unavailable.json", output, status);
    Put(fixture.army.data(), 0x124, kUnit);

    fixture.source_valid = false;
    status = ApplyArmyCommanderAssignment(bindings, fixture.scope, kUnit, kCandidate, output);
    Check(status == Status::rejected && output.final_eligibility_observable && output.can_assign &&
              !output.native_command_valid && !output.command_submitted &&
              output.unavailable_reason == "native_commander_command_validator_false",
          "command validator false remains separate from eligibility true");
    Check(fixture.factory_calls == 1 && fixture.validator_calls == 1 && fixture.clone_calls == 0 &&
              fixture.queue_calls == 0 && fixture.delete_calls == 1,
          "native factory source is released on final validator rejection");
    EmitAssignment(wire / "validator-rejected.json", output, status);

    fixture.source_valid = true;
    fixture.queue_accepted = false;
    status = ApplyArmyCommanderAssignment(bindings, fixture.scope, kUnit, kCandidate, output);
    Check(status == Status::rejected && output.native_command_valid && !output.command_submitted &&
              !output.verification_pending && output.unavailable_reason == "native_commander_queue_rejected",
          "owned queue rejection does not claim a submitted assignment");
    Check(fixture.factory_calls == 2 && fixture.validator_calls == 2 && fixture.clone_calls == 1 &&
              fixture.queue_calls == 1 && fixture.delete_calls == 3,
          "rejected owned queue releases native source and residual clone");
    EmitAssignment(wire / "queue-rejected.json", output, status);

    fixture.queue_accepted = true;
    status = ApplyArmyCommanderAssignment(bindings, fixture.scope, kUnit, kCandidate, output);
    Check(status == Status::submitted && output.native_command_valid && output.command_submitted &&
              output.verification_pending && output.unavailable_reason.empty() &&
              output.army_id == kUnit && output.native_carmy_id == kArmy &&
              output.owner_character_id == kPlayer && output.prior_commander_character_id == -1,
          "successful owned queue returns a typed ACK with independent verification pending");
    Check(fixture.factory_calls == 3 && fixture.validator_calls == 3 && fixture.clone_calls == 2 &&
              fixture.queue_calls == 2 && fixture.delete_calls == 5,
          "one accepted assignment clones and queues once with both native owned objects released");
    Check(Get<std::int32_t>(fixture.army.data(), 0x120) == -1,
          "queue acceptance alone cannot mutate the independent commander observation");
    EmitAssignment(wire / "submitted-ack.json", output, status);

    ArmyCommanderCandidatesSnapshot observation{};
    auto read = ReadArmyCommanderCandidates(fixture.reader, fixture.scope, kUnit, observation);
    Check(read == CommanderCandidatesReadResult::available &&
              observation.current_commander_status == "absent" &&
              observation.current_commander_character_id == -1,
          "fresh production readback can remain pending after a successful command ACK");
    EmitObserver(wire / "readback-pending.json", observation, read);

    // This explicit fixture state transition represents game application. The
    // observation is produced independently, never copied from the ACK DTO.
    Put(fixture.army.data(), 0x120, kCandidate);
    fixture.candidate_eligible = false;
    read = ReadArmyCommanderCandidates(fixture.reader, fixture.scope, kUnit, observation);
    Check(read == CommanderCandidatesReadResult::available &&
              observation.current_commander_status == "available" &&
              observation.current_commander_character_id == kCandidate &&
              !observation.candidates.front().can_assign,
          "independent native getter confirms assignment even when replacement eligibility is now false");
    EmitObserver(wire / "readback-confirmed.json", observation, read);

    status = ApplyArmyCommanderAssignment(bindings, fixture.scope, kUnit, kCandidate, output);
    Check(status == Status::already_assigned && !output.can_assign &&
              output.prior_commander_character_id == kCandidate && !output.command_submitted &&
              !output.verification_pending && fixture.factory_calls == 3 && fixture.queue_calls == 2,
          "actual current commander readback resolves an already assigned request without resubmission");
    EmitAssignment(wire / "already-assigned.json", output, status);
    Check(fixture.collect_calls == 8 && fixture.release_calls == 8 && fixture.can_calls == 16 &&
              fixture.allocated == nullptr && fixture.callback_error.empty(),
          "all observed native vectors are released and exact callback contracts hold");
    std::cout << "PASS checks=" << checks << " cases=10\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
