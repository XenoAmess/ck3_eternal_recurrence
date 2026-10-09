// AUTHORED_NOTRUN: three new historical preparation-Model association worlds.
// Reuse synthetic memory infrastructure only; the included producer never runs.
#define main PersonFollowing2922680PreparationModelMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include <array>
#include <span>

namespace {
enum class PreparationKind { mutation, owner_unread, recapture };
struct PreparationSpec { const char *name; PreparationKind kind; };
constexpr PreparationSpec kPreparationCases[] = {
    {"historical-preparation-model-before-original-mutation", PreparationKind::mutation},
    {"preparation-model-owner-unread-numerical-ready", PreparationKind::owner_unread},
    {"new-context-fresh-preparation-model", PreparationKind::recapture},
};
constexpr std::array<std::int32_t, 6> kPreparationCounts{
    7, -3, 0, (std::numeric_limits<std::int32_t>::max)(), -1,
    (std::numeric_limits<std::int32_t>::min)()};
constexpr std::array<std::int64_t, 6> kPreparationFirstWeights{
    700'000, -300'000, 0, 214'748'364'700'000LL, -100'000,
    -214'748'364'800'000LL};
constexpr std::array<std::int64_t, 6> kPreparationSecondWeights{
    800'000, -200'000, 100'000, -214'748'364'800'000LL, 0,
    -214'748'364'700'000LL};
std::uintptr_t PreparationReturnBits(std::uint32_t index) {
  return std::uintptr_t{0xBADC0FFE00000000ULL} |
      static_cast<std::uint32_t>(kPreparationCounts[index]);
}
struct PreparationWorld;
PreparationWorld *preparation_active_world = nullptr;
std::size_t preparation_original_calls = 0;
void *preparation_original_character = nullptr;
void *preparation_original_context = nullptr;
std::uint32_t preparation_original_index = 0;
std::uintptr_t __fastcall PreparationOriginal(void *, void *, std::uint32_t);
std::uintptr_t __fastcall PreparationAppendOriginal(void *, void *, std::int64_t) {
  return std::uintptr_t{0xDEADBEEF13572468ULL};
}

struct PreparationWorld : World {
  void *historical_model = nullptr;
  void *historical_context = nullptr;
  void *aggregate_pc = nullptr;
  void *installed_current_model = memory.Allocate(0xF0);
  void *different_generation_owner = memory.Allocate(0x20);
  void *baseline_keys = memory.Allocate(3 * 2);
  void *baseline_values = memory.Allocate(3 * 8);
  void *empty_pc = memory.Allocate(0x70);
  void *capture_game_slot = memory.Allocate(sizeof(void *));
  void *capture_character_slot = memory.Allocate(sizeof(void *));
  native4::PersonSixStageCaptureBindings12004 capture_bindings{};

