#include "xar_bridge/ck3_12003_holy_order_hire_action.hpp"
#include "xar_bridge/ck3_12003_holy_order_hire_wire.hpp"

#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <vector>

namespace holy = xar::ck3_12003::religion::holy_order;
namespace {
int checks = 0;
void Require(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
template <typename T> void Put(void *p, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *p, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value));
  return value;
}
struct Fixture;
Fixture *fixture = nullptr;
void *Patron(void *);
bool IsMilitary(void *);
bool CanHire(void *, void *, void *);
std::int64_t *Cost(void *, std::int64_t *, void *);
bool CanAfford(const std::int64_t *, void *, void *);
void ReasonDestroy(void *);
std::int32_t Soldiers(void *);
bool Validate(const void *, void *);
void **Clone(const void *, void **);
void *Delete(void *, std::uint32_t);
bool Queue(void *, void **, std::uint32_t);

struct Fixture {
  alignas(8) std::array<std::byte, 0x30> actor{}, manager{};
  alignas(8) std::array<std::byte, 0x90> order{}, fallback{};
  alignas(8) std::array<std::byte, 0x30> entries{};
  std::array<std::uintptr_t, 9> primary{};
  std::array<std::uintptr_t, 1> secondary{};
  void *manager_pointer = manager.data(), *fallback_pointer = fallback.data();
  std::uint32_t order_id = 0x81000003U;
  bool can_hire = true, can_afford = true, command_valid = true;
  bool military = true, queue_accepts = true;
  int validations = 0, clones = 0, queues = 0, deletes = 0;
  holy::HireActionBindings bindings{};
  Fixture() {
    fixture = this;
    Put(actor.data(), 0x18, std::int32_t{29829});
    Put(order.data(), 0x10, order_id);
    Put(order.data(), 0x14, std::uint32_t{0x486F4F72U});
    Put(order.data(), 0x24, std::uint32_t{0xA1000002U});
    Put(order.data(), 0x40, UINT32_MAX);
    Put(order.data(), 0x80, UINT32_MAX);
    Put(manager.data(), 0x20, static_cast<const void *>(entries.data()));
    Put(manager.data(), 0x2C, std::int32_t{3});
    // A real manager hole and fallback precede the selected organisation.
    Put(entries.data(), 0x18, fallback_pointer);
    Put(entries.data(), 0x28, static_cast<void *>(order.data()));
    primary[0] = reinterpret_cast<std::uintptr_t>(&Delete);
    primary[8] = reinterpret_cast<std::uintptr_t>(&Clone);
    bindings.enabled = true;
    bindings.context = {true, &manager_pointer, &fallback_pointer, &Patron,
        &IsMilitary, &CanHire, &Cost, &CanAfford, &ReasonDestroy, &Soldiers};
    bindings.commands.enabled = true;
    bindings.commands.command_manager = this;
    bindings.commands.queue_owned_command = &Queue;
    bindings.primary_vtable = reinterpret_cast<std::uintptr_t>(primary.data());
    bindings.secondary_vtable = reinterpret_cast<std::uintptr_t>(secondary.data());
    bindings.validate_source = &Validate;
  }
};
void Reason(void *sink, std::string_view value) {
  Require(sink && value.size() <= 15 && Get<std::size_t>(sink, 0x18) == 15,
          "existing native small-string reason ABI");
  std::memcpy(sink, value.data(), value.size());
  Put(sink, 0x10, value.size());
}
void *Patron(void *) { return nullptr; }
bool IsMilitary(void *) { return fixture->military; }
bool CanHire(void *order, void *actor, void *reason) {
  Require(order == fixture->order.data() && actor == fixture->actor.data(),
          "native hire getter receives actual player and manager order");
  Reason(reason, fixture->can_hire ? "" : "Requires war");
  return fixture->can_hire;
}
std::int64_t *Cost(void *, std::int64_t *cost, void *) {
  cost[0] = 250000; cost[2] = 100000;
  return cost;
}
bool CanAfford(const std::int64_t *, void *, void *reason) {
  Reason(reason, fixture->can_afford ? "" : "Not enough gold");
  return fixture->can_afford;
}
void ReasonDestroy(void *) {}
std::int32_t Soldiers(void *) { return 2200; }
void CheckSource(const void *opaque) {
  const auto &source = *static_cast<const holy::HireMode3Source *>(opaque);
  Require(source.primary_vtable == fixture->bindings.primary_vtable &&
      source.secondary_vtable == fixture->bindings.secondary_vtable &&
      source.played_character_full_id == 29829U &&
      source.holy_order_full_id == fixture->order_id && source.mode == 3 &&
      source.metadata_byte == 0 && source.metadata_word_0 == 0 &&
      source.metadata_word_1 == 0 && source.metadata_word_2 == 0,
      "exact inline source preserves full IDs, ordinary mode3, zero metadata and interfaces");
}
bool Validate(const void *source, void *reason) {
  ++fixture->validations;
  Require(reason == nullptr, "native CanExecute uses supported null reason");
  CheckSource(source);
  return fixture->command_valid;
}
void **Clone(const void *source, void **storage) {
  ++fixture->clones;
  CheckSource(source);
  *storage = new holy::HireMode3Source(*static_cast<const holy::HireMode3Source *>(source));
  return storage;
}
void *Delete(void *source, std::uint32_t flags) {
  Require(flags == 1, "native clone deleting destructor owns one allocation");
  ++fixture->deletes;
  delete static_cast<holy::HireMode3Source *>(source);
  return nullptr;
}
bool Queue(void *manager, void **source, std::uint32_t flags) {
  ++fixture->queues;
  Require(manager == fixture && flags == 0x0E && source && *source,
          "production SubmitCommandCopy passes one owning pointer and native flags0x0E");
  CheckSource(*source);
  if (fixture->queue_accepts) { Delete(*source, 1); *source = nullptr; }
  return fixture->queue_accepts;
}
}

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "output genuine production wire fixture path");
    xar::ck3_12003::HolyOrderHireRequestV1 request{};
    Require(xar::ck3_12003::ParseHolyOrderHireRequestV1(
        xar::ck3_12003::kHolyOrderHireStepV1,
        "{\"holy_order_id\":2164260867,\"expected_revision\":141}", request) &&
        request.holy_order_id == 0x81000003U && request.expected_revision == 141,
        "typed parser preserves generation-bearing full order reference");
    std::vector<std::pair<std::string, std::string>> wires;
    for (int scenario = 0; scenario != 8; ++scenario) {
      Fixture current;
      if (scenario == 1) current.can_hire = false;
      if (scenario == 2) current.command_valid = false;
      if (scenario == 3) Put(current.order.data(), 0x80, std::uint32_t{29829});
      if (scenario == 4) current.queue_accepts = false;
      if (scenario == 5) current.military = false;
      if (scenario == 6) { current.order_id = 0; Put(current.order.data(), 0x10, current.order_id); }
      // Separate CanAfford is retained; command CanExecute stays authoritative.
      if (scenario == 7) current.can_afford = false;
      holy::HireActionResult result{};
      const auto status = holy::ApplyHolyOrderHire12003(current.bindings,
          current.actor.data(), 29829, current.order_id, 53240904, 19, result);
      const bool submitted = scenario == 0 || scenario == 6 || scenario == 7;
      Require(status == (submitted ? holy::HireActionStatus::submitted :
          scenario == 3 ? holy::HireActionStatus::already_hired : holy::HireActionStatus::rejected),
          "provider reports native eligibility, existing employer and native queue outcomes");
      Require(result.command_submitted == submitted && result.verification_pending == submitted,
          "only queue acceptance produces pending submission");
      Require(current.clones == (submitted || scenario == 4 ? 1 : 0) &&
          current.queues == current.clones && current.deletes == current.clones,
          "production clone/submit owns exactly one copy and destroys no stack source");
      Require(result.prior_context.rows.size() == 1 && result.holy_order_resolved &&
          result.prior_context.rows[0].holy_order_id == current.order_id,
          "existing native context supplies selected full identity and independent terms");
      if (scenario == 7)
        Require(result.prior_context.rows[0].military_terms->can_afford == false &&
            result.prior_context.rows[0].military_terms->can_afford_reason_literal == "Not enough gold",
            "native affordability remains a literal observation independent of CanExecute");
      wires.emplace_back("scenario" + std::to_string(scenario),
          xar::ck3_12003::SerializeHolyOrderHireResultV1(result, "holy-hire-fixture",
              static_cast<std::uint64_t>(scenario + 1), 141, 53240904));
    }
    std::ofstream output(argv[1], std::ios::binary);
    output << '{';
    for (std::size_t i = 0; i < wires.size(); ++i) {
      if (i) output << ',';
      output << '"' << wires[i].first << "\":" << wires[i].second;
    }
    output << "}\n";
    Require(output.good(), "fixture writes genuine serializer command_result bytes");
    std::cout << "{\"status\":\"GREEN\",\"scenarios\":8,\"checks\":" << checks
              << ",\"synthetic_fixture\":true,\"live\":false}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
