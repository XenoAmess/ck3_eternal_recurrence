#include "xar_bridge/ck3_1210_character_roster_frame_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_1210_thread_runtime.hpp"
#include <windows.h>
namespace xar::ck3_1210 {
namespace {
bool SameBindings(const CoreBindings &a, const CoreBindings &b) noexcept {
  return a.enabled && b.enabled && a.game_state_slot == b.game_state_slot &&
    a.jomini_state_slot == b.jomini_state_slot && a.character_storage_slot == b.character_storage_slot &&
    a.get_local_player == b.get_local_player;
}
bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed && a.clock.paused == b.clock.paused &&
    a.local_player_id == b.local_player_id && a.map_ready == b.map_ready &&
    a.has_played_character == b.has_played_character && a.played_character_id == b.played_character_id &&
    a.played_character_alive == b.played_character_alive;
}
bool Revision(const CharacterRosterMailboxContextV1 &q) noexcept {
  return q.current_native_revision && q.current_connection_generation && q.expected_native_revision != 0 &&
    q.expected_connection_generation != 0 && *q.current_native_revision == q.expected_native_revision &&
    *q.current_connection_generation == q.expected_connection_generation;
}
bool Targets(const PersonalGoldMailboxContextV1 &p, const CharacterRosterMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  const auto &m = *p.mailbox;
  if (m.offline_fixture) return true;
  if (q.fixture_access.context || q.fixture_access.copy) return false;
  const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  const auto exact = BindCharacterManagerImageV1(base, kExecutableSha256);
  if (!base || !exact.exact_build_admitted || m.module_base != base ||
    m.game_state_slot != base + kGameStateSlotRva || m.jomini_state_slot != base + kJominiStateSlotRva ||
    s.tls_initialized_flag_address != m.tls_initialized_flag ||
    m.tls_initialized_flag != base + kMainThreadTlsInitializedFlagRva ||
    reinterpret_cast<std::uintptr_t>(m.tls_context_getter) != base + kMainThreadTlsContextGetterRva ||
    !SameBindings(q.bindings.core, exact.core) || q.bindings.manager_vtable != exact.manager_vtable) return false;
  return *reinterpret_cast<const std::uint8_t *>(m.tls_initialized_flag) == 1 &&
    reinterpret_cast<std::uintptr_t>(m.tls_context_getter()) == s.tls_context &&
    *reinterpret_cast<const std::uint8_t *>(s.tls_context + 0x20) == 1;
}
bool Owner(const PersonalGoldMailboxContextV1 &p, const CharacterRosterMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if (p.kind != ActorObservationKindV1::character_roster || p.roster != &q || !p.game || !p.game->enabled() ||
    !game::IsCk3_1210Descriptor(p.game->descriptor()) || !p.game->supports(kCharacterRosterCapabilityV1) ||
    !p.mailbox || p.ticket.sequence == 0 || !p.bindings.exact_build_admitted || !q.bindings.exact_build_admitted ||
    !SameBindings(p.bindings.core, q.bindings.core) || !Revision(q)) return false;
  const auto &m = *p.mailbox; const auto &b = q.bindings.core;
  if (s.thread_id == 0 || s.thread_id != GetCurrentThreadId() || s.pump_epoch == 0 ||
    s.tls_initialized != 1 || s.tls_main_thread_marker != 1 || !s.tls_context || !s.paused ||
    !s.game_state || !s.jomini_state || !m.iat_hook_installed.load() || m.owner_thread_id.load() != s.thread_id ||
    m.failure_flags.load() || m.stop_requested.load() || m.proof_reset_requested.load() ||
    m.active_hook_calls.load() == 0 || m.pump_epochs.load() != s.pump_epoch ||
    m.paused_owner_verified_pump_epochs.load() < ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
    m.state.load() != ck3_11906::MainThreadQueryMailboxStateV1::executing ||
    m.published_sequence.load() != p.ticket.sequence || m.executor_started_sequence.load() != p.ticket.sequence ||
    m.executor_started_pump_epoch.load() != s.pump_epoch || m.executor_context != &p ||
    m.executor.load() != &ExecutePersonalGoldMailboxV1 || !Targets(p, q, s) ||
    !b.game_state_slot || !b.jomini_state_slot ||
    reinterpret_cast<std::uintptr_t>(*b.game_state_slot) != s.game_state ||
    reinterpret_cast<std::uintptr_t>(*b.jomini_state_slot) != s.jomini_state) return false;
  return true;
}
bool Read(PersonalGoldMailboxContextV1 &p, const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  p.application_main_observed = false;
  if (!p.roster) return true;
  auto &q = *p.roster; ClearCharacterRosterV1(q, "character_roster_owner_unqualified");
  if (!Owner(p, q, s)) return true;
  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(q.bindings.core, before) || !SameFrame(before, q.expected) ||
      before.clock.date_raw != s.date_raw || before.clock.paused != s.paused) {
    ClearCharacterRosterV1(q, "character_roster_expected_frame_changed"); return true;
  }
  if (!Owner(p, q, s)) { ClearCharacterRosterV1(q, "character_roster_owner_changed_after_core"); return true; }
  (void)ReadCharacterManagerV1(q.bindings, before, q.observation, q.fixture_access);
  // The complete manager reader closes raw roots/clock after its final scan.
  // Do not call another native Core getter after that captured transcript.
  if (!Owner(p, q, s) || (q.observation.available && !SameFrame(before, q.observation.frame))) {
    ClearCharacterRosterV1(q, "character_roster_owner_or_frame_changed"); return true;
  }
  q.source.offline_fixture = p.mailbox->offline_fixture;
  // A real running callback can produce actual custody facts. An explicit
  // NoGame fixture remains a fixture even when its synthetic guards agree.
  if (!q.source.offline_fixture) {
    q.application_main_observed = p.application_main_observed = true;
    q.source = {true, false, q.expected_native_revision, q.expected_connection_generation,
      p.ticket.sequence, s.pump_epoch, s.thread_id, s.date_raw, before.played_character_id};
  }
  return true;
}
void Fault(PersonalGoldMailboxContextV1 &p) noexcept {
  if (p.roster) ClearCharacterRosterV1(*p.roster, "character_roster_memory_read_failed");
  p.application_main_observed = false;
}
} // namespace
void ClearCharacterRosterV1(CharacterRosterMailboxContextV1 &q, std::string_view reason) noexcept {
  q.observation = {}; q.observation.unavailable_reason = reason;
  q.source = {}; q.application_main_observed = false;
}
bool ExecuteCharacterRosterOnActorOwnerV1(PersonalGoldMailboxContextV1 &p,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
#if defined(_MSC_VER)
  __try { return Read(p, s); }
  __except(GetExceptionCode() == 0xE06D7363UL ? EXCEPTION_CONTINUE_SEARCH : EXCEPTION_EXECUTE_HANDLER) {
    Fault(p); return true;
  }
#else
  return Read(p, s);
#endif
}
} // namespace xar::ck3_1210
