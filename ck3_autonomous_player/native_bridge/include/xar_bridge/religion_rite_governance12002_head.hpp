#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12002::religion::head {
inline constexpr std::uintptr_t kRiteHeadIdGetterRva = 0xD55CF0;
inline constexpr std::uintptr_t kRiteHeadObjectGetterRva = 0x24FC610;
inline constexpr std::uintptr_t kFaithReligiousHeadGetterRva = 0x2439E10;
inline constexpr std::uintptr_t kFaithReligiousHeadTitleGetterRva = 0x2443FA0;
inline constexpr std::size_t kRiteHeadCharacterIdOffset = 0x4C0;
inline constexpr std::size_t kFaithReligiousHeadTitleIdOffset = 0x300;
inline constexpr std::size_t kTitleReferenceIdOffset = 0x10;
inline constexpr std::size_t kTitleHolderCharacterIdOffset = 0x128;

using HeadIdGetter = std::uint32_t *(*)(void *, std::uint32_t *);
struct Bindings {
  bool enabled = false;
  religion::Bindings context{};
  HeadIdGetter rite_head_id = nullptr;
  ObjectGetter rite_head = nullptr;
  ObjectGetter faith_religious_head = nullptr;
  ObjectGetter faith_religious_head_title = nullptr;
};
enum class Failure {
  none, bindings_unavailable, played_character_unavailable, frame_not_paused,
  rite_unavailable, faith_unavailable, main_rite_unavailable,
  rite_head_unavailable, main_rite_head_unavailable,
  faith_head_title_unavailable, faith_head_holder_unavailable, state_changed,
};
struct Context {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> actor_rite_id;
  std::optional<std::uint32_t> faith_id;
  std::optional<std::uint32_t> faith_main_rite_id;
  std::optional<std::uint32_t> actor_rite_head_character_id;
  std::optional<std::uint32_t> faith_main_rite_head_character_id;
  std::optional<std::uint32_t> faith_religious_head_title_id;
  std::optional<std::uint32_t> faith_religious_head_holder_character_id;
};
Bindings BindRiteHeadsImage12002(std::uintptr_t module_base,
                               std::string_view executable_sha256) noexcept;
// Existing paused application-main owner only; all objects remain native-owned.
// This reads three distinct identity sources, not a final clerical authority,
// doctrine classification, religious action, or military role.
bool ReadPlayedRiteHeads12002(const Bindings &bindings, std::uint64_t capture_epoch,
                             Context &output) noexcept;
const char *RiteHeadsFailureKey(Failure failure) noexcept;
std::string SerializePlayedRiteHeads12002(const Context &context);
} // namespace xar::ck3_12002::religion::head
