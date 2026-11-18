#pragma once
#include "xar_bridge/ck3_1210_adapter.hpp"
#include <limits>
#include <type_traits>

namespace xar::ck3_1210 {
// Private source boundary, not an identity issuer or a new execution scope.
// descriptor comes from the selected native adapter; core is its exact bundle.
// The owner reuses its existing Core identity/custody validator in access.
struct Scoped1210ImageSourceV1 {
  std::uintptr_t image_base = 0;
  const game::AdapterDescriptor *descriptor = nullptr;
  CoreBindings core{};
};
struct Scoped1210SourceAccessV1 {
  void *context = nullptr;
  bool (*copy)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  // Must establish the current actual actor, expected frame and application-
  // main custody AND bind this source to the actual current module/MQ/TLS.
  // Repeated equal bytes or a correct descriptor alone provide no authority.
  bool (*validate_core_identity)(void *, const Scoped1210ImageSourceV1 &,
      const CoreSnapshotPrefix &) noexcept = nullptr;
};
struct Scoped1210ImageRootsV1 {
  std::uintptr_t image_base = 0, game = 0, jomini = 0, data = 0, characters = 0;
  friend bool operator==(const Scoped1210ImageRootsV1 &,
      const Scoped1210ImageRootsV1 &) = default;
};
enum class Scoped1210ManagerKindV1 { unit, war, siege, council_task, character };
struct Scoped1210ManagerRootsV1 {
  Scoped1210ImageRootsV1 image{};
  Scoped1210ManagerKindV1 kind = Scoped1210ManagerKindV1::unit;
  std::uintptr_t manager = 0, registry = 0;
  // Only CharacterManager's maintained vector has this different shape.
  std::uintptr_t character_members = 0;
  std::int32_t character_member_count = 0;
  friend bool operator==(const Scoped1210ManagerRootsV1 &,
      const Scoped1210ManagerRootsV1 &) = default;
};
namespace scoped1210_source_detail_v1 {
inline bool Address(std::uintptr_t base, std::size_t offset,
    std::size_t size, std::uintptr_t &out) noexcept {
  out = 0;
  const auto max = (std::numeric_limits<std::uintptr_t>::max)();
  if (base == 0 || size == 0 || offset > max - base ||
      size - 1 > max - (base + offset)) return false;
  out = base + offset;
  return true;
}
template <class T>
inline bool Read(const Scoped1210SourceAccessV1 &a, std::uintptr_t base,
    std::size_t offset, T &out) noexcept {
  static_assert(std::is_trivially_copyable_v<T> && sizeof(T) <= 8);
  std::uintptr_t address = 0;
  return a.copy != nullptr && Address(base, offset, sizeof(T), address) &&
      a.copy(a.context, reinterpret_cast<const void *>(address), &out, sizeof(T));
}
inline bool Binding(const Scoped1210ImageSourceV1 &s) noexcept {
  // Compare the complete existing binder result. A caller's bool, relocated
  // vtable or one matching RVA alone cannot qualify this source.
  if (s.image_base == 0 || s.descriptor == nullptr ||
      !game::IsCk3_1210Descriptor(*s.descriptor)) return false;
  std::uintptr_t last = 0;
  if (!Address(s.image_base, kJominiStateSlotRva, sizeof(void *), last)) return false;
  const auto exact = BindCoreImage(s.image_base, s.descriptor->executable_sha256);
  return s.core.enabled && exact.enabled &&
      s.core.game_state_slot == exact.game_state_slot &&
      s.core.jomini_state_slot == exact.jomini_state_slot &&
      s.core.character_storage_slot == exact.character_storage_slot &&
      s.core.get_local_player == exact.get_local_player;
}
inline bool Capture(const Scoped1210ImageSourceV1 &s,
    const Scoped1210SourceAccessV1 &a, Scoped1210ImageRootsV1 &out) noexcept {
  if (!Binding(s)) return false;
  out.image_base = s.image_base;
  return Read(a, s.image_base, kGameStateSlotRva, out.game) && out.game != 0 &&
      Read(a, s.image_base, kJominiStateSlotRva, out.jomini) && out.jomini != 0 &&
      Read(a, s.image_base, kCharacterStorageSlotRva, out.characters) && out.characters != 0 &&
      Read(a, out.game, kGameStateDataOffset, out.data) && out.data != 0;
}
inline bool Manager(const Scoped1210SourceAccessV1 &a,
    Scoped1210ManagerKindV1 kind, Scoped1210ManagerRootsV1 &out) noexcept {
  // Every choice is an independently evidenced actual1210 source. There is
  // deliberately no configurable layout or unproved Combat/Province manager.
  std::size_t offset = 0, owned_offset = 0x20;
  std::uintptr_t manager_vt = 0, registry_slot = 0, registry_vt = 0;
  switch (kind) {
  case Scoped1210ManagerKindV1::unit:
    offset = 0x3ABF8; manager_vt = 0x4EA4090;
    registry_slot = 0x6A667A8; registry_vt = 0x4EA40C8; break;
  case Scoped1210ManagerKindV1::war:
    offset = 0x3F2D8; manager_vt = 0x4E9C2C0;
    registry_slot = 0x6A666D0; registry_vt = 0x4E9C188; break;
  case Scoped1210ManagerKindV1::siege:
    offset = 0x3F130; manager_vt = 0x4E4B000; owned_offset = 0x28;
    registry_slot = 0x6A67198; registry_vt = 0x4E4AE18; break;
  case Scoped1210ManagerKindV1::council_task:
    offset = 0x1EFA0; manager_vt = 0x4EA0060;
    registry_slot = 0x6A666F8; registry_vt = 0x4EA0110; break;
  case Scoped1210ManagerKindV1::character:
    offset = 0x3F540; manager_vt = 0x4E83550; break;
  default: return false;
  }
  out.kind = kind;
  std::uintptr_t actual = 0, expected = 0, owned = 0;
  if (!Address(out.image.data, offset, sizeof(void *), out.manager) ||
      !Read(a, out.manager, 0, actual) ||
      !Address(out.image.image_base, manager_vt, sizeof(void *), expected) ||
      actual != expected) return false;
  if (kind == Scoped1210ManagerKindV1::character) {
    // This maintained vector is not the global typed Character registry and
    // does not establish a manager-owned storage relationship.
    return Read(a, out.manager, 0x20, out.character_members) &&
        Read(a, out.manager, 0x2C, out.character_member_count) &&
        out.character_member_count >= 0 && out.character_member_count <= 131072 &&
        (out.character_member_count == 0 || out.character_members != 0);
  }
  return Read(a, out.manager, owned_offset, owned) && owned != 0 &&
      Read(a, out.image.image_base, registry_slot, out.registry) &&
      out.registry == owned && Read(a, out.registry, 0, actual) &&
      Address(out.image.image_base, registry_vt, sizeof(void *), expected) && actual == expected;
}
inline bool Scope(const Scoped1210ImageSourceV1 &s,
    const Scoped1210SourceAccessV1 &a, const CoreSnapshotPrefix &e) noexcept {
  return a.copy != nullptr && a.validate_core_identity != nullptr &&
      e.clock.paused && e.map_ready && e.has_played_character &&
      e.played_character_alive && e.played_character_id != -1 &&
      e.local_player_id >= 0 && e.clock.speed >= 1 && e.clock.speed <= 5 &&
      a.validate_core_identity(a.context, s, e);
}
} // namespace scoped1210_source_detail_v1

inline bool ResolveScoped1210ImageRootsV1(const Scoped1210ImageSourceV1 &source,
    const CoreSnapshotPrefix &expected, const Scoped1210SourceAccessV1 &access,
    Scoped1210ImageRootsV1 &output) noexcept {
  output = {};
  using namespace scoped1210_source_detail_v1;
  // Recheck identity before calling owner callbacks or copying memory.
  if (!Binding(source) || !Scope(source, access, expected)) return false;
  Scoped1210ImageRootsV1 first{}, second{};
  if (!Capture(source, access, first) || !Capture(source, access, second) ||
      first != second || !Scope(source, access, expected) || !Binding(source)) return false;
  Scoped1210ImageRootsV1 final{};
  if (!Capture(source, access, final) || final != second) return false;
  output = final;
  return true;
}
inline bool ResolveScoped1210ManagerV1(const Scoped1210ImageSourceV1 &source,
    const CoreSnapshotPrefix &expected, const Scoped1210SourceAccessV1 &access,
    Scoped1210ManagerKindV1 kind, Scoped1210ManagerRootsV1 &output) noexcept {
  output = {};
  using namespace scoped1210_source_detail_v1;
  if (!Binding(source) || !Scope(source, access, expected)) return false;
  Scoped1210ManagerRootsV1 first{}, second{};
  if (!Capture(source, access, first.image) || !Manager(access, kind, first) ||
      !Capture(source, access, second.image) || !Manager(access, kind, second) ||
      first != second || !Scope(source, access, expected) || !Binding(source)) return false;
  // Owner validation may itself observe a changed world. Re-read the root and
  // manager identities after it rather than treating equal frames as a pin.
  Scoped1210ManagerRootsV1 final{};
  if (!Capture(source, access, final.image) || !Manager(access, kind, final) ||
      final != second) return false;
  output = final;
  return true;
}
} // namespace xar::ck3_1210
