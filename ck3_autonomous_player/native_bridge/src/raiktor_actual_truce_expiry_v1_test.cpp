#include "xar_bridge/raiktor_actual_truce_expiry_v1.hpp"

#include <cstdlib>
#include <cstdint>
#include <string>

namespace {

struct Fixture {
  xar::game::Snapshot snapshot;
  std::int32_t owner = 1;
  std::int32_t toward = 2;
  std::int32_t expiry = 50000;
  bool has_truce = true;
  bool mutate_second_snapshot = false;
  int snapshot_reads = 0;
};

Fixture *g_fixture = nullptr;

void Require(bool condition) {
  if (!condition) std::abort();
}

bool ReadSnapshot(void *context, xar::game::Snapshot &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.snapshot;
  if (++fixture.snapshot_reads == 2 && fixture.mutate_second_snapshot) {
    ++output.date_raw;
  }
  return true;
}

void *ResolveCharacter(void *context, std::int32_t id) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (id == fixture.snapshot.played_character_id) return &fixture.owner;
  if (id == fixture.toward) return &fixture.toward;
  return nullptr;
}

bool HasTruce(void *, void *) { return g_fixture->has_truce; }
const void *GetEndDate(void *, void *) { return &g_fixture->expiry; }

xar::ck3_11906::RaiktorActualTruceExpiryAccessV1 Access(Fixture &fixture) {
  g_fixture = &fixture;
  return {true, &fixture, &ReadSnapshot, &ResolveCharacter, &HasTruce,
          &GetEndDate};
}

Fixture ReadyFixture() {
  Fixture fixture{};
  fixture.snapshot.date_raw = 10000;
  fixture.snapshot.paused = true;
  fixture.snapshot.map_ready = true;
  fixture.snapshot.player_id = 0;
  fixture.snapshot.has_played_character = true;
  fixture.snapshot.played_character_id = 1;
  fixture.snapshot.played_character_alive = true;
  return fixture;
}

} // namespace

int main() {
  using namespace xar;
  {
    auto fixture = ReadyFixture();
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        Access(fixture), fixture.toward, output);
    Require(result == game::ReadRaiktorActualTruceExpiryResultV1::available);
    Require(output.status ==
           game::RaiktorActualTruceExpiryStatusV1::available);
    Require(output.owner_character_id == 1);
    Require(output.toward_character_id == 2);
    Require(output.actual_expiry_observable);
    Require(output.expiry_date_raw == fixture.expiry);
    Require(output.same_frame_stable);
    Require(output.readiness);
    const auto wire = ck3_11906::SerializeRaiktorActualTruceExpiryV1(output);
    Require(wire.find("\"actual_expiry_observable\":true") !=
           std::string::npos);
    Require(wire.find("\"expiry_date_raw\":50000") != std::string::npos);
  }
  {
    auto fixture = ReadyFixture();
    fixture.has_truce = false;
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        Access(fixture), fixture.toward, output);
    Require(result == game::ReadRaiktorActualTruceExpiryResultV1::no_truce);
    Require(output.same_frame_stable);
    Require(!output.actual_expiry_observable);
    Require(!output.readiness);
    const auto wire = ck3_11906::SerializeRaiktorActualTruceExpiryV1(output);
    Require(wire.find("\"expiry_date_raw\":null") != std::string::npos);
  }
  {
    auto fixture = ReadyFixture();
    fixture.mutate_second_snapshot = true;
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        Access(fixture), fixture.toward, output);
    Require(result ==
           game::ReadRaiktorActualTruceExpiryResultV1::unstable_snapshot);
    Require(!output.readiness);
  }
  {
    auto fixture = ReadyFixture();
    fixture.snapshot.paused = false;
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        Access(fixture), fixture.toward, output);
    Require(result ==
           game::ReadRaiktorActualTruceExpiryResultV1::requires_paused);
    Require(!output.readiness);
  }
  {
    auto fixture = ReadyFixture();
    game::RaiktorActualTruceExpirySnapshotV1 output{};
    auto access = Access(fixture);
    access.exact_build_admitted = false;
    const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
        access, fixture.toward, output);
    Require(result == game::ReadRaiktorActualTruceExpiryResultV1::unavailable);
    Require(!output.readiness);
  }
}
