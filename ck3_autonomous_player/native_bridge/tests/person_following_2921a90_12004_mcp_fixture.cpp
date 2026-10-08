// SOURCE_NOTRUN: ten new whole-command packets through the genuine actual4
// Battle factory, production terminal double sample and shared formatter.
// Source was sealed first in battle-person-following-2921a90-12004.md.
// No old fixture/test or reader stub is included, and no native getter runs.
#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"
#include "xar_bridge/ck3_12004_battle.hpp"
#include "xar_bridge/ck3_12004_person_following_2921a90.hpp"

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
    std::cerr << "person-following2921a90: " << message << '\n';
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
  std::uintptr_t registry_slot_field = 0;
  std::size_t registry_slot_reads = 0;

  void *Allocate(std::size_t size, std::uintptr_t virtual_address = 0) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *const pointer = bytes.get();
    regions.push_back({std::move(bytes),
        virtual_address == 0 ? Address(pointer) : virtual_address, size});
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
    if (begin == memory.registry_slot_field && size == sizeof(void *))
      ++memory.registry_slot_reads;
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
  static constexpr std::uintptr_t kRegistrySlot =
      kModule + native4::kPersonFollowing2921a90RegistryRva;
  static constexpr std::uintptr_t kFallbackSlot =
      kModule + native4::kPersonFollowing2921a90FallbackRva;
  static constexpr std::uint32_t kRequestedId = 0x03000001U;
  static constexpr std::uint32_t kFallbackId = 0x05000002U;
  static constexpr std::uint32_t kMagic = 0x446F6D69U;
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
  void *old_definition = memory.Allocate(0x40);
  void *registry_slot = memory.Allocate(8, kRegistrySlot);
  void *fallback_slot = memory.Allocate(8, kFallbackSlot);
  void *registry = memory.Allocate(0x30);
  void *registry_rows = memory.Allocate(2 * 0x10);
  void *mapped_object = memory.Allocate(0x70);
  void *fallback_object = memory.Allocate(0x70);
  void *definition = memory.Allocate(0xBC0);
  void *mapped_list = memory.Allocate(4 * 8);
  void *fallback_list = memory.Allocate(8);
  void *a = memory.Allocate(0x17F0);
  void *b = memory.Allocate(0x17F0);
  void *c = memory.Allocate(0x17F0);
  void *a_keys = memory.Allocate(8);
  void *a_values = memory.Allocate(32);
  void *c_keys = memory.Allocate(2);
  void *c_values = memory.Allocate(8);
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
    // Keep the preceding carrier leaf source-known zero, with no cold default.
    memory.Put(carrier, 0x20, old_definition);
    memory.Put(old_definition, 0x38, std::uint32_t{0});
    memory.NoRead(carrier, 0xB70, 4);
    memory.Put(carrier, 0xB68, kRequestedId);
    memory.Put(registry_slot, 0, registry);
    memory.Put(fallback_slot, 0, fallback_object);
    memory.Put(registry, 0x20, registry_rows);
    memory.Put(registry, 0x2C, std::uint32_t{2});
    memory.Put(registry_rows, 0x10 + 8, mapped_object);
    memory.Put(mapped_object, 8, kRequestedId);
    memory.Put(mapped_object, 0xC, kMagic);
    memory.Put(mapped_object, 0x30, definition);
    memory.Put(mapped_object, 0x60, mapped_list);
    memory.Put(mapped_object, 0x6C, std::int32_t{4});
    memory.Put(fallback_object, 8, kFallbackId);
    memory.Put(fallback_object, 0xC, kMagic);
    memory.Put(fallback_object, 0x30, definition);
    memory.Put(fallback_object, 0x60, fallback_list);
    memory.Put(fallback_object, 0x6C, std::int32_t{1});
    memory.Put(mapped_list, 0, a);
    memory.Put(mapped_list, 8, b);
    memory.Put(mapped_list, 16, a);
    memory.Put(mapped_list, 24, c);
    memory.Put(fallback_list, 0, c);
    memory.Put(definition, 0xB8C, std::int32_t{0});
    memory.Put(definition, 0xBBC, std::int32_t{0});
    Property(a, a_keys, a_values, {0x22A, 0xFFFF, 0x22A, 0},
             {-100'000, (std::numeric_limits<std::int64_t>::min)(), 0,
              (std::numeric_limits<std::int64_t>::max)()});
    Property(b, nullptr, nullptr, {}, {});
    Property(c, c_keys, c_values, {0x22A}, {-250'000});
    memory.registry_slot_field = kRegistrySlot;
    memory.NoRead(model, 0x10, 0x10);
    for (const auto object : {a, b, c}) memory.NoRead(object, 0x1778 + 0x74, 4);
    memory.NoRead(b, 0x1778, 8);
    memory.NoRead(b, 0x1778 + 0x68, 8);
    // Conditional rows/classifier are unclosed; only the proved count tests read.
    memory.NoRead(definition, 0xB80, 8);
    memory.NoRead(definition, 0xBB0, 8);

    bindings = native4::BindBattleImage(
        kModule, native4::kExecutableSha256, native4::BattleImageDependencies{});
    bindings.game_state_slot = &game_state;
    bindings.jomini_state_slot = &jomini_state;
    bindings.character_storage_slot = &character_storage;
    Require(bindings.enabled && bindings.current_person_carrier_direct.enabled &&
                bindings.current_person_carrier_direct.module_base == kModule,
            "genuine actual4 factory/direct binding unavailable");
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
                !bindings.current_person_traits.enabled && !bindings.full_backing_inputs_enabled,
            "actual4 fixture enabled historical .3 person/backing leaves");
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
  void Property(void *object, void *keys, void *values,
                const std::vector<std::uint16_t> &raw_keys,
                const std::vector<std::int64_t> &raw_values) {
    Require(raw_keys.size() == raw_values.size(), "raw fixture pair lengths differ");
    const auto pc = At(object, 0x1778);
    memory.Put(pc, 0xC, static_cast<std::int32_t>(raw_keys.size()));
    if (raw_keys.empty()) return;
    memory.Put(pc, 0, keys);
    memory.Put(pc, 0x68, values);
    for (std::size_t i = 0; i < raw_keys.size(); ++i) {
      memory.Put(keys, i * 2, raw_keys[i]);
      memory.Put(values, i * 8, raw_values[i]);
    }
  }
  void NoMappedObject() {
    memory.NoRead(mapped_object, 0xC, 4);
    memory.NoRead(mapped_object, 0x30, 8);
    memory.NoRead(mapped_object, 0x60, 16);
    memory.NoRead(mapped_list, 0, 32);
  }
  void NoSelectedPayload(void *object) {
    memory.NoRead(object, 0x30, 8);
    memory.NoRead(object, 0x60, 16);
    memory.NoRead(definition, 0xB8C, 4);
    memory.NoRead(definition, 0xBBC, 4);
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
                !output.pending_death_queue && memory.registry_slot_reads == 2 &&
                memory.UndemandedAttempts() == 0 && memory.ByteSnapshot() == bytes,
            "production double sample, frame, skipped operands or read-only bytes differ");
    Require(output.character_observations && output.character_observations->size() == 1,
            "production query omitted or substituted requested enemy");
    const auto &observation = output.character_observations->front();
    Require(observation.character_id == kEnemy && observation.character_id != kPlayer &&
                scope.played_character_id == kPlayer && observation.alive == true &&
                observation.status == game::BattleTerminalCustodyStatusV1::none &&
                observation.actual_jailer_character_id == -1 && observation.current_person_state,
            "actual requested enemy, player or custody differs");
    const auto &person = *observation.current_person_state;
    Require(person.carrier_1c8_b70_direct && person.carrier_1c8_b70_direct->ready &&
                person.carrier_1c8_b70_direct->source_occurrence_count == 0U &&
                person.following_2921a90 &&
                !person.raw_numeric_inputs && !person.current_context_task_position_inputs &&
                !person.context_branch_inputs && !person.current_prior_context_inputs &&
                !person.current_stored_context_state && !person.current_context_source_inputs &&
                !person.effective_prowess.available && !person.effective_prowess.points &&
                person.injury_traits.status == game::BattleCurrentPersonInjuryTraitsStatusV1::unavailable &&
                person.death_record.status == game::BattleCurrentPersonDeathRecordStatusV1::unavailable,
            "new leaf lost preceding known-zero carrier or promoted historical .3 state");
    const auto &leaf = *person.following_2921a90;
    Require(leaf.character_id == kEnemyUnsigned && leaf.character_identity == Address(enemy) &&
                leaf.selected_model_identity == Address(model) &&
                leaf.destination_pc_identity == Address(model) + 0x10 &&
                leaf.build_version == native4::kGameVersion &&
                leaf.executable_sha256 == native4::kExecutableSha256,
            "same-query actual enemy/model or exact4 provenance differs");
    output.snapshot_revision = kRevision;
    return output;
  }
};

