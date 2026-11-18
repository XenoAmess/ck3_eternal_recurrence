// SOURCE ONLY: not compiled or executed by slot41.
// Integrator: compile C++20 with ck3_1210_core.cpp and the two added files.
#include "xar_bridge/ck3_1210_character_manager_v1.hpp"
#include <array>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <vector>
namespace {
using namespace xar::ck3_1210;
constexpr auto kActor = std::bit_cast<std::int32_t>(0x81000001U);
constexpr auto kPeer = std::bit_cast<std::int32_t>(0xFE000002U);
void Check(bool value, const char *message) {
  if (!value) { std::cerr << "FAIL " << message << '\n'; std::exit(1); }
}
template<class Buffer, class T> void Put(Buffer &b, std::size_t offset, T value) {
  Check(offset <= b.size() && sizeof(T) <= b.size() - offset, "fixture bounds");
  std::memcpy(b.data() + offset, &value, sizeof(T));
}
enum class Mutation { none, generation, death, living, member_pointer,
  members_array, storage, slots, manager_type, date, pause, count, capacity, state,
  final_getter_peer_death };
struct Fixture;
Fixture *active = nullptr;
void *GetPlayer(void *);
struct Fixture {
  std::array<std::byte, 0xA8> state{}, state2{};
  std::array<std::byte, 0x21> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(kCharacterManagerOffsetV1 + 0x38);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x1D8> actor{}, peer{}, peer2{}, zero{}, dead{};
  std::array<std::byte, 0x30> storage{}, storage2{};
  std::array<std::byte, 0x50> slots{}, slots2{};
  std::array<void *, 4> members{peer.data(), zero.data(), dead.data(), actor.data()};
  std::array<void *, 4> members2{};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data(),
    *storage_pointer = storage.data();
  CharacterManagerBindingsV1 bindings{};
  Mutation mutation = Mutation::none;
  const void *deny = nullptr;
  unsigned root_reads = 0, player_calls = 0;
  Fixture() {
    active = this;
    Put(state, 8, std::int32_t{53177016}); Put(state, 0x70, std::int32_t{4});
    Put(state, 0xA0, data.data()); state2 = state;
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, kActor);
    Init(actor, kActor); Init(peer, kPeer); Init(peer2, kPeer); Init(zero, 0); Init(dead, 3);
    Put(actor, 0x1B0, actor.data()); Put(peer, 0x1B0, peer.data());
    Put(peer2, 0x1B0, peer.data()); Put(dead, 0x1D0, dead.data());
    Place(1, actor.data()); Place(2, peer.data()); Place(0, zero.data()); Place(3, dead.data());
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{5});
    storage2 = storage; slots2 = slots; members2 = members;
    bindings = BindCharacterManagerImageV1(0x140000000, kExecutableSha256);
    bindings.core = {true, &state_pointer, &jomini_pointer, &storage_pointer, GetPlayer};
    Put(data, kCharacterManagerOffsetV1, bindings.manager_vtable);
    Put(data, kCharacterManagerOffsetV1 + 0x20, members.data());
    Put(data, kCharacterManagerOffsetV1 + 0x28, std::int32_t{4});
    Put(data, kCharacterManagerOffsetV1 + 0x2C, std::int32_t{4});
  }
  template<class Buffer> void Init(Buffer &b, std::int32_t id) {
    Put(b, 0x18, id); Put(b, 0x1C, std::uint32_t{0x43686172});
  }
  void Place(std::size_t index, void *object) { Put(slots, index * 0x10 + 8, object); }
  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix out{};
    Check(ReadCoreSnapshot(bindings.core, out) && out.has_played_character &&
      out.played_character_id == kActor && out.played_character_alive, "core setup");
    player_calls = root_reads = 0; return out;
  }
  void Apply() {
    switch (mutation) {
    case Mutation::generation: Put(peer, 0x18, std::bit_cast<std::int32_t>(0xFD000002U)); break;
    case Mutation::death: Put(peer, 0x1D0, peer.data()); break;
    case Mutation::living: Put(peer, 0x1B0, static_cast<void *>(nullptr)); break;
    case Mutation::member_pointer: members[0] = peer2.data(); Place(2, peer2.data()); break;
    case Mutation::members_array: Put(data, kCharacterManagerOffsetV1 + 0x20, members2.data()); break;
    case Mutation::storage: storage_pointer = storage2.data(); break;
    case Mutation::slots: Put(storage, 0x20, slots2.data()); break;
    case Mutation::manager_type: Put(data, kCharacterManagerOffsetV1, std::uintptr_t{1}); break;
    case Mutation::date: Put(state, 8, std::int32_t{53177017}); break;
    case Mutation::pause: jomini[0x20] = std::byte{}; break;
    case Mutation::count: Put(data, kCharacterManagerOffsetV1 + 0x2C, std::int32_t{3}); break;
    case Mutation::capacity: Put(data, kCharacterManagerOffsetV1 + 0x28, std::int32_t{5}); break;
    case Mutation::state: state_pointer = state2.data(); break;
    default: break;
    }
  }
  static bool Copy(void *context, const void *source, void *destination,
      std::size_t bytes) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    if (source == f.deny) return false;
    if (source == &f.storage_pointer && ++f.root_reads == 3) f.Apply();
    std::memcpy(destination, source, bytes); return true;
  }
  bool Read(const CoreSnapshotPrefix &expected, CharacterManagerObservationV1 &out) {
    return ReadCharacterManagerV1(bindings, expected, out, {this, Copy});
  }
};
void *GetPlayer(void *) {
  auto &f = *active;
  // A peer can change in the middle Core getter while the playedactor frame
  // remains identical; this must be detected by the second full transcript.
  if (++f.player_calls == 2 && f.mutation == Mutation::final_getter_peer_death)
    Put(f.peer, 0x1D0, f.peer.data());
  return f.player.data();
}
void Rejected(Fixture &f, CoreSnapshotPrefix expected, const char *label) {
  CharacterManagerObservationV1 out{};
  out.available = out.same_frame_ready = out.manager_members_complete = true;
  out.members.push_back({123, true, true});
  Check(!f.Read(expected, out), label);
  Check(!out.available && !out.same_frame_ready && !out.manager_members_complete &&
    !out.candidates_complete && !out.full_snapshot_available && out.members.empty() &&
    !out.unavailable_reason.empty(), "failure clears every value and scope flag");
}
} // namespace
int main() {
  Check(!BindCharacterManagerImageV1(0, kExecutableSha256).exact_build_admitted, "zero base");
  Check(!BindCharacterManagerImageV1(0x140000000, "wrong").exact_build_admitted, "wrong sha");
  Check(!BindCharacterManagerImageV1((std::numeric_limits<std::uintptr_t>::max)(),
    kExecutableSha256).exact_build_admitted, "overflow base");
  {
    Fixture f; const auto expected = f.Expected(); CharacterManagerObservationV1 out{};
    Check(f.Read(expected, out), "exact manager read beyond playedactor");
    Check(out.available && out.same_frame_ready && out.manager_members_complete &&
      !out.candidates_complete && !out.full_snapshot_available && out.unavailable_reason.empty(),
      "only maintained-member scope qualified");
    Check(out.members == std::vector<CharacterManagerMemberV1>{{kPeer,true,true},
      {0,true,false},{3,false,false},{kActor,true,true}},
      "native order, signed fullgen, zero, dead and independent living values");
  }
  {
    Fixture f; const auto expected = f.Expected(); CharacterManagerObservationV1 out{};
    Put(f.data, kCharacterManagerOffsetV1 + 0x28, std::int32_t{0});
    Put(f.data, kCharacterManagerOffsetV1 + 0x2C, std::int32_t{0});
    Put(f.data, kCharacterManagerOffsetV1 + 0x20, static_cast<void *>(nullptr));
    Check(f.Read(expected, out) && out.manager_members_complete && out.members.empty() &&
      !out.candidates_complete, "real empty vector does not prove a candidate universe");
  }
  for (const auto m : {Mutation::generation, Mutation::death, Mutation::living,
      Mutation::member_pointer, Mutation::members_array, Mutation::storage,
      Mutation::slots, Mutation::manager_type, Mutation::date, Mutation::pause,
      Mutation::count, Mutation::capacity, Mutation::state, Mutation::final_getter_peer_death}) {
    Fixture f; const auto expected = f.Expected(); f.mutation = m;
    Rejected(f, expected, "root/member/generation/lifecycle change rejected");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.members[1] = f.members[0];
    Rejected(f, expected, "duplicate full32 rejected");
  }
  {
    Fixture f; const auto expected = f.Expected(); Put(f.peer, 0x18, std::int32_t{-1});
    Rejected(f, expected, "minus-one sentinel rejected");
  }
  {
    Fixture f; const auto expected = f.Expected(); Put(f.peer, 0x1C, std::uint32_t{0x41726D79});
    Rejected(f, expected, "wrong typed object rejected");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.Place(2, f.peer2.data());
    Rejected(f, expected, "same fullgen but different storage object rejected");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.members[0] = nullptr;
    Rejected(f, expected, "null member never silently dropped");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.deny = f.peer.data() + 0x1D0;
    Rejected(f, expected, "exact field read failure never an empty collection");
  }
  for (const auto count : {-1, kCharacterManagerMemberLimitV1 + 1}) {
    Fixture f; const auto expected = f.Expected();
    Put(f.data, kCharacterManagerOffsetV1 + 0x2C, count);
    Rejected(f, expected, "invalid or over-budget count rejected");
  }
  // The manager header can be fully readable while its claimed count exceeds
  // the actual allocated capacity. Do not read adjacent valid-looking rows.
  for (const auto capacity : {-1, 0, 3}) {
    Fixture f; const auto expected = f.Expected();
    Put(f.data, kCharacterManagerOffsetV1 + 0x28, capacity);
    Rejected(f, expected, "manager count exceeds capacity or capacity invalid");
  }
  {
    Fixture f; const auto expected = f.Expected();
    Put(f.data, kCharacterManagerOffsetV1 + 0x2C, std::int32_t{0});
    Put(f.data, kCharacterManagerOffsetV1 + 0x20, static_cast<void *>(nullptr));
    Rejected(f, expected, "positive allocated capacity cannot have a null data pointer");
  }
  for (const auto capacity : {0, -1, kCharacterLookupCapacityLimitV1 + 1}) {
    Fixture f; const auto expected = f.Expected(); Put(f.storage, 0x2C, capacity);
    Rejected(f, expected, "invalid or over-budget capacity rejected");
  }
  {
    Fixture f; auto expected = f.Expected(); expected.clock.paused = false;
    Rejected(f, expected, "paused ownership precondition");
  }
  std::cout << "PASS character manager exact roots, full generation, source scope and lifecycle\n";
  return 0;
}
