#include "xar_bridge/ck3_1210_personal_cash_v1.hpp"

#include <algorithm>
#include <limits>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_1210 {
namespace {

bool SameCore(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}

bool SameBindings(const CoreBindings &a, const CoreBindings &b) noexcept {
  return a.enabled && b.enabled && a.game_state_slot == b.game_state_slot &&
      a.jomini_state_slot == b.jomini_state_slot &&
      a.character_storage_slot == b.character_storage_slot &&
      a.get_local_player == b.get_local_player;
}

bool BasisCore(const xar::game::Snapshot &s, const CoreSnapshotPrefix &p) noexcept {
  return s.date_raw == p.clock.date_raw && s.speed == p.clock.speed &&
      s.paused == p.clock.paused && s.player_id == p.local_player_id &&
      s.map_ready == p.map_ready && s.has_played_character == p.has_played_character &&
      s.played_character_id == p.played_character_id &&
      s.played_character_alive == p.played_character_alive &&
      s.played_character_gold.scale == kPersonalGoldScaleV1;
}

bool Fail(PersonalCashObservationV1 &out, std::string_view reason) noexcept {
  out.completed = out.same_frame_ready = false;
  out.personal_gold_raw.reset();
  out.monthly_gross_income_raw.reset();
  out.monthly_total_expenses_raw.reset();
  out.monthly_net_income_raw.reset();
  out.unavailable_reason = out.monthly_unavailable_reason = out.net_unavailable_reason = reason;
  return false;
}

bool FullCall(PersonalCashReadFullV1 read, void *context,
    xar::game::Snapshot &snapshot, std::uint64_t &revision) {
#if defined(_MSC_VER)
  __try {
#endif
    return read(context, snapshot, revision);
#if defined(_MSC_VER)
  } __except (GetExceptionCode() == 0xE06D7363UL
      ? EXCEPTION_CONTINUE_SEARCH : EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool CurrentFull(const PersonalCashReadContextV1 &c,
    const xar::game::Snapshot &basis, PersonalCashObservationV1 &out) {
  xar::game::Snapshot current{};
  std::uint64_t revision = 0;
  ++out.current_full_call_attempts;
  return FullCall(c.read_current_full, c.read_current_full_context, current, revision) &&
      revision == c.published_native_revision && current == basis &&
      *c.published_full == basis;
}

bool CurrentCore(const CoreBindings &b, const CoreSnapshotPrefix &expected) noexcept {
  CoreSnapshotPrefix actual{};
  return ReadCoreSnapshot(b, actual) && SameCore(actual, expected);
}

bool Scope(const xar::game::Snapshot &basis, PersonalCashObservationV1 &out) {
  // Preserve actual order. These bounds are availability bounds, not claims
  // about engine limits or proof that a nonempty Full family is qualified.
  if (basis.active_wars.size() > 1024 || basis.player_armies.size() > 4096) return false;
  for (const auto &war : basis.active_wars) {
    if (war.war_id <= 0 || std::find(out.active_war_ids.begin(),
        out.active_war_ids.end(), war.war_id) != out.active_war_ids.end()) return false;
    out.active_war_ids.push_back(war.war_id);
  }
  for (const auto &army : basis.player_armies) {
    if (army.army_id < 0 || std::find(out.player_army_ids.begin(),
        out.player_army_ids.end(), army.army_id) != out.player_army_ids.end()) return false;
    out.player_army_ids.push_back(army.army_id);
  }
  return true;
}

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) {
      out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15];
    } else out += static_cast<char>(c);
  }
  return out + '"';
}
std::string Bool(bool value) { return value ? "true" : "false"; }
std::string Fixed(const std::optional<std::int64_t> &value, bool emit) {
  return emit && value ? "{\"raw\":" + std::to_string(*value) +
      ",\"scale\":100000}" : "null";
}
std::string Reason(bool ready, std::string_view reason) {
  return ready ? "null" : Quote(reason.empty() ? "personal_cash_unavailable" : reason);
}
std::string Ids(const std::vector<std::int32_t> &ids) {
  std::string out = "[";
  for (const auto id : ids) {
    if (out.size() > 1) out += ',';
    out += std::to_string(id);
  }
  return out + ']';
}
std::string Military(std::int32_t actor, const std::string &wars, bool raised) {
  return "{\"status\":\"unavailable\",\"resource_kind\":" +
      Quote(raised ? "actor_military_all_raised_maintenance" :
          "actor_military_current_maintenance") +
      ",\"resource_id\":" + Quote(std::to_string(actor)) +
      ",\"owner_character_id\":" + std::to_string(actor) +
      ",\"war_ids\":" + wars + ",\"time_basis\":\"month\",\"raw_scale\":100000,"
      "\"source_scope\":\"actor_owned_military_once_across_all_wars\","
      "\"source\":" + Quote(raised ? "native_character_all_raised_military_expenses" :
          "native_character_current_military_expenses") +
      ",\"resource_raw_native\":null,\"gold_raw\":null,\"treasury_raw\":null,"
      "\"future_war_cost_upper_ready\":false,\"unavailable_reason\":" +
      Quote(kPersonalCashMilitaryUnknownV1) + '}';
}

} // namespace

