#include "xar_bridge/ck3_12004_player_heir_candidate_v1.hpp"

#include <array>
#include <cstring>
#include <limits>
#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12004::player_heir_candidate_v1 {
namespace {
static_assert(sizeof(void *) == 8, "exact native getter requires x64");
constexpr std::uint32_t kCharacterTag = 0x43686172;
constexpr std::size_t kCharacterTagOffset = 0x1C;
// First16B of exact raw getter, frozen native/function-window01.json
// SHA e1f10676c2be29878c6534d2f08392dbbb90063408f2e9c84ecb74a395c0504e.
constexpr std::array<unsigned char, 16> kGetterPrefix{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83,
    0xEC, 0x40, 0x0F, 0x57, 0xC0, 0x0F, 0x11, 0x44};

template <class T>
T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

bool SameCoreBindings(const CoreBindings &a, const CoreBindings &b) noexcept {
  return a.enabled && b.enabled && a.game_state_slot == b.game_state_slot &&
      a.jomini_state_slot == b.jomini_state_slot &&
      a.character_storage_slot == b.character_storage_slot &&
      a.get_local_player == b.get_local_player;
}

bool ValidBindings(const Bindings &b) noexcept {
  if (!b.enabled || b.executable_sha256 != kExecutableSha256 ||
      !b.core.enabled || !b.family.enabled ||
      !SameCoreBindings(b.core, b.family.core) ||
      !b.core.game_state_slot || !b.core.jomini_state_slot ||
      !b.core.character_storage_slot || !b.core.get_local_player ||
      !b.get_player_heir || !b.on_application_main)
    return false;
  if (b.offline_fixture) return true; // Explicit synthetic, never live credit.
#if !defined(XAR_CK3_ENABLE_PLAYER_HEIR_CANDIDATE12004_V1)
  return false;
#else
  if (b.module_base == 0 ||
      b.module_base > (std::numeric_limits<std::uintptr_t>::max)() - 0x5D1DE80)
    return false;
  const auto expected_core = ck3_12004::BindCoreImage(b.module_base,
                                                    b.executable_sha256);
  const auto expected_family = BindFamilyValuesImage(b.module_base,
                                                    b.executable_sha256);
  return SameCoreBindings(b.core, expected_core) &&
      b.family.house_store == expected_family.house_store &&
      b.family.house_fallback == expected_family.house_fallback &&
      b.family.dynasty_store == expected_family.dynasty_store &&
      b.family.dynasty_fallback == expected_family.dynasty_fallback &&
      reinterpret_cast<std::uintptr_t>(b.get_player_heir) ==
          b.module_base + kGetPlayerHeirRva &&
      std::memcmp(reinterpret_cast<const void *>(b.module_base +
                  kGetPlayerHeirRva), kGetterPrefix.data(),
                  kGetterPrefix.size()) == 0;
#endif
}

bool Ready(const CoreSnapshotPrefix &f) noexcept {
  return f.clock.paused && f.map_ready && f.local_player_id >= 0 &&
      f.has_played_character && f.played_character_id != -1 &&
      f.played_character_alive;
}

bool SameFrame(const CoreSnapshotPrefix &a,
               const CoreSnapshotPrefix &b) noexcept {
  return Ready(a) && Ready(b) && a.clock.date_raw == b.clock.date_raw &&
      a.clock.speed == b.clock.speed && a.local_player_id == b.local_player_id &&
      a.played_character_id == b.played_character_id;
}

struct Roots {
  std::array<void *, 7> values{};
  friend bool operator==(const Roots &, const Roots &) = default;
};

Roots ReadRoots(const Bindings &b) noexcept {
  const auto optional = [](void **slot) { return slot ? *slot : nullptr; };
  return {{{*b.core.game_state_slot, *b.core.jomini_state_slot,
            *b.core.character_storage_slot, optional(b.family.house_store),
            optional(b.family.house_fallback), optional(b.family.dynasty_store),
            optional(b.family.dynasty_fallback)}}};
}

bool Identity(const CoreBindings &core, const void *object,
              std::int32_t id) noexcept {
  return object && id != -1 &&
      Load<std::int32_t>(object, kCharacterFullIdOffset) == id &&
      Load<std::uint32_t>(object, kCharacterTagOffset) == kCharacterTag &&
      ck3_12004::ResolveCoreCharacter(core, id) == object;
}

Observation Fail(Observation out, std::string_view reason) noexcept {
  out.available = false;
  out.unavailable_reason = reason;
  out.candidate_character_id = -1;
  out.candidate_alive = false;
  out.identity_and_frame_stable = false;
  out.lineage_available = false;
  out.candidate_lineage = {};
  out.lineage_unavailable_reason = {};
  return out;
}

Observation ReadUnchecked(const Bindings &b) {
  Observation out{};
  out.source_fixture = b.offline_fixture;
  if (!ValidBindings(b)) return Fail(out, "player_heir_binding_unavailable");
  if (!b.on_application_main(b.thread_context))
    return Fail(out, "application_main_required");
  out.original_getter_source_bound = !b.offline_fixture;
  const auto roots = ReadRoots(b);
  if (!ck3_12004::ReadCoreSnapshot(b.core, out.before) || !Ready(out.before))
    return Fail(out, "paused_living_local_actor_required");
  out.actor_character_id = out.before.played_character_id;
  const auto *actor = ck3_12004::ResolveCoreCharacter(b.core,
                                                   out.actor_character_id);
  if (!Identity(b.core, actor, out.actor_character_id))
    return Fail(out, "actor_identity_unavailable");
  const auto actor_death = Load<void *>(actor, kCharacterDeathDataOffset);
  if (actor_death) return Fail(out, "actor_not_alive");
  const auto *candidate = b.get_player_heir(actor); // Exactly once.
  out.getter_observed = true;
  out.candidate_present = candidate != nullptr;
  void *candidate_death = nullptr;
  if (candidate) {
    const auto id = Load<std::int32_t>(candidate, kCharacterFullIdOffset);
    if (candidate == actor || !Identity(b.core, candidate, id))
      return Fail(out, "candidate_identity_unavailable");
    out.candidate_character_id = id;
    candidate_death = Load<void *>(candidate, kCharacterDeathDataOffset);
    out.candidate_alive = candidate_death == nullptr;
    out.lineage_available = ck3_12002::family_value::ReadCharacterLineage(
        b.family, candidate, out.candidate_lineage,
        &out.lineage_unavailable_reason);
  }
  if (!ck3_12004::ReadCoreSnapshot(b.core, out.after) ||
      !SameFrame(out.before, out.after) || roots != ReadRoots(b))
    return Fail(out, "player_heir_frame_or_roots_changed");
  if (!Identity(b.core, actor, out.actor_character_id) ||
      Load<void *>(actor, kCharacterDeathDataOffset) != actor_death)
    return Fail(out, "actor_identity_or_liveness_changed");
  if (candidate) {
    if (!Identity(b.core, candidate, out.candidate_character_id) ||
        Load<void *>(candidate, kCharacterDeathDataOffset) != candidate_death)
      return Fail(out, "candidate_identity_or_liveness_changed");
    ck3_12002::family_value::Lineage after_lineage{};
    std::string_view reason;
    const bool after_available = ck3_12002::family_value::ReadCharacterLineage(
        b.family, candidate, after_lineage, &reason);
    if (after_available != out.lineage_available ||
        (after_available && after_lineage != out.candidate_lineage))
      return Fail(out, "candidate_lineage_changed");
    // Lineage reads must not leave a changed component/storage/character copy.
    if (roots != ReadRoots(b) ||
        !Identity(b.core, candidate, out.candidate_character_id) ||
        !Identity(b.core, actor, out.actor_character_id) ||
        Load<void *>(candidate, kCharacterDeathDataOffset) != candidate_death ||
        Load<void *>(actor, kCharacterDeathDataOffset) != actor_death)
      return Fail(out, "player_heir_identity_changed_during_lineage");
  }
  out.available = true;
  out.unavailable_reason = {};
  out.identity_and_frame_stable = true;
  return out;
}

Observation ReadCppGuarded(const Bindings &b) noexcept {
  try { return ReadUnchecked(b); }
  catch (...) {
    Observation out{};
    out.source_fixture = b.offline_fixture;
    return Fail(out, "player_heir_native_call_failed");
  }
}
} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha,
                   OnApplicationMain on_main, void *context) noexcept {
  Bindings out{};
#if defined(XAR_CK3_ENABLE_PLAYER_HEIR_CANDIDATE12004_V1)
  if (base == 0 || sha != kExecutableSha256 || !on_main ||
      base > (std::numeric_limits<std::uintptr_t>::max)() - 0x5D1DE80)
    return out;
  out.module_base = base;
  out.executable_sha256 = sha;
  out.core = ck3_12004::BindCoreImage(base, sha);
  out.family = BindFamilyValuesImage(base, sha);
  out.get_player_heir = reinterpret_cast<GetPlayerHeir>(base + kGetPlayerHeirRva);
  out.on_application_main = on_main;
  out.thread_context = context;
  out.enabled = out.core.enabled && out.family.enabled;
#else
  (void)base; (void)sha; (void)on_main; (void)context;
#endif
  return out;
}

Observation Read(const Bindings &b) noexcept {
#if defined(_MSC_VER)
  __try { return ReadCppGuarded(b); }
  __except (EXCEPTION_EXECUTE_HANDLER) {
    Observation out{};
    out.source_fixture = b.offline_fixture;
    return Fail(out, "player_heir_memory_access_failed");
  }
#else
  return ReadCppGuarded(b);
#endif
}
} // namespace xar::ck3_12004::player_heir_candidate_v1
