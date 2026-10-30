#include "xar_bridge/player_faction_alerts_v1_mailbox.hpp"
#include <cassert>
#include <cstdlib>

namespace {
unsigned legacy_parse_calls = 0;
struct UnusedLegacyParseAudit {
  ~UnusedLegacyParseAudit() { assert(legacy_parse_calls == 0); }
} unused_legacy_parse_audit;
} // namespace

namespace xar::ck3_11906 {
bool ParsePlayerFactionAlertsExpectedRevisionV1(
    std::string_view, std::uint64_t &) noexcept {
  ++legacy_parse_calls;
  // The whole serializer is exercised; the unrelated legacy public Handle is not.
  std::abort();
}
} // namespace xar::ck3_11906
