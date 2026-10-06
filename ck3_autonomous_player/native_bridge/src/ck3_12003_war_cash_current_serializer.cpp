#include "xar_bridge/ck3_12003_war_cash_current_serializer.hpp"

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
