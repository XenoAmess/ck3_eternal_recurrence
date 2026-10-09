// AUTHORED_NOTRUN: fresh guarded-memory worlds through the actual4 Battle
// factory, CurrentPersonSample, terminal double sample and production formatter.
// No reader result/DTO is supplied by this fixture and no native getter runs.
// Character+1D0 is also the production DeathData pointer. Its nonnull header
// branch is one genuine dead-owner observation; the other13 require alive=true.
// CurrentPersonSample is independently published before the production alive
// read (ck3_12002_battle.cpp CharacterObservationSample); it remains present.
#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"
#include "xar_bridge/ck3_12004_battle.hpp"
#include "xar_bridge/ck3_12004_person_following_2922680.hpp"

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
    std::cerr << "person-following2922680: " << message << '\n';
    std::exit(1);
  }
}
std::uintptr_t Address(const void *pointer) {
  return reinterpret_cast<std::uintptr_t>(pointer);
}
void *Offset(void *pointer, std::size_t offset) {
  return static_cast<std::byte *>(pointer) + offset;
}

class Memory {
  struct Block {
    std::unique_ptr<std::byte[]> data;
    std::size_t size;
    std::uintptr_t observed_address;
  };
  struct Refusal {
    std::uintptr_t address;
    std::size_t size;
    bool expected_unrequested;
  };
  std::vector<Block> blocks_;
  std::vector<Refusal> refusals_;

public:
  std::size_t unexpected_reads = 0;
  void *Allocate(std::size_t size, std::uintptr_t observed_address = 0) {
    auto data = std::make_unique<std::byte[]>(size);
    void *const result = data.get();
    blocks_.push_back({std::move(data), size,
        observed_address == 0 ? Address(result) : observed_address});
    return result;
  }
  template <class T> void Put(void *base, std::size_t offset, T value) {
    for (const auto &block : blocks_) {
      if (Address(base) < Address(block.data.get())) continue;
      const auto local = Address(base) - Address(block.data.get());
      if (local <= block.size && offset <= block.size - local &&
          sizeof(T) <= block.size - local - offset) {
        std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(T));
        return;
      }
    }
    Require(false, "fake-memory setup write outside allocation");
  }
  void Refuse(std::uintptr_t address, std::size_t size, bool undemanded = true) {
    refusals_.push_back({address, size, undemanded});
  }
  void Refuse(void *base, std::size_t offset, std::size_t size,
              bool undemanded = true) {
    Refuse(Address(base) + offset, size, undemanded);
  }
  static bool Read(void *context, const void *source, void *destination,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto address = Address(source);
    for (const auto &refusal : memory.refusals_) {
      if (address < refusal.address + refusal.size &&
          refusal.address < address + size) {
        if (refusal.expected_unrequested) ++memory.unexpected_reads;
        return false;
      }
    }
    for (const auto &block : memory.blocks_) {
      if (address >= block.observed_address &&
          address - block.observed_address <= block.size &&
          size <= block.size - (address - block.observed_address)) {
        std::memcpy(destination,
            block.data.get() + (address - block.observed_address), size);
        return true;
      }
    }
    return false;
  }
  std::vector<std::vector<std::byte>> Bytes() const {
    std::vector<std::vector<std::byte>> result;
    for (const auto &block : blocks_)
      result.emplace_back(block.data.get(), block.data.get() + block.size);
    return result;
  }
};

