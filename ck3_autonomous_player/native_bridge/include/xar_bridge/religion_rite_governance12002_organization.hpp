#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12002::religion::organization {
inline constexpr std::uintptr_t kCountyCountRva = 0xB80410;
inline constexpr std::uintptr_t kCharacterFollowerCountRva = 0xEDDB90;
inline constexpr std::size_t kCountyCountOffset = 0x18;
inline constexpr std::size_t kCharacterFollowerCountOffset = 0x1C;
using CountGetter = std::int32_t (*)(void *);

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  ObjectGetter character_rite = nullptr;
  CountGetter county_count = nullptr;
  CountGetter character_follower_count = nullptr;
};
enum class Failure {
  none,
  bindings_unavailable,
  played_character_unavailable,
  frame_not_paused,
  rite_unavailable,
  state_changed,
};
struct Counts {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::int32_t> county_count;
  std::optional<std::int32_t> character_follower_count;
};

Bindings BindOrganizationImage12002(std::uintptr_t module_base,
                                    std::string_view executable_sha256) noexcept;
// Current paused player only. Counts are the native Rite cache, not a member list.
bool ReadPlayedOrganizationCounts12002(const Bindings &bindings,
                                      std::uint64_t capture_epoch,
                                      Counts &output) noexcept;
const char *OrganizationFailureKey(Failure failure) noexcept;
std::string SerializePlayedOrganizationCounts12002(const Counts &counts);
} // namespace xar::ck3_12002::religion::organization
