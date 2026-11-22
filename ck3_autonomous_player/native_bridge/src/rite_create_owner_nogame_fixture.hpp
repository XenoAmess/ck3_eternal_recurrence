#pragma once
// Only self-owned NoGame DATA dependencies are supplied. These translation units
// remain the actual owner/wire implementations, never copied test substitutes.
#ifndef XAR_RITE_CREATE_OWNER_TEST_WIRE_SOURCE
#define XAR_RITE_CREATE_OWNER_TEST_WIRE_SOURCE "ck3_121003_rite_create26785313_wire_v1.cpp"
#endif
#ifndef XAR_RITE_CREATE_OWNER_TEST_OWNER_SOURCE
#define XAR_RITE_CREATE_OWNER_TEST_OWNER_SOURCE "ck3_121003_rite_create26785313_owner_v1.cpp"
#endif
#include XAR_RITE_CREATE_OWNER_TEST_WIRE_SOURCE
#include XAR_RITE_CREATE_OWNER_TEST_OWNER_SOURCE
#include <array>
#include <iostream>
#include <stdexcept>

namespace rite_owner_fixture {
using namespace xar::ck3_121003::build26785313;
using Action = RiteCreateAction267V1;
using Phase = RiteCreatePhase267V1;
using Status = RiteCreateStatus267V1;
using Context = RiteCreateContext267V1;
using Session = RiteCreateSession267V1;
using Core = xar::ck3_1210::CoreSnapshotPrefix;
using Stamp = xar::ck3_11906::MainThreadExecutionStampV1;
using Mailbox = xar::ck3_11906::MainThreadQueryMailboxV1;

inline void Require(bool value, const char* why) {
  if (!value) throw std::runtime_error(why);
}
inline bool Has(const std::string& text, std::string_view part) {
  return text.find(part) != std::string::npos;
}
inline Core CoreFor(std::int32_t actor = 36423) {
  Core core{};
  core.clock.date_raw = 53144328; core.clock.speed = 1; core.clock.paused = true;
  core.local_player_id = 0;
  core.map_ready = core.has_played_character = core.played_character_alive = true;
  core.played_character_id = actor;
  return core;
}
inline RiteCreateSource267V1 Draft(std::int32_t actor, std::uint32_t rite, bool can) {
  RiteCreateSource267V1 source{};
  source.phase = Phase::draft; source.source_rite_id = rite; source.actor_id = actor;
  source.draft.emplace();
  auto& d = *source.draft;
  d.is_creating = true; d.native_can_create = can;
  d.piety_cost_raw = 123456; d.piety_missing_raw = -7;
  d.known_dynastic = d.selected_dynastic = true;
  d.create_button_found = d.create_button_visible = d.create_button_enabled = true;
  d.create_admissible = can;
  return source;
}
inline RiteCreateSource267V1 Confirmation(std::int32_t actor, std::uint32_t rite, bool can) {
  RiteCreateSource267V1 source{};
  source.phase = Phase::confirmation; source.source_rite_id = rite; source.actor_id = actor;
  source.confirmation.emplace();
  auto& c = *source.confirmation;
  c.modal_found = c.original_create_bound = true;
  c.native_can_accept = can;
  c.accept_button_visible = c.accept_button_enabled = true;
  c.accept_admissible = can;
  return source;
}
struct State {
  std::array<std::uint64_t, 12> memory{}; // Every pointer is to this executable-owned object.
  Core actual = CoreFor();
  std::uint32_t rite = 47;
  unsigned bindings = 0, frames = 0, observations = 0, window_reads = 0, window_binds = 0;
  unsigned calls = 0, entered_calls = 0;
  bool draft_can = true, accept_can = true, modal_pending = false;
  bool missing_raw = false, raw_cleanup_known = true, bind_ok = true;
  bool change_raw = false, drift_after_core = false, drift_after_world = false;
  RiteCreateCallStatus267V1 call_status = RiteCreateCallStatus267V1::returned;
  bool call_entered = true, call_cleanup_known = true;
  std::optional<RiteCreateAssociation267V1> observed_association;
  std::uint64_t observed_request_deadline = 0;
  std::uintptr_t Address(std::size_t index) { return reinterpret_cast<std::uintptr_t>(&memory[index]); }
  void Reset() {
    actual = CoreFor(); rite = 47;
    bindings = frames = observations = window_reads = window_binds = calls = entered_calls = 0;
    draft_can = accept_can = bind_ok = true;
    modal_pending = missing_raw = change_raw = drift_after_core = drift_after_world = false;
    raw_cleanup_known = call_cleanup_known = call_entered = true;
    call_status = RiteCreateCallStatus267V1::returned;
    observed_association.reset(); observed_request_deadline = 0;
  }
  void NextObservation() { frames = 0; }
};
inline State state;
inline std::uint64_t request_ids = 0;
inline std::unique_ptr<Mailbox> NewMailbox() {
  auto mailbox = std::make_unique<Mailbox>();
  mailbox->offline_fixture = false;
  mailbox->permitted_executor_octovigintary = &ExecuteRiteCreateOnOwner267V1;
  return mailbox;
}
inline Stamp NewStamp() {
  Stamp stamp{};
  stamp.thread_id = GetCurrentThreadId(); stamp.pump_epoch = 11; stamp.paused = true;
  return stamp;
}
inline Context Request(Session& session, Mailbox* mailbox, Action action,
                       std::uint64_t deadline = 0) {
  Context q{};
  q.session = &session; q.mailbox = mailbox; q.connection_generation = 21;
  q.ticket.sequence = ++request_ids;
  q.request.action = action; q.request.expected = state.actual;
  q.request.expected_source_rite_id = state.rite;
  q.request.deadline_unix_ms = deadline ? deadline : Wall() + 60000;
  const auto id = "rite-owner-nogame-" + std::to_string(request_ids);
  std::copy(id.begin(), id.end(), q.request.request_id.begin());
  q.request.request_id_size = static_cast<std::uint8_t>(id.size());
  if (action != Action::query) q.request.provider_generation = q.request.query_sequence = 1;
  ArmRiteCreateDeadline267V1(q);
  return q;
}
inline Context FromQuery(Session& session, Mailbox* mailbox, Action action, const Context& query) {
  auto q = Request(session, mailbox, action, query.request.deadline_unix_ms);
  q.request.expected = query.request.expected;
  q.request.expected_source_rite_id = query.request.expected_source_rite_id;
  q.request.provider_generation = query.result.provider_generation;
  q.request.query_sequence = query.result.query_sequence;
  return q;
}
inline void Run(Context& q, const Stamp& stamp = NewStamp()) {
  state.NextObservation();
  Require(ExecuteRiteCreateOnOwner267V1(&q, stamp), "actual Rite Create owner callback refused context");
}
inline void NoSource(const Context& q) {
  Require(!q.result.source_available && !q.result.source, "rejection retained a usable Source");
}
inline std::string Wire(const Context& q) {
  auto wire = SerializeRiteCreateResult267V1(q.request.id(), q.result);
  for (const auto part : {"\"rite_created\":false", "\"initial_binding_confirmed\":false",
        "\"new_date_observed\":false", "\"physical_save_confirmed\":false", "\"native_handled\":false"})
    Require(Has(wire, part), "actual wire fabricated business/handled/date/Save credit");
  return wire;
}
inline Context QueryDraft(Session& session, Mailbox* mailbox) {
  auto q = Request(session, mailbox, Action::query); Run(q);
  Require(q.result.status == Status::available && q.result.source && q.result.query_sequence > 0 &&
      q.result.provider_generation > 0, "actual complete draft query failed");
  return q;
}
inline Context Create(Session& session, Mailbox* mailbox, const Context& query) {
  auto q = FromQuery(session, mailbox, Action::create, query); Run(q);
  Require(q.result.status == Status::create_dispatched && q.result.source == query.result.source &&
      q.result.claim_sequence > 0 && q.result.effect_attempted && q.result.native_returned &&
      !q.result.native_handled && q.result.cleanup_known,
      "actual owner did not retain immutable draft beforeSource on one void Create");
  return q;
}
inline Context QueryConfirmation(Session& session, Mailbox* mailbox, const Context& originalDraft) {
  auto q = FromQuery(session, mailbox, Action::query_confirmation, originalDraft); Run(q);
  return q;
}
}

