#include "xar_bridge/ck3_12002_claim_terms.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_12002;
using Result = xar::game::ReadWarTerminationTermsResult;

template <typename T>
void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T>
T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

std::array<std::byte, 0x80> player{};
std::array<void *, 1> claim_vtable{};
std::int32_t destruction_count = 0;
std::int32_t getter_count = 0;
std::int32_t invalid_flag_title = -1;
bool wrong_return = false;
bool invalid_present = false;
void *war_to_mutate = nullptr;

void *LocalPlayer(void *) { return player.data(); }
bool Contains(const void *side, std::int32_t id) {
  return Get<std::int32_t>(side, 0) == id;
}
void *DestroyClaim(void *claim, std::int32_t delete_flags) {
  assert(delete_flags == 0);
  assert(Get<std::uint8_t>(claim, kClaimTermsPresentOffset) == 1);
  ++destruction_count;
  return claim;
}
void *ReadClaim(void *output, void *, void *title) {
  ++getter_count;
  const auto id = Get<std::int32_t>(title, 0x10);
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  // This fake writes the complete NEW optional layout. The +0x0C marker is
  // deliberately non-boolean so the former 1.19 strong/implicit offsets fail.
  Put(output, 0, claim_vtable.data());
  Put(output, 8, id);
  Put(output, 0x0C, std::uint32_t{0x436C6169});
  const auto present = static_cast<std::uint8_t>(index != 1);
  Put(output, 0x18, invalid_present ? std::uint8_t{2} : present);
  Put(output, 0x10, index == 1 ? std::uint8_t{0xFF}
                             : static_cast<std::uint8_t>(index <= 3));
  Put(output, 0x11, static_cast<std::uint8_t>(index == 3 || index == 5));
  if (id == invalid_flag_title) {
    Put(output, 0x10, std::uint8_t{2});
  }
  if (war_to_mutate != nullptr) {
    Put(war_to_mutate, 8, std::int32_t{0x06000001});
  }
  return wrong_return ? nullptr : output;
}

struct Fixture {
  std::array<std::byte, 0xB0> state{};
  std::array<std::byte, 0x40> jomini{};
  std::array<std::byte, 0x200> players{};
  std::vector<std::byte> data = std::vector<std::byte>(0x30000);
  std::array<std::byte, 0x100> record{};
  std::array<void *, 1> records{};
  std::array<std::byte, 0x40> character_storage{};
  std::array<std::byte, 0x30> character_slots{};
  std::array<std::byte, 0x200> played{};
  std::array<std::byte, 0x200> claimant{};
  std::array<std::byte, 0x40> war_storage{};
  std::array<std::byte, 0x20> war_slots{};
  std::array<std::byte, 0x400> war{};
  std::array<std::byte, 0x100> cb{};
  std::array<std::byte, 0x40> title_storage{};
  std::array<std::byte, 0x60> title_slots{};
  std::array<std::array<std::byte, 0x100>, 5> titles{};
  std::array<std::int32_t, 5> title_ids{};
  void *state_pointer = state.data();
  void *jomini_pointer = jomini.data();
  void *character_storage_pointer = character_storage.data();
  void *title_storage_pointer = title_storage.data();
  ClaimTermsBindings bindings;
  static constexpr std::int32_t war_id = 0x05000001;
  static constexpr std::int32_t player_id = 0x04000001;
  static constexpr std::int32_t claimant_id = 0x04000002;

