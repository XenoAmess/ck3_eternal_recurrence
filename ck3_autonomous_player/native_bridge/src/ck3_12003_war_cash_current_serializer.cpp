#include "xar_bridge/ck3_12003_war_cash_current_serializer.hpp"
#include <limits>

namespace xar::ck3_12003::war_cash_current {
namespace {

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') {
      out += '\\';
      out += static_cast<char>(c);
    } else if (c < 0x20) {
      out += "\\u00";
      out += hex[c >> 4];
      out += hex[c & 15];
    } else {
      out += static_cast<char>(c);
    }
  }
  return out + '"';
}

std::string Bool(bool value) { return value ? "true" : "false"; }
std::string Reason(std::string_view value) {
  return value.empty() ? "null" : Quote(value);
}
std::string Fixed(const std::optional<std::int64_t> &value) {
  return value ? "{\"raw\":" + std::to_string(*value) +
                     ",\"scale\":100000}" : "null";
}

std::string LoanLeaf(const ActorResources &resources, const game::Snapshot &snapshot,
    std::uint64_t revision, bool same_frame_ready, std::string_view version,
    std::string_view sha) {
  if (!resources.holy_order_loan || version != ck3_12004::kGameVersion ||
      sha != ck3_12004::kExecutableSha256) return {};
  const auto &loan = *resources.holy_order_loan;
  const auto &f = loan.source_frame;
  const auto &s = f.execution_stamp;
  const bool frame = same_frame_ready && loan.completed &&
      f.full_snapshot_owner_retained && snapshot.paused && snapshot.map_ready &&
      snapshot.has_played_character && snapshot.played_character_alive &&
      f.snapshot_revision == revision && f.ticket_sequence && s.pump_epoch &&
      s.thread_id && s.paused && f.local_player_id == snapshot.player_id &&
      f.played_character_id > 0 && f.played_character_id == snapshot.played_character_id &&
      f.date_raw == snapshot.date_raw && s.date_raw == f.date_raw;
  const auto matches = [&](const auto &v) {
    return v.available && v.played_character_id == f.played_character_id &&
        v.date_raw == f.date_raw && v.capture_epoch == s.pump_epoch;
  };
  const bool costs = frame && loan.decision_costs && matches(*loan.decision_costs);
  const bool principal = frame && loan.principal && matches(*loan.principal) &&
      loan.principal->owned_temporaries_released &&
      loan.principal->prospective_principal_raw.has_value();
  const std::string cost_reason = costs ? "" : !frame ? "loan_cash_owner_frame_unqualified"
      : loan.decision_costs_unavailable_reason.empty() ? "decision_costs_unavailable"
                                                     : loan.decision_costs_unavailable_reason;
  const std::string principal_reason = principal ? "" : !frame ? "loan_cash_owner_frame_unqualified"
      : loan.principal_unavailable_reason.empty() ? "principal_unavailable"
                                                 : loan.principal_unavailable_reason;
  const std::string status = costs && principal ? "available" : costs || principal ? "partial" : "unavailable";
  // Preserve every copied stamp member. The Python caller still owns the full
  // episode/public snapshot/PID/connection frame; native values cannot invent it.
  const auto stamp = "{\"pump_epoch\":" + std::to_string(s.pump_epoch) +
      ",\"thread_id\":" + std::to_string(s.thread_id) +
      ",\"rng_wrapper\":" + std::to_string(s.rng_wrapper) +
      ",\"rng_state\":" + std::to_string(s.rng_state) +
      ",\"rng_owner_thread_id\":" + std::to_string(s.rng_owner_thread_id) +
      ",\"tls_initialized_flag_address\":" + std::to_string(s.tls_initialized_flag_address) +
      ",\"tls_initialized\":" + std::to_string(s.tls_initialized) +
      ",\"tls_context\":" + std::to_string(s.tls_context) +
      ",\"tls_main_thread_marker\":" + std::to_string(s.tls_main_thread_marker) +
      ",\"jomini_state\":" + std::to_string(s.jomini_state) +
      ",\"game_state\":" + std::to_string(s.game_state) +
      ",\"date_raw\":" + std::to_string(s.date_raw) + ",\"paused\":" + Bool(s.paused) + '}';
  return ",\"holy_order_loan_observation_v1\":{"
      "\"schema\":\"xar.ck3.holy-order-loan-war-cash.v1\",\"read_only\":true,"
      "\"advertised\":false,\"formal_action_ready\":false,\"status\":" + Quote(status) +
      ",\"source_frame\":{\"snapshot_revision\":" + std::to_string(f.snapshot_revision) +
      ",\"ticket_sequence\":" + std::to_string(f.ticket_sequence) +
      ",\"local_player_id\":" + std::to_string(f.local_player_id) +
      ",\"played_character_id\":" + std::to_string(f.played_character_id) +
      ",\"date_raw\":" + std::to_string(f.date_raw) +
      ",\"full_snapshot_owner_retained\":" + Bool(f.full_snapshot_owner_retained) +
      ",\"same_frame_ready\":" + Bool(frame) + ",\"execution_stamp\":" + stamp + '}' +
      ",\"decision_costs\":" + (costs ?
          ck3_12004::religion::loan_decision_costs::SerializeHolyOrderLoanDecisionCosts12004(
              *loan.decision_costs) : "null") +
      ",\"decision_costs_unavailable_reason\":" + Reason(cost_reason) +
      ",\"principal\":{\"status\":" + Quote(principal ? "available" : "unavailable") +
      ",\"value_key\":\"holy_order_gold_value\",\"raw_scale\":100000,\"prospective_principal_raw\":" +
      (principal ? std::to_string(*loan.principal->prospective_principal_raw) : "null") +
      ",\"owned_temporaries_released\":" + (principal ? "true" : "null") +
      ",\"unavailable_reason\":" + Reason(principal_reason) + '}' +
      ",\"complete_loan_terms\":false,\"existing_debt_principal_raw\":null,"
      "\"received_funds_verified\":false,\"funding_credit_raw\":0,\"submit_planned\":false}";
}

