#include "xar_bridge/ck3_1210_actor_foundation_v1.hpp"

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
constexpr auto kPeerId = std::bit_cast<std::int32_t>(std::uint32_t{0x82000002});
constexpr std::int32_t kOtherPeerId = 0x03000003;
void Require(bool value, const char *message) {
  if (!value) { std::cerr << "FAIL " << message << '\n'; std::exit(1); }
}
template <class Buffer, class T>
void Store(Buffer &buffer, std::size_t offset, T value) {
  Require(offset <= buffer.size() && sizeof(value) <= buffer.size() - offset,
      "fixture store bounds");
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
enum class Mutation {
  none, date_first, paused_first, actor_second, family_second, living_second,
  gold_second, stress_second, betrothed_second, spouse_second, capacity_second,
  peer_pointer_second, peer_generation_second, map_second, death_second,
  actor_generation_second, type_second
};
struct Fixture;
Fixture *active = nullptr;
void *LocalPlayer(void *);

struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x21> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data =
      std::vector<std::byte>(kPlayerCharacterManagerOffset + 0x70);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x1D8> actor{}, actor_replacement{}, peer{}, zero_peer{},
      other_peer{}, peer_replacement{};
  std::array<std::byte, 0x300> living{}, other_living{};
  std::array<std::byte, 0x30> family{}, other_family{}, storage{};
  std::array<std::byte, 0x40> slots{};
  std::array<std::int32_t, 66> spouse_ids{};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data(),
      *storage_pointer = storage.data();
  ActorFoundationBindingsV1 bindings{};
  Mutation mutation = Mutation::none;
  unsigned reads = 0;

  Fixture() {
    active = this;
    Store(state, 8, std::int32_t{123456});
    Store(state, 0x70, std::int32_t{4}); Store(state, 0xA0, data.data());
    Store(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Store(players, 0x1F0, std::int32_t{7}); Store(player, 0x70, std::int32_t{7});
    Store(data, kPlayerCharacterManagerOffset + 0x58, entries.data());
    Store(data, kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Store(entry, 0xD8, std::int32_t{7}); Store(entry, 0xB0, kActorId);
    Init(actor, kActorId); Init(actor_replacement, kActorId);
    Init(peer, kPeerId); Init(peer_replacement, kPeerId);
    Init(zero_peer, 0); Init(other_peer, kOtherPeerId);
    Store(actor, 0x1B0, living.data());
    Store(actor_replacement, 0x1B0, living.data());
    Store(living, 0x100, std::int64_t{12345000});
    Store(living, 0x130, std::int64_t{-200000});
    Store(living, 0x110, std::int64_t{0}); Store(living, 0x2F8, std::int32_t{42});
    other_living = living;
    Store(storage, 0x20, slots.data()); Store(storage, 0x2C, std::int32_t{4});
    Place(kActorId, actor.data()); Place(kPeerId, peer.data());
    Place(0, zero_peer.data()); Place(kOtherPeerId, other_peer.data());
    bindings = BindActorFoundationImageV1(0x140000000, kExecutableSha256);
    Require(bindings.exact_build_admitted, "exact synthetic binding");
    bindings.core = {true, &state_pointer, &jomini_pointer, &storage_pointer, &LocalPlayer};
  }
  template <class Buffer>
  void Init(Buffer &buffer, std::int32_t id) {
    Store(buffer, 0x18, id); Store(buffer, 0x1C, std::uint32_t{0x43686172});
  }
  void Place(std::int32_t id, void *object) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Store(slots, index * 0x10 + 8, object);
  }
  void WithFamily() {
    Store(actor, 0x1A8, family.data());
    Store(actor_replacement, 0x1A8, family.data());
    Store(family, 0x10, std::int32_t{-1}); Store(family, 0x14, std::int32_t{-1});
    other_family = family;
  }
  void WithSpouses() {
    WithFamily();
    spouse_ids[0] = kPeerId; spouse_ids[1] = 0;
    Store(family, 0x10, kOtherPeerId); Store(family, 0x14, kPeerId);
    Store(family, 0x20, spouse_ids.data());
    Store(family, 0x28, std::int32_t{2}); Store(family, 0x2C, std::int32_t{2});
    other_family = family;
  }
  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix result{};
    Require(ReadCoreSnapshot(bindings.core, result) && result.map_ready &&
        result.has_played_character && result.played_character_id == kActorId &&
        result.played_character_alive, "real Core fixture capture");
    reads = 0;
    return result;
  }
};

