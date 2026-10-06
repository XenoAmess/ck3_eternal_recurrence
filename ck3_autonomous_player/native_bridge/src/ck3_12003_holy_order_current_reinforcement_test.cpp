#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_mailbox.hpp"
#include "xar_bridge/ck3_12003_holy_order_current_reinforcement.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>

namespace holy = xar::ck3_12003::religion::holy_order;
namespace {
template <class T> void Put(void *p, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
}
template <class T> T Get(void *p, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<std::byte *>(p) + offset, sizeof(value)); return value;
}
int checks = 0;
void *nonmilitary = nullptr;
void Check(bool ok, const char *reason) { ++checks; if (!ok) throw std::runtime_error(reason); }
void *Patron(void *) { return nullptr; }
bool Military(void *order) { return order != nonmilitary; }
bool Hire(void *, void *, void *) { return false; }
std::int64_t *Cost(void *, std::int64_t *out, void *) { std::memset(out, 0, 80); return out; }
bool Afford(const std::int64_t *, void *, void *) { return true; }
void Destroy(void *) {}
std::int64_t *Fraction(void *regiment, std::int64_t *out) {
  *out = Get<std::uint32_t>(regiment, 0x10) == 0xA1000000U ? 3000 : 0; return out;
}
std::int32_t Months(void *regiment) {
  return Get<std::uint32_t>(regiment, 0x10) == 0xA1000000U ? 4 : 0;
}
bool CanReplenish(void *regiment, void *chunk) {
  Check(Get<std::uint32_t>(regiment, 0x10) == Get<std::uint32_t>(chunk, 8), "actual persistent receiver and chunk backlink");
  return Get<std::int32_t>(chunk, 0x0C) == 0;
}
bool ChunkCanReplenish(void *chunk) { return Get<std::int32_t>(chunk, 0x0C) == 1; }
void Identity(void *object, std::uint32_t id, std::uint32_t tag) {
  Put(object, 0x10, id); Put(object, 0x14, tag);
}
void Database(void *db, void *entries, std::int32_t count) {
  Put(db, 0x20, entries); Put(db, 0x2C, count);
}
} // namespace

