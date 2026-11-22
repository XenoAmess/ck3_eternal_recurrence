#pragma once
// Explicit self-owned NoGame dependencies only. No GameAdapter, injection, live ABI,
// ScriptedGui execution, initialization, migration, date change, or SAVE is supplied.
#ifndef XAR_DES_INIT_GUARD_OWNER_TEST_WIRE_SOURCE
#define XAR_DES_INIT_GUARD_OWNER_TEST_WIRE_SOURCE "ck3_121003_des_init_guard26785313_wire_v1.cpp"
#endif
#ifndef XAR_DES_INIT_GUARD_OWNER_TEST_OWNER_SOURCE
#define XAR_DES_INIT_GUARD_OWNER_TEST_OWNER_SOURCE "ck3_121003_des_init_guard26785313_owner_v1.cpp"
#endif
#include XAR_DES_INIT_GUARD_OWNER_TEST_WIRE_SOURCE
#include XAR_DES_INIT_GUARD_OWNER_TEST_OWNER_SOURCE
#include <array>
#include <iostream>
#include <stdexcept>

namespace des_owner_fixture {
using namespace xar::ck3_121003::build26785313;
using Core = xar::ck3_1210::CoreSnapshotPrefix;
using Stamp = xar::ck3_11906::MainThreadExecutionStampV1;
using Mailbox = xar::ck3_11906::MainThreadQueryMailboxV1;
using Status = DesInitGuardStatus267V1;

inline Core CoreFor(std::int32_t actor = 36423) {
  Core core{};
  core.clock.date_raw = 53144328;
  core.clock.speed = 1;
  core.clock.paused = true;
  core.local_player_id = 0;
  core.map_ready = core.has_played_character = core.played_character_alive = true;
  core.played_character_id = actor;
  return core;
}
inline void Require(bool value, const char* why) {
  if (!value) throw std::runtime_error(why);
}
inline void Has(const std::string& text, std::string_view part, const char* why) {
  Require(text.find(part) != std::string::npos, why);
}
inline void MutateCore(Core& core, unsigned field) {
  switch (field) {
    case 0: core.clock.date_raw += 24; break;
    case 1: core.clock.speed = 2; break;
    case 2: core.clock.paused = false; break;
    case 3: core.local_player_id = 1; break;
    case 4: core.map_ready = false; break;
    case 5: core.has_played_character = false; break;
    case 6: core.played_character_id = 37846; break;
    case 7: core.played_character_alive = false; break;
    default: throw std::runtime_error("invalid self-owned Core mutation");
  }
}
struct State {
  // Real addresses belong to this executable's fixture, never to a CK3 process.
  std::array<std::uint64_t, 8> world{};
  Core actual = CoreFor();
  unsigned bindings = 0, frames = 0, observations = 0;
  unsigned post_core_field = 8, post_world_pointer = 7;
  bool shown = false, raw_missing = false, cleanup_known = true;
  bool frame_missing = false, facts_verified = true;
  std::uint64_t seen_wall = 0, seen_monotonic = 0;
  void* seen_context = nullptr;
  void Reset() {
    actual = CoreFor(); bindings = frames = observations = 0;
    post_core_field = 8; post_world_pointer = 7;
    shown = false; raw_missing = false; cleanup_known = true;
    frame_missing = false; facts_verified = true;
    seen_wall = seen_monotonic = 0; seen_context = nullptr;
  }
};
inline State state;
inline std::uint64_t ids = 0;

inline std::unique_ptr<Mailbox> NewMailbox() {
  auto mailbox = std::make_unique<Mailbox>();
  mailbox->offline_fixture = false;
  mailbox->permitted_executor_septemvigintary = &ExecuteDesInitGuardOnOwner267V1;
  return mailbox;
}
inline Stamp NewStamp() {
  Stamp stamp{};
  stamp.thread_id = GetCurrentThreadId();
  stamp.pump_epoch = 11;
  stamp.paused = true;
  return stamp;
}
inline DesInitGuardContext267V1 Query(DesInitGuardSession267V1& session,
                                     Mailbox* mailbox, std::int32_t actor = 36423) {
  DesInitGuardContext267V1 query{};
  query.session = &session;
  query.mailbox = mailbox;
  query.connection_generation = 21;
  query.ticket.sequence = ++ids;
  query.request.expected = CoreFor(actor);
  query.request.deadline_unix_ms = Wall() + 60000;
  const auto id = "des-owner-nogame-" + std::to_string(ids);
  std::copy(id.begin(), id.end(), query.request.request_id.begin());
  query.request.request_id_size = static_cast<std::uint8_t>(id.size());
  ArmDesInitGuardDeadline267V1(query);
  return query;
}
inline void Run(DesInitGuardContext267V1& query, const Stamp& stamp) {
  Require(ExecuteDesInitGuardOnOwner267V1(&query, stamp), "actual owner callback refused context");
}
inline void NoSource(const DesInitGuardContext267V1& query) {
  Require(!query.result.source_available && !query.result.source &&
          !query.result.provider_generation && !query.result.query_sequence,
          "refusal retained a query source or positive provider/query lease");
}
inline std::string ReadonlyWire(const DesInitGuardContext267V1& query) {
  auto wire = SerializeDesInitGuardResult267V1(query.request.id(), query.result);
  for (const auto part : {"\"claim_sequence\":\"0\"", "\"effect_attempted\":false",
       "\"native_returned\":false", "\"native_handled\":false",
       "\"initialization_executed\":false", "\"migration_executed\":false",
       "\"new_date_observed\":false", "\"physical_save_confirmed\":false"})
    Has(wire, part, "actual serializer granted an effect or initialization/date/SAVE credit");
  return wire;
}
}

