#include "xar_bridge/first_heir_pre_read_diagnostic_v1.hpp"
#include <cstdio>

namespace {
unsigned checks = 0;
unsigned failures = 0;
unsigned cases = 0;
void Check(bool condition) noexcept {
  ++checks;
  if (!condition) ++failures;
}
xar::game::Snapshot Stable() {
  xar::game::Snapshot s{};
  s.date_raw = 53290128;
  s.paused = true;
  s.map_ready = true;
  s.has_played_character = true;
  s.played_character_alive = true;
  s.player_id = 29829;
  s.played_character_id = 29829;
  return s;
}
void Case(const std::optional<xar::game::Snapshot> &previous,
          const xar::game::Snapshot &observed, bool read_ok,
          std::string_view expected, unsigned expected_reads) {
  ++cases;
  xar::game::Snapshot before{};
  unsigned reads = 0;
  bool completed = true;
  const auto failure = xar::bridge_detail::FirstHeirPreReadFailureV1(
      previous, before, [&](xar::game::Snapshot &out) {
        ++reads;
        out = observed;
        return read_ok;
      }, completed);
  Check(failure == expected);
  Check(reads == expected_reads);
  Check(completed == (expected_reads != 0 && read_ok));
  if (failure.empty()) return;
  const auto error = xar::bridge_detail::FirstHeirPreReadErrorV1(
      failure, completed, previous, before);
  Check(error.starts_with("current first-heir relationship frame changed; pre_read_guard="));
  Check(error.find(failure) != std::string::npos);
  Check(error.find('"') == std::string::npos && error.find('\n') == std::string::npos);
  if (!completed) Check(error.find("; observed=unknown;") != std::string::npos);
  else Check(error.find("; observed=date_raw:53290128,") != std::string::npos);
  if (!previous) Check(error.find("; cached=unknown;") != std::string::npos);
  if (failure == "snapshot_not_equal") {
    Check(error.find("differing_fields=played_character_event_trait_membership;") != std::string::npos);
    Check(error.find("played_character_event_trait_membership_present:0") != std::string::npos);
    Check(error.find("played_character_event_trait_membership_present:1") != std::string::npos);
  }
}
}

int main() {
  const auto valid = Stable();
  Case(std::nullopt, valid, true, "previous_snapshot_missing", 0);
  Case(valid, valid, false, "snapshot_read_failed", 1);
  auto trait_changed = valid;
  trait_changed.played_character_event_trait_membership.emplace();
  Case(valid, trait_changed, true, "snapshot_not_equal", 1);
  auto changed = valid;
  changed.paused = false;
  changed.map_ready = false;
  Case(changed, changed, true, "not_paused", 1);
  changed = valid;
  changed.map_ready = false;
  changed.has_played_character = false;
  Case(changed, changed, true, "map_not_ready", 1);
  changed = valid;
  changed.has_played_character = false;
  changed.played_character_alive = false;
  Case(changed, changed, true, "played_character_missing", 1);
  changed = valid;
  changed.played_character_alive = false;
  Case(changed, changed, true, "played_character_not_alive", 1);
  Case(valid, valid, true, {}, 1);
  std::printf("first_heir_pre_read_diagnostic cases=%u checks=%u failures=%u game_calls=0\n", cases, checks, failures);
  return failures == 0 && cases == 8 ? 0 : 1;
}
