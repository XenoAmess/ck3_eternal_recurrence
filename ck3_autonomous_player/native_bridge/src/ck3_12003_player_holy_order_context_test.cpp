#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"
#if defined(XAR_HOLY_ORDER_PRODUCE_WIRE)
#include "xar_bridge/ck3_12003_player_holy_order_mailbox.hpp"
#endif

#include <array>
#include <cstddef>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace holy = xar::ck3_12003::religion::holy_order;
namespace {
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
int checks = 0, military_calls = 0, patron_calls = 0;
int hire_calls = 0, cost_calls = 0, afford_calls = 0, destroyed = 0;
void *first_order = nullptr, *second_order = nullptr;
void *nonmilitary_order = nullptr, *played = nullptr, *dynamic_patron = nullptr;
void Check(bool condition, const char *reason) {
  ++checks;
  if (!condition) throw std::runtime_error(reason);
}
void WriteReason(void *sink, std::string_view text) {
  Check(Get<std::size_t>(sink, 0x10) == 0 &&
      Get<std::size_t>(sink, 0x18) == 15, "canonical native string empty state");
  if (text.size() <= 15) {
    std::memcpy(sink, text.data(), text.size());
    Put<char>(sink, text.size(), '\0');
  } else {
    auto *heap = new char[text.size() + 1];
    std::memcpy(heap, text.data(), text.size());
    heap[text.size()] = '\0';
    Put<char *>(sink, 0, heap);
    Put<std::size_t>(sink, 0x18, text.size());
  }
  Put<std::size_t>(sink, 0x10, text.size());
}
void ReasonDestroy(void *sink) {
  ++destroyed;
  if (Get<std::size_t>(sink, 0x18) >= 16)
    delete[] Get<char *>(sink, 0);
}
void *Patron(void *order) {
  ++patron_calls;
  return order == first_order ? dynamic_patron : nullptr;
}
bool IsMilitary(void *order) {
  ++military_calls;
  return order != nonmilitary_order;
}
bool CanHire(void *order, void *actor, void *reason) {
  ++hire_calls;
  Check(actor == played, "CanHire receives exact played character");
  WriteReason(reason, order == first_order ? "Requires \"war\"\n" : "Not enough piety for hire");
  return false;
}
std::int64_t *Cost(void *order, std::int64_t *out, void *actor) {
  ++cost_calls;
  Check(actor == played, "Cost receives exact played character");
  const std::array<std::int64_t, 10> values = order == first_order ?
      std::array<std::int64_t, 10>{14250000, -50000, 0, 11, 12, 13, 14, 15, 16, 17} :
      std::array<std::int64_t, 10>{0, 0, 30000000, 0, 0, 0, 0, 0, 0, 0};
  std::memcpy(out, values.data(), sizeof(values));
  return out;
}
bool CanAfford(const std::int64_t *cost, void *actor, void *reason) {
  ++afford_calls;
  Check(actor == played, "CanAfford receives exact played character");
  if (cost[0] == 14250000) {
    WriteReason(reason, "");
    return true;
  }
  WriteReason(reason, "\x15Z Not enough piety\x15!");
  return false;
}
void InitOrder(void *order, std::uint32_t id, std::uint32_t rite,
               std::uint32_t founder, std::uint32_t employer,
               const void *leases, std::int32_t lease_count) {
  Put(order, 0x10, id);
  Put(order, 0x14, std::uint32_t{0x486F4F72});
  Put(order, 0x24, rite);
  Put(order, 0x40, founder);
  Put(order, 0x80, employer);
  Put(order, 0x50, leases);
  Put(order, 0x5C, lease_count);
}
} // namespace