void *LocalPlayer(void *) {
  auto &f = *active; ++f.reads;
  if (f.reads == 1 && f.mutation == Mutation::date_first)
    Store(f.state, 8, std::int32_t{123457});
  if (f.reads == 1 && f.mutation == Mutation::paused_first)
    f.jomini[0x20] = std::byte{};
  if (f.reads == 2) {
    switch (f.mutation) {
    case Mutation::actor_second: f.Place(kActorId, f.actor_replacement.data()); break;
    case Mutation::family_second: Store(f.actor, 0x1A8, f.other_family.data()); break;
    case Mutation::living_second: Store(f.actor, 0x1B0, f.other_living.data()); break;
    case Mutation::gold_second: Store(f.living, 0x100, std::int64_t{12345001}); break;
    case Mutation::stress_second: Store(f.living, 0x2F8, std::int32_t{43}); break;
    case Mutation::betrothed_second: Store(f.family, 0x10, std::int32_t{0}); break;
    case Mutation::spouse_second: f.spouse_ids[0] = kOtherPeerId; break;
    case Mutation::capacity_second: Store(f.family, 0x28, std::int32_t{3}); break;
    case Mutation::peer_pointer_second: f.Place(kPeerId, f.peer_replacement.data()); break;
    case Mutation::peer_generation_second:
      Store(f.peer, 0x18, std::bit_cast<std::int32_t>(std::uint32_t{0x83000002})); break;
    case Mutation::map_second: return nullptr;
    case Mutation::death_second: Store(f.actor, 0x1D0, f.actor.data()); break;
    case Mutation::actor_generation_second:
      Store(f.actor, 0x18, std::bit_cast<std::int32_t>(std::uint32_t{0x82000001})); break;
    case Mutation::type_second: Store(f.actor, 0x1C, std::uint32_t{0x4C616E64}); break;
    default: break;
    }
  }
  return f.player.data();
}

void CheckScope(const ActorFoundationObservationV1 &out) {
  Require(out.schema == kActorFoundationSchemaV1 && out.game_version == kGameVersion &&
      out.steam_build_id == kSteamBuildId && out.executable_sha256 == kExecutableSha256 &&
      out.executable_file_size == kExecutableFileSize && out.resource_scale == 100000,
      "exact tuple and scale");
  Require(out.partial && !out.full_snapshot_available && !out.treasury_observed &&
      !out.monthly_flow_observed, "internal partial does not grant full finance or Snapshot");
}

ActorFoundationObservationV1 Observe(Fixture &f) {
  const auto expected = f.Expected();
  ActorFoundationObservationV1 out{};
  Require(ReadActorFoundationV1(f.bindings, expected, out) && out.available &&
      out.same_frame_ready, "observed stable internal frame");
  CheckScope(out);
  Require(out.frame.played_character_id == kActorId && out.frame.clock.date_raw == 123456 &&
      out.frame.clock.speed == 5 && out.frame.clock.paused && out.frame.local_player_id == 7 &&
      out.frame.map_ready && out.frame.has_played_character && out.frame.played_character_alive,
      "complete prefix retained");
  return out;
}

void WholeUnavailable(Fixture &f, const CoreSnapshotPrefix &expected,
    std::string_view reason) {
  ActorFoundationObservationV1 out{};
  out.available = true; out.gold_raw = 777; out.prestige_raw = 888;
  out.piety_raw = 999; out.stress_points = 10;
  out.relationships = ActorFoundationRelationshipsV1{};
  Require(!ReadActorFoundationV1(f.bindings, expected, out) && !out.available &&
      !out.same_frame_ready && !out.resources_ready && !out.relationships_ready &&
      !out.gold_raw && !out.prestige_raw && !out.piety_raw && !out.stress_points &&
      !out.relationships && out.unavailable_reason == reason,
      "whole failure clears old observations");
  CheckScope(out);
}

void FamilyUnavailable(Fixture &f, std::string_view reason) {
  const auto out = Observe(f);
  Require(out.resources_ready && out.gold_raw && out.prestige_raw && out.piety_raw &&
      out.stress_points && !out.relationships_ready && !out.relationships &&
      out.relationships_unavailable_reason == reason &&
      out.unavailable_reason == "actor_foundation_partial", "bad family cannot become empty");
}
} // namespace

