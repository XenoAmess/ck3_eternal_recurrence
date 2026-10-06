#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_confucian_assembly_predicates.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kConfucianAssemblyPrivateStep12003 =
    "query-confucian-assembly-predicates-v1";
inline constexpr std::string_view kConfucianAssemblyDomainKey12003 =
    "confucian_assembly_predicates_v1";
inline constexpr std::string_view kConfucianAssemblyBackend12003 =
    "ck3-1.20.0.3-native-confucian-assembly-predicates-v1";

struct ConfucianAssemblyMailboxContext12003 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  confucian_assembly::Bindings bindings{};
  confucian_assembly::Snapshot observation{};
  bool completed = false;
  std::string failure;
};

bool IsConfucianAssemblyPrivateStep12003(std::string_view step) noexcept;
bool ParseConfucianAssemblyRevision12003(std::string_view payload,
                                       std::uint64_t &expected_revision) noexcept;
bool ExecuteConfucianAssemblyMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeConfucianAssemblyResult12003(
    const ConfucianAssemblyMailboxContext12003 &, std::string_view request_id);

// The worker owns the context through terminal Wait/Reclaim. Owned native
// bindings let the offline fixture exercise the same reader and serializer.
bool RunConfucianAssemblyMailbox12003(ConfucianAssemblyMailboxContext12003 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandleConfucianAssemblyPrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12003
