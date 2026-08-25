#include "xar_bridge/combat_simulation_inputs_v3_mailbox.hpp"

#include <windows.h>

#include <algorithm>
#include <atomic>
#include <charconv>
#include <utility>

namespace xar::ck3_11906 {
namespace {

bool IsExecutingExactMailboxSlot(
    const CombatSimulationInputsV3MailboxContext &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.expected_snapshot_revision == 0 || query.module_base == 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor ==
             &ExecuteCombatSimulationInputsV3MailboxQuery &&
         mailbox.executor_context ==
             const_cast<CombatSimulationInputsV3MailboxContext *>(&query);
}

bool SnapshotContainsFullGenerationArmyId(
    const game::Snapshot &snapshot, std::int32_t army_id) noexcept {
  const auto contains = [army_id](const auto &armies) {
    return std::any_of(armies.begin(), armies.end(),
                       [army_id](const game::ArmySnapshot &army) {
                         return army.army_id == army_id;
                       });
  };
  if (army_id <= 0) {
    return false;
  }
  if (contains(snapshot.player_armies)) {
    return true;
  }
  for (const auto &war : snapshot.active_wars) {
    if (contains(war.allied_armies) || contains(war.enemy_armies)) {
      return true;
    }
  }
  return false;
}

bool GenerationBoundEncounterMatchesExpectedSnapshot(
    const game::Snapshot &snapshot,
    const game::CombatSimulationInputsRequest &request) noexcept {
  return !request.attacker_army_ids.empty() &&
         !request.defender_army_ids.empty() &&
         std::all_of(request.attacker_army_ids.begin(),
                     request.attacker_army_ids.end(),
                     [&snapshot](std::int32_t army_id) {
                       return SnapshotContainsFullGenerationArmyId(snapshot,
                                                                   army_id);
                     }) &&
         std::all_of(request.defender_army_ids.begin(),
                     request.defender_army_ids.end(),
                     [&snapshot](std::int32_t army_id) {
                       return SnapshotContainsFullGenerationArmyId(snapshot,
                                                                   army_id);
                     });
}

bool SameExpectedFrame(const game::Snapshot &snapshot,
                       const CombatSimulationInputsV3MailboxContext &query,
                       const MainThreadExecutionStampV1 &stamp) noexcept {
  // Snapshot equality binds every full-generation ArmyID, CharacterID and
  // WarID in the encounter scope in addition to the explicit pause/date
  // boundary.  ReadCombatSimulationInputsV3 independently generation-checks
  // the resolved native objects before publishing its payload.
  return snapshot == query.expected_snapshot && snapshot.paused &&
         snapshot.date_raw == stamp.date_raw &&
         GenerationBoundEncounterMatchesExpectedSnapshot(snapshot,
                                                          query.request);
}

bool PhaseRuntimeReady(std::uintptr_t module_base,
                       std::string_view &failure) noexcept {
  failure = {};
  switch (ReadCombatSimulationInputsV3PhaseRuntimeStatus(module_base)) {
  case CombatSimulationInputsV3PhaseRuntimeStatus::ready:
    return true;
  case CombatSimulationInputsV3PhaseRuntimeStatus::module_unavailable:
    failure = "native_phase_module_unavailable";
    return false;
  case CombatSimulationInputsV3PhaseRuntimeStatus::
      accolade_scripted_rules_uninitialized:
    failure =
        "native_phase_accolade_scripted_rules_singleton_uninitialized";
    return false;
  case CombatSimulationInputsV3PhaseRuntimeStatus::
      accolade_type_database_uninitialized:
    failure = "native_phase_accolade_type_database_uninitialized";
    return false;
  case CombatSimulationInputsV3PhaseRuntimeStatus::
      accolade_owner_named_key_unregistered:
    failure = "native_phase_accolade_owner_named_key_unregistered";
    return false;
  }
  return false;
}

game::ReadCombatSimulationInputsV3Result ReadBaseOnlyPhaseUnavailable(
    const Bindings &bindings,
    const game::CombatSimulationInputsRequest &request,
    std::string_view reason,
    game::CombatSimulationInputsV3Snapshot &output) noexcept {
  game::CombatSimulationInputsSnapshot base{};
  const auto base_result = ReadCombatSimulationInputs(bindings, request, base);
  switch (base_result) {
  case game::ReadCombatSimulationInputsResult::requires_paused:
    return game::ReadCombatSimulationInputsV3Result::requires_paused;
  case game::ReadCombatSimulationInputsResult::no_played_character:
    return game::ReadCombatSimulationInputsV3Result::no_played_character;
  case game::ReadCombatSimulationInputsResult::invalid_arguments:
    return game::ReadCombatSimulationInputsV3Result::invalid_arguments;
  case game::ReadCombatSimulationInputsResult::target_province_not_found:
    return game::ReadCombatSimulationInputsV3Result::
        target_province_not_found;
  case game::ReadCombatSimulationInputsResult::army_not_in_scope:
    return game::ReadCombatSimulationInputsV3Result::army_not_in_scope;
  case game::ReadCombatSimulationInputsResult::invalid_encounter:
    return game::ReadCombatSimulationInputsV3Result::invalid_encounter;
  case game::ReadCombatSimulationInputsResult::partial:
    return game::ReadCombatSimulationInputsV3Result::base_inputs_unavailable;
  case game::ReadCombatSimulationInputsResult::unavailable:
    return game::ReadCombatSimulationInputsV3Result::unavailable;
  case game::ReadCombatSimulationInputsResult::available:
    break;
  }
  if (!base.input_observation_ready || base.armies.empty()) {
    return game::ReadCombatSimulationInputsV3Result::base_inputs_unavailable;
  }
  output = {};
  output.base_inputs = std::move(base);
  output.phase_event_inputs.unavailable_reason = std::string(reason);
  return game::ReadCombatSimulationInputsV3Result::phase_inputs_unavailable;
}

} // namespace

bool ParseCombatSimulationInputsV3ExpectedRevision(
    std::string_view json, std::uint64_t &output) noexcept {
  output = 0;
  constexpr std::string_view key = "\"expected_revision\":";
  const auto at = json.find(key);
  if (at == std::string_view::npos ||
      json.find(key, at + key.size()) != std::string_view::npos) {
    return false;
  }
  auto begin = at + key.size();
  while (begin < json.size() &&
         (json[begin] == ' ' || json[begin] == '\t' ||
          json[begin] == '\r' || json[begin] == '\n')) {
    ++begin;
  }
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') {
    ++end;
  }
  auto delimiter = end;
  while (delimiter < json.size() &&
         (json[delimiter] == ' ' || json[delimiter] == '\t' ||
          json[delimiter] == '\r' || json[delimiter] == '\n')) {
    ++delimiter;
  }
  if (end == begin || (json[begin] == '0' && end - begin != 1U) ||
      (delimiter < json.size() && json[delimiter] != ',' &&
       json[delimiter] != '}')) {
    return false;
  }
  const auto parsed =
      std::from_chars(json.data() + begin, json.data() + end, output);
  return parsed.ec == std::errc{} && parsed.ptr == json.data() + end &&
         output > 0;
}

