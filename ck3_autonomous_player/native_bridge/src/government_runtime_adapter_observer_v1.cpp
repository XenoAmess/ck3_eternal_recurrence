#include "xar_bridge/government_runtime_adapter_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <string>
#include <string_view>

namespace xar::bridge::private_observer {
namespace {

using Names = std::span<const std::string_view>;
using ObservationStatus = GovernmentRuntimeAdapterObservationStatusV1;
using UnavailableReason = GovernmentRuntimeAdapterUnavailableReasonV1;
using SelectionStatus = GovernmentRuntimeAdapterSelectionStatusV1;

constexpr std::array<std::string_view, 0> kNoNames{};
constexpr std::array kFeudalFlags{
    std::string_view{"government_is_feudal"},
    std::string_view{"government_is_settled"},
    std::string_view{"may_elevate_co_monarch"},
    std::string_view{"government_uses_crown_authority"},
    std::string_view{"government_uses_domain_limit"},
};
constexpr std::array kRepublicFlags{
    std::string_view{"government_is_republic"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_uses_domain_limit"},
};
constexpr std::array kTheocracyFlags{
    std::string_view{"government_is_theocracy"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_uses_domain_limit"},
};
constexpr std::array kClanFlags{
    std::string_view{"government_is_clan"},
    std::string_view{"may_appoint_viziers"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_uses_crown_authority"},
    std::string_view{"government_uses_domain_limit"},
};
constexpr std::array kTribalFlags{
    std::string_view{"government_is_tribal"},
    std::string_view{"government_is_tribal_excluding_wanua"},
    std::string_view{"use_prestige_to_buy_maa"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_can_raid_rule"},
    std::string_view{"may_elevate_co_monarch"},
    std::string_view{"government_uses_domain_limit"},
};
constexpr std::array kWanuaFlags{
    std::string_view{"government_is_tribal"},
    std::string_view{"government_is_wanua"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_can_raid_rule"},
    std::string_view{"government_enables_naval_raiding"},
    std::string_view{"government_enables_river_travel"},
    std::string_view{"may_elevate_co_monarch"},
};
constexpr std::array kMercenaryFlags{
    std::string_view{"government_uses_crown_authority"},
    std::string_view{"cannot_be_vassal_or_liege"},
    std::string_view{"government_is_mercenary"},
};
constexpr std::array kHolyOrderFlags{
    std::string_view{"government_uses_crown_authority"},
    std::string_view{"cannot_be_vassal_or_liege"},
    std::string_view{"government_is_holy_order"},
};
constexpr std::array kAdministrativeFlags{
    std::string_view{"government_is_administrative"},
    std::string_view{"government_has_influence"},
    std::string_view{"government_has_treasury"},
    std::string_view{"government_has_title_men_at_arms"},
    std::string_view{"government_has_powerful_families"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_uses_domicile_but_not_adventurer"},
    std::string_view{"government_uses_domain_limit"},
    std::string_view{"government_uses_admin_province_obligations"},
};
constexpr std::array kLandlessAdventurerFlags{
    std::string_view{"cannot_be_vassal_or_liege"},
    std::string_view{"government_is_landless_adventurer"},
    std::string_view{"has_unique_government_perks"},
};
constexpr std::array kNomadFlags{
    std::string_view{"government_is_nomadic"},
    std::string_view{"government_has_herd"},
    std::string_view{"government_can_raid_rule"},
    std::string_view{"government_can_use_tributary_men_at_arms"},
    std::string_view{"can_start_war_with_raised_troops"},
    std::string_view{"ignores_faith_marriage_penalties"},
    std::string_view{"no_hostile_attrition_in_steppe"},
    std::string_view{"movement_speed_from_government"},
    std::string_view{"land_raiding_movement_speed_from_government"},
    std::string_view{"can_raze_holdings"},
    std::string_view{"government_uses_domicile_but_not_adventurer"},
};
constexpr std::array kHerderFlags{
    std::string_view{"government_is_herder"},
    std::string_view{"government_has_herd"},
    std::string_view{"ignores_faith_marriage_penalties"},
};
constexpr std::array kCelestialFlags{
    std::string_view{"government_is_celestial"},
    std::string_view{"government_has_merit"},
    std::string_view{"government_has_influence"},
    std::string_view{"government_has_treasury"},
    std::string_view{"government_has_title_men_at_arms"},
    std::string_view{"government_has_powerful_families"},
    std::string_view{"government_has_county_tier_noble_families"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_uses_domicile_but_not_adventurer"},
    std::string_view{"government_uses_domain_limit"},
    std::string_view{"government_uses_admin_province_obligations"},
    std::string_view{"government_uses_merit_family_aspirations"},
    std::string_view{"has_special_house_aspirations"},
};
constexpr std::array kMandalaFlags{
    std::string_view{"uses_mandala_aspects"},
    std::string_view{"uses_mandala_decrees"},
    std::string_view{"government_is_mandala"},
    std::string_view{"has_coerce_tributary_scheme"},
    std::string_view{"additional_piety_from_religious_buildings"},
    std::string_view{"can_perform_ritual_contracts"},
    std::string_view{"subjects_gain_piety_based_on_overlord_piety_level"},
    std::string_view{"has_special_house_aspirations"},
    std::string_view{"government_is_settled"},
    std::string_view{"has_unique_government_perks"},
    std::string_view{"no_powerful_vassals"},
};
constexpr std::array kSteppeAdministrativeFlags{
    std::string_view{"government_is_steppe_admin"},
    std::string_view{"government_can_raid_rule"},
    std::string_view{"government_can_use_tributary_men_at_arms"},
    std::string_view{"government_has_merit"},
    std::string_view{"government_has_influence"},
    std::string_view{"government_has_treasury"},
    std::string_view{"government_has_title_men_at_arms"},
    std::string_view{"government_has_powerful_families"},
    std::string_view{"government_has_county_tier_noble_families"},
    std::string_view{"ignores_faith_marriage_penalties"},
    std::string_view{"land_raiding_movement_speed_from_government"},
    std::string_view{"can_raze_holdings"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_uses_domicile_but_not_adventurer"},
    std::string_view{"government_uses_domain_limit"},
    std::string_view{"government_uses_admin_province_obligations"},
    std::string_view{"government_uses_merit_family_aspirations"},
    std::string_view{"has_special_house_aspirations"},
};
constexpr std::array kMeritocraticFlags{
    std::string_view{"government_is_meritocratic"},
    std::string_view{"government_has_merit"},
    std::string_view{"government_has_influence"},
    std::string_view{"government_has_treasury"},
    std::string_view{"government_has_title_men_at_arms"},
    std::string_view{"government_has_powerful_families"},
    std::string_view{"government_has_county_tier_noble_families"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_uses_domicile_but_not_adventurer"},
    std::string_view{"government_uses_domain_limit"},
    std::string_view{"government_uses_admin_province_obligations"},
    std::string_view{"government_uses_merit_family_aspirations"},
    std::string_view{"has_special_house_aspirations"},
};
constexpr std::array kJapanAdministrativeFlags{
    std::string_view{"government_is_japan_administrative"},
    std::string_view{"government_has_influence"},
    std::string_view{"government_has_title_men_at_arms"},
    std::string_view{"government_has_powerful_families"},
    std::string_view{"government_has_county_tier_noble_families"},
    std::string_view{"has_special_house_aspirations"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_uses_domicile_but_not_adventurer"},
    std::string_view{"has_unique_government_perks"},
    std::string_view{"government_uses_admin_province_obligations"},
    std::string_view{"government_has_house_blocs"},
};
constexpr std::array kJapanFeudalFlags{
    std::string_view{"may_elevate_co_monarch"},
    std::string_view{"government_is_japan_feudal"},
    std::string_view{"government_has_county_tier_noble_families"},
    std::string_view{"has_special_house_aspirations"},
    std::string_view{"government_is_settled"},
    std::string_view{"government_uses_domicile_but_not_adventurer"},
    std::string_view{"has_unique_government_perks"},
    std::string_view{"government_has_house_blocs"},
};

static_assert(
    kFeudalFlags.size() + kRepublicFlags.size() + kTheocracyFlags.size() +
            kClanFlags.size() + kTribalFlags.size() + kWanuaFlags.size() +
            kMercenaryFlags.size() + kHolyOrderFlags.size() +
            kAdministrativeFlags.size() + kLandlessAdventurerFlags.size() +
            kNomadFlags.size() + kHerderFlags.size() +
            kCelestialFlags.size() + kMandalaFlags.size() +
            kSteppeAdministrativeFlags.size() + kMeritocraticFlags.size() +
            kJapanAdministrativeFlags.size() + kJapanFeudalFlags.size() ==
        kGovernmentRuntimeAdapterStockFlagDeclarationCountV1,
    "the exact-build stock government flag declaration count changed");

constexpr std::array kAdminRequired{std::string_view{"admin_gov"}};
constexpr std::array kAdminProfile{
    std::string_view{"admin_gov"}, std::string_view{"roads_to_power"},
    std::string_view{"advanced_aspirations"}};
constexpr std::array kLandlessRequired{
    std::string_view{"landless_adventurer"}};
constexpr std::array kLandlessProfile{
    std::string_view{"landless_playable"},
    std::string_view{"landless_adventurer"},
    std::string_view{"roads_to_power"}};
constexpr std::array kNomadRequired{
    std::string_view{"khans_of_the_steppe"}, std::string_view{"nomads"}};
constexpr std::array kNomadProfile{
    std::string_view{"khans_of_the_steppe"}, std::string_view{"nomads"},
    std::string_view{"landless_playable"}};
constexpr std::array kHerderProfile{
    std::string_view{"khans_of_the_steppe"}, std::string_view{"nomads"}};
constexpr std::array kTgpRequired{std::string_view{"all_under_heaven"}};
constexpr std::array kWanuaProfile{
    std::string_view{"all_under_heaven"},
    std::string_view{"landless_playable"}};
constexpr std::array kCelestialProfile{
    std::string_view{"all_under_heaven"}, std::string_view{"merit_admin"},
    std::string_view{"advanced_aspirations"},
    std::string_view{"barter_troops"}};
constexpr std::array kMandalaProfile{
    std::string_view{"all_under_heaven"},
    std::string_view{"advanced_aspirations"},
    std::string_view{"barter_troops"}};
constexpr std::array kJapanAdministrativeProfile{
    std::string_view{"all_under_heaven"}, std::string_view{"merit_admin"},
    std::string_view{"advanced_aspirations"}};
constexpr std::array kJapanFeudalProfile{
    std::string_view{"all_under_heaven"},
    std::string_view{"advanced_aspirations"}};

struct GovernmentDefinitionV1 {
  std::string_view key;
  Names flags;
  SelectionStatus status;
  std::string_view family;
  Names required_features;
  Names profile_features;
  bool religious_opaque;
};

constexpr std::array<GovernmentDefinitionV1,
                     kGovernmentRuntimeAdapterStockGovernmentCountV1>
    kGovernmentDefinitions{{
        {"feudal_government", kFeudalFlags, SelectionStatus::core_supported,
         "core_landed", kNoNames, kNoNames, false},
        {"republic_government", kRepublicFlags,
         SelectionStatus::unsupported_nonplayer_identity, "", kNoNames,
         kNoNames, false},
        {"theocracy_government", kTheocracyFlags,
         SelectionStatus::owner_deferred_religious, "", kNoNames, kNoNames,
         true},
        {"clan_government", kClanFlags, SelectionStatus::core_supported,
         "core_landed", kNoNames, kNoNames, false},
        {"tribal_government", kTribalFlags, SelectionStatus::core_supported,
         "core_tribal", kNoNames, kNoNames, false},
        {"wanua_government", kWanuaFlags,
         SelectionStatus::adapter_spec_ready_not_implemented, "tgp_wanua",
         kTgpRequired, kWanuaProfile, false},
        {"mercenary_government", kMercenaryFlags,
         SelectionStatus::unsupported_nonplayer_identity, "", kNoNames,
         kNoNames, false},
        {"holy_order_government", kHolyOrderFlags,
         SelectionStatus::owner_deferred_religious, "", kNoNames, kNoNames,
         true},
        {"administrative_government", kAdministrativeFlags,
         SelectionStatus::adapter_spec_ready_not_implemented,
         "rtp_administrative", kAdminRequired, kAdminProfile, false},
        {"landless_adventurer_government", kLandlessAdventurerFlags,
         SelectionStatus::adapter_spec_ready_not_implemented,
         "rtp_landless_adventurer", kLandlessRequired, kLandlessProfile,
         false},
        {"nomad_government", kNomadFlags,
         SelectionStatus::adapter_spec_ready_not_implemented, "mpo_nomad",
         kNomadRequired, kNomadProfile, false},
        {"herder_government", kHerderFlags,
         SelectionStatus::adapter_spec_ready_not_implemented, "mpo_herder",
         kNomadRequired, kHerderProfile, false},
        {"celestial_government", kCelestialFlags,
         SelectionStatus::adapter_spec_ready_not_implemented,
         "tgp_celestial", kTgpRequired, kCelestialProfile, false},
        {"mandala_government", kMandalaFlags,
         SelectionStatus::adapter_spec_ready_not_implemented, "tgp_mandala",
         kTgpRequired, kMandalaProfile, false},
        {"steppe_admin_government", kSteppeAdministrativeFlags,
         SelectionStatus::adapter_spec_ready_not_implemented,
         "tgp_steppe_administrative", kTgpRequired, kCelestialProfile, false},
        {"meritocratic_government", kMeritocraticFlags,
         SelectionStatus::adapter_spec_ready_not_implemented,
         "tgp_meritocratic", kTgpRequired, kCelestialProfile, false},
        {"japan_administrative_government", kJapanAdministrativeFlags,
         SelectionStatus::adapter_spec_ready_not_implemented,
         "tgp_japan_administrative", kTgpRequired,
         kJapanAdministrativeProfile, false},
        {"japan_feudal_government", kJapanFeudalFlags,
         SelectionStatus::adapter_spec_ready_not_implemented,
         "tgp_japan_feudal", kTgpRequired, kJapanFeudalProfile, false},
    }};

constexpr std::array<std::string_view,
                     kGovernmentRuntimeAdapterFeatureCountV1>
    kFeatureKeys{{
        "garments_of_the_hre",
        "fashion_of_the_abbasid_court",
        "the_northern_lords",
        "hybridize_culture",
        "diverge_culture",
        "royal_court",
        "reform_culture",
        "court_artifacts",
        "the_fate_of_iberia",
        "friends_and_foes",
        "tours_and_tournaments",
        "advanced_activities",
        "accolades",
        "legacy_of_persia",
        "elegance_of_the_empire",
        "wards_and_wardens",
        "legends_of_the_dead",
        "legends",
        "north_african_attire",
        "couture_of_the_capets",
        "landless_playable",
        "admin_gov",
        "roads_to_power",
        "court_room_view",
        "wandering_nobles",
        "west_slavic_attire",
        "medieval_monuments",
        "khans_of_the_steppe",
        "nomads",
        "arctic_attire",
        "crowns_of_the_world",
        "landless_adventurer",
        "coronations",
        "all_under_heaven",
        "merit_admin",
        "advanced_aspirations",
        "barter_troops",
        "high_medieval_warfare_attire",
        "holy_buildings",
        "north_pacific_attire",
        "east_asian_wonders",
        "celestial_court_attire",
        "symbols_of_authority",
        "songs_of_the_realm",
    }};

constexpr std::array kRuntimeProductKeys{
    std::string_view{"Roads to Power"},
    std::string_view{"Khans of the Steppe"},
    std::string_view{"All Under Heaven"},
};

bool Utf8BytewiseLess(std::string_view left, std::string_view right) noexcept {
  return std::lexicographical_compare(
      left.begin(), left.end(), right.begin(), right.end(),
      [](char left_byte, char right_byte) noexcept {
        return static_cast<unsigned char>(left_byte) <
               static_cast<unsigned char>(right_byte);
      });
}

const GovernmentDefinitionV1 *FindGovernment(std::string_view key) noexcept {
  const auto found = std::find_if(
      kGovernmentDefinitions.begin(), kGovernmentDefinitions.end(),
      [key](const GovernmentDefinitionV1 &row) { return row.key == key; });
  return found == kGovernmentDefinitions.end() ? nullptr : &*found;
}

const GovernmentRuntimeFeatureIdentityV1 *FindFeature(
    const std::vector<GovernmentRuntimeFeatureIdentityV1> &features,
    std::string_view key) noexcept {
  const auto found = std::find_if(
      features.begin(), features.end(),
      [key](const GovernmentRuntimeFeatureIdentityV1 &feature) {
        return feature.key == key;
      });
  return found == features.end() ? nullptr : &*found;
}

bool Contains(Names values, std::string_view expected) noexcept {
  return std::find(values.begin(), values.end(), expected) != values.end();
}

GovernmentRuntimeAdapterObserverResultV1 Fail(
    const GovernmentRuntimeAdapterObserverInputV1 &input,
    ObservationStatus status, UnavailableReason reason) {
  GovernmentRuntimeAdapterObserverResultV1 result{};
  result.status = status;
  result.unavailable_reason = reason;
  result.frame = input.frame;
  result.player_character_id = input.player_character_id;
  return result;
}

} // namespace

std::span<const std::string_view>
GovernmentRuntimeAdapterExpectedFeatureKeysV1() noexcept {
  return kFeatureKeys;
}

GovernmentRuntimeAdapterObserverResultV1
EvaluateGovernmentRuntimeAdapterObserverV1(
    const GovernmentRuntimeAdapterObserverInputV1 &input) {
  if (!input.exact_build_admitted) {
    return Fail(input, ObservationStatus::unavailable,
                UnavailableReason::unsupported_build);
  }
  if (!input.application_main) {
    return Fail(input, ObservationStatus::unavailable,
                UnavailableReason::requires_application_main);
  }
  if (!input.paused) {
    return Fail(input, ObservationStatus::unavailable,
                UnavailableReason::requires_paused);
  }
  if (!input.state_identity_stable) {
    return Fail(input, ObservationStatus::unavailable,
                UnavailableReason::state_changed);
  }
  if (!input.player_character_id.has_value()) {
    auto result = Fail(input, ObservationStatus::not_present,
                       UnavailableReason::player_not_present);
    result.government.status = ObservationStatus::not_present;
    return result;
  }
  if (input.effective_government_stable_key.empty()) {
    auto result = Fail(input, ObservationStatus::not_present,
                       UnavailableReason::government_not_present);
    result.government.status = ObservationStatus::not_present;
    return result;
  }

  GovernmentRuntimeAdapterObserverResultV1 result{};
  result.frame = input.frame;
  result.player_character_id = input.player_character_id;
  result.government.stable_key = input.effective_government_stable_key;
  const auto *definition = FindGovernment(input.effective_government_stable_key);
  result.government.recognized_stock_key = definition != nullptr;
  result.government.religious_identity_opaque =
      definition != nullptr && definition->religious_opaque;
  if (!result.government.religious_identity_opaque) {
    if (!input.government_flags_available) {
      result.unavailable_reason =
          UnavailableReason::government_flags_unavailable;
      return result;
    }
    result.government.observed_flags.reserve(input.government_flags.size());
    for (const auto flag : input.government_flags) {
      result.government.observed_flags.emplace_back(flag);
    }
    std::sort(result.government.observed_flags.begin(),
              result.government.observed_flags.end(), Utf8BytewiseLess);
    if (definition != nullptr) {
      for (const auto &flag : result.government.observed_flags) {
        if (Contains(definition->flags, flag)) {
          result.government.applicable_stock_flags.push_back(flag);
        }
      }
    }
  }
  result.government.status = ObservationStatus::available;

  if (!input.feature_root_available) {
    result.unavailable_reason = UnavailableReason::feature_root_unavailable;
    return result;
  }
  if (input.effective_feature_flags.size() != kFeatureKeys.size()) {
    result.unavailable_reason = UnavailableReason::feature_registry_drift;
    return result;
  }
  std::int32_t enabled_count = 0;
  result.effective_feature_flags.reserve(kFeatureKeys.size());
  for (std::size_t index = 0; index < kFeatureKeys.size(); ++index) {
    const auto &input_feature = input.effective_feature_flags[index];
    if (input_feature.native_index != static_cast<std::int32_t>(index) ||
        input_feature.key != kFeatureKeys[index]) {
      result.effective_feature_flags.clear();
      result.unavailable_reason = UnavailableReason::feature_registry_drift;
      return result;
    }
    if (input_feature.enabled) {
      ++enabled_count;
    }
    result.effective_feature_flags.push_back(
        {input_feature.native_index, std::string{input_feature.key},
         input_feature.enabled});
  }
  if (enabled_count != input.enabled_feature_count) {
    result.effective_feature_flags.clear();
    result.unavailable_reason = UnavailableReason::feature_counter_mismatch;
    return result;
  }
  if (!input.script_dlc_set_available) {
    result.unavailable_reason = UnavailableReason::script_dlc_set_unavailable;
    return result;
  }
  result.script_dlc_keys.reserve(input.script_dlc_keys.size());
  for (const auto key : input.script_dlc_keys) {
    result.script_dlc_keys.emplace_back(key);
  }
  std::sort(result.script_dlc_keys.begin(), result.script_dlc_keys.end(),
            Utf8BytewiseLess);
  if (std::adjacent_find(result.script_dlc_keys.begin(),
                         result.script_dlc_keys.end()) !=
      result.script_dlc_keys.end()) {
    result.script_dlc_keys.clear();
    result.unavailable_reason = UnavailableReason::script_dlc_set_invalid;
    return result;
  }
  for (const auto product : kRuntimeProductKeys) {
    const bool present =
        std::binary_search(result.script_dlc_keys.begin(),
                           result.script_dlc_keys.end(), product,
                           Utf8BytewiseLess);
    result.runtime_products.push_back(
        {present ? ObservationStatus::available : ObservationStatus::not_present,
         std::string{product}});
  }

  result.entitlement_status = ObservationStatus::unavailable;
  result.entitlement_unavailable_reason =
      UnavailableReason::store_verdict_provenance_unclosed;
  if (definition == nullptr) {
    result.adapter.status = SelectionStatus::unadapted_runtime_government;
  } else {
    result.adapter.status = definition->status;
    if (!definition->family.empty()) {
      result.adapter.family = std::string{definition->family};
    }
    for (const auto key : definition->required_features) {
      result.adapter.required_effective_features.emplace_back(key);
    }
    bool requirements_met = true;
    for (const auto key : definition->profile_features) {
      const auto *feature = FindFeature(result.effective_feature_flags, key);
      if (feature == nullptr) {
        result.unavailable_reason = UnavailableReason::feature_registry_drift;
        return result;
      }
      result.adapter.capability_profile_features.push_back(*feature);
    }
    for (const auto key : definition->required_features) {
      const auto *feature = FindFeature(result.effective_feature_flags, key);
      if (feature == nullptr || !feature->enabled) {
        requirements_met = false;
      }
    }
    result.adapter.requirements_met = requirements_met;
    if (!requirements_met &&
        definition->status ==
            SelectionStatus::adapter_spec_ready_not_implemented) {
      result.adapter.status = SelectionStatus::unavailable_feature_mismatch;
    }
  }
  result.status = ObservationStatus::available;
  result.unavailable_reason = UnavailableReason::none;
  return result;
}

} // namespace xar::bridge::private_observer