struct World {
  static constexpr std::uintptr_t kModule = 0x140000000;
  static constexpr std::uintptr_t kStaticHeader = kModule + 0x5D67DE0;
  static constexpr std::uintptr_t kRiteRegistry = kModule + 0x5D1E2F8;
  static constexpr std::uintptr_t kRiteFallback = kModule + 0x5C67670;
  static constexpr std::uintptr_t kContextRegistry = kModule + 0x5D1E300;
  static constexpr std::uintptr_t kContextFallback = kModule + 0x5D1E2E0;
  static constexpr std::uintptr_t kRowRegistry = kModule + 0x5D1ED98;
  static constexpr std::uintptr_t kRowFallback = kModule + 0x5D1ED90;
  static constexpr std::uintptr_t kGameDataSlot = kModule + 0x5C68C50;
  static constexpr std::uintptr_t kSourceRegistry = kModule + 0x5D1ED80;
  static constexpr std::uintptr_t kSourceFallback = kModule + 0x5D1ED78;
  static constexpr std::uintptr_t kValueRegistry = kModule + 0x5D1FF70;
  static constexpr std::uintptr_t kValueFallback = kModule + 0x5D1FF78;
  static constexpr std::int32_t kPlayer = 29829;
  static constexpr std::int32_t kSubject = 0x04000003;
  static constexpr std::int32_t kDate = 53'236'632;
  static constexpr std::uint64_t kRevision = 49;
  static constexpr std::uint32_t kFirstId = 0x03000001;
  static constexpr std::uint32_t kSecondId = 0x03000002;
  static constexpr std::uint32_t kThirdId = 0x03000003;
  static constexpr std::string_view kStep =
      "query-battle-terminal-transition-v1-none:characters:67108867";

  Memory memory;
  void *game_state = memory.Allocate(0xA8);
  void *jomini = memory.Allocate(0x28);
  void *character_storage = memory.Allocate(0x30);
  void *character_slots = memory.Allocate((kPlayer + 1U) * 0x10U);
  void *player = memory.Allocate(0x1D8);
  void *subject = memory.Allocate(0x1D8);
  void *scratch = memory.Allocate(0x290);
  void *model = memory.Allocate(0x20);
  void *context = memory.Allocate(0x1A8);
  void *gate = memory.Allocate(8);
  void *list = memory.Allocate(4 * 4);
  void *static_header = memory.Allocate(0x10, kStaticHeader);
  void *old_carrier = memory.Allocate(0xB74);
  void *old_definition = memory.Allocate(0x40);
  void *rite_registry_slot = memory.Allocate(8, kRiteRegistry);
  void *rite_fallback_slot = memory.Allocate(8, kRiteFallback);
  void *context_registry_slot = memory.Allocate(8, kContextRegistry);
  void *context_fallback_slot = memory.Allocate(8, kContextFallback);
  void *row_registry_slot = memory.Allocate(8, kRowRegistry);
  void *row_fallback_slot = memory.Allocate(8, kRowFallback);
  void *rite = memory.Allocate(0x7B0);
  void *rite_context = memory.Allocate(0xA0);
  void *row_registry = memory.Allocate(0x30);
  void *row_slots = memory.Allocate(4 * 0x10);
  void *a = memory.Allocate(0xC7D0);
  void *b = memory.Allocate(0xC7D0);
  void *c = memory.Allocate(0xC7D0);
  void *fallback = memory.Allocate(0xC7D0);
  void *game_data_slot = memory.Allocate(8, kGameDataSlot);
  void *game_data = memory.Allocate(0x10);
  void *source_registry_slot = memory.Allocate(8, kSourceRegistry);
  void *source_fallback_slot = memory.Allocate(8, kSourceFallback);
  void *source_registry = memory.Allocate(0x30);
  void *source_slots = memory.Allocate(2 * 0x10);
  void *source_ids = memory.Allocate(4);
  void *source = memory.Allocate(0x400);
  void *hash_slot = memory.Allocate(12);
  void *value_registry_slot = memory.Allocate(8, kValueRegistry);
  void *value_fallback_slot = memory.Allocate(8, kValueFallback);
  void *value_registry = memory.Allocate(0x30);
  void *value_slots = memory.Allocate(2 * 0x10);
  void *getter_result = memory.Allocate(0x40);
  void *match_definition = memory.Allocate(0xC);
  void *item_container = memory.Allocate(0x100);
  void *item_array = memory.Allocate(3 * 8);
  void *item_a = memory.Allocate(0x408);
  void *item_b = memory.Allocate(0x408);
  void *nested_array_a = memory.Allocate(2 * 8);
  void *nested_array_b = memory.Allocate(8);
  void *nested_a = memory.Allocate(0x3A0);
  void *nested_b = memory.Allocate(0x3A0);
  void *nested_unmatched = memory.Allocate(0x3A0);
  void *primary_keys = memory.Allocate(4 * 2);
  void *primary_values = memory.Allocate(4 * 8);
  void *nested_a_keys = memory.Allocate(2);
  void *nested_a_values = memory.Allocate(8);
  void *nested_b_keys = memory.Allocate(2);
  void *nested_b_values = memory.Allocate(8);
  void *descriptors = memory.Allocate(0x30);
  void *membership_ids = memory.Allocate(8);
  void *member_key = memory.Allocate(8);
  void *other_key = memory.Allocate(8);
  native4::BattleBindings bindings;
  game::Snapshot scope;

