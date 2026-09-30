#include "xar_bridge/h2743_stock_private_query_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <atomic>
#include <charconv>
#include <utility>

namespace xar::ck3_11906 {
namespace {

template <class T>
bool ReadNative(std::uintptr_t address, T &out) noexcept {
  if (address == 0) return false;
  SIZE_T read = 0;
  return ReadProcessMemory(GetCurrentProcess(),
                          reinterpret_cast<const void *>(address), &out,
                          sizeof(out), &read) != FALSE && read == sizeof(out);
}

bool FreshNativeStamp(const MainThreadQueryMailboxV1 &mailbox,
                      const MainThreadExecutionStampV1 &stamp) noexcept {
  std::uintptr_t game_state = 0, jomini_state = 0;
  std::int32_t date = 0;
  std::uint8_t paused = 0, initialized = 0, marker = 0;
  if (mailbox.tls_context_getter == nullptr ||
      !ReadNative(mailbox.game_state_slot, game_state) ||
      !ReadNative(mailbox.jomini_state_slot, jomini_state) ||
      game_state != stamp.game_state || jomini_state != stamp.jomini_state ||
      !ReadNative(game_state + kGameStateDateRawOffset, date) ||
      !ReadNative(jomini_state + kJominiPausedOffset, paused) ||
      !ReadNative(mailbox.tls_initialized_flag, initialized) ||
      date != stamp.date_raw || paused != 1 || initialized != 1)
    return false;
  std::uintptr_t tls = 0;
  __try {
    tls = reinterpret_cast<std::uintptr_t>(mailbox.tls_context_getter());
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
  return tls == stamp.tls_context &&
         ReadNative(tls + kMainThreadTlsMarkerOffset, marker) && marker == 1;
}

bool OwnsPausedSlot(const H2743StockPrivateQueryV1 &query,
                    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.game == nullptr || query.expected_revision == 0 ||
      query.war_id <= 0 || stamp.pump_epoch == 0 || stamp.thread_id == 0 ||
      !stamp.paused || stamp.game_state == 0 || stamp.jomini_state == 0 ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      GetCurrentThreadId() != stamp.thread_id) {
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
         mailbox.permitted_h2743_stock_predicate_executor ==
             &ExecuteH2743StockPrivateQueryV1 &&
         mailbox.executor == &ExecuteH2743StockPrivateQueryV1 &&
         mailbox.executor_context == &query && FreshNativeStamp(mailbox, stamp);
}

bool ObserveStamp(void *opaque,
                  game::H2743StockPredicateStampV1 &out) noexcept {
  out = {};
  auto *query = static_cast<H2743StockPrivateQueryV1 *>(opaque);
  if (query == nullptr || !OwnsPausedSlot(*query, query->execution_stamp))
    return false;
  try {
    game::Snapshot actual{};
    if (!game::ReadSnapshot(*query->game, actual) ||
        actual != query->expected_snapshot || !actual.paused ||
        !actual.map_ready || !actual.has_played_character ||
        !actual.played_character_alive || actual.played_character_id <= 0 ||
        actual.date_raw != query->execution_stamp.date_raw)
      return false;
    const auto matches = std::count_if(
        actual.active_wars.begin(), actual.active_wars.end(),
        [&](const game::ActiveWarSnapshot &war) {
          return war.war_id == query->war_id &&
                 war.player_side == game::PlayerWarSide::defender &&
                 war.player_is_primary_war_leader &&
                 war.primary_opponent_character_id > 0 &&
                 war.primary_opponent_character_id != actual.played_character_id;
        });
    if (matches != 1 || std::count_if(
            actual.active_wars.begin(), actual.active_wars.end(),
            [&](const game::ActiveWarSnapshot &war) {
              return war.war_id == query->war_id;
            }) != 1)
      return false;
    out.actor_id = static_cast<std::uint32_t>(actual.played_character_id);
    out.war_id = static_cast<std::uint32_t>(query->war_id);
    out.date_raw = actual.date_raw;
    // Both fields bind the actual bridge's hash-bound published snapshot. The
    // pump epoch proves execution ownership and is not a snapshot revision.
    out.revision = query->expected_revision;
    out.native_revision = query->expected_revision;
    out.paused = actual.paused;
    out.living_map = actual.map_ready && actual.played_character_alive;
    return OwnsPausedSlot(*query, query->execution_stamp);
  } catch (...) {
    return false;
  }
}

std::string_view FailureName(game::H2743StockPredicateFailureV1 failure) {
  using F = game::H2743StockPredicateFailureV1;
  switch (failure) {
  case F::none: return "none";
  case F::disabled: return "stock_condition_reader_disabled";
  case F::wrong_session: return "stock_condition_wrong_session";
  case F::read_failed: return "stock_condition_read_failed";
  case F::stale_identity: return "stock_condition_stale_identity";
  case F::cache_unavailable: return "stock_condition_cache_unavailable";
  case F::bounded_extent_exceeded: return "stock_condition_bounded_extent_exceeded";
  case F::identifier_unavailable: return "stock_condition_identifier_unavailable";
  case F::phase_unavailable: return "stock_condition_phase_unavailable";
  case F::definition_unavailable: return "stock_condition_definition_unavailable";
  case F::unstable_sample: return "stock_condition_unstable_sample";
  }
  return "stock_condition_unknown_failure";
}

} // namespace

bool ParseH2743StockPrivateStepV1(std::string_view step,
                                std::int32_t &war_id) noexcept {
  war_id = -1;
  if (!step.starts_with(kH2743StockPrivateStepPrefixV1)) return false;
  const auto token = step.substr(kH2743StockPrivateStepPrefixV1.size());
  if (token.empty() || token.size() > 10 || token.front() == '0') return false;
  for (const auto digit : token)
    if (digit < '0' || digit > '9') return false;
  const auto [end, error] =
      std::from_chars(token.data(), token.data() + token.size(), war_id);
  return error == std::errc{} && end == token.data() + token.size() && war_id > 0;
}

bool ExecuteH2743StockPrivateQueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
#if !XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1
  (void)opaque;
  (void)stamp;
  return false;
#else
  auto *query = static_cast<H2743StockPrivateQueryV1 *>(opaque);
  if (query == nullptr) return false;
  ++query->executor_invocations;
  query->execution_stamp = stamp;
  query->completed = false;
  query->failure_stage = "application_main_ownership";
  if (query->executor_invocations != 1 || !OwnsPausedSlot(*query, stamp))
    return false;
  try {
    game::H2743StockPredicateStampV1 expected{};
    query->failure_stage = "admission_frame";
    if (!ObserveStamp(query, expected)) return true;
    query->read_result = game::ReadDefenderDeJureExitTermsV1(
        *query->game, query->war_id, query->baseline);
    const auto expected_war = std::find_if(
        query->expected_snapshot.active_wars.begin(),
        query->expected_snapshot.active_wars.end(),
        [&](const game::ActiveWarSnapshot &war) {
          return war.war_id == query->war_id;
        });
    if (query->read_result !=
        game::ReadDefenderDeJureExitTermsV1Result::available_baseline ||
        !query->baseline.same_frame_stable || query->baseline.material_complete ||
        query->baseline.war_id != query->war_id ||
        query->baseline.date_raw != expected.date_raw ||
        query->baseline.primary_defender_character_id !=
            static_cast<std::int32_t>(expected.actor_id) ||
        expected_war == query->expected_snapshot.active_wars.end() ||
        query->baseline.primary_attacker_character_id !=
            expected_war->primary_opponent_character_id ||
        query->baseline.target_title_ids != expected_war->targeted_title_ids) {
      query->failure_stage = "baseline_unavailable";
      return true;
    }
    game::H2743StockNativeContextV1 context{};
    context.module_base = query->module_base;
    context.application_main_thread_id = stamp.thread_id;
    // Successful installation has already checked the frozen executable and
    // all native pump anchors; this owner checks that exact installed mailbox.
    context.exact_build_verified = query->module_base != 0 &&
        query->mailbox->module_base == query->module_base &&
        !query->mailbox->offline_fixture &&
        query->mailbox->iat_hook_installed.load(std::memory_order_acquire);
    context.stamp_opaque = query;
    context.observe_stamp = &ObserveStamp;
    const auto bindings = game::BindH2743StockNativeSourcesV1(context);
    query->stock = game::ReadH2743StockPredicatesV1(bindings, expected);
    query->failure_stage = "completion_frame";
    game::H2743StockPredicateStampV1 after{};
    if (!ObserveStamp(query, after) || after != expected) return true;
    if (query->stock.double_sample_stable &&
        (query->stock.stamp != expected ||
         query->stock.attacker_id != static_cast<std::uint32_t>(
             query->baseline.primary_attacker_character_id) ||
         query->stock.defender_id != expected.actor_id)) {
      query->failure_stage = "stock_party_binding";
      return true;
    }
    query->failure_stage = {};
    query->completed = true;
    return true;
  } catch (...) {
    query->failure_stage = "reader_exception";
    return true;
  }
#endif
}

game::DefenderDeJureExitTermsV1::TruceInput H2743StockTypedInputV1(
    const game::H2743StockPredicateValueV1 &input) {
  game::DefenderDeJureExitTermsV1::TruceInput result{};
  using S = game::H2743StockPredicateStateV1;
  if (input.failure == game::H2743StockPredicateFailureV1::none &&
      (input.state == S::observed_native_true ||
       input.state == S::observed_native_false)) {
    result.value = input.state == S::observed_native_true;
    result.unavailable_reason.clear();
  } else {
    result.unavailable_reason = FailureName(input.failure);
  }
  return result;
}

std::string SerializeH2743StockPrivateEvidenceV1(
    const H2743StockPrivateQueryV1 &query) {
  const auto number = [](auto value) { return std::to_string(value); };
  const auto boolean = [](bool value) { return value ? "true" : "false"; };
  const bool parties_bound = query.stock.double_sample_stable &&
      query.stock.stamp.actor_id ==
          static_cast<std::uint32_t>(query.expected_snapshot.played_character_id) &&
      query.stock.stamp.war_id == static_cast<std::uint32_t>(query.war_id) &&
      query.stock.stamp.date_raw == query.expected_snapshot.date_raw &&
      query.stock.stamp.revision == query.expected_revision &&
      query.stock.stamp.native_revision == query.expected_revision &&
      query.stock.stamp.paused && query.stock.stamp.living_map &&
      query.stock.attacker_id == static_cast<std::uint32_t>(
          query.baseline.primary_attacker_character_id) &&
      query.stock.defender_id == static_cast<std::uint32_t>(
          query.baseline.primary_defender_character_id);
  std::string result =
      "{\"schema\":\"xar.ck3.h2743-stock-predicate-evidence.v1\"";
  result += ",\"native_revision\":" + number(query.expected_revision);
  result += ",\"date_raw\":" + number(query.expected_snapshot.date_raw);
  result += ",\"actor_character_id\":" +
      number(query.expected_snapshot.played_character_id);
  result += ",\"war_id\":" + number(query.war_id);
  result += ",\"attacker_character_id\":" +
      number(query.baseline.primary_attacker_character_id);
  result += ",\"defender_character_id\":" +
      number(query.baseline.primary_defender_character_id);
  result += ",\"paused\":" + std::string(boolean(query.execution_stamp.paused));
  result += ",\"map_ready\":" + std::string(boolean(query.expected_snapshot.map_ready));
  result += ",\"application_main_thread_id\":" + number(query.execution_stamp.thread_id);
  result += ",\"pump_epoch\":" + number(query.execution_stamp.pump_epoch);
  result += ",\"mailbox_sequence\":" + number(query.ticket.sequence);
  result += ",\"executor_invocations\":" + number(query.executor_invocations);
  result += ",\"same_frame_stable\":" +
      std::string(boolean(query.completed && query.baseline.same_frame_stable));
  result += ",\"stock_double_sample_stable\":" +
      std::string(boolean(query.stock.double_sample_stable));
  result += ",\"stock_parties_bound\":" + std::string(boolean(parties_bound));
  result += ",\"material_complete\":false}";
  return result;
}

} // namespace xar::ck3_11906
