#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class CampaignRootContextStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct CampaignRootTitleV1 {
  std::int32_t title_id = -1;
  std::int32_t tier_raw = 0;
  std::string tier_key;

  friend bool operator==(const CampaignRootTitleV1 &,
                         const CampaignRootTitleV1 &) = default;
};

struct CampaignRootGovernmentV1 {
  std::string key;
  std::vector<std::string> flags;
  std::int32_t native_flag_count = 0;

  friend bool operator==(const CampaignRootGovernmentV1 &,
                         const CampaignRootGovernmentV1 &) = default;
};

struct CampaignRootReadinessV1 {
  bool player_identity_ready = false;
  bool primary_title_ready = false;
  bool capital_ready = false;
  bool lieges_ready = false;
  bool government_ready = false;
  bool selected_game_rule_tokens_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(const CampaignRootReadinessV1 &,
                         const CampaignRootReadinessV1 &) = default;
};

// A successful row distinguishes native-observed absence from read failure by
// the top-level status. Optional primary/capital/immediate/government values
// are therefore legitimate engine states only when status is available.
struct CampaignRootContextV1 {
  CampaignRootContextStatusV1 status =
      CampaignRootContextStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::optional<std::int32_t> local_player_id;
  std::optional<std::int32_t> player_character_id;
  std::optional<bool> player_character_alive;
  std::optional<CampaignRootTitleV1> primary_title;
  std::optional<std::int32_t> capital_province_id;
  std::optional<std::int32_t> immediate_liege_character_id;
  std::optional<std::int32_t> top_liege_character_id;
  std::optional<bool> independent;
  std::optional<CampaignRootGovernmentV1> government;
  std::vector<std::string> selected_game_rule_tokens;
  std::int32_t native_selected_game_rule_token_count = 0;
  CampaignRootReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(const CampaignRootContextV1 &,
                         const CampaignRootContextV1 &) = default;
};

struct CampaignRootFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::int32_t played_character_id = -1;

  friend bool operator==(const CampaignRootFrameV1 &,
                         const CampaignRootFrameV1 &) = default;
};

enum class ReadCampaignRootContextResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kCampaignRootContextV1Capability =
    "game.command.query-campaign-root-context-v1";
inline constexpr std::string_view kCampaignRootContextV1Step =
    "query-campaign-root-context-v1";
inline constexpr std::string_view kCampaignRootContextV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view kCampaignRootContextV1ExecutableSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kCampaignRootContextV1BackendId =
    "ck3-1.19.0.6-native-campaign-root-context-v1";

inline constexpr std::uintptr_t kCampaignRootGameStateSlotRva = 0x570E068;
inline constexpr std::uintptr_t kCampaignRootJominiStateSlotRva = 0x570F7B8;
inline constexpr std::uintptr_t kCampaignRootCharacterStorageSlotRva =
    0x570C130;
inline constexpr std::uintptr_t kCampaignRootCharacterFallbackSlotRva =
    0x570C138;
inline constexpr std::uintptr_t kCampaignRootLandedTitleStorageSlotRva =
    0x570C410;
inline constexpr std::uintptr_t kCampaignRootLandedTitleFallbackSlotRva =
    0x570C3F8;
inline constexpr std::uintptr_t kCampaignRootGovernmentFallbackSlotRva =
    0x570CB50;
inline constexpr std::uintptr_t kCampaignRootGameRuleSelectionServiceSlotRva =
    0x5754B48;
inline constexpr std::uintptr_t kCampaignRootGameRuleTokenFallbackSlotRva =
    0x57D7430;

inline constexpr std::uintptr_t kCampaignRootPrimaryTitleRva = 0x25F3350;
inline constexpr std::uintptr_t kCampaignRootCapitalProvinceRva = 0x2606760;
inline constexpr std::uintptr_t kCampaignRootImmediateLiegeRva = 0x2613480;
inline constexpr std::uintptr_t kCampaignRootTopLiegeRva = 0x2613600;
inline constexpr std::uintptr_t kCampaignRootGovernmentRva = 0x26165B0;
inline constexpr std::uintptr_t kCampaignRootScriptIdentifierNameRva =
    0x3B58970;

#if defined(_MSC_VER)
#define XAR_CAMPAIGN_ROOT_FASTCALL __fastcall
#else
#define XAR_CAMPAIGN_ROOT_FASTCALL
#endif

using NativeCampaignRootCharacterResolverV1 =
    void *(XAR_CAMPAIGN_ROOT_FASTCALL *)(void *character);
using NativeCampaignRootScriptIdentifierNameV1 =
    const std::string *(XAR_CAMPAIGN_ROOT_FASTCALL *)(std::int32_t identifier);

#undef XAR_CAMPAIGN_ROOT_FASTCALL

struct CampaignRootNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  void **game_state_slot = nullptr;
  void **jomini_state_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void **landed_title_storage_slot = nullptr;
  void **landed_title_fallback_slot = nullptr;
  void **government_fallback_slot = nullptr;
  void **game_rule_selection_service_slot = nullptr;
  void **game_rule_token_fallback_slot = nullptr;
  NativeCampaignRootCharacterResolverV1 primary_title = nullptr;
  NativeCampaignRootCharacterResolverV1 capital_province = nullptr;
  NativeCampaignRootCharacterResolverV1 immediate_liege = nullptr;
  NativeCampaignRootCharacterResolverV1 top_liege = nullptr;
  NativeCampaignRootCharacterResolverV1 government = nullptr;
  NativeCampaignRootScriptIdentifierNameV1 script_identifier_name = nullptr;
};

using CaptureCampaignRootFrameV1 = bool (*)(
    void *context, game::CampaignRootFrameV1 &output) noexcept;
using IsCampaignRootMainThreadV1 = bool (*)(void *context) noexcept;
using ReadCampaignRootMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;
using ReadCampaignRootStringV1 = bool (*)(
    void *context, const void *native_string,
    std::string &output) noexcept;

struct CampaignRootAccessV1 {
  void *context = nullptr;
  CaptureCampaignRootFrameV1 capture_frame = nullptr;
  IsCampaignRootMainThreadV1 is_main_thread = nullptr;
  ReadCampaignRootMemoryV1 read_memory = nullptr;
  // Deterministic fixtures may provide an ABI-independent string reader.
  // Production leaves this null and reads the frozen MSVC std::string layout.
  ReadCampaignRootStringV1 read_string = nullptr;
};

struct CampaignRootContextRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
};

CampaignRootNativeEnvironmentV1 BindCampaignRootNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadCampaignRootContextResultV1 ReadCampaignRootContextV1(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    const CampaignRootContextRequestV1 &request,
    game::CampaignRootContextV1 &output) noexcept;

std::string SerializeCampaignRootContextV1(
    const game::CampaignRootContextV1 &context);

} // namespace xar::ck3_11906
