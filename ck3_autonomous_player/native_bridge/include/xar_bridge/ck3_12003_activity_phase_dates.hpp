#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::activity_phase_dates {

inline constexpr std::string_view kSchema = "ck3_12003_activity_phase_dates_v1";
inline constexpr std::string_view kExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
using NativeDateGetter = const void *(*)(const void *actual_activity);

struct Bindings {
  bool enabled = false;
  NativeDateGetter active_start_date = nullptr;
  NativeDateGetter progress_phase_date = nullptr;
};
struct Terms {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::int32_t date_raw = 0;
  std::uint64_t capture_epoch = 0;
  std::optional<std::int32_t> active_start_date_raw;
  std::optional<std::int32_t> progress_phase_date_raw;
};

Bindings BindActivityPhaseDatesImage12003(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// Caller supplies a borrowed, resolved CActivity from the same owner-thread
// snapshot. This leaf neither discovers an activity nor changes its ownership.
// GetProgressPhaseDate is a runtime phase progression schedule, never the
// entire activity end/return date. Preserve all native raw int32 values,
// including sentinel values; no Date subtraction or validity inference.
bool ReadActivityPhaseDates12003(const Bindings &, const void *actual_activity,
    std::int32_t date_raw, std::uint64_t capture_epoch, Terms &) noexcept;
std::string SerializeActivityPhaseDates12003(const Terms &);

} // namespace xar::ck3_12003::religion::activity_phase_dates
