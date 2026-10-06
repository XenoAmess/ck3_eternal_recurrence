#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_religious_title_readback.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kConfucianReligiousTitlePrivateStep12003 =
    "query-confucian-religious-title-v1";
inline constexpr std::string_view kConfucianReligiousTitleDomainKey12003 =
    "confucian_religious_title_v1";
inline constexpr std::string_view kConfucianReligiousTitleBackend12003 =
    "ck3-1.20.0.3-native-confucian-religious-title-v1";

struct ConfucianReligiousTitleMailboxContext12003 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  religious_title::Bindings bindings{};
  religious_title::Observation observation{};
  bool completed = false;
  std::string failure;
};

bool IsConfucianReligiousTitlePrivateStep12003(std::string_view step) noexcept;
bool ParseConfucianReligiousTitleRevision12003(std::string_view payload,
                                       std::uint64_t &expected_revision) noexcept;
bool ExecuteConfucianReligiousTitleMailbox12003(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeConfucianReligiousTitleResult12003(
    const ConfucianReligiousTitleMailboxContext12003 &, std::string_view request_id);

// The worker owns the context through terminal Wait/Reclaim. Owned native
// bindings let the offline fixture exercise the same reader and serializer.
bool RunConfucianReligiousTitleMailbox12003(ConfucianReligiousTitleMailboxContext12003 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandleConfucianReligiousTitlePrivate12003(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12003
