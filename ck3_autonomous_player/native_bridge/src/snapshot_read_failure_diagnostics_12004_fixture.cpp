#include "xar_bridge/nonwar_private_snapshot_guard_diagnostics_v1.hpp"
#include <array>
#include <iostream>
#include <thread>

namespace diag = xar::bridge::ck3_12004;
using Stage = diag::SnapshotReadFailureStage12004;
namespace {
int failures{}, cases{}, reads{};
void Require(bool condition, const char *message) {
  if (!condition) { ++failures; std::cerr << "FAIL " << message << '\n'; }
}
template<class Read>
std::string Guard(Read &&read) {
  std::optional<xar::game::Snapshot> previous{xar::game::Snapshot{}};
  xar::game::Snapshot current{};
  return xar::bridge::NonwarPrivateSnapshotGuardFailureV1(
      false, true, std::uint64_t{6}, std::uint64_t{6}, previous, current,
      [&](xar::game::Snapshot &out) { ++reads; return read(out); });
}
bool Contains(const std::string &text, const std::string &needle) {
  return text.find(needle) != std::string::npos;
}
} // namespace
int main() {
  // New helper/guard checks only. These are synthetic owned values, not an
  // observation of the R93 child or an execution of the native adapter.
  constexpr std::array stages{
    Stage::core_reader_missing, Stage::core_prefix, Stage::foundation_missing,
    Stage::actor_resources, Stage::played_relationships, Stage::events,
    Stage::world, Stage::settlement};
  for (const auto stage : stages) {
    ++cases;
    const auto count_before = reads;
    const bool prefix_ready = stage != Stage::core_reader_missing && stage != Stage::core_prefix;
    const auto error = Guard([&](xar::game::Snapshot &) {
      diag::BeginSnapshotReadAttempt12004();
      if (prefix_ready)
        diag::CopySnapshotReadPrefix12004(-12345, 5, -7, true, true, true, -29829, false);
      diag::RecordSnapshotReadFailure12004(stage,
          stage == Stage::world ? std::optional<std::uint32_t>{2u} : std::nullopt,
          stage == Stage::settlement ? std::optional<std::uint32_t>{2u} : std::nullopt);
      return false;
    });
    Require(reads == count_before + 1, "one original read callback per stage");
    Require(Contains(error, "cause=current_snapshot_read_failed expected_revision=6 native_revision=6"), "existing guard cause/revisions preserved");
    Require(Contains(error, " read_stage=" + std::string(diag::SnapshotReadFailureStageName12004(stage))), "exact stage forwarded");
    Require(Contains(error, std::string(" prefix_ready=") + (prefix_ready ? "true" : "false")), "prefix qualification forwarded");
    Require(Contains(error, " date_raw=-12345") == prefix_ready, "failed core has no default qualified date");
    Require(Contains(error, " played_character_id=-29829") == prefix_ready, "signed copied full identifier preserved");
    Require(Contains(error, " world_read_result=2") == (stage == Stage::world), "only supplied world enum forwarded");
    Require(Contains(error, " settlement_read_result=2") == (stage == Stage::settlement), "only supplied settlement enum forwarded");
  }
  ++cases;
  diag::BeginSnapshotReadAttempt12004();
  diag::RecordSnapshotReadFailure12004(Stage::events);
  auto error = Guard([](xar::game::Snapshot &) { return false; });
  Require(!Contains(error, " read_stage="), "stale prior attempt rejected");

  ++cases;
  error = Guard([](xar::game::Snapshot &) {
    diag::BeginSnapshotReadAttempt12004();
    return false;
  });
  Require(!Contains(error, " read_stage="), "no failure stage remains unknown");

  ++cases;
  error = Guard([](xar::game::Snapshot &) {
    diag::BeginSnapshotReadAttempt12004();
    diag::RecordSnapshotReadFailure12004(Stage::world, std::uint32_t{0});
    diag::BeginSnapshotReadAttempt12004();
    diag::RecordSnapshotReadFailure12004(Stage::events);
    return false;
  });
  Require(!Contains(error, " read_stage="), "multiple attempts cannot qualify one read");

  ++cases;
  error = Guard([](xar::game::Snapshot &) {
    std::thread worker([] {
      diag::BeginSnapshotReadAttempt12004();
      diag::RecordSnapshotReadFailure12004(Stage::foundation_missing);
    });
    worker.join();
    return false;
  });
  Require(!Contains(error, " read_stage="), "another thread receipt rejected");
  Require(reads == 12, "exact new read callback count");
  if (failures != 0) return 1;
  std::cout << "PASS " << cases << " new stage/guard cases; eight source stages; one callback each; stale/multiple/other-thread/unknown rejected\n";
  return 0;
}