namespace xar::ck3_121003::build26785313 {
ReadonlyBindings BindReadonlyImage(std::uintptr_t, std::string_view) noexcept {
  ++rite_owner_fixture::state.bindings; return {};
}
bool ReadRiteCreateFrameOnOwner267V1(const ReadonlyBindings&,
    ck3_11906::MainThreadQueryMailboxV1*, const ck3_11906::MainThreadQueryTicketV1&,
    const ck3_11906::MainThreadExecutionStampV1&, void*, const RiteCreateRequest267V1&,
    std::uint64_t, RiteCreateFrame267V1& out, std::string&) noexcept {
  auto& f = rite_owner_fixture::state; ++f.frames;
  out = {}; out.facts_verified = true; out.core = f.actual;
  if (f.frames > 1 && f.drift_after_core) out.core.clock.date_raw += 24;
  out.game = f.Address(f.frames > 1 && f.drift_after_world ? 11 : 0);
  out.jomini = f.Address(1); out.storage = f.Address(2); out.actor = f.Address(3);
  // No native RiteDraftV2 layout/model is simulated; the Raw dependency below is
  // explicitly DATA and does not dereference these NoGame bindings.
  return true;
}
bool ReadRiteCreateRaw267V1(const ReadonlyBindings&, const RiteCreateFrame267V1& frame,
    const RiteCreateRequest267V1& request, const std::optional<RiteCreateAssociation267V1>& association,
    std::uint64_t, RiteCreateRaw267V1& out, std::string& why) noexcept {
  auto& f = rite_owner_fixture::state; ++f.observations;
  out = {}; out.entered = true; out.cleanup_known = f.raw_cleanup_known;
  f.observed_association = association;
  f.observed_request_deadline = request.deadline_unix_ms;
  if (f.missing_raw) { why = "nogame_actual_complete_raw_unavailable"; return false; }
  const bool confirmation = request.action == RiteCreateAction267V1::query_confirmation ||
                            request.action == RiteCreateAction267V1::accept_confirmation;
  if (confirmation) {
    if (!association || association->controller != f.Address(4) || association->context != f.Address(5) ||
        association->window_root != f.Address(6) || association->source_rite_id != f.rite ||
        association->actor_id != frame.core.played_character_id ||
        association->original_deadline != request.deadline_unix_ms) {
      why = "nogame_actual_create_association_missing"; return false;
    }
    out.source = rite_owner_fixture::Confirmation(frame.core.played_character_id, f.rite, f.accept_can);
    out.pending = f.modal_pending;
  } else out.source = rite_owner_fixture::Draft(frame.core.played_character_id, f.rite, f.draft_can);
  if (f.change_raw && out.source.draft) ++out.source.draft->piety_cost_raw;
  out.controller = f.Address(4); out.context = f.Address(5);
  out.root = f.Address(confirmation ? 7 : 6);
  out.create_button = f.Address(8); out.modal = confirmation ? f.Address(9) : 0;
  out.manager = f.Address(10);
  out.dialog_pointers = {f.Address(6), f.Address(7)};
  return true;
}
bool ReadRiteCreateConfirmationWindowOnOwner267V1(const ReadonlyBindings&,
    ck3_11906::MainThreadQueryMailboxV1*, const ck3_11906::MainThreadQueryTicketV1&,
    const ck3_11906::MainThreadExecutionStampV1&, void*, const RiteCreateRequest267V1&,
    std::uint64_t, GuiWindowV1& out, std::string&) noexcept {
  ++rite_owner_fixture::state.window_reads; out = {}; return true;
}
bool BindRiteCreateConfirmationWindow267V1(const ReadonlyBindings&, const GuiWindowV1&,
    RiteCreateRaw267V1&, std::string& why) noexcept {
  auto& f = rite_owner_fixture::state; ++f.window_binds;
  if (!f.bind_ok) why = "nogame_actual_named_confirmation_window_unavailable";
  return f.bind_ok;
}
RiteCreateCall267V1 CallRiteCreateRaw267V1(const ReadonlyBindings&, const RiteCreateFrame267V1&,
    const RiteCreateRequest267V1&, const std::optional<RiteCreateAssociation267V1>&,
    std::uint64_t, const RiteCreateRaw267V1&) noexcept {
  auto& f = rite_owner_fixture::state; ++f.calls;
  if (f.call_entered) ++f.entered_calls;
  return {f.call_status, f.call_entered, f.call_cleanup_known};
}
}
