#pragma once

#include "xar_bridge/ck3_12002_phase_definitions.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kPhaseMiscCharacterStoreSlot = 0x5C67568;
inline constexpr std::uintptr_t kPhaseMiscCharacterFallbackSlot = 0x5C67570;
inline constexpr std::uintptr_t kPhaseMiscAccoladeStoreSlot = 0x5D1ECA0;
inline constexpr std::uintptr_t kPhaseMiscAccoladeFallbackSlot = 0x5D1EC40;
inline constexpr std::uintptr_t kPhaseMiscCourtPositionStoreSlot = 0x5D1DD10;
inline constexpr std::uintptr_t kPhaseMiscCourtPositionFallbackSlot = 0x5D1DD08;
inline constexpr std::uintptr_t kPhaseMiscCourtTypeDatabaseSlot = 0x5C67330;
inline constexpr std::uintptr_t kPhaseMiscCourtTypeFallbackSlot = 0x5D1DD40;
inline constexpr std::uintptr_t kPhaseMiscModifierDatabaseSlot = 0x5C670F8;
inline constexpr std::uintptr_t kPhaseMiscModifierFallbackSlot = 0x5D1E0B0;
inline constexpr std::uintptr_t kPhaseMiscModifierLookupRva = 0xAB8D20;
inline constexpr std::uintptr_t kPhaseMiscCanBeAcclaimedRva = 0x2B91300;
inline constexpr std::uintptr_t kPhaseMiscAccoladeHasParameterRva = 0x27BF5E0;
inline constexpr std::uintptr_t kPhaseMiscCharacterGovernmentRva = 0x28C2E10;
inline constexpr std::size_t kPhaseMiscCharacterExtensionOffset = 0x1B0;
inline constexpr std::size_t kPhaseMiscCharacterRelationsOffset = 0x1B8;
inline constexpr std::size_t kPhaseMiscCharacterDeathDataOffset = 0x1D0;
inline constexpr std::size_t kPhaseMiscAccoladeIdOffset = 0x570;
inline constexpr std::size_t kPhaseMiscAccoladeCategoriesOffset = 0x3A8;
inline constexpr std::size_t kPhaseMiscGovernmentFlagsOffset = 0x50;
inline constexpr std::size_t kPhaseMiscDatabaseObjectsOffset = 0x50;
inline constexpr std::size_t kPhaseMiscDatabaseCountOffset = 0x5C;

using PhaseMiscLookupDefinition = void *(*)(void *, std::int32_t);
using PhaseMiscCanBeAcclaimed = bool (*)(void *, void *, void *);
using PhaseMiscAccoladeHasParameter = bool (*)(void *, std::int32_t);
using PhaseMiscCharacterGovernment = void *(*)(void *);

struct PhaseMiscBindings {
  bool enabled = false;
  PhaseDefinitionBindings identifiers;
  void **character_store = nullptr;
  void **character_fallback = nullptr;
  void **accolade_store = nullptr;
  void **accolade_fallback = nullptr;
  void **court_position_store = nullptr;
  void **court_position_fallback = nullptr;
  void **court_type_database = nullptr;
  void **court_type_fallback = nullptr;
  void **modifier_database = nullptr;
  void **modifier_fallback = nullptr;
  PhaseMiscLookupDefinition lookup_modifier = nullptr;
  PhaseMiscCanBeAcclaimed can_be_acclaimed = nullptr;
  PhaseMiscAccoladeHasParameter accolade_has_parameter = nullptr;
  PhaseMiscCharacterGovernment character_government = nullptr;
};

struct PhaseMiscDefinitionContext {
  void *extreme_conqueror_modifier = nullptr;
  void *garuda_court_position_type = nullptr;
  std::vector<game::NamedSignedV3> attribute_variable_ids;
  std::vector<game::NamedSignedV3> accolade_parameter_ids;
  std::int32_t government_is_nomadic_id = -1;
  std::int32_t men_at_arms_category_id = -1;
  std::int32_t conqueror_variable_id = -1;
  std::int32_t hold_court_knight_variable_id = -1;
  std::int32_t hold_court_promise_variable_id = -1;
  std::int32_t accolade_progress_variable_id = -1;
};

// Address calculation only; the caller supplies its exact image/hash.
PhaseMiscBindings BindPhaseMiscImage(std::uintptr_t base,
                                    std::string_view executable_sha256) noexcept;
bool BuildPhaseMiscDefinitions(const PhaseMiscBindings &bindings,
                               PhaseMiscDefinitionContext &output) noexcept;

// Employer/liege identities must already come from the relations reader.
// This leaf only fills variables, modifiers, accolades, government and court.
bool ReadPhaseCharacterMisc(const PhaseMiscBindings &bindings,
                            const PhaseMiscDefinitionContext &definitions,
                            void *character,
                            game::CombatPhaseCharacterV3 &output) noexcept;
bool ReadPhaseCharacterMisc(const PhaseMiscBindings &bindings, void *character,
                            game::CombatPhaseCharacterV3 &output) noexcept;

} // namespace xar::ck3_12002
