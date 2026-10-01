#include "xar_bridge/religion_reform12002_costs.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

using namespace xar::ck3_12002::religion_reform;
namespace {
std::array<std::byte, 0xD0> window{};
std::int64_t price = 0, missing = 0;
bool edit = false, fail_price = false, fail_missing = false;
int calls = 0, price_drift = 0, missing_drift = 0, edit_calls = 0;
bool actor_drift = false, rite_drift = false, edit_drift = false;
unsigned checks = 0;
template <typename T> void Put(std::size_t off, T v) {
  std::memcpy(window.data() + off, &v, sizeof(v));
}
void Check(bool pass, const char *why) {
  ++checks;
  if (!pass) throw std::runtime_error(why);
}
std::int64_t *Price(void *p, std::int64_t *out) {
  Check(p == window.data(), "actual window must be forwarded");
  ++calls;
  *out = price + ((calls > 1) ? price_drift : 0);
  if (actor_drift) Put(kRiteCreationActorOffset, std::int32_t{8});
  if (rite_drift) Put(kRiteCreationSourceRiteOffset, std::uint32_t{5});
  return fail_price ? nullptr : out;
}
std::int64_t *Missing(void *p, std::int64_t *out) {
  Check(p == window.data(), "native missing window must be forwarded");
  *out = missing + ((calls > 1) ? missing_drift : 0);
  return fail_missing ? nullptr : out;
}
bool Editing(void *p) {
  Check(p == window.data(), "native edit window must be forwarded");
  ++edit_calls;
  return edit_drift && edit_calls > 1 ? !edit : edit;
}
void Reset() {
  window = {};
  Put(kRiteCreationActorOffset, std::int32_t{7});
  Put(kRiteCreationSourceRiteOffset, std::uint32_t{0});
  price = missing = 0;
  edit = fail_price = fail_missing = actor_drift = rite_drift = edit_drift = false;
  calls = price_drift = missing_drift = edit_calls = 0;
}
void Wire(const std::filesystem::path &out, const char *name, const CostQuote &q) {
  std::ofstream(out / (std::string(name) + ".json")) << SerializeCurrentRiteCreationCosts12002(q);
}
}
int main(int argc, char **argv) {
  try {
    if (argc != 2) throw std::runtime_error("expected output directory");
    const std::filesystem::path out = argv[1];
    CostBindings b{true, Price, Missing, Editing};
    CurrentDraftView v{window.data(), 7, 120, 53169072};
    CostQuote q{};
    Reset();
    Check(ReadCurrentRiteCreationCosts12002(b, v, q), "observed zero price");
    Check(q.piety_cost_raw == 0 && q.piety_missing_signed_raw == 0 &&
          q.source_rite_id == 0U && q.has_enough_piety == true, "zero semantics");
    Wire(out, "zero", q);
    Reset(); price = 250'000'000; missing = -175'500'000; edit = true;
    Put(kRiteCreationSourceRiteOffset, std::uint32_t{0x84000005U});
    Check(ReadCurrentRiteCreationCosts12002(b, v, q), "owned rite edit quote");
    Check(q.editing_owned_current_rite == true && q.source_rite_id == 0x84000005U &&
          q.piety_missing_signed_raw == -175'500'000 && q.has_enough_piety == true,
          "preserve negative budget difference and generation");
    Wire(out, "editing-affordable", q);
    Reset(); price = 100'000; missing = 1;
    Check(ReadCurrentRiteCreationCosts12002(b, v, q) && q.has_enough_piety == false,
          "positive missing is unaffordable");
    Wire(out, "missing-piety", q);
    Reset(); Put(kRiteCreationSourceRiteOffset, std::uint32_t{0xFFFFFFFFU});
    Check(ReadCurrentRiteCreationCosts12002(b, v, q) && !q.source_rite_id,
          "absent source is not zero ref");
    Wire(out, "absent-source", q);
    Reset(); fail_price = true;
    Check(!ReadCurrentRiteCreationCosts12002(b, v, q) &&
          q.failure == CostFailure::native_quote_unavailable && !q.piety_cost_raw,
          "native quote failure is unavailable");
    Wire(out, "native-unavailable", q);
    Reset(); fail_missing = true;
    Check(!ReadCurrentRiteCreationCosts12002(b, v, q) && !q.piety_missing_signed_raw,
          "native missing failure is unavailable");
    Reset(); auto absent = v; absent.window = nullptr;
    Check(!ReadCurrentRiteCreationCosts12002(b, absent, q) &&
          q.failure == CostFailure::draft_unavailable && calls == 0,
          "no window must not manufacture a quote");
    Wire(out, "no-draft", q);
    Reset(); auto other = v; other.played_character_id = 8;
    Check(!ReadCurrentRiteCreationCosts12002(b, other, q) &&
          q.failure == CostFailure::draft_actor_mismatch && calls == 0,
          "other actor draft must not become player quote");
    Reset(); price_drift = 1;
    Check(!ReadCurrentRiteCreationCosts12002(b, v, q) && q.failure == CostFailure::quote_changed,
          "price drift is observable");
    Reset(); missing_drift = -1;
    Check(!ReadCurrentRiteCreationCosts12002(b, v, q) && q.failure == CostFailure::quote_changed,
          "budget drift is observable");
    Reset(); actor_drift = true;
    Check(!ReadCurrentRiteCreationCosts12002(b, v, q) && q.failure == CostFailure::quote_changed,
          "actor drift is observable");
    Reset(); rite_drift = true;
    Check(!ReadCurrentRiteCreationCosts12002(b, v, q) && q.failure == CostFailure::quote_changed,
          "rite drift is observable");
    Reset(); edit_drift = true;
    Check(!ReadCurrentRiteCreationCosts12002(b, v, q) && q.failure == CostFailure::quote_changed,
          "pricing mode drift is observable");
    const auto bound = BindRiteCreationCostsImage12002(0x140000000,
                                                     xar::ck3_12002::kExecutableSha256);
    Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.piety_cost) ==
          0x140000000 + kRiteCreationPietyCostRva, "exact native cost binding");
    Check(!BindRiteCreationCostsImage12002(0x140000000, "wrong-build").enabled,
          "different image is not rebound as this build");
    Check(!BindRiteCreationCostsImage12002(0, xar::ck3_12002::kExecutableSha256).enabled,
          "zero image has no native quote");
    std::cout << "PASS checks=" << checks << " actual_wire_cases=6\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
