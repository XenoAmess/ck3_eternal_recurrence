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
  T value{}; std::memcpy(&value, static_cast<std::byte *>(p) + o, sizeof(value)); return value;
}
int checks = 0;
void Check(bool condition, const char *message) {
  ++checks; if (!condition) throw std::runtime_error(message);
}
void *played = nullptr;
bool quote_available = true;
std::size_t Index(void *order) { return Get<std::uint32_t>(order, 0x10) & 0x00FFFFFFU; }
// Only callback/world seams are synthetic. The production reader, memory
// projection, domain serializer and command_result serializer run unchanged.
void *Patron(void *order) {
  const auto index = Index(order);
  return index >= 2 && index <= 4 ? played : nullptr;
}
bool Military(void *order) { return Index(order) != 8; }
bool CanHire(void *, void *actor, void *) {
  Check(actor == played, "final native callback receives actual player"); return false;
}
std::int64_t *Cost(void *order, std::int64_t *out, void *actor) {
  Check(actor == played, "native quote callback receives actual player");
  std::memset(out, 0, sizeof(std::int64_t) * 10);
  if (Index(order) != 0) out[2] = 10600000; // Synthetic ordinary quote, no formula reconstruction.
  return quote_available ? out : nullptr;
}
bool Afford(const std::int64_t *, void *, void *) { return true; }
void Destroy(void *) {}
void Order(void *p, std::uint32_t id, std::uint32_t title, std::uint32_t employer) {
  Put(p, 0x10, id); Put(p, 0x14, std::uint32_t{0x486F4F72});
  Put(p, 0x24, std::uint32_t{15}); Put(p, 0x28, title);
  Put(p, 0x40, UINT32_MAX); Put(p, 0x80, employer);
}
} // namespace

