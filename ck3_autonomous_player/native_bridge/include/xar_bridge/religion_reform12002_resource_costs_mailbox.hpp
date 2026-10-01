#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_reform12002_resource_costs.hpp"
#include "xar_bridge/religion_reform12002_window.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionDraftResourceCostsPrivateStep12002 =
    "query-player-religion-draft-resource-costs-v1";
inline constexpr std::string_view kPlayerReligionDraftResourceCostsDomainKey12002 =
    "player_religion_draft_resource_costs_v1";
inline constexpr std::string_view kPlayerReligionDraftResourceCostsBackend12002 =
    "ck3-1.20.0.2-native-player-religion-draft-resource-costs-v1";

struct PlayerReligionDraftResourceCostsObservation12002 {
  bool available = false;
  bool draft_observed = false;
  std::string failure;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  religion_reform::DraftWindowView current_window{};
  religion_reform::BaseResourceCostQuote base_resource_cost_quote{};
};

struct PlayerReligionDraftResourceCostsMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  religion_reform::DraftWindowBindings window_bindings{};
  religion_reform::CostBindings cost_bindings{};
  PlayerReligionDraftResourceCostsObservation12002 observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionDraftResourceCostsPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionDraftResourceCostsRevision12002(std::string_view payload,
    std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionDraftResourceCostsMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionDraftResourceCostsObservation12002(
    const PlayerReligionDraftResourceCostsObservation12002 &);
std::string SerializePlayerReligionDraftResourceCostsResult12002(
    const PlayerReligionDraftResourceCostsMailboxContext12002 &, std::string_view request_id);
bool RunPlayerReligionDraftResourceCostsMailbox12002(
    PlayerReligionDraftResourceCostsMailboxContext12002 &, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerReligionDraftResourceCostsPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
