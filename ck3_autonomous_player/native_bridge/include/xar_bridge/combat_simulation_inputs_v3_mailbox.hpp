#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/combat_v3.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

// Read by the application-main executor before entering the phase reader.
// A null slot is a normal loading/not-yet-initialized state.  The executor
// must publish a typed phase_inputs_unavailable result without calling the
// reader that can otherwise reach CK3's lazy runtime paths.
// Exact accessor 0x1B36670 reads this slot before its lazy construction path.
inline constexpr std::uintptr_t
    kCombatSimulationInputsV3AccoladeScriptedRulesSingletonSlotRva =
        0x57C2060;
inline constexpr std::uintptr_t
    kCombatSimulationInputsV3AccoladeTypeDatabaseSlotRva = 0x570C030;
inline constexpr std::uintptr_t
    kCombatSimulationInputsV3AccoladeOwnerNamedKeyIdRva = 0x57EB620;

inline constexpr std::uint32_t
    kCombatSimulationInputsV3QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kCombatSimulationInputsV3ExecutingWaitSliceMilliseconds = 2'000;

bool ParseCombatSimulationInputsV3ExpectedRevision(
    std::string_view json, std::uint64_t &output) noexcept;

enum class CombatSimulationInputsV3PhaseRuntimeStatus : std::uint32_t {
  ready = 0,
  module_unavailable = 1,
  accolade_scripted_rules_uninitialized = 2,
  accolade_type_database_uninitialized = 3,
  accolade_owner_named_key_unregistered = 4,
};

CombatSimulationInputsV3PhaseRuntimeStatus
ReadCombatSimulationInputsV3PhaseRuntimeStatus(
    std::uintptr_t module_base) noexcept;

enum class CombatSimulationInputsV3MailboxCompletion : std::uint32_t {
  not_executed = 0,
  available = 1,
  phase_inputs_unavailable = 2,
  query_unavailable = 3,
  frame_changed = 4,
  infrastructure_rejected = 5,
};

struct CombatSimulationInputsV3MailboxContext {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::CombatSimulationInputsRequest request{};
  std::uint64_t expected_snapshot_revision = 0;
  game::Snapshot expected_snapshot{};
  std::uintptr_t module_base = 0;

  CombatSimulationInputsV3MailboxCompletion completion =
      CombatSimulationInputsV3MailboxCompletion::not_executed;
  game::ReadCombatSimulationInputsV3Result query_result =
      game::ReadCombatSimulationInputsV3Result::unavailable;
  game::CombatSimulationInputsV3Snapshot result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  CombatSimulationInputsV3MailboxContext() = default;
  CombatSimulationInputsV3MailboxContext(
      const CombatSimulationInputsV3MailboxContext &) = delete;
  CombatSimulationInputsV3MailboxContext &operator=(
      const CombatSimulationInputsV3MailboxContext &) = delete;
  CombatSimulationInputsV3MailboxContext(
      CombatSimulationInputsV3MailboxContext &&) = delete;
  CombatSimulationInputsV3MailboxContext &operator=(
      CombatSimulationInputsV3MailboxContext &&) = delete;
};

bool ExecuteCombatSimulationInputsV3MailboxQuery(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view CombatSimulationInputsV3FailureMessage(
    MainThreadQueryWaitResultV1 wait,
    CombatSimulationInputsV3MailboxCompletion completion,
    game::ReadCombatSimulationInputsV3Result query_result,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteCombatSimulationInputsV3MailboxQuery),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
