#include "xar_bridge/government_runtime_adapter_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace observer = xar::bridge::private_observer;
using Status = observer::GovernmentRuntimeAdapterObservationStatusV1;
using Reason = observer::GovernmentRuntimeAdapterUnavailableReasonV1;
using Selection = observer::GovernmentRuntimeAdapterSelectionStatusV1;
using Feature = observer::GovernmentRuntimeFeatureInputV1;
using Input = observer::GovernmentRuntimeAdapterObserverInputV1;
using Result = observer::GovernmentRuntimeAdapterObserverResultV1;

std::vector<Feature> Features(std::span<const std::string_view> enabled) {
  const auto keys = observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1();
  std::vector<Feature> result;
  result.reserve(keys.size());
  for (std::size_t index = 0; index < keys.size(); ++index) {
    result.push_back(
        {static_cast<std::int32_t>(index), keys[index],
         std::find(enabled.begin(), enabled.end(), keys[index]) != enabled.end()});
  }
  return result;
}

std::int32_t EnabledCount(std::span<const Feature> features) {
  return static_cast<std::int32_t>(std::count_if(
      features.begin(), features.end(),
      [](const Feature &feature) { return feature.enabled; }));
}

Input AvailableInput(std::string_view government,
                     std::span<const std::string_view> flags,
                     std::span<const Feature> features,
                     std::span<const std::string_view> script_dlcs) {
  Input input{};
  input.exact_build_admitted = true;
  input.application_main = true;
  input.paused = true;
  input.state_identity_stable = true;
  input.frame = 690;
  input.player_character_id = 29'829;
  input.effective_government_stable_key = government;
  input.government_flags_available = true;
  input.government_flags = flags;
  input.feature_root_available = true;
  input.effective_feature_flags = features;
  input.enabled_feature_count = EnabledCount(features);
  input.script_dlc_set_available = true;
  input.script_dlc_keys = script_dlcs;
  return input;
}

const observer::GovernmentRuntimeProductIdentityV1 *Product(
    const Result &result, std::string_view key) {
  const auto found = std::find_if(
      result.runtime_products.begin(), result.runtime_products.end(),
      [key](const auto &product) { return product.script_dlc_key == key; });
  return found == result.runtime_products.end() ? nullptr : &*found;
}

