// One new, unexecuted whole-command producer. Source sealed first in
// docs/ck3-native-ai/battle-person-carrier-same-query-12004.md.
// Uses the real exact4 Battle factory, production double-sample terminal reader,
// and shared production command_result formatter. No historical reader stubs,
// getter invocation, leaf-only JSON adapter, SDK, game, or process access.
#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"
#include "xar_bridge/ck3_12004_battle.hpp"
#include "xar_bridge/ck3_12004_person_carrier_direct.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <string>
#include <string_view>
#include <system_error>
#include <utility>
#include <vector>

namespace {
namespace native4 = xar::ck3_12004;
namespace game = xar::game;

void Require(bool condition, std::string_view message) {
  if (!condition) {
    std::cerr << "person-carrier-direct12004-mcp: " << message << '\n';
    std::exit(1);
  }
}

std::uintptr_t Address(const void *pointer) {
  return reinterpret_cast<std::uintptr_t>(pointer);
}
void *At(void *pointer, std::size_t offset) {
  return static_cast<std::byte *>(pointer) + offset;
}

struct Memory {
  struct Region {
    std::unique_ptr<std::byte[]> bytes;
    std::uintptr_t read_address;
    std::size_t size;
  };
  struct Interval {
    std::uintptr_t address;
    std::size_t size;
    std::size_t attempts = 0;
  };
  std::vector<Region> regions;
  std::vector<Interval> denied;
  std::vector<Interval> hidden;
  std::uintptr_t carrier_field = 0;
  std::size_t carrier_reads = 0;

  void *Allocate(std::size_t size, std::uintptr_t virtual_address = 0) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *const pointer = bytes.get();
    regions.push_back({std::move(bytes),
                       virtual_address == 0 ? Address(pointer) : virtual_address,
                       size});
    return pointer;
  }
  template <typename T>
  void Put(void *pointer, std::size_t offset, T value) {
    for (auto &region : regions) {
      const auto begin = Address(pointer);
      const auto base = Address(region.bytes.get());
      if (begin >= base && begin - base <= region.size &&
          offset <= region.size - static_cast<std::size_t>(begin - base) &&
          sizeof(value) <= region.size - static_cast<std::size_t>(begin - base) - offset) {
        std::memcpy(static_cast<std::byte *>(pointer) + offset, &value, sizeof(value));
        return;
      }
    }
    Require(false, "setup write outside owned fake memory");
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = Address(address);
    if (begin == memory.carrier_field && size == sizeof(void *))
      ++memory.carrier_reads;
    const auto overlaps = [begin, size](const Interval &interval) {
      return begin < interval.address + interval.size &&
             interval.address < begin + size;
    };
    for (auto &interval : memory.denied) {
      if (overlaps(interval)) { ++interval.attempts; return false; }
    }
    for (auto &interval : memory.hidden) {
      if (overlaps(interval)) { ++interval.attempts; return false; }
    }
    for (const auto &region : memory.regions) {
      if (begin >= region.read_address && begin - region.read_address <= region.size &&
          size <= region.size - static_cast<std::size_t>(begin - region.read_address)) {
        std::memcpy(output, region.bytes.get() + (begin - region.read_address), size);
        return true;
      }
    }
    return false;
  }
  void NoRead(const void *pointer, std::size_t offset, std::size_t size) {
    denied.push_back({Address(pointer) + offset, size});
  }
  void NoReadVirtual(std::uintptr_t address, std::size_t size) {
    denied.push_back({address, size});
  }
  std::size_t UndemandedAttempts() const {
    std::size_t attempts = 0;
    for (const auto &interval : denied) attempts += interval.attempts;
    return attempts;
  }
  std::vector<std::vector<std::byte>> ByteSnapshot() const {
    std::vector<std::vector<std::byte>> result;
    for (const auto &region : regions)
      result.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return result;
  }
};

