#include "xar_bridge/ck3_12003_war_cash_current_reader.hpp"
#include "xar_bridge/ck3_12002_war_cash_treasury.hpp"

#include <cstring>
#include <limits>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12003::war_cash_current {
namespace {

bool ActorMatches(const void *actor, std::int32_t id) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    std::int32_t actual_id = -1;
    std::uint32_t actual_type = 0;
    void *death_data = nullptr;
    std::memcpy(&actual_type, static_cast<const std::byte *>(actor) + 0x1C,
                sizeof(actual_type));
    std::memcpy(&actual_id, static_cast<const std::byte *>(actor) + 0x18,
                sizeof(actual_id));
    std::memcpy(&death_data,
                static_cast<const std::byte *>(actor) +
                    ck3_12003::kCharacterDeathDataOffset,
                sizeof(death_data));
    return actual_type == 0x43686172U && actual_id == id && death_data == nullptr;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool Gold(const void *actor, std::int64_t &raw) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    void *living = nullptr;
    std::memcpy(&living,
                static_cast<const std::byte *>(actor) +
                    ck3_12002::kWarCashCharacterLivingExtensionOffset,
                sizeof(living));
    // This is stock GetGold's legitimate zero for a missing extension.
    raw = 0;
    if (living != nullptr) {
      std::memcpy(&raw,
                  static_cast<const std::byte *>(living) +
                      ck3_12002::kWarCashCharacterGoldOffset,
                  sizeof(raw));
    }
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool MonthlyFlow(const Bindings &bindings, void *actor,
                 std::int32_t actor_id, ActorResources &output) noexcept {
  output.gross_income_unavailable_reason = "war_cash_monthly_income_unavailable";
  output.total_expenses_unavailable_reason = "war_cash_monthly_total_expenses_unavailable";
  output.income_unavailable_reason = "war_cash_monthly_net_income_unavailable";
  if (bindings.monthly_income == nullptr ||
      bindings.expense_context_character == nullptr ||
      bindings.monthly_total_expenses == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    // DF1C70's gold HUD writer uses this exact .3 native argument chain.
    void *context = bindings.expense_context_character(actor);
    if (context == nullptr || !ActorMatches(actor, actor_id)) return false;
    std::int64_t gross = 0;
    std::int64_t secondary_income = 0;
    if (bindings.monthly_income(&gross, actor, &secondary_income, nullptr) != &gross ||
        !ActorMatches(actor, actor_id)) return false;
    output.monthly_gross_income_raw = gross;
    output.gross_income_unavailable_reason.clear();
    std::int64_t expenses = 0;
    if (bindings.monthly_total_expenses(&expenses, actor, context,
                                      secondary_income, false, nullptr) != &expenses ||
        !ActorMatches(actor, actor_id)) return false;
    output.monthly_total_expenses_raw = expenses;
    output.total_expenses_unavailable_reason.clear();
    constexpr auto minimum = std::numeric_limits<std::int64_t>::min();
    constexpr auto maximum = std::numeric_limits<std::int64_t>::max();
    if ((expenses > 0 && gross < minimum + expenses) ||
        (expenses < 0 && gross > maximum + expenses)) {
      output.income_unavailable_reason = "war_cash_monthly_net_income_overflow";
      return false;
    }
    output.monthly_net_income_raw = gross - expenses;
    output.income_unavailable_reason.clear();
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool Current(CurrentMaintenance function, void *actor,
             std::array<std::int64_t, 10> &raw) noexcept {
  if (function == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return function(raw.data(), actor, nullptr) == raw.data();
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool AllRaised(AllRaisedMaintenance function, void *actor,
               std::array<std::int64_t, 10> &raw) noexcept {
  if (function == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return function(raw.data(), actor) == raw.data();
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool FailActor(ActorResources &output, std::string_view reason) {
  output.current_treasury_raw.reset();
  output.monthly_gross_income_raw.reset();
  output.monthly_total_expenses_raw.reset();
  output.monthly_net_income_raw.reset();
  output.current = {};
  output.all_raised = {};
  output.treasury_unavailable_reason = reason;
  output.gross_income_unavailable_reason = reason;
  output.total_expenses_unavailable_reason = reason;
  output.income_unavailable_reason = reason;
  output.current.unavailable_reason = reason;
  output.all_raised.unavailable_reason = reason;
  output.unavailable_reason = reason;
  return false;
}

} // namespace

Bindings BindImage(std::uintptr_t image_base, std::string_view version,
                   std::string_view sha) noexcept {
  Bindings output{};
  constexpr std::string_view lower_sha =
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6";
  if (image_base == 0 || version != ck3_12003::kGameVersion ||
      (sha != ck3_12003::kExecutableSha256 && sha != lower_sha)) {
    return output;
  }
  output.enabled = true;
  output.monthly_income = reinterpret_cast<MonthlyIncome>(
      image_base + kMonthlyIncomeRva);
  output.expense_context_character = reinterpret_cast<ExpenseContextCharacter>(
      image_base + kExpenseContextCharacterRva);
  output.monthly_total_expenses = reinterpret_cast<MonthlyTotalExpenses>(
      image_base + kMonthlyTotalExpensesRva);
  output.current_maintenance = reinterpret_cast<CurrentMaintenance>(
      image_base + kCurrentMaintenanceRva);
  output.all_raised_maintenance = reinterpret_cast<AllRaisedMaintenance>(
      image_base + kAllRaisedMaintenanceRva);
  return output;
}

bool ReadActor(const Bindings &bindings, void *actor,
               std::int32_t actor_id, ActorResources &output) noexcept {
  try {
    output = {};
    if (!bindings.enabled)
      return FailActor(output, "war_cash_current_binding_unavailable");
    if (actor == nullptr || actor_id <= 0 || !ActorMatches(actor, actor_id))
      return FailActor(output, "war_cash_current_played_character_unavailable");

    std::int64_t treasury = 0;
    if (Gold(actor, treasury)) {
      output.current_treasury_raw = treasury;
      output.treasury_unavailable_reason.clear();
    } else {
      output.treasury_unavailable_reason = "war_cash_current_treasury_unavailable";
    }

    (void)MonthlyFlow(bindings, actor, actor_id, output);
    if (!ActorMatches(actor, actor_id))
      return FailActor(output, "war_cash_current_actor_changed_during_read");

    auto &current = output.current;
    current.available = Current(bindings.current_maintenance, actor,
                                current.resources_raw);
    if (!ActorMatches(actor, actor_id))
      return FailActor(output, "war_cash_current_actor_changed_during_read");
    if (current.available) {
      current.unavailable_reason.clear();
    } else {
      current.resources_raw = {};
      current.unavailable_reason = "native_current_maintenance_unavailable";
    }

    auto &all = output.all_raised;
    all.available = AllRaised(bindings.all_raised_maintenance, actor,
                              all.resources_raw);
    if (all.available) {
      all.unavailable_reason.clear();
    } else {
      all.resources_raw = {};
      all.unavailable_reason = "native_all_raised_maintenance_unavailable";
    }

    if (!ActorMatches(actor, actor_id))
      return FailActor(output, "war_cash_current_actor_changed_during_read");

    if (output.current_treasury_raw.has_value() &&
        output.monthly_net_income_raw.has_value() &&
        current.available && all.available) {
      output.unavailable_reason.clear();
    } else {
      output.unavailable_reason = "war_cash_current_resources_partial";
    }
    return true;
  } catch (...) {
    // Field availability stays false/null after an actual failed read/copy.
    output.current_treasury_raw.reset();
    output.monthly_gross_income_raw.reset();
    output.monthly_total_expenses_raw.reset();
    output.monthly_net_income_raw.reset();
    output.current.available = false;
    output.all_raised.available = false;
    return false;
  }
}

} // namespace xar::ck3_12003::war_cash_current
