#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12003_holy_order_selected_title_terms.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kPlayerHolyOrderSelectedTitleTermsPrivateStep12003 =
    "query-player-holy-order-selected-title-terms-v1";
inline constexpr std::string_view kPlayerHolyOrderSelectedTitleTermsDomainKey12003 =
    "player_holy_order_selected_title_terms_v1";
inline constexpr std::string_view kPlayerHolyOrderSelectedTitleTermsBackend12003 =
    "ck3-1.20.0.3-native-player-holy-order-selected-title-terms-v1";

struct PlayerHolyOrderSelectedTitleTermsMailboxContext12003 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  ck3_12002::CoreBindings core{};
  religion::holy_order::selected_title_terms::Bindings bindings{};
  religion::holy_order::selected_title_terms::Context observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerHolyOrderSelectedTitleTermsPrivateStep12003(std::string_view step) noexcept;
bool ParsePlayerHolyOrderSelectedTitleTermsRevision12003(
    std::string_view payload, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerHolyOrderSelectedTitleTermsMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerHolyOrderSelectedTitleTermsResult12003(
    const PlayerHolyOrderSelectedTitleTermsMailboxContext12003 &, std::string_view request_id);
bool RunPlayerHolyOrderSelectedTitleTermsMailbox12003(PlayerHolyOrderSelectedTitleTermsMailboxContext12003 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerHolyOrderSelectedTitleTermsPrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12003
