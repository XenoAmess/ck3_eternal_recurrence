#include "xar_bridge/camera_follow_readonly_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"
#include "xar_bridge/ck3_12004_tactical_daily_sentinel.hpp"
#include "xar_bridge/ck3_12004_modal_choice_port_v1.hpp"
#include <cstddef>
#include <windows.h>

namespace xar::presentation::tracked {
namespace {
using Address = std::uintptr_t;
bool Continue(ContinueRead callback, void *context, Frame &out) noexcept {
  if (callback == nullptr || callback(context)) return true;
  out.reason = Failure::cooperative_yield;
  out.complete = false;
  out.ui_clear = false;
  return false;
}
bool Copy(Address address, void *out, std::size_t size) noexcept {
  SIZE_T copied = 0;
  return address != 0 && out != nullptr && size != 0 &&
      ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<void *>(address),
          out, size, &copied) != FALSE && copied == size;
}
template<class T> bool Get(Address object, std::size_t offset, T &out) noexcept {
  return object != 0 && object + offset >= object &&
      Copy(object + offset, &out, sizeof(out));
}
#if !defined(XAR_CAMERA_FOLLOW_READONLY_PENDING_FIXTURE)
Address Component(void **slot, std::int32_t id, std::size_t id_offset) noexcept {
  Address storage = 0, slots = 0, object = 0;
  std::int32_t capacity = 0, actual = -1;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (id == -1 || !Get(reinterpret_cast<Address>(slot), 0, storage) ||
      !Get(storage, 0x20, slots) || !Get(storage, 0x2C, capacity) ||
      capacity <= 0 || capacity > 1000000 ||
      index >= static_cast<std::uint32_t>(capacity) ||
      !Get(slots, index * 0x10ULL + 8, object) ||
      !Get(object, id_offset, actual) || actual != id) return 0;
  return object;
}
// Actual .4 province collector: GameData+140/14C, Province ID+10/tag+85C.
bool Province(Address game, Address province, std::int32_t &id) noexcept {
  Address data = 0, array = 0, roundtrip = 0;
  std::int32_t count = 0;
  std::uint32_t tag = 0;
  return Get(province, 0x10, id) && id > 0 &&
      Get(province, 0x85C, tag) && tag == 0x50726F76U &&
      Get(game, 0xA0, data) && Get(data, 0x140, array) &&
      Get(data, 0x14C, count) && count > id &&
      Get(array, static_cast<std::size_t>(id) * 8, roundtrip) &&
      roundtrip == province;
}
#endif
// The source storage is a high-water slot table, not an active vector. Scan all
// admitted slots, including holes. Above this safety budget is UNKNOWN, never
// an empty list. Actual ordinary-game capacity/latency remain unqualified.
template<class Read, class Pending, class Validate>
bool PendingClear(Address storage, std::int32_t actor, Address character,
    Read read, Pending is_pending, Validate validate, Frame &out,
    Address primary, Address secondary, ContinueRead continue_read = nullptr,
    void *context = nullptr) noexcept {
  Address slots = 0;
  std::int32_t capacity = -1;
  out.reason = Failure::pending_storage_read;
  if (!read(storage, 0x20, slots) || !read(storage, 0x2C, capacity)) return false;
  out.pending_slot_capacity = capacity;
  out.reason = Failure::pending_capacity;
  if (capacity < 0 || capacity > kMaximumPendingSlotsPerRead ||
      (capacity != 0 && slots == 0)) return false;
  out.reason = Failure::pending_slot_read;
  for (std::int32_t index = 0; index < capacity; ++index) {
    if (index % 32 == 0 && !Continue(continue_read, context, out)) return false;
    ++out.pending_slots_visited;
    Address item = 0;
    std::int32_t id = -1, kind = -1, recipient = -1;
    if (!read(slots, static_cast<std::size_t>(index) * 0x10 + 8, item)) return false;
    if (item == 0) continue;
    if (!read(item, 0x10, id)) return false;
    if (id == -1 || (static_cast<std::uint32_t>(id) & 0xFFFFFFU) !=
        static_cast<std::uint32_t>(index)) continue;
    if (!read(item, 0x5C0, kind)) return false;
    if (kind != 0 && kind != 1 && kind != 2) continue;
    if (!read(item, kind == 1 ? 0x300 : 0x2F4, recipient)) return false;
    if (recipient != actor || !is_pending(item, character)) continue;
    std::uint8_t notification = 0;
    if (!read(item, 0x5C6, notification)) return false;
    if (notification == 0) {
      ck3_12002::EventCommand command{};
      command.primary_vtable = primary;
      command.secondary_vtable = secondary;
      command.instance_id = id;
      command.choice = 0;
      if (!validate(&command)) continue;
    }
    out.reason = Failure::pending_present;
    return false; // A real ordinary interaction/notification preempts tracking.
  }
  Address after_slots = 0;
  std::int32_t after_capacity = -1;
  out.reason = Failure::pending_storage_changed;
  return read(storage, 0x20, after_slots) && slots == after_slots &&
      read(storage, 0x2C, after_capacity) && capacity == after_capacity;
}
#if !defined(XAR_CAMERA_FOLLOW_READONLY_PENDING_FIXTURE)
bool ReadImpl(Address base, std::string_view sha, const Request &q, Frame &out,
    ContinueRead continue_read, void *context) {
  if (!Continue(continue_read, context, out)) return false;
  out.reason = Failure::invalid_request;
  if (base == 0 || sha != ck3_12004::kExecutableSha256 || q.actor < 0 ||
      q.fullarmy_id == -1 || q.scope_generation == 0 ||
      q.start_date_raw <= 0 || q.max_date_raw < q.start_date_raw) return false;
  const auto core = ck3_12004::BindCoreImage(base, sha);
  ck3_12004::CoreSnapshotPrefix before{};
  out.reason = Failure::core_read;
  if (!core.enabled || !ck3_12004::ReadCoreSnapshot(core, before)) return false;
  out.actor = before.played_character_id;
  out.date_raw = before.clock.date_raw;
  out.paused = before.clock.paused;
  out.alive = before.played_character_alive;
  out.map_ready = before.map_ready;
  out.reason = Failure::actor_or_date;
  if (!out.map_ready || !before.has_played_character || !out.alive ||
      out.actor != q.actor || out.date_raw < q.start_date_raw ||
      out.date_raw > q.max_date_raw) return false;
  const auto scope = ck3_11906::ReadTacticalDailySentinelStatusV1();
  out.reason = Failure::clock_scope;
  out.scope_generation = scope.generation;
  out.scope_start_date_raw = scope.starting_date_raw;
  out.scope_target_date_raw = scope.target_date_raw;
  out.scope_armed = scope.state == ck3_11906::TacticalDailySentinelStateV1::armed;
  if (!out.scope_armed || scope.generation != q.scope_generation ||
      scope.starting_date_raw != q.start_date_raw ||
      scope.target_date_raw != q.max_date_raw || scope.abnormal) return false;
  const auto units = ck3_12004::BindTacticalDailySentinelImage12004(base, sha);
  out.reason = Failure::army_identity;
  Address game = 0;
  if (!units.enabled || !Get(reinterpret_cast<Address>(core.game_state_slot), 0, game))
    return false;
  const auto unit = Component(units.army_storage_slot, q.fullarmy_id, 0x10);
  std::int32_t kind = -1, internal_id = -1, backref = -1, retreat = 0;
  Address province = 0;
  if (!Get(unit, 0x18, kind) || kind != 0 ||
      !Get(unit, 0x174, out.subject_owner) || out.subject_owner != q.actor ||
      !Get(unit, 0x178, internal_id) || !Get(unit, 0x20, province) ||
      !Get(unit, 0x170, retreat) || !Province(game, province, out.current_province_id))
    return false;
  const auto army = Component(units.army_internal_storage_slot, internal_id, 0x10);
  if (!Get(army, 0x124, backref) || backref != q.fullarmy_id ||
      !Get(army, 0x128, out.combat_id)) return false;
  out.full_id_valid = true;
  out.retreating = retreat > 0;
  out.reason = Failure::combat_or_position;
  if (out.combat_id != -1) {
    const auto combat = Component(units.combat_storage_slot, out.combat_id, 8);
    Address battle_province = 0;
    std::uint8_t finalized = 0, updating = 0;
    std::int32_t phase = -1;
    if (!Get(combat, 0x6B0, phase) || phase < 0 || phase > 3 ||
        !Get(combat, 0x704, finalized) || finalized != 0 ||
        !Get(combat, 0x705, updating) || updating != 0 ||
        !Get(combat, 0x6B8, battle_province) ||
        !Province(game, battle_province, out.battle_province_id)) return false;
  }
  auto environment = ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(
      base, true, ck3_11906::GuiAbiRevisionV1::crozier12004, sha);
  const auto modal = mandatory_choice_v1::ReadTopExclusiveModalHint12004V1(
      environment, 0);
  out.reason = Failure::modal_not_clear;
  if (modal.status != mandatory_choice_v1::ModalHintStatus::absent) return false;
  const auto events = ck3_12004::BindSnapshotEventsImage(base, sha);
  Address data = 0;
  out.reason = Failure::event_not_clear;
  if (!events.get_current_event || !Get(game, 0xA0, data) || data == 0 ||
      events.get_current_event(reinterpret_cast<void *>(data +
          ck3_12004::kEventManagerOffset12004)) != nullptr) return false;
  const auto actor = reinterpret_cast<Address>(ck3_12004::ResolveCoreCharacter(core, q.actor));
  Address pending_storage = 0;
  out.reason = Failure::pending_binding;
  if (actor == 0 || !events.is_pending_for_character || !events.validate_reply ||
      !Get(reinterpret_cast<Address>(events.pending_interaction_storage_slot), 0,
          pending_storage)) return false;
  const auto read = [](Address p, std::size_t o, auto &v) noexcept { return Get(p, o, v); };
  if (!PendingClear(pending_storage, q.actor, actor, read,
      [&](Address p, Address c) { return events.is_pending_for_character(
          reinterpret_cast<void *>(p), reinterpret_cast<void *>(c)); },
      [&](ck3_12002::EventCommand *c) { return events.validate_reply(c); }, out,
      events.reply_primary_vtable, events.reply_secondary_vtable,
      continue_read, context)) return false;
  ck3_12004::CoreSnapshotPrefix after{};
  out.reason = Failure::final_identity;
  const auto end_scope = ck3_11906::ReadTacticalDailySentinelStatusV1();
  std::int32_t end_owner = -1, end_combat = -1;
  Address end_province = 0, end_game = 0;
  if (!ck3_12004::ReadCoreSnapshot(core, after) || !after.map_ready ||
      !after.has_played_character || !after.played_character_alive ||
      after.played_character_id != q.actor || after.local_player_id != before.local_player_id ||
      after.clock.date_raw != out.date_raw || after.clock.paused != out.paused ||
      end_scope.generation != scope.generation || end_scope.state != scope.state ||
      end_scope.starting_date_raw != scope.starting_date_raw ||
      end_scope.target_date_raw != scope.target_date_raw || end_scope.abnormal ||
      !Get(reinterpret_cast<Address>(core.game_state_slot), 0, end_game) || game != end_game ||
      Component(units.army_storage_slot, q.fullarmy_id, 0x10) != unit ||
      Component(units.army_internal_storage_slot, internal_id, 0x10) != army ||
      !Get(unit, 0x174, end_owner) || end_owner != q.actor ||
      !Get(unit, 0x20, end_province) || end_province != province ||
      !Get(army, 0x128, end_combat) || end_combat != out.combat_id) return false;
  if (!Continue(continue_read, context, out)) return false;
  out.ui_clear = true;
  out.complete = true;
  out.reason = Failure::none;
  return true;
}
// Keep SEH in a leaf without C++ objects requiring unwinding (MSVC C2712).
bool GuardedRead(Address base, std::string_view sha, const Request &q, Frame &out,
    ContinueRead continue_read, void *context) {
#if defined(_MSC_VER)
  __try { return ReadImpl(base, sha, q, out, continue_read, context); }
  __except (EXCEPTION_EXECUTE_HANDLER) {
    out.reason = Failure::fault_or_exception;
    return false;
  }
#else
  return ReadImpl(base, sha, q, out, continue_read, context);
#endif
}
#endif
} // namespace
#if !defined(XAR_CAMERA_FOLLOW_READONLY_PENDING_FIXTURE)
bool ReadTrackedSubject12004V1(Address base, std::string_view sha,
    const Request &request, Frame &frame, ContinueRead continue_read,
    void *context) noexcept {
  frame = {};
  LARGE_INTEGER frequency{}, started{}, finished{};
  const bool clock = QueryPerformanceFrequency(&frequency) != FALSE &&
      frequency.QuadPart > 0 && QueryPerformanceCounter(&started) != FALSE;
  bool complete = false;
  try {
    complete = GuardedRead(base, sha, request, frame, continue_read, context);
  } catch (...) { frame.reason = Failure::fault_or_exception; }
  if (clock && QueryPerformanceCounter(&finished) != FALSE &&
      finished.QuadPart >= started.QuadPart) {
    const auto delta = static_cast<std::uint64_t>(finished.QuadPart - started.QuadPart);
    if (delta <= (~std::uint64_t{0}) / 1000000)
      frame.elapsed_us = delta * 1000000 / static_cast<std::uint64_t>(frequency.QuadPart);
  }
  if (!complete) { frame.complete = false; frame.ui_clear = false; }
  return complete;
}
#endif
} // namespace xar::presentation::tracked
