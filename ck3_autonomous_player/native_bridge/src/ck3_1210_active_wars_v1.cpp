#include "xar_bridge/ck3_1210_nonempty_military_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_active_wars_v1.hpp"

#include <cstring>
#include <limits>
#include <type_traits>
#include <utility>

#if defined(_MSC_VER)
#include <windows.h>
#endif

// ABI01/GAP04: CWar RTTI and real owner/full-ID/member callers independently
// establish this graph. Native character-relative caller1B889A0 proves score
// direction. No military-empty, Unit, target hierarchy or old binder is used.
namespace xar::ck3_1210 {
namespace {
constexpr std::uint32_t kWarTag = 0x5761725FU, kCharacterTag = 0x43686172U;
constexpr std::size_t kTranscriptWordLimit = 16'777'216;
bool CopyLocal(void *, const void *source, void *dest, std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(dest, source, size); return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool Core(const CoreBindings &bindings, CoreSnapshotPrefix &out) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ReadCoreSnapshot(bindings, out);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { out = {}; return false; }
#endif
}
bool NativeScore(ActiveWarsNativeScoreGetterV1 getter, const void *war,
    std::int32_t &score) {
#if defined(_MSC_VER)
  __try {
#endif
    score = getter(war, nullptr); return true;
#if defined(_MSC_VER)
  } __except (GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool SameCore(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool SameIdentity(const ActiveWarIdentityRowV1 &a, const ActiveWarIdentityRowV1 &b) noexcept {
  return a.war_id == b.war_id && a.actual_player_character_id == b.actual_player_character_id &&
      a.player_side == b.player_side &&
      a.primary_attacker_character_id == b.primary_attacker_character_id &&
      a.primary_defender_character_id == b.primary_defender_character_id &&
      a.primary_opponent_character_id == b.primary_opponent_character_id &&
      a.player_is_primary_war_leader == b.player_is_primary_war_leader &&
      a.attacker_participant_ids == b.attacker_participant_ids &&
      a.defender_participant_ids == b.defender_participant_ids;
}
bool Fail(ActiveWarsObservationV1 &out, std::string_view reason) noexcept {
  const auto calls = out.native_score_calls_attempted;
  out = {}; out.native_score_calls_attempted = calls; out.unavailable_reason = reason;
  return false;
}
struct Storage { const void *slots = nullptr; std::int32_t capacity = 0; };
struct Roots {
  const void *game = nullptr, *jomini = nullptr, *data = nullptr;
  const void *characters = nullptr, *character_slots = nullptr, *actor = nullptr;
  const void *wars = nullptr, *war_slots = nullptr;
  std::int32_t character_capacity = 0, war_capacity = 0;
  friend bool operator==(const Roots &, const Roots &) = default;
};
struct Pass {
  const ActiveWarsBindingsV1 &bindings;
  const CoreSnapshotPrefix &expected;
  ActiveWarsReadAccessV1 access;
  std::size_t &calls;
  Roots roots{};
  Storage characters{}, wars{};
  std::vector<std::uint64_t> transcript;
  std::vector<ActiveWarIdentityRowV1> rows;
  std::string_view reason = "active_wars_read_failed";
  std::size_t active_count = 0, ended_count = 0, participants = 0;

  template <class T> bool Read(const void *base, std::size_t offset, T &value) {
    static_assert(std::is_trivially_copyable_v<T> && sizeof(T) <= 8);
    const auto address = reinterpret_cast<std::uintptr_t>(base);
    const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
    if (address == 0 || offset > maximum - address ||
        sizeof(T) - 1 > maximum - (address + offset)) {
      reason = "active_wars_address_invalid"; return false;
    }
    const auto copy = access.copy != nullptr ? access.copy : CopyLocal;
    if (!copy(access.context, reinterpret_cast<const void *>(address + offset), &value, sizeof(T))) {
      reason = "active_wars_read_failed"; return false;
    }
    if (transcript.size() == kTranscriptWordLimit) {
      reason = "active_wars_observation_scope_exceeded"; return false;
    }
    std::uint64_t word = 0; std::memcpy(&word, &value, sizeof(T));
    transcript.push_back(word); return true;
  }
  bool Header(const void *object, Storage &out) {
    if (object == nullptr) { reason = "active_wars_registry_unavailable"; return false; }
    if (!Read(object, 0x20, out.slots) || !Read(object, 0x2C, out.capacity)) return false;
    if (out.capacity < 0 || out.capacity > kActiveWarsStorageLimitV1 ||
        (out.capacity != 0 && out.slots == nullptr)) {
      reason = "active_wars_storage_header_invalid"; return false;
    }
    return true;
  }
  bool Character(std::int32_t id, bool actor) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    if (id == -1 || index >= static_cast<std::uint32_t>(characters.capacity)) {
      reason = "active_wars_character_generation_unresolved"; return false;
    }
    const void *peer = nullptr; std::int32_t full_id = -1; std::uint32_t tag = 0;
    if (!Read(characters.slots, static_cast<std::size_t>(index) * 0x10 + 8, peer)) return false;
    if (peer == nullptr) { reason = "active_wars_character_generation_unresolved"; return false; }
    if (!Read(peer, 0x18, full_id) || !Read(peer, 0x1C, tag)) return false;
    if (full_id != id || tag != kCharacterTag) {
      reason = "active_wars_character_generation_unresolved"; return false;
    }
    if (actor) {
      const void *death = nullptr;
      if (!Read(peer, kCharacterDeathDataOffset, death)) return false;
      if (death != nullptr) { reason = "active_wars_actor_not_alive"; return false; }
      roots.actor = peer;
    }
    return true;
  }
  bool ReadRoots() {
    const auto &core = bindings.core;
    if (!Read(core.game_state_slot, 0, roots.game) ||
        !Read(core.jomini_state_slot, 0, roots.jomini) ||
        !Read(core.character_storage_slot, 0, roots.characters)) return false;
    if (roots.game == nullptr || roots.jomini == nullptr || roots.characters == nullptr) {
      reason = "active_wars_core_graph_unavailable"; return false;
    }
    if (!Read(roots.game, kGameStateDataOffset, roots.data)) return false;
    if (roots.data == nullptr) { reason = "active_wars_game_data_unavailable"; return false; }
    if (!Header(roots.characters, characters) || !Character(expected.played_character_id, true)) return false;
    roots.character_slots = characters.slots; roots.character_capacity = characters.capacity;
    const void *owned = nullptr; std::uintptr_t manager_type = 0, storage_type = 0;
    if (!Read(bindings.war_registry_slot, 0, roots.wars) ||
        !Read(roots.data, kActiveWarsManagerOffsetV1, manager_type) ||
        !Read(roots.data, kActiveWarsManagerOffsetV1 + 0x20, owned)) return false;
    if (roots.wars == nullptr || roots.wars != owned) {
      reason = "active_wars_registry_owner_mismatch"; return false;
    }
    if (!Read(roots.wars, 0, storage_type)) return false;
    if (manager_type != bindings.war_manager_vtable || storage_type != bindings.war_registry_vtable) {
      reason = "active_wars_registry_type_mismatch"; return false;
    }
    if (!Header(roots.wars, wars)) return false;
    roots.war_slots = wars.slots; roots.war_capacity = wars.capacity;
    return true;
  }
  bool Side(const void *war, std::size_t offset, std::vector<std::int32_t> &ids,
      bool &contains_player) {
    const void *records = nullptr; std::int32_t capacity = 0, count = 0;
    if (!Read(war, offset + 8, records) || !Read(war, offset + 0x10, capacity) ||
        !Read(war, offset + 0x14, count)) return false;
    if (capacity < 0 || capacity > kActiveWarsSideLimitV1 || count < 0 || count > capacity ||
        (count != 0 && records == nullptr)) {
      reason = "active_wars_participant_header_invalid"; return false;
    }
    if (static_cast<std::size_t>(count) > kActiveWarsParticipantBudgetV1 - participants) {
      reason = "active_wars_participant_scope_exceeded"; return false;
    }
    participants += static_cast<std::size_t>(count);
    contains_player = false; ids.reserve(static_cast<std::size_t>(count));
    for (std::int32_t i = 0; i < count; ++i) {
      const void *record = nullptr; std::int32_t id = -1;
      if (!Read(records, static_cast<std::size_t>(i) * sizeof(void *), record)) return false;
      if (record == nullptr) { reason = "active_wars_participant_record_invalid"; return false; }
      if (!Read(record, 8, id) || !Character(id, false)) return false;
      ids.push_back(id); contains_player = contains_player || id == expected.played_character_id;
    }
    return true;
  }
  bool ReadAt(std::int32_t index, const void *&war, ActiveWarIdentityRowV1 &row,
      bool &linked) {
    linked = false; war = nullptr;
    if (index < 0 || index >= wars.capacity) { reason = "active_wars_index_invalid"; return false; }
    if (!Read(wars.slots, static_cast<std::size_t>(index) * 0x10 + 8, war)) return false;
    if (war == nullptr) return true;
    std::int32_t id = -1; std::uint32_t tag = 0; std::uint8_t ended = 0;
    std::uintptr_t war_type = 0;
    if (!Read(war, 0, war_type) || !Read(war, 8, id) ||
        !Read(war, 0xC, tag) || !Read(war, 0x360, ended)) return false;
    if (id == -1 || (static_cast<std::uint32_t>(id) & 0x00FFFFFFU) !=
            static_cast<std::uint32_t>(index) || tag != kWarTag ||
        war_type != bindings.war_vtable || ended > 1) {
      reason = "active_wars_war_identity_invalid"; return false;
    }
    if (ended != 0) { ++ended_count; return true; }
    ++active_count;
    bool attacking = false, defending = false;
    if (!Side(war, 0x20, row.attacker_participant_ids, attacking) ||
        !Side(war, 0x80, row.defender_participant_ids, defending)) return false;
    if (attacking && defending) { reason = "active_wars_player_on_both_sides"; return false; }
    if (!attacking && !defending) return true;
    row.war_id = id; row.actual_player_character_id = expected.played_character_id;
    row.player_side = attacking ? ActiveWarPlayerSideV1::attacker : ActiveWarPlayerSideV1::defender;
    if (!Read(war, 0x290, row.primary_attacker_character_id) ||
        !Read(war, 0x294, row.primary_defender_character_id) ||
        !Character(row.primary_attacker_character_id, false) ||
        !Character(row.primary_defender_character_id, false)) return false;
    row.primary_opponent_character_id = attacking ? row.primary_defender_character_id :
        row.primary_attacker_character_id;
    row.player_is_primary_war_leader = (attacking ? row.primary_attacker_character_id :
        row.primary_defender_character_id) == expected.played_character_id;
    linked = true; return true;
  }
  bool ScoreGuard() const noexcept {
    std::array<std::uint8_t,32> code{};
    const auto copy = access.copy != nullptr ? access.copy : CopyLocal;
    const auto address = reinterpret_cast<std::uintptr_t>(bindings.get_attacker_war_score);
    return address != 0 && address <= (std::numeric_limits<std::uintptr_t>::max)() -
        (code.size() - 1) && copy(access.context, reinterpret_cast<const void *>(address),
        code.data(), code.size()) && code == (IsHotfix(bindings.core.image_build) ? military_hotfix26757580::kScoreEntry32 : kActiveWarsScoreEntry32V1);
  }
  bool Score(std::int32_t index, const void *war, ActiveWarIdentityRowV1 &row) {
    if (!bindings.integration_native_calls_permitted) {
      row.score_unavailable_reason = "active_wars_native_calls_not_permitted"; return true;
    }
    if (bindings.get_attacker_war_score == nullptr) {
      row.score_unavailable_reason = "active_wars_score_getter_unavailable"; return true;
    }
    const auto admit=bindings.native_call_admission;
    const auto admission_context=bindings.native_call_admission_context;
    if(IsHotfix(bindings.core.image_build) && !admit){
      row.score_unavailable_reason="active_wars_score_owner_unqualified";return true;
    }
    if (!ScoreGuard()) {
      row.score_unavailable_reason = "active_wars_score_guard_unavailable"; return true;
    }
    CoreSnapshotPrefix before_core{}, after_core{};
    if (!Core(bindings.core, before_core) || !SameCore(before_core, expected)) {
      reason = "active_wars_score_core_changed"; return false;
    }
    // Re-resolve roots, actor, exact slot, all side pointers/ordered full IDs
    // and primaries immediately before and after this particular native call.
    Pass before{bindings, expected, access, calls};
    ActiveWarIdentityRowV1 before_row{}, after_row{};
    const void *before_war = nullptr, *after_war = nullptr;
    bool before_linked = false, after_linked = false;
    if (!before.ReadRoots() || !before.ReadAt(index, before_war, before_row, before_linked)) {
      reason = before.reason; return false;
    }
    if (before.roots != roots || before_war != war || !before_linked || !SameIdentity(before_row, row)) {
      reason = "active_wars_score_identity_changed"; return false;
    }
    if (admit != nullptr && !admit(admission_context)) {
      reason = "active_wars_score_owner_changed"; return false;
    }
    std::int32_t raw = 0; ++calls;
    const bool read_score = NativeScore(bindings.get_attacker_war_score, war, raw);
    if(bindings.native_call_admission!=admit || bindings.native_call_admission_context!=admission_context ||
        (admit!=nullptr && !admit(admission_context))) {
      reason = "active_wars_score_owner_changed"; return false;
    }
    if (!Core(bindings.core, after_core) || !SameCore(after_core, expected)) {
      reason = "active_wars_score_core_changed"; return false;
    }
    Pass after{bindings, expected, access, calls};
    if (!after.ReadRoots() || !after.ReadAt(index, after_war, after_row, after_linked)) {
      reason = after.reason; return false;
    }
    if (after.roots != roots || before_war != after_war || !after_linked ||
        !SameIdentity(before_row, after_row) || before.transcript != after.transcript) {
      reason = "active_wars_score_identity_changed"; return false;
    }
    if (!read_score) { row.score_unavailable_reason = "active_wars_native_score_failed"; return true; }
    if (!ScoreGuard()) { row.score_unavailable_reason = "active_wars_score_guard_changed"; return true; }
    row.native_attacker_score_raw = raw;
    const std::int64_t relative = row.player_side == ActiveWarPlayerSideV1::attacker ?
        static_cast<std::int64_t>(raw) : -static_cast<std::int64_t>(raw);
    if (relative < (std::numeric_limits<std::int32_t>::min)() ||
        relative > (std::numeric_limits<std::int32_t>::max)()) {
      row.score_unavailable_reason = "active_wars_relative_score_overflow"; return true;
    }
    row.player_relative_war_score = static_cast<std::int32_t>(relative);
    row.score_unavailable_reason = {}; return true;
  }
  bool Capture() {
    if (!ReadRoots()) return false;
    for (std::int32_t i = 0; i < wars.capacity; ++i) {
      const void *war = nullptr; ActiveWarIdentityRowV1 row{}; bool linked = false;
      if (!ReadAt(i, war, row, linked)) return false;
      if (!linked) continue;
      if (rows.size() == kActiveWarsOwnedLimitV1) {
        reason = "active_wars_owned_scope_exceeded"; return false;
      }
      if (!Score(i, war, row)) return false;
      rows.push_back(std::move(row));
    }
    return true;
  }
};
bool ReadImpl(const ActiveWarsBindingsV1 &bindings, const CoreSnapshotPrefix &expected,
    ActiveWarsObservationV1 &out, ActiveWarsReadAccessV1 access) {
  out = {}; const auto &core = bindings.core;
  if (!bindings.exact_build_admitted || !core.enabled) return Fail(out, "unsupported_build");
  if (core.game_state_slot == nullptr || core.jomini_state_slot == nullptr ||
      core.character_storage_slot == nullptr || core.get_local_player == nullptr ||
      bindings.war_registry_slot == nullptr || bindings.war_registry_vtable == 0 ||
      bindings.war_manager_vtable == 0 || bindings.war_vtable == 0)
    return Fail(out, "active_wars_binding_unavailable");
  if (!expected.clock.paused) return Fail(out, "requires_paused");
  if (!expected.map_ready) return Fail(out, "map_not_ready");
  if (!expected.has_played_character || expected.played_character_id == -1 ||
      expected.local_player_id < 0 || !expected.played_character_alive)
    return Fail(out, "active_wars_actor_unavailable");
  CoreSnapshotPrefix first{}, middle{}, last{};
  if (!Core(core, first)) return Fail(out, "core_read_failed");
  if (!SameCore(first, expected)) return Fail(out, "core_frame_changed");
  Pass before{bindings, expected, access, out.native_score_calls_attempted};
  if (!before.Capture()) return Fail(out, before.reason);
  if (!Core(core, middle)) return Fail(out, "core_read_failed");
  if (!SameCore(middle, first)) return Fail(out, "core_frame_changed");
  Pass after{bindings, expected, access, out.native_score_calls_attempted};
  if (!after.Capture()) return Fail(out, after.reason);
  if (!Core(core, last)) return Fail(out, "core_read_failed");
  if (!SameCore(last, first)) return Fail(out, "core_frame_changed");
  if (before.transcript != after.transcript || before.rows.size() != after.rows.size())
    return Fail(out, "active_wars_identity_changed");
  out.score_complete = true;
  for (std::size_t i = 0; i < before.rows.size(); ++i) {
    auto &a = before.rows[i]; const auto &b = after.rows[i];
    if (!SameIdentity(a, b)) return Fail(out, "active_wars_identity_changed");
    if (a.native_attacker_score_raw != b.native_attacker_score_raw ||
        a.player_relative_war_score != b.player_relative_war_score ||
        a.score_unavailable_reason != b.score_unavailable_reason) {
      a.native_attacker_score_raw.reset(); a.player_relative_war_score.reset();
      a.score_unavailable_reason = "active_wars_score_changed";
    }
    out.score_complete = out.score_complete && a.player_relative_war_score.has_value();
  }
  out.available = out.same_frame_ready = out.identity_complete = true;
  out.frame = last; out.active_wars = std::move(before.rows);
  out.war_slots_scanned = before.wars.capacity;
  out.active_war_rows = before.active_count; out.ended_war_rows = before.ended_count;
  out.participant_records = before.participants; out.unavailable_reason = {};
  return true;
}
} // namespace
ActiveWarsBindingsV1 BindActiveWarsImageV1(std::uintptr_t base, std::string_view sha) noexcept {
  ActiveWarsBindingsV1 out{};
  const auto build=ImageBuildForSha(sha);
  const auto registry=ImageRva(build,kActiveWarsRegistryRvaV1,military_hotfix26757580::kWarRegistry);
  const auto top=registry+sizeof(void*)-1;
  if (base == 0 || build == ImageBuildV1::unknown ||
      base > (std::numeric_limits<std::uintptr_t>::max)() - top) return out;
  out.core = BindCoreImage(base, sha); if (!out.core.enabled) return {};
  out.war_registry_slot = reinterpret_cast<void **>(base + registry);
  out.war_registry_vtable = base + ImageRva(build,kActiveWarsRegistryVtableRvaV1,military_hotfix26757580::kWarRegistryVt);
  out.war_manager_vtable = base + ImageRva(build,kActiveWarsManagerVtableRvaV1,military_hotfix26757580::kWarManagerVt);
  out.war_vtable = base + ImageRva(build,kActiveWarsWarVtableRvaV1,military_hotfix26757580::kWarVt);
  out.get_attacker_war_score = reinterpret_cast<ActiveWarsNativeScoreGetterV1>(base + ImageRva(build,kActiveWarsScoreRvaV1,military_hotfix26757580::kWarScore));
  out.exact_build_admitted = true; return out;
}
bool ReadActiveWarsV1(const ActiveWarsBindingsV1 &bindings, const CoreSnapshotPrefix &expected,
    ActiveWarsObservationV1 &out, ActiveWarsReadAccessV1 access) noexcept {
  try { return ReadImpl(bindings, expected, out, access); }
  catch (...) { return Fail(out, "active_wars_allocation_or_internal_error"); }
}
} // namespace xar::ck3_1210
