#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"

namespace xar::ck3_12002::religion::state_rite {

inline constexpr std::uintptr_t kCharacterTopLiegeRva = 0x28BFDA0;
inline constexpr std::uintptr_t kCharacterPrimaryTitleRva = 0x289DA30;
inline constexpr std::uintptr_t kTitleStateRiteRva = 0x2315030;
inline constexpr std::size_t kCharacterIdentityOffset = 0x18;
inline constexpr std::size_t kCharacterLandedDataOffset = 0x1C0;
inline constexpr std::size_t kLandedTitlesOffset = 0x1E0;
inline constexpr std::size_t kLandedTitlesCountOffset = 0x1EC;
inline constexpr std::size_t kDeathTitlesOffset = 0x68;
inline constexpr std::size_t kDeathTitlesCountOffset = 0x74;
inline constexpr std::size_t kTitleIdentityOffset = 0x10;
inline constexpr std::size_t kTitleStateRiteIdOffset = 0x308;

struct Bindings {
  bool enabled = false;
  religion::Bindings context{};
  ObjectGetter character_top_liege = nullptr;
  ObjectGetter character_primary_title = nullptr;
  ObjectGetter title_state_rite = nullptr;
};

struct TitleContext {
  std::optional<std::uint32_t> title_id;
  std::optional<std::uint32_t> state_rite_id;
  std::optional<std::uint32_t> state_faith_id;
  bool operator==(const TitleContext &) const = default;
};

enum class Failure {
  none,
  bindings_unavailable,
  played_character_unavailable,
  frame_not_paused,
  actor_rite_unavailable,
  actor_faith_unavailable,
  actor_main_rite_unavailable,
  top_liege_unavailable,
  primary_title_unavailable,
  title_state_rite_unavailable,
  title_state_faith_unavailable,
  state_changed,
};

struct Context {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = kAbsentReference;
  std::optional<std::uint32_t> actor_rite_id;
  std::optional<std::uint32_t> actor_faith_id;
  std::optional<std::uint32_t> actor_faith_main_rite_id;
  std::optional<std::uint32_t> top_liege_character_id;
  TitleContext player_primary_title;
  TitleContext realm_primary_title;
};

Bindings BindStateRiteImage12002(std::uintptr_t module_base,
                                std::string_view executable_sha256) noexcept;

// Existing paused application-main owner only. This observes actual realm
// identities; it does not decide conversion legality or issue a command.
bool ReadPlayedStateRite12002(const Bindings &bindings,
                             std::uint64_t capture_epoch,
                             Context &output) noexcept;
std::string SerializePlayedStateRite12002(const Context &context);
const char *StateRiteFailureKey(Failure failure) noexcept;

} // namespace xar::ck3_12002::religion::state_rite
