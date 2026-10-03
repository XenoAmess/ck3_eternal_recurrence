#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kPlayerHolyOrderContextPrivateStep12003 =
    "query-player-holy-order-context-v1";
inline constexpr std::string_view kPlayerHolyOrderContextDomainKey12003 =
    "player_holy_order_context_v1";
inline constexpr std::string_view kPlayerHolyOrderContextBackend12003 =
    "ck3-1.20.0.3-native-player-holy-order-context-v1";

struct PlayerHolyOrderMailboxContext12003 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  ck3_12002::CoreBindings core{};
  religion::holy_order::Bindings bindings{};
  religion::holy_order::Context observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerHolyOrderContextPrivateStep12003(std::string_view step) noexcept;
bool ParsePlayerHolyOrderContextRevision12003(
    std::string_view payload, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerHolyOrderContextMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerHolyOrderContextResult12003(
    const PlayerHolyOrderMailboxContext12003 &, std::string_view request_id);
bool RunPlayerHolyOrderContextMailbox12003(PlayerHolyOrderMailboxContext12003 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerHolyOrderContextPrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12003