PersonalCashBindingsV1 BindPersonalCashImageV1(std::uintptr_t base,
    std::string_view sha) noexcept {
  PersonalCashBindingsV1 b{};
  b.gold = BindPersonalGoldImageV1(base, sha);
  b.monthly = BindMonthlyFlowImageV1(base, sha);
  b.exact_build_admitted = b.gold.exact_build_admitted && b.monthly.exact_build_admitted;
  return b;
}

bool ReadPersonalCashV1(const PersonalCashBindingsV1 &b,
    const PersonalCashReadContextV1 &context, PersonalCashObservationV1 &out) noexcept {
  out = {};
  try {
    const auto c = context;
    if (!b.exact_build_admitted || !b.gold.exact_build_admitted ||
        !b.monthly.exact_build_admitted || !SameBindings(b.gold.core, b.monthly.core))
      return Fail(out, "personal_cash_exact_binding_unavailable");
    if (!b.integration_native_calls_permitted || !b.monthly.integration_native_calls_permitted)
      return Fail(out, "personal_cash_integration_gate_closed");
    if (!c.paused_application_main_owner_admitted)
      return Fail(out, "personal_cash_paused_main_owner_required");
    const auto p = c.expected_core;
    if (c.published_full == nullptr || c.read_current_full == nullptr ||
        c.published_native_revision == 0 || !p.clock.paused || !p.map_ready ||
        !p.has_played_character || !p.played_character_alive || p.played_character_id == -1)
      return Fail(out, "personal_cash_published_full_basis_required");
    const xar::game::Snapshot basis = *c.published_full;
    if (!BasisCore(basis, p)) return Fail(out, "personal_cash_full_core_mismatch");
    if (!CurrentCore(b.gold.core, p)) return Fail(out, "personal_cash_core_changed");
    if (!CurrentFull(c, basis, out)) return Fail(out, "personal_cash_current_full_changed");
    out.frame = p;
    out.native_revision = c.published_native_revision;
    if (!Scope(basis, out)) {
      out.active_war_ids.clear(); out.player_army_ids.clear();
      return Fail(out, "personal_cash_full_scope_unrepresentable");
    }
    PersonalGoldObservationV1 before{};
    if (!ReadPersonalGoldV1(b.gold, p, before) || !before.available ||
        !before.same_frame_ready || !before.personal_gold_raw ||
        *before.personal_gold_raw != basis.played_character_gold.raw)
      return Fail(out, "personal_cash_wallet_basis_changed");

    MonthlyFlowObservationV1 monthly{};
    const bool monthly_ok = ReadMonthlyFlowV1(b.monthly, p, monthly);
    out.context_call_attempts = monthly.context_call_attempts;
    out.gross_call_attempted = monthly.gross_call_attempted;
    out.expenses_call_attempted = monthly.expenses_call_attempted;
    const bool flow_ready = monthly_ok && monthly.available && monthly.same_frame_ready &&
        monthly.gross_ready && monthly.total_expenses_ready &&
        monthly.monthly_gross_income_raw && monthly.monthly_total_expenses_raw;
    const auto flow_reason = flow_ready ? std::string_view{} :
        (monthly.unavailable_reason.empty() ? std::string_view{"personal_cash_monthly_unavailable"} :
          monthly.unavailable_reason);
    if (!CurrentFull(c, basis, out)) return Fail(out, "personal_cash_current_full_changed");
    PersonalGoldObservationV1 after{};
    if (!ReadPersonalGoldV1(b.gold, p, after) || !after.available ||
        !after.same_frame_ready || after.personal_gold_raw != before.personal_gold_raw ||
        !after.personal_gold_raw || *after.personal_gold_raw != basis.played_character_gold.raw)
      return Fail(out, "personal_cash_wallet_changed");
    if (!CurrentCore(b.gold.core, p) || *c.published_full != basis ||
        context.published_native_revision != c.published_native_revision ||
        !SameCore(context.expected_core, p) || context.published_full != c.published_full ||
        context.read_current_full != c.read_current_full ||
        context.read_current_full_context != c.read_current_full_context ||
        context.paused_application_main_owner_admitted != c.paused_application_main_owner_admitted)
      return Fail(out, "personal_cash_core_or_basis_changed");

    out.personal_gold_raw = before.personal_gold_raw;
    if (!flow_ready) {
      // A failed native monthly call is not an observed zero. The independent
      // wallet survives only after the same real Full/Core/wallet guards.
      out.completed = out.same_frame_ready = true;
      out.monthly_unavailable_reason = out.net_unavailable_reason = flow_reason;
      out.unavailable_reason = "personal_cash_monthly_and_military_unavailable";
      return true;
    }
    out.monthly_gross_income_raw = monthly.monthly_gross_income_raw;
    out.monthly_total_expenses_raw = monthly.monthly_total_expenses_raw;
    // Validate the existing reader's arithmetic; do not create another source.
    std::int64_t checked = 0;
    const bool fits = CheckedMonthlyNetV1(*out.monthly_gross_income_raw,
        *out.monthly_total_expenses_raw, checked);
    if (fits != monthly.net_ready ||
        (fits ? !monthly.monthly_net_income_raw || *monthly.monthly_net_income_raw != checked :
          monthly.monthly_net_income_raw.has_value()))
      return Fail(out, "personal_cash_monthly_net_inconsistent");
    out.monthly_net_income_raw = monthly.monthly_net_income_raw;
    out.completed = out.same_frame_ready = true;
    out.monthly_unavailable_reason = {};
    out.net_unavailable_reason = fits ? std::string_view{} :
        std::string_view{"war_cash_monthly_net_income_overflow"};
    out.unavailable_reason = "personal_cash_military_maintenance_unavailable";
    return true;
  } catch (...) {
    return Fail(out, "personal_cash_callback_or_copy_failed");
  }
}

