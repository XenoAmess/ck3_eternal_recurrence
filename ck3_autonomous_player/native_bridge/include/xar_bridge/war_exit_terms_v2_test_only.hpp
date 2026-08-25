#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

inline constexpr std::int64_t kWarExitTermsFixedPointScale = 100'000;
inline constexpr std::string_view kWarExitTermsV2ContractSha256 =
    "6F14AF260C46E1C359DDC8839B0384C8B584B64B0A03BDD2F57139E15B7317C7";

struct WarExitFixedPointV2TestOnly {
  std::int64_t raw = 0;
  std::int64_t scale = kWarExitTermsFixedPointScale;
};

struct WarExitClaimV2TestOnly {
  std::int32_t title_id = -1;
  bool present = false;
  bool strong = false;
  bool implicit = false;
  std::string state;
};

struct WarExitResourceV2TestOnly {
  std::int32_t character_id = -1;
  std::string resource_kind;
  WarExitFixedPointV2TestOnly value;
};

struct WarExitCharacterFixedPointV2TestOnly {
  std::int32_t character_id = -1;
  WarExitFixedPointV2TestOnly value;
};

struct WarExitGoldTransferV2TestOnly {
  std::int32_t from_character_id = -1;
  std::int32_t to_character_id = -1;
  WarExitFixedPointV2TestOnly value;
};

struct WarExitTruceV2TestOnly {
  std::int32_t owner_character_id = -1;
  std::int32_t toward_character_id = -1;
  std::int32_t evaluated_days = 0;
  std::int32_t current_date_raw = 0;
  std::int32_t expiry_date_raw = 0;
};

struct WarExitPrisonerReleaseV2TestOnly {
  std::int32_t jailer_character_id = -1;
  std::int32_t prisoner_character_id = -1;
  std::string reason;
};

struct WarExitOutcomeV2TestOnly {
  std::string declared_title_disposition;
  std::string claim_disposition;
  bool native_validator_passed = false;
  WarExitFixedPointV2TestOnly acceptance;
  std::int32_t decision_status_raw = 3;
  bool would_accept_now = false;
  bool auto_accept = false;
  WarExitFixedPointV2TestOnly cb_prestige_factor;
  std::vector<WarExitGoldTransferV2TestOnly> primary_gold_transfers;
  std::vector<WarExitResourceV2TestOnly> primary_resource_deltas;
  WarExitTruceV2TestOnly truce;
  std::vector<WarExitPrisonerReleaseV2TestOnly> prisoner_releases;
  bool complete = false;
};

struct WarTerminationExitTermsV2TestOnly {
  std::int32_t war_id = -1;
  std::int32_t date_raw = 0;
  std::int32_t casus_belli_database_index = -1;
  std::string casus_belli_key;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::int32_t claimant_character_id = -1;
  std::vector<std::int32_t> target_title_ids;
  std::vector<WarExitClaimV2TestOnly> claims;
  std::vector<WarExitResourceV2TestOnly> primary_resource_balances;
  std::vector<WarExitCharacterFixedPointV2TestOnly>
      primary_monthly_gold_income;
  WarExitOutcomeV2TestOnly white_peace;
  WarExitOutcomeV2TestOnly attacker_defeat;
  bool same_frame_stable = false;
  bool claim_temporary_lifecycle_verified = false;
  bool exit_terms_ready = false;
};

// Test-only, available-only serializer. Invalid/incomplete DTOs return nullopt;
// no unavailable/partial production union or dispatch literal is emitted.
std::optional<std::string> SerializeWarTerminationExitTermsV2TestOnly(
    const WarTerminationExitTermsV2TestOnly &terms);

} // namespace xar::game
