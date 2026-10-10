#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::conception_last_child_date {

inline constexpr std::uintptr_t kLoadedMonthShiftSlotRva = 0x5C69E84;
inline constexpr std::uintptr_t kMonthTableRva = 0x444C340;
inline constexpr std::uintptr_t kDayTableRva = 0x444C4B0;
inline constexpr std::uintptr_t kMonthLengthTableRva = 0x4513BD0;
inline constexpr std::uintptr_t kCharacterFallbackSlotRva = 0x5C67570;
inline constexpr std::size_t kCharacterFamilyOffset = 0x1A8;
inline constexpr std::size_t kFamilyChildIdsOffset = 0x38;
inline constexpr std::size_t kFamilyChildCountOffset = 0x44;
inline constexpr std::size_t kSelectedCharacterDateOffset = 0x60;

using ReadMemory = bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;
// The owner's existing actual4 full-ID resolver; null means native lookup
// miss and requests the actual loaded fallback, not an invented date.
using ResolveCharacter = void *(*)(void *, std::int32_t) noexcept;

struct Access {
  bool exact_build_admitted = false;
  std::string_view executable_sha256{};
  std::uintptr_t image_base = 0;
  void *context = nullptr;
  ReadMemory read_memory = nullptr;
  ResolveCharacter resolve_character = nullptr;
};

// The existing current-household owner supplies the native first role and
// its actual2B958AF..2B9590F selection. Full generation IDs, final occurrence
// and native fallback stay distinct; this leaf does not create a new store,
// select the maximum birth date or substitute a null/default Character.
struct CurrentHouseholdSourceInputs {
  std::int32_t first_character_id = -1;
  std::uint32_t provider_mode_raw = 3;
  std::optional<bool> first_family_present{};
  std::optional<std::int32_t> child_count_raw{};
  std::optional<std::uint32_t> last_requested_full_id_raw{};
  std::optional<std::uint32_t> selected_full_id_raw{};
  std::optional<bool> selected_is_native_fallback{};
  std::uintptr_t selected_character = 0;
};

struct Observation {
  CurrentHouseholdSourceInputs source{};
  bool date_inputs_available = false;
  std::string_view unavailable_reason = "last_child_date_binding_unavailable";
  std::string_view status = "unavailable";
  bool date_helper_demanded = false;
  std::optional<std::int64_t> selected_date_storage_raw64{};
  std::optional<std::int32_t> loaded_month_shift_raw_i32{};
  std::optional<std::int32_t> current_date_raw_i32{};
  std::optional<std::int32_t> adjusted_date_raw_i32{};
  std::optional<std::int64_t> adjusted_date_storage_raw64{};
  std::optional<bool> recent_child_branch_passed{};
};

struct CurrentInputObservation {
  bool source_inputs_available = false;
  std::string_view unavailable_reason = "last_child_date_binding_unavailable";
  CurrentHouseholdSourceInputs source{};
};

// Reuses the owning query's current full-ID resolver and guarded memory
// callback. It does not walk, create or cache a separate Character store.
// Store-null follows the actual provider before reading the final array ID;
// ordinary lookup/generation miss selects loaded5C67570, with identities
// retained separately. The parent still owns paused frame validation.
CurrentInputObservation ReadCurrentHouseholdSourceInputs(
    const Access &, const void *first_character, std::int32_t first_character_id,
    std::uint32_t provider_mode_raw = 3) noexcept;

// Only memory reads and source-derived arithmetic on caller-owned copies.
// Family-absent/count0 bypasses demand no selected date/clock/shift/table read.
// The owning query retains its existing paused before/after frame guard.
// A passed branch is one provider condition, not couple probability,
// monthly scheduling, native provider execution or active pregnancy.
Observation Read(const Access &, const CurrentHouseholdSourceInputs &) noexcept;

} // namespace xar::ck3_12004::conception_last_child_date
