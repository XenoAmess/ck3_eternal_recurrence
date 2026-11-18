#include "xar_bridge/ck3_1210_pending_snapshot_v1.hpp"
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
constexpr auto kSenderId = std::bit_cast<std::int32_t>(std::uint32_t{0x83000002});
void Require(bool value, const char *message) {
  if (!value) { std::cerr << "FAIL " << message << std::endl; std::exit(1); }
}
template <class Buffer, class T>
void Store(Buffer &buffer, std::size_t offset, T value) {
  Require(offset <= buffer.size() && sizeof(value) <= buffer.size() - offset, "fixture bounds");
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
template <class T> T Load(const void *object, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <class T> concept HasSubmit = requires(T value) { value.submit_command; };
static_assert(!HasSubmit<PendingSnapshotBindingsV1>);
enum class Mutation {
  none, date_first, date_second, pause_second, speed_second, local_second,
  actor_second, generation_second, root_second, sender_second, id_second,
  row_second, new_row_second, header_second, predicate_sender, validator_notification
};
struct Fixture;
Fixture *active = nullptr;
void *LocalPlayer(void *);
bool IsPending(void *, void *);
bool Validate(void *);
struct Fixture {
  std::array<std::byte, 0xA8> state{}, other_state{};
  std::array<std::byte, 0x21> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(kPlayerCharacterManagerOffset + 0x70);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x1D8> actor{}, replacement{};
  std::array<std::byte, 0x30> character_storage{}, database{};
  std::array<std::byte, 0x20> character_slots{};
  std::array<std::byte, 0x40> rows{}, other_rows{};
  std::array<std::array<std::byte, 0x5D8>, 4> pending{};
  std::array<bool, 4> accepts{true,true,true,true}, validates{true,true,true,true};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data();
  void *character_storage_pointer = character_storage.data(), *database_pointer = database.data();
  PendingSnapshotBindingsV1 bindings{};
  Mutation mutation = Mutation::none;
  unsigned core_reads = 0, predicate_calls = 0, validator_calls = 0, queue_calls = 0;
  std::int32_t actor_id;
  explicit Fixture(std::int32_t id = kActorId) : actor_id(id) {
    active = this;
    Store(state, 8, std::int32_t{123456}); Store(state, 0x70, std::int32_t{4});
    Store(state, 0xA0, data.data()); other_state = state;
    Store(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Store(players, 0x1F0, std::int32_t{7}); Store(player, 0x70, std::int32_t{7});
    Store(data, kPlayerCharacterManagerOffset + 0x58, entries.data());
    Store(data, kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Store(entry, 0xD8, std::int32_t{7}); Store(entry, 0xB0, actor_id);
    Store(actor, 0x18, actor_id); Store(actor, 0x1C, std::uint32_t{0x43686172});
    replacement = actor;
    Store(character_storage, 0x20, character_slots.data());
    Store(character_storage, 0x2C, std::int32_t{2}); PlaceActor(actor.data());
    bindings = BindPendingSnapshotImageV1(0x140000000, kExecutableSha256);
    Require(bindings.exact_build_admitted, "exact constructor");
    bindings.core = {true,&state_pointer,&jomini_pointer,&character_storage_pointer,&LocalPlayer};
    bindings.pending_storage_slot = &database_pointer;
    bindings.is_pending_for_character = &IsPending; bindings.validate_reply = &Validate;
    Store(database, 0, bindings.database_vtable); Store(database, 0x20, rows.data());
    Store(database, 0x2C, std::int32_t{4}); Add(0);
  }
  void PlaceActor(void *pointer) {
    const auto index = static_cast<std::uint32_t>(actor_id) & 0xFFFFFFU;
    Store(character_slots, std::size_t{index} * 0x10 + 8, pointer);
  }
  void Add(std::size_t index, std::int32_t kind = 0, bool notification = false) {
    auto &p = pending[index]; p.fill(std::byte{});
    const auto full_id = std::bit_cast<std::int32_t>(std::uint32_t{0x82000000} | static_cast<std::uint32_t>(index));
    Store(p, 0, bindings.pending_vtable); Store(p, 0x10, full_id);
    Store(p, 0x14, kPendingSnapshotTypeV1); Store(p, 0x300, kSenderId);
    Store(p, 0x304, actor_id); Store(p, 0x310, actor_id); Store(p, 0x5D0, kind);
    p[0x5D6] = notification ? std::byte{1} : std::byte{};
    Store(rows, index * 0x10 + 8, p.data());
  }
  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix result{};
    Require(ReadCoreSnapshot(bindings.core, result), "fixture Core capture");
    Require(result.has_played_character && result.played_character_id == actor_id, "full actor ID");
    core_reads = 0; return result;
  }
};
void *LocalPlayer(void *) {
  auto &f = *active; ++f.core_reads;
  if (f.core_reads == 1 && f.mutation == Mutation::date_first)
    Store(f.state, 8, std::int32_t{123457});
  if (f.core_reads == 2) {
    switch (f.mutation) {
    case Mutation::date_second: Store(f.state, 8, std::int32_t{123457}); break;
    case Mutation::pause_second: f.jomini[0x20] = std::byte{}; break;
    case Mutation::speed_second: Store(f.state, 0x70, std::int32_t{3}); break;
    case Mutation::local_second: Store(f.players, 0x1F0, std::int32_t{8}); break;
    case Mutation::actor_second: f.PlaceActor(f.replacement.data()); break;
    case Mutation::generation_second:
      Store(f.actor, 0x18, std::bit_cast<std::int32_t>(std::uint32_t{0x84000001})); break;
    case Mutation::root_second: f.state_pointer = f.other_state.data(); break;
    case Mutation::sender_second: Store(f.pending[0], 0x300, std::int32_t{22}); break;
    case Mutation::id_second:
      Store(f.pending[0], 0x10, std::bit_cast<std::int32_t>(std::uint32_t{0x85000000})); break;
    case Mutation::row_second: Store(f.rows, 8, static_cast<void *>(nullptr)); break;
    case Mutation::new_row_second: f.Add(3); break;
    case Mutation::header_second: Store(f.database, 0x20, f.other_rows.data()); break;
    default: break;
    }
  }
  return f.player.data();
}
bool IsPending(void *pending, void *character) {
  auto &f = *active; ++f.predicate_calls;
  Require(character == f.actor.data(), "native predicate receives resolved actual actor");
  const auto id = Load<std::int32_t>(pending, 0x10);
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  Require(index < f.pending.size() && pending == f.pending[index].data(), "predicate object and full ID");
  if (f.mutation == Mutation::predicate_sender && f.predicate_calls == 1)
    Store(f.pending[0], 0x300, std::int32_t{99});
  return f.accepts[index];
}
bool Validate(void *opaque) {
  auto &f = *active; ++f.validator_calls;
  const auto &c = *static_cast<PendingReplyValidationCommandV1 *>(opaque);
  Require(c.primary_vtable == f.bindings.reply_primary_vtable &&
      c.secondary_vtable == f.bindings.reply_secondary_vtable && c.flags == 0 &&
      c.choice == 0, "validation-only DTO uses new vtables, flags and accept choice");
  for (const auto byte : c.reserved) Require(byte == std::byte{}, "DTO reserved bytes zero");
  const auto index = static_cast<std::uint32_t>(c.instance_id) & 0xFFFFFFU;
  Require(index < f.pending.size() && c.instance_id == Load<std::int32_t>(f.pending[index].data(), 0x10),
      "DTO preserves complete signed generation ID");
  if (f.mutation == Mutation::validator_notification && f.validator_calls == 1)
    f.pending[0][0x5D6] = std::byte{1};
  Require(f.queue_calls == 0, "validation does not enqueue");
  return f.validates[index];
}
void Unavailable(Fixture &f, const CoreSnapshotPrefix &expected, std::string_view reason = {}) {
  PendingSnapshotObservationV1 out{};
  out.available = out.found = out.same_frame_ready = true;
  out.pending_character_interaction_id = 777; out.pending_sender_character_id = 888;
  out.pending_auto_accept_notification = true; out.slots_scanned = 42;
  Require(!ReadPendingSnapshotV1(f.bindings, expected, out), "unavailable returns false");
  Require(!out.available && !out.found && !out.same_frame_ready &&
      out.pending_character_interaction_id == -1 && out.pending_sender_character_id == -1 &&
      !out.pending_auto_accept_notification && out.slots_scanned == 0 &&
      !out.unavailable_reason.empty(), "failure clears stale selection and cannot claim empty");
  if (!reason.empty()) Require(out.unavailable_reason == reason, "exact failure reason");
  Require(out.partial && !out.full_snapshot_available && f.queue_calls == 0,
      "failure is neither full Snapshot nor action");
}
PendingSnapshotObservationV1 Observed(Fixture &f, bool found) {
  const auto expected = f.Expected();
  PendingSnapshotObservationV1 out{};
  Require(ReadPendingSnapshotV1(f.bindings, expected, out), "bounded complete observation");
  Require(out.available && out.found == found && out.same_frame_ready &&
      out.partial && !out.full_snapshot_available && out.unavailable_reason.empty(),
      "observed pending family remains partial");
  Require(out.frame.clock.date_raw == expected.clock.date_raw &&
      out.frame.clock.speed == expected.clock.speed && out.frame.clock.paused &&
      out.frame.map_ready && out.frame.has_played_character && out.frame.played_character_alive &&
      out.frame.local_player_id == expected.local_player_id &&
      out.frame.played_character_id == f.actor_id && f.queue_calls == 0, "complete stable Core and no queue");
  if (!found) Require(out.pending_character_interaction_id == -1 &&
      out.pending_sender_character_id == -1 && !out.pending_auto_accept_notification,
      "proved empty carries no stale selected fields");
  return out;
}
} // namespace

int main() {
  using namespace xar::ck3_1210;
  {
    Fixture f;
    const auto out = Observed(f, true);
    Require(f.actor_id < 0 && f.actor_id != -1 && out.pending_character_interaction_id < 0 &&
        out.pending_character_interaction_id != -1 && out.pending_sender_character_id == kSenderId,
        "negative full-generation IDs are valid, including observed sender");
    Require(out.slots_scanned == 4 && out.occupied_slots == 1 &&
        f.predicate_calls == 1 && f.validator_calls == 1 && !out.pending_auto_accept_notification,
        "non-notification validated once and complete scan recorded");
  }
  { Fixture f(0); Observed(f, true); }
  {
    Fixture f; f.rows.fill(std::byte{});
    const auto out = Observed(f, false);
    Require(out.slots_scanned == 4 && out.occupied_slots == 0 &&
        f.predicate_calls == 0 && f.validator_calls == 0, "true empty full collection");
  }
  {
    Fixture f; Store(f.database, 0x2C, std::int32_t{0});
    Store(f.database, 0x20, static_cast<void *>(nullptr));
    Require(Observed(f, false).slots_scanned == 0, "valid stable zero-capacity database");
  }
  {
    Fixture f; f.rows.fill(std::byte{});
    f.Add(0); Store(f.pending[0], 0x304, std::int32_t{123});
    f.Add(1, 3, true); f.Add(2, 1, true); f.Add(3, 2);
    Store(f.pending[2], 0x304, std::int32_t{456}); f.validates[3] = false;
    const auto out = Observed(f, true);
    Require(out.pending_character_interaction_id == Load<std::int32_t>(f.pending[2].data(), 0x10) &&
        out.pending_auto_accept_notification && out.occupied_slots == 4 && out.slots_scanned == 4 &&
        f.predicate_calls == 2 && f.validator_calls == 1,
        "kind1 alternate recipient, kind3 filter, notification skips validator, later rows still checked");
  }
  {
    Fixture f; f.Add(0, 2, true); Store(f.pending[0], 0x310, std::int32_t{123});
    Require(Observed(f, true).pending_auto_accept_notification && f.validator_calls == 0,
        "kind2 uses primary recipient and native notification flag");
  }
  {
    Fixture f; Store(f.pending[0], 0x304, std::int32_t{123});
    Observed(f, false); Require(f.predicate_calls == 0, "nonlocal entry is not evaluated");
  }
  {
    Fixture f; f.Add(0, 3, true); Observed(f, false);
    Require(f.predicate_calls == 0 && f.validator_calls == 0, "known kind3 is not local-eligible");
  }
  {
    Fixture f; f.accepts[0] = false; Observed(f, false);
    Require(f.predicate_calls == 1 && f.validator_calls == 0, "native context rejection is valid filter");
  }
  {
    Fixture f; f.validates[0] = false; Observed(f, false);
    Require(f.predicate_calls == 1 && f.validator_calls == 1, "native accept-validation rejection is filter");
  }
  {
    Fixture f; f.Add(1);
    Store(f.pending[0], 0x10, std::bit_cast<std::int32_t>(std::uint32_t{0xFE000000}));
    Store(f.pending[1], 0x10, std::int32_t{0x01000001});
    const auto out = Observed(f, true);
    Require(out.pending_character_interaction_id == std::bit_cast<std::int32_t>(std::uint32_t{0xFE000000}) &&
        f.validator_calls == 2, "first storage index wins across signed generation IDs");
  }
  {
    Fixture f; const auto expected = f.Expected();
    f.bindings.exact_build_admitted = false; Unavailable(f, expected, "unsupported_build");
    f.bindings.exact_build_admitted = true; f.bindings.core.enabled = false;
    Unavailable(f, expected, "unsupported_build");
    Require(f.predicate_calls == 0 && f.validator_calls == 0, "disabled binding invokes no native callback");
  }
  {
    Fixture f; const auto expected = f.Expected();
    f.bindings.is_pending_for_character = nullptr;
    Unavailable(f, expected, "pending_binding_unavailable");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.bindings.validate_reply = nullptr;
    Unavailable(f, expected, "pending_binding_unavailable");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.database_pointer = nullptr;
    Unavailable(f, expected, "pending_header_unreadable");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.database, 0, std::uintptr_t{1});
    Unavailable(f, expected, "pending_database_type_mismatch");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.database, 0x2C, std::int32_t{-1});
    Unavailable(f, expected, "pending_capacity_invalid");
  }
  {
    Fixture f; const auto expected = f.Expected();
    Store(f.database, 0x2C, static_cast<std::int32_t>(kPendingSnapshotMaxSlotsV1 + 1));
    Unavailable(f, expected, "pending_capacity_bound");
  }
  {
    Fixture f; std::vector<std::byte> large(kPendingSnapshotMaxSlotsV1 * 0x10);
    Store(f.database, 0x20, large.data());
    Store(f.database, 0x2C, static_cast<std::int32_t>(kPendingSnapshotMaxSlotsV1));
    Require(Observed(f, false).slots_scanned == kPendingSnapshotMaxSlotsV1,
        "inclusive adapter work bound is completely scanned");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.database, 0x20, static_cast<void *>(nullptr));
    Unavailable(f, expected, "pending_slots_unavailable");
  }
  {
    Fixture f; const auto expected = f.Expected();
    Store(f.database, 0x20, reinterpret_cast<void *>((std::numeric_limits<std::uintptr_t>::max)() - 7));
    Unavailable(f, expected, "pending_read_failed");
  }
  for (const auto offset : {std::size_t{0},std::size_t{0x14},std::size_t{0x10}}) {
    Fixture f; const auto expected = f.Expected();
    if (offset == 0) Store(f.pending[0], offset, std::uintptr_t{0x448BC28});
    else if (offset == 0x14) Store(f.pending[0], offset, std::uint32_t{0});
    else Store(f.pending[0], offset, std::int32_t{-1});
    Unavailable(f, expected, "pending_identity_invalid");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.pending[0], 0x10, std::int32_t{1});
    Unavailable(f, expected, "pending_identity_invalid");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.pending[0], 0x5D0, std::int32_t{4});
    Unavailable(f, expected, "pending_kind_unsupported");
  }
  {
    Fixture f; f.Add(3); const auto expected = f.Expected();
    Store(f.pending[3], 0x14, std::uint32_t{0});
    Unavailable(f, expected, "pending_identity_invalid");
    Require(f.validator_calls == 1, "late invalid row defeats earlier valid selected entry");
  }
  for (const auto mutation : {Mutation::date_first,Mutation::date_second,
      Mutation::pause_second,Mutation::speed_second,Mutation::local_second,
      Mutation::actor_second,Mutation::generation_second,Mutation::root_second,
      Mutation::sender_second,Mutation::id_second,Mutation::row_second,
      Mutation::new_row_second,Mutation::header_second,Mutation::predicate_sender,
      Mutation::validator_notification}) {
    Fixture f; const auto expected = f.Expected(); f.mutation = mutation;
    Unavailable(f, expected);
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
    Fixture f; auto expected = f.Expected(); expected.has_played_character = false;
    Unavailable(f, expected, "player_identity_unavailable");
  }
  {
    Fixture f; auto expected = f.Expected(); expected.played_character_id = -1;
    Unavailable(f, expected, "player_identity_unavailable");
  }
  {
    Fixture f; auto expected = f.Expected(); expected.played_character_alive = false;
    Unavailable(f, expected, "player_not_alive");
  }
  {
    Fixture f; auto expected = f.Expected(); ++expected.clock.date_raw;
    Unavailable(f, expected, "core_frame_changed");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.actor, 0x1C, std::uint32_t{0x4C616E64});
    Unavailable(f, expected, "player_identity_unavailable");
  }
  {
    Fixture f; const auto expected = f.Expected(); Store(f.actor, 0x18, std::int32_t{1});
    Unavailable(f, expected); // Low index same, high generation mismatched.
  }
  {
    Fixture f; const auto expected = f.Expected(); f.bindings.core.get_local_player = nullptr;
    Unavailable(f, expected, "core_binding_unavailable");
  }