namespace xar::ck3_121003::build26785313 {
// The production owner binds its image, but this dependency supplies no addresses.
ReadonlyBindings BindReadonlyImage(std::uintptr_t, std::string_view) noexcept {
  ++des_owner_fixture::state.bindings;
  return {};
}
bool ReadDesInitGuardFrameOnOwner267V1(
    const ReadonlyBindings&, ck3_11906::MainThreadQueryMailboxV1*,
    const ck3_11906::MainThreadQueryTicketV1&,
    const ck3_11906::MainThreadExecutionStampV1&, void* context,
    std::uint64_t wall, std::uint64_t monotonic,
    DesInitGuardFrame267V1& out, std::string& reason) noexcept {
  auto& fixture = des_owner_fixture::state;
  ++fixture.frames;
  fixture.seen_context = context;
  fixture.seen_wall = wall;
  fixture.seen_monotonic = monotonic;
  out = {};
  out.facts_verified = fixture.facts_verified;
  out.core = fixture.actual;
  if (fixture.frames > 1 && fixture.post_core_field < 8)
    des_owner_fixture::MutateCore(out.core, fixture.post_core_field);
  std::array<void**, 7> pointers{&out.game, &out.jomini, &out.storage,
    &out.data, &out.players, &out.player, &out.actor};
  for (std::size_t i = 0; i < pointers.size(); ++i)
    *pointers[i] = &fixture.world[(fixture.frames > 1 && fixture.post_world_pointer == i) ? 7 : i];
  if (fixture.frame_missing) {
    reason = "nogame_frame_dependency_unavailable";
    return false;
  }
  return true;
}
bool ReadDesInitGuardRaw267V1(const ReadonlyBindings&,
    const DesInitGuardFrame267V1& before, std::uint64_t, std::uint64_t,
    DesInitGuardRaw267V1& out, std::string& reason) noexcept {
  auto& fixture = des_owner_fixture::state;
  ++fixture.observations;
  out = {};
  out.entered = true;
  out.cleanup_known = fixture.cleanup_known;
  if (fixture.raw_missing) {
    reason = "nogame_actual_definition_unavailable";
    return false;
  }
  out.source.character_id = before.core.played_character_id;
  out.source.character_alive = true;
  out.source.native_is_player = true;
  out.source.native_definition_found = true;
  out.source.native_shown = fixture.shown;
  out.source.scope_bound = true;
  out.source.sampled_twice = true;
  out.definition = reinterpret_cast<std::uintptr_t>(&fixture.world[0]);
  return true;
}
}
