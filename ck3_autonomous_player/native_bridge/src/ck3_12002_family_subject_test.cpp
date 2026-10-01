#include "xar_bridge/ck3_12002_family_subject.hpp"
#include "xar_bridge/ck3_12002_family_subject_abi.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12002;
using Failure = xar::ck3_11906::PlayerChildMarriageSubjectFailureV1;
constexpr std::int32_t player_id = 0x03000001, child_id = 0x03000002,
    peer_id = 0x03000003, employer_id = 0x03000004,
    house_id = 0x05000002, dynasty_id = 0x06000003;
template <typename T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(T));
}
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void *local_player = nullptr;
void *LocalPlayer(void *) { return local_player; }
bool mutate_date = false;
void *state_to_mutate = nullptr;
FamilySubjectIsChildOf native_child_of = nullptr;
int child_reads = 0;
bool ChildRead(void *child, void *parent) {
  ++child_reads;
  if (mutate_date && child_reads == 2) Put(state_to_mutate, 8, std::int32_t{53220024});
  return native_child_of(child, parent);
}
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{}, house_store{}, dynasty_store{};
  std::array<std::byte, 8 * 0x10> slots{}, house_slots{}, dynasty_slots{};
  std::array<std::array<std::byte, 0x1D8>, 4> characters{};
  std::array<std::array<std::byte, 0x58>, 4> families{};
  std::array<std::byte, 0xD0> court{};
  std::array<std::byte, 0x38> house{}, dynasty{}, house_fallback{}, dynasty_fallback{};
  std::array<std::int32_t, 2> child_ids{child_id, peer_id};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *store_ptr = store.data(),
      *house_store_ptr = house_store.data(), *dynasty_store_ptr = dynasty_store.data(),
      *house_fallback_ptr = house_fallback.data(), *dynasty_fallback_ptr = dynasty_fallback.data();
  std::int32_t threshold_zero = 16, threshold_one = 18;
  FamilySubjectBindings bindings{};
  Fixture() {
    Put(state.data(), 8, std::int32_t{53220000}); Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xA0, game.data()); Put(jomini.data(), 0x18, players.data());
    jomini[0x20] = std::byte{1}; Put(players.data(), 0x1F0, std::int32_t{7});
    Put(local.data(), 0x70, std::int32_t{7}); local_player = local.data();
    Put(game.data(), 0x222E8 + 0x58, entries.data());
    Put(game.data(), 0x222E8 + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{7}); Put(entry.data(), 0xB0, player_id);
    const std::array<std::int32_t, 4> ids{player_id, child_id, peer_id, employer_id};
    Put(store.data(), 0x20, slots.data()); Put(store.data(), 0x2C, std::int32_t{8});
    for (std::size_t index = 0; index < ids.size(); ++index) {
      Put(characters[index].data(), 0x18, ids[index]);
      Put(slots.data(), (ids[index] & 0xFFFFFF) * 0x10 + 8, characters[index].data());
      Put(characters[index].data(), 0x1A8, families[index].data());
      Put(characters[index].data(), 0x158, std::int32_t{-1});
      Put(families[index].data(), 0, std::int32_t{-1});
      Put(families[index].data(), 4, std::int32_t{-1});
      Put(families[index].data(), 0x10, std::int32_t{-1});
      Put(families[index].data(), 0x14, std::int32_t{-1});
      Put(characters[index].data(), 0x68, std::int16_t{15});
    }
    Put(families[1].data(), 0, player_id);
    Put(families[2].data(), 4, player_id);
    Put(characters[1].data(), 0x1A1, std::uint8_t{1});
    Put(characters[1].data(), 0x158, house_id);
    Put(house.data(), 0x10, house_id); Put(house.data(), 0x2C, dynasty_id);
    Put(dynasty.data(), 0x10, dynasty_id);
    Put(house_store.data(), 0x20, house_slots.data()); Put(house_store.data(), 0x2C, std::int32_t{8});
    Put(dynasty_store.data(), 0x20, dynasty_slots.data()); Put(dynasty_store.data(), 0x2C, std::int32_t{8});
    Put(house_slots.data(), (house_id & 0xFFFFFF) * 0x10 + 8, house.data());
    Put(dynasty_slots.data(), (dynasty_id & 0xFFFFFF) * 0x10 + 8, dynasty.data());
    Put(characters[1].data(), 0x1B8, court.data()); Put(court.data(), 0xC8, employer_id);
    Put(families[0].data(), 0x38, child_ids.data());
    Put(families[0].data(), 0x40, std::int32_t{2}); Put(families[0].data(), 0x44, std::int32_t{2});
    bindings = BindFamilySubjectImage(0x140000000, kExecutableSha256);
    native_child_of = bindings.is_character_child_of;
    bindings.family.context.core = {true, &state_ptr, &jomini_ptr, &store_ptr, &LocalPlayer};
    bindings.family.adult_threshold_zero = &threshold_zero;
    bindings.family.adult_threshold_one = &threshold_one;
    bindings.house_storage_slot = &house_store_ptr; bindings.house_fallback_slot = &house_fallback_ptr;
    bindings.dynasty_storage_slot = &dynasty_store_ptr; bindings.dynasty_fallback_slot = &dynasty_fallback_ptr;
    bindings.is_character_child_of = &ChildRead;
    state_to_mutate = state.data(); child_reads = 0; mutate_date = false;
  }
  auto Read(std::int32_t id = child_id) { return ReadPlayerChildMarriageSubjectV1(bindings, id); }
};
} // namespace

