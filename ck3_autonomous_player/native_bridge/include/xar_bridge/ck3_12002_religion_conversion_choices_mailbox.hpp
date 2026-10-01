#pragma once

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_faith.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_rite.hpp"

namespace xar::ck3_12002 {
inline constexpr char kPlayerReligionConversionChoicesPrivateStep12002[] =
    "query-player-religion-conversion-choices-v1";
inline constexpr char kPlayerReligionConversionChoicesDomainKey12002[] =
    "player_religion_conversion_choices_v1";
inline constexpr char kPlayerReligionConversionChoicesBackend12002[] =
    "ck3-1.20.0.2-native-player-religion-conversion-choices-v1";

struct PlayerReligionConversionChoicesSnapshot12002 {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  religion_conversion::faith::Choices faith_choices;
  religion_conversion_rite::FaithRites current_faith_rites;
};
struct PlayerReligionConversionChoicesMailboxContext12002 {
  QueryMailboxEnvelope envelope;
  religion_conversion::faith::Bindings faith_bindings;
  religion_conversion_rite::Bindings rite_bindings;
  PlayerReligionConversionChoicesSnapshot12002 observation;
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionConversionChoicesPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionConversionChoicesRequest12002(std::string_view payload,
    std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionConversionChoicesMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionConversionChoicesResult12002(
    const PlayerReligionConversionChoicesMailboxContext12002 &, std::string_view request_id);
bool RunPlayerReligionConversionChoicesMailbox12002(
    PlayerReligionConversionChoicesMailboxContext12002 &, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerReligionConversionChoicesPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;
} // namespace xar::ck3_12002
#endif