bool TestCoreGovernmentIdentityGreen() {
  constexpr std::string_view enabled[]{"roads_to_power", "admin_gov"};
  const auto features = Features(enabled);
  constexpr std::string_view flags[]{
      "government_uses_domain_limit", "mod_added_runtime_flag",
      "government_is_feudal"};
  constexpr std::string_view dlcs[]{"Roads to Power", "A Royal Court"};
  const auto result = observer::EvaluateGovernmentRuntimeAdapterObserverV1(
      AvailableInput("feudal_government", flags, features, dlcs));
  const auto *rtp = Product(result, "Roads to Power");
  const auto *mpo = Product(result, "Khans of the Steppe");
  return result.status == Status::available && result.unavailable_reason == Reason::none &&
         result.player_character_id == std::optional<std::int32_t>{29'829} &&
         result.government.status == Status::available &&
         result.government.stable_key == "feudal_government" &&
         result.government.recognized_stock_key &&
         !result.government.religious_identity_opaque &&
         result.government.observed_flags.size() == 3 &&
         result.government.applicable_stock_flags ==
             std::vector<std::string>{"government_is_feudal",
                                      "government_uses_domain_limit"} &&
         result.effective_feature_flags.size() == 44 &&
         result.script_dlc_keys ==
             std::vector<std::string>{"A Royal Court", "Roads to Power"} &&
         rtp != nullptr && rtp->status == Status::available && mpo != nullptr &&
         mpo->status == Status::not_present &&
         result.entitlement_status == Status::unavailable &&
         result.entitlement_unavailable_reason ==
             Reason::store_verdict_provenance_unclosed &&
         result.adapter.status == Selection::core_supported &&
         result.adapter.family == std::optional<std::string>{"core_landed"} &&
         result.adapter.requirements_met;
}

bool TestDlcAdapterAndFeatureIdentity() {
  constexpr std::string_view enabled[]{"all_under_heaven", "merit_admin",
                                       "advanced_aspirations", "barter_troops"};
  const auto features = Features(enabled);
  constexpr std::string_view flags[]{"government_is_celestial",
                                     "government_has_merit"};
  constexpr std::string_view dlcs[]{"All Under Heaven"};
  const auto result = observer::EvaluateGovernmentRuntimeAdapterObserverV1(
      AvailableInput("celestial_government", flags, features, dlcs));
  const auto *product = Product(result, "All Under Heaven");
  return result.status == Status::available &&
         result.adapter.status == Selection::adapter_spec_ready_not_implemented &&
         result.adapter.family == std::optional<std::string>{"tgp_celestial"} &&
         result.adapter.required_effective_features ==
             std::vector<std::string>{"all_under_heaven"} &&
         result.adapter.capability_profile_features.size() == 4 &&
         result.adapter.requirements_met && product != nullptr &&
         product->status == Status::available;
}

bool TestFeatureMismatchIsTyped() {
  constexpr std::string_view enabled[]{"landless_playable"};
  const auto features = Features(enabled);
  constexpr std::string_view flags[]{"government_is_nomadic",
                                     "government_has_herd"};
  constexpr std::string_view dlcs[]{"Khans of the Steppe"};
  const auto result = observer::EvaluateGovernmentRuntimeAdapterObserverV1(
      AvailableInput("nomad_government", flags, features, dlcs));
  return result.status == Status::available &&
         result.government.status == Status::available &&
         result.adapter.status == Selection::unavailable_feature_mismatch &&
         !result.adapter.requirements_met;
}

bool TestUnknownGovernmentRetainsIdentity() {
  const auto features = Features(std::span<const std::string_view>{});
  constexpr std::string_view flags[]{"mod_flag_b", "mod_flag_a"};
  constexpr std::array<std::string_view, 0> dlcs{};
  const auto result = observer::EvaluateGovernmentRuntimeAdapterObserverV1(
      AvailableInput("modded_government", flags, features, dlcs));
  return result.status == Status::available &&
         result.government.stable_key == "modded_government" &&
         !result.government.recognized_stock_key &&
         result.government.observed_flags ==
             std::vector<std::string>{"mod_flag_a", "mod_flag_b"} &&
         result.government.applicable_stock_flags.empty() &&
         result.adapter.status == Selection::unadapted_runtime_government;
}

bool TestReligiousGovernmentIsOpaqueIdentityOnly() {
  const auto features = Features(std::span<const std::string_view>{});
  constexpr std::string_view flags[]{"government_is_theocracy",
                                     "government_is_settled"};
  constexpr std::array<std::string_view, 0> dlcs{};
  auto input = AvailableInput("theocracy_government", flags, features, dlcs);
  input.government_flags_available = false;
  const auto result = observer::EvaluateGovernmentRuntimeAdapterObserverV1(input);
  return result.status == Status::available &&
         result.government.status == Status::available &&
         result.government.stable_key == "theocracy_government" &&
         result.government.recognized_stock_key &&
         result.government.religious_identity_opaque &&
         result.government.observed_flags.empty() &&
         result.government.applicable_stock_flags.empty() &&
         result.adapter.status == Selection::owner_deferred_religious &&
         result.adapter.family == std::nullopt;
}

bool TestTypedNotPresent() {
  Input no_player{};
  no_player.exact_build_admitted = true;
  no_player.application_main = true;
  no_player.paused = true;
  no_player.state_identity_stable = true;
  const auto player =
      observer::EvaluateGovernmentRuntimeAdapterObserverV1(no_player);
  no_player.player_character_id = 29'829;
  const auto government =
      observer::EvaluateGovernmentRuntimeAdapterObserverV1(no_player);
  return player.status == Status::not_present &&
         player.unavailable_reason == Reason::player_not_present &&
         player.government.status == Status::not_present &&
         government.status == Status::not_present &&
         government.unavailable_reason == Reason::government_not_present &&
         government.government.status == Status::not_present;
}

bool TestTypedUnavailableInputs() {
  const auto features = Features(std::span<const std::string_view>{});
  constexpr std::string_view flags[]{"government_is_feudal"};
  constexpr std::string_view dlcs[]{"duplicate", "duplicate"};
  auto input = AvailableInput("feudal_government", flags, features, dlcs);
  input.government_flags_available = false;
  const auto flags_unavailable =
      observer::EvaluateGovernmentRuntimeAdapterObserverV1(input);
  input.government_flags_available = true;
  input.effective_feature_flags = input.effective_feature_flags.first(43);
  const auto registry_drift =
      observer::EvaluateGovernmentRuntimeAdapterObserverV1(input);
  input.effective_feature_flags = features;
  input.enabled_feature_count = EnabledCount(features);
  const auto duplicate_dlcs =
      observer::EvaluateGovernmentRuntimeAdapterObserverV1(input);
  input.script_dlc_keys = {};
  input.script_dlc_set_available = false;
  const auto dlcs_unavailable =
      observer::EvaluateGovernmentRuntimeAdapterObserverV1(input);
  return flags_unavailable.status == Status::unavailable &&
         flags_unavailable.unavailable_reason ==
             Reason::government_flags_unavailable &&
         registry_drift.status == Status::unavailable &&
         registry_drift.unavailable_reason == Reason::feature_registry_drift &&
         duplicate_dlcs.status == Status::unavailable &&
         duplicate_dlcs.unavailable_reason == Reason::script_dlc_set_invalid &&
         dlcs_unavailable.status == Status::unavailable &&
         dlcs_unavailable.unavailable_reason ==
             Reason::script_dlc_set_unavailable;
}

bool TestExecutionGates() {
  Input input{};
  const auto build = observer::EvaluateGovernmentRuntimeAdapterObserverV1(input);
  input.exact_build_admitted = true;
  const auto thread = observer::EvaluateGovernmentRuntimeAdapterObserverV1(input);
  input.application_main = true;
  const auto pause = observer::EvaluateGovernmentRuntimeAdapterObserverV1(input);
  input.paused = true;
  const auto state = observer::EvaluateGovernmentRuntimeAdapterObserverV1(input);
  return build.unavailable_reason == Reason::unsupported_build &&
         thread.unavailable_reason == Reason::requires_application_main &&
         pause.unavailable_reason == Reason::requires_paused &&
         state.unavailable_reason == Reason::state_changed;
}

} // namespace

int main() {
  const bool green =
      observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1().size() == 44 &&
      observer::kGovernmentRuntimeAdapterStockGovernmentCountV1 == 18 &&
      observer::kGovernmentRuntimeAdapterStockFlagDeclarationCountV1 == 136 &&
      TestCoreGovernmentIdentityGreen() &&
      TestDlcAdapterAndFeatureIdentity() && TestFeatureMismatchIsTyped() &&
      TestUnknownGovernmentRetainsIdentity() &&
      TestReligiousGovernmentIsOpaqueIdentityOnly() && TestTypedNotPresent() &&
      TestTypedUnavailableInputs() && TestExecutionGates();
  if (!green) {
    std::cerr << "government-runtime-adapter-observer-v1: RED\n";
    return 1;
  }
  std::cout << "government-runtime-adapter-observer-v1: GREEN\n";
  return 0;
}
