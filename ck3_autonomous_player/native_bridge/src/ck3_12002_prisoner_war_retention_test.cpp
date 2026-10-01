#include "xar_bridge/ck3_12002_prisoner_war_retention.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_12002;
using Result = xar::ck3_11906::ReadWarPrisonerReleasePairsResultV1;
using Observation = xar::ck3_11906::WarPrisonerReleasePairsObservationV1;
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
std::array<std::byte, 0x80> player{};
void *date_to_mutate = nullptr;
void *successor_to_mutate = nullptr;
int local_calls = 0;
int primary_calls = 0;
void *LocalPlayer(void *) {
  ++local_calls;
  return player.data();
}
void *PrimaryTitle(void *character) {
  ++primary_calls;
  if (primary_calls == 5 && date_to_mutate != nullptr)
    Put(date_to_mutate, 8, std::int32_t{1235});
  if (primary_calls == 5 && successor_to_mutate != nullptr)
    Put(successor_to_mutate, 0x15C, std::int32_t{0});
  return Get<void *>(character, 0x40);
}
void *ImprisonedBy(void *character) {
  void *extension = Get<void *>(character, kWarRetentionCharacterExtensionOffset);
  void *relation = extension == nullptr ? nullptr :
      Get<void *>(extension, kWarRetentionCustodyRelationOffset);
  return relation == nullptr ? nullptr : Get<void *>(relation, 8);
}

struct Fixture {
  static constexpr std::int32_t war_id = 0x05000001;
  static constexpr std::int32_t attacker_id = 0x04000001;
  static constexpr std::int32_t defender_id = 0x04000002;
  std::array<std::byte, 0xB0> state{};
  std::array<std::byte, 0x40> jomini{};
  std::array<std::byte, 0x200> players{};
  std::vector<std::byte> data = std::vector<std::byte>(0x30000);
  std::array<std::byte, 0x100> record{};
  std::array<void *, 1> records{record.data()};
  std::array<std::byte, 0x40> characters_store{}, wars_store{}, titles_store{};
  std::array<std::byte, 0xA0> characters_slots{};
  std::array<std::byte, 0x20> wars_slots{};
  std::array<std::byte, 0x30> titles_slots{};
  std::array<std::array<std::byte, 0x200>, 9> characters{};
  std::array<std::array<std::byte, 0x300>, 9> extensions{};
  std::array<std::array<std::byte, 0x10>, 9> relations{};
  std::array<std::byte, 0x400> war{};
  std::array<std::byte, 0x100> cb{};
  std::array<std::array<std::byte, 0x200>, 2> titles{};
  std::array<std::byte, 0x10> attacking_participant{}, defending_participant{};
  std::array<void *, 1> attackers{attacking_participant.data()};
  std::array<void *, 1> defenders{defending_participant.data()};
  std::array<std::int32_t, 4> attacker_successors{
      0x04000003, 0x04000004, 0x04000005, 0x04000009};
  std::array<std::int32_t, 3> defender_successors{
      0x04000006, 0x04000007, 0x04000008};
  void *state_pointer = state.data();
  void *jomini_pointer = jomini.data();
  void *characters_pointer = characters_store.data();
  void *titles_pointer = titles_store.data();
  PrisonerWarRetentionBindings bindings{};

