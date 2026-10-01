// Reuse the already qualified production-reader graph without executing its
// thirteen-case runner again. This target only exercises its new wire boundary.
#define main OriginalPrisonerWarRetentionFixtureMain
#include "ck3_12002_prisoner_war_retention_test.cpp"
#undef main

#include "xar_bridge/ck3_12002_prisoner_mailbox.hpp"
#include <filesystem>
#include <fstream>

namespace {
bool WriteActualObservation(Fixture &fixture, const std::filesystem::path &path,
                            std::uint64_t sequence, bool expected_empty) {
  Observation observed{};
  if (ReadWarPrisonerReleasePairsV1(fixture.bindings, fixture.war_id, observed) !=
      Result::available || observed.release_pairs.empty() != expected_empty)
    return false;
  const auto payload = xar::ck3_12002::SerializePrisonerWarRetentionV1(observed);
  if (payload.empty()) return false;
  const auto step = "query-war-prisoner-release-pairs-v1-" +
      std::to_string(fixture.war_id);
  if (xar::ck3_12002::ParsePrisonerWarRetentionStep12002(step) != fixture.war_id)
    return false;
  // The envelope matches the existing handler's public wire. The observation
  // within it came from the production reader and production serializer above.
  const auto wire = "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"offline-prisoner-war-wire\",\"ok\":true,\"result\":{"
      "\"step\":\"" + step + "\",\"accepted\":true,\"status\":\"available\","
      "\"query_sequence\":" + std::to_string(sequence) +
      ",\"snapshot_revision\":1,\"war_prisoner_release_pairs_v1\":" + payload +
      ",\"read_only\":true,\"backend_id\":\"native-headless\"}}\n";
  std::ofstream stream(path, std::ios::binary);
  stream << wire;
  return stream.good();
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path output(argv[1]);
  std::filesystem::create_directories(output);
  int passed = 0;
  {
    Fixture fixture;
    // Played attacker holds the defender's first heir: a real positive
    // retention pair for the existing player's ransom consumer.
    fixture.Imprison(5, 0);
    if (Check(WriteActualObservation(fixture, output / "positive.json", 1, false),
              "production reader to wire positive pair")) ++passed;
  }
  {
    Fixture fixture;
    if (Check(WriteActualObservation(fixture, output / "empty.json", 2, true),
              "production reader to wire complete known-empty")) ++passed;
  }
  {
    using xar::ck3_12002::ParsePrisonerWarRetentionStep12002;
    if (Check(ParsePrisonerWarRetentionStep12002(
                  "query-war-prisoner-release-pairs-v1-83886081") == Fixture::war_id &&
              !ParsePrisonerWarRetentionStep12002("query-war-prisoner-release-pairs-v1-") &&
              !ParsePrisonerWarRetentionStep12002("query-war-prisoner-release-pairs-v1-0") &&
              !ParsePrisonerWarRetentionStep12002("query-war-prisoner-release-pairs-v1-83886081-extra") &&
              !ParsePrisonerWarRetentionStep12002("query-player-prisoner-collection-private-v1"),
              "exact existing step matcher")) ++passed;
  }
  std::cout << "prisoner war-retention production wire fixtures " << passed << "/3\n";
  return passed == 3 ? 0 : 1;
}
