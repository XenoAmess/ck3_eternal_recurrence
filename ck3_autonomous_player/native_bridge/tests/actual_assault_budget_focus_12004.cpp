#include "actual_assault_budget_focus_12004.hpp"
#include "xar_bridge/ck3_12004_actual_assault_budget_journal.hpp"
#include "xar_bridge/army_actual_assault_budget_observations_v1_serializer.hpp"
#include <bit>
#include <stdexcept>
#include <string>

namespace xar::ck3_12004::focus {
namespace {
std::uintptr_t g_raw = kActualBudgetFocusRawReturn12004;
std::uint32_t g_original_calls = 0;
void *g_receiver = nullptr;
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
std::uintptr_t __fastcall Original(void *receiver) {
  ++g_original_calls; g_receiver = receiver; return g_raw;
}
} // namespace
void PrepareActualAssaultBudgetFocus12004(std::uintptr_t raw) {
  ArmyAssaultConsumerParent12004 parent{};
  Check(!CopyActiveArmyAssaultConsumerParent12004(parent), "38c prepare must be outside active natural consumer");
  g_raw = raw; g_original_calls = 0; g_receiver = nullptr;
  auto b = BindActualAssaultBudgetJournalImage12004(0x40000000,
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
  Check(b.enabled && InitializeActualAssaultBudgetJournalFixture12004(b, Original),
      "38c new child fixture initialization failed");
}
std::uintptr_t RunActualAssaultBudgetFocus12004(void *receiver) {
  ArmyAssaultConsumerParent12004 parent{};
  Check(CopyActiveArmyAssaultConsumerParent12004(parent) && parent.active,
      "38c natural child requires real37 active TLS parent");
  const auto before = g_original_calls;
  const auto result = InvokeActualAssaultBudgetObserver12004(receiver, kActualAssaultBudgetCallerReturnRva12004);
  Check(g_original_calls == before + 1 && g_receiver == receiver && result == g_raw,
      "38c must preserve exact selected receiver and full raw RAX from original once");
  return result;
}
void RunExcludedActualAssaultBudgetFocus12004(void *receiver) {
  ArmyAssaultConsumerParent12004 parent{};
  const bool active = CopyActiveArmyAssaultConsumerParent12004(parent);
  const auto before_events = active ? ReadActualAssaultBudgetObservations12004(parent.entry_event).events.size() : 0;
  const auto before = g_original_calls;
  const auto caller = active ? kActualAssaultBudgetCallerReturnRva12004 + 1 : kActualAssaultBudgetCallerReturnRva12004;
  const auto result = InvokeActualAssaultBudgetObserver12004(receiver, caller);
  Check(result == g_raw && g_original_calls == before + 1, "38c excluded call must still invoke original once");
  if (active)
    Check(ReadActualAssaultBudgetObservations12004(parent.entry_event).events.size() == before_events,
        "38c wrong caller must not fabricate another natural child record");
}
void VerifyActualAssaultBudgetFocus12004(const ArmyNaturalPhaseEvent12004 &parent_entry, bool bound) {
  const auto rows = ReadActualAssaultBudgetObservations12004(parent_entry);
  Check(!rows.events.empty(), "38c actual parent child observation absent");
  const auto &row = rows.events.back();
  Check(row.original_called && row.original_returned && row.raw_return_bits == g_raw &&
      row.consumed_eax_u32 == static_cast<std::uint32_t>(g_raw) &&
      row.native_expected_loss_i32 == std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(g_raw)),
      "38c opaque raw RAX and consumed signed EAX are separate facts");
  Check(row.parent_still_active && row.same_clock_thread_order && row.receiver_identity_unchanged,
      "38c same parent full generation/clock/thread ordering is incomplete");
  Check(row.parent_group_budget_recorded == bound && !row.full_besieging_dependencies_captured,
      "38c naturally returned scalar must bind independently without inventing full B family");
  Check(row.actual_caller_return_rva == kActualAssaultBudgetCallerReturnRva12004 &&
      row.entry_receiver.siege_full_id && row.entry_receiver.province_full_id &&
      row.entry_receiver.province_identity && *row.entry_receiver.province_identity,
      "38c source receiver/generation/Province facts missing");
  std::string wire;
  game::AppendArmyActualAssaultBudgetObservationsV1(wire, rows,
      [](auto value) { return std::to_string(value); },
      [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  Check(wire.find("\"native_expected_loss_i32\":" + std::to_string(row.native_expected_loss_i32)) != std::string::npos &&
      wire.find("\"full_besieging_dependencies_captured\":false") != std::string::npos,
      "38c new child serializer lost natural scalar or unknown B dependency boundary");
  auto wrong = parent_entry; ++wrong.sequence;
  Check(ReadActualAssaultBudgetObservations12004(wrong).events.empty(),
      "38c a later or unrelated query token cannot backfill history");
}
} // namespace xar::ck3_12004::focus
