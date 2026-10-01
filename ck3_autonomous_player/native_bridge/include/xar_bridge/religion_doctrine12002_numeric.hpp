#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12002::religion::doctrine12002 {

inline constexpr std::size_t kRiteNumericSpecialOffset = 0x7D0;
inline constexpr std::size_t kNumericMinimumFervorOffset = 0xC;
inline constexpr std::size_t kNumericHolySiteGainOffset = 0x10;
inline constexpr std::size_t kNumericFervorGainOffset = 0x18;
inline constexpr std::size_t kNumericHeresyProtectionOffset = 0x20;
inline constexpr std::size_t kNumericHeresyThresholdOffset = 0x28;

struct NumericSpecialBindings { bool enabled{}; };

struct NumericSpecialParameter {
  std::string key;
  std::int64_t raw{};
  std::uint32_t scale{1};
  std::string unit;
  bool unset{};
  bool operator==(const NumericSpecialParameter &) const = default;
};

struct RiteNumericSpecialParameters {
  std::uint32_t rite_id{};
  std::vector<NumericSpecialParameter> parameters;
  bool operator==(const RiteNumericSpecialParameters &) const = default;
};

struct NumericSpecialContext {
  bool available{};
  std::string failure{"bindings_unavailable"};
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{};
  std::uint32_t played_character_id{};
  std::optional<std::uint32_t> faith_id;
  std::optional<RiteNumericSpecialParameters> current_rite;
  std::optional<RiteNumericSpecialParameters> faith_main_rite;
};

enum class NumericParameterLookupState { Value, Unset, UnsupportedKey, UnavailableSource };
struct NumericParameterLookup {
  NumericParameterLookupState state{NumericParameterLookupState::UnavailableSource};
  std::optional<NumericSpecialParameter> parameter;
};

NumericSpecialBindings BindNumericSpecialParameters12002(std::uintptr_t module_base,
                                                        std::string_view executable_sha) noexcept;
bool ReadPlayedNumericSpecialParameters12002(const religion::Bindings &religion_bindings,
                                            const NumericSpecialBindings &numeric_bindings,
                                            std::uint64_t capture_epoch,
                                            NumericSpecialContext &output) noexcept;
NumericParameterLookup LookupNumericSpecialParameter12002(const NumericSpecialContext &context,
                                                          bool faith_main_rite,
                                                          std::string_view key);
std::string SerializeNumericSpecialParameters12002(const NumericSpecialContext &context);

} // namespace xar::ck3_12002::religion::doctrine12002
