#include "xar_bridge/ck3_12002_sway_state.hpp"
#include "xar_bridge/ck3_12002_gift_opinion.hpp"

#include <cstring>
#include <limits>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
using namespace bridge;
bool Copy(std::uintptr_t address, void *out, std::size_t size) noexcept {
  if (!address || !out) return false;
  __try { std::memcpy(out, reinterpret_cast<const void *>(address), size); return true; }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
template <typename T> bool Read(std::uintptr_t at, T &out) noexcept {
  return Copy(at, &out, sizeof(out));
}
std::uint64_t Hash(std::uint64_t hash, std::uint64_t value) noexcept {
  for (int i = 0; i < 8; ++i) { hash ^= value & 255; hash *= 1099511628211ULL; value >>= 8; }
  return hash;
}
bool Key(std::uintptr_t type, std::array<char, 96> &out) noexcept {
  std::uint64_t size{}, capacity{};
  std::uintptr_t text = type + 0x18;
  if (!Read(text + 0x10, size) || !Read(text + 0x18, capacity) ||
      size == 0 || size >= out.size() || capacity < size) return false;
  if (capacity >= 16 && !Read(text, text)) return false;
  out = {};
  return Copy(text, out.data(), static_cast<std::size_t>(size));
}
bool ReadOnce(const SwayStateBindings12002 &b, std::uint64_t epoch,
              ActiveSchemeStateV1PrivateObservation &out) noexcept {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.core, frame) || !frame.clock.paused ||
      !frame.map_ready || !frame.played_character_alive || frame.played_character_id <= 0)
    return false;
  std::uintptr_t state{}, data{}, storage{}, vt{}, blocks{}, slots{};
  std::int32_t capacity{}, count{};
  if (!Read(reinterpret_cast<std::uintptr_t>(b.core.game_state_slot), state) ||
      !Read(state + 0xA0, data) || !data ||
      !Read(data + b.manager_offset, vt) || vt != b.module_base + b.manager_vtable_rva ||
      !Read(data + b.manager_offset + 0x20, storage) || !storage ||
      !Read(storage, vt) || vt != b.module_base + b.storage_vtable_rva ||
      !Read(storage + 8, blocks) || !Read(storage + 0x20, slots) ||
      !Read(storage + 0x2C, capacity) || !Read(storage + 0x3C, count) ||
      capacity < 0 || capacity > 0x1000000 || count < 0 || count > capacity ||
      (capacity && (!blocks || !slots))) return false;
  out = {};
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  auto generation = Hash(14695981039346656037ULL, frame.played_character_id);
  std::int32_t enumerated = 0;
  for (std::int32_t i = 0; i < capacity; ++i) {
    std::uintptr_t scheme{}, block{};
    if (!Read(slots + static_cast<std::size_t>(i) * 16 + 8, scheme)) return false;
    if (!scheme) continue;
    ++enumerated;
    std::uint32_t id{}, owner{};
    if (!Read(blocks + (static_cast<std::uint32_t>(i) >> 10) * sizeof(void *), block) ||
        scheme != block + (static_cast<std::uint32_t>(i) & 0x3FF) * 0x358 ||
        !Read(scheme, vt) || vt != b.module_base + b.instance_vtable_rva ||
        !Read(scheme + 0x10, id) || (id & 0xFFFFFF) != static_cast<std::uint32_t>(i) ||
        id == 0xFFFFFFFF || !Read(scheme + 0x2C, owner)) return false;
    if (owner != static_cast<std::uint32_t>(frame.played_character_id)) continue;
    if (out.row_count >= out.rows.size()) return false;
    auto &row = out.rows[out.row_count++];
    row.scheme_instance_id = id;
    row.scheme_instance_generation = id >> 24;
    row.owner_character_id = owner;
    generation = Hash(generation, id);
    std::uintptr_t type{};
    if (!Read(scheme + 0x20, type) || !type || !Read(type, vt) ||
        vt != b.module_base + b.type_vtable_rva || !Key(type, row.scheme_type_key)) return false;
    if (std::strcmp(row.scheme_type_key.data(), "sway") != 0) continue;
    std::uint32_t kind{}, target{}, magic{};
    std::uint8_t basic{}, exposed{}, frozen{};
    std::int32_t progress{}, goal{};
    if (!Read(type + 0x38, magic) || magic != 0x4744624F ||
        !Read(type + 0xA4E, basic) || basic != 1 ||
        !Read(scheme + 0x30, kind) || kind != 0 ||
        !Read(scheme + 0x34, target) || !ResolveCoreCharacter(b.core, static_cast<std::int32_t>(target)) ||
        !Read(scheme + 0x78, progress) || !Read(scheme + 0x350, goal) ||
        progress < 0 || goal <= 0 || progress > goal ||
        !Read(scheme + 0x27C, exposed) || exposed > 1 ||
        !Read(scheme + 0x2A8, frozen) || frozen > 1) return false;
    std::memcpy(row.category_key.data(), "personal", 9);
    row.target_kind = ActiveSchemeStateV1PrivateTargetKind::character;
    row.target_id = target;
    row.is_basic = true;
    row.is_secret = false; // Frozen stock Sway definition is non-secret.
    row.is_exposed = exposed != 0;
    row.is_frozen = frozen != 0;
    row.progress = {ActiveSchemeStateV1PrivateValueStatus::available, progress};
    row.progress_goal = {ActiveSchemeStateV1PrivateValueStatus::available, goal};
    const ActiveSchemeStateV1PrivateValue<std::int32_t> na{
        ActiveSchemeStateV1PrivateValueStatus::not_applicable, 0};
    row.success_chance = row.maximum_success_chance = row.secrecy = na;
    row.opportunity_charges = row.breaches = row.maximum_breaches = na;
    row.phases_remaining_until_opportunity = na;
  }
  if (enumerated != count) return false;
  out.container_generation = Hash(generation, out.row_count);
  if (!out.container_generation) out.container_generation = 1;
  out.status = ActiveSchemeStateV1PrivateStatus::available;
  out.unavailable_reason = ActiveSchemeStateV1PrivateFailure::none;
  return true;
}
bool Same(const ActiveSchemeStateV1PrivateObservation &a,
          const ActiveSchemeStateV1PrivateObservation &b) noexcept {
  if (a.date_raw != b.date_raw || a.played_character_id != b.played_character_id ||
      a.container_generation != b.container_generation || a.row_count != b.row_count) return false;
  for (std::size_t i = 0; i < a.row_count; ++i) {
    const auto &x = a.rows[i]; const auto &y = b.rows[i];
    if (x.scheme_instance_id != y.scheme_instance_id || x.owner_character_id != y.owner_character_id ||
        x.scheme_type_key != y.scheme_type_key || x.target_kind != y.target_kind || x.target_id != y.target_id ||
        x.is_exposed != y.is_exposed || x.is_frozen != y.is_frozen ||
        x.progress.value != y.progress.value || x.progress_goal.value != y.progress_goal.value) return false;
  }
  return true;
}
bool OpinionCall(SwayReadOpinion12002 fn, void *owner, void *toward,
                 std::int32_t &out) noexcept {
  __try { out = fn(owner, toward); return true; }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
} // namespace

