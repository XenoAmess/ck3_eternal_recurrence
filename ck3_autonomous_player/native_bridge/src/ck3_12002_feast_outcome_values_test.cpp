#include "xar_bridge/ck3_12002_feast_outcome_values.hpp"
#include "xar_bridge/activity_feast_resource_balance_v1.hpp"
#include "activity_feast_stage5_start_private_transport_v1.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <map>
#include <string>
#include <vector>

namespace {
using namespace xar::bridge;
using xar::ck3_12002::phase_character::NativeTraitXpSpan;

constexpr std::uintptr_t kModule = 0x140000000;
constexpr std::uintptr_t kStorage = 0x430000000;
constexpr std::uintptr_t kSlots = 0x440000000;
constexpr std::uintptr_t kActor = 0x450000000;
constexpr std::uintptr_t kExtension = 0x460000000;
constexpr std::uintptr_t kRoot = 0x200000000;
constexpr std::uintptr_t kWorld = 0x300000000;
constexpr std::uintptr_t kManager = kWorld + 0x22CB8;
constexpr std::uintptr_t kChunks = 0x470000000;
constexpr std::uintptr_t kChunk = 0x480000000;
constexpr std::uintptr_t kIndex = 0x490000000;
constexpr std::uintptr_t kType = 0x4A000000;
constexpr std::uintptr_t kFeast = kChunk + 5 * 0x628;
constexpr std::int32_t kActorId = 29829;

struct Fixture;
Fixture *active = nullptr;

struct Fixture {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  ActivityHostedIdentityFrameV1 frame{7, 53219928, kActorId, true, true, true, true};
  std::array<std::byte, 0x80> database{};
  std::array<std::byte, 0x2A0> definition{};
  std::array<void *, 1> definitions{definition.data()};
  std::int64_t xp = 6500000;
  bool present = true;
  bool database_missing = false;
  bool change_frame = false;
  std::uint32_t frame_reads = 0;