CombatSimulationInputsV3PhaseRuntimeStatus
ReadCombatSimulationInputsV3PhaseRuntimeStatus(
    std::uintptr_t module_base) noexcept {
  if (module_base == 0) {
    return CombatSimulationInputsV3PhaseRuntimeStatus::module_unavailable;
  }
  if (*reinterpret_cast<void **>(
          module_base +
          kCombatSimulationInputsV3AccoladeScriptedRulesSingletonSlotRva) ==
      nullptr) {
    return CombatSimulationInputsV3PhaseRuntimeStatus::
        accolade_scripted_rules_uninitialized;
  }
  if (*reinterpret_cast<void **>(
          module_base +
          kCombatSimulationInputsV3AccoladeTypeDatabaseSlotRva) == nullptr) {
    return CombatSimulationInputsV3PhaseRuntimeStatus::
        accolade_type_database_uninitialized;
  }
  if (*reinterpret_cast<std::int32_t *>(
          module_base +
          kCombatSimulationInputsV3AccoladeOwnerNamedKeyIdRva) == -1) {
    return CombatSimulationInputsV3PhaseRuntimeStatus::
        accolade_owner_named_key_unregistered;
  }
  return CombatSimulationInputsV3PhaseRuntimeStatus::ready;
}

bool ExecuteCombatSimulationInputsV3MailboxQuery(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<CombatSimulationInputsV3MailboxContext *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          CombatSimulationInputsV3MailboxCompletion::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion = CombatSimulationInputsV3MailboxCompletion::
          infrastructure_rejected;
    }
    return false;
  }

  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;

    // Gate every can_be_acclaimed prerequisite before any snapshot or
    // Character resolution.  The checks are raw reads only and never call the
    // lazy scripted-rules constructor or the named-key interner.
    std::string_view prerequisite_failure;
    const bool phase_runtime_ready =
        PhaseRuntimeReady(query->module_base, prerequisite_failure);

    game::Snapshot before{};
    if (!ReadSnapshot(query->bindings, before) ||
        !SameExpectedFrame(before, *query, stamp)) {
      query->result = {};
      query->query_result =
          game::ReadCombatSimulationInputsV3Result::unavailable;
      query->completion =
          CombatSimulationInputsV3MailboxCompletion::frame_changed;
      return true;
    }

    query->query_result =
        phase_runtime_ready
            ? ReadCombatSimulationInputsV3(query->bindings, query->request,
                                           query->result)
            : ReadBaseOnlyPhaseUnavailable(
                  query->bindings, query->request, prerequisite_failure,
                  query->result);

    game::Snapshot after{};
    if (!ReadSnapshot(query->bindings, after) || after != before ||
        !SameExpectedFrame(after, *query, stamp)) {
      query->result = {};
      query->query_result =
          game::ReadCombatSimulationInputsV3Result::unavailable;
      query->completion =
          CombatSimulationInputsV3MailboxCompletion::frame_changed;
      return true;
    }

    if (query->query_result ==
        game::ReadCombatSimulationInputsV3Result::available) {
      query->completion =
          CombatSimulationInputsV3MailboxCompletion::available;
      return true;
    }
    if (query->query_result == game::ReadCombatSimulationInputsV3Result::
                                   phase_inputs_unavailable) {
      query->completion = CombatSimulationInputsV3MailboxCompletion::
          phase_inputs_unavailable;
      return true;
    }
    query->result = {};
    query->completion =
        CombatSimulationInputsV3MailboxCompletion::query_unavailable;
    return true;
  } catch (...) {
    query->result = {};
    query->query_result =
        game::ReadCombatSimulationInputsV3Result::unavailable;
    query->completion =
        CombatSimulationInputsV3MailboxCompletion::query_unavailable;
    return true;
  }
}

