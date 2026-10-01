#include "xar_bridge/ck3_12002_family_value.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstring>
#include <iostream>

using namespace xar::ck3_12002;
namespace fv = xar::ck3_12002::family_value;

template <typename T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  assert(offset + sizeof(value) <= N);
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

namespace {
bool gate_allows = true;
int gate_calls = 0;
void *last_gate_character = nullptr;
bool Gate(void *character) {
  ++gate_calls;
  last_gate_character = character;
  return gate_allows;
}
struct Fixture {
  std::array<std::byte, 0x220> character{};
  std::array<std::byte, 0x220> employer{};
  std::array<std::byte, 0x400> extension{};
  std::array<std::byte, 0xD0> court{};
  std::array<std::byte, 0x40> house{};
  std::array<std::byte, 0x20> dynasty{};
  std::array<std::byte, 0x30> character_store{}, house_store{}, dynasty_store{};
  std::array<std::byte, 0x40> character_slots{}, house_slots{}, dynasty_slots{};
  void *character_store_pointer = character_store.data();
  void *house_store_pointer = house_store.data();
  void *dynasty_store_pointer = dynasty_store.data();
  void *house_fallback = nullptr;
  void *dynasty_fallback = nullptr;
  fv::Bindings bindings{};
  static constexpr std::int32_t character_id = 0x01000001;
  static constexpr std::int32_t employer_id = 0x02000002;
  static constexpr std::int32_t house_id = 0x03000001;
  static constexpr std::int32_t dynasty_id = 0x04000001;

  Fixture() {
    for (auto *store : {&character_store, &house_store, &dynasty_store})
      Put(*store, 0x2C, std::int32_t{4});
    Put(character_store, 0x20, static_cast<void *>(character_slots.data()));
    Put(house_store, 0x20, static_cast<void *>(house_slots.data()));
    Put(dynasty_store, 0x20, static_cast<void *>(dynasty_slots.data()));
    Put(character_slots, 0x18, static_cast<void *>(character.data()));
    Put(character_slots, 0x28, static_cast<void *>(employer.data()));
    Put(house_slots, 0x18, static_cast<void *>(house.data()));
    Put(dynasty_slots, 0x18, static_cast<void *>(dynasty.data()));
    Put(character, 0x18, character_id);
    Put(employer, 0x18, employer_id);
    Put(house, 0x10, house_id);
    Put(dynasty, 0x10, dynasty_id);
    Put(character, fv::kCharacterAgeOffset, std::int16_t{23});
    Put(character, fv::kCharacterSexSelectorOffset, std::uint8_t{1});
    Put(character, fv::kCharacterHouseOffset, house_id);
    Put(house, fv::kHouseDynastyOffset, dynasty_id);
    Put(character, fv::kCharacterCourtRelationOffset, static_cast<void *>(court.data()));
    Put(court, fv::kCourtRelationEmployerOffset, employer_id);
    Put(character, fv::kFertilityExtensionOffset, static_cast<void *>(extension.data()));
    Put(extension, fv::kFertilityRawOffset, std::int64_t{54321});
    bindings.enabled = true;
    bindings.core.enabled = true;
    bindings.core.character_storage_slot = &character_store_pointer;
    bindings.house_store = &house_store_pointer;
    bindings.house_fallback = &house_fallback;
    bindings.dynasty_store = &dynasty_store_pointer;
    bindings.dynasty_fallback = &dynasty_fallback;
    bindings.fertility_gate = &Gate;
  }
};
} // namespace

