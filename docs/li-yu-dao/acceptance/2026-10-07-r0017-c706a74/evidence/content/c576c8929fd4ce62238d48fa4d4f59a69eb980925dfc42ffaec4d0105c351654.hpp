#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/h2743_stock_predicate_reader_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

#ifndef XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1
#define XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1 0
#endif

namespace xar::ck3_11906 {

// Reuses the existing baseline wire step; it adds no public capability/action.
inline constexpr std::string_view kH2743StockPrivateStepPrefixV1 =
    "query-defender-de-jure-exit-terms-v1-";

bool ParseH2743StockPrivateStepV1(std::string_view step,
                                std::int32_t &war_id) noexcept;

struct H2743StockPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  const game::GameAdapter *game = nullptr;
  std::uintptr_t module_base = 0;
  std::uint64_t expected_revision = 0;
  game::Snapshot expected_snapshot{};
  std::int32_t war_id = -1;
  game::ReadDefenderDeJureExitTermsV1Result read_result =
      game::ReadDefenderDeJureExitTermsV1Result::unavailable;
  game::DefenderDeJureExitTermsV1 baseline{};
  game::H2743StockPredicateResultV1 stock{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
  bool completed = false;
  std::string_view failure_stage = "not_executed";
};

bool ExecuteH2743StockPrivateQueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept;

// A typed unavailable value remains null with an explicit reason. This never
// supplies an evaluated duration, persisted expiry, exit permission or action.
game::DefenderDeJureExitTermsV1::TruceInput H2743StockTypedInputV1(
    const game::H2743StockPredicateValueV1 &input);

std::string SerializeH2743StockPrivateEvidenceV1(
    const H2743StockPrivateQueryV1 &query);

} // namespace xar::ck3_11906