  template <typename T>
  void Write(std::uintptr_t address, T value) {
    const auto *data = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t n = 0; n < sizeof(value); ++n) bytes[address + n] = data[n];
  }
  template <std::size_t N>
  void Code(std::uintptr_t rva, const std::array<std::uint8_t, N> &code) {
    for (std::size_t n = 0; n < N; ++n) bytes[kModule + rva + n] = code[n];
  }
  void EmptyHostedManager() {
    Write(kManager + 0x50, std::int32_t{-1});
    Write(kManager + 0x54, std::uint32_t{0});
    Write(kIndex + 5 * 16 + 8, std::uintptr_t{0});
  }
  void HostedFeast(bool completed) {
    Write(kManager + 0x50, std::int32_t{5});
    Write(kManager + 0x54, std::uint32_t{1});
    Write(kIndex + 5 * 16 + 8, kFeast);
    Write(kFeast + 0x421, static_cast<std::uint8_t>(completed));
  }
  template <typename T, std::size_t N>
  static void Put(std::array<std::byte, N> &buffer, std::size_t offset, T value) {
    std::memcpy(buffer.data() + offset, &value, sizeof(value));
  }
  static bool Read(void *context, std::uintptr_t address, void *output,
                   std::size_t size) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    auto *destination = static_cast<std::uint8_t *>(output);
    for (std::size_t n = 0; n < size; ++n) {
      const auto it = self.bytes.find(address + n);
      if (it == self.bytes.end()) return false;
      destination[n] = it->second;
    }
    return true;
  }
  static bool ReadFrame(void *context, ActivityHostedIdentityFrameV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    output = self.frame;
    if (self.change_frame && ++self.frame_reads == 2) ++output.date_raw;
    return true;
  }
  static void *GetDatabase() {
    return active->database_missing ? nullptr : active->database.data();
  }
  static bool HasTrait(void *, const void *definition_pointer) {
    return active->present && definition_pointer == active->definition.data();
  }
  static void *Tracks(void *, void *output, const void *) {
    auto &span = *static_cast<NativeTraitXpSpan *>(output);
    span.data = active->present ? &active->xp : nullptr;
    span.count = active->present ? 1 : 0;
    return output;
  }
  static std::int32_t TrackIndex(const void *, const std::string *) { return -1; }
  FeastOutcomeEnvironmentV1 Environment() {
    FeastOutcomeEnvironmentV1 result{};
    result.identity = {true, kActivityHostedIdentity12002ExeSha256V1,
                       kModule, this, Read, ReadFrame};
    result.traits.enabled = true;
    result.traits.get_trait_database = GetDatabase;
    result.traits.character_has_trait = HasTrait;
    result.traits.character_trait_tracks = Tracks;
    result.traits.trait_track_index = TrackIndex;
    return result;
  }
  Fixture() {
    active = this;
    Write(kModule + kActivityHosted12002CharacterStorageRva, kStorage);
    Write(kModule + kActivityHosted12002CharacterFallbackRva, std::uintptr_t{0});
    Write(kStorage + 0x20, kSlots);
    Write(kStorage + 0x2C, std::uint32_t{30000});
    Write(kSlots + static_cast<std::size_t>(kActorId) * 16 + 8, kActor);
    Write(kActor + 0x18, static_cast<std::uint32_t>(kActorId));
    Write(kActor + 0x1B0, kExtension);
    Write(kExtension + 0x100, std::int64_t{12500000});
    Write(kExtension + 0x110, std::int64_t{7000000});
    Write(kExtension + 0x130, std::int64_t{-500000});
    Write(kExtension + 0x2F8, std::int32_t{48});
    constexpr std::string_view key = "lifestyle_reveler";
    Put(definition, 0x18, key.data());
    Put(definition, 0x28, std::uint64_t{key.size()});
    Put(definition, 0x30, std::uint64_t{key.size()});
    Put(definition, 0x29C, std::int32_t{1});
    Put(database, 0x50, definitions.data());
    Put(database, 0x5C, std::int32_t{1});

    Code(0x2ADD8EE,
         std::array<std::uint8_t, 7>{0x49, 0x8D, 0xBF, 0xB8, 0x2C, 0x02, 0x00});
    Code(0x29C2E97,
         std::array<std::uint8_t, 7>{0x48, 0x81, 0xC3, 0x28, 0x06, 0x00, 0x00});
    Code(0x23F0195,
         std::array<std::uint8_t, 7>{0x41, 0x89, 0x87, 0xA8, 0x03, 0x00, 0x00});
    Write(kModule + kActivityHosted12002GameStateRva, kRoot);
    Write(kRoot + 0xA0, kWorld);
    Write(kManager + 0x10, std::uint8_t{1});
    Write(kManager + 0x60, std::uint8_t{0});
    Write(kManager + 0x61, std::uint8_t{0});
    Write(kManager + 0x20, kChunks);
    Write(kManager + 0x2C, std::uint32_t{1});
    Write(kManager + 0x38, kIndex);
    Write(kManager + 0x44, std::uint32_t{16});
    Write(kChunks, kChunk);
    for (std::uint32_t index = 0; index <= 5; ++index)
      Write(kIndex + index * 16 + 8, std::uintptr_t{0});
    Write(kFeast, kModule + kActivityHosted12002ActivityVtableRva);
    Write(kFeast + 0x08, std::uint32_t{0x02000005});
    Write(kFeast + 0x3A0, kType);
    Write(kFeast + 0x3A8, kActorId);
    Write(kFeast + 0x421, std::uint8_t{0});
    Write(kFeast + 0x422, std::uint8_t{0});
    Write(kType, kModule + kActivityHosted12002ActivityTypeVtableRva);
    constexpr std::string_view activity_key = "activity_feast";
    for (std::size_t n = 0; n < activity_key.size(); ++n)
      Write(kType + 0x18 + n, static_cast<std::uint8_t>(activity_key[n]));
    Write(kType + 0x28, std::uint64_t{activity_key.size()});
    Write(kType + 0x30, std::uint64_t{15});
    EmptyHostedManager();
  }
};

void TestIndependentActorCountersUseActualSources() {
  Fixture fixture;
  const auto result = ReadFeastOutcomeValues12002(fixture.Environment(), fixture.frame);
  assert(result.status == FeastOutcomeStatusV1::observed);
  assert(result.value.frame == fixture.frame);
  assert(result.value.prestige_available && result.value.prestige_raw == -500000);
  assert(result.value.stress_available && result.value.stress_points == 48);
  assert(result.value.reveler_available && result.value.reveler_present);
  assert(result.value.reveler_xp_available);
  assert(result.value.reveler_xp_raw == 6500000);
}

