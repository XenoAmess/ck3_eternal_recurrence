#pragma once

#include "xar_bridge/ck3_12003.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::church_tax_inputs {

inline constexpr std::string_view kSchema = "ck3_12003_player_church_tax_inputs_v1";
inline constexpr std::uintptr_t kIncomeContextRva = 0x28BFC70;
inline constexpr std::uintptr_t kCharacterFaithRva = 0x289E750;
inline constexpr std::uintptr_t kFaithLeaseContractRva = 0x2442E20;
inline constexpr std::uintptr_t kLeaseLiegeRva = 0x2A22FA0;
inline constexpr std::uintptr_t kTopLeaseLiegeDirectRva = 0x2A268A0;
inline constexpr std::uintptr_t kPriorShareRva = 0x31BFA20;
inline constexpr std::uintptr_t kRulerShareRva = 0x31BFC50;
inline constexpr std::uintptr_t kIncomeRulesRva = 0x31C01B0;
inline constexpr std::uintptr_t kStringDestroyRva = 0x856050;
inline constexpr std::uintptr_t kLeaseLiegeLabelRva = 0x449F2E0;
inline constexpr std::uintptr_t kTopLeaseLiegeDirectLabelRva = 0x46DB418;

struct alignas(8) NativeString32 { std::array<std::byte, 32> bytes{}; };
static_assert(sizeof(NativeString32) == 32);
using ObjectGetter = void *(*)(void *);
using LeaseLiege = std::int32_t *(*)(void *, std::int32_t *, std::int32_t);
using TopLeaseLiegeDirect = std::int32_t *(*)(std::int32_t *, std::int32_t);
using PriorShare = std::int64_t *(*)(void *, std::int64_t *, void *,
    std::int64_t, std::int64_t, std::int32_t, std::int32_t, std::int64_t,
    const void *, void *);
using RulerShare = std::int64_t *(*)(void *, std::int64_t *, void *,
    std::int32_t, bool, std::int64_t, void *);
using IncomeRules = NativeString32 *(*)(void *, NativeString32 *, void *, void *);
using StringDestroy = void (*)(NativeString32 *);

struct Bindings {
  bool enabled = false;
  ck3_12002::CoreBindings core{};
  void **game_state_slot = nullptr;
  ObjectGetter income_context = nullptr, character_faith = nullptr;
  ObjectGetter faith_lease_contract = nullptr;
  LeaseLiege lease_liege = nullptr;
  TopLeaseLiegeDirect top_lease_liege_direct = nullptr;
  PriorShare prior_share = nullptr;
  RulerShare ruler_share = nullptr;
  IncomeRules income_rules = nullptr;
  StringDestroy string_destroy = nullptr;
  const void *lease_liege_label = nullptr, *top_lease_liege_direct_label = nullptr;
};

struct Terms {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<std::int32_t> income_context_character_id;
  std::optional<std::uint32_t> income_context_faith_id;
  std::optional<std::int32_t> actual_lessee_character_id;
  std::optional<std::int32_t> lease_liege_character_id;
  std::optional<std::int32_t> top_lease_liege_direct_character_id;
  std::optional<std::int64_t> lease_liege_share_raw;
  std::optional<std::int64_t> top_lease_liege_direct_share_raw;
  std::optional<std::int64_t> remaining_before_ruler_share_raw;
  std::optional<std::int64_t> effective_ruler_tax_share_raw;
  std::optional<std::int64_t> native_configured_ruler_tax_ceiling_raw;
  std::optional<std::string> income_rules_text;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindPlayerChurchTaxInputsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
// Actual owner/frame are supplied by the existing paused religion mailbox.
// All raw shares are fractions, never a monthly account or promised reward.
bool ReadPlayerChurchTaxInputs12003(const Bindings &, void *actual_played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Terms &) noexcept;
std::string SerializePlayerChurchTaxInputs12003(const Terms &);

} // namespace xar::ck3_12003::religion::church_tax_inputs
