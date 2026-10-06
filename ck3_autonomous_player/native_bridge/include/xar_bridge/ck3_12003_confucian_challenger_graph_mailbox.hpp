#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_challenger_graph_readback.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kConfucianChallengerGraphPrivateStep12003 =
    "query-confucian-challenger-graph-v1";
inline constexpr std::string_view kConfucianChallengerGraphDomainKey12003 =
    "confucian_challenger_graph_v1";
inline constexpr std::string_view kConfucianChallengerGraphBackend12003 =
    "ck3-1.20.0.3-native-confucian-challenger-graph-v1";

struct ConfucianChallengerGraphMailboxContext12003 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  challenger_graph::Bindings bindings{};
  challenger_graph::Observation observation{};
  challenger_graph::Request request{};
  bool completed = false;
  std::string failure;
};

bool IsConfucianChallengerGraphPrivateStep12003(std::string_view step) noexcept;
bool ParseConfucianChallengerGraphRevision12003(std::string_view payload,
                                       std::uint64_t &expected_revision) noexcept;
bool ExecuteConfucianChallengerGraphMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeConfucianChallengerGraphResult12003(
    const ConfucianChallengerGraphMailboxContext12003 &, std::string_view request_id);

// The worker owns the context through terminal Wait/Reclaim. Owned native
// bindings let the offline fixture exercise the same reader and serializer.
bool RunConfucianChallengerGraphMailbox12003(ConfucianChallengerGraphMailboxContext12003 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandleConfucianChallengerGraphPrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12003
