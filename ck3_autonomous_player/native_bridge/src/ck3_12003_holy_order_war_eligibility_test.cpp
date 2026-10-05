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
int checks = 0, war_calls = 0, destroyed = 0;
void *played = nullptr, *qualified = nullptr, *nonmilitary = nullptr;
bool cost_available = true;
void Check(bool ok, const char *message) {
  ++checks; if (!ok) throw std::runtime_error(message);
}
void Reason(void *sink, const char *text) {
  Check(Get<std::size_t>(sink, 0x10) == 0 && Get<std::size_t>(sink, 0x18) == 15,
      "native war reason receives owned canonical empty string");
  const auto size = std::strlen(text);
  if (size <= 15) std::memcpy(sink, text, size + 1);
  else {
    auto *heap = new char[size + 1]; std::memcpy(heap, text, size + 1);
    Put(sink, 0, heap); Put(sink, 0x18, size);
  }
  Put(sink, 0x10, size);
}
void Destroy(void *sink) {
  ++destroyed;
  if (Get<std::size_t>(sink, 0x18) >= 16) delete[] Get<char *>(sink, 0);
}
void *Patron(void *) { return nullptr; }
bool IsMilitary(void *order) { return order != nonmilitary; }
bool CanHire(void *, void *actor, void *sink) {
  Check(actor == played, "final hire retains actual player");
  Reason(sink, "Already hired"); return false;
}
bool WarEligibility(void *order, void *actor, void *sink) {
  ++war_calls;
  Check(actor == played, "independent native war input receives actual player");
  const bool result = order == qualified;
  Reason(sink, result ? "" : "\x15R Requires hostile enemy\x15!\n");
  return result;
}
std::int64_t *Cost(void *, std::int64_t *out, void *) {
  std::memset(out, 0, sizeof(std::int64_t) * 10);
  return cost_available ? out : nullptr;
}
bool Afford(const std::int64_t *, void *, void *sink) { Reason(sink, ""); return true; }
void Order(void *p, std::uint32_t id) {
  Put(p, 0x10, id); Put(p, 0x14, std::uint32_t{0x486F4F72});
  Put(p, 0x24, std::uint32_t{15}); Put(p, 0x40, UINT32_MAX);
  Put(p, 0x80, std::uint32_t{29829});
}
} // namespace

int main(int argc, char **argv) {
  try {
    constexpr std::int32_t actor = 29829, date = 53236176;
    alignas(8) std::array<std::byte, 0x30> player{}, manager{}, entries{};
    alignas(8) std::array<std::byte, 0x90> first{}, second{}, monk{}, fallback{};
    Put(player.data(), 0x18, actor); played = player.data(); qualified = first.data();
    nonmilitary = monk.data();
    Order(first.data(), 0xA1000001U); Order(second.data(), 0xA2000002U);
    Order(monk.data(), 0xA3000003U);
    Put(entries.data(), 8, first.data()); Put(entries.data(), 0x18, second.data());
    Put(entries.data(), 0x28, monk.data());
    Put(manager.data(), 0x20, entries.data()); Put(manager.data(), 0x2C, std::int32_t{3});
    void *manager_pointer = manager.data(), *fallback_pointer = fallback.data();
    holy::Bindings bindings{true, &manager_pointer, &fallback_pointer,
        &Patron, &IsMilitary, &CanHire, &Cost, &Afford, &Destroy};
    bindings.current_war_eligibility = &WarEligibility;
    constexpr std::uintptr_t base = 0x10000000;
    const auto exact = holy::BindPlayerHolyOrderImage12003(base, holy::kExecutableSha256);
    Check(reinterpret_cast<std::uintptr_t>(exact.current_war_eligibility) == base + 0x261C120,
        "exact build war predicate RVA");
    Check(!holy::BindPlayerHolyOrderImage12003(base, "wrong-build").enabled,
        "existing exact build selection");
    std::string samples = "{\"samples\":[";
    for (int sample = 0; sample < 3; ++sample) {
      cost_available = sample != 1;
      bindings.current_war_eligibility = sample == 2 ? nullptr : &WarEligibility;
      holy::Context observation{};
      Check(holy::ReadPlayerHolyOrderContext12003(bindings, played, actor, date,
          20001 + static_cast<std::uint64_t>(sample), observation), "real provider reads rows");
      Check(observation.rows.size() == 3 && !observation.rows[2].military_terms,
          "nonmilitary row never evaluates military war input");
      for (std::size_t i = 0; i < 2; ++i) {
        const auto &row = observation.rows[i];
        const auto &terms = *row.military_terms;
        const auto &war = terms.current_war_eligibility;
        Check(row.employer_id == static_cast<std::uint32_t>(actor) && terms.can_hire == false,
            "already hired actor can still observe independent religious war input");
        Check(terms.available == (sample != 1), "war availability does not alter final terms");
        if (sample == 2) {
          Check(!war.available && !war.qualifies && !war.reasons_available,
              "missing native war binding is observable unavailable");
        } else {
          Check(war.available && war.qualifies == (i == 0) && war.reasons_available,
              "true and legal false retained independently of final hire");
          Check(war.reason_literal == (i == 0 ? "" : "\x15R Requires hostile enemy\x15!\n"),
              "native empty/heap war reasons retained exactly");
        }
      }
      xar::ck3_12003::PlayerHolyOrderMailboxContext12003 query{};
      query.observation = std::move(observation); query.completed = true;
      query.envelope.frame_stable = true;
      query.envelope.expected_snapshot_revision = 154 + static_cast<std::uint64_t>(sample);
      query.envelope.expected_snapshot.date_raw = date;
      const auto packet = xar::ck3_12003::SerializePlayerHolyOrderContextResult12003(
          query, "g2-read-holywar-" + std::to_string(sample));
      Check(!packet.empty(), "production command_result wire serialized");
      if (sample != 0) samples += ',';
      samples += packet;
    }
    Check(war_calls == 4 && destroyed == 16,
        "one native war call per military row; all separate reason sinks reclaimed");
    samples += "]}";
    if (argc > 1) { std::ofstream out(argv[1]); out << samples << '\n'; }
    std::cout << "GREEN holy-order current war input checks=" << checks << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n'; return 1;
  }
}