SwayStateBindings12002 BindSwayStateImage12002(std::uintptr_t base,
    std::string_view sha) noexcept {
  SwayStateBindings12002 b{};
  b.core = BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  b.enabled = true; b.module_base = base;
  // The shared recipient-opinion reader owns this build's exact native call.
  return b;
}
bool ReadActiveSwayState12002(const SwayStateBindings12002 &b,
    std::uint64_t epoch, bridge::ActiveSchemeStateV1PrivateObservation &output) noexcept {
  output = {};
  if (!b.enabled || !b.core.enabled || !b.module_base || !epoch) return false;
  bridge::ActiveSchemeStateV1PrivateObservation first{}, second{};
  if (!ReadOnce(b, epoch, first) || !ReadOnce(b, epoch, second) || !Same(first, second)) return false;
  output = second; return true;
}
bool ReadSwayTargetOpinion12002(const SwayStateBindings12002 &b,
    std::int64_t actor, std::uint32_t target, std::int32_t &output) noexcept {
  output = 0;
  if (!b.enabled || !b.core.enabled || actor <= 0 || actor > INT32_MAX || !target) return false;
  if (!b.opinion) return ReadCharacterOpinion12002(b.module_base, b.core, target,
      static_cast<std::uint32_t>(actor), output);
  auto *owner = ResolveCoreCharacter(b.core, static_cast<std::int32_t>(target));
  auto *toward = ResolveCoreCharacter(b.core, static_cast<std::int32_t>(actor));
  if (!owner || !toward || !OpinionCall(b.opinion, owner, toward, output)) return false;
  return output >= -100 && output <= 100 &&
      ResolveCoreCharacter(b.core, static_cast<std::int32_t>(target)) == owner &&
      ResolveCoreCharacter(b.core, static_cast<std::int32_t>(actor)) == toward;
}
} // namespace xar::ck3_12002