int main() {
  using namespace xar::ck3_1210;
  {
    Fixture f;
    Require(kActorId < 0 && kPeerId < 0, "signed high generations exercised");
    auto out = Observe(f);
    Require(out.resources_ready && out.gold_raw == 12345000 && out.prestige_raw == -200000 &&
        out.piety_raw == 0 && out.stress_points == 42, "four atomic native values");
    Require(out.relationships_ready && out.relationships &&
        out.relationships->betrothed_character_id == -1 &&
        out.relationships->primary_spouse_character_id == -1 &&
        out.relationships->spouse_character_ids.empty(), "real null family is empty");
    for (const auto amount : {std::int64_t{0}, std::int64_t{-1},
             (std::numeric_limits<std::int64_t>::min)(),
             (std::numeric_limits<std::int64_t>::max)()}) {
      Store(f.living, 0x100, amount); Store(f.living, 0x130, amount);
      Store(f.living, 0x110, amount); out = Observe(f);
      Require(out.resources_ready && out.gold_raw == amount &&
          out.prestige_raw == amount && out.piety_raw == amount, "signed i64 extrema");
    }
    for (const auto stress : {(std::numeric_limits<std::int32_t>::min)(),
             std::int32_t{0}, (std::numeric_limits<std::int32_t>::max)()}) {
      Store(f.living, 0x2F8, stress); out = Observe(f);
      Require(out.resources_ready && out.stress_points == stress,
          "signed native stress retained without gameplay validity claim");
    }
    Store(f.actor, 0x1B0, static_cast<void *>(nullptr)); out = Observe(f);
    Require(out.resources_ready && out.gold_raw == 0 && out.prestige_raw == 0 &&
        out.piety_raw == 0 && out.stress_points == 0, "null living is observed zero");
  }
  {
    Fixture f; f.WithFamily(); auto out = Observe(f);
    Require(out.relationships_ready && out.relationships->spouse_character_ids.empty(),
        "nonnull empty family");
    Store(f.family, 0x20, f.spouse_ids.data()); Store(f.family, 0x28, std::int32_t{66});
    out = Observe(f);
    Require(out.relationships_ready && out.relationships->spouse_character_ids.empty(),
        "allocated empty vector and capacity above64 do not assert an engine limit");
  }
  {
    Fixture f; f.WithSpouses(); auto out = Observe(f);
    Require(out.relationships_ready && out.relationships->betrothed_character_id == kOtherPeerId &&
        out.relationships->primary_spouse_character_id == kPeerId &&
        out.relationships->spouse_character_ids == std::vector<std::int32_t>({kPeerId, 0}),
        "nonempty full-generation relations preserve negative and zero IDs and order");
    Store(f.peer, 0x1D0, f.peer.data()); out = Observe(f);
    Require(out.relationships_ready && out.relationships->spouse_character_ids.size() == 2,
        "raw vector does not import script alive filters");
    Store(f.family, 0x14, kOtherPeerId); out = Observe(f);
    Require(out.relationships_ready && out.relationships->primary_spouse_character_id == kOtherPeerId,
        "internal raw relation does not invent primary membership restriction");
  }
  {
    Fixture f; f.WithSpouses(); f.spouse_ids.fill(kPeerId);
    Store(f.family, 0x28, std::int32_t{66}); Store(f.family, 0x2C, std::int32_t{64});
    const auto out = Observe(f);
    Require(out.relationships_ready && out.relationships->spouse_character_ids.size() == 64,
        "64 is observation bound; raw entries are not silently deduplicated");
  }
  for (int invalid = 0; invalid < 5; ++invalid) {
    Fixture f; f.WithSpouses();
    if (invalid == 0) Store(f.family, 0x28, std::int32_t{-1});
    if (invalid == 1) Store(f.family, 0x2C, std::int32_t{-1});
    if (invalid == 2) Store(f.family, 0x28, std::int32_t{1});
    if (invalid == 3) Store(f.family, 0x20, static_cast<void *>(nullptr));
    if (invalid == 4) { Store(f.family, 0x28, std::int32_t{66});
      Store(f.family, 0x2C, std::int32_t{65}); }
    FamilyUnavailable(f, invalid == 4 ? "spouse_observation_scope_exceeded" : "family_header_invalid");
  }
  {
    Fixture f; f.WithSpouses(); f.spouse_ids[0] = -1;
    FamilyUnavailable(f, "family_peer_unavailable");
  }
  {
    Fixture f; f.WithSpouses();
    Store(f.family, 0x10, std::bit_cast<std::int32_t>(std::uint32_t{0x83000002}));
    FamilyUnavailable(f, "family_peer_unavailable");
  }
  {
    Fixture f; f.WithSpouses(); Store(f.peer, 0x1C, std::uint32_t{0x4C616E64});
    FamilyUnavailable(f, "family_peer_unavailable");
  }
  for (const auto change : {Mutation::date_first, Mutation::paused_first,
           Mutation::actor_second, Mutation::family_second, Mutation::living_second,
           Mutation::map_second, Mutation::death_second,
           Mutation::actor_generation_second, Mutation::type_second}) {
    Fixture f; f.WithSpouses(); const auto expected = f.Expected(); f.mutation = change;
    WholeUnavailable(f, expected, change == Mutation::actor_second ||
        change == Mutation::family_second || change == Mutation::living_second ||
        change == Mutation::type_second ? "player_identity_changed" : "core_frame_changed");
  }
  for (const auto change : {Mutation::gold_second, Mutation::stress_second,
           Mutation::betrothed_second, Mutation::spouse_second, Mutation::capacity_second,
           Mutation::peer_pointer_second, Mutation::peer_generation_second}) {
    Fixture f; f.WithSpouses(); const auto expected = f.Expected(); f.mutation = change;
    ActorFoundationObservationV1 out{};
    Require(ReadActorFoundationV1(f.bindings, expected, out) && out.same_frame_ready,
        "one changed group preserves the other current observation");
    const bool resource_change = change == Mutation::gold_second || change == Mutation::stress_second;
    Require(resource_change ? (!out.resources_ready && !out.gold_raw && !out.prestige_raw &&
        !out.piety_raw && !out.stress_points && out.relationships_ready && out.relationships &&
        out.resources_unavailable_reason == "resources_changed") :
        (out.resources_ready && !out.relationships_ready && !out.relationships &&
         out.relationships_unavailable_reason == (change == Mutation::peer_generation_second ?
             "family_peer_unavailable" : "relationships_changed")), "groups fail atomically");
  }
  {
    Fixture f; const auto expected = f.Expected(); auto wrong = expected;
    wrong.clock.paused = false; WholeUnavailable(f, wrong, "requires_paused");
    wrong = expected; wrong.map_ready = false; WholeUnavailable(f, wrong, "map_not_ready");
    wrong = expected; wrong.has_played_character = false;
    WholeUnavailable(f, wrong, "player_identity_unavailable");
    wrong = expected; wrong.played_character_id = -1;
    WholeUnavailable(f, wrong, "player_identity_unavailable");
    wrong = expected; wrong.played_character_alive = false;
    WholeUnavailable(f, wrong, "player_not_alive");
    wrong = expected; ++wrong.clock.date_raw; WholeUnavailable(f, wrong, "core_frame_changed");
    wrong = expected; --wrong.clock.speed; WholeUnavailable(f, wrong, "core_frame_changed");
    wrong = expected; ++wrong.local_player_id; WholeUnavailable(f, wrong, "core_frame_changed");
    Store(f.actor, 0x1C, std::uint32_t{0x4C616E64});
    WholeUnavailable(f, expected, "player_identity_unavailable");
  }
  {
    Fixture f; const auto expected = f.Expected(); f.bindings.exact_build_admitted = false;
    WholeUnavailable(f, expected, "unsupported_build");
    f.bindings.exact_build_admitted = true; f.bindings.core.get_local_player = nullptr;
    WholeUnavailable(f, expected, "core_binding_unavailable");
  }
#if defined(_MSC_VER)
  {
    Fixture f; Store(f.actor, 0x1A8, reinterpret_cast<void *>(std::uintptr_t{1}));
    FamilyUnavailable(f, "family_read_failed");
  }
  {
    Fixture f; Store(f.actor, 0x1B0, reinterpret_cast<void *>(std::uintptr_t{1}));
    const auto out = Observe(f);
    Require(!out.resources_ready && !out.gold_raw && !out.prestige_raw && !out.piety_raw &&
        !out.stress_points && out.relationships_ready && out.relationships &&
        out.resources_unavailable_reason == "resource_read_failed", "bad living is not observed zero");
  }
  {
    Fixture f; f.WithSpouses();
    Store(f.family, 0x20, reinterpret_cast<void *>(std::uintptr_t{1}));
    FamilyUnavailable(f, "family_read_failed");
  }
  {
    Fixture f;
    Store(f.actor, 0x1B0, reinterpret_cast<void *>(std::uintptr_t{1}));
    Store(f.actor, 0x1A8, reinterpret_cast<void *>(std::uintptr_t{1}));
    const auto expected = f.Expected(); ActorFoundationObservationV1 out{};
    Require(!ReadActorFoundationV1(f.bindings, expected, out) && out.same_frame_ready &&
        !out.available && !out.resources_ready && !out.relationships_ready &&
        !out.gold_raw && !out.relationships, "two bad groups are unavailable, not zero or empty");
  }
#endif
  Require(!BindActorFoundationImageV1(0, kExecutableSha256).exact_build_admitted,
      "null base rejected");
  Require(!BindActorFoundationImageV1(0x140000000,
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
      .exact_build_admitted, "old identity rejected");
  Require(!BindActorFoundationImageV1((std::numeric_limits<std::uintptr_t>::max)(),
      kExecutableSha256).exact_build_admitted, "base overflow rejected");
  std::cout << "PASS synthetic actor resources/family/full-generation/partial/"
      "bounds/stability guards; no EXE or game code executed\n";
  return 0;
}
