#include "xar_bridge/religion_reform12002_resource_costs.hpp"

#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace rr = xar::ck3_12002::religion_reform;
namespace {
int checks = 0;
void Expect(bool value, const char *name) {
  ++checks;
  if (!value) throw std::runtime_error(name);
}
struct Fixture {
  std::array<std::byte, 0x400> window{};
  std::int64_t price = 155'000'000;
  std::int64_t missing = 75'000'000;
  bool editing = false;
  int fixed_calls = 0;
  int edit_calls = 0;
};
static_assert(offsetof(Fixture, window) == 0);
std::int64_t *Price(void *window, std::int64_t *out) {
  auto &fixture = *static_cast<Fixture *>(window);
  ++fixture.fixed_calls;
  *out = fixture.price;
  return out;
}
std::int64_t *Missing(void *window, std::int64_t *out) {
  auto &fixture = *static_cast<Fixture *>(window);
  ++fixture.fixed_calls;
  *out = fixture.missing;
  return out;
}
bool Editing(void *window) {
  auto &fixture = *static_cast<Fixture *>(window);
  ++fixture.edit_calls;
  return fixture.editing;
}
void Wire(const std::filesystem::path &directory, const char *name,
          const rr::BaseResourceCostQuote &q) {
  std::ofstream output(directory / name, std::ios::binary);
  output << rr::SerializeCurrentRiteCreationBaseResourceCosts12002(q) << '\n';
  Expect(output.good(), "write actual C++ serialized wire");
}
} // namespace

int main(int argc, char **argv) {
  try {
    if (argc != 2) throw std::runtime_error("output directory required");
    const std::filesystem::path directory(argv[1]);
    Fixture fixture;
    const std::int32_t actor = 29829;
    const std::uint32_t rite = 0x84000005U;
    std::memcpy(fixture.window.data() + rr::kRiteCreationActorOffset, &actor, sizeof(actor));
    std::memcpy(fixture.window.data() + rr::kRiteCreationSourceRiteOffset, &rite, sizeof(rite));
    const auto original_window = fixture.window;
    rr::CostBindings bindings{true, Price, Missing, Editing};
    rr::CurrentDraftView view{fixture.window.data(), actor, 73, 53169072};
    rr::BaseResourceCostQuote quote;
    Expect(rr::ReadCurrentRiteCreationBaseResourceCosts12002(bindings, view, quote), "actual reader create quote");
    Expect(quote.draft_quote.piety_cost_raw == fixture.price, "native price retained");
    Expect(quote.draft_quote.piety_missing_signed_raw == fixture.missing, "signed native budget retained");
    Expect(quote.draft_quote.source_rite_id == rite && quote.draft_quote.capture_epoch == 73,
           "full-generation Rite and frame retained");
    Expect(fixture.fixed_calls == 4 && fixture.edit_calls == 2, "original CostReader really called");
    const std::array<std::int64_t, 10> expected{0, 0, 155'000'000, 0, 0, 0, 0, 0, 0, 0};
    Expect(quote.native_base_fee_slots_raw == expected, "exact command CCost draft base-fee contract");
    Expect(!quote.draft_quote.has_enough_piety.value(), "budget failure remains distinct from vector observation");
    Wire(directory, "create-missing-piety.json", quote);

    fixture.price = 0;
    fixture.missing = -175'500'000;
    fixture.editing = true;
    Expect(rr::ReadCurrentRiteCreationBaseResourceCosts12002(bindings, view, quote), "actual reader legitimate zero edit");
    Expect(quote.base_resource_cost_vector_observed && quote.native_base_fee_slots_raw.has_value(),
           "zero is observed data");
    Expect(quote.draft_quote.editing_owned_current_rite.value() &&
           quote.draft_quote.has_enough_piety.value() &&
           quote.draft_quote.piety_missing_signed_raw == -175'500'000,
           "edit and signed native affordability retained");
    Expect(fixture.window == original_window, "readers leave draft bytes unchanged");
    Wire(directory, "edit-zero.json", quote);

    bindings.enabled = false;
    Expect(!rr::ReadCurrentRiteCreationBaseResourceCosts12002(bindings, view, quote), "disabled quote unavailable");
    Expect(!quote.base_resource_cost_vector_observed && !quote.native_base_fee_slots_raw,
           "unavailable never manufactures zero vector");
    Expect(quote.draft_quote.failure == rr::CostFailure::bindings_unavailable,
           "original reader failure retained");
    Wire(directory, "bindings-unavailable.json", quote);
    std::cout << "PASS checks=" << checks << " actual_wire_cases=3\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
