#pragma once

#include <Windows.h>

#include <array>
#include <atomic>
#include <cstdint>
#include <string>

namespace xar::ck3_11906 {

inline constexpr std::size_t kAdvantageComponentMaximumMaterializationsV1 = 8;

struct AdvantageSideComponentsV1 {
  std::int32_t side_index = -1;
  std::int32_t roll = 0;
  std::int32_t commander_character_id = -1;
  std::int64_t roll_raw = 0;
  std::int64_t commander_raw = 0;
  std::int64_t aggregator_raw = 0;
  std::int64_t total_raw = 0;
  std::uint32_t helper_calls = 0;
  bool complete = false;
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
  bool complete = false;
};

struct AdvantageComponentObserverV1 {
  std::atomic<bool> armed{false};
  std::atomic<std::uint32_t> count{0};
  std::atomic<std::uint32_t> failure_flags{0};
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
  std::array<Site, 4> sites{};
  std::uint32_t failure_flags = 0;
};

// All four patches are optional, exact-build only, and installed/removed at
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
