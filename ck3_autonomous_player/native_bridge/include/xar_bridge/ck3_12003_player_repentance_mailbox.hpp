#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_repentance_context.hpp"
#include "xar_bridge/ck3_12003_repentance_recipient_candidates.hpp"
#include "xar_bridge/ck3_12003_repentance_petition_decision_terms.hpp"
#include "xar_bridge/ck3_12003_repentance_recovery_inputs.hpp"
#include "xar_bridge/ck3_12003_repentance_pam_route.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kPlayerRepentancePrivateStep12003 =
    "query-player-repentance-context-v1";
inline constexpr std::string_view kPlayerRepentanceDomainKey12003 =
    "player_repentance_context_v1";
inline constexpr std::string_view kPlayerRepentanceBackend12003 =
    "ck3-1.20.0.3-native-player-repentance-context-v1";

struct PlayerRepentanceMailboxContext12003 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  religion::repentance::Bindings bindings{};
  religion::repentance::Context observation{};
  religion::repentance_candidates::Bindings candidate_bindings{};
  religion::repentance_candidates::Context candidate_observation{};
  religion::repentance_fallback::Bindings fallback_bindings{};
  religion::repentance_fallback::Context fallback_observation{};
  religion::repentance_recovery_inputs::Bindings recovery_bindings{};
  religion::repentance_recovery_inputs::Context recovery_observation{};
  ck3_12002::religion::Bindings route_religion_bindings{};
  ck3_12002::religion::doctrine12002::TenetParameterBindings route_parameter_bindings{};
  ck3_12002::religion::Context route_religion_observation{};
  ck3_12002::religion::doctrine12002::TenetParameterContext route_parameter_observation{};
  ck3_12002::religion::doctrine12002::FaithMainRiteDoctrines route_doctrine_observation{};
  religion::repentance_pam_route::Bindings pam_bindings{};
  religion::repentance_pam_route::Context pam_observation{};
  religion::repentance_petition::Bindings petition_bindings{};
  religion::repentance_petition::Terms petition_observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerRepentancePrivateStep12003(std::string_view step) noexcept;
bool ParsePlayerRepentanceRevision12003(
    std::string_view payload, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerRepentanceMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerRepentanceResult12003(
    const PlayerRepentanceMailboxContext12003 &, std::string_view request_id);
bool RunPlayerRepentanceMailbox12003(PlayerRepentanceMailboxContext12003 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerRepentancePrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12003
