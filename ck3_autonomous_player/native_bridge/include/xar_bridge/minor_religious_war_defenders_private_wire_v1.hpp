#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/minor_religious_war_defenders_v1.hpp"
#include "xar_bridge/war_entry_assessments_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kMinorReligiousWarDefendersPrivateStepPrefixV1 =
        "query-minor-religious-war-defenders-v1-";

bool ParseMinorReligiousWarDefendersPrivateStepV1(
    std::string_view step, std::int32_t &target_character_id) noexcept;

struct MinorReligiousWarDefendersPrivateResultV1 {
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  game::DeclarableWarSnapshot declaration{};
  game::WarEntryAssessmentRowV1 assessment{};
  MinorReligiousDefenderReadbackV1 defenders{};
};

struct MinorReligiousWarDefendersPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  const game::GameAdapter *game = nullptr;
  std::uintptr_t module_base = 0;
  WarEntryNativeEnvironmentV1 war_environment{};
  MinorReligiousDefenderEnvironmentV1 defender_environment{};
  std::uint64_t expected_revision = 0;
  game::Snapshot expected_snapshot{};
  std::vector<game::DeclarableWarSnapshot> expected_declarations;
  game::DeclarableWarSnapshot chosen_declaration{};
  std::int32_t target_character_id = -1;

  MinorReligiousWarDefendersPrivateResultV1 result{};
  std::string failure_stage;
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
  bool available = false;
};

bool ExecuteMinorReligiousWarDefendersPrivateQueryV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept;

std::string SerializeMinorReligiousWarDefendersPrivateResultV1(
    const MinorReligiousWarDefendersPrivateResultV1 &result);

} // namespace xar::ck3_11906