void TestAbsentRevelerHasNoApplicableXp() {
  Fixture fixture;
  fixture.present = false;
  const auto result = ReadFeastOutcomeValues12002(fixture.Environment(), fixture.frame);
  assert(result.status == FeastOutcomeStatusV1::observed);
  assert(result.value.reveler_available && !result.value.reveler_present);
  assert(!result.value.reveler_xp_available);
  assert(result.value.reveler_xp_raw == 0);
}

void TestBeforeAfterCountersDoNotClaimRewardOrCausality() {
  Fixture fixture;
  const auto before = ReadFeastOutcomeValues12002(fixture.Environment(), fixture.frame);
  ++fixture.frame.revision;
  fixture.Write(kExtension + 0x130, std::int64_t{9500000});
  fixture.Write(kExtension + 0x2F8, std::int32_t{28});
  fixture.xp = 7000000;
  const auto after = ReadFeastOutcomeValues12002(fixture.Environment(), fixture.frame);
  assert(before.status == FeastOutcomeStatusV1::observed);
  assert(after.status == FeastOutcomeStatusV1::observed);
  assert(after.value.prestige_raw == 9500000 && after.value.stress_points == 28);
  assert(after.value.reveler_xp_raw == 7000000);
}

void TestMissingDefinitionDoesNotEraseUsefulActorCounters() {
  Fixture fixture;
  fixture.database_missing = true;
  const auto result = ReadFeastOutcomeValues12002(fixture.Environment(), fixture.frame);
  assert(result.status == FeastOutcomeStatusV1::observed_partial);
  assert(result.value.prestige_available && result.value.stress_available);
  assert(!result.value.reveler_available);
}

void TestZeroExtensionMatchesNativeGetterZero() {
  Fixture fixture;
  fixture.Write(kActor + 0x1B0, std::uintptr_t{0});
  const auto result = ReadFeastOutcomeValues12002(fixture.Environment(), fixture.frame);
  assert(result.status == FeastOutcomeStatusV1::observed);
  assert(result.value.prestige_available && result.value.prestige_raw == 0);
  assert(result.value.stress_available && result.value.stress_points == 0);
}

void TestActorAndFrameIdentityRemainBound() {
  Fixture fixture;
  fixture.Write(kActor + 0x18, static_cast<std::uint32_t>(kActorId | 0x01000000));
  assert(ReadFeastOutcomeValues12002(fixture.Environment(), fixture.frame).status ==
         FeastOutcomeStatusV1::actor_unavailable);
  fixture.Write(kActor + 0x18, static_cast<std::uint32_t>(kActorId));
  fixture.change_frame = true;
  assert(ReadFeastOutcomeValues12002(fixture.Environment(), fixture.frame).status ==
         FeastOutcomeStatusV1::snapshot_changed);
}

void TestLegacyProfileIsNotANewOutcomeSource() {
  Fixture fixture;
  auto environment = fixture.Environment();
  environment.identity.admitted_executable_sha256 = kActivityHostedIdentityExeSha256V1;
  assert(ReadFeastOutcomeValues12002(environment, fixture.frame).status ==
         FeastOutcomeStatusV1::exact_build_rejected);
}

// Copies are produced by the same readers called by production Stage5Capture.
// Only planner/cost/guest metadata in the baseline wrapper is fixture supplied;
// these rows prove the actor counters, hosted identity and actual serializer.
xar::bridge::ActivityFeastStage5PostV1 ReadActualPost(Fixture &fixture) {
  const auto environment = fixture.Environment();
  const auto counters = ReadFeastOutcomeValues12002(environment, fixture.frame);
  const auto hosted = ReadActivityHostedIdentityV1(environment.identity,
                                                  fixture.frame);
  const auto balances = ReadActivityFeastResourceBalancesV1(environment.identity,
                                                           fixture.frame);
  assert(counters.status == FeastOutcomeStatusV1::observed);
  assert(hosted.status == ActivityHostedIdentityStatusV1::observed);
  assert(balances.status == ActivityFeastBalanceStatusV1::observed_partial);
  xar::bridge::ActivityFeastStage5PostV1 post{};
  post.frame = fixture.frame;
  post.outcome_values = counters.value;
  post.balances = balances.value;
  post.hosted_identities_observed = true;
  post.hosted_count = hosted.hosted_count;
  post.hosted = hosted.hosted;
  return post;
}

