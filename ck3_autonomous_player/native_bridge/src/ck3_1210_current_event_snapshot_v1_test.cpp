#include "xar_bridge/ck3_1210_current_event_snapshot_v1.hpp"
#include <array>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <vector>
namespace {
using namespace xar::ck3_1210;
constexpr auto kActorId = std::bit_cast<std::int32_t>(std::uint32_t{0x81000001});
void Require(bool value, const char *message) {
  if (!value) { std::cerr << "FAIL " << message << std::endl; std::exit(1); }
}
template <class B, class T> void Store(B &buffer, std::size_t offset, T value) {
  Require(offset <= buffer.size() && sizeof(value) <= buffer.size() - offset, "fixture bounds");
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
enum class Mutation {
  none, null_second, event_second, instance_second, definition_second, count_second,
  capacity_second, authored_second, character_second, cache_second, queue_second,
  data_second, selector_date, selector_pause, selector_actor_type, core_date_second,
  core_local_second, core_generation_second, core_current_second, core_actor_second,
  core_final_date, core_final_instance, core_final_queue
};
struct Fixture;
Fixture *active = nullptr;
void *LocalPlayer(void *);
void *Select(void *);
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x21> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(kCurrentEventManagerOffsetV1 + 0x1F28);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x1D8> actor{}, replacement{};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x20> slots{};
  std::array<std::byte, 0x1C8> event{}, other_event{};
  std::array<std::byte, 0x148> definition{}, other_definition{};
  std::array<std::byte, 3> authored_payload{};
  std::array<void *, kCurrentEventMaxAuthoredV1> authored{};
  std::array<void *, 2> queue{event.data(),other_event.data()};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data(), *storage_pointer = storage.data();
  void *current = event.data();
  std::int32_t actor_id, selector_character;
  CurrentEventSnapshotBindingsV1 bindings{};
  Mutation mutation = Mutation::none;
  unsigned core_reads = 0, selectors = 0, action_calls = 0;
  explicit Fixture(std::int32_t id = kActorId) : actor_id(id), selector_character(id) {
    active = this;
    Store(state, 8, std::int32_t{123456}); Store(state, 0x70, std::int32_t{4}); Store(state, 0xA0, data.data());
    Store(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Store(players, 0x1F0, std::int32_t{7}); Store(player, 0x70, std::int32_t{7});
    Store(data, kPlayerCharacterManagerOffset + 0x58, entries.data());
    Store(data, kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Store(entry, 0xD8, std::int32_t{7}); Store(entry, 0xB0, actor_id);
    Store(actor, 0x18, actor_id); Store(actor, 0x1C, std::uint32_t{0x43686172}); replacement = actor;
    Store(storage, 0x20, slots.data()); Store(storage, 0x2C, std::int32_t{2}); PlaceActor(actor.data());
    bindings = BindCurrentEventSnapshotImageV1(0x140000000, kExecutableSha256);
    Require(bindings.exact_build_admitted, "exact address-only constructor");
    bindings.core = {true,&state_pointer,&jomini_pointer,&storage_pointer,&LocalPlayer};
    bindings.get_current_event = &Select; bindings.selector_character_id_slot = &selector_character;
    Store(data, kCurrentEventManagerOffsetV1 + 0x1F18, queue.data());
    Store(data, kCurrentEventManagerOffsetV1 + 0x1F24, std::int32_t{1});
    authored.fill(authored_payload.data());
    Store(definition, 0, bindings.definition_vtable); Store(definition, 0x138, authored.data());
    Store(definition, 0x140, std::int32_t{2}); Store(definition, 0x144, std::int32_t{2});
    Store(event, 0x1B8, definition.data()); Store(event, 0x1C0, actor_id);
    Store(event, 0x1C4, std::int32_t{42}); other_event = event; other_definition = definition;
  }
  void PlaceActor(void *value) {
    Store(slots, (static_cast<std::uint32_t>(actor_id) & 0xFFFFFFU) * 0x10 + 8, value);
  }
  void Empty() {
    current = nullptr; Store(data, kCurrentEventManagerOffsetV1 + 0x1F18, static_cast<void *>(nullptr));
    Store(data, kCurrentEventManagerOffsetV1 + 0x1F24, std::int32_t{0});
  }
  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix out{}; Require(ReadCoreSnapshot(bindings.core, out), "fixture Core");
    Require(out.has_played_character && out.played_character_id == actor_id, "fixture complete actor generation");
    core_reads = selectors = 0; return out;
  }
};
void *LocalPlayer(void *) {
  auto &f = *active; ++f.core_reads;
  if (f.core_reads == 2) switch (f.mutation) {
    case Mutation::core_date_second: Store(f.state, 8, std::int32_t{123457}); break;
    case Mutation::core_local_second: Store(f.players, 0x1F0, std::int32_t{8}); break;
    case Mutation::core_generation_second: Store(f.actor, 0x18, std::int32_t{1}); break;
    case Mutation::core_current_second: f.current = nullptr; break;
    case Mutation::core_actor_second: f.PlaceActor(f.replacement.data()); break;
    default: break;
  }
  if (f.core_reads == 3) {
    if (f.mutation == Mutation::core_final_date) Store(f.state, 8, std::int32_t{123457});
    if (f.mutation == Mutation::core_final_instance) Store(f.event, 0x1C4, std::int32_t{43});
    if (f.mutation == Mutation::core_final_queue) f.queue[0] = f.other_event.data();
  }
  return f.player.data();
}
void *Select(void *manager) {
  auto &f = *active; ++f.selectors;
  Require(manager == f.data.data() + kCurrentEventManagerOffsetV1, "actual manager/data-root argument");
  if (f.selectors == 2) switch (f.mutation) {
    case Mutation::null_second: f.current = nullptr; break;
    case Mutation::event_second: f.current = f.other_event.data(); break;
    case Mutation::instance_second: Store(f.event, 0x1C4, std::int32_t{43}); break;
    case Mutation::definition_second: Store(f.event, 0x1B8, f.other_definition.data()); break;
    case Mutation::count_second: Store(f.definition, 0x144, std::int32_t{1}); break;
    case Mutation::capacity_second: Store(f.definition, 0x140, std::int32_t{3}); break;
    case Mutation::authored_second: f.authored[0] = f.authored_payload.data() + 2; break;
    case Mutation::character_second: Store(f.event, 0x1C0, std::int32_t{7}); break;
    case Mutation::cache_second: f.selector_character = -1; break;
    case Mutation::queue_second: f.queue[0] = f.other_event.data(); break;
    case Mutation::data_second: Store(f.state, 0xA0, static_cast<void *>(nullptr)); break;
    case Mutation::selector_date: Store(f.state, 8, std::int32_t{123457}); break;
    case Mutation::selector_pause: f.jomini[0x20] = std::byte{}; break;
    case Mutation::selector_actor_type: Store(f.actor, 0x1C, std::uint32_t{0}); break;
    default: break;
  }
  Require(f.action_calls == 0, "selector is not an action"); return f.current;
}
void Unavailable(Fixture &f, const CoreSnapshotPrefix &expected, std::string_view reason = {}) {
  CurrentEventSnapshotObservationV1 out{};
  out.available = out.found = out.same_frame_ready = true;
  out.active_event_instance_id = 777; out.active_event_option_count = 888;
  Require(!ReadCurrentEventSnapshotV1(f.bindings, expected, out), "unavailable read returns false");
  Require(!out.available && !out.found && !out.same_frame_ready && out.active_event_instance_id == -1 &&
      out.active_event_option_count == 0 && !out.unavailable_reason.empty(), "failure cannot retain selection or fake observed empty");
  if (!reason.empty()) Require(out.unavailable_reason == reason, "exact unavailable reason");
  Require(out.partial && !out.full_snapshot_available && !out.option_eligibility_observed &&
      f.action_calls == 0, "unavailable grants no full Snapshot, eligibility or actions");
}
CurrentEventSnapshotObservationV1 Observed(Fixture &f, bool found) {
  const auto expected = f.Expected(); CurrentEventSnapshotObservationV1 out{};
  Require(ReadCurrentEventSnapshotV1(f.bindings, expected, out), "complete basic event observation");
  Require(out.available && out.found == found && out.same_frame_ready && out.partial &&
      !out.full_snapshot_available && out.option_count_is_authored_total && !out.option_eligibility_observed &&
      out.unavailable_reason.empty() && f.selectors == 2 && f.core_reads == 3 && f.action_calls == 0,
      "two real selectors preserve basic-only qualification");
  Require(out.frame.clock.date_raw == expected.clock.date_raw && out.frame.clock.speed == expected.clock.speed &&
      out.frame.clock.paused && out.frame.map_ready && out.frame.has_played_character &&
      out.frame.played_character_alive && out.frame.local_player_id == 7 &&
      out.frame.played_character_id == f.actor_id, "complete matching Core prefix");
  if (!found) Require(out.active_event_instance_id == -1 && out.active_event_option_count == 0,
      "proved no-event values");
  return out;
}
} // namespace
int main() {
  using namespace xar::ck3_1210;
  {
    Fixture f; const auto out = Observed(f, true);
    Require(f.actor_id < 0 && f.actor_id != -1 && f.actor_id != 7 && out.active_event_instance_id == 42 &&
        out.active_event_option_count == 2, "event owner is full signed CharacterID, not network player7");
    // Authored payloads carry no enabled/UI data. Reading total2 does not grant
    // shown/clickable/executable choices or a materialized event-window context.
    Require(!out.option_eligibility_observed, "authored count is not clickable count");
  }
  { Fixture f(0); Observed(f, true); }
  { Fixture f; f.Empty(); Observed(f, false); }
  {
    Fixture f; Store(f.definition, 0x140, std::int32_t{0}); Store(f.definition, 0x144, std::int32_t{0});
    Store(f.definition, 0x138, static_cast<void *>(nullptr));
    const auto out = Observed(f, true);
    Require(out.active_event_option_count == 0 && out.active_event_instance_id == 42,
        "zero authored count does not erase a real current instance");
  }
  {
    Fixture f; Store(f.definition, 0x140, static_cast<std::int32_t>(kCurrentEventMaxAuthoredV1));
    Store(f.definition, 0x144, static_cast<std::int32_t>(kCurrentEventMaxAuthoredV1));
    Require(Observed(f, true).active_event_option_count == static_cast<std::int32_t>(kCurrentEventMaxAuthoredV1), "inclusive authored bound");
  }
  {
    Fixture f; std::array<void *, kCurrentEventMaxQueuedV1> many{}; many.fill(f.event.data());
    Store(f.data, kCurrentEventManagerOffsetV1 + 0x1F18, many.data());
    Store(f.data, kCurrentEventManagerOffsetV1 + 0x1F24, static_cast<std::int32_t>(many.size()));
    Observed(f, true);
  }
  {
    Fixture f; const auto expected = f.Expected(); f.bindings.exact_build_admitted = false;
    Unavailable(f, expected, "unsupported_build"); Require(f.selectors == 0, "disabled build makes no selector call");
  }
  {
    Fixture f; f.Empty(); const auto expected = f.Expected(); f.bindings.get_current_event = nullptr;
    Unavailable(f, expected, "event_binding_unavailable");
  }
  {
    Fixture f; f.Empty(); const auto expected = f.Expected(); f.selector_character = -1;
    Unavailable(f, expected, "selector_character_mismatch");
    Require(f.selectors == 0, "invalid selector cache cannot manufacture two null results");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.selector_character = 7;
    Unavailable(f, expected, "selector_character_mismatch");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.event, 0x1C0, std::int32_t{7});
    Unavailable(f, expected, "event_character_mismatch");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.current = f.other_event.data();
    Unavailable(f, expected, "current_event_not_owned");
  }
  for (const auto id : {std::int32_t{-1},std::int32_t{0}}) {
    Fixture f; const auto expected = f.Expected(); Store(f.event, 0x1C4, id);
    Unavailable(f, expected, "event_instance_invalid");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.event, 0x1B8, static_cast<void *>(nullptr));
    Unavailable(f, expected, "event_definition_unavailable");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.definition, 0, std::uintptr_t{1});
    Unavailable(f, expected, "event_definition_type_mismatch");
  }
  for (const auto offset : {std::size_t{0x140},std::size_t{0x144}}) {
    Fixture f; const auto expected = f.Expected(); Store(f.definition, offset, std::int32_t{-1});
    Unavailable(f, expected, "event_options_header_invalid");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.definition, 0x144, std::int32_t{3});
    Unavailable(f, expected, "event_options_header_invalid");
  }
  {
    Fixture f; const auto expected = f.Expected();
    Store(f.definition, 0x140, static_cast<std::int32_t>(kCurrentEventMaxAuthoredV1 + 1));
    Unavailable(f, expected, "event_options_bound");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.definition, 0x138, static_cast<void *>(nullptr));
    Unavailable(f, expected, "event_options_header_invalid");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.authored[1] = nullptr;
    Unavailable(f, expected, "event_authored_pointer_invalid");
  }
  for (const auto count : {std::int32_t{-1},static_cast<std::int32_t>(kCurrentEventMaxQueuedV1 + 1)}) {
    Fixture f; const auto expected = f.Expected(); Store(f.data, kCurrentEventManagerOffsetV1 + 0x1F24, count);
    Unavailable(f, expected); Require(f.selectors == 0, "queue bound/header checked before selector");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.queue[0] = nullptr;
    Unavailable(f, expected, "event_queue_read_failed");
  }
  for (const auto mutation : {Mutation::null_second,Mutation::event_second,Mutation::instance_second,
      Mutation::definition_second,Mutation::count_second,Mutation::capacity_second,Mutation::authored_second,
      Mutation::character_second,Mutation::cache_second,Mutation::queue_second,Mutation::data_second,
      Mutation::selector_date,Mutation::selector_pause,Mutation::selector_actor_type,Mutation::core_date_second,
      Mutation::core_local_second,Mutation::core_generation_second,Mutation::core_current_second,
      Mutation::core_actor_second,Mutation::core_final_date,Mutation::core_final_instance,Mutation::core_final_queue}) {
    Fixture f; const auto expected = f.Expected(); f.mutation = mutation; Unavailable(f, expected);
  }
  {
    Fixture f; f.Empty(); const auto expected = f.Expected(); f.mutation = Mutation::cache_second;
    Unavailable(f, expected, "event_root_changed");
  }
  {
    Fixture f; auto expected = f.Expected(); expected.clock.paused = false;
    Unavailable(f, expected, "requires_paused");
  }
  {
    Fixture f; auto expected = f.Expected(); expected.map_ready = false;
    Unavailable(f, expected, "map_not_ready");
  }
  {
    Fixture f; auto expected = f.Expected(); expected.played_character_id = -1;
    Unavailable(f, expected, "player_identity_unavailable");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.actor, 0x1C, std::uint32_t{0});
    Unavailable(f, expected, "player_identity_unavailable");
  }
