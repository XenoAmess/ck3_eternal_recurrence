#pragma once

#include "xar_bridge/religion_doctrine12002_numeric.hpp"

namespace xar::ck3_12002::religion::doctrine12002 {

inline constexpr std::uintptr_t kFaithHeresyThresholdGetterRva = 0x2440920;
inline constexpr std::uintptr_t kFaithHeresyThresholdDefineRva = 0x5C68D88;
using FaithHeresyThresholdGetter = std::int64_t *(*)(const void *, std::int64_t *);

struct FaithNumericFinalBindings {
  bool enabled{};
  FaithHeresyThresholdGetter faith_heresy_threshold{};
  const std::int64_t *heresy_threshold_define{};
};
struct FaithNumericFinalContext {
  bool available{};
  std::string failure{"bindings_unavailable"};
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{};
  std::uint32_t played_character_id{};
  std::optional<std::uint32_t> current_rite_id;
  std::optional<std::uint32_t> faith_id;
  std::optional<std::uint32_t> main_rite_id;
  std::optional<std::int64_t> main_rite_adjustment_raw;
  std::optional<std::int64_t> native_define_raw;
  std::optional<std::int64_t> final_heresy_threshold_raw;
};

FaithNumericFinalBindings BindFaithNumericFinal12002(std::uintptr_t module_base,
                                                   std::string_view executable_sha) noexcept;
bool ReadPlayedFaithNumericFinal12002(const religion::Bindings &religion_bindings,
                                     const NumericSpecialBindings &numeric_bindings,
                                     const FaithNumericFinalBindings &final_bindings,
                                     std::uint64_t capture_epoch,
                                     FaithNumericFinalContext &output) noexcept;
std::string SerializeFaithNumericFinal12002(const FaithNumericFinalContext &context);

} // namespace xar::ck3_12002::religion::doctrine12002
