#include "xar_bridge/person_natural_lineage_clock_12004.hpp"

#include <atomic>
#include <windows.h>

namespace xar::ck3_12004 {
namespace {
std::atomic<std::uint64_t> g_next_sequence{0};
}

PersonInstalledTransferEvent12004 NextPersonNaturalLineageEvent12004() noexcept {
  return {reinterpret_cast<std::uintptr_t>(&g_next_sequence),
          g_next_sequence.fetch_add(1, std::memory_order_relaxed) + 1,
          GetCurrentThreadId()};
}

} // namespace xar::ck3_12004
