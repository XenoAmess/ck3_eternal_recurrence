#pragma once

#include "xar_bridge/combat_v3.hpp"
#include "xar_bridge/ck3_12002_combat.hpp"
#include "xar_bridge/ck3_12002_phase_character.hpp"
#include "xar_bridge/ck3_12002_phase_definitions.hpp"
#include "xar_bridge/ck3_12002_phase_culture.hpp"
#include "xar_bridge/ck3_12002_phase_advantage.hpp"
#include "xar_bridge/ck3_12002_phase_misc.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12002 {

inline constexpr std::string_view kPhaseSourceDeltaSha256 =
    "878E82FD735D3D5A04715049242DB6A7FE560AFC6EEE54849CE29A69A56B04B7";
inline constexpr std::string_view kPhaseNonReligiousAstSha256 =
    "A6647A6DC0E3E15D6C9D0C050A18CE0C68D42FA498AE61704A4D9540B0137E66";
inline constexpr std::int32_t kPhaseAstEventRows = 13;
inline constexpr std::int32_t kPhaseAstSourceDefinitions = 59;
inline constexpr std::int32_t kPhaseAstDeferredOpaqueNodes = 17;
inline constexpr std::string_view kPhaseContractStage =
    "migration_native_phase_diagnostic";

inline constexpr std::size_t kPhaseCombatSideSize = 0x348;
inline constexpr std::size_t kPhaseCombatShellSize = 0x718;
inline constexpr std::size_t kPhaseGatheringOffset = 0x344;
inline constexpr std::uintptr_t kConstructPhaseSideRva = 0x264CA60;
inline constexpr std::uintptr_t kPopulatePhaseSideRva = 0x264DE30;
inline constexpr std::uintptr_t kSelectPhaseCommanderRva = 0x264D790;
inline constexpr std::uintptr_t kRefreshPhaseStrengthRva = 0x26505E0;
inline constexpr std::uintptr_t kReadPhaseStrengthRva = 0x2651100;
inline constexpr std::uintptr_t kDestroyPhaseSideRva = 0x25861A0;
inline constexpr std::uintptr_t kResolvePhaseAdvantageRva = 0x258B510;
inline constexpr std::uintptr_t kReadPhaseDynamicRva = 0x258A470;
inline constexpr std::uintptr_t kPhaseProvinceHasHoldingRva = 0xC6AF20;
inline constexpr std::uintptr_t kPhaseCommanderDynamicRva = 0x2589E10;
inline constexpr std::uintptr_t kPhaseSideModifierRva = 0x25899C0;
inline constexpr std::uintptr_t kPhaseRelationKindRva = 0x2589810;
inline constexpr std::uintptr_t kPhaseCombatPrimaryVtableRva = 0x473D138;
inline constexpr std::uintptr_t kPhaseCombatSecondaryVtableRva = 0x473D100;

using ConstructPhaseSide = void *(*)(void *, void *);
using PopulatePhaseSide = void (*)(void *, void *);
using SelectPhaseCommander = void *(*)(void *);
using RefreshPhaseStrength = void (*)(void *);
using ReadPhaseStrength = std::int32_t (*)(void *);
using DestroyPhaseSide = void (*)(void *);
using ResolvePhaseAdvantage = void (*)(void *);
using ReadPhaseDynamic = std::int64_t *(*)(void *, std::int64_t *,
                                         std::int32_t, void *);
using PhaseProvincePredicate = bool (*)(void *);
using PhaseCommanderDynamic = std::int64_t *(*)(void *, std::int64_t *, void *,
                                              std::int32_t, std::int32_t, void *);
using PhaseSideModifier = std::int64_t *(*)(void *, std::int64_t *, void *,
                                         std::int32_t, std::int32_t, void *);
using PhaseRelationKind = std::int32_t (*)(void *, std::int32_t);

struct PhaseBindings {
  bool enabled = false;
  ConstructPhaseSide construct_side = nullptr;
  PopulatePhaseSide populate_side = nullptr;
  SelectPhaseCommander select_commander = nullptr;
  RefreshPhaseStrength refresh_strength = nullptr;
  ReadPhaseStrength read_strength = nullptr;
  DestroyPhaseSide destroy_side = nullptr;
  ResolvePhaseAdvantage resolve_advantage = nullptr;
  ReadPhaseDynamic read_dynamic = nullptr;
  PhaseProvincePredicate province_has_holding = nullptr;
  CombatBindings combat;
  phase_character::Bindings traits;
  PhaseDefinitionBindings definitions;
  std::uintptr_t image_base = 0;
  phase_culture::Bindings culture;
  AdvantageBindings advantage;
  PhaseCommanderDynamic commander_dynamic = nullptr;
  PhaseSideModifier side_modifier = nullptr;
  PhaseRelationKind relation_kind = nullptr;
  std::uintptr_t combat_primary_vtable = 0;
  std::uintptr_t combat_secondary_vtable = 0;
  PhaseMiscBindings misc;
};