#if defined(XAR_ENABLE_WAR_PAYMENT_GENERIC_CONTEXT_12004)
template<class T> std::string RawOptional(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string RawValues(const ck3_12004::WarPaymentGenericValues12004 &v) {
  return "{\"context_identity_before\":"+RawOptional(v.context_identity_before)+
      ",\"context_identity_after\":"+RawOptional(v.context_identity_after)+
      ",\"value_2c0\":"+RawOptional(v.value_2c0)+",\"value_2c8\":"+RawOptional(v.value_2c8)+
      ",\"value_28\":"+RawOptional(v.value_28)+",\"value_30\":"+RawOptional(v.value_30)+
      ",\"capture_complete\":"+Bool(v.capture_complete)+",\"context_stable\":"+Bool(v.context_stable)+
      ",\"failed_reads\":"+std::to_string(v.failed_reads)+'}';
}
#endif
std::string CurrentRawContextLeaf(const ActorResources &resources,
    const game::Snapshot &snapshot,std::uint64_t revision,bool same_frame_ready) {
#if defined(XAR_ENABLE_WAR_PAYMENT_GENERIC_CONTEXT_12004)
  if(!resources.current_raw_context)return {};
  const auto &raw=*resources.current_raw_context;
  const auto &v=raw.values;
  const bool frame=same_frame_ready&&snapshot.paused&&snapshot.map_ready&&
      snapshot.has_played_character&&snapshot.played_character_alive&&raw.actor_identity_stable&&
      raw.character&&snapshot.played_character_id>0&&
      raw.character_full_id==static_cast<std::uint32_t>(snapshot.played_character_id);
  const bool aligned=v.context_identity_before&&*v.context_identity_before&&
      !(*v.context_identity_before%8)&&
      *v.context_identity_before<=(std::numeric_limits<std::uintptr_t>::max)()-0x2CF;
  const bool admitted=frame&&v.capture_complete&&aligned;
  const std::string reason=!frame?"war_cash_current_raw_context_frame_unqualified":
      !v.capture_complete?"war_cash_current_raw_context_incomplete":
      !aligned?"war_cash_current_raw_context_unaligned_or_overflow":"";
  return ",\"current_raw_context_v1\":{\"schema_version\":1,"
      "\"observation_kind\":\"paused_current_raw_context\","
      "\"attribution_scope\":\"current_raw_context_only\",\"maintenance_attribution\":\"unclosed\","
      "\"character\":"+std::to_string(raw.character)+",\"character_full_id\":"+std::to_string(raw.character_full_id)+
      ",\"snapshot_revision\":"+std::to_string(revision)+",\"date_raw\":"+std::to_string(snapshot.date_raw)+
      ",\"actor_identity_stable\":"+Bool(raw.actor_identity_stable)+",\"same_frame_ready\":"+Bool(same_frame_ready)+
      ",\"values\":"+RawValues(v)+",\"admission_ready\":"+Bool(admitted)+",\"unavailable_reason\":"+Reason(reason)+'}';
#else
  (void)resources;(void)snapshot;(void)revision;(void)same_frame_ready;
  return {};
#endif
}

std::string WarIds(const game::Snapshot &snapshot) {
  std::string out = "[";
  for (const auto &war : snapshot.active_wars) {
    if (out.size() > 1) out += ',';
    out += std::to_string(war.war_id);
  }
  return out + ']';
}
std::string ArmyIds(const game::Snapshot &snapshot) {
  std::string out = "[";
  for (const auto &army : snapshot.player_armies) {
    if (out.size() > 1) out += ',';
    out += std::to_string(army.army_id);
  }
  return out + ']';
}
std::string Expense(const MilitaryResources &resources, std::int32_t actor,
                    const std::string &war_ids, bool all_raised) {
  std::string vector = "null";
  if (resources.available) {
    vector = "[";
    for (const auto raw : resources.resources_raw) {
      if (vector.size() > 1) vector += ',';
      vector += std::to_string(raw);
    }
    vector += ']';
  }
  const std::string gold = resources.available
      ? std::to_string(resources.resources_raw[kGoldResourceSlot]) : "null";
  const std::string treasury = resources.available
      ? std::to_string(resources.resources_raw[kTreasuryResourceSlot]) : "null";
  return "{\"status\":" + Quote(resources.available ? "available" : "unavailable") +
      ",\"resource_kind\":" + Quote(all_raised
          ? "actor_military_all_raised_maintenance" : "actor_military_current_maintenance") +
      ",\"resource_id\":" + Quote(std::to_string(actor)) +
      ",\"owner_character_id\":" + std::to_string(actor) +
      ",\"war_ids\":" + war_ids +
      ",\"time_basis\":\"month\",\"raw_scale\":100000,"
      "\"source_scope\":\"actor_owned_military_once_across_all_wars\",\"source\":" +
      Quote(all_raised ? "native_character_all_raised_military_expenses"
                       : "native_character_current_military_expenses") +
      ",\"resource_raw_native\":" + vector + ",\"gold_raw\":" + gold +
      ",\"treasury_raw\":" + treasury +
      ",\"future_war_cost_upper_ready\":false,\"unavailable_reason\":" +
      (resources.available ? "null" :
       Quote(resources.unavailable_reason.empty() ? "native_military_expenses_unavailable"
                                                  : resources.unavailable_reason)) + '}';
}

} // namespace