int main() {
  Fixture f;
  fv::CharacterValue value{};
  std::string_view reason;
  gate_calls = 0;
  assert(fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, true, &reason));
  assert(reason.empty() && value.character_id == Fixture::character_id);
  assert(value.age_raw == 23 && value.sex_selector_raw == 1);
  assert(value.lineage.house_id == Fixture::house_id && value.lineage.dynasty_id == Fixture::dynasty_id);
  assert(value.employer_character_id == Fixture::employer_id);
  assert(value.fertility.available && value.fertility.extension_present);
  assert(value.fertility.native_gate_evaluated && value.fertility.native_gate_allows);
  assert(value.fertility.effective_raw == 54321 && gate_calls == 1);
  assert(last_gate_character == f.character.data());

  gate_allows = false;
  assert(fv::ReadCharacterValue(f.bindings, Fixture::character_id, value));
  assert(value.fertility.native_gate_evaluated && !value.fertility.native_gate_allows);
  assert(value.fertility.effective_raw == 0);
  Put(f.extension, fv::kFertilityRawOffset, std::int64_t{0});
  gate_allows = true;
  assert(fv::ReadCharacterValue(f.bindings, Fixture::character_id, value));
  assert(value.fertility.available && value.fertility.native_gate_allows && value.fertility.effective_raw == 0);

  Put(f.character, fv::kFertilityExtensionOffset, static_cast<void *>(nullptr));
  const auto calls = gate_calls;
  assert(fv::ReadCharacterValue(f.bindings, Fixture::character_id, value));
  assert(value.fertility.available && !value.fertility.extension_present);
  assert(!value.fertility.native_gate_evaluated && gate_calls == calls);
  f.bindings.fertility_gate = nullptr;
  assert(!fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, true, &reason));
  assert(reason == "native_fertility_gate_unavailable" && value == fv::CharacterValue{});
  assert(fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, false));
  assert(!value.fertility.available && value.lineage.house_id == Fixture::house_id);

  Put(f.character, fv::kCharacterHouseOffset, std::int32_t{-1});
  Put(f.character, fv::kCharacterCourtRelationOffset, static_cast<void *>(nullptr));
  assert(fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, false));
  assert(value.lineage == fv::Lineage{} && value.employer_character_id == -1);
  Put(f.character, fv::kCharacterHouseOffset, Fixture::house_id);
  Put(f.house, fv::kHouseDynastyOffset, std::int32_t{-1});
  assert(fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, false));
  assert(value.lineage.house_id == Fixture::house_id && value.lineage.dynasty_id == -1);
  Put(f.house, 0x10, std::int32_t{0x05000001});
  assert(!fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, false, &reason));
  assert(reason == "house_full_id_unavailable" && value == fv::CharacterValue{});
  Put(f.house, 0x10, Fixture::house_id);
  f.house_fallback = f.house.data();
  assert(!fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, false, &reason));
  assert(reason == "house_full_id_unavailable");
  f.house_fallback = nullptr;
  Put(f.house, fv::kHouseDynastyOffset, Fixture::dynasty_id);
  Put(f.dynasty, 0x10, std::int32_t{0x05000001});
  assert(!fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, false, &reason));
  assert(reason == "dynasty_full_id_unavailable");
  Put(f.dynasty, 0x10, Fixture::dynasty_id);
  // Full ID zero is a legitimate stored component; -1 alone means absent.
  Put(f.house_slots, 8, static_cast<void *>(f.house.data()));
  Put(f.dynasty_slots, 8, static_cast<void *>(f.dynasty.data()));
  Put(f.character, fv::kCharacterHouseOffset, std::int32_t{0});
  Put(f.house, 0x10, std::int32_t{0});
  Put(f.house, fv::kHouseDynastyOffset, std::int32_t{0});
  Put(f.dynasty, 0x10, std::int32_t{0});
  assert(fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, false));
  assert(value.lineage.house_id == 0 && value.lineage.dynasty_id == 0);
  Put(f.character, fv::kCharacterSexSelectorOffset, std::uint8_t{2});
  assert(!fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, false, &reason));
  assert(reason == "character_sex_selector_unavailable");
  Put(f.character, fv::kCharacterSexSelectorOffset, std::uint8_t{0});
  Put(f.character, kCharacterDeathDataOffset, static_cast<void *>(f.court.data()));
  assert(!fv::ReadCharacterValue(f.bindings, Fixture::character_id, value, false, &reason));
  assert(reason == "character_full_id_or_liveness_unavailable");

  const auto bound = fv::BindImage(0x140000000ULL, kExecutableSha256);
  assert(bound.enabled && bound.core.enabled);
  assert(reinterpret_cast<std::uintptr_t>(bound.house_store) == 0x140000000ULL + fv::kHouseStoreSlotRva);
  assert(reinterpret_cast<std::uintptr_t>(bound.fertility_gate) == 0x140000000ULL + fv::kFertilityGateRva);
  assert(!fv::BindImage(0, kExecutableSha256).enabled);
  assert(!fv::BindImage(0x140000000ULL, "old-build").enabled);
  std::cout << "PASS family value: exact IDs, lineage, employer, native fertility gate and lawful zero/absence\n";
}