int main(int argc, char **argv) {
  try {
    constexpr std::int32_t actor = 29829, date = 53290000;
    constexpr std::uint32_t persistent0 = 0xA1000000U, persistent1 = 0xA2000001U;
    constexpr std::uint32_t arrg = 0xB1000000U, carmy = 0xC1000000U, unit = 0xD1000000U;
    alignas(8) std::array<std::byte, 0x30> player{}, order_db{}, persistent_db{}, arrg_db{}, army_db{}, unit_db{}, combat_db{};
    alignas(8) std::array<std::byte, 0x40> order_entries{}, persistent_entries{};
    alignas(8) std::array<std::byte, 0x10> arrg_entries{}, army_entries{}, unit_entries{};
    alignas(8) std::array<std::array<std::byte, 0xA0>, 4> orders{};
    alignas(8) std::array<std::array<std::byte, 0x150>, 3> persistent{};
    alignas(8) std::array<std::byte, 0x148> army_regiment{};
    alignas(8) std::array<std::byte, 0x130> army{};
    alignas(8) std::array<std::byte, 0x180> public_unit{};
    alignas(8) std::array<std::byte, 0x20> fallback{};
    const std::array<std::uint32_t, 5> roster{persistent0, persistent1, persistent0, 0xA3000002U, UINT32_MAX};
    const std::array<std::uint32_t, 2> transient{arrg, arrg};
    Put(player.data(), 0x18, actor); nonmilitary = orders[3].data();
    for (std::size_t i = 0; i < orders.size(); ++i) {
      Identity(orders[i].data(), static_cast<std::uint32_t>(i), 0x486F4F72U);
      Put(orders[i].data(), 0x24, std::uint32_t{15}); Put(orders[i].data(), 0x40, UINT32_MAX);
      Put(orders[i].data(), 0x80, i == 1 ? std::uint32_t{39004} : static_cast<std::uint32_t>(actor));
      Put(order_entries.data(), i * 0x10 + 8, orders[i].data());
    }
    Put(orders[0].data(), 0x68, roster.data()); Put(orders[0].data(), 0x74, std::int32_t{5});
    Put(orders[0].data(), 0x88, transient.data()); Put(orders[0].data(), 0x94, std::int32_t{2});
    Put(orders[1].data(), 0x68, roster.data()); Put(orders[1].data(), 0x74, std::int32_t{1});
    Database(order_db.data(), order_entries.data(), 4);
    for (std::size_t r = 0; r < persistent.size(); ++r) {
      const auto id = r == 0 ? persistent0 : r == 1 ? persistent1 : 0xA6000002U;
      Identity(persistent[r].data(), id, 0x52656769U);
      Put(persistent[r].data(), 0x12C, r == 0 ? std::uint32_t{40001} : std::uint32_t{40002});
      Put(persistent_entries.data(), r * 0x10 + 8, persistent[r].data());
      for (std::int32_t c = 0; c < 7; ++c) {
        auto *chunk = persistent[r].data() + 0x18 + static_cast<std::size_t>(c) * 0x24;
        Put(chunk, 0, c == 0 ? std::int32_t{100} : std::int32_t{0});
        Put(chunk, 4, c == 0 && r == 0 ? std::int32_t{60} : std::int32_t{0});
        Put(chunk, 8, id); Put(chunk, 0x0C, c);
        Put(chunk, 0x10, c == 0 && r == 0 ? arrg : UINT32_MAX);
        Put(chunk, 0x14, std::uint8_t{0}); Put(chunk, 0x18, r == 1 && c == 0 ? std::int32_t{3} : std::int32_t{0});
      }
    }
    Database(persistent_db.data(), persistent_entries.data(), 4);
    Identity(army_regiment.data(), arrg, 0x41725267U); Put(army_regiment.data(), 0x140, carmy);
    Put(arrg_entries.data(), 8, army_regiment.data()); Database(arrg_db.data(), arrg_entries.data(), 1);
    Identity(army.data(), carmy, 0x41726D79U); Put(army.data(), 0x120, std::uint32_t{35000});
    Put(army.data(), 0x124, unit); Put(army.data(), 0x128, UINT32_MAX);
    Put(army_entries.data(), 8, army.data()); Database(army_db.data(), army_entries.data(), 1);
    Identity(public_unit.data(), unit, 0x556E6974U); Put(public_unit.data(), 0x174, static_cast<std::uint32_t>(actor));
    Put(public_unit.data(), 0x178, carmy); Put(unit_entries.data(), 8, public_unit.data());
    Database(unit_db.data(), unit_entries.data(), 1); Database(combat_db.data(), nullptr, 0);
    void *order_registry = order_db.data(), *persistent_registry = persistent_db.data();
    void *arrg_registry = arrg_db.data(), *army_registry = army_db.data(), *unit_registry = unit_db.data();
    void *combat_registry = combat_db.data(), *fallback_pointer = fallback.data();
    holy::Bindings b{true, &order_registry, &fallback_pointer, &Patron, &Military, &Hire, &Cost, &Afford, &Destroy};
    b.regiment_registry_slot = &arrg_registry; b.army_registry_slot = &army_registry; b.combat_registry_slot = &combat_registry;
    b.current_reinforcement.enabled = true;
    b.current_reinforcement.persistent_registry_slot = &persistent_registry;
    b.current_reinforcement.monthly_fraction = &Fraction; b.current_reinforcement.months_to_full = &Months;
    b.current_reinforcement.can_replenish = &CanReplenish; b.current_reinforcement.chunk_can_replenish = &ChunkCanReplenish;
    b.current_reinforcement.army_registry_slot = b.army_registry_slot;
    b.current_reinforcement.unit_registry_slot = &unit_registry;
    std::string samples = "{\"fixture_provenance\":\"synthetic game memory and native callbacks; real whole provider and serializer\",\"samples\":[";
    for (int scene = 0; scene < 2; ++scene) {
      b.current_reinforcement.monthly_fraction = scene == 1 ? nullptr : &Fraction;
      holy::Context observation;
      Check(holy::ReadPlayerHolyOrderContext12003(b, player.data(), actor, date,
          46001 + static_cast<std::uint64_t>(scene), observation), "real whole provider read");
      const auto &family = observation.rows[0].military_terms->current_reinforcement_v1;
      if (scene == 0) {
        Check(family.available && family.source_count == 5 && family.rows.size() == 5, "complete actual persistent collection");
        Check(family.rows[0].owner_character_id == 40001U && family.rows[0].native_months_to_full == 4 &&
            family.rows[0].monthly_replenishment_fraction_raw == 3000, "fresh actual Regi receiver values");
        Check(family.rows[2].persistent_regiment_id == persistent0 && family.rows[2].source_index == 2, "ordered duplicate preserved");
        Check(family.rows[1].chunks[0].current_soldiers == 0 && family.rows[1].chunks[0].state_raw == 3 &&
            family.rows[1].native_months_to_full == 0 && family.rows[1].monthly_replenishment_fraction_raw == 0,
            "physical zero and native zero timing are distinct from full strength");
        Check(family.rows[0].chunks[0].native_can_replenish == true &&
            family.rows[0].chunks[0].native_chunk_can_replenish == false, "independent native booleans");
        Check(!family.rows[3].resolved && family.rows[3].available && family.rows[3].chunks.empty(), "stale persistent generation has no actual values");
        Check(!family.rows[4].resolved && family.rows[4].available, "sentinel current reference is known invalid");
        Check(observation.rows[1].military_terms->current_reinforcement_v1.rows[0].owner_character_id == 40001U,
            "foreign employer retains current candidate reinforcement inputs");
        Check(observation.rows[2].military_terms->current_reinforcement_v1.available &&
            observation.rows[2].military_terms->current_reinforcement_v1.rows.empty(), "current empty persistent roster");
      } else Check(!family.available && !family.source_count && family.rows.empty(), "missing new callback not synthetic zero");
      const auto &roles = family.army_roles;
      Check(roles.available && roles.rows.size() == 2 && roles.rows[0].native_carmy_id == carmy &&
          roles.rows[0].public_army_id == unit && roles.rows[0].commander_character_id == 35000U &&
          roles.rows[0].owner_character_id == static_cast<std::uint32_t>(actor), "actual commander/Unit owner distinct from persistent owner");
      Check(roles.rows[1].association_index == 1 && roles.rows[1].public_army_id == unit, "existing association multiplicity retained");
      Check(!observation.rows[1].military_terms->current_reinforcement_v1.army_roles.applies_to_player,
          "foreign order does not expose player-only Army roles");
      Check(!observation.rows[3].military_terms, "nonmilitary has no new military family");
      xar::ck3_12003::PlayerHolyOrderMailboxContext12003 query;
      query.completed = true; query.observation = std::move(observation); query.envelope.frame_stable = true;
      query.envelope.expected_snapshot_revision = 420 + static_cast<std::uint64_t>(scene);
      query.envelope.expected_snapshot.date_raw = date;
      if (scene != 0) samples += ',';
      samples += xar::ck3_12003::SerializePlayerHolyOrderContextResult12003(
          query, "g2-read-holyreinforcement-" + std::to_string(scene));
    }
    samples += "]}";
    if (argc > 1) { std::ofstream out(argv[1]); out << samples << '\n'; }
    std::cout << "GREEN HolyOrder current reinforcement checks=" << checks << '\n'; return 0;
  } catch (const std::exception &e) { std::cerr << "RED " << e.what() << '\n'; return 1; }
}
