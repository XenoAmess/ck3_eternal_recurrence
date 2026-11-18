#include "xar_bridge/ck3_1210_personal_cash_v1.hpp"

// Reuse the independent RAM world and strict JSON reader. Run the complete
// original V1 regression first; none of this constitutes actual-module proof.
#define main PersonalCashLegacyFixtureMainV1
#include "ck3_1210_personal_cash_v1_test.cpp"
#undef main

namespace {
void Armies(Fixture &f, const std::vector<std::int32_t> &ids) {
  f.world.player_armies.clear();
  for (const auto id : ids) {
    xar::game::ArmySnapshot army{}; army.army_id = id;
    army.owner_character_id = f.actor_id; f.world.player_armies.push_back(army);
  }
  f.published = f.world;
}
Json CashV2(const PersonalCashObservationV1 &out) {
  const auto result = JsonReader(SerializePersonalCashV2(out)).Document();
  Require(result.At("step").Text() == kPersonalCashStepV2 &&
      result.At("accepted").Flag() && result.At("read_only").Flag() &&
      result.At("private_build").Flag() && !result.At("advertised").Flag(),
      "V2 has an independent exact step");
  const auto cash = result.At("war_cash_current_resources");
  Require(cash.At("schema").Text() == kPersonalCashSchemaV2 &&
      cash.At("game_version").Text() == "1.21.0" &&
      cash.At("executable_sha256").Text() == kExecutableSha256,
      "V2 binds exact schema and Florin provenance");
  return cash;
}
PersonalCashObservationV1 ReadV2(Fixture &f) {
  PersonalCashObservationV1 out{};
  Require(ReadPersonalCashV2(f.bindings, f.request, out) && out.completed && out.same_frame_ready &&
      out.scope_version == PersonalCashScopeVersion::florin_unit_full_id_v2,
      "V2 provider records explicit V2 scope provenance");
  Attempts(f, out); return out;
}
void FailureV2(Fixture &f, bool before_monthly = false) {
  PersonalCashObservationV1 out{}; out.completed = out.same_frame_ready = true;
  out.personal_gold_raw = out.monthly_gross_income_raw = out.monthly_total_expenses_raw =
      out.monthly_net_income_raw = 123;
  Require(!ReadPersonalCashV2(f.bindings, f.request, out) && !out.completed &&
      !out.same_frame_ready && !out.personal_gold_raw && !out.monthly_gross_income_raw &&
      !out.monthly_total_expenses_raw && !out.monthly_net_income_raw,
      "V2 failure clears all stale amounts and readiness");
  Attempts(f, out); const auto cash = CashV2(out);
  Require(cash.At("status").Text() == "unavailable" && cash.At("current_treasury").IsNull() &&
      cash.At("player_monthly_net_income").IsNull() &&
      !cash.At("readiness").At("same_frame_ready").Flag(), "failed V2 is explicit unknown");
  if (before_monthly) Require(f.context_calls == 0 && f.gross_calls == 0 && f.expense_calls == 0,
      "invalid scope cannot reach monthly native callbacks");
  UnknownScope(out, cash);
}
} // namespace

