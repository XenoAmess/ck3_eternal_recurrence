#include "xar_bridge/h2743_preaction_existing_truce_v1.hpp"

#include <cstdlib>
#include <cstdint>
#include <string>

namespace {

struct Fixture {
  xar::game::Snapshot snapshot;
  int war = 1;
  int cb = 2;
  int owner = 3;
  int defender = 4;
  std::int32_t expiry = 53219000;
  bool has_truce = true;
  bool change_second_has = false;
  bool change_second_expiry = false;
  bool change_second_war = false;
  bool change_second_snapshot = false;
  bool direction_correct = true;
  int has_reads = 0;
  int end_reads = 0;
  int war_reads = 0;
  int snapshot_reads = 0;
};

Fixture *g_fixture = nullptr;

void Require(bool condition) {
  if (!condition) std::abort();
}

bool ReadSnapshot(void *context, xar::game::Snapshot &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.snapshot;
  if (++fixture.snapshot_reads == 2 && fixture.change_second_snapshot) {
    ++output.date_raw;
  }
  return true;
}

bool ReadWarIdentity(
    void *context,
    xar::ck3_11906::H2743TruceWarIdentityV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output.war_object = &fixture.war;
  output.casus_belli_object = &fixture.cb;
  output.war_id = 16777231;
  output.primary_attacker_id = 30097;
  output.primary_defender_id = 29829;
  output.casus_belli_database_index = 17;
  output.exact_casus_belli_key = true;
  output.target_title_ids = {2128};
  if (++fixture.war_reads == 2 && fixture.change_second_war) {
    output.primary_attacker_id = 30098;
  }
  return true;
}

void *ResolveCharacter(void *context, std::int32_t id) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (id == 30097) return &fixture.owner;
  if (id == 29829) return &fixture.defender;
  return nullptr;
}

bool HasTruce(void *owner, void *toward) {
  g_fixture->direction_correct &=
      owner == &g_fixture->owner && toward == &g_fixture->defender;
  const int read = ++g_fixture->has_reads;
  return read == 2 && g_fixture->change_second_has
             ? !g_fixture->has_truce
             : g_fixture->has_truce;
}

const void *GetEndDate(void *owner, void *toward) {
  g_fixture->direction_correct &=
      owner == &g_fixture->owner && toward == &g_fixture->defender;
  if (++g_fixture->end_reads == 2 && g_fixture->change_second_expiry) {
    ++g_fixture->expiry;
  }
  return &g_fixture->expiry;
}

xar::ck3_11906::H2743ExistingTruceAccessV1 Access(Fixture &fixture) {
  g_fixture = &fixture;
  return {true, &fixture, &ReadSnapshot, &ReadWarIdentity,
          &ResolveCharacter, &HasTruce, &GetEndDate};
}

Fixture ReadyFixture() {
  Fixture fixture{};
  auto &snapshot = fixture.snapshot;
  snapshot.paused = true;
  snapshot.map_ready = true;
  snapshot.has_played_character = true;
  snapshot.played_character_id = 29829;
  snapshot.played_character_alive = true;
  snapshot.date_raw = 53217264;
  xar::game::ActiveWarSnapshot war{};
  war.war_id = 16777231;
  war.player_side = xar::game::PlayerWarSide::defender;
  war.primary_opponent_character_id = 30097;
  war.player_is_primary_war_leader = true;
  war.targeted_title_ids = {2128};
  snapshot.active_wars.push_back(war);
  return fixture;
}

xar::ck3_11906::H2743PreactionFrameClaimV1 FrameClaim(
    std::uint64_t native_revision, std::uint64_t public_revision) {
  return {public_revision, native_revision, 53217264, 29829, 16777231,
          "native:" + std::to_string(native_revision),
          std::string(xar::ck3_11906::kH2743EpisodeIdV1),
          std::string(xar::ck3_11906::kH2743CheckpointSha256V1),
          std::string(xar::ck3_11906::kH2743ExeSha256V1)};
}

} // namespace

