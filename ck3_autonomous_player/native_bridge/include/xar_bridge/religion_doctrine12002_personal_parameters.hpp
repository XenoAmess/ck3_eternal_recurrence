#pragma once

#include "xar_bridge/religion_doctrine12002_tenet.hpp"

namespace xar::ck3_12002::religion::doctrine12002 {
inline constexpr std::uintptr_t kPersonalParameterCollectionGetterRva = 0x28BD090;
inline constexpr std::uintptr_t kPersonalParameterDatabaseSlotRva = 0x5D1DEB8;
inline constexpr std::size_t kPersonalParameterCharacterExtensionOffset = 0x1C8;
inline constexpr std::size_t kPersonalParameterOwnedTenetsOffset = 0x88;
inline constexpr std::size_t kPersonalParameterDefinitionSetOffset = 0x740;
inline constexpr std::size_t kPersonalParameterSupportedSetOffset = 0xF20;
using PersonalParameterCollectionGetter = const void *(*)(const void *);
struct PersonalParameterBindings {
  bool enabled{};
  const void *const *database_slot{};
  PersonalParameterCollectionGetter owned_tenets{};
  BooleanParameterMembership contains_parameter{};
  ParameterTokenKey parameter_key{};
};
struct PersonalParameterValue {
  std::string key;
  bool value{};
  bool operator==(const PersonalParameterValue &) const = default;
};
struct PersonalParameterContext {
  bool available{};
  std::string failure{"bindings_unavailable"};
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{};
  std::uint32_t played_character_id{};
  bool has_character_extension{};
  std::vector<std::string> personal_tenet_keys;
  std::vector<PersonalParameterValue> parameters;
};
enum class PersonalParameterLookupState { Value, UnsupportedKey, UnavailableSource };
struct PersonalParameterLookup {
  PersonalParameterLookupState state{PersonalParameterLookupState::UnavailableSource};
  std::optional<bool> value;
};
PersonalParameterBindings BindPersonalParameters12002(std::uintptr_t module_base,
                                                     std::string_view executable_sha) noexcept;
bool ReadPlayedPersonalParameters12002(const religion::Bindings &religion_bindings,
                                      const PersonalParameterBindings &parameter_bindings,
                                      std::uint64_t capture_epoch,
                                      PersonalParameterContext &output) noexcept;
PersonalParameterLookup LookupPersonalParameter12002(const PersonalParameterContext &context,
                                                    std::string_view key) noexcept;
std::string SerializePersonalParameters12002(const PersonalParameterContext &context);
} // namespace xar::ck3_12002::religion::doctrine12002