std::string SerializePersonalCashV1(const PersonalCashObservationV1 &o) {
  std::int64_t checked = 0;
  const bool pair = o.monthly_gross_income_raw && o.monthly_total_expenses_raw;
  const bool fits = pair && CheckedMonthlyNetV1(*o.monthly_gross_income_raw,
      *o.monthly_total_expenses_raw, checked);
  const bool all_monthly_unknown = !o.monthly_gross_income_raw &&
      !o.monthly_total_expenses_raw && !o.monthly_net_income_raw;
  const bool arithmetic = all_monthly_unknown || (pair && (fits ? o.monthly_net_income_raw &&
      *o.monthly_net_income_raw == checked : !o.monthly_net_income_raw));
  const bool emit = o.completed && o.same_frame_ready && o.native_revision != 0 &&
      o.frame.clock.paused && o.frame.map_ready && o.frame.has_played_character &&
      o.frame.played_character_alive && o.frame.played_character_id != -1 &&
      o.personal_gold_raw && arithmetic;
  const bool flow = emit && pair;
  const bool net = flow && fits;
  const auto actor = o.frame.played_character_id;
  const auto wars = Ids(o.active_war_ids);
  const auto reason = o.completed && !emit ?
      std::string_view{"personal_cash_observation_inconsistent"} : o.unavailable_reason;
  const auto flow_reason = emit && !flow ? o.monthly_unavailable_reason : reason;
  const auto net_reason = flow && !fits ?
      std::string_view{"war_cash_monthly_net_income_overflow"} :
      emit && !flow ? o.net_unavailable_reason : reason;
  std::string out = "{\"step\":" + Quote(kPersonalCashStepV1) +
      ",\"accepted\":true,\"private_build\":true,\"read_only\":true,"
      "\"advertised\":false,\"war_cash_current_resources\":{\"schema\":" +
      Quote(kPersonalCashSchemaV1) + ",\"game_version\":" + Quote(kGameVersion) +
      ",\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"status\":" + Quote(emit ? "partial" : "unavailable") +
      ",\"read_only\":true,\"advertised\":false,\"formal_action_ready\":false,"
      "\"played_character_id\":" + std::to_string(actor) +
      ",\"snapshot_revision\":" + std::to_string(o.native_revision) +
      ",\"date_raw\":" + std::to_string(o.frame.clock.date_raw) +
      ",\"active_war_ids\":" + wars + ",\"player_army_ids\":" + Ids(o.player_army_ids) +
      ",\"current_treasury\":" + Fixed(o.personal_gold_raw, emit) +
      ",\"player_monthly_gross_income\":" + Fixed(o.monthly_gross_income_raw, flow) +
      ",\"player_monthly_total_expenses\":" + Fixed(o.monthly_total_expenses_raw, flow) +
      ",\"player_monthly_net_income\":" + Fixed(o.monthly_net_income_raw, net) +
      ",\"monthly_income_semantics\":{\"version\":"
      "\"ck3-1.21.0-native-income-minus-total-expenses-v2\",\"time_basis\":\"month\","
      "\"source_scope\":\"played_character_personal_gold\","
      "\"income_source\":\"native_character_monthly_gold_income\","
      "\"expense_source\":\"native_character_monthly_total_gold_expenses\","
      "\"military_expenses_included\":true},\"current_treasury_unavailable_reason\":" +
      Reason(emit, reason) + ",\"monthly_gross_income_unavailable_reason\":" +
      Reason(flow, flow_reason) + ",\"monthly_total_expenses_unavailable_reason\":" +
      Reason(flow, flow_reason) + ",\"monthly_net_income_unavailable_reason\":" +
      Reason(net, net_reason) + ",\"military_expenses\":{\"current\":" +
      Military(actor, wars, false) + ",\"all_raised\":" + Military(actor, wars, true) +
      "},\"readiness\":{\"same_frame_ready\":" + Bool(emit) +
      ",\"current_treasury_ready\":" + Bool(emit) +
      ",\"monthly_gross_income_ready\":" + Bool(flow) +
      ",\"monthly_total_expenses_ready\":" + Bool(flow) +
      ",\"monthly_net_income_ready\":" + Bool(net) +
      ",\"current_military_expenses_ready\":false,\"all_raised_military_expenses_ready\":false},"
      "\"complete_snapshot\":false,\"true_treasury_observed\":false,"
      "\"military_categories_observed\":false,\"tax_categories_observed\":false,"
      "\"prosperity_observed\":false,\"native_getter_diagnostics\":{"
      "\"current_full_call_attempts\":" + std::to_string(o.current_full_call_attempts) +
      ",\"context_call_attempts\":" + std::to_string(o.context_call_attempts) +
      ",\"gross_call_attempted\":" + Bool(o.gross_call_attempted) +
      ",\"expenses_call_attempted\":" + Bool(o.expenses_call_attempted) +
      ",\"zero_native_side_effects_verified\":false,\"native_unwind_cleanup_verified\":false},"
      "\"unobserved_future_inputs\":[\"pending_war_cash_raw\",\"future_war_cost_upper_raw\","
      "\"future_risk_budget_raw\",\"policy_minimum_gold_reserve_raw\",\"horizon_days\","
      "\"future_bound_assumptions\"],\"unavailable_reason\":" + Reason(false, reason) + "}}";
  return out;
}

} // namespace xar::ck3_1210
