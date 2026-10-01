#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_personal_parameters.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionPersonalParametersPrivateStep12002 =
    "query-player-religion-personal-parameters-v1";
inline constexpr std::string_view kPlayerReligionPersonalParametersDomainKey12002 =
    "player_religion_personal_parameters_v1";
inline constexpr std::string_view kPlayerReligionPersonalParametersBackend12002 =
    "ck3-1.20.0.2-native-player-religion-personal-parameters-v1";

struct PlayerReligionPersonalParametersMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::Bindings bindings{};
  religion::doctrine12002::PersonalParameterBindings parameter_bindings{};
  religion::doctrine12002::PersonalParameterContext observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionPersonalParametersPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionPersonalParametersRevision12002(std::string_view payload,
                                     std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionPersonalParametersMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionPersonalParametersResult12002(
    const PlayerReligionPersonalParametersMailboxContext12002 &, std::string_view request_id);

// Shared by the real handler and the fixture with owned native-memory bindings.
// The caller owns the context until the mailbox is terminal and reclaimed.
bool RunPlayerReligionPersonalParametersMailbox12002(PlayerReligionPersonalParametersMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionPersonalParametersPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
