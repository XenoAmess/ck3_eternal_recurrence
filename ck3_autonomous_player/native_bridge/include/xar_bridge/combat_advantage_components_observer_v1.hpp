#pragma once

#include <Windows.h>

#include <array>
#include <atomic>
#include <cstdint>
#include <string>

namespace xar::ck3_11906 {

inline constexpr std::size_t kAdvantageComponentMaximumMaterializationsV1 = 8;
inline constexpr std::size_t kAdvantageAccoladeGateMaximumCallsV1 = 512;

enum class AdvantageAggregatorCallKindV1 : std::uint8_t {
  rejected = 0,
  nested_commander = 1,
  primary_side = 2,
};

struct AdvantageAggregatorCallDecisionV1 {
  AdvantageAggregatorCallKindV1 kind =
      AdvantageAggregatorCallKindV1::rejected;
  // 0 accepted; 1 null return; 2 unknown caller; 3 wrong combat;
  // 4 wrong side; 5 duplicate or wrong call order.
  std::uint32_t failure_gate = 0;
};

AdvantageAggregatorCallDecisionV1 ClassifyAdvantageAggregatorCallV1(
    bool value_present, bool combat_matches, std::uint32_t caller_rva,
    std::int32_t side_index, std::int32_t expected_side_index,
    std::uint32_t helper_calls, std::uint32_t nested_calls,
    std::uint32_t primary_calls) noexcept;

struct AdvantageSideComponentsV1 {
  std::int32_t side_index = -1;
  std::int32_t roll = 0;
  std::int32_t commander_character_id = -1;
  std::int64_t roll_raw = 0;
  std::int64_t commander_raw = 0;
  std::int64_t aggregator_raw = 0;
  std::int64_t total_raw = 0;
  std::uint32_t helper_calls = 0;
  std::uint32_t nested_aggregator_calls = 0;
  std::uint32_t primary_aggregator_calls = 0;
  bool complete = false;
};

// One original 0x251C200 invocation. The caller's RSI MAA entry pointer is
// outside this ABI, so the slot association remains explicitly unresolved.
struct AdvantageAccoladeGateV1 {
  std::uint32_t ordinal = 0;
  std::int32_t side_index = -1;
  std::int32_t accolade_id = -1;
  std::int32_t source_row_count = -1;
  bool all_rows_passed = false;
  bool stable = false;
};

struct AdvantageMaterializationV1 {
  std::uint32_t ordinal = 0;
  std::uint32_t thread_id = 0;
  std::uint32_t caller_rva = 0;
  std::int32_t combat_id = -1;
  std::int32_t date_raw = 0;
  std::int64_t base_raw = 0;
  std::int64_t resolved_raw = 0;
  std::array<AdvantageSideComponentsV1, 2> sides{};
  std::uint32_t refresh_side_count = 0;
  std::uint32_t accolade_gate_count = 0;
  std::array<AdvantageAccoladeGateV1,
             kAdvantageAccoladeGateMaximumCallsV1> accolade_gates{};
  bool complete = false;
};

struct AdvantageComponentObserverV1 {
  std::atomic<bool> armed{false};
  std::atomic<std::uint32_t> count{0};
  std::atomic<std::uint32_t> failure_flags{0};
  // Gate 0 means no unexpected aggregator invocation. 0xFFFFFFFF is the
  // brief first-writer reservation, never a completed wire value.
  std::atomic<std::uint32_t> first_aggregator_failure_gate{0};
  std::uint32_t first_aggregator_failure_thread_id = 0;
  std::uint32_t first_aggregator_failure_caller_rva = 0;
  std::uint64_t first_aggregator_failure_caller_address = 0;
  std::int32_t first_aggregator_failure_side_index = -1;
  std::int32_t first_aggregator_failure_expected_side_index = -1;
  std::uint32_t first_aggregator_failure_helper_calls = 0;
  bool first_aggregator_failure_value_present = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t combat = 0;
  std::int32_t combat_id = -1;
  std::uintptr_t current_date_slot = 0;
  std::uintptr_t current_date_object = 0;
  std::array<AdvantageMaterializationV1,
             kAdvantageComponentMaximumMaterializationsV1> records{};
};

struct AdvantageComponentDetoursV1 {
  struct Site {
    std::uintptr_t target = 0;
    void *trampoline = nullptr;
    std::array<std::uint8_t, 16> original{};
    std::uint8_t size = 0;
    bool installed = false;
  };
  std::array<Site, 7> sites{};
  std::uint32_t failure_flags = 0;
};

// All seven patches are optional, exact-build only, and installed/removed at
// managed paused quiescence. A failed rollback retains trampoline ownership.
bool InstallAdvantageComponentObserverV1(
    AdvantageComponentDetoursV1 &detours, AdvantageComponentObserverV1 &observer,
    std::uintptr_t module_base, bool exact_build_admitted,
    bool paused_quiescence_proven) noexcept;
bool UninstallAdvantageComponentObserverV1(
    AdvantageComponentDetoursV1 &detours,
    AdvantageComponentObserverV1 &observer) noexcept;
bool AdvantageComponentObserverCompleteV1(
    const AdvantageComponentObserverV1 &observer) noexcept;
std::string SerializeAdvantageComponentObserverV1(
    const AdvantageComponentObserverV1 &observer);

} // namespace xar::ck3_11906
