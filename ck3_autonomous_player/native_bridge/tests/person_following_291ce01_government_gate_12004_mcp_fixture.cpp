// AUTHORED_NOTRUN: fresh stable Government getter/gate worlds through the
// production current-person query and whole-command formatter. Reuse only
// synthetic World setup; the historical main/Produce are never invoked.
#define main PersonFollowing2922680HistoricalMainNotInvoked
#include "person_following_2922680_12004_mcp_fixture.cpp"
#undef main
#include "xar_bridge/ck3_12004_person_government_gate.hpp"

namespace {
enum class GovernmentGateKind {
  living_clear, living_set, selected_null, invalid_input,
  related_hit, related_generation_fallback, flags_unread
};
struct GovernmentGateSpec {
  const char *name;
  GovernmentGateKind kind;
};
constexpr GovernmentGateSpec kGovernmentGateCases[] = {
    {"living-context-bit-clear", GovernmentGateKind::living_clear},
    {"living-context-bit-set", GovernmentGateKind::living_set},
    {"selected-null-default-bit-clear", GovernmentGateKind::selected_null},
    {"invalid-input-default-bit-set", GovernmentGateKind::invalid_input},
    {"related-character-generation-hit", GovernmentGateKind::related_hit},
    {"related-character-generation-fallback", GovernmentGateKind::related_generation_fallback},
    {"government-flags-unread", GovernmentGateKind::flags_unread},
};

struct GovernmentGateWorld : World {
  static constexpr std::uintptr_t kCharacterRegistry = kModule + 0x5C67568;
  static constexpr std::uintptr_t kCharacterFallback = kModule + 0x5C67570;
  static constexpr std::uintptr_t kGovernmentFallback = kModule + 0x5D1E2A8;
  static constexpr std::uint32_t kRelatedId = 0x03000001;
  static constexpr std::uint32_t kClearFlags = 0x80000001;
  static constexpr std::uint32_t kSetFlags = 0x80080001;
  void *government_context = memory.Allocate(0x408);
  void *government = memory.Allocate(0x44);
  void *default_government = memory.Allocate(0x44);
  void *government_fallback_slot = memory.Allocate(8, kGovernmentFallback);
  void *related_registry_slot = memory.Allocate(8, kCharacterRegistry);
  void *related_fallback_slot = memory.Allocate(8, kCharacterFallback);
  void *related_registry = memory.Allocate(0x30);
  void *related_slots = memory.Allocate(2 * 0x10);
  void *relay = memory.Allocate(0xD0);
  void *related_character = memory.Allocate(0x1D8);
  void *related_fallback_character = memory.Allocate(0x1D8);
  void *related_context = memory.Allocate(0x408);