  Fixture() {
    local_calls = primary_calls = 0;
    date_to_mutate = successor_to_mutate = nullptr;
    Put(player.data(), 0x70, std::int32_t{1});
    Put(state.data(), 8, std::int32_t{1234});
    Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xA0, data.data());
    Put(jomini.data(), 0x18, players.data());
    Put(jomini.data(), 0x20, std::uint8_t{1});
    Put(players.data(), 0x1F0, std::int32_t{0});
    Put(data.data(), kPlayerCharacterManagerOffset + 0x58, records.data());
    Put(data.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(record.data(), 0xD8, std::int32_t{0});
    Put(record.data(), 0xB0, attacker_id);
    Put(characters_store.data(), 0x20, characters_slots.data());
    Put(characters_store.data(), 0x2C, std::int32_t{10});
    for (std::size_t i = 0; i < characters.size(); ++i) {
      Put(characters_slots.data(), (i + 1) * 0x10 + 8, characters[i].data());
      Put(characters[i].data(), 0x18, static_cast<std::int32_t>(attacker_id + i));
      Put(characters[i].data(), kWarRetentionCharacterExtensionOffset, extensions[i].data());
    }
    Put(data.data(), kWorldWarManagerOffset + 0x20, wars_store.data());
    Put(wars_store.data(), 0x20, wars_slots.data());
    Put(wars_store.data(), 0x2C, std::int32_t{2});
    Put(wars_slots.data(), 0x18, war.data());
    Put(war.data(), 8, war_id);
    Put(war.data(), kWorldWarCasusBelliOffset, cb.data());
    Put(war.data(), kWorldWarPrimaryAttackerOffset, attacker_id);
    Put(war.data(), kWorldWarPrimaryDefenderOffset, defender_id);
    Put(cb.data(), 0x10, std::int32_t{42});
    std::memcpy(cb.data() + 0x18, "claim_cb", 8);
    Put(cb.data(), 0x28, std::size_t{8});
    Put(cb.data(), 0x30, std::size_t{15});
    Put(attacking_participant.data(), 8, attacker_id);
    Put(defending_participant.data(), 8, defender_id);
    Put(war.data(), kWorldWarAttackersOffset + 8, attackers.data());
    Put(war.data(), kWorldWarAttackersOffset + 0x10, std::int32_t{1});
    Put(war.data(), kWorldWarAttackersOffset + 0x14, std::int32_t{1});
    Put(war.data(), kWorldWarDefendersOffset + 8, defenders.data());
    Put(war.data(), kWorldWarDefendersOffset + 0x10, std::int32_t{1});
    Put(war.data(), kWorldWarDefendersOffset + 0x14, std::int32_t{1});
    Put(titles_store.data(), 0x20, titles_slots.data());
    Put(titles_store.data(), 0x2C, std::int32_t{3});
    for (std::size_t i = 0; i < titles.size(); ++i) {
      Put(titles_slots.data(), (i + 1) * 0x10 + 8, titles[i].data());
      Put(titles[i].data(), 0x10, static_cast<std::int32_t>(0x07000001 + i));
      Put(characters[i].data(), 0x40, titles[i].data());
    }
    Put(titles[0].data(), 0x150, attacker_successors.data());
    Put(titles[0].data(), 0x158, std::int32_t{4});
    Put(titles[0].data(), 0x15C, std::int32_t{4});
    Put(titles[1].data(), 0x150, defender_successors.data());
    Put(titles[1].data(), 0x158, std::int32_t{3});
    Put(titles[1].data(), 0x15C, std::int32_t{3});
    bindings.enabled = true;
    bindings.core = {true, &state_pointer, &jomini_pointer, &characters_pointer, &LocalPlayer};
    bindings.world.enabled = true;
    bindings.world.game_state_slot = &state_pointer;
    bindings.titles.enabled = true;
    bindings.titles.landed_title_storage_slot = &titles_pointer;
    bindings.primary_title = &PrimaryTitle;
    bindings.imprisoned_by = &ImprisonedBy;
  }
  void Imprison(std::size_t prisoner_index, std::size_t jailer_index) {
    Put(extensions[prisoner_index].data(), 0x288, relations[prisoner_index].data());
    Put(relations[prisoner_index].data(), 0,
        static_cast<std::int32_t>(attacker_id + jailer_index));
    Put(relations[prisoner_index].data(), 8, characters[jailer_index].data());
  }
};
bool Check(bool ok, const char *name) {
  if (!ok) std::cerr << "FAIL: " << name << '\n';
  return ok;
}
} // namespace

int main() {
  int passed = 0;
  auto run = [&](bool ok, const char *name) { if (Check(ok, name)) ++passed; };
  {
    const auto b = BindPrisonerWarRetentionImage(0x140000000ULL, kExecutableSha256);
    run(b.enabled && reinterpret_cast<std::uintptr_t>(b.imprisoned_by) ==
        0x140000000ULL + kWarRetentionImprisonedByRva &&
        !BindPrisonerWarRetentionImage(1, "old-build").enabled, "exact binding");
  }
  {
    Fixture f; f.Imprison(0, 1); f.Imprison(2, 1); f.Imprison(6, 0); f.Imprison(8, 1);
    Observation o;
    const auto r = ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o);
    run(r == Result::available && o.full_participant_scan &&
        o.primary_and_first_three_successors_scanned && o.same_frame_stable &&
        o.release_pairs.size() == 3 && o.release_pairs[0].prisoner_character_id ==
        Fixture::attacker_id && o.attacker_release_candidate_ids.size() == 4 &&
        o.attacker_release_candidate_ids.back() == 0x04000005,
        "actual graph both sides, primary and three heirs, fourth excluded");
  }
  {
    Fixture f; Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::available &&
        o.release_pairs.empty() && o.same_frame_stable, "complete empty is observable");
  }
  {
    Fixture f; f.Imprison(2, 8); Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::available &&
        o.release_pairs.empty(), "unrelated jailer does not match participant");
  }
  {
    Fixture f; f.Imprison(2, 1); Put(f.relations[2].data(), 0, std::int32_t{0x06000002});
    Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::unavailable &&
        !o.full_participant_scan && o.war_id == -1, "unresolved custody is unavailable");
  }
  {
    Fixture f; Put(f.defending_participant.data(), 8, std::int32_t{0x06000002}); Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::unavailable &&
        o.release_pairs.empty() && !o.same_frame_stable, "incomplete participants not empty proof");
  }
  {
    Fixture f; f.attacker_successors[1] = f.attacker_successors[0]; Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::unavailable,
        "duplicate successor graph unavailable");
  }
  {
    Fixture f; Put(f.record.data(), 0xB0, std::int32_t{0x04000009}); Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::player_not_participant,
        "nonparticipant player");
  }
  {
    Fixture f; Put(f.jomini.data(), 0x20, std::uint8_t{0}); Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::requires_paused,
        "paused requirement");
  }
  {
    Fixture f; Put(f.characters[0].data(), 0x1D0, f.characters[0].data()); Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::no_played_character,
        "dead played character");
  }
  {
    Fixture f; Put(f.war.data(), kWorldWarEndedOffset, std::uint8_t{1}); Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::war_not_found,
        "ended war");
  }
  {
    Fixture f; date_to_mutate = f.state.data(); Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::unavailable,
        "date drift");
  }
  {
    Fixture f; successor_to_mutate = f.titles[0].data(); Observation o;
    run(ReadWarPrisonerReleasePairsV1(f.bindings, f.war_id, o) == Result::unavailable,
        "actual source graph drift");
  }
  std::cout << "prisoner war-retention production reader fixtures " << passed << "/13\n";
  return passed == 13 ? 0 : 1;
}
