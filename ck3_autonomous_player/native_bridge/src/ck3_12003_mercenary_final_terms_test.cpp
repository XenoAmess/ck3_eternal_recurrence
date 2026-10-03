#include "xar_bridge/ck3_12003_mercenary_final_terms.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace merc = xar::ck3_12003::mercenary;
namespace {
int checks = 0, hire_calls = 0, cost_calls = 0, payment_calls = 0;
int afford_calls = 0, duration_calls = 0, destroyed = 0, scenario = 0;
void *current_player = nullptr, *current_company = nullptr;
std::int32_t expected_quote_input = 0;
void Require(bool condition, const char *reason) {
  ++checks;
  if (!condition) throw std::runtime_error(reason);
}
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
void Reason(void *sink, std::string_view text) {
  Require(Get<std::size_t>(sink, 0x10) == 0 &&
      Get<std::size_t>(sink, 0x18) == 15, "canonical native reason empty state");
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
void Destroy(void *sink) {
  ++destroyed;
  if (Get<std::size_t>(sink, 0x18) >= 16)
    delete[] Get<char *>(sink, 0);
}
void Actors(void *company, void *actor) {
  Require(company == current_company && actor == current_player,
          "native terms receive supplied current actor and company");
}
bool CanHire(void *company, void *actor, std::uint32_t mode, void *sink) {
  ++hire_calls;
  Actors(company, actor);
  Require(mode == 1, "normal hire uses native mode 1");
  Reason(sink, scenario == 0 ? "" : "Already hired");
  return scenario == 0;
}
std::int64_t *Cost(void *company, std::int64_t *out, void *actor,
                   std::int32_t current_value) {
  ++cost_calls;
  Actors(company, actor);
  Require(current_value == expected_quote_input,
          "quote receives native current landstate value");
  const std::array<std::int64_t, 10> values = scenario == 0 ?
      std::array<std::int64_t, 10>{12500000, -50000, 2, 3, 4, 5, 6, 7, 8, 9} :
      scenario == 1 ? std::array<std::int64_t, 10>{0, 0, 0, 0, 0, 0, 7900000, 0, 0, 0} :
      std::array<std::int64_t, 10>{0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  std::memcpy(out, values.data(), sizeof(values));
  return out;
}
std::int32_t Payment(void *company, void *actor, std::uint32_t mode) {
  ++payment_calls;
  Actors(company, actor);
  Require(mode == 1, "payment evaluation uses native mode 1");
  return scenario == 0 ? 1 : scenario == 1 ? 0 : 2;
}
bool CanAfford(const std::int64_t *cost, void *actor, void *sink) {
  ++afford_calls;
  Require(actor == current_player, "full-cost predicate receives current actor");
  if (scenario == 0) {
    Require(cost[0] == 12500000 && cost[1] == -50000 && cost[9] == 9,
            "full signed ten-resource evaluated cost passed to native predicate");
    Reason(sink, "\x15X Not enough gold\x15!\nQuoted \"cost\"");
  } else if (scenario == 1) {
    Require(cost[0] == 0 && cost[6] == 7900000, "treasury slot not relabeled gold");
    Reason(sink, "Treasury low");
  } else {
    Require(cost[0] == 0 && cost[6] == 0 && cost[9] == 0,
            "evaluated zero vector remains available");
    Reason(sink, "");
  }
  return scenario == 2;
}
std::int64_t Duration(void *company, void *actor) {
  ++duration_calls;
  Actors(company, actor);
  return scenario == 0 ? 47 : scenario == 1 ? 23 : 11;
}
} // namespace

int main(int argc, char **argv) {
  try {
    alignas(8) std::array<std::byte, 0x1C8> player{};
    alignas(8) std::array<std::byte, 0x1D8> landstate{};
    alignas(8) std::array<std::byte, 0x20> company{};
    current_player = player.data();
    current_company = company.data();
    Put(player.data(), 0x18, std::int32_t{29829});
    Put(player.data(), 0x1C0, static_cast<const void *>(landstate.data()));
    expected_quote_input = -4;
    Put(landstate.data(), 0x1D0, expected_quote_input);
    merc::FinalTermsBindings bindings{true, &CanHire, &Cost, &Payment,
        &CanAfford, &Duration, &Destroy};
    merc::FinalTerms debt{};
    Require(merc::ReadMercenaryFinalTerms12003(bindings, current_company,
        current_player, debt), "new production terms reader succeeds for native debt permission");
    Require(debt.can_hire == true && debt.can_afford == false &&
        debt.payment_status == 1, "native allowed debt never overwritten by generic affordability");
    Require(debt.hire_duration_months == 47, "actual current contract months survive without stock substitution");
    Require(debt.resource_costs_raw && (*debt.resource_costs_raw)[0] == 12500000 &&
        (*debt.resource_costs_raw)[1] == -50000 && (*debt.resource_costs_raw)[9] == 9,
        "every signed evaluated resource slot survives");
    Require(debt.can_hire_reason_literal == "" &&
        debt.can_afford_reason_literal == "\x15X Not enough gold\x15!\nQuoted \"cost\"" &&
        destroyed == 2, "owned inline and heap reasons copied before destruction");
    const auto debt_json = merc::SerializeMercenaryFinalTerms12003(debt);
    Require(debt_json.find("\"can_hire\":true") != std::string::npos &&
        debt_json.find("\"can_afford\":false") != std::string::npos &&
        debt_json.find("\\u0015X") != std::string::npos &&
        debt_json.find("\\u000aQuoted \\\"cost\\\"") != std::string::npos,
        "production terms serializer preserves predicates and literal native controls");
    scenario = 1;
    expected_quote_input = 0;
    Put<const void *>(player.data(), 0x1C0, nullptr);
    merc::FinalTerms treasury{};
    Require(merc::ReadMercenaryFinalTerms12003(bindings, current_company,
        current_player, treasury), "absent landstate follows actual callback zero argument");
    Require(treasury.can_hire == false && treasury.can_afford == false &&
        treasury.payment_status == 0 && treasury.hire_duration_months == 23 &&
        (*treasury.resource_costs_raw)[6] == 7900000 &&
        treasury.can_hire_reason_literal == "Already hired", "native denied hire and treasury quote independently preserved");
    scenario = 2;
    merc::FinalTerms zero{};
    Require(merc::ReadMercenaryFinalTerms12003(bindings, current_company,
        current_player, zero), "evaluated zero quote is available");
    Require(zero.can_hire == false && zero.can_afford == true &&
        zero.payment_status == 2 && zero.hire_duration_months == 11 &&
        zero.can_afford_reason_literal == "", "full funds and denied hire remain distinct");
    Require(hire_calls == 3 && cost_calls == 3 && payment_calls == 3 &&
        afford_calls == 3 && duration_calls == 3 && destroyed == 6,
        "only new production module called once per sample; all owned reasons released");
    if (argc > 1) {
      std::ofstream out(argv[1], std::ios::binary);
      out << "[" << debt_json << ',' << merc::SerializeMercenaryFinalTerms12003(treasury)
          << ',' << merc::SerializeMercenaryFinalTerms12003(zero) << "]\n";
      Require(out.good(), "new production serialized fixture artifact written");
    }
    std::cout << "{\"status\":\"GREEN\",\"checks\":" << checks
        << ",\"production_reader_calls\":3,\"scenarios\":3,\"destroyed_reasons\":6}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
