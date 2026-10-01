#include "xar_bridge/ck3_12002_family_obligations_lineage.hpp"

#include <cstring>
#include <iostream>
#include <stdexcept>

namespace {
using namespace xar::ck3_12002;
template <typename T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *base, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(value)); return value;
}
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
constexpr std::int32_t actor_id = 0x01000001, subject_id = 0x01000002,
    candidate_id = 0x01000003, subject_house = 0x01000001, candidate_house = 0x01000002,
    subject_dynasty = 0x01000001, candidate_dynasty = 0x01000002;
std::array<std::byte, 0x200> actor{}, subject{}, candidate{};
bool selected = false, native_legal = true, wrong_parent = false, drift = false;
int contexts = 0, destroys = 0, previews = 0;
bool ReadOption(const void *, std::uint32_t option) { Check(option == 9, "option ID"); return selected; }
void Refresh(void *, bool value) { Check(value, "refresh bool follows existing native pair"); }
void Finalize(void *) {}
void *NativeParent(const void *offer) {
  ++previews;
  Check(Get<std::uintptr_t>(offer, 0) == 0x12002, "exact offer vtable");
  Check(Get<void *>(offer, 8) == nullptr, "detached native cached-option branch");
  Check(Get<std::int32_t>(offer, 0x28) == subject_id &&
        Get<std::int32_t>(offer, 0x2C) == candidate_id, "full secondary IDs");
  Check(Get<bool>(offer, 0x80) == selected, "actual native selected option");
  if (wrong_parent) return actor.data();
  return selected == Get<bool>(subject.data(), family_value::kCharacterSexSelectorOffset)
      ? subject.data() : candidate.data();
}
struct Components {
  std::array<std::byte, 0x30> house_store{}, dynasty_store{};
  std::array<std::byte, 0x30> house_slots{}, dynasty_slots{};
  std::array<std::byte, 0x40> house_a{}, house_b{}, dynasty_a{}, dynasty_b{};
  void *houses = house_store.data(), *dynasties = dynasty_store.data();
  void *house_fallback = nullptr, *dynasty_fallback = nullptr;
  Components() {
    Put(house_store.data(), 0x20, house_slots.data()); Put(house_store.data(), 0x2C, std::int32_t{3});
    Put(dynasty_store.data(), 0x20, dynasty_slots.data()); Put(dynasty_store.data(), 0x2C, std::int32_t{3});
    Put(house_slots.data(), 0x18, house_a.data()); Put(house_slots.data(), 0x28, house_b.data());
    Put(dynasty_slots.data(), 0x18, dynasty_a.data()); Put(dynasty_slots.data(), 0x28, dynasty_b.data());
    Put(house_a.data(), 0x10, subject_house); Put(house_b.data(), 0x10, candidate_house);
    Put(house_a.data(), 0x2C, subject_dynasty); Put(house_b.data(), 0x2C, candidate_dynasty);
    Put(dynasty_a.data(), 0x10, subject_dynasty); Put(dynasty_b.data(), 0x10, candidate_dynasty);
  }
};
} // namespace

namespace xar::ck3_12002 {
CoreBindings BindCoreImage(std::uintptr_t, std::string_view) noexcept { return {}; }
FamilyBindings BindFamilyImage(std::uintptr_t, std::string_view) noexcept { return {}; }
FamilyProjectionBindings BindFamilyProjectionImage(std::uintptr_t, std::string_view) noexcept { return {}; }
bool ReadCoreSnapshot(const CoreBindings &, CoreSnapshotPrefix &out) noexcept {
  out = {}; out.clock.paused = true; out.clock.date_raw = drift && previews ? 53220001 : 53220000;
  out.map_ready = true; out.has_played_character = true; out.played_character_alive = true;
  out.played_character_id = actor_id; return true;
}
void *ResolveCoreCharacter(const CoreBindings &, std::int32_t id) noexcept {
  return id == actor_id ? actor.data() : id == subject_id ? subject.data() :
      id == candidate_id ? candidate.data() : nullptr;
}
bool PrepareFamilyPairContextV1(const FamilyBindings &, std::int32_t actor_value,
    std::int32_t subject_value, std::int32_t candidate_value, FamilyPairContextV1 &out) noexcept {
  if (actor_value != actor_id || subject_value != subject_id || candidate_value != candidate_id) return false;
  out.initialized = true; ++contexts; return true;
}
void DestroyFamilyPairContextV1(const FamilyBindings &, FamilyPairContextV1 &out) noexcept {
  if (out.initialized) ++destroys;
  out = {};
}
bool ReadFamilyPairTermsV1(const FamilyBindings &, std::int32_t, std::int32_t,
    const FamilyPairContextV1 &, FamilyPairTermsV1 &out) noexcept {
  out = {}; out.complete_can_send = native_legal;
  // Deliberately differs from selected UI option to catch aliasing the two.
  out.effective_matrilineal_if_accepted = !selected; return true;
}
bool SelectFamilyMatrilinealOptionV1(const FamilyProjectionBindings &, void *) noexcept {
  selected = true; return true;
}
} // namespace xar::ck3_12002

