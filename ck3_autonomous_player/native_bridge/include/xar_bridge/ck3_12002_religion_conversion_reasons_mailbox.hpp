#pragma once

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_reasons.hpp"

namespace xar::ck3_12002 {

inline constexpr char kPlayerReligionConversionReasonsPrivateStep12002[] =
    "query-player-religion-conversion-reasons-v1";
inline constexpr char kPlayerReligionConversionReasonsDomainKey12002[] =
    "player_religion_conversion_reasons_v1";
inline constexpr char kPlayerReligionConversionReasonsBackend12002[] =
    "ck3-1.20.0.2-native-player-religion-conversion-reasons-v1";

struct PlayerReligionConversionReasonsMailboxContext12002 {
  QueryMailboxEnvelope envelope;
  religion_conversion::reasons::Bindings bindings;
  std::uint32_t target_rite_id = 0xFFFFFFFFU;
  religion_conversion::reasons::Reasons observation;
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionConversionReasonsPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionConversionReasonsRequest12002(std::string_view payload,
    std::uint32_t &target_rite_id, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionConversionReasonsMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionConversionReasonsResult12002(
    const PlayerReligionConversionReasonsMailboxContext12002 &, std::string_view request_id);
bool RunPlayerReligionConversionReasonsMailbox12002(
    PlayerReligionConversionReasonsMailboxContext12002 &, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerReligionConversionReasonsPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
#endif
