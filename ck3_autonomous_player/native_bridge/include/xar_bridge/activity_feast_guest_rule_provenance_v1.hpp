#pragma once

#include "xar_bridge/activity_cost_slot12_passive_v1.hpp"

#include <array>
#include <cstdint>
#include <mutex>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityGuestRuleProvenanceExeSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::uintptr_t kActivityGuestRuleRefreshRvaV1 = 0x28CF3A0;
inline constexpr std::uintptr_t kActivityGuestRuleEffectRvaV1 = 0x3380410;
inline constexpr std::uintptr_t kActivityGuestRuleEffectReturnRvaV1 = 0x28CF51A;
inline constexpr std::uintptr_t kActivityGuestRuleRefreshReturnRvaV1 = 0x10B0A61;
inline constexpr std::size_t kActivityGuestRuleRefreshPatchBytesV1 = 15;
inline constexpr std::size_t kActivityGuestRuleEffectPatchBytesV1 = 18;
inline constexpr std::size_t kActivityGuestRuleMaxRulesV1 = 64;
inline constexpr std::size_t kActivityGuestRuleMaxIdsV1 = 4096;

struct ActivityGuestRuleProvenanceRuleV1 {
  std::uintptr_t definition = 0;
  std::uint32_t native_key_hash = 0;
  std::int32_t priority = -1;
  std::uint32_t raw_begin = 0;
  std::uint32_t raw_count = 0;
  std::uint32_t filtered_begin = 0;
  std::uint32_t filtered_count = 0;
};

struct ActivityGuestRuleProvenanceCaptureV1 {
  std::uint64_t sequence = 0;
  ActivityCostSlot12FrameV1 frame{};
  std::uintptr_t planner = 0;
  std::uintptr_t activity_type = 0;
  std::uintptr_t active_rules = 0;
  std::uintptr_t filtered_groups = 0;
  std::uint64_t group_fingerprint = 0;
  std::uint64_t active_rule_fingerprint = 0;
  std::int32_t planning_stage = -1;
  std::uint32_t rule_count = 0;
  std::uint32_t raw_id_count = 0;
  std::uint32_t filtered_id_count = 0;
  bool overflow = false;
  bool native_read_failed = false;
  std::array<ActivityGuestRuleProvenanceRuleV1,
             kActivityGuestRuleMaxRulesV1> rules{};
  std::array<std::uint32_t, kActivityGuestRuleMaxIdsV1> raw_ids{};
  std::array<std::uint32_t, kActivityGuestRuleMaxIdsV1> filtered_ids{};
};

enum class ActivityGuestRuleProvenanceStatusV1 {
  observed,
  exact_build_rejected,
  no_normal_refresh,
  frame_changed,
  planner_unavailable,
  rule_unavailable,
  ambiguous_rule,
  capture_overflow,
  native_read_failed,
};

struct ActivityGuestRuleProvenanceResultV1 {
  ActivityGuestRuleProvenanceStatusV1 status =
      ActivityGuestRuleProvenanceStatusV1::exact_build_rejected;
  std::uint64_t normal_refresh_sequence = 0;
  std::uint32_t native_key_hash = 0;
  std::uint32_t raw_rule_character_count = 0;
  std::uint32_t filtered_rule_character_count = 0;
  bool candidate_membership = false;
  std::array<std::uint32_t, kActivityGuestRuleMaxIdsV1> filtered_ids{};
};

struct ActivityGuestRuleProvenanceObserverV1 {
  ActivityCostSlot12EnvironmentV1 environment{};
  std::array<std::uint8_t, kActivityGuestRuleRefreshPatchBytesV1>
      refresh_original{};
  std::array<std::uint8_t, kActivityGuestRuleEffectPatchBytesV1>
      effect_original{};
  void *refresh_trampoline = nullptr;
  void *effect_trampoline = nullptr;
  bool installed = false;
  ActivityGuestRuleProvenanceCaptureV1 working{};
  std::mutex capture_mutex{};
  ActivityGuestRuleProvenanceCaptureV1 latest{};
};

// These seams are also used by the focused fixture. The original scripted
// effect and original refresh are called only by their hooks, once each.
bool BeginActivityGuestRuleRefreshV1(
    ActivityGuestRuleProvenanceObserverV1 &observer,
    std::uintptr_t caller_return, std::uintptr_t planner,
    std::uintptr_t active_rules, std::uintptr_t filtered_groups) noexcept;
void RecordActivityGuestRuleEffectReturnV1(
    ActivityGuestRuleProvenanceObserverV1 &observer,
    std::uintptr_t caller_return, std::uintptr_t effect,
    std::uintptr_t temporary_output) noexcept;
void FinishActivityGuestRuleRefreshV1(
    ActivityGuestRuleProvenanceObserverV1 &observer) noexcept;

ActivityGuestRuleProvenanceResultV1 ReadActivityGuestRuleProvenanceV1(
    ActivityGuestRuleProvenanceObserverV1 &observer,
    const ActivityCostSlot12FrameV1 &expected, std::uintptr_t planner,
    std::uint32_t native_key_hash, std::uint32_t candidate_character_id) noexcept;

bool VerifyActivityGuestRuleProvenanceExactAbiV1(
    const ActivityCostSlot12EnvironmentV1 &environment) noexcept;
bool InstallActivityGuestRuleProvenanceV1(
    ActivityGuestRuleProvenanceObserverV1 &observer,
    const ActivityCostSlot12EnvironmentV1 &environment) noexcept;
std::string_view ActivityGuestRuleProvenanceStatusKeyV1(
    ActivityGuestRuleProvenanceStatusV1 status) noexcept;

} // namespace xar::bridge
