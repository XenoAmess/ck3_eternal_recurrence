#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12002::religion::doctrine12002 {

inline constexpr std::uintptr_t kBooleanParameterMembershipRva = 0xB9DE80;
inline constexpr std::uintptr_t kParameterTokenKeyRva = 0x3F4F900;
inline constexpr std::size_t kRiteBooleanParameterOffset = 0x7B8;
inline constexpr std::size_t kArrayDataOffset = 0x0;
inline constexpr std::size_t kArrayCountOffset = 0xC;

using BooleanParameterMembership = bool (*)(const void *, const std::int32_t *);
using ParameterTokenKey = const void *(*)(std::int32_t);

struct TenetParameterBindings {
  bool enabled{};
  BooleanParameterMembership contains_boolean_parameter{};
  ParameterTokenKey parameter_key{};
};

struct BooleanParameter {
  std::string key;
  bool value{true};
  bool operator==(const BooleanParameter &) const = default;
};

struct RiteBooleanParameters {
  std::uint32_t rite_id{};
  std::vector<BooleanParameter> parameters;
  bool operator==(const RiteBooleanParameters &) const = default;
};

struct TenetParameterContext {
  bool available{};
  std::string failure{"bindings_unavailable"};
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{};
  std::uint32_t played_character_id{};
  std::optional<std::uint32_t> faith_id;
  std::optional<RiteBooleanParameters> current_rite;
  std::optional<RiteBooleanParameters> faith_main_rite;
};

TenetParameterBindings BindTenetParameters12002(std::uintptr_t module_base,
                                               std::string_view executable_sha) noexcept;
bool ReadPlayedTenetParameters12002(const religion::Bindings &religion_bindings,
                                  const TenetParameterBindings &parameter_bindings,
                                  std::uint64_t capture_epoch,
                                  TenetParameterContext &output) noexcept;
std::string SerializeTenetParameters12002(const TenetParameterContext &context);

} // namespace xar::ck3_12002::religion::doctrine12002
