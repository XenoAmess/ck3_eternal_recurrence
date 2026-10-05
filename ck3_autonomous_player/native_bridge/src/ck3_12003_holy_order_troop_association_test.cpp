#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_mailbox.hpp"

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
template <class T> void Put(void *p, std::size_t o, T v) {
  std::memcpy(static_cast<std::byte *>(p) + o, &v, sizeof(v));
}
int checks = 0;
void *nonmilitary = nullptr, *played = nullptr;
void Check(bool ok, const char *message) { ++checks; if (!ok) throw std::runtime_error(message); }
void *Patron(void *) { return nullptr; }
bool IsMilitary(void *order) { return order != nonmilitary; }
bool Hire(void *, void *player, void *) { Check(player == played, "actual player preserved"); return false; }
std::int64_t *Cost(void *, std::int64_t *out, void *) {
  std::memset(out, 0, sizeof(std::int64_t) * 10); return out;
}
bool Afford(const std::int64_t *, void *, void *) { return true; }
void Destroy(void *) {}
void Identity(void *p, std::uint32_t id, std::uint32_t tag) {
  Put(p, 0x10, id); Put(p, 0x14, tag);
}
void Order(void *p, std::uint32_t id, std::uint32_t employer) {
  Identity(p, id, 0x486F4F72U); Put(p, 0x24, std::uint32_t{15});
  Put(p, 0x40, UINT32_MAX); Put(p, 0x80, employer);
}
} // namespace

