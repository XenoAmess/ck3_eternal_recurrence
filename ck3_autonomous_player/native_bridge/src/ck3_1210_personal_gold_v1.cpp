#include "xar_bridge/ck3_1210_personal_gold_v1.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"

#include <cstring>
#include <limits>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_1210 {
namespace {

template <class T>
T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
      sizeof(value));
  return value;
}

bool SamePrefix(const CoreSnapshotPrefix &a,
    const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw &&
      a.clock.speed == b.clock.speed && a.clock.paused == b.clock.paused &&
      a.local_player_id == b.local_player_id && a.map_ready == b.map_ready &&
      a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}

bool Fail(PersonalGoldObservationV1 &output, std::string_view reason) noexcept {
  const auto sha=output.executable_sha256;
  const auto steam=output.steam_build_id;
  const auto bytes=output.executable_file_size;
  output = {};
  output.executable_sha256=sha;output.steam_build_id=steam;output.executable_file_size=bytes;
  output.unavailable_reason = reason;
  return false;
}

struct ActorSample {
  std::int32_t full_id = -1;
  std::uint32_t type = 0;
  void *death = nullptr;
  void *living = nullptr;
  std::int64_t gold = 0;
};

ActorSample Sample(const void *actor) noexcept {
  ActorSample result{};
  result.full_id = Load<std::int32_t>(actor, kCharacterFullIdOffset);
  result.type = Load<std::uint32_t>(actor, kPersonalGoldCharacterTypeOffsetV1);
  result.death = Load<void *>(actor, kCharacterDeathDataOffset);
  result.living = Load<void *>(actor, kPersonalGoldLivingExtensionOffsetV1);
  return result;
}

std::int64_t Gold(const ActorSample &sample) noexcept {
  // Called only after identity/alive validation. Null living has the actual
  // GetGold zero semantics; it never implies death or a failed read.
  return sample.living == nullptr ? 0 :
      Load<std::int64_t>(sample.living, kPersonalGoldBalanceOffsetV1);
}

bool ValidActor(const ActorSample &sample,
    const CoreSnapshotPrefix &expected) noexcept {
  return sample.full_id == expected.played_character_id &&
      sample.type == 0x43686172U && sample.death == nullptr &&
      expected.played_character_alive;
}

bool ReadImpl(const PersonalGoldBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected,
    PersonalGoldObservationV1 &output) noexcept {
  output = {};
  const auto &core = bindings.core;
  if(IsHotfix(core.image_build)) {
    output.executable_sha256=hotfix26757580::kExecutableSha256;
    output.steam_build_id=hotfix26757580::kSteamBuildId;
    output.executable_file_size=114761336;
  }
  if (!bindings.exact_build_admitted || !core.enabled)
    return Fail(output, "unsupported_build");
  if (core.game_state_slot == nullptr || core.jomini_state_slot == nullptr ||
      core.character_storage_slot == nullptr || core.get_local_player == nullptr)
    return Fail(output, "core_binding_unavailable");
  if (!expected.clock.paused) return Fail(output, "requires_paused");
  if (!expected.map_ready) return Fail(output, "map_not_ready");
  if (expected.local_player_id < 0 || !expected.has_played_character ||
      expected.played_character_id == -1)
    return Fail(output, "player_identity_unavailable");
  if (!expected.played_character_alive)
    return Fail(output, "player_not_alive");

  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(core, before))
    return Fail(output, "core_read_failed");
  if (!SamePrefix(before, expected))
    return Fail(output, "core_frame_changed");
  const auto actor = ResolveCoreCharacter(core, expected.played_character_id);
  if (actor == nullptr) return Fail(output, "player_generation_unavailable");
  auto first = Sample(actor);
  if (!ValidActor(first, expected))
    return Fail(output, "player_identity_unavailable");
  first.gold = Gold(first);

  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(core, after))
    return Fail(output, "core_read_failed");
  if (!SamePrefix(after, expected) || !SamePrefix(before, after))
    return Fail(output, "core_frame_changed");
  const auto confirmed = ResolveCoreCharacter(core, expected.played_character_id);
  if (confirmed == nullptr || confirmed != actor)
    return Fail(output, "player_identity_changed");
  auto second = Sample(confirmed);
  if (!ValidActor(second, expected) || first.full_id != second.full_id ||
      first.type != second.type || first.death != second.death ||
      first.living != second.living)
    return Fail(output, "player_identity_changed");
  second.gold = Gold(second);
  if (first.gold != second.gold)
    return Fail(output, "personal_gold_changed");

  output.frame = after;
  output.personal_gold_raw = first.gold;
  output.available = true;
  output.same_frame_ready = true;
  output.unavailable_reason = {};
  return true;
}
} // namespace

PersonalGoldBindingsV1 BindPersonalGoldImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  PersonalGoldBindingsV1 result{};
  // Core performs exact-profile and image-overflow checks. No native Gold call.
  result.core = BindCoreImage(image_base, executable_sha256);
  result.exact_build_admitted = result.core.enabled;
  return result;
}

bool ReadPersonalGoldV1(const PersonalGoldBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected,
    PersonalGoldObservationV1 &output) noexcept {
#if defined(_MSC_VER)
  __try {
    return ReadImpl(bindings, expected, output);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return Fail(output, "memory_read_failed");
  }
#else
  return ReadImpl(bindings, expected, output);
#endif
}

} // namespace xar::ck3_1210