int main(int argc, char **argv) {
  try {
    constexpr std::int32_t actor = 29829, date = 53234568;
    constexpr std::uint64_t epoch = 17985;
    alignas(8) std::array<std::byte, 0x30> player{}, patron{}, manager{};
    alignas(8) std::array<std::byte, 0x90> military{}, second_military{}, nonmilitary{}, fallback{};
    alignas(8) std::array<std::byte, 0x50> entries{};
    const std::array<std::uint32_t, 3> leases{0x12000001U, 0xA0000015U, 0U};
    Put(player.data(), 0x18, actor);
    Put(patron.data(), 0x18, std::uint32_t{0x7FFFFFF0U});
    played = player.data();
    dynamic_patron = patron.data();
    first_order = military.data();
    second_order = second_military.data();
    nonmilitary_order = nonmilitary.data();
    InitOrder(first_order, 0x81000003U, 0x11000002U, 4242U, UINT32_MAX,
              leases.data(), static_cast<std::int32_t>(leases.size()));
    InitOrder(nonmilitary_order, 0xFE00000CU, 0U, UINT32_MAX, 0U, nullptr, 0);
    InitOrder(second_order, 0x23000009U, 0x11000002U, UINT32_MAX, 37333U, nullptr, 0);
    void *manager_pointer = manager.data(), *fallback_pointer = fallback.data();
    Put(manager.data(), 0x20, static_cast<const void *>(entries.data()));
    Put(manager.data(), 0x2C, std::int32_t{5});
    Put(entries.data(), 0x08, first_order);
    // Slot 1 is a real NULL hole, not the end of the live range.
    Put(entries.data(), 0x28, nonmilitary_order);
    Put(entries.data(), 0x38, fallback_pointer);
    Put(entries.data(), 0x48, second_order);
    holy::Bindings bindings{true, &manager_pointer, &fallback_pointer,
        &Patron, &IsMilitary, &CanHire, &Cost, &CanAfford, &ReasonDestroy};
    holy::Context current{};
    Check(holy::ReadPlayerHolyOrderContext12003(bindings, played, actor, date, epoch, current),
          "production reader succeeds");
#if defined(XAR_HOLY_ORDER_PRODUCE_WIRE)
    if (argc > 1 && std::string_view(argv[1]) == "--wire-only") {
      xar::ck3_12003::PlayerHolyOrderMailboxContext12003 query{};
      query.observation = std::move(current);
      query.completed = true;
      query.envelope.frame_stable = true;
      query.envelope.expected_snapshot_revision = 154;
      query.envelope.expected_snapshot.date_raw = date;
      const auto wire = xar::ck3_12003::SerializePlayerHolyOrderContextResult12003(
          query, "g2-read-holyorder-fixture");
      if (wire.empty()) throw std::runtime_error("production wire empty");
      std::cout << wire << '\n';
      std::cerr << "GREEN new production wire only; existing 32 reader checks reused\n";
      return 0;
    }
#endif
    Check(current.available && current.unavailable_reason.empty(), "collection available");
    Check(current.rows.size() == 3, "range bound visits all real entries and skips holes/fallback");
    Check(current.capture_epoch == epoch && current.date_raw == date &&
          current.played_character_id == actor, "frame identity survives");
    const auto &first = current.rows[0];
    Check(first.holy_order_id == 0x81000003U && first.rite_id == 0x11000002U,
          "full generation-bearing organisation and rite IDs survive");
    Check(first.founder_id == 4242U && first.patron_id == 0x7FFFFFF0U &&
          !first.employer_id, "dynamic patron differs from founder; absent employer null");
    Check(first.leased_title_ids == std::vector<std::uint32_t>(leases.begin(), leases.end()),
          "complete generation-bearing leases including legal zero survive");
    Check(first.military_terms.has_value() && first.military_terms->available,
          "military terms available");
    const auto &terms = *first.military_terms;
    Check(terms.can_hire == false && terms.can_afford == true,
          "final hire legality differs from affordability");
    Check(terms.resource_costs_raw.has_value() && terms.resource_costs_raw->size() == 10 &&
          (*terms.resource_costs_raw)[0] == 14250000 &&
          (*terms.resource_costs_raw)[1] == -50000 &&
          (*terms.resource_costs_raw)[9] == 17, "signed ten-slot fixed costs survive");
    Check(terms.can_hire_reasons_available &&
          terms.can_hire_reason_literal == "Requires \"war\"\n" &&
          terms.can_afford_reasons_available && terms.can_afford_reason_literal == "",
          "two literal reason sinks preserve text and legal empty reason");
    const auto &nonmil = current.rows[1];
    Check(nonmil.holy_order_id == 0xFE00000CU && nonmil.rite_id == 0 &&
          !nonmil.is_military && !nonmil.military_terms, "nonmilitary terms inapplicable");
    Check(!nonmil.founder_id && !nonmil.patron_id && nonmil.employer_id == 0U &&
          nonmil.leased_title_ids.empty(), "nullable identities distinguish legal zero");
    Check(current.rows[2].military_terms->can_afford == false &&
          current.rows[2].military_terms->can_afford_reason_literal ==
              "\x15Z Not enough piety\x15!", "affordability false retains native reason");
    Check(military_calls == 3 && patron_calls == 3 && hire_calls == 2 &&
          cost_calls == 2 && afford_calls == 2 && destroyed == 4,
          "each military item evaluated once; owned native reason sinks destroyed");
    const auto current_json = holy::SerializePlayerHolyOrderContext12003(current);
    Check(current_json.find("\"military_terms\":null") != std::string::npos &&
          current_json.find("\\u0015Z") != std::string::npos &&
          current_json.find("Requires \\\"war\\\"\\u000a") != std::string::npos,
          "production serializer preserves null and escapes native text");
    holy::Context empty{};
    entries.fill(std::byte{});
    Put(manager.data(), 0x2C, std::int32_t{5});
    Check(holy::ReadPlayerHolyOrderContext12003(bindings, played, actor, date, epoch, empty) &&
          empty.available && empty.rows.empty(), "legal manager empty live set remains available");
    const auto empty_json = holy::SerializePlayerHolyOrderContext12003(empty);
    Check(empty_json.find("\"rows\":[]") != std::string::npos &&
          empty_json.find("\"available\":true") != std::string::npos,
          "empty actual collection serializer");
    holy::Context unavailable{};
    manager_pointer = nullptr;
    Check(!holy::ReadPlayerHolyOrderContext12003(bindings, played, actor, date, epoch, unavailable) &&
          unavailable.unavailable_reason == "holy_order_manager_unavailable",
          "missing manager is unavailable, not known empty");
    Check(!holy::BindPlayerHolyOrderImage12003(0x140000000ULL, "old-sha").enabled,
          "exact build admission");
    if (argc > 1) {
      std::ofstream out(argv[1], std::ios::binary);
      out << current_json << '\n';
      Check(out.good(), "write native current serializer artifact");
    }
    if (argc > 2) {
      std::ofstream out(argv[2], std::ios::binary);
      out << empty_json << '\n';
      Check(out.good(), "write native known-empty serializer artifact");
    }
    std::cerr << "GREEN " << checks << " checks; production reader and serializer; 3 scenarios\n";
    std::cout << current_json << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
