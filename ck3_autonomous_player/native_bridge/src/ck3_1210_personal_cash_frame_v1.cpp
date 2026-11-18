#include "xar_bridge/ck3_1210_personal_cash_frame_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"

#include <windows.h>
#include <array>
#include <cstring>

namespace xar::ck3_1210 {
namespace {

bool SameBindings(const CoreBindings &a, const CoreBindings &b) noexcept {
  return a.enabled && b.enabled && a.game_state_slot == b.game_state_slot &&
      a.jomini_state_slot == b.jomini_state_slot &&
      a.character_storage_slot == b.character_storage_slot &&
      a.get_local_player == b.get_local_player;
}

bool ProductionTargets(const PersonalGoldMailboxContextV1 &parent,
    const PersonalCashMailboxContextV1 &cash,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  const auto &m=*parent.mailbox;
  if(m.offline_fixture)return true; // Explicit RAM-only fixture, never a live module proof.
  const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  if(!base || m.module_base!=base || m.tls_initialized_flag!=base+0x695910C ||
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=base+0x44FEA30 ||
      !SameBindings(parent.bindings.core,BindCoreImage(base,kExecutableSha256)) ||
      reinterpret_cast<std::uintptr_t>(cash.bindings.monthly.context)!=base+kMonthlyFlowContextRvaV1 ||
      reinterpret_cast<std::uintptr_t>(cash.bindings.monthly.gross)!=base+kMonthlyFlowGrossRvaV1 ||
      reinterpret_cast<std::uintptr_t>(cash.bindings.monthly.expenses)!=base+kMonthlyFlowExpensesRvaV1)
    return false;
  if(*reinterpret_cast<const std::uint8_t *>(m.tls_initialized_flag)!=1 ||
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter())!=stamp.tls_context ||
      *reinterpret_cast<const std::uint8_t *>(stamp.tls_context+0x20)!=1)return false;
  constexpr std::array<unsigned char,32> context{0x4c,0x8b,0x05,0x49,0x3f,0xb0,0x03,0x4c,0x3b,0xc1,0x0f,0x84,0x84,0x00,0x00,0x00,0x4c,0x8b,0x15,0x31,0x3f,0xb0,0x03,0x66,0x0f,0x1f,0x84,0x00,0x00,0x00,0x00,0x00};
  constexpr std::array<unsigned char,32> gross{0x48,0x89,0x5c,0x24,0x20,0x4c,0x89,0x44,0x24,0x18,0x48,0x89,0x4c,0x24,0x08,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57,0x48,0x8d,0xac,0x24,0xc0,0xfe};
  constexpr std::array<unsigned char,32> expenses{0x48,0x89,0x5c,0x24,0x20,0x4c,0x89,0x44,0x24,0x18,0x48,0x89,0x4c,0x24,0x08,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57,0x48,0x8d,0xac,0x24,0x30,0xfe};
  return std::memcmp(reinterpret_cast<const void *>(base+0x2DA46E0),context.data(),context.size())==0 &&
      std::memcmp(reinterpret_cast<const void *>(base+0x30F0EA0),gross.data(),gross.size())==0 &&
      std::memcmp(reinterpret_cast<const void *>(base+0x30F1870),expenses.data(),expenses.size())==0;
}

bool Capabilities(const game::GameAdapter *adapter, PersonalCashScopeVersion version) noexcept {
  const bool v1 = version == PersonalCashScopeVersion::legacy_nonnegative_v1;
  const bool v2 = version == PersonalCashScopeVersion::florin_unit_full_id_v2;
  return (v1 || v2) && adapter != nullptr && adapter->enabled() &&
      game::IsCk3_1210Descriptor(adapter->descriptor()) &&
      adapter->supports(v2 ? kPersonalCashCapabilityV2 : kPersonalCashCapabilityV1) &&
      adapter->supports_snapshot() &&
      adapter->supports("game.query.fresh-full-state.v1");
}

bool Owner(const PersonalGoldMailboxContextV1 &parent,
    const PersonalCashMailboxContextV1 &cash,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if (parent.kind != ActorObservationKindV1::personal_cash || parent.cash != &cash ||
      !Capabilities(parent.game, cash.scope_version) ||
      !Capabilities(cash.native_full_adapter, cash.scope_version) ||
      parent.mailbox == nullptr || parent.ticket.sequence == 0 ||
      !parent.bindings.exact_build_admitted || !cash.bindings.exact_build_admitted ||
      !cash.bindings.gold.exact_build_admitted || !cash.bindings.monthly.exact_build_admitted ||
      !SameBindings(parent.bindings.core, cash.bindings.gold.core) ||
      !SameBindings(cash.bindings.gold.core, cash.bindings.monthly.core) ||
      cash.expected_native_revision == 0 || cash.current_published_revision == nullptr)
    return false;
  const auto &m = *parent.mailbox;
  const auto &core = parent.bindings.core;
  if (s.thread_id == 0 || s.thread_id != GetCurrentThreadId() || s.pump_epoch == 0 ||
      s.tls_initialized != 1 || s.tls_main_thread_marker != 1 || s.tls_context == 0 ||
      !s.paused || s.game_state == 0 || s.jomini_state == 0 ||
      !m.iat_hook_installed.load() || m.owner_thread_id.load() != s.thread_id ||
      m.failure_flags.load() != 0 || m.stop_requested.load() || m.proof_reset_requested.load() ||
      m.active_hook_calls.load() == 0 || m.pump_epochs.load() != s.pump_epoch ||
      m.paused_owner_verified_pump_epochs.load() <
          ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      m.state.load() != ck3_11906::MainThreadQueryMailboxStateV1::executing ||
      m.published_sequence.load() != parent.ticket.sequence ||
      m.executor_started_sequence.load() != parent.ticket.sequence ||
      m.executor_started_pump_epoch.load() != s.pump_epoch ||
      m.executor_context != &parent || m.executor.load() != &ExecutePersonalGoldMailboxV1 ||
      core.game_state_slot == nullptr || core.jomini_state_slot == nullptr ||
      reinterpret_cast<std::uintptr_t>(*core.game_state_slot) != s.game_state ||
      reinterpret_cast<std::uintptr_t>(*core.jomini_state_slot) != s.jomini_state)
    return false;
  // execution_stamp is deliberately not checked: the MQ stores that member
  // after the callback. The started sequence/pump above exist before entry.
  return *cash.current_published_revision == cash.expected_native_revision &&
      ProductionTargets(parent,cash,s);
}

void ClearAmounts(PersonalCashMailboxContextV1 &cash, std::string_view reason) noexcept {
  auto &out = cash.observation;
  out.completed = out.same_frame_ready = false;
  out.personal_gold_raw.reset();
  out.monthly_gross_income_raw.reset();
  out.monthly_total_expenses_raw.reset();
  out.monthly_net_income_raw.reset();
  out.unavailable_reason = out.monthly_unavailable_reason = out.net_unavailable_reason = reason;
}

struct FullReadContext {
  PersonalGoldMailboxContextV1 *parent = nullptr;
  PersonalCashMailboxContextV1 *cash = nullptr;
  ck3_11906::MainThreadExecutionStampV1 stamp{};
  std::uint64_t expected_revision = 0;
  PersonalCashScopeVersion scope_version = PersonalCashScopeVersion::legacy_nonnegative_v1;
  const game::GameAdapter *native_full_adapter = nullptr;
  const std::uint64_t *current_published_revision = nullptr;
};

bool SameFullSources(const FullReadContext &call) noexcept {
  const auto &cash = *call.cash;
  return call.native_full_adapter != nullptr && call.current_published_revision != nullptr &&
      cash.native_full_adapter == call.native_full_adapter &&
      cash.current_published_revision == call.current_published_revision;
}

bool AdmitMonthlyOnCashOwner(void *opaque) noexcept {
  const auto &call = *static_cast<const FullReadContext *>(opaque);
  const auto &cash = *call.cash;
  return SameFullSources(call) && cash.scope_version == call.scope_version &&
      cash.expected_native_revision == call.expected_revision &&
      *call.current_published_revision == call.expected_revision &&
      Owner(*call.parent, cash, call.stamp);
}

bool ReadCurrentFull(void *opaque, game::Snapshot &snapshot,
    std::uint64_t &revision) {
  revision = 0;
  auto &call = *static_cast<FullReadContext *>(opaque);
  auto &cash = *call.cash;
  if (!SameFullSources(call) || cash.expected_native_revision != call.expected_revision ||
      cash.scope_version != call.scope_version || !Owner(*call.parent, cash, call.stamp) ||
      *call.current_published_revision != call.expected_revision) return false;
  // This is the actual native adapter virtual read, never expected_full or
  // a WorkerAdapter read. Full fields are compared by the existing provider.
  if (!call.native_full_adapter->read_snapshot(snapshot)) return false;
  if (!SameFullSources(call) || cash.expected_native_revision != call.expected_revision ||
      *call.current_published_revision != call.expected_revision ||
      cash.scope_version != call.scope_version || !Owner(*call.parent, cash, call.stamp)) return false;
  revision = call.expected_revision;
  return true;
}

CoreSnapshotPrefix Prefix(const game::Snapshot &s) noexcept {
  CoreSnapshotPrefix p{};
  p.clock = {s.date_raw, s.speed, s.paused}; p.local_player_id = s.player_id;
  p.map_ready = s.map_ready; p.has_played_character = s.has_played_character;
  p.played_character_id = s.played_character_id;
  p.played_character_alive = s.played_character_alive;
  return p;
}

bool Read(PersonalGoldMailboxContextV1 &parent,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  parent.observation = {}; parent.foundation = {};
  parent.application_main_observed = false;
  if (parent.cash == nullptr) return true;
  auto &cash = *parent.cash;
  cash.observation = {}; cash.observation.scope_version = cash.scope_version;
  cash.application_main_observed = false;
  try {
    if (!Owner(parent, cash, stamp)) {
      ClearAmounts(cash, "personal_cash_actor_owner_unqualified"); return true;
    }
    if (cash.expected_full.date_raw != stamp.date_raw || !cash.expected_full.paused ||
        !cash.expected_full.map_ready || !cash.expected_full.has_played_character ||
        !cash.expected_full.played_character_alive || cash.expected_full.played_character_id == -1) {
      ClearAmounts(cash, "personal_cash_full_basis_not_paused_actor"); return true;
    }
    parent.application_main_observed = cash.application_main_observed = true;
    // This local copy is the only place these gates are opened. The bridge's
    // shared bindings remain closed even after success, failure or a fault.
    auto local = cash.bindings;
    local.integration_native_calls_permitted = true;
    local.monthly.integration_native_calls_permitted = true;
    FullReadContext call{&parent, &cash, stamp, cash.expected_native_revision, cash.scope_version,
        cash.native_full_adapter, cash.current_published_revision};
    local.monthly.native_call_admission = &AdmitMonthlyOnCashOwner;
    local.monthly.native_call_admission_context = &call;
    PersonalCashReadContextV1 request{};
    request.paused_application_main_owner_admitted = true;
    request.published_native_revision = call.expected_revision;
    request.expected_core = Prefix(cash.expected_full);
    request.published_full = &cash.expected_full;
    request.read_current_full = &ReadCurrentFull;
    request.read_current_full_context = &call;
    if (call.scope_version == PersonalCashScopeVersion::florin_unit_full_id_v2)
      (void)ReadPersonalCashV2(local, request, cash.observation);
    else
      (void)ReadPersonalCashV1(local, request, cash.observation);
    if (!SameFullSources(call) || !Owner(parent, cash, stamp) ||
        cash.expected_native_revision != call.expected_revision ||
        cash.scope_version != call.scope_version)
      ClearAmounts(cash, "personal_cash_actor_owner_changed");
    return true;
  } catch (...) {
    ClearAmounts(cash, "personal_cash_actor_callback_failed"); return true;
  }
}

void Fault(PersonalGoldMailboxContextV1 &parent) noexcept {
  if (parent.cash != nullptr)
    ClearAmounts(*parent.cash, "personal_cash_actor_memory_read_failed");
}

} // namespace