struct Fixture {
  static constexpr std::uintptr_t kModule = 0x140000000;
  static constexpr std::uintptr_t kDefault =
      kModule + native4::kPersonCarrierDefaultPcRva12004;
  static constexpr std::uintptr_t kGuard =
      kModule + native4::kPersonCarrierDefaultGuardRva12004;
  static constexpr std::int32_t kPlayer = 29829;
  static constexpr std::int32_t kEnemy = 0x04000003;
  static constexpr std::uint32_t kEnemyUnsigned = 0x04000003U;
  static constexpr std::int32_t kStorageCount = kPlayer + 1;
  static constexpr std::uint64_t kRevision = 41;
  static constexpr std::string_view kStep =
      "query-battle-terminal-transition-v1-none:characters:67108867";

  Memory memory;
  void *game_state = memory.Allocate(0xA8);
  void *jomini_state = memory.Allocate(0x28);
  void *character_storage = memory.Allocate(0x30);
  void *character_slots = memory.Allocate(static_cast<std::size_t>(kStorageCount) * 0x10);
  void *player = memory.Allocate(0x1D8);
  void *enemy = memory.Allocate(0x1D8);
  void *scratch = memory.Allocate(0x290);
  void *model = memory.Allocate(0x20);
  void *carrier = memory.Allocate(0xB74);
  void *definition = memory.Allocate(0x3E8);
  void *table = memory.Allocate(2 * 0x340);
  void *mapped = At(table, 0x340);
  void *default_pc = memory.Allocate(0x78, kDefault);
  void *default_guard = memory.Allocate(4, kGuard);
  void *mapped_keys = memory.Allocate(8);
  void *mapped_values = memory.Allocate(32);
  void *default_keys = memory.Allocate(8);
  void *default_values = memory.Allocate(32);
  native4::BattleBindings bindings;
  game::Snapshot scope;