  PreparationWorld() {
    memory.Put(installed_current_model, 8, subject);
    memory.Put(installed_current_model, 0x10, static_cast<void *>(nullptr));
    memory.Put(different_generation_owner, 0x18, std::uint32_t{0x05000003U});
    memory.Put(context, 0x198 + 0xC, std::int32_t{0});
    Property(empty_pc, nullptr, nullptr, {}, {});
    NewPreparationModel(false);
    capture_bindings.memory = bindings.current_person_carrier_direct;
    memory.Put(capture_game_slot, 0, game_state);
    capture_bindings.game_state_slot = reinterpret_cast<void **>(capture_game_slot);
    memory.Put(capture_character_slot, 0, character_storage);
    preparation_original_calls = 0;
    preparation_original_character = preparation_original_context = nullptr;
    preparation_original_index = 0;
    preparation_active_world = this;
    Require(native4::InitializePersonSixStageCaptureFixture12004(
                capture_bindings, &PreparationOriginal, &PreparationAppendOriginal),
            "preparation Model fixture initialization failed");
  }
  void NewPreparationModel(bool second) {
    historical_model = memory.Allocate(0xF0);
    historical_context = Offset(historical_model, 0x10);
    aggregate_pc = Offset(historical_context, 0x68);
    memory.Put(historical_model, 8, subject);
    memory.Put(historical_model, 0x10, static_cast<void *>(nullptr));
    model = historical_model;
    memory.Put(scratch, 0x258, model);
    if (second) {
      baseline_keys = memory.Allocate(2 * 2);
      baseline_values = memory.Allocate(2 * 8);
      Property(aggregate_pc, baseline_keys, baseline_values, {222, 129}, {75, -25});
    } else {
      Property(aggregate_pc, baseline_keys, baseline_values, {129, 97, 111},
               {100'000, 0, -25'000});
    }
  }
  void OriginalMutation(std::uint32_t index) {
    if (index != std::uint32_t{0}) return;
    // Both changes occur after Invoke's before-original association copy.
    memory.Put(historical_model, 8, different_generation_owner);
    model = installed_current_model;
    memory.Put(scratch, 0x258, model);
  }
  void Capture() {
    for (std::uint32_t index = 0; index < std::uint32_t{6}; ++index) {
      const auto before = preparation_original_calls;
      const auto returned = native4::InvokePersonSixStageCapture12004(
          subject, historical_context, index,
          kModule + native4::kPersonSixStageReturnRva12004);
      Require(returned == PreparationReturnBits(index) &&
                  preparation_original_calls == before + std::size_t{1} &&
                  preparation_original_character == subject &&
                  preparation_original_context == historical_context &&
                  preparation_original_index == index,
              "Invoke changed original forwarding, arguments or full RAX");
      if (index != std::uint32_t{2})
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(empty_pc),
            kPreparationFirstWeights[index],
            kModule + native4::kPersonSixStageFirstAppendReturnRva12004);
      if (index != std::uint32_t{4})
        native4::ObservePersonSixStageAppend12004(
            Address(historical_context), Address(empty_pc),
            kPreparationSecondWeights[index],
            kModule + native4::kPersonSixStageSecondAppendReturnRva12004);
    }
    native4::CompletePersonSixStageCapture12004(
        Address(subject), static_cast<std::uint32_t>(kSubject),
        Address(historical_context));
  }
  void Configure(PreparationKind kind) {
    if (kind == PreparationKind::owner_unread)
      memory.Refuse(historical_model, 8, sizeof(void *), false);
    Capture();
    if (kind != PreparationKind::recapture) return;
    const auto first = native4::ReadPersonSixStageCaptureForCharacter12004(
        Address(subject), static_cast<std::uint32_t>(kSubject));
    const auto first_model = historical_model;
    const auto first_context = historical_context;
    Require(first.capture_sequence == std::uint64_t{1} &&
                first.preparation_model.ready &&
                first.preparation_model.model_identity == Address(first_model) &&
                first.preparation_model.owner_character_identity == Address(subject) &&
                first.preparation_model.owner_character_id ==
                    static_cast<std::uint32_t>(kSubject) &&
                first.pre_six_aggregate.pc.properties &&
                first.post_six_aggregate.pc.properties,
            "first capture did not own its historical preparation association");
    memory.Put(baseline_values, 0, std::int64_t{999'999});
    NewPreparationModel(true);
    Require(historical_model != first_model && historical_context != first_context,
            "recapture reused the first Model/context");
    Capture();
    Require(first.preparation_model.model_identity == Address(first_model) &&
                first.context_identity == Address(first_context) &&
                first.preparation_model.owner_character_identity == Address(subject) &&
                first.preparation_model.owner_character_id ==
                    static_cast<std::uint32_t>(kSubject) &&
                first.preparation_model.owner_matches_capture == true &&
                first.pre_six_aggregate.pc.properties->values_q64 ==
                    std::vector<std::int64_t>{100'000, 0, -25'000} &&
                first.post_six_aggregate.pc.properties->values_q64 ==
                    std::vector<std::int64_t>{100'000, 0, -25'000},
            "fresh Model capture changed the preceding owned association/PCs");
  }
};

std::uintptr_t __fastcall PreparationOriginal(void *character, void *context,
                                            std::uint32_t index) {
  ++preparation_original_calls;
  preparation_original_character = character;
  preparation_original_context = context;
  preparation_original_index = index;
  Require(preparation_active_world != nullptr && index < std::uint32_t{6},
          "fixture original received an unexpected native index");
  preparation_active_world->OriginalMutation(index);
  return PreparationReturnBits(index);
}

void ProducePreparationModel(const std::filesystem::path &directory,
                             const PreparationSpec &spec,
                             std::uint64_t sequence) {
  PreparationWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const std::array<std::int32_t, 1> requested_ids{World::kSubject};
  const auto source_before = world.memory.Bytes();
  const auto captures = native4::CollectPersonSixStageQuery12004(
      reinterpret_cast<void **>(world.capture_character_slot),
      std::span<const std::int32_t>{requested_ids}, snapshot.snapshot_revision,
      snapshot.observed_date_raw);
  Require(world.memory.unexpected_reads == 0 && world.memory.Bytes() == source_before &&
              captures.character_captures.size() == std::size_t{1},
          "whole-query collection changed source bytes or requested cardinality");
  const auto &leaf = captures.character_captures.front();
  const auto &association = leaf.preparation_model;
  const bool partial = spec.kind == PreparationKind::owner_unread;
  const bool recapture = spec.kind == PreparationKind::recapture;
  Require(leaf.ready && leaf.raw_counts_ready && leaf.capture_complete &&
              leaf.aggregate_postimage_inputs_ready &&
              leaf.aggregate_postimage_comparison_ready &&
              leaf.pre_six_aggregate.observed && leaf.pre_six_aggregate.pc.ready &&
              leaf.post_six_aggregate.observed && leaf.post_six_aggregate.pc.ready &&
              leaf.capture_sequence == (recapture ? std::uint64_t{2} : std::uint64_t{1}) &&
              preparation_original_calls == (recapture ? std::size_t{12} : std::size_t{6}) &&
              !leaf.actual_model_write_performed && !leaf.full_helper_ready,
          "association changed independent six-stage or numerical readiness");
  Require(association.observed && association.ready == !partial &&
              association.model_identity == Address(world.historical_model) &&
              leaf.context_identity == Address(world.historical_context) &&
              Address(world.historical_context) == Address(world.historical_model) + 0x10 &&
              world.model != world.historical_model,
          "historical preparation Model was replaced by the installed current Model");
  if (partial) {
    Require(association.reason == "preparation_model_owner_unread" &&
                !association.owner_character_identity && !association.owner_character_id &&
                !association.owner_matches_capture,
            "unread Model owner became a complete association");
  } else {
    Require(association.reason.empty() &&
                association.owner_character_identity == Address(world.subject) &&
                association.owner_character_id == static_cast<std::uint32_t>(World::kSubject) &&
                association.owner_matches_capture == true &&
                association.owner_character_identity != Address(world.different_generation_owner),
            "before-original owner/full ID was replaced by the mutated Model owner");
  }
  const auto expected_keys = recapture ? std::vector<std::uint16_t>{222, 129}
                                       : std::vector<std::uint16_t>{129, 97, 111};
  const auto expected_values = recapture ? std::vector<std::int64_t>{75, -25}
                                         : std::vector<std::int64_t>{100'000, 0, -25'000};
  for (const auto *pc : {&leaf.pre_six_aggregate.pc, &leaf.post_six_aggregate.pc})
    Require(pc->properties && pc->properties->keys_u16 == expected_keys &&
                pc->properties->values_q64 == expected_values,
            "Model association changed the independently copied baseline/completion PC");
  const auto packet =
      xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultWithPersonSixStagesV1(
          std::string("person-preparation-model-") + spec.name,
          World::kStep, sequence, snapshot, captures);
  Require(packet.find("\"preparation_model\":{") != std::string::npos,
          "whole production formatter omitted preparation Model association");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist preparation Model whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_preparation_model_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create preparation Model whole-packet directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kPreparationCases)
    ProducePreparationModel(directory, spec, ++sequence);
  std::cout << "person preparation Model: three new whole-command packets\n";
  return 0;
}