int main() {
  using Status = xar::game::H2743ExistingTruceStatusV1;
  using xar::ck3_11906::ReadH2743PreactionExistingTruceV1;
  using xar::ck3_11906::AdmitH2743PreactionFrameClaimV1;
  {
    const auto ready = ReadyFixture();
    for (const auto native_revision : {std::uint64_t{3}, std::uint64_t{4}}) {
      const auto claim = FrameClaim(native_revision, native_revision + 1);
      Require(AdmitH2743PreactionFrameClaimV1(
          claim, native_revision, ready.snapshot));
      auto wrong = claim;
      wrong.snapshot_id = "native:3";
      if (native_revision == 4) {
        Require(!AdmitH2743PreactionFrameClaimV1(
            wrong, native_revision, ready.snapshot));
      }
      wrong = claim;
      wrong.public_revision = 0;
      Require(!AdmitH2743PreactionFrameClaimV1(
          wrong, native_revision, ready.snapshot));
      wrong = claim;
      ++wrong.native_revision;
      Require(!AdmitH2743PreactionFrameClaimV1(
          wrong, native_revision, ready.snapshot));
      wrong = claim;
      ++wrong.date_raw;
      Require(!AdmitH2743PreactionFrameClaimV1(
          wrong, native_revision, ready.snapshot));
      wrong = claim;
      ++wrong.actor_character_id;
      Require(!AdmitH2743PreactionFrameClaimV1(
          wrong, native_revision, ready.snapshot));
      wrong = claim;
      ++wrong.war_id;
      Require(!AdmitH2743PreactionFrameClaimV1(
          wrong, native_revision, ready.snapshot));
      wrong = claim;
      wrong.episode_id = "wrong";
      Require(!AdmitH2743PreactionFrameClaimV1(
          wrong, native_revision, ready.snapshot));
      wrong = claim;
      wrong.checkpoint_sha256 = "wrong";
      Require(!AdmitH2743PreactionFrameClaimV1(
          wrong, native_revision, ready.snapshot));
      wrong = claim;
      wrong.exe_sha256 = "wrong";
      Require(!AdmitH2743PreactionFrameClaimV1(
          wrong, native_revision, ready.snapshot));
      auto changed = ready.snapshot;
      changed.paused = false;
      Require(!AdmitH2743PreactionFrameClaimV1(
          claim, native_revision, changed));
      changed = ready.snapshot;
      changed.active_wars[0].war_id = 16777232;
      Require(!AdmitH2743PreactionFrameClaimV1(
          claim, native_revision, changed));
    }
    // The Python public counter can advance independently of native revision.
    Require(AdmitH2743PreactionFrameClaimV1(
        FrameClaim(4, 7), 4, ready.snapshot));
  }
  {
    auto fixture = ReadyFixture();
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(Access(fixture), output) ==
            Status::existing_truce);
    Require(fixture.direction_correct && fixture.has_reads == 2 &&
            fixture.end_reads == 2 && fixture.war_reads == 2);
    Require(output.same_frame_stable &&
            output.preaction_existing_expiry_observable &&
            output.preaction_existing_expiry_date_raw == 53219000);
    const auto wire =
        xar::ck3_11906::SerializeH2743PreactionExistingTruceV1(output);
    Require(wire.find("\"preaction_existing_expiry_date_raw\":53219000") !=
            std::string::npos);
    Require(wire.find("\"post_surrender_actual_expiry_date_raw\":null") !=
            std::string::npos);
    Require(wire.find("\"action_literal\":null") != std::string::npos);
  }
  {
    auto fixture = ReadyFixture();
    fixture.has_truce = false;
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(Access(fixture), output) ==
            Status::no_existing_truce);
    Require(fixture.direction_correct && fixture.end_reads == 0);
    Require(output.same_frame_stable &&
            !output.preaction_existing_expiry_observable);
    const auto wire =
        xar::ck3_11906::SerializeH2743PreactionExistingTruceV1(output);
    Require(wire.find("\"preaction_existing_expiry_date_raw\":null") !=
            std::string::npos);
  }
  {
    auto fixture = ReadyFixture();
    fixture.change_second_has = true;
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(Access(fixture), output) ==
            Status::unavailable);
    Require(!output.preaction_existing_expiry_observable);
  }
  {
    auto fixture = ReadyFixture();
    fixture.change_second_expiry = true;
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(Access(fixture), output) ==
            Status::unavailable);
  }
  {
    auto fixture = ReadyFixture();
    fixture.change_second_war = true;
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(Access(fixture), output) ==
            Status::unavailable);
  }
  {
    auto fixture = ReadyFixture();
    fixture.change_second_snapshot = true;
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(Access(fixture), output) ==
            Status::unavailable);
  }
  {
    auto fixture = ReadyFixture();
    fixture.snapshot.date_raw = 53217265;
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(Access(fixture), output) ==
            Status::unavailable);
  }
  {
    auto fixture = ReadyFixture();
    fixture.snapshot.active_wars[0].targeted_title_ids = {2129};
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(Access(fixture), output) ==
            Status::unavailable);
  }
  {
    auto fixture = ReadyFixture();
    fixture.snapshot.active_wars.push_back(fixture.snapshot.active_wars[0]);
    fixture.snapshot.active_wars.back().targeted_title_ids = {2129};
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(Access(fixture), output) ==
            Status::unavailable);
  }
  {
    auto fixture = ReadyFixture();
    auto access = Access(fixture);
    access.exact_build_admitted = false;
    xar::game::H2743ExistingTruceSnapshotV1 output{};
    Require(ReadH2743PreactionExistingTruceV1(access, output) ==
            Status::unavailable);
  }
}