  Fixture() {
    memory.Put(game_state, 8, std::int32_t{53'236'632});
    memory.Put(jomini_state, 0x20, std::uint8_t{1});
    memory.Put(character_storage, 0x20, character_slots);
    memory.Put(character_storage, 0x2C, kStorageCount);
    Store(kPlayer, player);
    Store(kEnemy, enemy);
    memory.Put(player, native4::kCharacterFullIdOffset, kPlayer);
    memory.Put(enemy, native4::kCharacterFullIdOffset, kEnemy);
    memory.Put(enemy, 0x1B0, scratch);
    memory.Put(enemy, 0x1C8, carrier);
    memory.Put(enemy, native4::kCharacterDeathDataOffset, static_cast<void *>(nullptr));
    memory.Put(scratch, 0x258, model);
    memory.Put(scratch, 0x288, static_cast<void *>(nullptr));
    memory.Put(model, 8, enemy);
    memory.Put(carrier, 0x20, definition);
    memory.Put(carrier, 0xB70, std::int32_t{1});
    memory.Put(definition, 0x38, std::uint32_t{0x4744624F});
    memory.Put(definition, 0x3D8, table);
    memory.Put(definition, 0x3E4, std::int32_t{2});
    memory.Put(default_guard, 0, std::int32_t{7});
    Property(mapped, mapped_keys, mapped_values,
             {0x22A, 0xFFFF, 0x22A, 0},
             {-100'000, (std::numeric_limits<std::int64_t>::min)(), 0,
              (std::numeric_limits<std::int64_t>::max)()});
    Property(default_pc, default_keys, default_values, {0x22A}, {-250'000});
    memory.carrier_field = Address(enemy) + 0x1C8;
    memory.NoRead(model, 0x10, 0x10);
    memory.NoRead(mapped, 0x74, 4);
    memory.NoReadVirtual(kDefault + 0x74, 4);

    // Begin with the real actual4 factory. Only the three fixture roots and
    // the already bound direct leaf's guarded-copy callback/context change.
    bindings = native4::BindBattleImage(
        kModule, native4::kExecutableSha256, native4::BattleImageDependencies{});
    bindings.game_state_slot = &game_state;
    bindings.jomini_state_slot = &jomini_state;
    bindings.character_storage_slot = &character_storage;
    Require(bindings.enabled && bindings.current_person_carrier_direct.enabled &&
                bindings.current_person_carrier_direct.module_base == kModule,
            "actual4 factory did not install the exact direct binding");
    bindings.current_person_carrier_direct.read_memory = &Memory::Read;
    bindings.current_person_carrier_direct.read_context = &memory;
    Require(!bindings.current_person_state_enabled &&
                !bindings.current_person_effective_prowess_enabled &&
                !bindings.current_person_raw_numeric_inputs_enabled &&
                !bindings.current_person_context_branch_inputs_enabled &&
                !bindings.current_person_prior_context_inputs_enabled &&
                !bindings.current_person_stored_context_state_enabled &&
                !bindings.current_person_context_source_inputs.enabled &&
                !bindings.current_person_task_position.enabled &&
                !bindings.current_person_traits.enabled &&
                !bindings.full_backing_inputs_enabled,
            "actual4 fixture enabled legacy .3 person/backing bindings");

    scope.date_raw = 53'236'632;
    scope.paused = true;
    scope.map_ready = true;
    scope.has_played_character = true;
    scope.played_character_id = kPlayer;
    scope.played_character_alive = true;
  }
  void Store(std::int32_t full_id, void *character) {
    const auto slot = static_cast<std::uint32_t>(full_id) & 0xFFFFFFU;
    memory.Put(character_slots, static_cast<std::size_t>(slot) * 0x10 + 8, character);
  }
  void Property(void *pc, void *keys, void *values,
                const std::vector<std::uint16_t> &raw_keys,
                const std::vector<std::int64_t> &raw_values) {
    Require(raw_keys.size() == raw_values.size(), "fixture raw pair lengths differ");
    memory.Put(pc, 0xC, static_cast<std::int32_t>(raw_keys.size()));
    if (raw_keys.empty()) return;
    memory.Put(pc, 0, keys);
    memory.Put(pc, 0x68, values);
    for (std::size_t i = 0; i < raw_keys.size(); ++i) {
      memory.Put(keys, i * 2, raw_keys[i]);
      memory.Put(values, i * 8, raw_values[i]);
    }
  }
  void NoDefault() {
    memory.NoReadVirtual(kGuard, 4);
    memory.NoReadVirtual(kDefault, 0x70);
  }
  void NoMappedTable() {
    memory.NoRead(definition, 0x3D8, 8);
    memory.NoRead(table, 0, 2 * 0x340);
  }
  game::BattleTerminalTransitionSnapshotV1 Observe() {
    const auto bytes = memory.ByteSnapshot();
    game::BattleTerminalTransitionRequestV1 request;
    request.character_ids = {kEnemy};
    game::BattleTerminalTransitionSnapshotV1 output;
    const auto status = xar::ck3_12002::ReadBattleTerminalTransitionV1(
        bindings, scope, request, output);
    Require(status == game::BattleTerminalTransitionStatusV1::available &&
                output.status == status && output.unavailable_reason.empty() &&
                output.observed_date_raw == scope.date_raw &&
                output.prior_combat_id == -1 && output.subject_public_cunit_id == -1 &&
                !output.pending_death_queue,
            "production character-only terminal query unavailable");
    Require(memory.carrier_reads == 2 && memory.UndemandedAttempts() == 0 &&
                memory.ByteSnapshot() == bytes,
            "production double sample skipped, undemanded field read, or memory mutated");
    Require(output.character_observations && output.character_observations->size() == 1,
            "production query added, omitted, or substituted requested Character");
    const auto &observation = output.character_observations->front();
    Require(observation.character_id == kEnemy && observation.character_id != kPlayer &&
                scope.played_character_id == kPlayer && observation.alive == true &&
                observation.status == game::BattleTerminalCustodyStatusV1::none &&
                observation.actual_jailer_character_id == -1 &&
                observation.current_person_state,
            "enemy identity, player identity, actual custody, or person state differs");
    const auto &person = *observation.current_person_state;
    Require(!person.raw_numeric_inputs && !person.current_context_task_position_inputs &&
                !person.context_branch_inputs && !person.current_prior_context_inputs &&
                !person.current_stored_context_state && !person.current_context_source_inputs &&
                !person.effective_prowess.available && !person.effective_prowess.points &&
                person.injury_traits.status == game::BattleCurrentPersonInjuryTraitsStatusV1::unavailable &&
                person.death_record.status == game::BattleCurrentPersonDeathRecordStatusV1::unavailable &&
                person.carrier_1c8_b70_direct,
            "actual4 direct leaf promoted legacy .3 person observations");
    const auto &leaf = *person.carrier_1c8_b70_direct;
    Require(leaf.character_id == kEnemyUnsigned && leaf.character_identity == Address(enemy) &&
                leaf.selected_model_identity == Address(model) &&
                leaf.destination_pc_identity == Address(model) + 0x10 &&
                leaf.build_version == native4::kGameVersion &&
                leaf.executable_sha256 == native4::kExecutableSha256 &&
                leaf.weight_q100000 == 100'000,
            "same-query actual enemy/model identity or exact4 provenance differs");
    // Production dispatch supplies the mailbox revision after the same reader.
    output.snapshot_revision = kRevision;
    return output;
  }
};

enum class Case { absent, wrong_magic, mapped_empty, mapped_positive,
                  initialized_default, guard_zero, raw_partial, negative_rank };
struct Spec { const char *name; Case kind; };
constexpr Spec kCases[] = {
    {"absent-carrier", Case::absent},
    {"wrong-magic", Case::wrong_magic},
    {"mapped-empty", Case::mapped_empty},
    {"mapped-nonempty-signed-prowess", Case::mapped_positive},
    {"fallback-initialized", Case::initialized_default},
    {"fallback-guard-zero", Case::guard_zero},
    {"raw-partial-values", Case::raw_partial},
    {"negative-rank-undemanded-count", Case::negative_rank},
};

void Produce(const std::filesystem::path &directory, const Spec &spec,
             std::uint64_t sequence) {
  Fixture f;
  switch (spec.kind) {
  case Case::absent:
    f.memory.Put(f.enemy, 0x1C8, static_cast<void *>(nullptr));
    f.memory.NoRead(f.carrier, 0, 0xB74);
    f.memory.NoRead(f.definition, 0, 0x3E8);
    f.NoDefault();
    break;
  case Case::wrong_magic:
    f.memory.Put(f.definition, 0x38, std::uint32_t{0});
    f.memory.NoRead(f.carrier, 0xB70, 4);
    f.memory.NoRead(f.definition, 0x3E4, 4);
    f.NoMappedTable();
    f.NoDefault();
    break;
  case Case::mapped_empty:
    f.Property(f.mapped, f.mapped_keys, f.mapped_values, {}, {});
    f.memory.NoRead(f.mapped, 0, 8);
    f.memory.NoRead(f.mapped, 0x68, 8);
    f.NoDefault();
    break;
  case Case::mapped_positive:
    f.NoDefault();
    break;
  case Case::initialized_default:
    f.memory.Put(f.carrier, 0xB70, std::int32_t{2});
    f.memory.Put(f.default_guard, 0, std::int32_t{-2});
    f.NoMappedTable();
    break;
  case Case::guard_zero:
    f.memory.Put(f.carrier, 0xB70, std::int32_t{2});
    f.memory.Put(f.default_guard, 0, std::int32_t{0});
    f.NoMappedTable();
    break;
  case Case::raw_partial:
    f.memory.hidden.push_back({Address(f.mapped_values), 32});
    f.NoDefault();
    break;
  case Case::negative_rank:
    f.memory.Put(f.carrier, 0xB70, std::int32_t{-1});
    f.Property(f.default_pc, f.default_keys, f.default_values, {}, {});
    f.memory.NoRead(f.definition, 0x3E4, 4);
    f.memory.NoReadVirtual(Fixture::kDefault, 8);
    f.memory.NoReadVirtual(Fixture::kDefault + 0x68, 8);
    f.NoMappedTable();
    break;
  }
  const auto snapshot = f.Observe();
  const auto &leaf = *snapshot.character_observations->front().current_person_state->carrier_1c8_b70_direct;
  const bool partial = spec.kind == Case::guard_zero || spec.kind == Case::raw_partial;
  Require(leaf.ready == !partial && (partial ? !leaf.source_occurrence_count : leaf.reason.empty()),
          "bounded branch readiness/partial occurrence differs");
  switch (spec.kind) {
  case Case::absent:
  case Case::wrong_magic:
    Require(leaf.selection == "none" && leaf.source_occurrence_count == 0U &&
                !leaf.rank_i32 && !leaf.row_count_i32 && !leaf.properties,
            "native admission skip did not retain known zero");
    break;
  case Case::mapped_empty:
    Require(leaf.selection == "mapped_row" && leaf.source_occurrence_count == 0U &&
                leaf.selected_pc_count_i32 == 0 && leaf.properties &&
                leaf.properties->keys_u16->empty() && leaf.properties->values_q64->empty(),
            "mapped empty source differs");
    break;
  case Case::mapped_positive:
  case Case::raw_partial:
    Require(leaf.selection == "mapped_row" && leaf.selected_pc_count_i32 == 4 &&
                leaf.properties && *leaf.properties->keys_u16 ==
                    std::vector<std::uint16_t>{0x22A, 0xFFFF, 0x22A, 0},
            "mapped physical duplicate/sentinel/zero keys differ");
    if (partial) {
      Require(!leaf.properties->values_q64 && leaf.reason == "selected_pc_values_unread" &&
                  f.memory.hidden.front().attempts == 2,
              "failed values copy lost physical keys or double-sample semantics");
    } else {
      Require(leaf.source_occurrence_count == 1U && *leaf.properties->values_q64 ==
                  std::vector<std::int64_t>{-100'000,
                      (std::numeric_limits<std::int64_t>::min)(), 0,
                      (std::numeric_limits<std::int64_t>::max)()},
              "mapped signed source Q64 payload changed");
    }
    break;
  case Case::initialized_default:
  case Case::guard_zero:
    Require(leaf.selection == "static_default_5d71200" &&
                leaf.rank_i32 == 2 && leaf.row_count_i32 == 2 &&
                leaf.default_guard_raw == (partial ? 0 : -2) &&
                leaf.selected_pc_identity == Fixture::kDefault &&
                leaf.selected_pc_count_i32 == 1 && leaf.properties &&
                *leaf.properties->keys_u16 == std::vector<std::uint16_t>{0x22A} &&
                *leaf.properties->values_q64 == std::vector<std::int64_t>{-250'000},
            "actual inline fallback physical source differs");
    Require(partial ? leaf.reason == "fallback_31937a0_default_initialization_unobserved"
                    : leaf.source_occurrence_count == 1U,
            "lazy-default guard qualification differs");
    break;
  case Case::negative_rank:
    Require(leaf.rank_i32 == -1 && !leaf.row_count_i32 &&
                leaf.selection == "static_default_5d71200" &&
                leaf.selected_pc_count_i32 == 0 && leaf.source_occurrence_count == 0U &&
                leaf.properties && leaf.properties->keys_u16->empty() &&
                leaf.properties->values_q64->empty(),
            "negative rank read undemanded definition count or lost actual empty PC");
    break;
  }
  const auto request_id = std::string("person-carrier-direct12004-mcp-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, Fixture::kStep, sequence, snapshot);
  Require(packet.find("command_result") != std::string::npos &&
              packet.find(request_id) != std::string::npos &&
              packet.find(Fixture::kStep) != std::string::npos &&
              packet.find("\"carrier_1c8_b70_direct\":{") != std::string::npos,
          "shared production formatter did not publish a complete command_result");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot write original production command_result packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: person_carrier_direct12004_mcp_fixture output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create packet output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kCases) Produce(directory, spec, ++sequence);
  std::cout << "person carrier direct12004: eight production whole-command packets\n";
  return 0;
}
