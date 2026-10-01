#pragma once

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/conversion_outcome12002_query.hpp"

namespace xar::ck3_12002 {
inline constexpr char kPlayerReligionConversionOutcomePrivateStep12002[] =
    "query-player-religion-conversion-outcome-v1";
inline constexpr char kPlayerReligionConversionOutcomeDomainKey12002[] =
    "player_religion_conversion_outcome_v1";
inline constexpr char kPlayerReligionConversionOutcomeBackend12002[] =
    "ck3-1.20.0.2-native-player-religion-conversion-outcome-v1";

struct PlayerReligionConversionOutcomeMailboxContext12002 {
  QueryMailboxEnvelope envelope;
  religion_conversion::outcome::Bindings bindings;
  std::uint32_t target_rite_id = religion::kAbsentReference;
  religion_conversion::outcome::Context observation;
  bool completed = false;
  std::string failure;
};
bool IsPlayerReligionConversionOutcomePrivateStep12002(std::string_view) noexcept;
bool ParsePlayerReligionConversionOutcomeRequest12002(std::string_view,
    std::uint32_t &target_rite_id, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionConversionOutcomeMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionConversionOutcomeResult12002(
    const PlayerReligionConversionOutcomeMailboxContext12002 &, std::string_view request_id);
bool RunPlayerReligionConversionOutcomeMailbox12002(
    PlayerReligionConversionOutcomeMailboxContext12002 &, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerReligionConversionOutcomePrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;
} // namespace xar::ck3_12002
#endif
