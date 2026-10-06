#pragma once

// Synthetic memory only. Reuses the reviewed existing-contact field layout;
// no native entry point, process, EXE or game session is involved.
#include "xar_bridge/ck3_12002_routes.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace xar::arrival_first_fixture {

template <std::size_t Size> using Bytes = std::array<std::byte, Size>;

template <std::size_t Size, class Value>
void Put(Bytes<Size> &object, std::size_t offset, const Value &value) {
  if (offset + sizeof(value) > Size)
    throw std::runtime_error("fixture field exceeds its owned object");
  std::memcpy(object.data() + offset, &value, sizeof(value));
}

template <class Value> Value At(const void *object, std::size_t offset) {
  Value value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

struct Storage {
  Bytes<0x30> object{};
  std::array<Bytes<0x10>, 8> slots{};
  void *root = object.data();

  Storage() {
    Put(object, 0x20, slots.data());
    Put(object, 0x2C, std::int32_t{8});
  }

  template <std::size_t Size>
  void Add(std::int32_t id, Bytes<Size> &value, std::size_t id_offset) {
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    if (index >= slots.size()) throw std::runtime_error("fixture slot overflow");
    Put(value, id_offset, id);
    Put(slots[index], 8, value.data());
  }
};

inline bool g_join_defender = false;
inline bool g_empty = false;

struct Memory {
  static constexpr std::int32_t subject_id = 0x01000001;
  static constexpr std::int32_t subject_native_id = 0x02000001;
  static constexpr std::int32_t owner_id = 0x03000001;
  static constexpr std::int32_t attacker_id = 0x03000002;
  static constexpr std::int32_t defender_id = 0x03000003;
  static constexpr std::int32_t first_combat_id = 0x04000001;
  static constexpr std::int32_t last_combat_id = 0x04000002;
  static constexpr std::int32_t date_raw = 53'178'264;
  static constexpr std::uint64_t native_revision = 41;

  Storage units, armies, characters, combats;
  std::array<Bytes<0x1D8>, 5> unit{};
  std::array<Bytes<0x148>, 5> army{};
  std::array<Bytes<0x20>, 3> character{};
  std::array<Bytes<0x710>, 2> combat{};
  std::array<Bytes<0x868>, 2> province{};
  std::array<Bytes<0x20>, 2> province_gate{};
  std::array<void *, 4> province_rows{};
  Bytes<0x150> data{};
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1C8> mode_root{};
  Bytes<0x30> mode{};
  std::array<std::int32_t, 2> province_combat_ids{};
  std::vector<std::int32_t> target_public_unit_ids;
  std::array<std::vector<std::int32_t>, 2> attacker_native_ids;
  std::array<std::vector<std::int32_t>, 2> defender_native_ids;
  void *state_ptr = state.data();
  void *jomini_ptr = jomini.data();
  void *mode_ptr = mode_root.data();
  ck3_12002::RouteBindings bindings{};
  game::Snapshot scope{};

  static bool Hostile(void *left, void *right, bool) {
    const auto a = At<std::int32_t>(left, 0x18);
    const auto b = At<std::int32_t>(right, 0x18);
    const auto hostile_rep = g_join_defender ? attacker_id : defender_id;
    return (a == owner_id && b == hostile_rep) ||
           (b == owner_id && a == hostile_rep);
  }
  static bool Empty(void *) { return g_empty; }
  static bool InCombat(void *value) {
    return At<std::int32_t>(value, 0x128) > 0;
  }

  Memory() {
    g_join_defender = false;
    g_empty = false;
    Put(state, 8, date_raw);
    Put(state, 0xA0, data.data());
    Put(jomini, 0x20, std::uint8_t{1});
    Put(data, 0x140, province_rows.data());
    Put(data, 0x14C, std::int32_t{4});
    Put(mode_root, 0x1C0, mode.data());
    for (std::size_t i = 0; i < province.size(); ++i) {
      const auto id = static_cast<std::int32_t>(i) + 2;
      Put(province[i], 0x10, id);
      Put(province[i], 0x85C, std::uint32_t{0x50726F76});
      Put(province[i], 0x20, province_gate[i].data());
      Put(province_gate[i], 0x1B, std::uint8_t{1});
      province_rows[static_cast<std::size_t>(id)] = province[i].data();
    }
    Put(province[1], 0x758, province_combat_ids.data());
    Put(province[1], 0x764, std::int32_t{0});
    for (std::size_t i = 0; i < unit.size(); ++i) {
      const auto index = static_cast<std::int32_t>(i);
      const auto public_id = subject_id + index;
      const auto native_id = subject_native_id + index;
      units.Add(public_id, unit[i], 0x10);
      armies.Add(native_id, army[i], 0x10);
      Put(unit[i], 0x20, province[i == 0 ? 0 : 1].data());
      Put(unit[i], 0x174, i == 0 ? owner_id :
          (i % 2 != 0 ? attacker_id : defender_id));
      Put(unit[i], 0x178, native_id);
      Put(army[i], 0x124, public_id);
      Put(army[i], 0x128, std::int32_t{-1});
    }
    for (std::size_t i = 0; i < character.size(); ++i) {
      characters.Add(owner_id + static_cast<std::int32_t>(i), character[i], 0x18);
      Put(character[i], 0x1C, std::uint32_t{0x43686172});
    }
    bindings.enabled = true;
    bindings.game_state_slot = &state_ptr;
    bindings.jomini_state_slot = &jomini_ptr;
    bindings.army_storage_slot = &units.root;
    bindings.army_internal_storage_slot = &armies.root;
    bindings.character_storage_slot = &characters.root;
    bindings.combat_storage_slot = &combats.root;
    bindings.contact_game_mode_slot = &mode_ptr;
    bindings.is_character_hostile = &Hostile;
    bindings.is_army_empty_for_contact = &Empty;
    bindings.is_army_in_combat = &InCombat;
    scope.paused = true;
    scope.date_raw = date_raw;
    // No controllable/player-army row is required for a foreign observation.
  }

  void AddCombat(std::size_t index, bool subject_participates = false) {
    const auto cid = first_combat_id + static_cast<std::int32_t>(index);
    combats.Add(cid, combat[index], 8);
    Put(combat[index], 0x6B8, province[1].data());
    Put(combat[index], 0x90, attacker_id);
    Put(combat[index], 0x3D8, defender_id);
    Put(combat[index], 0xD8, combat[index].data());
    Put(combat[index], 0x420, combat[index].data());
    const auto first_army = subject_native_id +
        static_cast<std::int32_t>(index * 2 + 1);
    attacker_native_ids[index] = {first_army};
    defender_native_ids[index] = {first_army + 1};
    if (subject_participates) {
      attacker_native_ids[index].insert(attacker_native_ids[index].begin(),
                                        subject_native_id);
      Put(unit[0], 0x20, province[1].data());
      Put(army[0], 0x128, cid);
      target_public_unit_ids = {subject_id, subject_id + 1, subject_id + 2};
      Put(province[1], 0x740, target_public_unit_ids.data());
      Put(province[1], 0x74C,
          static_cast<std::int32_t>(target_public_unit_ids.size()));
    }
    Put(combat[index], 0x30, attacker_native_ids[index].data());
    Put(combat[index], 0x3C,
        static_cast<std::int32_t>(attacker_native_ids[index].size()));
    Put(combat[index], 0x378, defender_native_ids[index].data());
    Put(combat[index], 0x384,
        static_cast<std::int32_t>(defender_native_ids[index].size()));
    Put(army[index * 2 + 1], 0x128, cid);
    Put(army[index * 2 + 2], 0x128, cid);
    province_combat_ids[index] = cid;
    Put(province[1], 0x764, static_cast<std::int32_t>(index + 1));
  }

  auto PhysicalBytes() const {
    return std::tuple{units.object, units.slots, armies.object, armies.slots,
                      characters.object, characters.slots, combats.object,
                      combats.slots, unit, army, character, combat, province,
                      province_gate, province_rows, data, state, jomini,
                      mode_root, mode, province_combat_ids,
                      attacker_native_ids, defender_native_ids,
                      target_public_unit_ids};
  }
};

} // namespace xar::arrival_first_fixture