  World() {
    memory.Put(game_state, 8, kDate);
    memory.Put(jomini, 0x20, std::uint8_t{1});
    memory.Put(character_storage, 0x20, character_slots);
    memory.Put(character_storage, 0x2C, kPlayer + 1);
    StoreCharacter(kPlayer, player);
    StoreCharacter(kSubject, subject);
    memory.Put(player, native4::kCharacterFullIdOffset, kPlayer);
    memory.Put(subject, native4::kCharacterFullIdOffset, kSubject);
    memory.Put(subject, native4::kCharacterDeathDataOffset,
               static_cast<void *>(nullptr));
    memory.Put(subject, 0x1B0, scratch);
    memory.Put(subject, 0x1C0, context);
    memory.Put(subject, 0x1C8, old_carrier);
    memory.Put(subject, 0x1D0, static_cast<void *>(nullptr));
    memory.Put(scratch, 0x258, model);
    memory.Put(model, 8, subject);
    memory.Put(old_carrier, 0x20, old_definition);
    memory.Put(old_definition, 0x38, std::uint32_t{0});
    memory.Put(context, 0x198, list);
    memory.Put(context, 0x198 + 0xC, std::int32_t{4});
    memory.Put(static_header, 0xC, std::int32_t{0});
    for (const auto &[index, id] :
         {std::pair<std::size_t, std::uint32_t>{0, kFirstId},
          {1, kSecondId}, {2, kFirstId}, {3, kThirdId}})
      memory.Put(list, index * 4, id);
    // Genuine fallback resolution of the two Rite roles and their context.
    memory.Put(rite_registry_slot, 0, static_cast<void *>(nullptr));
    memory.Put(context_registry_slot, 0, static_cast<void *>(nullptr));
    memory.Put(rite_fallback_slot, 0, rite);
    memory.Put(context_fallback_slot, 0, rite_context);
    memory.Put(rite, 8, std::uint32_t{0x05000005});
    memory.Put(rite_context, 8, std::uint32_t{0x05000006});
    memory.Put(row_registry_slot, 0, row_registry);
    memory.Put(row_fallback_slot, 0, fallback);
    memory.Put(row_registry, 0x20, row_slots);
    memory.Put(row_registry, 0x2C, std::uint32_t{4});
    const std::vector<void *> rows{a, b, c};
    const std::vector<std::uint32_t> ids{kFirstId, kSecondId, kThirdId};
    for (std::size_t index = 0; index < rows.size(); ++index) {
      memory.Put(row_slots, (index + 1) * 0x10 + 8, rows[index]);
      memory.Put(rows[index], 8, ids[index]);
    }
    memory.Put(fallback, 8, std::uint32_t{0x05000004});
    for (const auto row : {a, b, c, fallback}) {
      memory.Put(row, 0xC7CE, std::int16_t{1077});
      memory.Put(row, 0xC7C8, kDate - 1);
      memory.Put(row, 0x134, std::int32_t{0});
    }
    memory.Put(game_data_slot, 0, game_data);
    memory.Put(game_data, 8, kDate);
    memory.Refuse(model, 0x10, 0x10);

    bindings = native4::BindBattleImage(
        kModule, native4::kExecutableSha256, native4::BattleImageDependencies{});
    Require(bindings.enabled && bindings.current_person_carrier_direct.enabled,
            "actual4 production factory did not supply same-query bindings");
    bindings.game_state_slot = &game_state;
    bindings.jomini_state_slot = &jomini;
    bindings.character_storage_slot = &character_storage;
    bindings.current_person_carrier_direct.read_memory = &Memory::Read;
    bindings.current_person_carrier_direct.read_context = &memory;
    scope.date_raw = kDate;
    scope.paused = true;
    scope.map_ready = true;
    scope.has_played_character = true;
    scope.played_character_id = kPlayer;
    scope.played_character_alive = true;
  }
  void StoreCharacter(std::int32_t id, void *character) {
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    memory.Put(character_slots, static_cast<std::size_t>(index) * 0x10 + 8,
               character);
  }
  void NoRootDemand() {
    for (const auto slot : {kRiteRegistry, kRiteFallback, kContextRegistry,
                           kContextFallback, kRowRegistry, kRowFallback})
      memory.Refuse(slot, 8);
  }
  void ExpiredInputsOnly() {
    for (const auto row : {a, b, c, fallback})
      memory.Refuse(row, 0x128, 0x10);
  }
  void ZeroSourceInputs() {
    for (const auto row : {a, b, c, fallback}) {
      memory.Put(row, 0xC7CE, std::int16_t{1});
      memory.Refuse(row, 0xC7C8, 4);
      memory.Refuse(row, 0x128, 8);
    }
    memory.Refuse(kGameDataSlot, 8);
  }
  void Property(void *pc, void *keys, void *values,
                const std::vector<std::uint16_t> &raw_keys,
                const std::vector<std::int64_t> &raw_values) {
    Require(raw_keys.size() == raw_values.size(), "fixture PC pair lengths differ");
    memory.Put(pc, 0xC, static_cast<std::int32_t>(raw_keys.size()));
    if (raw_keys.empty()) return;
    memory.Put(pc, 0, keys);
    memory.Put(pc, 0x68, values);
    for (std::size_t index = 0; index < raw_keys.size(); ++index) {
      memory.Put(keys, index * 2, raw_keys[index]);
      memory.Put(values, index * 8, raw_values[index]);
    }
  }
  void NumericInputs(bool membership_present, bool membership_matches,
                     bool partial_primary) {
    constexpr std::uint32_t source_id = 0x06000001;
    constexpr std::uint32_t result_id = 0x07000001;
    constexpr std::uint32_t match_id = 0xAABBCCDD;
    memory.Put(context, 0x198 + 0xC, std::int32_t{1});
    memory.Put(a, 0xC7CE, std::int16_t{1});
    memory.Put(a, 0x128, source_ids);
    memory.Put(a, 0x134, std::int32_t{1});
    memory.Put(source_ids, 0, source_id);
    memory.Put(source_registry_slot, 0, source_registry);
    memory.Put(source_fallback_slot, 0, source);
    memory.Put(source_registry, 0x20, source_slots);
    memory.Put(source_registry, 0x2C, std::uint32_t{2});
    memory.Put(source_slots, 0x10 + 8, source);
    memory.Put(source, 8, source_id);
    memory.Put(source, 0xC, std::uint32_t{0x53695352});
    // A single mask-zero slot with the actual character's exact key avoids
    // constructing or assuming any unobserved collision/overflow history.
    memory.Put(source, 0xF0, hash_slot);
    memory.Put(source, 0xFC, std::int32_t{0});
    memory.Put(source, 0x100, std::uint8_t{0});
    memory.Put(hash_slot, 0, std::uint8_t{1});
    memory.Put(hash_slot, 4, static_cast<std::uint32_t>(kSubject));
    memory.Put(hash_slot, 8, result_id);
    memory.Put(value_registry_slot, 0, value_registry);
    memory.Put(value_fallback_slot, 0, getter_result);
    memory.Put(value_registry, 0x20, value_slots);
    memory.Put(value_registry, 0x2C, std::uint32_t{2});
    memory.Put(value_slots, 0x10 + 8, getter_result);
    memory.Put(getter_result, 8, result_id);
    memory.Put(getter_result, 0xC, std::uint32_t{0x53695047});
    memory.Put(getter_result, 0x30, match_definition);
    memory.Put(match_definition, 8, match_id);
    memory.Put(source, 0x3F8, item_container);
    memory.Put(item_container, 0xF0, item_array);
    memory.Put(item_container, 0xFC, std::int32_t{3});
    memory.Put(item_array, 0, item_a);
    memory.Put(item_array, 8, item_b);
    memory.Put(item_array, 16, item_a);
    memory.Put(item_a, 0x3F0, std::uint8_t{1});
    memory.Put(item_b, 0x3F0, std::uint8_t{1});
    Property(Offset(item_a, 0x40), primary_keys, primary_values,
             {0x22A, 0xFFFF, 0x22A, 0},
             {-100'000, (std::numeric_limits<std::int64_t>::min)(), 0,
              (std::numeric_limits<std::int64_t>::max)()});
    Property(Offset(item_b, 0x40), nullptr, nullptr, {}, {});
    memory.Refuse(item_b, 0x40, 8);
    memory.Refuse(item_b, 0x40 + 0x68, 8);
    memory.Put(item_a, 0x3F8, nested_array_a);
    memory.Put(item_a, 0x404, std::int32_t{2});
    memory.Put(item_b, 0x3F8, nested_array_b);
    memory.Put(item_b, 0x404, std::int32_t{1});
    memory.Put(nested_array_a, 0, nested_a);
    memory.Put(nested_array_a, 8, nested_unmatched);
    memory.Put(nested_array_b, 0, nested_b);
    memory.Put(nested_a, 8, match_id);
    memory.Put(nested_b, 8, match_id);
    memory.Put(nested_unmatched, 8, match_id - 1U);
    Property(Offset(nested_a, 0x10), nested_a_keys, nested_a_values,
             {0x111}, {-250'000});
    Property(Offset(nested_b, 0x10), nested_b_keys, nested_b_values,
             {0x333}, {300'000});
    memory.Refuse(nested_unmatched, 0x10, 0x80);
    memory.Refuse(nested_unmatched, 0x390, 0x10);
    if (membership_present) {
      memory.Put(item_a, 0x3C0, descriptors);
      memory.Put(item_a, 0x3CC, std::int32_t{1});
      memory.Put(descriptors, 0x20,
                 membership_matches ? member_key : other_key);
      memory.Put(Offset(rite, 0x750), 0x50, membership_ids);
      memory.Put(Offset(rite, 0x750), 0x5C, std::int32_t{1});
      memory.Put(membership_ids, 0, member_key);
    }
    if (partial_primary) memory.Refuse(primary_values, 0, 32, false);
  }
  game::BattleTerminalTransitionSnapshotV1 Observe(bool expected_alive = true) {
    const auto original_bytes = memory.Bytes();
    game::BattleTerminalTransitionRequestV1 request;
    request.character_ids = {kSubject};
    game::BattleTerminalTransitionSnapshotV1 output;
    const auto status = xar::ck3_12002::ReadBattleTerminalTransitionV1(
        bindings, scope, request, output);
    Require(status == game::BattleTerminalTransitionStatusV1::available &&
                output.status == status && output.unavailable_reason.empty() &&
                output.observed_date_raw == kDate && output.character_observations &&
                output.character_observations->size() == 1 &&
                memory.unexpected_reads == 0 && memory.Bytes() == original_bytes,
            "production query frame, demand or read-only source bytes differ");
    const auto &observed = output.character_observations->front();
    Require(observed.character_id == kSubject && observed.character_id != kPlayer &&
                observed.alive == expected_alive && observed.current_person_state,
            "query did not retain the explicitly requested character");
    const auto &person = *observed.current_person_state;
    Require(person.following_2922680 && !person.raw_numeric_inputs &&
                !person.current_stored_context_state &&
                !person.current_context_source_inputs &&
                !person.effective_prowess.available,
            "new same-query leaf missing or promoted historical person state");
    const auto &leaf = *person.following_2922680;
    Require(leaf.character_id == static_cast<std::uint32_t>(kSubject) &&
                leaf.character_identity == Address(subject) &&
                leaf.selected_model_identity == Address(model) &&
                leaf.destination_pc_identity == Address(model) + 0x10 &&
                leaf.build_version == native4::kGameVersion &&
                leaf.executable_sha256 == native4::kExecutableSha256,
            "same-query owner/model or exact4 provenance differs");
    output.snapshot_revision = kRevision;
    return output;
  }
};

enum class Kind { zero, absent, gated, negative, expired, source_zero,
                  generation, null_registry, partial, source_negative,
                  primary, membership_nonmatch, membership_admitted,
                  primary_partial };
struct Spec { const char *name; Kind kind; };
constexpr Spec kCases[] = {
    {"context-header-zero", Kind::zero},
    {"absent-context-static-zero", Kind::absent},
    {"dead-owner-static-header-zero", Kind::gated},
    {"negative-list-count", Kind::negative},
    {"expired-ordered-duplicates", Kind::expired},
    {"zero-source-count", Kind::source_zero},
    {"generation-fallback", Kind::generation},
    {"null-row-registry-skips-ids", Kind::null_registry},
    {"repeated-row-date-partial", Kind::partial},
    {"negative-source-count", Kind::source_negative},
    {"primary-ordered-duplicates-matched-nested", Kind::primary},
    {"membership-nonmatch-known-zero", Kind::membership_nonmatch},
    {"membership-admitted-primary-usable", Kind::membership_admitted},
    {"partial-primary-independent-siblings", Kind::primary_partial},
};

void Produce(const std::filesystem::path &directory, const Spec &spec,
             std::uint64_t sequence) {
  World world;
  const bool numeric = spec.kind == Kind::primary ||
      spec.kind == Kind::membership_nonmatch ||
      spec.kind == Kind::membership_admitted || spec.kind == Kind::primary_partial;
  if (!numeric) world.memory.Refuse(Offset(world.rite, 0x750), 0, 0x60);
  const bool header_only = spec.kind == Kind::zero || spec.kind == Kind::absent ||
                           spec.kind == Kind::gated || spec.kind == Kind::negative;
  switch (spec.kind) {
  case Kind::zero:
    world.memory.Put(world.context, 0x198 + 0xC, std::int32_t{0});
    break;
  case Kind::absent:
    world.memory.Put(world.subject, 0x1C0, static_cast<void *>(nullptr));
    break;
  case Kind::gated:
    world.memory.Put(world.subject, 0x1D0, world.gate);
    break;
  case Kind::negative:
    world.memory.Put(world.context, 0x198 + 0xC, std::int32_t{-2});
    break;
  case Kind::expired: break;
  case Kind::source_zero: world.ZeroSourceInputs(); break;
  case Kind::generation:
    world.memory.Put(world.a, 8, std::uint32_t{0x04000001});
    break;
  case Kind::null_registry:
    world.memory.Put(world.row_registry_slot, 0, static_cast<void *>(nullptr));
    world.memory.Refuse(world.list, 0, 4 * 4);
    break;
  case Kind::partial:
    world.memory.Refuse(world.a, 0xC7CE, 2, false);
    break;
  case Kind::source_negative:
    world.ZeroSourceInputs();
    world.memory.Put(world.a, 0x134, std::int32_t{-1});
    break;
  case Kind::primary: world.NumericInputs(false, false, false); break;
  case Kind::membership_nonmatch: world.NumericInputs(true, false, false); break;
  case Kind::membership_admitted: world.NumericInputs(true, true, false); break;
  case Kind::primary_partial: world.NumericInputs(false, false, true); break;
  }
  if (header_only) {
    world.NoRootDemand();
    const auto selected_header =
        spec.kind == Kind::absent || spec.kind == Kind::gated
            ? World::kStaticHeader : Address(world.context) + 0x198;
    world.memory.Refuse(selected_header, 8);
  } else if (!numeric && spec.kind != Kind::source_zero &&
             spec.kind != Kind::source_negative) {
    world.ExpiredInputsOnly();
  }
  const auto snapshot = world.Observe(spec.kind != Kind::gated);
  const auto &leaf = *snapshot.character_observations->front()
                          .current_person_state->following_2922680;
  const bool partial = spec.kind == Kind::partial || spec.kind == Kind::source_negative ||
                       spec.kind == Kind::membership_admitted ||
                       spec.kind == Kind::primary_partial;
  Require(leaf.ready == !(partial || spec.kind == Kind::negative),
          "whole leaf readiness differs");
  if (header_only) {
    const bool static_header = spec.kind == Kind::absent || spec.kind == Kind::gated;
    Require(leaf.list_header_identity ==
                (static_header ? World::kStaticHeader : Address(world.context) + 0x198) &&
                leaf.list_count_i32 == (spec.kind == Kind::negative ? -2 : 0) &&
                !leaf.list_array_identity && leaf.rows.empty() &&
                !leaf.rite_resolution.selected_identity &&
                !leaf.source_operand_identity,
            "header selection/count-zero demand or negative count differs");
    if (spec.kind == Kind::negative)
      Require(leaf.reason == "list_count_negative", "negative count became known empty");
  } else if (!numeric) {
    Require(leaf.list_count_i32 == 4 && leaf.list_array_identity == Address(world.list) &&
                leaf.rows.size() == 4 && leaf.source_operand_ready &&
                leaf.source_operand_identity == Address(world.rite) + 0x750,
            "physical list or pointer-only source operand differs");
    for (std::size_t index = 0; index < leaf.rows.size(); ++index) {
      const auto &row = leaf.rows[index];
      const bool failed = partial && (index == 0 || index == 2);
      Require(row.native_index == index && row.ready == !failed &&
                  row.known_no_contribution == !failed,
              "native occurrence ordinal or independently empty later row lost");
      if (spec.kind == Kind::null_registry) {
        Require(row.list_id_demanded == false && !row.list_full_id_u32 &&
                    row.resolution.selection == "fallback" &&
                    row.resolution.selected_identity == Address(world.fallback),
                "null registry demanded list ID or lost actual fallback");
      } else {
        const std::uint32_t expected = index == 1 ? World::kSecondId
            : index == 3 ? World::kThirdId : World::kFirstId;
        Require(row.list_id_demanded == true && row.list_full_id_u32 == expected,
                "full DWORD list generation or repeated order changed");
      }
      if (failed) {
        Require(row.reason == (spec.kind == Kind::partial
                    ? "row_cached_date_unread" : "source_list_count_negative"),
                "partial row reason was erased or upgraded");
      } else if (spec.kind == Kind::source_zero || spec.kind == Kind::source_negative) {
        Require(row.derived_year_i32 == 1 && !row.raw_date_c7c8_i32 &&
                    !row.current_date_i32 && row.source_list_count_i32 == 0 &&
                    !row.source_list_array_identity && row.sources.empty(),
                "known zero source family demanded raw date/array/current date");
      } else {
        Require(row.date_admitted == false && row.raw_date_c7c8_i32 == World::kDate - 1 &&
                    row.current_date_i32 == World::kDate && !row.source_list_count_i32,
                "expired row demanded remaining source inputs or lost current date");
      }
    }
    if (spec.kind != Kind::null_registry)
      Require(leaf.rows[0].resolution.selected_identity ==
                  leaf.rows[2].resolution.selected_identity,
              "duplicate physical rows were merged or selected differently");
    if (spec.kind == Kind::generation)
      Require(leaf.rows[0].resolution.selection == "fallback" &&
                  leaf.rows[0].resolution.candidate_full_id_u32 == 0x04000001U &&
                  leaf.rows[0].resolution.selected_identity == Address(world.fallback),
              "full generation mismatch did not select fallback");
  } else {
    Require(leaf.rows.size() == 1 && leaf.rows[0].sources.size() == 1 &&
                leaf.primary_ready == (spec.kind != Kind::primary_partial),
            "numeric source cardinality or independent primary readiness differs");
    const auto &source = leaf.rows[0].sources[0];
    Require(source.getter.ready && source.getter.admitted == true &&
                source.getter.mask_i32 == 0 && source.getter.start_index_i64 == 0 &&
                source.getter.selected_value_u32 == 0x07000001U &&
                source.items.size() == 3 &&
                source.items[0].object_identity == source.items[2].object_identity &&
                source.items[0].nested.size() == 2 &&
                source.items[0].nested[0].matched == true &&
                source.items[0].nested[1].matched == false,
            "actual hash hit, repeated item order or nested match changed");
    std::size_t primary_index = 0;
    std::size_t mapped_count = 0;
    for (const auto &append : leaf.append_occurrences) {
      if (append.kind == "item_mapped" || append.kind == "nested_mapped") {
        ++mapped_count;
        Require(spec.kind == Kind::membership_admitted && !append.ready &&
                    append.admitted == true &&
                    append.reason == "actual42127e0_input_unobserved",
                "admitted mapped input became an invented PC or lost its precise gap");
        continue;
      }
      Require(append.kind == (primary_index % 2 == 0 ? "item_primary" : "nested_primary") &&
                  append.outer_index == 0 && append.source_index == 0 &&
                  append.item_index == primary_index / 2 &&
                  append.weight_q100000 == 100'000,
              "primary source order, physical index or append weight differs");
      const bool unavailable = spec.kind == Kind::primary_partial &&
                               (primary_index == 0 || primary_index == 4);
      Require(append.ready == !unavailable && append.properties &&
                  append.properties->keys_u16 &&
                  static_cast<bool>(append.properties->values_q64) == !unavailable,
              "partial repeated PC discarded keys or independent sibling values");
      ++primary_index;
    }
    Require(primary_index == 6 && mapped_count ==
                (spec.kind == Kind::membership_admitted ? 2U : 0U),
            "primary/known-nonmatch/mapped append cardinality differs");
    if (spec.kind == Kind::membership_nonmatch || spec.kind == Kind::membership_admitted)
      Require(source.items[0].membership.rows.size() == 1 &&
                  source.items[0].membership.rows[0].admitted ==
                      (spec.kind == Kind::membership_admitted),
              "full pointer membership match/nonmatch result differs");
  }
  const auto request_id = std::string("person-following2922680-") + spec.name;
  const auto packet = xar::ck3_11906::SerializeBattleTerminalTransitionCommandResultV1(
      request_id, World::kStep, sequence, snapshot);
  Require(packet.find("\"following_2922680\":{") != std::string::npos &&
              packet.find(request_id) != std::string::npos &&
              packet.find("command_result") != std::string::npos,
          "real terminal formatter did not emit complete new whole packet");
  std::ofstream output(directory / (std::string(spec.name) + ".json"), std::ios::binary);
  output << packet;
  Require(static_cast<bool>(output), "cannot persist original production whole packet");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "usage: xar_ck3_12004_person_following_2922680_mcp_test output_directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  Require(!error, "cannot create packet output directory");
  std::uint64_t sequence = 0;
  for (const auto &spec : kCases) Produce(directory, spec, ++sequence);
  std::cout << "person following2922680: fourteen fresh production whole-command packets\n";
  return 0;
}
