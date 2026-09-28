#pragma once

#include "active_scheme_precondition_command_binders_v1_private.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/faction_gift_receivers_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActiveSchemeSwayPrivateQueryPrefixV1 =
    "query-active-scheme-sway-target-v1-private-";

bool ParseActiveSchemeSwayPrivateQueryStepV1(std::string_view step,
                                             std::uint32_t &target_id) noexcept;

struct ActiveSchemeSwayPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  std::uint32_t target_character_id = 0;
  xar::bridge::ActiveSchemeStateV1PrivateObservation active{};
  xar::bridge::ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
  GiftOpinionReceiverResultV1 target_opinion{};
  bool matching_active_scheme = false;
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActiveSchemeSwayPrivateQueryV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;

std::string SerializeActiveSchemeSwayPrivateQueryV1(
    const ActiveSchemeSwayPrivateQueryV1 &query);

} // namespace xar::ck3_11906
