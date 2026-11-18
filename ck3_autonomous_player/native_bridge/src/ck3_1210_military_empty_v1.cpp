#include "xar_bridge/ck3_1210_military_empty_v1.hpp"

#include <cstring>
#include <limits>
#include <type_traits>
#include <vector>

#if defined(_MSC_VER)
#include <windows.h>
#endif

// SNAPSHOT-MILITARY-1210-OFFLINE-ABI01.json: new RTTI, manager constructors,
// GameState owner users and native complete-ID resolvers independently close
// this graph. No legacy binder or nonempty-war enrichment is installed here.
namespace xar::ck3_1210 {
namespace {
constexpr std::uint32_t kUnitType = 0x556E6974U;
constexpr std::uint32_t kWarType = 0x5761725FU;
constexpr std::uint32_t kCharacterType = 0x43686172U;
constexpr std::size_t kTranscriptWordLimit = 16'777'216;

bool CopyLocal(void *, const void *source, void *target,
    std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(target, source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool Core(const CoreBindings &bindings, CoreSnapshotPrefix &output) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ReadCoreSnapshot(bindings, output);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { output = {}; return false; }
#endif
}

bool Same(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}

bool Fail(MilitaryEmptyObservationV1 &out, std::string_view reason) noexcept {
  out = {};
  out.unavailable_reason = reason;
  return false;
}

struct Storage {
  const void *object = nullptr;
  const void *slots = nullptr;
  std::int32_t capacity = 0;
};

struct Pass {
  const MilitaryEmptyBindingsV1 &bindings;
  MilitaryEmptyReadAccessV1 access;
  std::vector<std::uint64_t> transcript;
  std::string_view reason = "military_read_failed";
  Storage characters{};
  std::int32_t unit_slots = 0, war_slots = 0;
  std::size_t units = 0, wars = 0, participants = 0;

  template <class T>
  bool Read(const void *base, std::size_t offset, T &value) {
    static_assert(std::is_trivially_copyable_v<T> && sizeof(T) <= 8);
    const auto address = reinterpret_cast<std::uintptr_t>(base);
    const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
    if (address == 0 || offset > maximum - address ||
        sizeof(T) - 1 > maximum - (address + offset)) {
      reason = "military_address_invalid";
      return false;
    }
    const auto copier = access.copy != nullptr ? access.copy : CopyLocal;
    if (!copier(access.context, reinterpret_cast<const void *>(address + offset),
            &value, sizeof(T))) {
      reason = "military_read_failed";
      return false;
    }
    if (transcript.size() == kTranscriptWordLimit) {
      reason = "military_observation_scope_exceeded";
      return false;
    }
    // Exact values, not a lossy digest. Pointer roots and every used scalar,
    // every slot (including null), and every participant are captured.
    std::uint64_t word = 0;
    std::memcpy(&word, &value, sizeof(T));
    transcript.push_back(word);
    return true;
  }

  bool Header(const void *object, Storage &storage) {
    storage.object = object;
    if (object == nullptr || !Read(object, 0x20, storage.slots) ||
        !Read(object, 0x2C, storage.capacity)) {
      if (object == nullptr) reason = "military_registry_unavailable";
      return false;
    }
    if (storage.capacity < 0 || storage.capacity > kMilitaryEmptyStorageLimitV1 ||
        (storage.capacity != 0 && storage.slots == nullptr)) {
      reason = "military_storage_header_invalid";
      return false;
    }
    return true;
  }

  bool Character(std::int32_t id, bool actor) {
    if (id == -1) { reason = "military_character_identity_unavailable"; return false; }
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    if (index >= static_cast<std::uint32_t>(characters.capacity)) {
      reason = "military_character_generation_unresolved";
      return false;
    }
    const void *character = nullptr;
    std::int32_t actual = -1;
    std::uint32_t type = 0;
    if (!Read(characters.slots, static_cast<std::size_t>(index) * 0x10 + 8,
            character)) return false;
    if (character == nullptr) {
      reason = "military_character_generation_unresolved";
      return false;
    }
    if (!Read(character, 0x18, actual) || !Read(character, 0x1C, type)) return false;
    if (actual != id || type != kCharacterType) {
      reason = "military_character_generation_unresolved";
      return false;
    }
    if (actor) {
      const void *death = nullptr;
      if (!Read(character, kCharacterDeathDataOffset, death)) return false;
      if (death != nullptr) { reason = "military_actor_not_alive"; return false; }
    }
    return true;
  }

  bool Registry(const void *data, std::size_t manager_offset,
      void **global_slot, std::uintptr_t manager_vtable,
      std::uintptr_t registry_vtable, Storage &storage) {
    const void *global = nullptr, *owned = nullptr;
    std::uintptr_t manager_type = 0, storage_type = 0;
    if (!Read(global_slot, 0, global) ||
        !Read(data, manager_offset, manager_type) ||
        !Read(data, manager_offset + 0x20, owned)) return false;
    if (global == nullptr || owned != global) {
      reason = "military_registry_owner_mismatch";
      return false;
    }
    if (!Read(global, 0, storage_type)) return false;
    if (manager_type != manager_vtable || storage_type != registry_vtable) {
      reason = "military_registry_type_mismatch";
      return false;
    }
    return Header(global, storage);
  }

  bool Units(const Storage &storage, std::int32_t player) {
    unit_slots = storage.capacity;
    for (std::int32_t i = 0; i < storage.capacity; ++i) {
      const void *unit = nullptr;
      if (!Read(storage.slots, static_cast<std::size_t>(i) * 0x10 + 8, unit)) return false;
      if (unit == nullptr) continue;
      ++units;
      std::int32_t id = -1, owner = -1;
      std::uint32_t type = 0;
      if (!Read(unit, 0x10, id) || !Read(unit, 0x14, type) ||
          !Read(unit, 0x174, owner)) return false;
      if (id == -1 || (static_cast<std::uint32_t>(id) & 0x00FFFFFFU) !=
              static_cast<std::uint32_t>(i) || type != kUnitType) {
        reason = "military_unit_identity_invalid";
        return false;
      }
      if (!Character(owner, false)) return false;
      if (owner == player) { reason = "player_armies_nonempty"; return false; }
    }
    return true;
  }

  bool Side(const void *war, std::size_t side, std::int32_t player,
      bool &contains_player) {
    const void *records = nullptr;
    std::int32_t capacity = 0, count = 0;
    if (!Read(war, side + 8, records) || !Read(war, side + 0x10, capacity) ||
        !Read(war, side + 0x14, count)) return false;
    if (capacity < 0 || capacity > kMilitaryEmptySideLimitV1 || count < 0 ||
        count > capacity || (count != 0 && records == nullptr)) {
      reason = "military_participant_header_invalid";
      return false;
    }
    if (static_cast<std::size_t>(count) >
        kMilitaryEmptyParticipantBudgetV1 - participants) {
      reason = "military_participant_scope_exceeded";
      return false;
    }
    participants += static_cast<std::size_t>(count);
    contains_player = false;
    for (std::int32_t i = 0; i < count; ++i) {
      const void *record = nullptr;
      std::int32_t id = -1;
      if (!Read(records, static_cast<std::size_t>(i) * sizeof(void *), record))
        return false;
      if (record == nullptr) { reason = "military_participant_record_invalid"; return false; }
      if (!Read(record, 8, id) || !Character(id, false)) return false;
      contains_player = contains_player || id == player;
    }
    return true;
  }

  bool Wars(const Storage &storage, std::int32_t player) {
    war_slots = storage.capacity;
    for (std::int32_t i = 0; i < storage.capacity; ++i) {
      const void *war = nullptr;
      if (!Read(storage.slots, static_cast<std::size_t>(i) * 0x10 + 8, war)) return false;
      if (war == nullptr) continue;
      std::int32_t id = -1;
      std::uint32_t type = 0;
      std::uint8_t ended = 0;
      if (!Read(war, 8, id) || !Read(war, 0xC, type) || !Read(war, 0x360, ended))
        return false;
      if (id == -1 || (static_cast<std::uint32_t>(id) & 0x00FFFFFFU) !=
              static_cast<std::uint32_t>(i) || type != kWarType || ended > 1) {
        reason = "military_war_identity_invalid";
        return false;
      }
      if (ended != 0) continue;
      ++wars;
      bool attacking = false, defending = false;
      if (!Side(war, 0x20, player, attacking) ||
          !Side(war, 0x80, player, defending)) return false;
      if (attacking && defending) {
        reason = "military_player_on_both_sides";
        return false;
      }
      if (attacking || defending) {
        reason = "active_wars_nonempty_rich_observation_unavailable";
        return false;
      }
    }
    return true;
  }

  bool Capture(std::int32_t player) {
    const void *game = nullptr, *jomini = nullptr, *data = nullptr;
    const void *character_storage = nullptr;
    const auto &core = bindings.core;
    if (!Read(core.game_state_slot, 0, game) ||
        !Read(core.jomini_state_slot, 0, jomini) ||
        !Read(core.character_storage_slot, 0, character_storage)) return false;
    if (game == nullptr || jomini == nullptr || character_storage == nullptr) {
      reason = "military_core_graph_unavailable";
      return false;
    }
    if (!Read(game, kGameStateDataOffset, data)) return false;
    if (data == nullptr) { reason = "military_game_data_unavailable"; return false; }
    if (!Header(character_storage, characters) || !Character(player, true)) return false;
    Storage units_storage{}, wars_storage{};
    return Registry(data, kMilitaryUnitManagerOffsetV1, bindings.unit_registry_slot,
               bindings.unit_manager_vtable, bindings.unit_registry_vtable, units_storage) &&
        Registry(data, kMilitaryWarManagerOffsetV1, bindings.war_registry_slot,
               bindings.war_manager_vtable, bindings.war_registry_vtable, wars_storage) &&
        Units(units_storage, player) && Wars(wars_storage, player);
  }
};

bool ReadImpl(const MilitaryEmptyBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, MilitaryEmptyObservationV1 &output,
    MilitaryEmptyReadAccessV1 access) {
  output = {};
  const auto &core = bindings.core;
  if (!bindings.exact_build_admitted || !core.enabled)
    return Fail(output, "unsupported_build");
  if (core.game_state_slot == nullptr || core.jomini_state_slot == nullptr ||
      core.character_storage_slot == nullptr || core.get_local_player == nullptr ||
      bindings.unit_registry_slot == nullptr || bindings.war_registry_slot == nullptr ||
      bindings.unit_registry_vtable == 0 || bindings.war_registry_vtable == 0 ||
      bindings.unit_manager_vtable == 0 || bindings.war_manager_vtable == 0)
    return Fail(output, "military_binding_unavailable");
  if (!expected.clock.paused) return Fail(output, "requires_paused");
  if (!expected.map_ready) return Fail(output, "map_not_ready");
  if (!expected.has_played_character || expected.played_character_id == -1 ||
      expected.local_player_id < 0 || !expected.played_character_alive)
    return Fail(output, "military_actor_unavailable");
  CoreSnapshotPrefix first{}, middle{}, last{};
  if (!Core(core, first)) return Fail(output, "core_read_failed");
  if (!Same(first, expected)) return Fail(output, "core_frame_changed");
  Pass before{bindings, access};
  if (!before.Capture(expected.played_character_id)) return Fail(output, before.reason);
  if (!Core(core, middle)) return Fail(output, "core_read_failed");
  if (!Same(middle, first)) return Fail(output, "core_frame_changed");
  Pass after{bindings, access};
  if (!after.Capture(expected.played_character_id)) return Fail(output, after.reason);
  if (!Core(core, last)) return Fail(output, "core_read_failed");
  if (!Same(last, first)) return Fail(output, "core_frame_changed");
  if (before.transcript != after.transcript)
    return Fail(output, "military_collections_changed");
  output.available = true;
  output.same_frame_ready = true;
  output.player_armies_empty_proven = true;
  output.active_wars_empty_proven = true;
  output.frame = last;
  output.unit_slots_scanned = before.unit_slots;
  output.war_slots_scanned = before.war_slots;
  output.live_unit_rows = before.units;
  output.active_war_rows = before.wars;
  output.participant_records = before.participants;
  output.unavailable_reason = {};
  return true;
}
} // namespace

MilitaryEmptyBindingsV1 BindMilitaryEmptyImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  MilitaryEmptyBindingsV1 result{};
  constexpr auto top = kMilitaryUnitRegistryRvaV1 + sizeof(void *) - 1;
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      image_base > (std::numeric_limits<std::uintptr_t>::max)() - top) return result;
  result.core = BindCoreImage(image_base, executable_sha256);
  if (!result.core.enabled) return {};
  result.unit_registry_slot = reinterpret_cast<void **>(image_base + kMilitaryUnitRegistryRvaV1);
  result.war_registry_slot = reinterpret_cast<void **>(image_base + kMilitaryWarRegistryRvaV1);
  result.unit_registry_vtable = image_base + kMilitaryUnitRegistryVtableRvaV1;
  result.war_registry_vtable = image_base + kMilitaryWarRegistryVtableRvaV1;
  result.unit_manager_vtable = image_base + kMilitaryUnitManagerVtableRvaV1;
  result.war_manager_vtable = image_base + kMilitaryWarManagerVtableRvaV1;
  result.exact_build_admitted = true;
  return result;
}

bool ReadMilitaryEmptyV1(const MilitaryEmptyBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, MilitaryEmptyObservationV1 &output,
    MilitaryEmptyReadAccessV1 access) noexcept {
  try {
    return ReadImpl(bindings, expected, output, access);
  } catch (...) {
    return Fail(output, "military_allocation_or_internal_error");
  }
}

} // namespace xar::ck3_1210
