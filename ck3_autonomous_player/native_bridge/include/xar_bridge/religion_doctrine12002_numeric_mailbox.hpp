#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_numeric.hpp"
#include "xar_bridge/religion_doctrine12002_numeric_final.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionNumericSpecialParametersPrivateStep12002 =
    "query-player-religion-numeric-special-parameters-v1";
inline constexpr std::string_view kPlayerReligionNumericSpecialParametersDomainKey12002 =
    "player_religion_numeric_special_parameters_v1";
inline constexpr std::string_view kPlayerReligionNumericSpecialParametersBackend12002 =
    "ck3-1.20.0.2-native-player-religion-numeric-special-parameters-v1";

struct PlayerReligionNumericSpecialParametersMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::Bindings bindings{};
  religion::doctrine12002::NumericSpecialBindings numeric_bindings{};
  religion::doctrine12002::FaithNumericFinalBindings final_bindings{};
  religion::doctrine12002::NumericSpecialContext observation{};
  religion::doctrine12002::FaithNumericFinalContext final_observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionNumericSpecialParametersPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionNumericSpecialParametersRevision12002(
    std::string_view payload, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionNumericSpecialParametersMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionNumericSpecialParametersResult12002(
    const PlayerReligionNumericSpecialParametersMailboxContext12002 &, std::string_view request_id);

// The caller owns the context until the mailbox is terminal and reclaimed.
bool RunPlayerReligionNumericSpecialParametersMailbox12002(
    PlayerReligionNumericSpecialParametersMailboxContext12002 &, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerReligionNumericSpecialParametersPrivate12002(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
