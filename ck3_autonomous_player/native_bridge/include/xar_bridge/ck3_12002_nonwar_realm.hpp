#pragma once

#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/campaign_root_state_changed_diagnostics_12004.hpp"

namespace xar::ck3_12002 {

// Caller-owned, allocation-free readonly evidence. Never part of root readiness,
// equality, projection fields or the original campaign result envelope.
struct HeldTitlePartitionFailure12002 {
  std::string_view guard;
  std::string_view resolver_guard;
  std::uint32_t sample = 0;
  std::int32_t actor_id = -1;
  std::int32_t index = -1;
  std::int32_t title_id = -1;
  std::int32_t held_count = -1;
  std::int32_t held_capacity = -1;
  std::int32_t holder_id = -1;
  std::int32_t tier_raw = -1;
  std::int32_t successor_count = -1;
  std::int32_t successor_capacity = -1;
  std::int32_t first_heir_id = -1;
  std::int32_t capital_province_id = -1;
  // Diagnostic-only values; the address is never dereferenced or reused.
  bool capital_getter_attempted = false;
  bool capital_getter_completed = false;
  std::uint64_t capital_getter_return_address = 0;
  bool capital_getter_return_nonnull = false;
  bool capital_type_tag_read_attempted = false;
  bool capital_type_tag_observed = false;
  std::uint32_t capital_type_tag = 0;
  bool capital_no_province_by_stock_type_tag_observed = false;
  bool capital_no_province_by_stock_type_tag = false;
  bool landless_type_read_attempted = false;
  bool landless_type_observed = false;
  std::uint32_t landless_type_value = 0;
  bool noble_family_read_attempted = false;
  bool noble_family_observed = false;
  std::uint32_t noble_family_value = 0;
  bool children_count_read_attempted = false;
  bool children_count_observed = false;
  std::int32_t children_count = -1;
  bool title_key_read_attempted = false;
  bool title_key_observed = false;
  std::int32_t primary_title_id = -1;
  std::int32_t primary_match_count = -1;
  bool held_count_observed = false;
  bool title_id_observed = false;
  bool successor_count_observed = false;
  bool capital_province_id_observed = false;
  // A separate optional diagnostic family; held-title fields keep their meaning.
  std::optional<ck3_12004::CampaignRootStateChangedDiagnostic12004>
      campaign_root_state_changed;
};

// Reviewed against the frozen Crozier executable; no 1.19 layout reuse.
inline constexpr std::uintptr_t kNonwarRealmTitleProvinceRva = 0x230F900;
inline constexpr std::uintptr_t kNonwarRealmProvinceHolderCharacterIdRva = 0x247D030;
inline constexpr std::size_t kNonwarRealmCharacterLandStateOffset = 0x1C0;
inline constexpr std::size_t kNonwarRealmHeldTitlesOffset = 0x1E0;
inline constexpr std::size_t kNonwarRealmTitleHolderOffset = 0x128;
inline constexpr std::size_t kNonwarRealmTitleSuccessorDataOffset = 0x150;
inline constexpr std::size_t kNonwarRealmTitleSuccessorCapacityOffset = 0x158;
inline constexpr std::size_t kNonwarRealmTitleSuccessorCountOffset = 0x15C;

struct NonwarRealmInput12002 {
  void *game_data = nullptr;
  void *player_character = nullptr;
  std::int32_t player_character_id = -1;
  void *primary_title_pointer = nullptr;
  std::optional<game::CampaignRootTitleV1> primary_title;
  std::int32_t top_liege_character_id = -1;
};

struct NonwarRealmProjection12002 {
  std::vector<std::int32_t> primary_title_succession_character_ids;
  std::vector<game::CampaignRootHeldTitleSuccessionV1> held_title_partition;
  std::vector<std::int32_t> direct_landed_vassal_character_ids;
  std::vector<std::int32_t> adjacent_external_province_holder_character_ids;
  std::vector<game::CampaignRootRelatedCharacterV1> related_character_contexts;

  friend bool operator==(const NonwarRealmProjection12002 &,
                         const NonwarRealmProjection12002 &) = default;
};

void BindNonwarRealm12002(CampaignRootNativeEnvironmentV1 &environment,
                         std::uintptr_t module_base) noexcept;

// Called inside the campaign root's paused, application-main double sample.
// The caller retains the exact-build/frame gate. No commands or cache writes.
bool ReadNonwarRealmProjection12002(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    const NonwarRealmInput12002 &input,
    NonwarRealmProjection12002 &output,
    std::string_view &failure,
    HeldTitlePartitionFailure12002 *failure_diagnostic = nullptr) noexcept;

} // namespace xar::ck3_12002