std::string PostWire(const xar::bridge::ActivityFeastStage5PostV1 &post) {
  xar::ck3_11906::ActivityFeastStage5PrivateQueryV1 query{};
  query.completed = true;
  query.mode = xar::ck3_11906::ActivityFeastStage5PrivateModeV1::hosted_post;
  query.post = post;
  auto payload = xar::ck3_11906::SerializeActivityFeastStage5PrivateV1(query);
  assert(!payload.empty());
  return payload;
}

void Save(const std::filesystem::path &path, const std::string &data) {
  std::ofstream stream(path, std::ios::binary);
  assert(stream.good());
  stream << data << '\n';
  assert(stream.good());
}

void TestProductionProviderToSerializerTrace(const std::filesystem::path &output) {
  Fixture fixture;
  const auto baseline = ReadActualPost(fixture);
  assert(baseline.hosted_count == 0);
  xar::ck3_11906::ActivityFeastStage5PrivateQueryV1 inputs{};
  inputs.completed = true;
  inputs.inputs.frame = baseline.frame;
  inputs.inputs.four_costs_observed = true;
  inputs.inputs.cost_resource_indices = {0, 6, 2, 9};
  inputs.inputs.cost_raw = {1000000, 0, 0, 0};
  inputs.inputs.normal_cost_refresh_sequence = 17;
  inputs.inputs.final_can_start = true;
  inputs.inputs.balances = baseline.balances;
  inputs.inputs.hosted_identities_observed = true;
  inputs.inputs.hosted_count = baseline.hosted_count;
  inputs.inputs.hosted = baseline.hosted;
  inputs.inputs.outcome_values = baseline.outcome_values;
  const auto before_start =
      xar::ck3_11906::SerializeActivityFeastStage5PrivateV1(inputs);
  assert(!before_start.empty());

  ++fixture.frame.revision;
  fixture.HostedFeast(false);
  fixture.Write(kExtension + 0x100, std::int64_t{11500000});
  const auto ongoing = ReadActualPost(fixture);
  assert(ongoing.hosted_count == 1 && ongoing.hosted[0].activity_id == 0x02000005U);
  assert(!ongoing.hosted[0].native_completed);

  ++fixture.frame.revision;
  fixture.HostedFeast(true);
  fixture.Write(kExtension + 0x130, std::int64_t{9500000});
  fixture.Write(kExtension + 0x2F8, std::int32_t{28});
  fixture.xp = 7000000;
  const auto completed = ReadActualPost(fixture);
  assert(completed.hosted[0].activity_id == ongoing.hosted[0].activity_id);
  assert(completed.hosted[0].native_completed);

  ++fixture.frame.revision;
  fixture.present = false;
  fixture.HostedFeast(false);
  const auto nonreveler = ReadActualPost(fixture);
  assert(nonreveler.outcome_values.reveler_available);
  assert(!nonreveler.outcome_values.reveler_present);
  assert(!nonreveler.outcome_values.reveler_xp_available);

  ++fixture.frame.revision;
  fixture.EmptyHostedManager();
  const auto released = ReadActualPost(fixture);
  assert(released.hosted_count == 0);

  std::vector<std::string> post_wires{
      PostWire(ongoing), PostWire(completed), PostWire(nonreveler), PostWire(released)};
  assert(post_wires[0].find("\"prestige_raw\":-500000") != std::string::npos);
  assert(post_wires[1].find("\"prestige_raw\":9500000") != std::string::npos);
  assert(post_wires[1].find("\"native_completed\":true") != std::string::npos);
  assert(post_wires[2].find("\"reveler_xp_raw\":null") != std::string::npos);
  if (output.empty()) return;
  std::filesystem::create_directories(output);
  Save(output / "before-start.json", before_start);
  std::string array = "[";
  for (std::size_t n = 0; n < post_wires.size(); ++n) {
    if (n != 0) array += ",\n";
    array += post_wires[n];
  }
  array += "]";
  Save(output / "post-wire.json", array);
}
} // namespace

int main(int argc, char **argv) {
  TestIndependentActorCountersUseActualSources();
  TestAbsentRevelerHasNoApplicableXp();
  TestBeforeAfterCountersDoNotClaimRewardOrCausality();
  TestMissingDefinitionDoesNotEraseUsefulActorCounters();
  TestZeroExtensionMatchesNativeGetterZero();
  TestActorAndFrameIdentityRemainBound();
  TestLegacyProfileIsNotANewOutcomeSource();
  TestProductionProviderToSerializerTrace(argc > 1 ? argv[1] : "");
}