std::string_view CombatSimulationInputsV3FailureMessage(
    MainThreadQueryWaitResultV1 wait,
    CombatSimulationInputsV3MailboxCompletion completion,
    game::ReadCombatSimulationInputsV3Result query_result,
    bool completion_snapshot_stable) noexcept {
  switch (wait) {
  case MainThreadQueryWaitResultV1::executor_failed:
    return "application-main combat-input v3 executor failed";
  case MainThreadQueryWaitResultV1::infrastructure_failed:
    return "application-main combat-input v3 boundary drifted";
  case MainThreadQueryWaitResultV1::cancelled:
    return "application-main combat-input v3 query was cancelled";
  case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
    return "application-main combat-input v3 query timed out before execution";
  case MainThreadQueryWaitResultV1::timeout_executor_already_running:
    return "application-main combat-input v3 executor is still running";
  case MainThreadQueryWaitResultV1::ticket_mismatch:
    return "application-main combat-input v3 ticket mismatch";
  case MainThreadQueryWaitResultV1::completed:
    break;
  }
  if ((completion == CombatSimulationInputsV3MailboxCompletion::available ||
       completion == CombatSimulationInputsV3MailboxCompletion::
                         phase_inputs_unavailable) &&
      (query_result == game::ReadCombatSimulationInputsV3Result::available ||
       query_result == game::ReadCombatSimulationInputsV3Result::
                           phase_inputs_unavailable)) {
    return completion_snapshot_stable
               ? "application-main combat-input v3 result is inconsistent"
               : "combat-input v3 completion snapshot changed";
  }
  if (completion ==
      CombatSimulationInputsV3MailboxCompletion::frame_changed) {
    return "combat-input v3 application-main frame changed";
  }
  switch (query_result) {
  case game::ReadCombatSimulationInputsV3Result::requires_paused:
    return "CK3 combat-input v3 query requires a paused map";
  case game::ReadCombatSimulationInputsV3Result::no_played_character:
    return "no living played CK3 character";
  case game::ReadCombatSimulationInputsV3Result::invalid_arguments:
    return "combat-input v3 query arguments are invalid";
  case game::ReadCombatSimulationInputsV3Result::target_province_not_found:
    return "combat-input v3 target province was not found";
  case game::ReadCombatSimulationInputsV3Result::army_not_in_scope:
    return "combat-input v3 army is outside allowed scope";
  case game::ReadCombatSimulationInputsV3Result::invalid_encounter:
    return "selected armies do not form a canonical v3 encounter";
  case game::ReadCombatSimulationInputsV3Result::base_inputs_unavailable:
    return "CK3 combat-input v3 base slice is unavailable";
  case game::ReadCombatSimulationInputsV3Result::available:
  case game::ReadCombatSimulationInputsV3Result::phase_inputs_unavailable:
    return "application-main combat-input v3 completion is inconsistent";
  case game::ReadCombatSimulationInputsV3Result::unavailable:
    return "CK3 combat-input v3 query is unavailable";
  }
  return "application-main combat-input v3 failure state is unknown";
}

} // namespace xar::ck3_11906