int main() {
  using namespace xar::ck3_12002::family_obligations_lineage;
  try {
    Components components{};
    Put(subject.data(), family_value::kCharacterHouseOffset, subject_house);
    Put(candidate.data(), family_value::kCharacterHouseOffset, candidate_house);
    std::uint32_t option_id = 9;
    Bindings b{}; b.enabled = true; b.family.enabled = true; b.family.context.core.enabled = true;
    b.family.values.enabled = true; b.family.values.core.enabled = true;
    b.family.values.house_store = &components.houses; b.family.values.house_fallback = &components.house_fallback;
    b.family.values.dynasty_store = &components.dynasties; b.family.values.dynasty_fallback = &components.dynasty_fallback;
    b.family.read_boolean_option = ReadOption; b.family.matrilineal_option = &option_id;
    b.family.context.refresh = Refresh; b.family.context.finalize = Finalize;
    b.native_preview_parent = NativeParent; b.native_offer_vtable = 0x12002;
    Snapshot out{}; std::string_view reason{};
    for (int selector = 0; selector < 2; ++selector) {
      Put(subject.data(), family_value::kCharacterSexSelectorOffset, static_cast<std::uint8_t>(selector));
      for (int option = 0; option < 2; ++option) {
        selected = option != 0;
        Check(Read(b, subject_id, candidate_id, false, out, &reason), "native preview reads concrete pair");
        bool first = selected == (selector != 0);
        Check(out.native_selected_parent_character_id == (first ? subject_id : candidate_id), "native parent choice");
        Check(out.native_preview_lineage.house_id == (first ? subject_house : candidate_house) &&
              out.native_preview_lineage.dynasty_id == (first ? subject_dynasty : candidate_dynasty), "full parent lineage");
        Check(out.selected_matrilineal_option == selected &&
              out.effective_matrilineal_if_accepted == !selected, "selected and effective option distinct");
      }
    }
    selected = false; Put(subject.data(), family_value::kCharacterSexSelectorOffset, std::uint8_t{1});
    Check(Read(b, subject_id, candidate_id, true, out, &reason) && selected &&
          out.requested_matrilineal_option && out.native_selected_parent_character_id == subject_id,
          "requested option consumed by actual native parent getter");
    native_legal = false;
    Check(Read(b, subject_id, candidate_id, false, out, &reason) && !out.complete_can_send,
          "negative native legality remains observable");
    Put(subject.data(), family_value::kCharacterHouseOffset, std::int32_t{-1});
    Check(Read(b, subject_id, candidate_id, false, out, &reason) &&
          out.native_preview_lineage.house_id == -1 && out.native_preview_lineage.dynasty_id == -1,
          "native no house is legitimate absence");
    Put(subject.data(), family_value::kCharacterHouseOffset, subject_house);
    Put(components.house_a.data(), 0x10, std::int32_t{0x02000001});
    Check(!Read(b, subject_id, candidate_id, false, out, &reason) && !out.available,
          "actual stale house generation cannot be projected as lineage");
    Put(components.house_a.data(), 0x10, subject_house); wrong_parent = true;
    Check(!Read(b, subject_id, candidate_id, false, out, &reason), "native returned parent belongs to pair");
    wrong_parent = false; drift = true; previews = 0;
    Check(!Read(b, subject_id, candidate_id, false, out, &reason), "paused date changed");
    Check(contexts == destroys, "every actual borrowed context destroyed");
    std::cout << "PASS native child-house preview, full lineage, selected option, negative legality and context ownership\n";
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