#if defined(_MSC_VER)
  {
    Fixture f; const auto expected = f.Expected();
    f.bindings.pending_storage_slot = reinterpret_cast<void **>(std::uintptr_t{1});
    Unavailable(f, expected, "memory_read_failed"); // NoGame SEH read fault.
  }
#endif
  {
    constexpr std::uintptr_t base = 0x140000000;
    const auto exact = BindPendingSnapshotImageV1(base, kExecutableSha256);
    Require(exact.exact_build_admitted && exact.core.enabled &&
        reinterpret_cast<std::uintptr_t>(exact.pending_storage_slot) == base + 0x6A67190 &&
        reinterpret_cast<std::uintptr_t>(exact.is_pending_for_character) == base + 0x14DEB60 &&
        reinterpret_cast<std::uintptr_t>(exact.validate_reply) == base + 0x2E4F9B0 &&
        exact.database_vtable == base + 0x4E98050 && exact.pending_vtable == base + 0x4E76878 &&
        exact.reply_primary_vtable == base + 0x4AF48D0 &&
        exact.reply_secondary_vtable == base + 0x4AF4898, "exact Florin address-only binding");
    const auto wrong = BindPendingSnapshotImageV1(base, "old-or-unknown-sha");
    Require(!wrong.exact_build_admitted && !wrong.core.enabled && !wrong.pending_storage_slot &&
        !wrong.is_pending_for_character && !wrong.validate_reply && !wrong.reply_primary_vtable &&
        !wrong.reply_secondary_vtable, "wrong SHA leaves no partial binding");
    Require(!BindPendingSnapshotImageV1(0, kExecutableSha256).exact_build_admitted &&
        !BindPendingSnapshotImageV1((std::numeric_limits<std::uintptr_t>::max)(),
            kExecutableSha256).exact_build_admitted, "zero/overflow image unavailable");
  }
  std::cout << "PASS ck3_1210_pending_snapshot_v1 NoGame fixtures; queue_calls=0; full_snapshot=false" << std::endl;
  return 0;
}
