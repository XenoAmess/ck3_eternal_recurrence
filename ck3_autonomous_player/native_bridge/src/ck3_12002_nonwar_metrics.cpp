#include "xar_bridge/ck3_12002_nonwar_metrics.hpp"

#include <cstring>
#include <limits>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12002 {
namespace {

bool DirectRead(const void *address, void *output, std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

template <typename T>
bool Read(const ck3_11906::CampaignRootAccessV1 &access,
          const void *base, std::size_t offset, T &output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - address) {
    return false;
  }
  const auto *source = reinterpret_cast<const void *>(address + offset);
  if (access.read_memory != nullptr) {
    return access.read_memory(access.context, source, &output, sizeof(output));
  }
  return DirectRead(source, &output, sizeof(output));
}

bool Income(ck3_11906::NativeCampaignRootMonthlyGoldIncomeV1 function,
            void *character, std::int64_t &output) noexcept {
#if defined(_MSC_VER)
  __try {
    return function(&output, character, nullptr, nullptr) == &output;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return function(&output, character, nullptr, nullptr) == &output;
#endif
}

bool Health(ck3_11906::NativeCampaignRootCharacterFixedPointV1 function,
            void *character, std::int64_t &output) noexcept {
#if defined(_MSC_VER)
  __try {
    return function(character, &output) == &output;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return function(character, &output) == &output;
#endif
}

bool Maintenance(
    ck3_11906::NativeCampaignRootMaxMonthlyMaintenanceV1 function,
    void *character, std::int64_t &output) noexcept {
  // The native getter initializes all ten slots. A scalar output would let
  // the real production call write beyond the caller-owned buffer.
  std::int64_t resources[10]{};
#if defined(_MSC_VER)
  __try {
    if (function(resources, character) != resources) {
      return false;
    }
    output = resources[0];
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  if (function(resources, character) != resources) {
    return false;
  }
  output = resources[0];
  return true;
#endif
}

bool Integer(ck3_11906::NativeCampaignRootCharacterInt32V1 function,
             void *character, std::int32_t &output) noexcept {
#if defined(_MSC_VER)
  __try {
    output = function(character);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = function(character);
  return true;
#endif
}

} // namespace

void BindNonwarMetrics12002(
    ck3_11906::CampaignRootNativeEnvironmentV1 &environment,
    std::uintptr_t module_base) noexcept {
  environment.monthly_gold_income = reinterpret_cast<
      ck3_11906::NativeCampaignRootMonthlyGoldIncomeV1>(
      module_base + kCampaignRootMonthlyGoldIncomeRva);
  environment.health = reinterpret_cast<
      ck3_11906::NativeCampaignRootCharacterFixedPointV1>(
      module_base + kCampaignRootHealthRva);
  environment.domain_size = reinterpret_cast<
      ck3_11906::NativeCampaignRootCharacterInt32V1>(
      module_base + kCampaignRootDomainSizeRva);
  environment.domain_limit = reinterpret_cast<
      ck3_11906::NativeCampaignRootCharacterInt32V1>(
      module_base + kCampaignRootDomainLimitRva);
}

void BindNonwarFinance12003(
    ck3_11906::CampaignRootNativeEnvironmentV1 &environment,
    std::uintptr_t module_base) noexcept {
  environment.max_monthly_maintenance = module_base == 0
      ? nullptr
      : reinterpret_cast<ck3_11906::NativeCampaignRootMaxMonthlyMaintenanceV1>(
            module_base + kCampaignRootMaxMonthlyMaintenanceRva12003);
}

game::CampaignRootMaxMonthlyGoldMaintenanceV1
ReadOptionalMaxMonthlyGoldMaintenance12003(
    ck3_11906::NativeCampaignRootMaxMonthlyMaintenanceV1 function,
    void *character) noexcept {
  game::CampaignRootMaxMonthlyGoldMaintenanceV1 output{};
  std::int64_t raw = 0;
  if (function == nullptr) {
    output.unavailable_reason = "getter_unavailable";
  } else if (character == nullptr || !Maintenance(function, character, raw)) {
    output.unavailable_reason = "getter_failed";
  } else if (raw < 0) {
    output.unavailable_reason = "amount_invalid";
  } else {
    output.value = game::FixedPointValue{raw, 100'000};
  }
  return output;
}

bool ReadNonwarMetrics12002(
    const ck3_11906::CampaignRootNativeEnvironmentV1 &environment,
    const ck3_11906::CampaignRootAccessV1 &access, void *character,
    NonwarMetricsProjection12002 &output,
    std::string_view &failure) noexcept {
  output = {};
  failure = {};
  if (character == nullptr || environment.monthly_gold_income == nullptr ||
      environment.health == nullptr || environment.domain_size == nullptr ||
      environment.domain_limit == nullptr) {
    failure = "nonwar_metrics_environment_unavailable";
    return false;
  }
  if (!Income(environment.monthly_gold_income, character,
              output.monthly_gold_income_raw)) {
    failure = "player_monthly_gold_income_unavailable";
    return false;
  }
  if (!Health(environment.health, character, output.health_raw)) {
    failure = "player_health_unavailable";
    return false;
  }
  output.max_monthly_gold_maintenance =
      ReadOptionalMaxMonthlyGoldMaintenance12003(
          environment.max_monthly_maintenance, character);
  if (!Integer(environment.domain_size, character, output.domain_size) ||
      !Integer(environment.domain_limit, character, output.domain_limit) ||
      output.domain_size < 0 || output.domain_limit < 1) {
    failure = "player_domain_unavailable";
    return false;
  }
  void *land_state = nullptr;
  if (!Read(access, character, kCampaignRootCharacterLandStateOffset12002,
            land_state) ||
      (land_state != nullptr &&
       (!Read(access, land_state, kCampaignRootTargetingFactionCountOffset12002,
              output.targeting_faction_count) ||
        output.targeting_faction_count < 0))) {
    failure = "player_targeting_factions_unavailable";
    return false;
  }
  void *legitimacy_data = nullptr;
  std::int64_t legitimacy_raw = 0;
  if (!Read(access, character, kCampaignRootCharacterLegitimacyDataOffset12002,
            legitimacy_data)) {
    output.legitimacy.unavailable_reason = "data_pointer_unreadable";
  } else if (legitimacy_data == nullptr) {
    output.legitimacy.unavailable_reason = "data_absent";
  } else if (!Read(access, legitimacy_data,
                   kCampaignRootLegitimacyBalanceOffset12002,
                   legitimacy_raw)) {
    output.legitimacy.unavailable_reason = "balance_unreadable";
  } else if (legitimacy_raw < 0) {
    output.legitimacy.unavailable_reason = "balance_invalid";
  } else {
    output.legitimacy.value = game::FixedPointValue{legitimacy_raw, 100'000};
  }
  return true;
}

} // namespace xar::ck3_12002