int main(int argc, char **argv) {
  const std::vector<std::int32_t> ids{(std::numeric_limits<std::int32_t>::min)(),
      -2, (std::numeric_limits<std::int32_t>::max)(), kActor};
  if (argc == 2) {
    Require(std::string_view{argv[1]} == "--emit-json", "known V2 emission option");
    Fixture f; Armies(f, ids);
    std::cout << SerializePersonalCashV2(ReadV2(f)) << '\n'; return 0;
  }
  Require(argc == 1, "no unexpected V2 fixture arguments");
  Require(PersonalCashLegacyFixtureMainV1(argc, argv) == 0, "original V1 regression retained");
  {
    Fixture f; Armies(f, ids); const auto out = ReadV2(f); const auto cash = CashV2(out);
    Require(out.player_army_ids == ids && f.full_calls == 2 && f.context_calls == 2 &&
        f.gross_calls == 1 && f.expense_calls == 1, "V2 preserves ID order and call bounds");
    Require(cash.At("player_army_ids").elements.size() == ids.size(), "V2 ID count preserved");
    for (std::size_t i = 0; i != ids.size(); ++i)
      Require(cash.At("player_army_ids").elements[i].Number() == std::to_string(ids[i]),
          "signed UnitFullId serializes exactly without mask/absolute value");
    Fixed(cash, "current_treasury", f.wallet); Fixed(cash, "player_monthly_gross_income", f.gross);
    Fixed(cash, "player_monthly_total_expenses", f.expenses); Fixed(cash, "player_monthly_net_income", -220000);
    UnknownScope(out, cash);
    const auto old = Cash(out);
    Require(old.At("current_treasury").IsNull() && old.At("player_army_ids").elements.empty(),
        "V2 DTO cannot be relabeled as qualified V1 cash");
  }
  {
    Fixture f; const auto cash = CashV2(Read(f));
    Require(cash.At("current_treasury").IsNull() && cash.At("player_army_ids").elements.empty(),
        "positive V1 DTO still requires a separate V2 read");
  }
  for (const auto id : {std::int32_t{0}, (std::numeric_limits<std::int32_t>::min)(),
      std::int32_t{-2}, (std::numeric_limits<std::int32_t>::max)(), kActor}) {
    Fixture f; Armies(f, {id}); const auto out = ReadV2(f);
    Require(out.player_army_ids == std::vector<std::int32_t>{id}, "each UnitFullId boundary retained");
  }
  for (const auto id : {(std::numeric_limits<std::int32_t>::min)(), -2, kActor}) {
    Fixture f; Armies(f, {id}); Failure(f);
    Require(f.full_calls == 1 && f.context_calls == 0, "V1 still rejects negative IDs before monthly");
  }
  const std::vector<std::vector<std::int32_t>> bad{{-1}, {0, 0}, {-2, -2}, {0, -1}};
  for (const auto &scope : bad) { Fixture f; Armies(f, scope); FailureV2(f, true); }
  for (const std::int32_t count : {4096, 4097}) {
    Fixture f; std::vector<std::int32_t> scope;
    for (std::int32_t i = 0; i != count; ++i)
      scope.push_back(i == 0 ? (std::numeric_limits<std::int32_t>::min)() : i);
    Armies(f, scope);
    if (count == 4096) Require(ReadV2(f).player_army_ids == scope, "4096 exact IDs admitted");
    else FailureV2(f, true);
  }
  for (const std::int32_t war_id : {0, -2, 17}) {
    Fixture f; f.world.active_wars[1].war_id = war_id; f.published = f.world;
    FailureV2(f, true);
  }
  for (const std::int32_t count : {1024, 1025}) {
    Fixture f; f.world.active_wars.clear();
    for (std::int32_t i = 0; i != count; ++i) {
      xar::game::ActiveWarSnapshot war{}; war.war_id = i + 1; f.world.active_wars.push_back(war);
    }
    f.published = f.world;
    if (count == 1024) Require(ReadV2(f).active_war_ids.size() == 1024, "1024 positive wars admitted");
    else FailureV2(f, true);
  }
  for (const auto mode : {Mode::full_before_fail, Mode::full_after_fail, Mode::revision_before,
      Mode::revision_after, Mode::war_after, Mode::army_after, Mode::wallet_after,
      Mode::wallet_after_full, Mode::date_gross, Mode::pause_gross, Mode::actor_generation,
      Mode::published_basis_after, Mode::request_revision_after, Mode::full_throw_before,
      Mode::full_throw_after, Mode::full_fault_after}) {
    Fixture f; Armies(f, ids); f.mode = mode; FailureV2(f);
  }
  for (unsigned gate = 0; gate != 3; ++gate) {
    Fixture f;
    if (gate == 0) f.bindings.integration_native_calls_permitted = false;
    if (gate == 1) f.bindings.monthly.integration_native_calls_permitted = false;
    if (gate == 2) f.request.paused_application_main_owner_admitted = false;
    FailureV2(f, true);
    Require(f.core_calls == 0 && f.full_calls == 0, "V2 closed gate makes zero callbacks");
  }
  {
    Fixture f; Armies(f, ids); f.mode = Mode::null_context; const auto out = ReadV2(f);
    const auto cash = CashV2(out); Fixed(cash, "current_treasury", f.wallet);
    Require(cash.At("player_monthly_gross_income").IsNull() &&
        !cash.At("readiness").At("monthly_net_income_ready").Flag(),
        "V2 wallet-only partial keeps monthly unknown"); UnknownScope(out, cash);
  }
  for (unsigned mutation = 0; mutation != 3; ++mutation) {
    Fixture f; auto out = ReadV2(f);
    if (mutation == 0) out.player_army_ids = {-1};
    if (mutation == 1) out.player_army_ids = {-2, -2};
    if (mutation == 2) out.scope_version = static_cast<PersonalCashScopeVersion>(99);
    const auto cash = CashV2(out);
    Require(cash.At("current_treasury").IsNull() && cash.At("player_army_ids").elements.empty(),
        "malformed or mismatched DTO emits unknown amounts and empty invalid scope");
  }
  std::cout << "ck3_1210_personal_cash_signed_scope_v2 NoGame fixture PASS\n";
  return 0;
}
