#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_rite.hpp"

#include <array>

namespace xar::ck3_12002::religion::conversion_cost {

inline constexpr std::uintptr_t kFinalPietyCostRva = 0x29A3DE0;
inline constexpr std::uintptr_t kConversionCommandVtableRva = 0x4770340;
inline constexpr std::uintptr_t kConversionCommandSecondaryVtableRva = 0x47703D8;
inline constexpr std::uintptr_t kRiteDatabaseGlobalRva = 0x5D1E2F8;
inline constexpr std::size_t kResourceExtensionOffset = 0x1B0;
inline constexpr std::size_t kPietyBalanceOffset = 0x110;

// The GUI builds this exact CConvertFaithAndRiteCommand locally before asking
// for its cost. Calling the cost member never submits or executes this object.
using NativeCostCommand = religion_conversion_rite::FaithAndRiteConversionCommand;
static_assert(sizeof(NativeCostCommand) == 0x30);
static_assert(offsetof(NativeCostCommand, actor_id) == 0x20);
static_assert(offsetof(NativeCostCommand, target_rite_id) == 0x24);
static_assert(offsetof(NativeCostCommand, pay_piety) == 0x28);
using FinalPietyCost = std::int32_t (*)(const NativeCostCommand *, void *tooltip);

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  void **rite_database = nullptr;
  ObjectGetter character_rite = nullptr;
  ObjectGetter character_faith = nullptr;
  ObjectGetter rite_faith = nullptr;
  FinalPietyCost final_piety_cost = nullptr;
  std::uintptr_t command_vtable = 0;
  std::uintptr_t command_secondary_vtable = 0;
};

enum class Failure {
  none, bindings_unavailable, played_character_unavailable, frame_not_paused,
  current_religion_unavailable, target_rite_unavailable, target_faith_unavailable,
  state_changed,
};
struct Cost {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t target_rite_id = kAbsentReference;
  std::optional<std::uint32_t> target_faith_id;
  std::optional<bool> same_faith;
  std::optional<std::int32_t> piety_points;
  std::optional<std::int64_t> piety_cost_raw;
  std::optional<std::int64_t> actor_piety_raw;
  std::optional<bool> can_afford_piety;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindReligionConversionCostImage12002(std::uintptr_t module_base,
                                            std::string_view executable_sha256) noexcept;
// Paused application-main read, with the played actor and the GUI's paid
// conversion semantics. This is neither final conversion legality nor an action.
bool ReadPlayedReligionConversionCost12002(const Bindings &, std::uint32_t target_rite_id,
                                          std::uint64_t capture_epoch, Cost &) noexcept;
const char *ConversionCostFailureKey(Failure) noexcept;
std::string SerializeReligionConversionCost12002(const Cost &);

} // namespace xar::ck3_12002::religion::conversion_cost