  Fixture() {
    destruction_count = getter_count = 0;
    invalid_flag_title = -1;
    wrong_return = invalid_present = false;
    war_to_mutate = nullptr;
    claim_vtable[0] = reinterpret_cast<void *>(&DestroyClaim);
    Put(player.data(), 0x70, std::int32_t{1});
    Put(state.data(), 8, std::int32_t{1234});
    Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xA0, data.data());
    Put(jomini.data(), 0x18, players.data());
    Put(jomini.data(), 0x20, std::uint8_t{1});
    Put(players.data(), 0x1F0, std::int32_t{0});
    records[0] = record.data();
    Put(data.data(), kPlayerCharacterManagerOffset + 0x58, records.data());
    Put(data.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(record.data(), 0xD8, std::int32_t{0});
    Put(record.data(), 0xB0, player_id);
    Put(character_storage.data(), 0x20, character_slots.data());
    Put(character_storage.data(), 0x2C, std::int32_t{3});
    Put(character_slots.data(), 0x18, played.data());
    Put(character_slots.data(), 0x28, claimant.data());
    Put(played.data(), 0x18, player_id);
    Put(claimant.data(), 0x18, claimant_id);
    Put(data.data(), kWorldWarManagerOffset + 0x20, war_storage.data());
    Put(war_storage.data(), 0x20, war_slots.data());
    Put(war_storage.data(), 0x2C, std::int32_t{2});
    Put(war_slots.data(), 0x18, war.data());
    Put(war.data(), 8, war_id);
    Put(war.data(), 0x20, player_id);
    Put(war.data(), 0x80, std::int32_t{0x04000003});
    Put(war.data(), kWorldWarCasusBelliOffset, cb.data());
    Put(war.data(), kWorldWarClaimantOffset, claimant_id);
    Put(cb.data(), 0x10, std::int32_t{42});
    std::memcpy(cb.data() + 0x18, "claim_cb", 8);
    Put(cb.data(), 0x28, std::size_t{8});
    Put(cb.data(), 0x30, std::size_t{15});
    Put(title_storage.data(), 0x20, title_slots.data());
    Put(title_storage.data(), 0x2C, std::int32_t{6});
    for (std::size_t index = 0; index < titles.size(); ++index) {
      title_ids[index] = static_cast<std::int32_t>(0x07000001 + index);
      Put(titles[index].data(), 0x10, title_ids[index]);
      Put(title_slots.data(), (index + 1) * 0x10 + 8, titles[index].data());
    }
    Put(war.data(), 0x270, title_ids.data());
    Put(war.data(), 0x278, std::int32_t{5});
    Put(war.data(), 0x27C, std::int32_t{5});
    bindings.enabled = true;
    bindings.core = {true, &state_pointer, &jomini_pointer,
                     &character_storage_pointer, &LocalPlayer};
    bindings.world.enabled = true;
    bindings.world.game_state_slot = &state_pointer;
    bindings.world.contains_war_participant = &Contains;
    bindings.provinces.enabled = true;
    bindings.provinces.game_state_slot = &state_pointer;
    bindings.provinces.landed_title_storage_slot = &title_storage_pointer;
    bindings.read_character_claim = &ReadClaim;
    bindings.character_claim_vtable =
        reinterpret_cast<std::uintptr_t>(claim_vtable.data());
  }
};
} // namespace

int main() {
  using namespace xar::ck3_12002;
  xar::game::WarTerminationTermsSnapshot output;
  {
    Fixture f;
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::available);
    assert(output.target_title_ids == std::vector<std::int32_t>(f.title_ids.begin(), f.title_ids.end()));
    assert(output.claims.size() == 5 && getter_count == 5 && destruction_count == 4);
    const std::array<const char *, 5> expected{
        "absent", "strong_explicit", "strong_implicit", "weak_explicit", "weak_implicit"};
    for (std::size_t index = 0; index < expected.size(); ++index) {
      assert(output.claims[index].state == expected[index]);
    }
    assert(output.attacker_defeat.claim_disposition == "remove_declared_target_claims");
    assert(output.white_peace.claim_disposition == "retain_and_strengthen_weak");
  }
  {
    Fixture f;
    Put(f.jomini.data(), 0x20, std::uint8_t{0});
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::requires_paused);
    assert(output.war_id == -1 && getter_count == 0);
  }
  {
    Fixture f;
    Put(f.played.data(), kCharacterDeathDataOffset, f.played.data());
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::no_played_character);
  }
  {
    Fixture f;
    assert(ReadWarTerminationTerms(f.bindings, 0x06000001, output) == Result::war_not_found);
    Put(f.war.data(), 0x20, std::int32_t{0x04000008});
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::player_not_participant);
  }
  {
    Fixture f;
    std::memcpy(f.cb.data() + 0x18, "other_cb", 8);
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::unsupported_casus_belli);
    assert(output.active_casus_belli_key == "other_cb" && output.claims.empty());
  }
  {
    Fixture f;
    Put(f.claimant.data(), 0x18, std::int32_t{0x09000002});
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::unavailable);
    assert(output.war_id == -1 && getter_count == 0);
  }
  {
    Fixture f;
    Put(f.titles[0].data(), 0x10, std::int32_t{0x09000001});
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::unavailable);
    assert(output.war_id == -1 && getter_count == 0);
  }
  {
    Fixture f;
    invalid_flag_title = f.title_ids[1];
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::unavailable);
    assert(output.claims.empty() && destruction_count == 1);
  }
  {
    Fixture f;
    wrong_return = true;
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::unavailable);
  }
  {
    Fixture f;
    invalid_present = true;
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::unavailable);
  }
  {
    Fixture f;
    war_to_mutate = f.war.data();
    assert(ReadWarTerminationTerms(f.bindings, f.war_id, output) == Result::unavailable);
    assert(output.war_id == -1 && output.claims.empty());
  }
  {
    constexpr std::uintptr_t base = 0x140000000;
    const auto binding = BindClaimTermsImage(base, kExecutableSha256);
    assert(binding.enabled);
    assert(binding.character_claim_vtable == base + kClaimTermsClaimVtableRva);
    assert(reinterpret_cast<std::uintptr_t>(binding.read_character_claim) == base + kClaimTermsGetterRva);
    assert(!BindClaimTermsImage(base, "old-build").enabled);
  }
  std::cout << "CK3 1.20.0.2 claim terms fixture passed\n";
}
