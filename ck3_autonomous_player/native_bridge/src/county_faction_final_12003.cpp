#include "xar_bridge/county_faction_final_12003.hpp"
#include "xar_bridge/ck3_12002_faction_alerts.hpp"

#include <cstddef>
#include <cstring>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_12002 {
namespace {

bool ReadScalar(const PlayerFactionAlertsAccessV1 &access, const void *address,
                void *output, std::size_t size) noexcept {
  if (!address || !output) return false;
  if (access.read_memory)
    return access.read_memory(access.context, address, output, size);
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(output, address, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool InvokeScore(NativeCountyFactionJoinScore12003 function, void *faction,
                 void *county_title, std::int64_t &output) noexcept {
  if (!function) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return function(faction, &output, county_title) == &output;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool InvokeCanAdd(NativeCountyFactionCanAdd12003 function, void *faction,
                  void *county_title, bool &output) noexcept {
  if (!function) return false;
#if defined(_MSC_VER)
  __try {
#endif
    output = function(faction, county_title);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

} // namespace

CountyFactionFinalBindings12003 BindCountyFactionFinals12003(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  CountyFactionFinalBindings12003 bindings{};
  if (!module_base || !exact_build_admitted) return bindings;
  bindings.join_score = reinterpret_cast<NativeCountyFactionJoinScore12003>(
      module_base + 0x2602570);
  bindings.can_add = reinterpret_cast<NativeCountyFactionCanAdd12003>(
      module_base + 0x26028E0);
  bindings.leave_score_threshold = reinterpret_cast<const std::int32_t *>(
      module_base + 0x5C694C0);
  return bindings;
}

bool ReadCountyFactionFinals12003(
    const CountyFactionFinalBindings12003 &bindings,
    const PlayerFactionAlertsAccessV1 &access, void *faction, void *county_title,
    const void *county_member_row,
    CountyFactionFinalObservation12003 &output) noexcept {
  output = {};
  if (!faction || !county_title || !county_member_row) return false;
  std::uint8_t queued = 0;
  std::int32_t threshold = 0;
  std::int64_t score = 0;
  bool can_add = false;
  if (ReadScalar(access, static_cast<const std::byte *>(county_member_row) + 0x0C,
                 &queued, sizeof queued))
    output.removal_queued = queued != 0;
  if (ReadScalar(access, bindings.leave_score_threshold, &threshold, sizeof threshold))
    output.leave_score_threshold = threshold;
  if (InvokeScore(bindings.join_score, faction, county_title, score))
    output.join_score_raw = score;
  if (InvokeCanAdd(bindings.can_add, faction, county_title, can_add))
    output.can_add_county = can_add;
  return output.join_score_raw.has_value() && output.can_add_county.has_value() &&
         output.removal_queued.has_value() && output.leave_score_threshold.has_value();
}

} // namespace xar::ck3_12002
