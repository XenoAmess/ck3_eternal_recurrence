#include "xar_bridge/ck3_12002_feast_outcome_values.hpp"
#include "xar_bridge/ck3_12004_activity_migration_v1.hpp"
#include "xar_bridge/ck3_12004_phase_character.hpp"

#include <array>
#include <limits>

namespace xar::bridge {
namespace {

template <typename T>
bool Read(const ActivityHostedIdentityEnvironmentV1 &environment,
          std::uintptr_t base, std::size_t offset, T &output) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base ||
      environment.read_memory == nullptr)
    return false;
  return environment.read_memory(environment.context, base + offset, &output,
                                 sizeof(output));
}

bool Sample(const FeastOutcomeEnvironmentV1 &environment,
            const ActivityHostedIdentityFrameV1 &expected,
            FeastOutcomeValuesV1 &output) noexcept {
  const auto &identity = environment.identity;
  const auto actor_id = static_cast<std::uint32_t>(expected.actor_character_id);
  std::uintptr_t storage = 0, fallback = 0, slots = 0, actor = 0, extension = 0;
  std::uint32_t capacity = 0, observed_id = 0;
  if (!Read(identity, identity.module_base,
            Activity12004RvaV1(identity.admitted_executable_sha256, kActivityHosted12002CharacterStorageRva), storage) || storage == 0 ||
      !Read(identity, identity.module_base,
            Activity12004RvaV1(identity.admitted_executable_sha256, kActivityHosted12002CharacterFallbackRva), fallback) ||
      !Read(identity, storage, 0x20, slots) || slots == 0 ||
      !Read(identity, storage, 0x2C, capacity) ||
      (actor_id & 0x00FFFFFFU) >= capacity ||
      !Read(identity, slots, static_cast<std::size_t>(actor_id & 0x00FFFFFFU) * 16 + 8,
            actor) || actor == 0 || actor == fallback ||
      !Read(identity, actor, 0x18, observed_id) || observed_id != actor_id ||
      !Read(identity, actor, kActivityFeast12002ResourceExtensionOffset,
            extension))
    return false;
  output.frame = expected;
  if (extension != 0 &&
      (!Read(identity, extension, kFeastOutcome12002PrestigeOffset,
             output.prestige_raw) ||
       !Read(identity, extension, kFeastOutcome12002StressOffset,
             output.stress_points)))
    return false;
  // Both native getters return legal zero if the extension is absent.
  output.prestige_available = true;
  output.stress_available = true;
  auto traits = environment.traits;
  if (!traits.enabled)
    traits = IsActivity12004BuildV1(identity.admitted_executable_sha256)
                 ? ck3_12004::phase_character::BindImage(
                       identity.module_base,
                       identity.admitted_executable_sha256)
                 : ck3_12002::phase_character::BindImage(
                       identity.module_base,
                       identity.admitted_executable_sha256);
  if (traits.enabled && traits.get_trait_database != nullptr) {
    auto *definition = ck3_12002::phase_character::FindUniqueTraitDefinition(
        traits.get_trait_database(), "lifestyle_reveler");
    std::array<void *, 1> definitions{definition};
    auto *character = reinterpret_cast<void *>(actor);
    if (definition != nullptr &&
        ck3_12002::phase_character::ReadTraitPresence(
            traits, character, definitions, output.reveler_present)) {
      output.reveler_available = true;
      if (output.reveler_present &&
          ck3_12002::phase_character::ReadTraitTrackXp(
              traits, character, definition, "", output.reveler_xp_raw))
        output.reveler_xp_available = true;
    }
  }
  std::uintptr_t actor_after = 0, extension_after = 0;
  return Read(identity, slots,
              static_cast<std::size_t>(actor_id & 0x00FFFFFFU) * 16 + 8,
              actor_after) && actor_after == actor &&
         Read(identity, actor, 0x18, observed_id) && observed_id == actor_id &&
         Read(identity, actor, kActivityFeast12002ResourceExtensionOffset,
              extension_after) && extension_after == extension;
}

} // namespace

FeastOutcomeResultV1 ReadFeastOutcomeValues12002(
    const FeastOutcomeEnvironmentV1 &environment,
    const ActivityHostedIdentityFrameV1 &expected) noexcept {
  FeastOutcomeResultV1 result{};
  result.value.frame = expected;
  const auto &identity = environment.identity;
  if (!identity.enabled || identity.module_base == 0 ||
      (identity.admitted_executable_sha256 != kActivityHostedIdentity12002ExeSha256V1 &&
       !IsActivity12004BuildV1(identity.admitted_executable_sha256)) ||
      identity.read_memory == nullptr || identity.read_frame == nullptr)
    return result;
  ActivityHostedIdentityFrameV1 before{};
  if (expected.revision == 0 || expected.actor_character_id <= 0 ||
      !expected.application_main_thread || !expected.paused ||
      !expected.map_ready || !expected.actor_alive ||
      !identity.read_frame(identity.context, before) || before != expected) {
    result.status = FeastOutcomeStatusV1::frame_rejected;
    return result;
  }
  FeastOutcomeValuesV1 first{}, second{};
  if (!Sample(environment, expected, first)) {
    result.status = FeastOutcomeStatusV1::actor_unavailable;
    return result;
  }
  ActivityHostedIdentityFrameV1 after{};
  if (!Sample(environment, expected, second) || first != second ||
      !identity.read_frame(identity.context, after) || after != expected) {
    result.status = FeastOutcomeStatusV1::snapshot_changed;
    return result;
  }
  result.value = first;
  result.status = first.reveler_available &&
                          (!first.reveler_present || first.reveler_xp_available)
                      ? FeastOutcomeStatusV1::observed
                      : FeastOutcomeStatusV1::observed_partial;
  return result;
}

} // namespace xar::bridge
