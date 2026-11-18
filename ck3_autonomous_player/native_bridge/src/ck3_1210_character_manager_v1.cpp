#include "xar_bridge/ck3_1210_character_manager_v1.hpp"
#include <algorithm>
#include <cstring>
#include <limits>
#include <type_traits>
#include <utility>
#if defined(_MSC_VER)
#include <windows.h>
#endif

// Florin EXE-only source chain recorded in slot41/REPORT.json:
// GameData ctor2FDF464 -> data+3F540 -> ctor2DDB170 -> primary VT4E83550
// -> COL5652228 -> TD65B49A0 CCharacterManager. VT slot5=2DE2D40 retains
// this in r13; 2DE2EBD..2DE2EF3 traverses +20 pointer/+2C count, stride8.
// 2DE196A..2DE19A3 independently proves storage68A8628 full32 lookup.
// Char tag+1C is admitted by core anchors AFBB63; living+1B0/death+1D0
// are source operands, not a claim that this vector contains all living actors.
namespace xar::ck3_1210 {
namespace {
constexpr std::uint32_t kCharacterTag = 0x43686172U;
constexpr std::size_t kLiving = 0x1B0;
bool LocalCopy(void *, const void *source, void *destination,
    std::size_t bytes) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(destination, source, bytes); return true;
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
bool SameCore(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool Fail(CharacterManagerObservationV1 &output, std::string_view reason) noexcept {
  output = {}; output.unavailable_reason = reason; return false;
}
struct Roots {
  const void *game = nullptr, *jomini = nullptr, *data = nullptr, *players = nullptr;
  const void *storage = nullptr, *slots = nullptr, *manager = nullptr, *members = nullptr;
  std::uintptr_t manager_type = 0;
  std::int32_t storage_capacity = 0, member_capacity = 0, member_count = 0;
  std::int32_t date_raw = 0, native_speed = 0, local_player_id = -1;
  std::uint8_t paused = 0;
  friend bool operator==(const Roots &, const Roots &) = default;
};
struct Row {
  const void *object = nullptr, *death = nullptr, *living = nullptr;
  std::int32_t id = -1;
  std::uint32_t tag = 0;
  friend bool operator==(const Row &, const Row &) = default;
};
struct Transcript {
  Roots roots{};
  Row actor{};
  std::vector<Row> rows;
  friend bool operator==(const Transcript &, const Transcript &) = default;
};
struct Reader {
  const CharacterManagerBindingsV1 &bindings;
  CharacterManagerReadAccessV1 access;
  std::string_view reason = "character_manager_read_failed";
  template<class T> bool Read(const void *base, std::size_t offset, T &value) noexcept {
    static_assert(std::is_trivially_copyable_v<T> && sizeof(T) <= 8);
    const auto address = reinterpret_cast<std::uintptr_t>(base);
    const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
    if (address == 0 || offset > maximum - address ||
        sizeof(T) - 1 > maximum - (address + offset)) {
      reason = "character_manager_address_invalid"; return false;
    }
    const auto copy = access.copy != nullptr ? access.copy : LocalCopy;
    if (!copy(access.context, reinterpret_cast<const void *>(address + offset),
        &value, sizeof(T))) { reason = "character_manager_read_failed"; return false; }
    return true;
  }
  bool Root(Roots &out) noexcept {
    const auto &core = bindings.core;
    if (!Read(core.game_state_slot, 0, out.game) ||
        !Read(core.jomini_state_slot, 0, out.jomini) ||
        !Read(core.character_storage_slot, 0, out.storage) ||
        !Read(out.game, kGameStateDataOffset, out.data) ||
        !Read(out.game, kGameStateDateOffset, out.date_raw) ||
        !Read(out.game, kGameStateSpeedOffset, out.native_speed) ||
        !Read(out.jomini, kJominiPausedOffset, out.paused) ||
        !Read(out.jomini, kJominiPlayersOffset, out.players) ||
        !Read(out.players, kPlayersLocalPlayerIdOffset, out.local_player_id)) return false;
    const auto data = reinterpret_cast<std::uintptr_t>(out.data);
    const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
    if (data == 0 || out.jomini == nullptr ||
        kCharacterManagerOffsetV1 > maximum - data) {
      reason = "character_manager_roots_unavailable"; return false;
    }
    out.manager = reinterpret_cast<const void *>(data + kCharacterManagerOffsetV1);
    if (!Read(out.manager, 0, out.manager_type) ||
        !Read(out.manager, 0x20, out.members) ||
        !Read(out.manager, 0x28, out.member_capacity) ||
        !Read(out.manager, 0x2C, out.member_count) ||
        !Read(out.storage, kCharacterStorageSlotsOffset, out.slots) ||
        !Read(out.storage, kCharacterStorageCapacityOffset, out.storage_capacity)) return false;
    if (out.manager_type != bindings.manager_vtable) {
      reason = "character_manager_type_mismatch"; return false;
    }
    // New-image append2DE19F3->2DE17D7->8C7050 independently proves
    // vector+8 capacity/+C count; manager vector base is +20.
    if (out.member_capacity < 0 || out.member_count < 0 ||
        out.member_count > out.member_capacity || out.member_count > kCharacterManagerMemberLimitV1 ||
        (out.member_capacity != 0 && out.members == nullptr) || out.storage_capacity <= 0 ||
        out.storage_capacity > kCharacterLookupCapacityLimitV1 || out.slots == nullptr) {
      reason = "character_manager_header_invalid"; return false;
    }
    return true;
  }
  bool Header(const void *object, Row &row) noexcept {
    row.object = object;
    if (!Read(object, kCharacterFullIdOffset, row.id) || !Read(object, 0x1C, row.tag) ||
        !Read(object, kCharacterDeathDataOffset, row.death) || !Read(object, kLiving, row.living))
      return false;
    if (row.id == -1 || row.tag != kCharacterTag) {
      reason = "character_manager_member_type_or_id_invalid"; return false;
    }
    return true;
  }
  bool Lookup(const Roots &roots, std::int32_t id, const void *&object) noexcept {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    if (id == -1 || index >= static_cast<std::uint32_t>(roots.storage_capacity)) {
      reason = "character_manager_generation_unresolved"; return false;
    }
    if (!Read(roots.slots, static_cast<std::size_t>(index) * kCharacterStorageSlotStride +
        kCharacterStorageObjectOffset, object)) return false;
    if (object == nullptr) { reason = "character_manager_generation_unresolved"; return false; }
    return true;
  }
  bool Capture(const CoreSnapshotPrefix &expected, Transcript &out) {
    if (!Root(out.roots)) return false;
    if (out.roots.date_raw != expected.clock.date_raw ||
        out.roots.native_speed < 0 || out.roots.native_speed > 4 ||
        out.roots.native_speed + 1 != expected.clock.speed ||
        (out.roots.paused != 0) != expected.clock.paused ||
        out.roots.local_player_id != expected.local_player_id) {
      reason = "core_frame_changed"; return false;
    }
    const void *actor = nullptr;
    if (!Lookup(out.roots, expected.played_character_id, actor) || !Header(actor, out.actor))
      return false;
    if (out.actor.id != expected.played_character_id || out.actor.death != nullptr) {
      reason = "character_manager_actor_changed"; return false;
    }
    out.rows.reserve(static_cast<std::size_t>(out.roots.member_count));
    std::vector<std::uint32_t> ids;
    ids.reserve(static_cast<std::size_t>(out.roots.member_count));
    for (std::int32_t i = 0; i < out.roots.member_count; ++i) {
      const void *listed = nullptr, *resolved = nullptr;
      Row row{};
      if (!Read(out.roots.members, static_cast<std::size_t>(i) * sizeof(void *), listed) ||
          !Header(listed, row) || !Lookup(out.roots, row.id, resolved)) return false;
      if (resolved != listed) { reason = "character_manager_member_identity_mismatch"; return false; }
      out.rows.push_back(row); ids.push_back(static_cast<std::uint32_t>(row.id));
    }
    std::sort(ids.begin(), ids.end());
    if (std::adjacent_find(ids.begin(), ids.end()) != ids.end()) {
      reason = "character_manager_duplicate_member"; return false;
    }
    Roots confirmed{};
    if (!Root(confirmed)) return false;
    if (confirmed != out.roots) { reason = "character_manager_roots_changed"; return false; }
    return true;
  }
};
bool ReadImpl(const CharacterManagerBindingsV1 &bindings, const CoreSnapshotPrefix &expected,
    CharacterManagerObservationV1 &output, CharacterManagerReadAccessV1 access) {
  output = {};
  const auto &core = bindings.core;
  if (!bindings.exact_build_admitted || !core.enabled) return Fail(output, "unsupported_build");
  if (core.game_state_slot == nullptr || core.jomini_state_slot == nullptr ||
      core.character_storage_slot == nullptr || core.get_local_player == nullptr ||
      bindings.manager_vtable == 0) return Fail(output, "character_manager_binding_unavailable");
  if (!expected.clock.paused) return Fail(output, "requires_paused");
  if (!expected.map_ready || expected.local_player_id < 0 || !expected.has_played_character ||
      expected.played_character_id == -1 || !expected.played_character_alive)
    return Fail(output, "player_identity_unavailable");
  CoreSnapshotPrefix before{}, middle{};
  if (!Core(core, before) || !SameCore(before, expected)) return Fail(output, "core_frame_changed");
  Reader reader{bindings, access}; Transcript first{}, second{};
  if (!reader.Capture(expected, first)) return Fail(output, reader.reason);
  if (!Core(core, middle) || !SameCore(middle, expected)) return Fail(output, "core_frame_changed");
  if (!reader.Capture(expected, second)) return Fail(output, reader.reason);
  if (first != second) return Fail(output, "character_manager_transcript_changed");
  Roots final_roots{};
  if (!reader.Root(final_roots)) return Fail(output, reader.reason);
  if (final_roots != second.roots) return Fail(output, "character_manager_roots_changed");
  output.members.reserve(first.rows.size());
  for (const auto &row : first.rows)
    output.members.push_back({row.id, row.death == nullptr, row.living != nullptr});
  output.frame = middle;
  output.available = output.same_frame_ready = output.manager_members_complete = true;
  output.unavailable_reason = {}; return true;
}
} // namespace
CharacterManagerBindingsV1 BindCharacterManagerImageV1(std::uintptr_t base,
    std::string_view sha) noexcept {
  CharacterManagerBindingsV1 out{};
  const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  if (base == 0 || sha != kExecutableSha256 ||
      base > maximum - kJominiStateSlotRva - (sizeof(void *) - 1)) return out;
  out.core = BindCoreImage(base, sha);
  out.manager_vtable = base + kCharacterManagerVtableRvaV1;
  out.exact_build_admitted = out.core.enabled;
  return out;
}
bool ReadCharacterManagerV1(const CharacterManagerBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, CharacterManagerObservationV1 &output,
    CharacterManagerReadAccessV1 access) noexcept {
  try { return ReadImpl(bindings, expected, output, access); }
  catch (...) { return Fail(output, "allocation_or_internal_error"); }
}
} // namespace xar::ck3_1210
