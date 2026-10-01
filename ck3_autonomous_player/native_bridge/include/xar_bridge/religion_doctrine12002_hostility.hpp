#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"

namespace xar::ck3_12002::religion::doctrine12002 {

inline constexpr std::uintptr_t kHostilityRiteStorageSlotRva = 0x5D1E2F8;
inline constexpr std::uintptr_t kHostilityRiteFinalRva = 0x2591CE0;
inline constexpr std::uintptr_t kHostilityFaithFinalRva = 0x243E950;
inline constexpr std::size_t kHostilityRiteComponentOffset = 0x750;
inline constexpr std::uint32_t kHostilityRiteTypeTag = 0x52697465;

enum class HostilityLevel : std::uint8_t {
  righteous = 0, astray = 1, hostile = 2, evil = 3,
};
using RiteHostilityGetter = std::uint8_t (*)(void *source_component,
                                            void *source_rite, void *target_rite);
using FaithHostilityGetter = std::uint8_t (*)(void *source_faith,
                                             void *target_faith, bool offset);
struct HostilityBindings {
  bool enabled = false;
  religion::Bindings context{};
  void **rite_storage_slot = nullptr;
  RiteHostilityGetter rite_hostility = nullptr;
  FaithHostilityGetter faith_hostility = nullptr;
};
enum class HostilityFailure {
  none, bindings_unavailable, played_character_unavailable, frame_not_paused,
  actor_rite_unavailable, target_rite_unavailable, faith_unavailable,
  religion_unavailable, main_rite_unavailable, native_level_unavailable,
  state_changed,
};
struct HostilityObservation {
  bool available = false;
  HostilityFailure failure = HostilityFailure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> actor_rite_id, target_rite_id;
  std::optional<std::uint32_t> actor_faith_id, target_faith_id;
  std::optional<std::uint32_t> actor_religion_id, target_religion_id;
  std::optional<std::uint32_t> actor_main_rite_id, target_main_rite_id;
  std::optional<HostilityLevel> actor_rite_towards_target;
  std::optional<HostilityLevel> target_rite_towards_actor;
  std::optional<HostilityLevel> actor_faith_towards_target;
  std::optional<HostilityLevel> target_faith_towards_actor;
  std::optional<bool> same_faith, same_religion;
};
HostilityBindings BindHostilityImage12002(std::uintptr_t module_base,
                                        std::string_view executable_sha256) noexcept;
// Application-main paused owner only. Explicit full target Rite reference;
// no process discovery, command, policy or calculated marriage acceptance.
bool ReadPlayedHostilityTowardsRite12002(const HostilityBindings &bindings,
                                        std::uint32_t target_rite_id,
                                        std::uint64_t capture_epoch,
                                        HostilityObservation &output) noexcept;
const char *HostilityLevelKey(HostilityLevel level) noexcept;
const char *HostilityFailureKey(HostilityFailure failure) noexcept;
std::string SerializeHostilityObservation12002(const HostilityObservation &output);

} // namespace xar::ck3_12002::religion::doctrine12002
