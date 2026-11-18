#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_1210_army_base_v1.hpp"
#include <limits>
#include <optional>
#include <type_traits>

namespace xar::ck3_1210 {
// UnitState D39173 calls bool(CArmy*) 28FE540. The complete leaf through
// 28FE590 resolves CArmy+128 via 6A66718 and checks Combat fullID+8/tag+C.
inline constexpr std::uintptr_t kBattleCandidateCombatRegistryRvaV1 = 0x6A66718;
inline constexpr std::uintptr_t kBattleCandidateNativePredicateRvaV1 = 0x28FE540;
// Evidence only. Unresolved IDs never use the native fallback as absence.
inline constexpr std::uintptr_t kBattleCandidateFallbackRvaV1 = 0x6A666B0;
struct BattleCandidateBindingsV1 {
  bool exact_build_admitted = false;
  void **unit_registry_slot = nullptr;
  void **army_registry_slot = nullptr;
  void **combat_registry_slot = nullptr;
};
inline BattleCandidateBindingsV1 BindBattleCandidateImageV1(
    std::uintptr_t base, std::string_view sha) noexcept {
  if (base == 0 || sha != kExecutableSha256 ||
      base > (std::numeric_limits<std::uintptr_t>::max)() -
          kPlayerArmyUnitRegistryRvaV1 - (sizeof(void *) - 1)) return {};
  return {true,
      reinterpret_cast<void **>(base + kPlayerArmyUnitRegistryRvaV1),
      reinterpret_cast<void **>(base + kArmyBaseNativeRegistryRvaV1),
      reinterpret_cast<void **>(base + kBattleCandidateCombatRegistryRvaV1)};
}
using BattleCandidateCopyV1 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
// Owning caller proves the expected actor, paused frame and main custody
// throughout this call. Exact image admission alone cannot establish custody.
using BattleCandidateSamePausedFrameV1 = bool (*)(void *) noexcept;
struct BattleCandidateAccessV1 {
  void *context = nullptr;
  BattleCandidateCopyV1 copy = nullptr;
  BattleCandidateSamePausedFrameV1 same_paused_frame = nullptr;
};
enum class BattleCandidateStatusV1 { unavailable, not_referenced, identity_candidate };
struct BattleCandidateObservationV1 {
  BattleCandidateStatusV1 status = BattleCandidateStatusV1::unavailable;
  std::int32_t subject_public_cunit_id = -1;
  std::int32_t source_native_carmy_id = -1;
  std::optional<std::int32_t> candidate_combat_id;
};
namespace battle_candidate_detail_v1 {
struct Registry {
  const void *root = nullptr, *rows = nullptr;
  std::int32_t capacity = 0;
  friend bool operator==(const Registry &, const Registry &) = default;
};
struct Sample {
  Registry units{}, armies{}, combats{};
  const void *unit = nullptr, *army = nullptr, *combat = nullptr;
  std::int32_t unit_id = -1, owner = -1, army_ref = -1, army_id = -1;
  std::int32_t unit_backlink = -1, combat_ref = -1, combat_id = -1;
  std::uint32_t unit_tag = 0, army_tag = 0, combat_tag = 0;
  BattleCandidateStatusV1 status = BattleCandidateStatusV1::unavailable;
  friend bool operator==(const Sample &, const Sample &) = default;
};
struct Reader {
  const BattleCandidateBindingsV1 &bindings;
  BattleCandidateAccessV1 access;
  template <class T> bool Read(const void *base, std::size_t offset, T &value) noexcept {
    static_assert(std::is_trivially_copyable_v<T> && sizeof(T) <= 8);
    const auto address = reinterpret_cast<std::uintptr_t>(base);
    const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
    if (address == 0 || offset > maximum - address ||
        sizeof(T) - 1 > maximum - address - offset) return false;
    return access.copy(access.context,
        reinterpret_cast<const void *>(address + offset), &value, sizeof(T));
  }
  bool Header(void **slot, Registry &out) noexcept {
    if (!Read(slot, 0, out.root) || out.root == nullptr ||
        !Read(out.root, 0x20, out.rows) || !Read(out.root, 0x2C, out.capacity))
      return false;
    return out.capacity >= 0 && out.capacity <= kPlayerArmyStorageLimitV1 &&
        (out.capacity == 0 || out.rows != nullptr);
  }
  bool Resolve(const Registry &storage, std::int32_t full_id,
      std::size_t identity_offset, const void *&object, std::int32_t &identity,
      std::uint32_t &tag) noexcept {
    // -1 alone is sentinel; ID zero and high-bit generations remain valid.
    const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
    if (full_id == -1 || index >= static_cast<std::uint32_t>(storage.capacity) ||
        !Read(storage.rows, static_cast<std::size_t>(index) * 0x10 + 8, object) ||
        object == nullptr || !Read(object, identity_offset, identity) ||
        !Read(object, identity_offset + 4, tag)) return false;
    return identity == full_id;
  }
  bool Capture(std::int32_t unit_id, std::int32_t actor_id, Sample &out) noexcept {
    if (!Header(bindings.unit_registry_slot, out.units) ||
        !Resolve(out.units, unit_id, 0x10, out.unit, out.unit_id, out.unit_tag) ||
        out.unit_tag != 0x556E6974U || !Read(out.unit, 0x174, out.owner) ||
        out.owner != actor_id || !Read(out.unit, 0x178, out.army_ref) ||
        !Header(bindings.army_registry_slot, out.armies) ||
        !Resolve(out.armies, out.army_ref, 0x10, out.army, out.army_id, out.army_tag) ||
        out.army_tag != 0x41726D79U || !Read(out.army, 0x124, out.unit_backlink) ||
        out.unit_backlink != unit_id || !Read(out.army, 0x128, out.combat_ref)) return false;
    if (out.combat_ref == -1) {
      // Field sentinel only: no claim of list completeness or no-battle state.
      out.status = BattleCandidateStatusV1::not_referenced; return true;
    }
    if (!Header(bindings.combat_registry_slot, out.combats) ||
        !Resolve(out.combats, out.combat_ref, 8, out.combat, out.combat_id, out.combat_tag) ||
        out.combat_tag != 0x436F6D62U) return false;
    out.status = BattleCandidateStatusV1::identity_candidate; return true;
  }
};
} // namespace battle_candidate_detail_v1

// Memory-only candidate identity: no default memcpy and no native call.
// Manager ownership, complete lists, side membership, phase/daily/finalized
// lifecycle and result remain unproven. Never grants BattleControl/Transition
// ready, adapter capabilities, command admission, Installed or live credit.
inline bool ReadBattleCandidateV1(const BattleCandidateBindingsV1 &bindings,
    std::int32_t unit_id, std::int32_t expected_actor_id,
    BattleCandidateObservationV1 &output, BattleCandidateAccessV1 access) noexcept {
  output = {};
  if (!bindings.exact_build_admitted || access.copy == nullptr ||
      access.same_paused_frame == nullptr || unit_id == -1 || expected_actor_id == -1 ||
      !access.same_paused_frame(access.context)) return false;
  battle_candidate_detail_v1::Reader reader{bindings, access};
  battle_candidate_detail_v1::Sample first{}, second{};
  if (!reader.Capture(unit_id, expected_actor_id, first) ||
      !access.same_paused_frame(access.context) ||
      !reader.Capture(unit_id, expected_actor_id, second) ||
      first != second || !access.same_paused_frame(access.context)) return false;
  output.status = second.status;
  output.subject_public_cunit_id = second.unit_id;
  output.source_native_carmy_id = second.army_id;
  if (second.status == BattleCandidateStatusV1::identity_candidate)
    output.candidate_combat_id = second.combat_id;
  return true;
}
} // namespace xar::ck3_1210
