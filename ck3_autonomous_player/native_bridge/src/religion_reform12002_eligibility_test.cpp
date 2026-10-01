#include "xar_bridge/religion_reform12002_eligibility.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace {
using namespace xar::ck3_12002::religion_reform;
std::array<std::byte, 0x1040> window{};
bool create_value = false;
bool edit_value = false;
bool mutate_actor = false;
unsigned calls = 0;
unsigned checks = 0;

void SetActor(std::uint32_t actor) {
  std::memcpy(window.data() + kCreationWindowActorIdOffset, &actor, sizeof(actor));
}
bool Create(const void *actual_window, void *reason) {
  if (actual_window != window.data() || reason != nullptr) std::abort();
  ++calls;
  return create_value;
}
bool Edit(const void *actual_window, void *reason) {
  if (actual_window != window.data() || reason != nullptr) std::abort();
  ++calls;
  if (mutate_actor) SetActor(7);
  return edit_value;
}
void Check(bool value, const char *label) {
  ++checks;
  if (!value) {
    std::cerr << "FAIL " << label << '\n';
    std::exit(1);
  }
}
void Wire(const std::filesystem::path &path, const char *name,
          const DraftEligibility &out) {
  std::ofstream(path / (std::string(name) + ".json")) <<
      SerializeDraftEligibility12002(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path output = argv[1];
  std::filesystem::create_directories(output);
  const EligibilityBindings bindings{true, &Create, &Edit};
  constexpr std::uint32_t actor = 0x84000005U;
  SetActor(actor);
  DraftEligibility out{};
  Check(ReadCurrentDraftEligibility12002(bindings, window.data(), actor, out),
        "native negative is observed");
  Check(out.can_create_rite == false && out.can_edit_rite == false,
        "false is not unavailable");
  Check(out.draft_actor_id == actor && calls == 2, "full actor ID and callbacks");
  Wire(output, "observed-negative", out);
  create_value = true;
  Check(ReadCurrentDraftEligibility12002(bindings, window.data(), actor, out),
        "current draft positive");
  Check(out.can_create_rite == true && out.can_edit_rite == false,
        "create and edit are independent native results");
  Wire(output, "create-positive", out);
  create_value = false;
  edit_value = true;
  Check(ReadCurrentDraftEligibility12002(bindings, window.data(), actor, out) &&
            out.can_create_rite == false && out.can_edit_rite == true,
        "edit positive");
  Wire(output, "edit-positive", out);
  const auto before = calls;
  Check(!ReadCurrentDraftEligibility12002(bindings, window.data(), 5, out) &&
            out.failure == EligibilityFailure::draft_actor_mismatch && calls == before,
        "generation mismatch does not call native gate");
  Wire(output, "actor-mismatch", out);
  Check(!ReadCurrentDraftEligibility12002(bindings, nullptr, actor, out) &&
            out.failure == EligibilityFailure::current_window_unavailable,
        "missing current draft is unavailable");
  Check(!out.can_create_rite && !out.can_edit_rite,
        "no stale native results on missing draft");
  Wire(output, "window-unavailable", out);
  Check(!ReadCurrentDraftEligibility12002(bindings, window.data(), 0xFFFFFFFFU, out) &&
            out.failure == EligibilityFailure::played_character_unavailable,
        "absent actual player");
  EligibilityBindings missing = bindings;
  missing.can_create_rite = nullptr;
  Check(!ReadCurrentDraftEligibility12002(missing, window.data(), actor, out) &&
            out.failure == EligibilityFailure::bindings_unavailable,
        "missing native callable");
  mutate_actor = true;
  Check(!ReadCurrentDraftEligibility12002(bindings, window.data(), actor, out) &&
            out.failure == EligibilityFailure::draft_actor_changed,
        "actual window subject change");
  Check(!out.can_create_rite && !out.can_edit_rite,
        "drift discards gate values");
  Wire(output, "actor-changed", out);
  Check(!BindEligibilityImage12002(0x140000000U, "wrong").enabled,
        "version binding");
  Check(!BindEligibilityImage12002(0, xar::ck3_12002::kExecutableSha256).enabled,
        "no module binding");
  const auto native = BindEligibilityImage12002(0x140000000U,
                                               xar::ck3_12002::kExecutableSha256);
  Check(native.enabled && reinterpret_cast<std::uintptr_t>(native.can_create_rite) ==
            0x140000000U + kCanCreateRiteCoreRva &&
            reinterpret_cast<std::uintptr_t>(native.can_edit_rite) ==
            0x140000000U + kCanEditRiteCoreRva,
        "exact actual source addresses");
  std::cout << "PASS checks=" << checks << " actual_wire_cases=6\n";
  return 0;
}