int main() {
  try {
    const auto bound = BindFamilySubjectImage(0x140000000, kExecutableSha256);
    Check(bound.enabled && bound.is_character_child_of != nullptr &&
        reinterpret_cast<std::uintptr_t>(bound.house_storage_slot) ==
            0x140000000 + kFamilySubjectHouseStorageSlotRva, "exact 1.20 subject binding");
    Check(!BindFamilySubjectImage(0x140000000, "1.19.0.6").enabled, "legacy build is not a subject binding");
    Fixture f;
    auto subject = f.Read();
    Check(subject.failure == Failure::none && subject.unavailable_reason.empty() &&
        subject.played_character_id == player_id && subject.subject_character_id == child_id &&
        subject.subject_is_player_child && subject.adult_readback_available &&
        subject.adult_measure_raw == 15 && subject.adult_selector_raw == 1 &&
        subject.adult_threshold_raw == 18 && !subject.is_adult &&
        subject.lineage.house_id == house_id && subject.lineage.dynasty_id == dynasty_id &&
        subject.employer_character_id == employer_id && subject.relationship.betrothed_character_id == -1,
        "minor actual child keeps concrete age, runtime threshold, lineage, employer and empty relationships");
    const xar::ck3_11906::PlayerChildMarriageSubjectReadV1 *legacy_wire = &subject;
    Check(legacy_wire->subject_character_id == child_id, "formal serializer subject prefix preserved");
    auto second_parent = f.Read(peer_id);
    Check(second_parent.failure == Failure::none && second_parent.subject_is_player_child &&
        second_parent.lineage.house_id == -1 && second_parent.lineage.dynasty_id == -1 &&
        second_parent.employer_character_id == -1, "second parent relation and legitimate empty lineage/employer");
    Put(f.characters[1].data(), 0x68, std::int16_t{18});
    Check(f.Read().is_adult, "signed adult equality uses selected runtime threshold");
    Put(f.characters[1].data(), 0x68, std::int16_t{-1});
    Check(!f.Read().is_adult, "signed negative age never wraps into adulthood");
    Put(f.characters[1].data(), 0x68, std::int16_t{17});
    Put(f.characters[1].data(), 0x1A1, std::uint8_t{0});
    Check(f.Read().is_adult && f.Read().adult_threshold_raw == 16, "selector zero chooses different runtime threshold");
    auto family = ReadPlayerFamilyArrayProbeV1(f.bindings, player_id);
    Check(family.available && family.spouse_readable && family.slots.size() == 2 &&
        family.slots[0].offset == 0x20 && family.slots[1].offset == 0x38 &&
        family.slots[1].count == 2 && family.slots[1].sample_ids ==
            std::vector<std::int32_t>{child_id, peer_id} &&
        family.slots[1].sample_generation_valid == std::vector<bool>{true, true},
        "actual child iterator collection is family+38, independent of guessed legacy probe slots");
    Check(f.Read(employer_id).failure == Failure::not_player_child,
        "non-child same current map cannot borrow child authority");
    Check(f.Read(player_id).failure == Failure::subject_unavailable,
        "current player is not his own child subject");
    Put(f.families[1].data(), 0, std::int32_t{0x07000001});
    Check(f.Read().failure == Failure::not_player_child, "full parent ID, not low-index match");
    Put(f.families[1].data(), 0, player_id);
    Put(f.house.data(), 0x10, std::int32_t{0x07000002});
    Check(f.Read().failure == Failure::lineage_unavailable, "house generation remains actual identity");
    Put(f.house.data(), 0x10, house_id);
    Put(f.court.data(), 0xC8, std::int32_t{0x07000004});
    Check(f.Read().failure == Failure::employer_unavailable, "employer is not an inferred liege or stale slot");
    Put(f.court.data(), 0xC8, employer_id);
    Put(f.characters[1].data(), 0x1D0, f.court.data());
    Check(f.Read().failure == Failure::subject_unavailable, "new 1.20 death field observed");
    Put(f.characters[1].data(), 0x1D0, static_cast<void *>(nullptr));
    Put(f.characters[1].data(), 0x1A1, std::uint8_t{1});
    mutate_date = true; child_reads = 0;
    Check(f.Read().failure == Failure::frame_changed, "changed paused source frame cannot complete subject read");
    std::cout << "PASS CK3 1.20 child subject: native parents, concrete lineage/employer/adult, actual child array, formal prefix\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