enum class Case { mapped, empty_list, absent_carrier, generation_mismatch,
                  wrong_magic, sentinel, row_partial, b8c, bbc, negative_count };
struct Spec { const char *name; Case kind; };
constexpr Spec kCases[] = {
    {"mapped-ordered-pcs", Case::mapped},
    {"empty-direct-list", Case::empty_list},
    {"absent-carrier-fallback", Case::absent_carrier},
    {"generation-mismatch-fallback", Case::generation_mismatch},
    {"wrong-selected-magic", Case::wrong_magic},
    {"fallback-id-sentinel", Case::sentinel},
    {"row-values-partial", Case::row_partial},
    {"conditional-b8c-demanded", Case::b8c},
    {"conditional-bbc-demanded", Case::bbc},
    {"negative-direct-count", Case::negative_count},
};

void CheckMappedRows(const native4::PersonFollowing2921a90DTO &leaf,
                     const Fixture &f, bool partial) {
  Require(leaf.direct_rows.size() == 4U && leaf.direct_count_i32 == 4,
          "four physical list occurrences changed");
  const auto &rows = leaf.direct_rows;
  for (std::size_t i = 0; i < rows.size(); ++i) {
    Require(rows[i].native_index == static_cast<std::uint32_t>(i) &&
                rows[i].weight_q100000 == 100'000,
            "physical row ordinal or source weight changed");
  }
  Require(rows[0].object_identity == Address(f.a) &&
              rows[2].object_identity == rows[0].object_identity &&
              rows[0].source_pc_identity == Address(f.a) + 0x1778 &&
              rows[1].object_identity == Address(f.b) && rows[1].ready &&
              rows[1].pc_count_i32 == 0 && rows[1].properties &&
              rows[1].properties->keys_u16->empty() && rows[1].properties->values_q64->empty() &&
              rows[3].object_identity == Address(f.c) && rows[3].ready &&
              *rows[3].properties->keys_u16 == std::vector<std::uint16_t>{0x22A} &&
              *rows[3].properties->values_q64 == std::vector<std::int64_t>{-250'000},
          "duplicate/empty occurrence or independently complete later row lost");
  for (const std::size_t index : {std::size_t{0}, std::size_t{2}}) {
    const auto &row = rows[index];
    Require(row.pc_count_i32 == 4 && row.properties &&
                *row.properties->keys_u16 == std::vector<std::uint16_t>{0x22A, 0xFFFF, 0x22A, 0},
            "raw signed-PC repeated/sentinel/zero keys changed");
    if (partial) Require(!row.ready && row.reason == "pc_values_unread" &&
                             !row.properties->values_q64,
                         "failed values copy discarded keys or became ready");
    else Require(row.ready && row.reason.empty() && *row.properties->values_q64 ==
                     std::vector<std::int64_t>{-100'000,
                         (std::numeric_limits<std::int64_t>::min)(), 0,
                         (std::numeric_limits<std::int64_t>::max)()},
                 "full signed Q64 source extrema/order changed");
  }
}

void Produce(const std::filesystem::path &directory, const Spec &spec,
             std::uint64_t sequence) {
  Fixture f;
  switch (spec.kind) {
  case Case::mapped: break;
  case Case::empty_list:
    f.memory.Put(f.mapped_object, 0x60, static_cast<void *>(nullptr));
    f.memory.Put(f.mapped_object, 0x6C, std::int32_t{0});
    f.memory.NoRead(f.mapped_list, 0, 32);
    break;
  case Case::absent_carrier:
    f.memory.Put(f.enemy, 0x1C8, static_cast<void *>(nullptr));
    f.memory.NoRead(f.carrier, 0, 0xB74);
    f.memory.NoRead(f.registry, 0x20, 8);
    f.NoMappedObject();
    break;
  case Case::generation_mismatch:
    f.memory.Put(f.mapped_object, 8, std::uint32_t{0x04000001});
    f.NoMappedObject();
    break;
  case Case::wrong_magic:
  case Case::sentinel:
    f.memory.Put(f.registry_slot, 0, static_cast<void *>(nullptr));
    f.memory.NoRead(f.registry, 0, 0x30);
    f.NoSelectedPayload(f.fallback_object);
    if (spec.kind == Case::wrong_magic) {
      f.memory.Put(f.fallback_object, 0xC, std::uint32_t{0});
      f.memory.NoRead(f.fallback_object, 8, 4);
    } else f.memory.Put(f.fallback_object, 8, std::uint32_t{0xFFFFFFFF});
    break;
  case Case::row_partial:
    f.memory.hidden.push_back({Address(f.a_values), 32});
    break;
  case Case::b8c:
    f.memory.Put(f.definition, 0xB8C, std::int32_t{1});
    f.memory.NoRead(f.definition, 0xBBC, 4);
    break;
  case Case::bbc:
    f.memory.Put(f.definition, 0xBBC, std::int32_t{-1});
    break;
  case Case::negative_count:
    f.memory.Put(f.mapped_object, 0x6C, std::int32_t{-1});
    f.memory.NoRead(f.mapped_list, 0, 32);
    break;
  }
  const auto snapshot = f.Observe();
  const auto &leaf = *snapshot.character_observations->front().current_person_state->following_2921a90;
  const bool conditional_gap = spec.kind == Case::b8c || spec.kind == Case::bbc;
  const bool direct_gap = spec.kind == Case::row_partial || spec.kind == Case::negative_count;
  Require(leaf.ready == !(conditional_gap || direct_gap) &&
              leaf.direct_ready == !direct_gap && leaf.conditional_ready == !conditional_gap,
          "whole/direct/conditional readiness differs");
  if (spec.kind == Case::wrong_magic || spec.kind == Case::sentinel) {
    Require(leaf.admitted == false && leaf.resolution_selection == "fallback" &&
                !leaf.direct_count_i32 && !leaf.direct_array_identity && leaf.direct_rows.empty() &&
                !leaf.conditional_definition_identity && !leaf.conditional_b8c_count_i32 &&
                !leaf.conditional_bbc_count_i32 && leaf.conditional_occurrence_count == 0U,
            "observed gate failure demanded payload or lost known zero");
    Require(spec.kind == Case::wrong_magic ? !leaf.selected_full_id_u32
                                         : leaf.selected_full_id_u32 == 0xFFFFFFFFU,
            "selected full-ID sentinel demand differs");
  } else {
    Require(leaf.admitted == true, "actual selected linked object was not admitted");
    if (conditional_gap) {
      Require(leaf.conditional_reason == "conditional_modifier_2a38030_2872300_unobserved" &&
                  leaf.reason == leaf.conditional_reason && !leaf.conditional_occurrence_count &&
                  (spec.kind == Case::b8c
                      ? leaf.conditional_b8c_count_i32 == 1 && !leaf.conditional_bbc_count_i32
                      : leaf.conditional_b8c_count_i32 == 0 && leaf.conditional_bbc_count_i32 == -1),
              "nonzero conditional demand was substituted or BBC read too early");
    } else Require(leaf.conditional_b8c_count_i32 == 0 &&
                       leaf.conditional_bbc_count_i32 == 0 &&
                       leaf.conditional_occurrence_count == 0U,
                   "observed empty conditional family lost zero occurrence");
    if (spec.kind == Case::absent_carrier || spec.kind == Case::generation_mismatch) {
      Require(leaf.resolution_selection == "fallback" && leaf.selected_full_id_u32 == Fixture::kFallbackId &&
                  leaf.direct_count_i32 == 1 && leaf.direct_rows.size() == 1U &&
                  leaf.direct_rows[0].ready && leaf.direct_rows[0].object_identity == Address(f.c),
              "actual fallback source or full generation equality differs");
      Require(spec.kind == Case::absent_carrier
                  ? leaf.carrier_present == false && leaf.requested_full_id_u32 == 0xFFFFFFFFU &&
                        !leaf.registry_slots_identity
                  : leaf.requested_full_id_u32 == Fixture::kRequestedId,
              "null carrier skipped helper or requested full generation was changed");
    } else if (spec.kind == Case::empty_list) {
      Require(leaf.direct_count_i32 == 0 && leaf.direct_array_identity == std::uintptr_t{0} &&
                  leaf.direct_rows.empty(), "empty physical list was not known zero");
    } else if (spec.kind == Case::negative_count) {
      Require(leaf.direct_count_i32 == -1 && leaf.direct_array_identity == Address(f.mapped_list) &&
                  leaf.direct_rows.empty() && leaf.direct_reason == "direct_count_negative" &&
                  leaf.reason == leaf.direct_reason,
              "negative direct count was silently treated as empty");
    } else {
      CheckMappedRows(leaf, f, spec.kind == Case::row_partial);
      if (spec.kind == Case::row_partial)
        Require(leaf.direct_reason == "direct_rows_partial" && leaf.reason == leaf.direct_reason &&
                    f.memory.hidden.front().attempts == 4,
                "partial physical repeated rows lost independent later occurrences");
    }
  }
  const auto request_id = std::string("person-following2921a90-mcp-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, Fixture::kStep, sequence, snapshot);
  Require(packet.find("command_result") != std::string::npos &&
              packet.find(request_id) != std::string::npos &&
              packet.find(Fixture::kStep) != std::string::npos &&
              packet.find("\"following_2921a90\":{") != std::string::npos,
          "shared real formatter did not emit the original complete packet");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot write original production packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_following_2921a90_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create whole-packet output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kCases) Produce(directory, spec, ++sequence);
  std::cout << "person following2921a90: ten production whole-command packets\n";
  return 0;
}
