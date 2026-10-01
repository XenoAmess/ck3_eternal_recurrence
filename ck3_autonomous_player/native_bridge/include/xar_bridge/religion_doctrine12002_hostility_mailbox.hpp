#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_hostility.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionHostilityPrivateStep12002 =
    "query-player-religion-hostility-v1";
inline constexpr std::string_view kPlayerReligionHostilityDomainKey12002 =
    "player_religion_hostility_v1";
inline constexpr std::string_view kPlayerReligionHostilityBackend12002 =
    "ck3-1.20.0.2-native-player-religion-hostility-v1";

struct PlayerReligionHostilityMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion::doctrine12002::HostilityBindings bindings{};
  std::uint32_t target_rite_id = religion::kAbsentReference;
  religion::doctrine12002::HostilityObservation observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionHostilityPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionHostilityRequest12002(std::string_view payload,
    std::uint32_t &target_rite_id, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionHostilityMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionHostilityResult12002(
    const PlayerReligionHostilityMailboxContext12002 &, std::string_view request_id);
bool RunPlayerReligionHostilityMailbox12002(PlayerReligionHostilityMailboxContext12002 &,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerReligionHostilityPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
