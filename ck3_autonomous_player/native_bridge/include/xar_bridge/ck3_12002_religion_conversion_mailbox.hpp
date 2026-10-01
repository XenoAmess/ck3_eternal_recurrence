#pragma once

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_terms.hpp"

namespace xar::ck3_12002 {

inline constexpr char kPlayerReligionConversionTermsPrivateStep12002[] =
    "query-player-religion-conversion-terms-v1";
inline constexpr char kPlayerReligionConversionTermsDomainKey12002[] =
    "player_religion_conversion_terms_v1";
inline constexpr char kPlayerReligionConversionTermsBackend12002[] =
    "ck3-1.20.0.2-native-player-religion-conversion-terms-v1";

struct PlayerReligionConversionTermsMailboxContext12002 {
  QueryMailboxEnvelope envelope;
  religion_conversion::terms::Bindings bindings;
  std::uint32_t target_rite_id = religion::kAbsentReference;
  religion_conversion::terms::Terms observation;
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionConversionTermsPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionConversionTermsRequest12002(std::string_view payload,
    std::uint32_t &target_rite_id, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionConversionTermsMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionConversionTermsResult12002(
    const PlayerReligionConversionTermsMailboxContext12002 &, std::string_view request_id);
bool RunPlayerReligionConversionTermsMailbox12002(
    PlayerReligionConversionTermsMailboxContext12002 &, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerReligionConversionTermsPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
#endif