bool ExecutePersonalCashOnActorOwnerV1(PersonalGoldMailboxContextV1 &parent,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
#if defined(_MSC_VER)
  __try { return Read(parent, stamp); }
  __except (GetExceptionCode() == 0xE06D7363UL
      ? EXCEPTION_CONTINUE_SEARCH : EXCEPTION_EXECUTE_HANDLER) {
    Fault(parent); return true;
  }
#else
  return Read(parent, stamp);
#endif
}

namespace {
std::string SerializePersonalCashFrameResult(const PersonalCashMailboxContextV1 &cash,
    PersonalCashScopeVersion version) {
  const auto serialize = version == PersonalCashScopeVersion::florin_unit_full_id_v2 ?
      &SerializePersonalCashV2 : &SerializePersonalCashV1;
  if (!cash.application_main_observed || cash.scope_version != version) {
    // An observation copied without this frame's main-owner receipt must not
    // revive known amounts. True still relies on the full owner checks above.
    auto unqualified = cash.observation;
    unqualified.completed = unqualified.same_frame_ready = false;
    unqualified.personal_gold_raw.reset();
    unqualified.monthly_gross_income_raw.reset();
    unqualified.monthly_total_expenses_raw.reset();
    unqualified.monthly_net_income_raw.reset();
    unqualified.unavailable_reason = unqualified.monthly_unavailable_reason =
        unqualified.net_unavailable_reason = "personal_cash_actor_owner_unqualified";
    return serialize(unqualified);
  }
  return serialize(cash.observation);
}
} // namespace

std::string SerializePersonalCashFrameResultV1(const PersonalCashMailboxContextV1 &cash) {
  return SerializePersonalCashFrameResult(cash, PersonalCashScopeVersion::legacy_nonnegative_v1);
}
std::string SerializePersonalCashFrameResultV2(const PersonalCashMailboxContextV1 &cash) {
  return SerializePersonalCashFrameResult(cash, PersonalCashScopeVersion::florin_unit_full_id_v2);
}

} // namespace xar::ck3_1210