int main(int argc, char **argv) {
  try {
    constexpr std::int32_t actor = 29829, date = 53236176;
    alignas(8) std::array<std::byte, 0x30> player{}, order_registry{}, regi_registry{}, army_registry{}, combat_registry{};
    alignas(8) std::array<std::byte, 0x40> order_entries{};
    alignas(8) std::array<std::byte, 0x50> regi_entries{};
    alignas(8) std::array<std::byte, 0x20> army_entries{};
    alignas(8) std::array<std::byte, 0x10> combat_entries{};
    alignas(8) std::array<std::array<std::byte, 0xA0>, 4> orders{};
    alignas(8) std::array<std::array<std::byte, 0x148>, 4> regiments{};
    alignas(8) std::array<std::array<std::byte, 0x130>, 2> armies{};
    alignas(8) std::array<std::byte, 0x20> combat{}, fallback{};
    const std::array<std::uint32_t, 8> ids{0xA1000000U, 0xA2000001U, 0xA1000000U,
        0xA3000002U, 0xA4000003U, UINT32_MAX, 0xA7000006U, 0xA8000004U};
    Put(player.data(), 0x18, actor); played = player.data(); nonmilitary = orders[3].data();
    for (std::size_t i = 0; i < orders.size(); ++i) {
      Order(orders[i].data(), 0xD1000001U + static_cast<std::uint32_t>(i),
          i == 2 ? std::uint32_t{39004} : static_cast<std::uint32_t>(actor));
      Put(order_entries.data(), i * 0x10 + 8, orders[i].data());
    }
    Put(orders[0].data(), 0x88, ids.data()); Put(orders[0].data(), 0x94, std::int32_t{8});
    Put(orders[2].data(), 0x88, ids.data()); Put(orders[2].data(), 0x94, std::int32_t{8});
    Put(order_registry.data(), 0x20, order_entries.data()); Put(order_registry.data(), 0x2C, std::int32_t{4});
    for (std::size_t i = 0; i < regiments.size(); ++i) {
      Identity(regiments[i].data(), ids[i == 2 ? 3 : i == 3 ? 4 : i], 0x41725267U);
      Put(regi_entries.data(), i * 0x10 + 8, regiments[i].data());
    }
    Put(regiments[2].data(), 0x10, std::uint32_t{0xA6000002U}); // stale generation
    Put(regiments[0].data(), 0x140, std::uint32_t{0xB1000000U});
    Put(regiments[1].data(), 0x140, UINT32_MAX); // valid but not raised
    Put(regiments[3].data(), 0x140, std::uint32_t{0xB2000001U});
    Identity(armies[0].data(), 0xB1000000U, 0x41726D79U);
    Identity(armies[1].data(), 0xB6000001U, 0x41726D79U); // stale Army generation
    Put(armies[0].data(), 0x128, std::uint32_t{0xC1000000U});
    Put(combat.data(), 0x08, std::uint32_t{0xC1000000U}); Put(combat.data(), 0x0C, std::uint32_t{0x436F6D62U});
    Put(army_entries.data(), 8, armies[0].data()); Put(army_entries.data(), 0x18, armies[1].data());
    Put(combat_entries.data(), 8, combat.data());
    Put(regi_registry.data(), 0x20, regi_entries.data()); Put(regi_registry.data(), 0x2C, std::int32_t{5});
    Put(army_registry.data(), 0x20, army_entries.data()); Put(army_registry.data(), 0x2C, std::int32_t{2});
    Put(combat_registry.data(), 0x20, combat_entries.data()); Put(combat_registry.data(), 0x2C, std::int32_t{1});
    void *registry = order_registry.data(), *fallback_pointer = fallback.data();
    void *regi_db = regi_registry.data(), *army_db = army_registry.data(), *combat_db = combat_registry.data();
    holy::Bindings b{true, &registry, &fallback_pointer, &Patron, &IsMilitary, &Hire, &Cost, &Afford, &Destroy};
    b.army_registry_slot = &army_db; b.combat_registry_slot = &combat_db;
    constexpr std::uintptr_t base = 0x10000000;
    const auto exact = holy::BindPlayerHolyOrderImage12003(base, holy::kExecutableSha256);
    Check(reinterpret_cast<std::uintptr_t>(exact.regiment_registry_slot) == base + 0x5D1F340,
        "source-derived Regiment DB RVA");
    Check(reinterpret_cast<std::uintptr_t>(exact.army_registry_slot) == base + 0x5D1DE48,
        "source-derived Army DB RVA");
    Check(reinterpret_cast<std::uintptr_t>(exact.combat_registry_slot) == base + 0x5D1DE70,
        "source-derived Combat DB RVA");
    std::string samples = "{\"samples\":[";
    for (int sample = 0; sample < 4; ++sample) {
      b.regiment_registry_slot = sample == 1 ? nullptr : &regi_db;
      regi_db = sample == 2 ? nullptr : regi_registry.data();
      Put(orders[0].data(), 0x94, sample == 3 ? std::int32_t{-1} : std::int32_t{8});
      holy::Context observation{};
      Check(holy::ReadPlayerHolyOrderContext12003(b, played, actor, date,
          40001 + static_cast<std::uint64_t>(sample), observation), "production readonly provider");
      const auto &association = observation.rows[0].military_terms->troop_association;
      Check(observation.rows[0].military_terms->can_hire == false && association.applies_to_player,
          "already-hired final false retains applicable association");
      if (sample == 1) {
        Check(!association.available && association.rows.empty() &&
            association.unavailable_reason == "native_troop_association_binding_unavailable",
            "missing native bindings unavailable, not knownempty");
      } else if (sample == 3) {
        Check(!association.available && association.rows.empty() &&
            association.unavailable_reason == "native_troop_association_vector_unavailable",
            "failed vector read differs from legalzero");
      } else {
        Check(association.available && association.rows.size() == ids.size(), "all ordered source occurrences copied");
        for (std::size_t i = 0; i < ids.size(); ++i) {
          const auto &member = association.rows[i];
          Check(member.regiment_id == ids[i] && member.available, "fullgeneration/order/duplicates retained");
          if (sample == 2) {
            Check(!member.regiment_resolved && !member.native_carmy_id && !member.combat_id,
                "null native registry follows known invalid fallback");
          } else if (i == 0 || i == 2) {
            Check(member.regiment_resolved && member.native_carmy_id == 0xB1000000U &&
                member.native_carmy_resolved && member.combat_id == 0xC1000000U && member.combat_resolved,
                "actual Regi->Army->Combat chain uses its distinct full IDs");
          } else if (i == 1) {
            Check(member.regiment_resolved && !member.native_carmy_id && !member.native_carmy_resolved,
                "unraised valid Regiment differs from missingRegiment");
          } else if (i == 4) {
            Check(member.regiment_resolved && member.native_carmy_id == 0xB2000001U &&
                !member.native_carmy_resolved && !member.combat_id,
                "stale Army fullref retained without resolving a different generation");
          } else {
            Check(!member.regiment_resolved && !member.native_carmy_id,
                "stale/null/outofrange/sentinel Regiment follows canonical invalid fallback");
          }
        }
      }
      const auto &empty = observation.rows[1].military_terms->troop_association;
      Check(empty.rows.empty() && empty.available == (sample != 1), "zero Regi vector is knownempty with bindings");
      const auto &other = observation.rows[2].military_terms->troop_association;
      Check(other.available && !other.applies_to_player && other.rows.empty(), "other employer is explicitly inapplicable");
      Check(!observation.rows[3].military_terms, "nonmilitary has no military association");
      xar::ck3_12003::PlayerHolyOrderMailboxContext12003 query{};
      query.observation = std::move(observation); query.completed = true;
      query.envelope.frame_stable = true;
      query.envelope.expected_snapshot_revision = 354 + static_cast<std::uint64_t>(sample);
      query.envelope.expected_snapshot.date_raw = date;
      const auto packet = xar::ck3_12003::SerializePlayerHolyOrderContextResult12003(
          query, "g2-read-holyassociation-" + std::to_string(sample));
      Check(!packet.empty(), "actual command_result contains copied identity association");
      if (sample != 0) samples += ',';
      samples += packet;
    }
    samples += "]}";
    if (argc > 1) { std::ofstream out(argv[1]); out << samples << '\n'; }
    std::cout << "GREEN HolyOrder troop association checks=" << checks << '\n'; return 0;
  } catch (const std::exception &error) { std::cerr << "RED " << error.what() << '\n'; return 1; }
}