#if defined(_MSC_VER)
  {
    Fixture f; const auto expected = f.Expected(); Store(f.definition, 0x138, reinterpret_cast<void *>(std::uintptr_t{1}));
    Unavailable(f, expected, "memory_read_failed");
  }
#endif
  {
    constexpr std::uintptr_t base = 0x140000000;
    const auto b = BindCurrentEventSnapshotImageV1(base, kExecutableSha256);
    Require(b.exact_build_admitted && b.core.enabled && b.definition_vtable == base + 0x4E52FA8 &&
        reinterpret_cast<std::uintptr_t>(b.get_current_event) == base + 0x2EBF120 &&
        reinterpret_cast<std::uintptr_t>(b.selector_character_id_slot) == base + 0x5D50448, "exact Florin bindings");
    const auto wrong = BindCurrentEventSnapshotImageV1(base, "old-or-unknown");
    Require(!wrong.exact_build_admitted && !wrong.core.enabled && !wrong.get_current_event &&
        !wrong.selector_character_id_slot && !wrong.definition_vtable, "wrong build leaves empty binding");
    Require(!BindCurrentEventSnapshotImageV1(0, kExecutableSha256).exact_build_admitted &&
        !BindCurrentEventSnapshotImageV1((std::numeric_limits<std::uintptr_t>::max)(),
            kExecutableSha256).exact_build_admitted, "zero/overflow address rejected");
  }
  std::cout << "PASS ck3_1210_current_event_snapshot_v1 NoGame; authored-only; full=false; actions=0" << std::endl;
  return 0;
}