std::string SerializeCurrentResourcesV1(
    const ActorResources &resources, const game::Snapshot &snapshot,
    std::uint64_t revision, bool same_frame_ready,
    std::string_view game_version, std::string_view executable_sha256) {
  const bool treasury = resources.current_treasury_raw.has_value();
  const bool income = resources.monthly_net_income_raw.has_value();
  const unsigned available = static_cast<unsigned>(treasury) +
      static_cast<unsigned>(income) + static_cast<unsigned>(resources.current.available) +
      static_cast<unsigned>(resources.all_raised.available);
  const std::string_view status = available == 4 ? "available"
      : available == 0 ? "unavailable" : "partial";
  const auto war_ids = WarIds(snapshot);
  const auto actor = snapshot.played_character_id;
  return "{\"step\":" + Quote(kCurrentStepV1) +
      ",\"accepted\":true,\"private_build\":true,\"read_only\":true,"
      "\"advertised\":false,\"war_cash_current_resources\":{"
      "\"schema\":\"xar.ck3.war-cash-current-resources.v1\","
      "\"game_version\":" + Quote(game_version) + ",\"executable_sha256\":" +
      Quote(executable_sha256) + ",\"status\":" + Quote(status) +
      ",\"read_only\":true,\"advertised\":false,\"formal_action_ready\":false,"
      "\"played_character_id\":" + std::to_string(actor) +
      ",\"snapshot_revision\":" + std::to_string(revision) +
      ",\"date_raw\":" + std::to_string(snapshot.date_raw) +
      ",\"active_war_ids\":" + war_ids + ",\"player_army_ids\":" + ArmyIds(snapshot) +
      CurrentRawContextLeaf(resources,snapshot,revision,same_frame_ready)+
      LoanLeaf(resources, snapshot, revision, same_frame_ready, game_version, executable_sha256) +
      ",\"current_treasury\":" + Fixed(resources.current_treasury_raw) +
      ",\"player_monthly_gross_income\":" + Fixed(resources.monthly_gross_income_raw) +
      ",\"player_monthly_total_expenses\":" + Fixed(resources.monthly_total_expenses_raw) +
      ",\"player_monthly_net_income\":" + Fixed(resources.monthly_net_income_raw) +
      ",\"monthly_income_semantics\":{\"version\":" +
      Quote("ck3-" + std::string(game_version) + "-native-income-minus-total-expenses-v2") + ","
      "\"time_basis\":\"month\",\"source_scope\":\"played_character_personal_gold\","
      "\"income_source\":\"native_character_monthly_gold_income\","
      "\"expense_source\":\"native_character_monthly_total_gold_expenses\","
      "\"military_expenses_included\":true},"
      "\"monthly_gross_income_unavailable_reason\":" +
      (resources.monthly_gross_income_raw ? "null" : Reason(resources.gross_income_unavailable_reason)) +
      ",\"monthly_total_expenses_unavailable_reason\":" +
      (resources.monthly_total_expenses_raw ? "null" : Reason(resources.total_expenses_unavailable_reason)) +
      ",\"current_treasury_unavailable_reason\":" +
      (treasury ? "null" : Reason(resources.treasury_unavailable_reason)) +
      ",\"monthly_net_income_unavailable_reason\":" +
      (income ? "null" : Reason(resources.income_unavailable_reason)) +
      ",\"military_expenses\":{\"current\":" +
      Expense(resources.current, actor, war_ids, false) + ",\"all_raised\":" +
      Expense(resources.all_raised, actor, war_ids, true) + "},\"readiness\":{"
      "\"current_treasury_ready\":" + Bool(treasury) +
      ",\"monthly_gross_income_ready\":" + Bool(resources.monthly_gross_income_raw.has_value()) +
      ",\"monthly_total_expenses_ready\":" + Bool(resources.monthly_total_expenses_raw.has_value()) +
      ",\"monthly_net_income_ready\":" + Bool(income) +
      ",\"current_military_expenses_ready\":" + Bool(resources.current.available) +
      ",\"all_raised_military_expenses_ready\":" + Bool(resources.all_raised.available) +
      ",\"same_frame_ready\":" + Bool(same_frame_ready) +
      "},\"unobserved_future_inputs\":[\"pending_war_cash_raw\","
      "\"future_war_cost_upper_raw\",\"future_risk_budget_raw\","
      "\"policy_minimum_gold_reserve_raw\",\"horizon_days\",\"future_bound_assumptions\"],"
      "\"unavailable_reason\":" + (available == 4 ? "null" :
      Quote(resources.unavailable_reason.empty() ? "war_cash_current_resources_unavailable"
                                                 : resources.unavailable_reason)) + "}}";
}

} // namespace xar::ck3_12003::war_cash_current
