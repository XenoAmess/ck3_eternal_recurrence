#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/realm_law_candidate_collection_11906.hpp"
#include "xar_bridge/realm_law_final_terms_11906.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kRealmLawPausedPrivateQueryStepV1 =
    "query-realm-law-final-terms-v1-private";

struct RealmLawPausedPrivateCandidateV1 {
  bridge::RealmLawFinalTerms11906Result terms{};
  std::string native_reason{};
};

struct RealmLawPausedPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  private_law::RealmLawCandidateCollection11906 collection{};
  std::array<std::array<RealmLawPausedPrivateCandidateV1,
                        private_law::kRealmLawMaximumRelevantCandidates11906>, 2>
      final{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteRealmLawPausedPrivateQueryV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeRealmLawPausedPrivateQueryV1(
    const RealmLawPausedPrivateQueryV1 &query);

} // namespace xar::ck3_11906
