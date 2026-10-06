#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_county_conversion.hpp"
#include "xar_bridge/ck3_12003_clergy_candidate_terms.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerClergyAppointmentPrivateStep12002 =
    "query-player-clergy-appointment-v1";
inline constexpr std::string_view kPlayerClergyAppointmentDomainKey12002 =
    "player_clergy_appointment_v1";
inline constexpr std::string_view kPlayerClergyAppointmentBackend12002 =
    "ck3-1.20.0.2-native-player-clergy-appointment-v1";

struct PlayerClergyAppointmentRequest12002 {
  std::int32_t candidate_character_id = -1;
  std::uint64_t expected_revision = 0;
  // Optional internal binding from the unchanged public clergy API.
  // Older requests leave zero and omit the new .3 sibling.
  std::uint64_t expected_public_revision = 0;
};

struct PlayerClergyAppointmentMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  PlayerClergyAppointmentRequest12002 request{};
  religion::clergy::Bindings bindings{};
  religion::clergy::Observation observation{};
  // Present only for the actual exact .3 adapter; the existing .2 query is unchanged.
  std::optional<ck3_12003::religion::county_conversion::Environment> county_conversion_environment;
  std::optional<ck3_12003::religion::county_conversion::Observation> county_conversion_observation;
  std::optional<ck3_12003::religion::clergy_candidate_terms::Environment> candidate_terms_environment;
  std::optional<ck3_12003::religion::clergy_candidate_terms::Observation> candidate_terms_observation;
  std::string candidate_terms_snapshot_id;
  bool completed = false;
  std::string failure;
};

bool IsPlayerClergyCandidateTermsMainThread12002(void *) noexcept;
bool CapturePlayerClergyCandidateTermsFrame12002(void *, CouncilCandidatesFrameV1 &) noexcept;

bool IsPlayerClergyAppointmentPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerClergyAppointmentRequest12002(
    std::string_view payload, PlayerClergyAppointmentRequest12002 &request) noexcept;
bool ExecutePlayerClergyAppointmentMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerClergyAppointmentResult12002(
    const PlayerClergyAppointmentMailboxContext12002 &, std::string_view request_id);
bool RunPlayerClergyAppointmentMailbox12002(
    PlayerClergyAppointmentMailboxContext12002 &, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerClergyAppointmentPrivate12002(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
