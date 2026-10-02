#pragma once

#include <cstdint>
#include <optional>

namespace xar::ck3_12002 {

struct PlayerFactionAlertsAccessV1;

#if defined(_MSC_VER)
#define XAR_COUNTY_FACTION_12003_CALL __fastcall
#else
#define XAR_COUNTY_FACTION_12003_CALL
#endif

using NativeCountyFactionJoinScore12003 = std::int64_t *(XAR_COUNTY_FACTION_12003_CALL *)(
    void *faction, std::int64_t *output, void *county_title);
using NativeCountyFactionCanAdd12003 = bool(XAR_COUNTY_FACTION_12003_CALL *)(
    void *faction, void *county_title);

#undef XAR_COUNTY_FACTION_12003_CALL

struct CountyFactionFinalBindings12003 {
  NativeCountyFactionJoinScore12003 join_score = nullptr;
  NativeCountyFactionCanAdd12003 can_add = nullptr;
  const std::int32_t *leave_score_threshold = nullptr;
};

struct CountyFactionFinalObservation12003 {
  std::optional<std::int64_t> join_score_raw;
  std::optional<std::int32_t> leave_score_threshold;
  std::optional<bool> can_add_county;
  std::optional<bool> removal_queued;
};

CountyFactionFinalBindings12003 BindCountyFactionFinals12003(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

// The caller already round-trips the actual TitleID and CFaction* member row.
// Failed reads remain absent; independent successful values are retained.
bool ReadCountyFactionFinals12003(
    const CountyFactionFinalBindings12003 &bindings,
    const PlayerFactionAlertsAccessV1 &access, void *faction, void *county_title,
    const void *county_member_row,
    CountyFactionFinalObservation12003 &output) noexcept;

} // namespace xar::ck3_12002