int main(int argc, char **argv) {
  try {
    constexpr std::int32_t actor = 29829, date = 53236176;
    alignas(8) std::array<std::byte, 0x30> player{}, manager{}, titles_registry{};
    alignas(8) std::array<std::byte, 0x90> entries{};
    alignas(8) std::array<std::byte, 0x70> title_entries{};
    alignas(8) std::array<std::array<std::byte, 0x98>, 9> orders{};
    alignas(8) std::array<std::array<std::byte, 0x130>, 7> titles{};
    alignas(8) std::array<std::byte, 0x130> fallback_title{};
    Put(player.data(), 0x18, actor); played = player.data();
    Put(fallback_title.data(), 0x128, UINT32_MAX);
    for (std::size_t i = 0; i < orders.size(); ++i) {
      const auto index = static_cast<std::uint32_t>(i);
      const auto title_id = i == 7 ? UINT32_MAX : 0xB1000000U + index;
      const auto employer = i == 2 ? UINT32_MAX : i == 4 ? static_cast<std::uint32_t>(actor)
                                                                  : 0xD1000003U;
      Order(orders[i].data(), 0xA1000000U + index, title_id, employer);
      Put(entries.data(), i * 0x10 + 8, orders[i].data());
    }
    for (std::size_t i = 0; i < titles.size(); ++i) {
      const auto title_id = (i == 5 ? 0xC1000000U : 0xB1000000U)
                            + static_cast<std::uint32_t>(i);
      Put(titles[i].data(), 0x10, title_id);
      const auto holder = i == 0 ? static_cast<std::uint32_t>(actor) : i == 6 ? 0U : 0xE1000001U;
      Put(titles[i].data(), 0x128, holder);
      Put(title_entries.data(), i * 0x10 + 8, titles[i].data());
    }
    Put(manager.data(), 0x20, entries.data());
    Put(manager.data(), 0x2C, std::int32_t{9});
    Put(titles_registry.data(), 0x20, title_entries.data());
    Put(titles_registry.data(), 0x2C, std::int32_t{7});
    void *manager_pointer = manager.data(), *fallback_pointer = nullptr;
    void *title_registry_pointer = titles_registry.data(), *title_fallback_pointer = fallback_title.data();
    // Nondefault actual loaded values distinguish observation from stock constants.
    std::int64_t hire_factor = -25000, recall_factor = 175000;
    holy::Bindings b;
    b.enabled = true; b.manager_slot = &manager_pointer; b.fallback_slot = &fallback_pointer;
    b.patron = &Patron; b.is_military = &Military; b.can_hire = &CanHire;
    b.cost = &Cost; b.can_afford = &Afford; b.reason_destroy = &Destroy;
    b.hire_cost_context = {&title_registry_pointer, &title_fallback_pointer, &hire_factor, &recall_factor};
    const auto exact = holy::BindPlayerHolyOrderImage12003(0x10000000, holy::kExecutableSha256);
    Check(reinterpret_cast<std::uintptr_t>(exact.hire_cost_context.title_registry_slot) == 0x15D1DAF8
          && reinterpret_cast<std::uintptr_t>(exact.hire_cost_context.title_fallback_slot) == 0x15D1DAE0
          && reinterpret_cast<std::uintptr_t>(exact.hire_cost_context.patron_hire_multiplier_raw) == 0x15C69250
          && reinterpret_cast<std::uintptr_t>(exact.hire_cost_context.patron_recall_multiplier_raw) == 0x15C69248,
          "source-exact title and loaded multiplier bindings");
    std::string samples = "{\"samples\":[";
    for (int sample = 0; sample < 4; ++sample) {
      quote_available = sample != 1;
      b.hire_cost_context.title_registry_slot = sample == 2 ? nullptr : &title_registry_pointer;
      b.hire_cost_context.patron_recall_multiplier_raw = sample == 3 ? nullptr : &recall_factor;
      holy::Context observation;
      Check(holy::ReadPlayerHolyOrderContext12003(b, played, actor, date,
          22001 + static_cast<std::uint64_t>(sample), observation), "whole production context provider");
      Check(observation.rows.size() == 9 && !observation.rows[8].military_terms,
            "nonmilitary row has no military observer");
      for (std::size_t i = 0; i < 8; ++i) {
        const auto &terms = *observation.rows[i].military_terms;
        const auto &context = terms.hire_cost_context;
        Check(terms.can_hire == false && terms.available == (sample != 1),
              "cost branch independent of false finalCan and unavailable resource quote");
        if (sample == 2) {
          Check(!context.available && !context.order_title_id && !context.cost_branch,
                "missing title binding retains unsampled unavailable");
          continue;
        }
        Check(context.order_title_id == (i == 7 ? UINT32_MAX : 0xB1000000U + static_cast<std::uint32_t>(i))
              && context.order_title_resolved == (i != 5 && i != 7),
              "fullgeneration and raw sentinel retained with native fallback");
        if (i == 0) {
          Check(context.available && context.cost_branch == "title_holder_zero"
                && context.title_holder_is_player == true && !context.patron_is_player
                && !context.employed_by_other && !context.selected_patron_multiplier_raw,
                "early holder exemption skips all later source branches");
        } else if (i >= 2 && i <= 4) {
          Check(context.cost_branch == (i == 3 ? "patron_recall" : "patron_hire")
                && context.patron_is_player == true && context.employed_by_other == (i == 3),
                "patron pointer and current/other/empty employer select exact branch");
          if (sample == 3 && i == 3) {
            Check(!context.available && !context.selected_patron_multiplier_raw
                  && context.unavailable_reason == "native_hire_cost_context_multiplier_unavailable",
                  "only demanded recall multiplier absence is unavailable");
          } else {
            Check(context.available && context.selected_patron_multiplier_raw == (i == 3 ? recall_factor : hire_factor),
                  "signed actual loaded multiplier preserved");
          }
        } else {
          Check(context.available && context.cost_branch == "ordinary" && context.patron_is_player == false
                && !context.employed_by_other && !context.selected_patron_multiplier_raw,
                "ordinary cost path does not sample patron employer/factor");
          if (i == 6) Check(context.order_title_holder_id == 0U, "legal zero holder preserved");
          if (i == 5 || i == 7) Check(!context.order_title_holder_id && context.title_holder_is_player == false,
                                    "stale/sentinel resolves actual canonical fallback holder");
        }
      }
      xar::ck3_12003::PlayerHolyOrderMailboxContext12003 query;
      query.observation = std::move(observation); query.completed = true;
      query.envelope.frame_stable = true;
      query.envelope.expected_snapshot_revision = 170 + static_cast<std::uint64_t>(sample);
      query.envelope.expected_snapshot.date_raw = date;
      const auto wire = xar::ck3_12003::SerializePlayerHolyOrderContextResult12003(
          query, "g2-read-holycost-" + std::to_string(sample));
      Check(!wire.empty(), "actual production command_result serializer");
      if (sample != 0) samples += ',';
      samples += wire;
    }
    samples += "]}";
    if (argc > 1) { std::ofstream out(argv[1]); out << samples << '\n'; }
    std::cout << "GREEN holy-order hire cost context checks=" << checks << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n'; return 1;
  }
}
