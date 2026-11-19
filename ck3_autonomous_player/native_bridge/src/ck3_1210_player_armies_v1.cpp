#include "xar_bridge/ck3_1210_nonempty_military_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_player_armies_v1.hpp"

#include <cstring>
#include <limits>
#include <type_traits>
#include <utility>

#if defined(_MSC_VER)
#include <windows.h>
#endif

// Positive ABI02: CUnit RTTI/serializer + native state, route destructor and
// last-Province getter independently prove this graph. No legacy bindings,
// Army strength/raise/siege implementation or gameplay capability is reused.
namespace xar::ck3_1210 {
namespace {
constexpr std::uint32_t kUnitTag = 0x556E6974U, kCharacterTag = 0x43686172U;
constexpr std::uint32_t kProvinceTag = 0x50726F76U;
constexpr std::size_t kTranscriptWordLimit = 16'777'216;

bool CopyLocal(void *, const void *source, void *target, std::size_t size) noexcept {
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
bool NativeState(PlayerArmyNativeStateGetterV1 getter, void *unit,
    std::int32_t &state) {
#if defined(_MSC_VER)
  __try {
#endif
    state = getter(unit);
    return true;
#if defined(_MSC_VER)
  } __except (GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool Same(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool Fail(PlayerArmiesObservationV1 &out, std::string_view reason) noexcept {
  const auto calls = out.native_state_calls_attempted;
  out = {};
  out.native_state_calls_attempted = calls;
  out.unavailable_reason = reason;
  return false;
}
std::string_view StateName(std::int32_t state) noexcept {
  switch (state) {
  case 1: return "regular"; case 2: return "combat"; case 3: return "sieging";
  case 4: return "embarked"; case 5: return "gathering"; case 6: return "retreating";
  case 7: return "moving"; case 8: return "raiding"; case 9: return "bartering";
  default: return "unknown";
  }
}
struct Storage { const void *slots = nullptr; std::int32_t capacity = 0; };

struct Pass {
  const PlayerArmiesBindingsV1 &bindings;
  PlayerArmiesReadAccessV1 access;
  std::size_t &calls;
  std::vector<std::uint64_t> transcript;
  std::vector<PlayerArmyObservationRowV1> rows;
  std::string_view reason = "player_armies_read_failed";
  Storage characters{};
  const void *game_data = nullptr;
  std::int32_t scanned_slots = 0;
  std::size_t units = 0, route_entries = 0;
  bool state_guard_verified = false;

  template <class T> bool Read(const void *base, std::size_t offset, T &value) {
    static_assert(std::is_trivially_copyable_v<T> && sizeof(T) <= 8);
    const auto address = reinterpret_cast<std::uintptr_t>(base);
    const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
    if (address == 0 || offset > maximum - address ||
        sizeof(T) - 1 > maximum - (address + offset)) {
      reason = "player_armies_address_invalid"; return false;
    }
    const auto copier = access.copy != nullptr ? access.copy : CopyLocal;
    if (!copier(access.context, reinterpret_cast<const void *>(address + offset),
            &value, sizeof(T))) {
      reason = "player_armies_read_failed"; return false;
    }
    if (transcript.size() == kTranscriptWordLimit) {
      reason = "player_armies_observation_scope_exceeded"; return false;
    }
    std::uint64_t word = 0;
    std::memcpy(&word, &value, sizeof(T));
    transcript.push_back(word);
    return true;
  }
  bool Header(const void *storage, Storage &out) {
    if (storage == nullptr) { reason = "player_armies_registry_unavailable"; return false; }
    if (!Read(storage, 0x20, out.slots) || !Read(storage, 0x2C, out.capacity)) return false;
    if (out.capacity < 0 || out.capacity > kPlayerArmyStorageLimitV1 ||
        (out.capacity != 0 && out.slots == nullptr)) {
      reason = "player_armies_storage_header_invalid"; return false;
    }
    return true;
  }
  bool Character(std::int32_t id, bool actor) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    if (id == -1 || index >= static_cast<std::uint32_t>(characters.capacity)) {
      reason = "player_armies_character_generation_unresolved"; return false;
    }
    const void *character = nullptr;
    std::int32_t full_id = -1;
    std::uint32_t tag = 0;
    if (!Read(characters.slots, static_cast<std::size_t>(index) * 0x10 + 8, character)) return false;
    if (character == nullptr) { reason = "player_armies_character_generation_unresolved"; return false; }
    if (!Read(character, 0x18, full_id) || !Read(character, 0x1C, tag)) return false;
    if (full_id != id || tag != kCharacterTag) {
      reason = "player_armies_character_generation_unresolved"; return false;
    }
    if (actor) {
      const void *death = nullptr;
      if (!Read(character, kCharacterDeathDataOffset, death)) return false;
      if (death != nullptr) { reason = "player_armies_actor_not_alive"; return false; }
    }
    return true;
  }
  bool Province(std::int32_t id, const void *expected = nullptr) {
    const void *array = nullptr, *province = nullptr;
    std::int32_t count = 0, actual = -1;
    std::uint32_t tag = 0;
    if (!Read(game_data, 0x4140, array) || !Read(game_data, 0x414C, count)) return false;
    if (id <= 0 || count <= 1 || count > kPlayerArmyStorageLimitV1 ||
        id >= count || array == nullptr) {
      reason = "player_armies_province_header_or_id_invalid"; return false;
    }
    if (!Read(array, static_cast<std::size_t>(id) * sizeof(void *), province)) return false;
    if (province == nullptr || (expected != nullptr && province != expected)) {
      reason = "player_armies_province_identity_invalid"; return false;
    }
    if (!Read(province, 0x10, actual) || !Read(province, 0xB24, tag)) return false;
    if (actual != id || tag != kProvinceTag) {
      reason = "player_armies_province_identity_invalid"; return false;
    }
    return true;
  }
  bool Route(const void *unit, PlayerArmyObservationRowV1 &row) {
    const void *path = nullptr;
    std::int32_t capacity = 0, count = 0;
    if (!Read(unit, 0x38, path) || !Read(unit, 0x40, capacity) ||
        !Read(unit, 0x44, count)) return false;
    if (capacity < 0 || capacity > kPlayerArmyStorageLimitV1 || count < 0 ||
        count > capacity || (capacity != 0 && path == nullptr)) {
      reason = "player_armies_route_header_invalid"; return false;
    }
    if (count > kPlayerArmyRouteLimitV1 || static_cast<std::size_t>(count) >
        kPlayerArmyRouteBudgetV1 - route_entries) {
      reason = "player_armies_route_scope_exceeded"; return false;
    }
    row.route_source_count = count;
    route_entries += static_cast<std::size_t>(count);
    row.route_province_ids.reserve(static_cast<std::size_t>(count));
    for (std::int32_t i = 0; i < count; ++i) {
      const void *info = nullptr;
      std::int32_t province_id = -1;
      if (!Read(path, static_cast<std::size_t>(i) * sizeof(void *), info)) return false;
      if (info == nullptr) { reason = "player_armies_route_entry_unresolved"; return false; }
      if (!Read(info, 0, province_id) || !Province(province_id)) return false;
      row.route_province_ids.push_back(province_id);
    }
    row.route_read_status = count == 0 ? PlayerArmyRouteReadStatusV1::complete_empty :
        PlayerArmyRouteReadStatusV1::complete_nonempty;
    if (count != 0) row.move_target_province_id = row.route_province_ids.back();
    return true;
  }
  bool State(void *unit, PlayerArmyObservationRowV1 &row) {
    if (!bindings.integration_native_calls_permitted) {
      reason = "player_armies_native_calls_not_permitted"; return false;
    }
    if (bindings.get_unit_state == nullptr) {
      reason = "player_armies_native_state_unavailable"; return false;
    }
    const bool hotfix=IsHotfix(bindings.core.image_build);
    const auto admit=bindings.native_call_admission;
    const auto admission_context=bindings.native_call_admission_context;
    if ((hotfix && admit==nullptr) || (admit && !admit(admission_context))) {
      reason="player_armies_native_owner_before_unavailable";return false;
    }
    if (!state_guard_verified || hotfix) {
      std::array<std::uint8_t, 32> actual{};
      for (std::size_t offset = 0; offset < actual.size(); offset += sizeof(std::uint64_t)) {
        std::uint64_t word = 0;
        if (!Read(reinterpret_cast<const void *>(bindings.get_unit_state), offset, word)) return false;
        std::memcpy(actual.data() + offset, &word, sizeof word);
      }
      if (actual != (IsHotfix(bindings.core.image_build) ? military_hotfix26757580::kStateEntry32 : kPlayerArmyStateEntryGuardV1)) {
        reason = "player_armies_native_state_guard_mismatch"; return false;
      }
      state_guard_verified = true;
    }
    PlayerArmyStateInputWordsV1 input_before{}, input_after{};
    const auto validate = access.validate_state_input;
    if (validate != nullptr) {
      if (!validate(access.state_input_context, unit, row.native_army_reference, input_before)) {
        reason = "player_armies_native_state_input_unavailable"; return false;
      }
      if (input_before.size() > kTranscriptWordLimit - transcript.size()) {
        reason = "player_armies_observation_scope_exceeded"; return false;
      }
      transcript.insert(transcript.end(), input_before.begin(), input_before.end());
    }
    ++calls;
    const bool state_read = NativeState(bindings.get_unit_state, unit, row.army_state_code);
    if (bindings.native_call_admission!=admit || bindings.native_call_admission_context!=admission_context ||
        (admit && !admit(admission_context))) {
      reason="player_armies_native_owner_after_unavailable";return false;
    }
    if (validate != nullptr) {
      if (!validate(access.state_input_context, unit, row.native_army_reference, input_after)) {
        reason = "player_armies_native_state_input_unavailable"; return false;
      }
      if (input_before != input_after) {
        reason = "player_armies_native_state_input_changed"; return false;
      }
      if (input_after.size() > kTranscriptWordLimit - transcript.size()) {
        reason = "player_armies_observation_scope_exceeded"; return false;
      }
      transcript.insert(transcript.end(), input_after.begin(), input_after.end());
    }
    if (!state_read) {
      reason = "player_armies_native_state_read_failed"; return false;
    }
    if (row.army_state_code < 1 || row.army_state_code > 9) {
      reason = "player_armies_native_state_invalid"; return false;
    }
    row.army_state = StateName(row.army_state_code);
    row.in_combat = row.army_state_code == 2;
    return true;
  }
  bool Capture(std::int32_t player) {
    const void *game = nullptr, *jomini = nullptr, *character_storage = nullptr;
    const auto &core = bindings.core;
    if (!Read(core.game_state_slot, 0, game) || !Read(core.jomini_state_slot, 0, jomini) ||
        !Read(core.character_storage_slot, 0, character_storage)) return false;
    if (game == nullptr || jomini == nullptr || character_storage == nullptr) {
      reason = "player_armies_core_graph_unavailable"; return false;
    }
    if (!Read(game, kGameStateDataOffset, game_data)) return false;
    if (game_data == nullptr) { reason = "player_armies_game_data_unavailable"; return false; }
    if (!Header(character_storage, characters) || !Character(player, true)) return false;
    const void *registry = nullptr, *owned = nullptr;
    std::uintptr_t manager_type = 0, registry_type = 0;
    if (!Read(bindings.unit_registry_slot, 0, registry) ||
        !Read(game_data, kPlayerArmyUnitManagerOffsetV1, manager_type) ||
        !Read(game_data, kPlayerArmyUnitManagerOffsetV1 + 0x20, owned)) return false;
    if (registry == nullptr || registry != owned) {
      reason = "player_armies_registry_owner_mismatch"; return false;
    }
    if (!Read(registry, 0, registry_type)) return false;
    if (registry_type != bindings.unit_registry_vtable || manager_type != bindings.unit_manager_vtable) {
      reason = "player_armies_registry_type_mismatch"; return false;
    }
    Storage storage{};
    if (!Header(registry, storage)) return false;
    scanned_slots = storage.capacity;
    for (std::int32_t i = 0; i < storage.capacity; ++i) {
      void *unit = nullptr;
      std::int32_t id = -1, owner = -1;
      std::uint32_t type = 0;
      if (!Read(storage.slots, static_cast<std::size_t>(i) * 0x10 + 8, unit)) return false;
      if (unit == nullptr) continue;
      ++units;
      if (!Read(unit, 0x10, id) || !Read(unit, 0x14, type) || !Read(unit, 0x174, owner)) return false;
      if (id == -1 || (static_cast<std::uint32_t>(id) & 0x00FFFFFFU) !=
              static_cast<std::uint32_t>(i) || type != kUnitTag) {
        reason = "player_armies_unit_identity_invalid"; return false;
      }
      if (!Character(owner, false)) return false;
      if (owner != player) continue;
      if (rows.size() == kPlayerArmyOwnedLimitV1) {
        reason = "player_armies_owned_scope_exceeded"; return false;
      }
      PlayerArmyObservationRowV1 row{};
      row.army_id = id; row.owner_character_id = owner; row.controllable = true;
      const void *province = nullptr;
      if (!Read(unit, 0x20, province) || !Read(unit, 0x170, row.retreat_state_raw) ||
          !Read(unit, 0x178, row.native_army_reference)) return false;
      row.retreating = row.retreat_state_raw > 0;
      if (province != nullptr) {
        std::int32_t province_id = -1;
        if (!Read(province, 0x10, province_id) || !Province(province_id, province)) return false;
        row.current_province_id = province_id;
      }
      if (!Route(unit, row) || !State(unit, row)) return false;
      rows.push_back(std::move(row));
    }
    return true;
  }
};

bool ReadImpl(const PlayerArmiesBindingsV1 &bindings, const CoreSnapshotPrefix &expected,
    PlayerArmiesObservationV1 &out, PlayerArmiesReadAccessV1 access) {
  out = {};
  const auto &core = bindings.core;
  if (!bindings.exact_build_admitted || !core.enabled) return Fail(out, "unsupported_build");
  if (core.game_state_slot == nullptr || core.jomini_state_slot == nullptr ||
      core.character_storage_slot == nullptr || core.get_local_player == nullptr ||
      bindings.unit_registry_slot == nullptr || bindings.unit_registry_vtable == 0 ||
      bindings.unit_manager_vtable == 0) return Fail(out, "player_armies_binding_unavailable");
  if (!expected.clock.paused) return Fail(out, "requires_paused");
  if (!expected.map_ready) return Fail(out, "map_not_ready");
  if (!expected.has_played_character || expected.played_character_id == -1 ||
      expected.local_player_id < 0 || !expected.played_character_alive)
    return Fail(out, "player_armies_actor_unavailable");
  CoreSnapshotPrefix first{}, middle{}, last{};
  if (!Core(core, first)) return Fail(out, "core_read_failed");
  if (!Same(first, expected)) return Fail(out, "core_frame_changed");
  Pass before{bindings, access, out.native_state_calls_attempted};
  if (!before.Capture(expected.played_character_id)) return Fail(out, before.reason);
  if (!Core(core, middle)) return Fail(out, "core_read_failed");
  if (!Same(middle, first)) return Fail(out, "core_frame_changed");
  Pass after{bindings, access, out.native_state_calls_attempted};
  if (!after.Capture(expected.played_character_id)) return Fail(out, after.reason);
  if (!Core(core, last)) return Fail(out, "core_read_failed");
  if (!Same(last, first)) return Fail(out, "core_frame_changed");
  if (before.transcript != after.transcript || before.rows != after.rows)
    return Fail(out, "player_armies_collection_changed");
  out.available = out.same_frame_ready = out.collection_complete = true;
  out.frame = last;
  out.player_armies = std::move(before.rows);
  out.unit_slots_scanned = before.scanned_slots;
  out.live_unit_rows = before.units;
  out.unavailable_reason = {};
  return true;
}
} // namespace

PlayerArmiesBindingsV1 BindPlayerArmiesImageV1(std::uintptr_t base,
    std::string_view sha) noexcept {
  PlayerArmiesBindingsV1 result{};
  const auto build=ImageBuildForSha(sha);
  const auto registry=ImageRva(build,kPlayerArmyUnitRegistryRvaV1,military_hotfix26757580::kUnitRegistry);
  const auto top=registry+sizeof(void*)-1;
  if (base == 0 || build == ImageBuildV1::unknown ||
      base > (std::numeric_limits<std::uintptr_t>::max)() - top) return result;
  result.core = BindCoreImage(base, sha);
  if (!result.core.enabled) return {};
  result.unit_registry_slot = reinterpret_cast<void **>(base + registry);
  result.unit_registry_vtable = base + ImageRva(build,kPlayerArmyUnitRegistryVtableRvaV1,military_hotfix26757580::kUnitRegistryVt);
  result.unit_manager_vtable = base + ImageRva(build,kPlayerArmyUnitManagerVtableRvaV1,military_hotfix26757580::kUnitManagerVt);
  result.get_unit_state = reinterpret_cast<PlayerArmyNativeStateGetterV1>(base + ImageRva(build,kPlayerArmyUnitStateRvaV1,military_hotfix26757580::kUnitState));
  result.exact_build_admitted = true;
  return result;
}
bool ReadPlayerArmiesV1(const PlayerArmiesBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, PlayerArmiesObservationV1 &output,
    PlayerArmiesReadAccessV1 access) noexcept {
  try { return ReadImpl(bindings, expected, output, access); }
  catch (...) { return Fail(output, "player_armies_allocation_or_internal_error"); }
}
} // namespace xar::ck3_1210
