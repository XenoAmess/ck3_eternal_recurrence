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
template <class T> T Get(void *p, std::size_t o) {
  T v{}; std::memcpy(&v, static_cast<std::byte *>(p) + o, sizeof(v)); return v;
}
int checks = 0, release_calls = 0, combat_calls = 0;
void *played = nullptr, *retained = nullptr, *combat_order = nullptr, *ready = nullptr;
void *nonmilitary = nullptr;
bool cost_available = true;
void Check(bool ok, const char *message) {
  ++checks; if (!ok) throw std::runtime_error(message);
}
void *Patron(void *) { return nullptr; }
bool IsMilitary(void *p) { return p != nonmilitary; }
bool Hire(void *, void *actor, void *sink) {
  Check(actor == played, "hire uses current actor");
  std::memcpy(sink, "Already hired", 14); Put(sink, 0x10, std::size_t{13}); return false;
}
std::int64_t *Cost(void *, std::int64_t *out, void *) {
  std::memset(out, 0, sizeof(std::int64_t) * 10);
  return cost_available ? out : nullptr;
}
bool Afford(const std::int64_t *, void *, void *) { return true; }
void Destroy(void *) {}
bool Release(void *order) {
  ++release_calls;
  Check(order == retained || order == combat_order || order == ready,
      "native release predicate only samples currently player-employed order");
  return order == ready;
}
bool Combat(void *vector) {
  ++combat_calls;
  auto *order = static_cast<std::byte *>(vector) - 0x88;
  Check(order == retained || order == combat_order || order == ready,
      "native combat predicate receives order+88 vector");
  return order == combat_order;
}
void Order(void *p, std::uint32_t id, std::uint32_t employer) {
  Put(p, 0x10, id); Put(p, 0x14, std::uint32_t{0x486F4F72});
  Put(p, 0x24, std::uint32_t{15}); Put(p, 0x40, UINT32_MAX); Put(p, 0x80, employer);
}
} // namespace

int main(int argc, char **argv) {
  try {
    constexpr std::int32_t actor = 29829, date = 53236176;
    alignas(8) std::array<std::byte, 0x30> player{};
    alignas(8) std::array<std::byte, 0x24D8> manager{};
    alignas(8) std::array<std::byte, 0x60> entries{};
    alignas(8) std::array<std::array<std::byte, 0xA0>, 6> orders{};
    alignas(8) std::array<std::byte, 0xA0> fallback{};
    const std::array<std::uint32_t, 2> queue{0xA2000002U, 0xA3000003U};
    Put(player.data(), 0x18, actor); played = player.data();
    retained = orders[0].data(); combat_order = orders[1].data(); ready = orders[2].data();
    nonmilitary = orders[5].data();
    for (std::size_t i = 0; i < orders.size(); ++i) {
      const auto employer = i == 3 ? std::uint32_t{39004} : i == 4 ? UINT32_MAX : std::uint32_t{29829};
      Order(orders[i].data(), 0xA1000001U + static_cast<std::uint32_t>(i) * 0x01000001U, employer);
      Put(entries.data(), i * 0x10 + 8, orders[i].data());
    }
    void *registry = manager.data() + 0x28, *fallback_pointer = fallback.data();
    Put(registry, 0x20, entries.data()); Put(registry, 0x2C, std::int32_t{6});
    Put(manager.data(), 0x24A8, queue.data());
    holy::Bindings bindings{true, &registry, &fallback_pointer,
        &Patron, &IsMilitary, &Hire, &Cost, &Afford, &Destroy};
    constexpr std::uintptr_t base = 0x10000000;
    const auto exact = holy::BindPlayerHolyOrderImage12003(base, holy::kExecutableSha256);
    Check(reinterpret_cast<std::uintptr_t>(exact.release_eligible) == base + 0x261A1D0,
        "actual exact release predicate bound");
    Check(reinterpret_cast<std::uintptr_t>(exact.associated_regiment_in_combat) == base + 0x261D5F0,
        "actual exact combat predicate bound");
    std::string samples = "{\"samples\":[";
    for (int sample = 0; sample < 4; ++sample) {
      cost_available = sample != 1;
      bindings.release_eligible = sample == 2 ? nullptr : &Release;
      bindings.associated_regiment_in_combat = sample == 2 ? nullptr : &Combat;
      Put(manager.data(), 0x24B4, sample == 3 ? std::int32_t{-1} : std::int32_t{2});
      holy::Context observation{};
      Check(holy::ReadPlayerHolyOrderContext12003(bindings, played, actor, date,
          30001 + static_cast<std::uint64_t>(sample), observation), "actual provider copies new lifecycle");
      Check(observation.rows.size() == 6 && !observation.rows[5].military_terms,
          "nonmilitary lifecycle stays inapplicable");
      for (std::size_t i = 0; i < 5; ++i) {
        const auto &terms = *observation.rows[i].military_terms;
        const auto &service = terms.service_lifecycle;
        Check(terms.can_hire == false && terms.available == (sample != 1),
            "lifecycle stays independent of final hire and resources");
        Check(service.applies_to_player == (i < 3), "service owned by actual current player only");
        if (i >= 3) {
          Check(service.available && !service.release_eligible &&
              !service.associated_regiment_in_combat && !service.release_check_queued,
              "unhired and other employer yield explicit nonapplicable values");
        } else if (sample == 2) {
          Check(!service.available && !service.release_eligible &&
              service.unavailable_reason == "native_service_lifecycle_binding_unavailable",
              "missing new bindings are unavailable");
        } else {
          Check(service.release_eligible == (i == 2) &&
              service.associated_regiment_in_combat == (i == 1),
              "retained service, combat delay and ready release remain distinct");
          if (sample == 3) {
            Check(!service.available && !service.release_check_queued &&
                service.unavailable_reason == "native_release_check_queue_unavailable",
                "queue read failure retains sampled native predicates");
          } else {
            Check(service.available && service.release_check_queued == (i != 0),
                "full generation ID candidate membership preserved; stale queued combat stays pending");
          }
        }
      }
      xar::ck3_12003::PlayerHolyOrderMailboxContext12003 query{};
      query.observation = std::move(observation); query.completed = true;
      query.envelope.frame_stable = true;
      query.envelope.expected_snapshot_revision = 254 + static_cast<std::uint64_t>(sample);
      query.envelope.expected_snapshot.date_raw = date;
      const auto packet = xar::ck3_12003::SerializePlayerHolyOrderContextResult12003(
          query, "g2-read-holylifecycle-" + std::to_string(sample));
      Check(!packet.empty(), "real command_result wire serializes lifecycle");
      if (sample != 0) samples += ',';
      samples += packet;
    }
    Check(release_calls == 9 && combat_calls == 9,
        "only3player-employed military rows per available binding capture sampled");
    samples += "]}";
    if (argc > 1) { std::ofstream out(argv[1]); out << samples << '\n'; }
    std::cout << "GREEN holy-order service lifecycle checks=" << checks << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n'; return 1;
  }
}
