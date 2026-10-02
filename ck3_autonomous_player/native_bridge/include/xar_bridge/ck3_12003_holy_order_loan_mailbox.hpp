#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_holy_order_loan_context.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerHolyOrderLoanPrivateStep12003 =
    ck3_12003::religion::loan::kQueryStep;
inline constexpr std::string_view kPlayerHolyOrderLoanDomainKey12003 =
    ck3_12003::religion::loan::kDomain;
inline constexpr std::string_view kPlayerHolyOrderLoanBackend12003 =
    "ck3-1.20.0.3-native-player-holy-order-loan-context-v1";

struct PlayerHolyOrderLoanMailboxContext12003 {
  QueryMailboxEnvelope envelope{};
  ck3_12003::religion::loan::Bindings bindings{};
  ck3_12003::religion::loan::Context observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerHolyOrderLoanPrivateStep12003(std::string_view step) noexcept;
bool ParsePlayerHolyOrderLoanRevision12003(
    std::string_view payload, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerHolyOrderLoanMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerHolyOrderLoanResult12003(
    const PlayerHolyOrderLoanMailboxContext12003 &, std::string_view request_id);
bool RunPlayerHolyOrderLoanMailbox12003(PlayerHolyOrderLoanMailboxContext12003 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerHolyOrderLoanPrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