// Address calculation only. Resolving the current game's entities is supplied
// by the v2 adapter so neither the old build nor process discovery is reused.
PhaseBindings BindPhaseImage(std::uintptr_t image_base,
                             std::string_view executable_sha256) noexcept;

struct PhaseEnvironment {
  void *context = nullptr;
  void *(*resolve_internal_army)(void *, std::int32_t) = nullptr;
  void *(*resolve_character)(void *, std::int32_t) = nullptr;
  void *(*resolve_province)(void *, std::int32_t) = nullptr;
  bool (*read_army_gathering)(void *, std::int32_t, bool &) = nullptr;
  void *(*resolve_regiment)(void *, std::int32_t) = nullptr;
};

struct NativeCombatPhaseSide {
  std::vector<std::int32_t> ordered_army_ids;
  std::vector<game::CombatPhaseCandidateSourceRowV3> ordered_candidates;
  std::int32_t commander_character_id = -1;
  std::int32_t primary_participant_character_id = -1;
  std::int32_t strength_raw = 0;
  std::int64_t army_size_raw = 0;
  std::int64_t dynamic_advantage_raw = 0;
  bool source_vector_equivalence = false;
};

struct NativeCombatPhase {
  bool available = false;
  std::array<NativeCombatPhaseSide, 2> sides;
  // Native side difference with zero rolls. The separately recorded constructor
  // ledger contains all nonreligious sources; religion/rites operands remain implementation pending.
  std::int64_t dynamic_advantage_at_zero_roll_raw = 0;
  game::CombatAdvantageModelV3TestOnly nonreligious_advantage_model;
  bool nonreligious_constructor_ready = false;
  bool religion_constructor_ready = false;
  std::int64_t base_nonreligious_accumulator_raw = 0;
  std::vector<game::ContextualAdvantageReligionSourceSnapshot> religion_constructor_sources;
  std::string unavailable_reason;
};

struct NonReligiousPhaseOperands {
  game::CombatPhaseInputsV3 fields;
  NativeCombatPhase native_sides;
  bool non_religious_ready = false;
  std::vector<std::string> completed_domains;
  std::vector<std::string> failed_domains;
  std::vector<std::string> deferred_domains{"religion_and_rites"};
};

enum class ReadNativeCombatPhaseResult {
  available, requires_paused, no_played_character, base_inputs_unavailable,
  native_phase_unavailable, unavailable
};

// Caller runs this on CK3's owning thread with an already captured paused
// scope and v2 inputs. Offline tests supply only fixture-owned native objects.
ReadNativeCombatPhaseResult ReadNativeCombatPhase(
    const PhaseBindings &, const PhaseEnvironment &, const game::Snapshot &,
    const game::CombatSimulationInputsSnapshot &, NativeCombatPhase &,
    bool include_constructor_religion = false) noexcept;

// Existing v2 owning-thread adapter calls this only after v2 composition
// succeeds. It directly reads the native nonreligious context without the full
// phase AST, traits, culture or miscellaneous migration readers.
bool ReadContextualAdvantageInputs(
    const PhaseBindings &, const game::Snapshot &paused_scope,
    const game::CombatSimulationInputsSnapshot &already_read_v2,
    game::ContextualAdvantageSnapshot &) noexcept;

// Private projection using the version-independent DTO. Complete v3 remains
// unavailable because religion/rites operands remain implementation pending;
// migrated nonreligious values remain accessible in the diagnostic serializer.
game::ReadCombatSimulationInputsV3Result ReadCombatPhaseInputs(
    const PhaseBindings &, const PhaseEnvironment &, const game::Snapshot &,
    const game::CombatSimulationInputsSnapshot &,
    game::CombatPhaseInputsV3 &) noexcept;

game::ReadCombatSimulationInputsV3Result ReadCombatSimulationInputsV3(
    const PhaseBindings &, const game::Snapshot &paused_scope,
    const game::CombatSimulationInputsRequest &,
    game::CombatSimulationInputsV3Snapshot &) noexcept;

bool ReadNonReligiousPhaseOperands(
    const PhaseBindings &, const PhaseEnvironment &, const game::Snapshot &,
    const game::CombatSimulationInputsSnapshot &, NonReligiousPhaseOperands &) noexcept;

std::string SerializeCombatPhaseInputsV3(const game::CombatPhaseInputsV3 &);
std::string SerializeNonReligiousPhaseOperands(const NonReligiousPhaseOperands &);

} // namespace xar::ck3_12002