  GovernmentGateWorld() {
    memory.Put(subject, 0x1C, std::uint32_t{0x43686172});
    memory.Put(subject, 0x1C0, government_context);
    // Preserve a genuinely empty, independently ready preceding PC helper.
    memory.Put(government_context, 0x198 + 0xC, std::int32_t{0});
    memory.Put(government_context, 0x3F8, government);
    memory.Put(government, 0x40, kClearFlags);
    memory.Put(default_government, 0x40, kClearFlags);
    memory.Put(government_fallback_slot, 0, default_government);
    memory.Put(related_registry_slot, 0, related_registry);
    memory.Put(related_fallback_slot, 0, related_fallback_character);
    memory.Put(related_registry, 0x20, related_slots);
    memory.Put(related_registry, 0x2C, std::uint32_t{2});
    memory.Put(related_slots, 0x10 + 8, related_character);
    for (const auto character : {related_character, related_fallback_character}) {
      memory.Put(character, 0x1C, std::uint32_t{0x43686172});
      memory.Put(character, 0x1D0, static_cast<void *>(nullptr));
      memory.Put(character, 0x1C0, related_context);
    }
    memory.Put(related_character, 0x18, kRelatedId);
    memory.Put(related_fallback_character, 0x18, std::uint32_t{0x05000002});
    memory.Put(related_context, 0x3F8, government);
    memory.Put(relay, 0xC8, kRelatedId);
  }
  void Configure(GovernmentGateKind kind) {
    switch (kind) {
    case GovernmentGateKind::living_set:
      memory.Put(government, 0x40, kSetFlags);
      break;
    case GovernmentGateKind::selected_null:
      memory.Put(government_context, 0x3F8, static_cast<void *>(nullptr));
      break;
    case GovernmentGateKind::invalid_input:
      memory.Put(subject, 0x1C, std::uint32_t{0});
      memory.Put(default_government, 0x40, kSetFlags);
      break;
    case GovernmentGateKind::related_hit:
    case GovernmentGateKind::related_generation_fallback:
      memory.Put(subject, 0x1C0, static_cast<void *>(nullptr));
      memory.Put(subject, 0x1B8, relay);
      if (kind == GovernmentGateKind::related_generation_fallback) {
        memory.Put(related_character, 0x18, std::uint32_t{0x04000001});
        memory.Put(government, 0x40, kSetFlags);
      }
      break;
    case GovernmentGateKind::flags_unread:
      memory.Refuse(government, 0x40, 4, false);
      break;
    default: break;
    }
    if (kind != GovernmentGateKind::selected_null &&
        kind != GovernmentGateKind::invalid_input)
      memory.Refuse(default_government, 0x40, 4);
  }
};

void ProduceGovernmentGate(const std::filesystem::path &directory,
                           const GovernmentGateSpec &spec,
                           std::uint64_t sequence) {
  GovernmentGateWorld world;
  world.Configure(spec.kind);
  const auto snapshot = world.Observe();
  const auto &person = *snapshot.character_observations->front().current_person_state;
  Require(person.following_291ce01_government_gate.has_value(),
          "same-query current-person Government gate is missing");
  const auto &gate = *person.following_291ce01_government_gate;
  const bool unavailable = spec.kind == GovernmentGateKind::flags_unread;
  const bool bit_set = spec.kind == GovernmentGateKind::living_set ||
      spec.kind == GovernmentGateKind::invalid_input ||
      spec.kind == GovernmentGateKind::related_generation_fallback;
  const bool related = spec.kind == GovernmentGateKind::related_hit ||
                       spec.kind == GovernmentGateKind::related_generation_fallback;
  const auto selection = spec.kind == GovernmentGateKind::selected_null
      ? "selected_null_fallback" : spec.kind == GovernmentGateKind::invalid_input
      ? "invalid_character_fallback" : "living_context";
  const auto expected_government = spec.kind == GovernmentGateKind::selected_null ||
      spec.kind == GovernmentGateKind::invalid_input
      ? world.default_government : world.government;
  Require(gate.build_version == native4::kGameVersion &&
              gate.executable_sha256 == native4::kExecutableSha256 &&
              gate.character_id == static_cast<std::uint32_t>(World::kSubject) &&
              gate.character_identity == Address(world.subject) &&
              gate.selected_model_identity == Address(world.model) &&
              gate.model_owner_matches == true && gate.selection == selection &&
              gate.government_identity == Address(expected_government) &&
              gate.ready == !unavailable,
          "Government gate exact-build receiver, owner or getter selection changed");
  Require(gate.steps.size() == (related ? 2U : 1U),
          "Government traversal steps were collapsed or invented");
  for (std::size_t index = 0; index < gate.steps.size(); ++index)
    Require(gate.steps[index].native_index == index,
            "Government traversal order changed");
  Require(gate.steps[0].character_identity == Address(world.subject) &&
              gate.steps[0].magic_u32 == (spec.kind == GovernmentGateKind::invalid_input
                  ? 0U : 0x43686172U),
          "Government getter lost actual root magic or Character identity");
  if (unavailable) {
    Require(gate.reason == "government_flags_unread" && !gate.flags_40_u32 &&
                !gate.bit19_set && !gate.branch_admitted && !gate.known_no_contribution,
            "unread flags became a known clear gate");
  } else {
    Require(gate.reason.empty() &&
                gate.flags_40_u32 == (bit_set ? GovernmentGateWorld::kSetFlags
                                             : GovernmentGateWorld::kClearFlags) &&
                gate.bit19_set == bit_set && gate.branch_admitted == bit_set &&
                gate.known_no_contribution == !bit_set,
            "raw DWORD, bit19 gate or known empty branch changed");
  }
  if (related) {
    const auto &root = gate.steps[0];
    const bool fallback = spec.kind == GovernmentGateKind::related_generation_fallback;
    const auto expected_character = fallback ? world.related_fallback_character
                                              : world.related_character;
    Require(root.related_context_identity == Address(world.relay) &&
                root.related_full_id_u32 == GovernmentGateWorld::kRelatedId &&
                root.registry_count_u32 == 2U &&
                root.registry_slots_identity == Address(world.related_slots) &&
                root.candidate_identity == Address(world.related_character) &&
                root.candidate_full_id_u32 == (fallback ? 0x04000001U
                                                       : GovernmentGateWorld::kRelatedId) &&
                root.resolution_selection == (fallback ? "fallback" : "mapped") &&
                root.selected_character_identity == Address(expected_character) &&
                gate.steps[1].character_identity == Address(expected_character) &&
                gate.steps[1].full_id_u32 == (fallback ? 0x05000002U
                                                      : GovernmentGateWorld::kRelatedId) &&
                gate.steps[1].living_context_identity == Address(world.related_context),
            "related Character full generation resolution or repeat evaluation changed");
  }
  Require(person.following_2922680 && person.following_2922680->ready &&
              person.following_2922680->primary_ready &&
              person.following_2922680->append_occurrences.empty(),
          "new independent raw gate changed preceding known-empty PC helper");
  const auto request_id = std::string("person-government-gate-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, World::kStep, sequence, snapshot);
  Require(packet.find("\"following_291ce01_government_gate\":{") != std::string::npos &&
              packet.find(request_id) != std::string::npos,
          "real whole-command formatter lost the Government gate");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist original Government gate whole packet");
}

void CheckDeathContextDirectReader() {
  GovernmentGateWorld world;
  void *const death_context = world.memory.Allocate(0x90);
  world.memory.Put(world.subject, 0x1D0, death_context);
  world.memory.Put(death_context, 0x88, world.government);
  world.memory.Refuse(world.government_context, 0x3F8, 8);
  world.memory.Refuse(world.default_government, 0x40, 4);
  const auto before = world.memory.Bytes();
  // Character+1D0 is the real DeathData pointer. Exercise its getter directly;
  // do not alter an alive observation or manufacture a whole-query packet.
  const auto gate = native4::ReadPersonGovernmentGateForCharacter12004(
      world.bindings.current_person_carrier_direct, Address(world.subject));
  Require(gate.ready && gate.selection == "death_context" &&
              gate.government_identity == Address(world.government) &&
              gate.flags_40_u32 == GovernmentGateWorld::kClearFlags &&
              gate.bit19_set == false && gate.known_no_contribution == true &&
              gate.steps.size() == 1 &&
              gate.steps[0].death_context_identity == Address(death_context) &&
              world.memory.unexpected_reads == 0 && world.memory.Bytes() == before,
          "direct death-context getter or read-only demands differ");
}
} // namespace

int main(int argc, char **argv) try {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_following_291ce01_government_gate_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create Government gate packet output directory");
  CheckDeathContextDirectReader();
  std::uint64_t sequence = 0;
  for (const auto &spec : kGovernmentGateCases)
    ProduceGovernmentGate(directory, spec, ++sequence);
  std::cout << "person Government gate: seven fresh production whole-command packets\n";
  return 0;
} catch (const std::exception &error) {
  std::cerr << "person Government gate: " << error.what() << '\n';
  return 1;
}
