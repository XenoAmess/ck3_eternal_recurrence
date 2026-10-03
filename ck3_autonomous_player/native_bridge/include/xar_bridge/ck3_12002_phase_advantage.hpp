#pragma once

#include "xar_bridge/ck3_12002_combat.hpp"
#include "xar_bridge/combat_v3.hpp"

namespace xar::ck3_12002 {

struct PhaseEnvironment;

inline constexpr std::uintptr_t kAdvantageRuleDatabaseRva = 0x8FC3E0;
inline constexpr std::uintptr_t kAdvantageSupplySelectorRva = 0x25870B0;
inline constexpr std::uintptr_t kAdvantageDebtSelectorRva = 0x2BCA620;
inline constexpr std::uintptr_t kAdvantageResolveTreasuryRva = 0x9D6DF0;
inline constexpr std::uintptr_t kAdvantageCharacterGovernmentRva = 0x28C2E10;
inline constexpr std::uintptr_t kAdvantageModifierFlagRva = 0x23037B0;
inline constexpr std::uintptr_t kAdvantageProvinceModifierRva = 0x2C23360;
inline constexpr std::uintptr_t kAdvantageModifierValueRva = 0x2C4D550;
inline constexpr std::uintptr_t kAdvantageSupplyUnitStorageRva = 0x5D1EB68;
inline constexpr std::uintptr_t kAdvantageSupplyThresholdsRva = 0x5456498;
inline constexpr std::uintptr_t kAdvantageSupplyThresholdCountRva = 0x54564A4;

struct AdvantageNativeIdArray {
  const std::int32_t *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};
using SelectAdvantageSupply = void *(*)(const AdvantageNativeIdArray *);
using SelectAdvantageDebt = std::int32_t (*)(void *, std::int32_t);
using ResolveAdvantageTreasury = void *(*)(const std::int32_t *);
using AdvantageModifierFlag = bool (*)(void *, std::int32_t);
using ReadAdvantageProvinceModifier = std::int64_t *(*)(
    std::int64_t *, void *, std::int32_t, std::int32_t, void *);
using ReadAdvantageModifierValue = std::int64_t *(*)(
    std::int64_t *, void *, std::int32_t, void *, std::int64_t, std::int32_t);

// These operands are installed only by the exact .3 adapter. The pure target
// predicate reads its main Rite; canonical native NullObjects preserve absence.
struct ConstructorReligionBindings {
  bool enabled = false;
  void **rite_storage_slot = nullptr;
  void **faith_storage_slot = nullptr;
  void **null_rite_slot = nullptr;
  void **null_faith_slot = nullptr;
  bool (*target_faith_is_unreformed)(void *) = nullptr;
};

struct AdvantageBindings {
  bool enabled = false;
  GetCombatRules get_rules = nullptr;
  ConstructorReligionBindings constructor_religion;
  SelectAdvantageSupply select_supply = nullptr;
  SelectAdvantageDebt select_debt = nullptr;
  ResolveAdvantageTreasury resolve_treasury = nullptr;
  GetCharacterModifierAggregator get_modifier_aggregator = nullptr;
  GetProvinceTerrain get_terrain = nullptr;
  IsHoldingDefender is_holding_defender = nullptr;
  bool (*province_has_holding)(void *) = nullptr;
  void *(*get_government)(void *) = nullptr;
  AdvantageModifierFlag has_modifier_flag = nullptr;
  ReadAdvantageProvinceModifier read_province_modifier = nullptr;
  ReadAdvantageModifierValue read_modifier_value = nullptr;
  void **regiment_storage_slot = nullptr;
  void **supply_unit_storage_slot = nullptr;
  const std::int32_t *const *supply_thresholds = nullptr;
  const std::int32_t *supply_threshold_count = nullptr;
};

// Uses only address calculation after exact hash selection. The terrain,
// character and regiment bindings come from the same build's combat adapter.
AdvantageBindings BindAdvantageImage(std::uintptr_t image_base,
    std::string_view executable_sha256, const CombatBindings &) noexcept;

struct AdvantageLedgerEntry {
  void *effect = nullptr;
  // Native 0x2586C90 stores the scaled, unsigned-by-side contribution here,
  // not the scale. Defender subtraction is applied to the shell accumulator.
  std::int64_t contribution_raw = 0;
};
static_assert(sizeof(AdvantageLedgerEntry) == 16);

struct NonReligiousAdvantagePlan {
  bool nonreligious_available = false;
  bool religion_constructor_ready = false;
  std::int64_t base_nonreligious_accumulator_raw = 0;
  std::vector<game::ContextualAdvantageReligionSourceSnapshot> religion_constructor_sources;
  bool holding_defender = false;
  std::array<std::vector<AdvantageLedgerEntry>, 2> ledgers;
  game::CombatAdvantageModelV3TestOnly model;
  std::string unavailable_reason;
};

// Builds every nonreligious constructor stage from current native inputs.
// The two deferred religion stages remain explicit and model.available=false.
// No complete-advantage or Monte Carlo readiness is claimed from this plan.
bool BuildNonReligiousAdvantagePlan(const AdvantageBindings &,
    const PhaseEnvironment &, const game::CombatSimulationInputsSnapshot &,
    const std::array<void *, 2> &selected_commanders,
    NonReligiousAdvantagePlan &) noexcept;

// Completes only the contextual query's two closed faith constructor stages.
// The old nonreligious plan entry and full-v3 availability remain unchanged.
bool CompleteConstructorReligionPlan(const AdvantageBindings &,
    const PhaseEnvironment &, const game::CombatSimulationInputsSnapshot &,
    NonReligiousAdvantagePlan &) noexcept;

} // namespace xar::ck3_12002
