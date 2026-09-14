#include "xar_bridge/faction_targeting_row_observer_v1.hpp"
#include "xar_bridge/faction_targeting_row_observer_v1_serializer.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>

namespace {

using xar::bridge::FactionTargetingRowCaptureAdmissionV1;
using xar::bridge::FactionTargetingRowObserverEnvironmentV1;
using xar::bridge::FactionTargetingRowObserverStateV1;

constexpr std::array<std::uint8_t, 15> kAnchor{
    0xE8, 0x7D, 0x98, 0xBD, 0xFF,
    0x48, 0x89, 0x44, 0x24, 0x20,
    0x48, 0x8D, 0x54, 0x24, 0x30};

struct AdmissionFixture {
  FactionTargetingRowCaptureAdmissionV1 value{};
  bool readable = true;
  bool drift_on_second = false;
  std::size_t calls = 0;
};

bool ReadAdmission(
    void *context,
    FactionTargetingRowCaptureAdmissionV1 &output) noexcept {
  auto &fixture = *static_cast<AdmissionFixture *>(context);
  ++fixture.calls;
  if (!fixture.readable) return false;
  output = fixture.value;
  if (fixture.drift_on_second && fixture.calls == 2) {
    ++output.snapshot_revision;
  }
  return true;
}

struct FixtureMemory {
  std::array<std::uint8_t, 15> target{kAnchor};
  std::array<std::uint8_t,
             xar::bridge::kFactionTargetingRowObserverStubCapacityV1>
      stub{};
  std::size_t allocation_count = 0;
  std::size_t free_count = 0;
  std::size_t read_count = 0;
  std::uintptr_t drift_read_address = 0;
  std::size_t drift_read_match = 0;
  std::size_t drift_read_matches = 0;
};

bool FixtureRead(void *context, std::uintptr_t address, void *output,
                 std::size_t size) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(context);
  ++fixture.read_count;
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  if (fixture.drift_read_address >= address &&
      fixture.drift_read_address - address < size) {
    ++fixture.drift_read_matches;
    if (fixture.drift_read_matches == fixture.drift_read_match) {
      static_cast<std::uint8_t *>(output)[fixture.drift_read_address - address] ^=
          1U;
    }
  }
  return true;
}

bool FixtureWrite(void *, std::uintptr_t address, const void *source,
                  std::size_t size) noexcept {
  if (address == 0 || source == nullptr || size == 0) return false;
  std::memcpy(reinterpret_cast<void *>(address), source, size);
  return true;
}

void *FixtureAlloc(void *context, std::size_t size, DWORD, DWORD) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(context);
  if (size != fixture.stub.size() || fixture.allocation_count != 0) {
    return nullptr;
  }
  ++fixture.allocation_count;
  return fixture.stub.data();
}

bool FixtureFree(void *context, void *, std::size_t, DWORD) noexcept {
  ++static_cast<FixtureMemory *>(context)->free_count;
  return true;
}

bool FixtureProtect(void *, void *, std::size_t, DWORD new_protection,
                    DWORD &old_protection) noexcept {
  old_protection = new_protection == PAGE_EXECUTE_READ
      ? PAGE_READWRITE
      : PAGE_EXECUTE_READ;
  return true;
}

bool FixtureFlush(void *, const void *, std::size_t) noexcept {
  return true;
}

struct CharacterMemberRowFixture {
  std::uintptr_t process_local_vtable = 0;
  std::uint32_t character_id = 0;
  std::uint32_t owner_faction_id = 0;
  std::array<std::uint8_t, 0x10> opaque_tail{};
};

static_assert(sizeof(CharacterMemberRowFixture) == 0x20);
static_assert(offsetof(CharacterMemberRowFixture, character_id) == 0x08);
static_assert(offsetof(CharacterMemberRowFixture, owner_faction_id) == 0x0C);

struct ResolvedFactionFixture {
  std::array<std::uint8_t, 0x10> prefix{};
  std::uint32_t faction_id = 0;
  std::array<std::uint8_t, 0x2C> between_identity_and_target{};
  std::uint32_t target_character_id = 0;
  std::uint32_t leader_character_id = 0;
  std::uintptr_t character_member_data = 0;
  std::uint32_t character_member_unknown_word = 0;
  std::int32_t character_member_count = 0;
};

static_assert(offsetof(ResolvedFactionFixture, faction_id) == 0x10);
static_assert(offsetof(ResolvedFactionFixture, target_character_id) == 0x40);
static_assert(offsetof(ResolvedFactionFixture, leader_character_id) == 0x44);
static_assert(offsetof(ResolvedFactionFixture, character_member_data) == 0x48);
static_assert(offsetof(ResolvedFactionFixture, character_member_count) == 0x54);

struct ResolvedCharacterFixture {
  std::array<std::uint8_t, 0x18> prefix{};
  std::uint32_t character_id = 0;
};

static_assert(offsetof(ResolvedCharacterFixture, character_id) == 0x18);

struct ResolverFixture {
  std::array<ResolvedFactionFixture, 3> factions{};
  std::array<ResolvedCharacterFixture, 16> characters{};
  bool fail_faction = false;
  bool fail_character = false;
  std::uint32_t failed_character_id = 0;
  std::uint32_t round_trip_mismatch_character_id = 0;
};

bool ResolveFactionIdentity(void *context, std::uint32_t faction_id,
                            std::uintptr_t &resolved) noexcept {
  auto &fixture = *static_cast<ResolverFixture *>(context);
  resolved = 0;
  if (fixture.fail_faction) return false;
  for (auto &faction : fixture.factions) {
    if (faction.faction_id == faction_id) {
      resolved = reinterpret_cast<std::uintptr_t>(&faction);
      return true;
    }
  }
  return false;
}

bool ResolveCharacterIdentity(void *context, std::uint32_t character_id,
                              std::uintptr_t &resolved) noexcept {
  auto &fixture = *static_cast<ResolverFixture *>(context);
  resolved = 0;
  if (character_id == 0 || fixture.fail_character ||
      (fixture.failed_character_id != 0 &&
       fixture.failed_character_id == character_id)) {
    return false;
  }
  if (fixture.round_trip_mismatch_character_id == character_id) {
    resolved = reinterpret_cast<std::uintptr_t>(&fixture.characters.back());
    return true;
  }
  for (auto &character : fixture.characters) {
    if (character.character_id == character_id) {
      resolved = reinterpret_cast<std::uintptr_t>(&character);
      return true;
    }
  }
  return false;
}

FactionTargetingRowObserverEnvironmentV1 Environment(
    FixtureMemory &memory, AdmissionFixture &admission,
    ResolverFixture &resolver) {
  FactionTargetingRowObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      xar::bridge::kFactionTargetingRowObserverExecutableSha256V1;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  environment.patch_target_override =
      reinterpret_cast<std::uintptr_t>(memory.target.data());
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(memory.target.data() +
                                       memory.target.size());
  environment.original_getter_target_override = 0x123456789ABCDEF0ULL;
  environment.identity_resolver_target_override = 0x0FEDCBA987654321ULL;
  environment.character_identity_resolver_target_override =
      0x1020304050607080ULL;
  environment.memory_context = &memory;
  environment.memory_read_override = &FixtureRead;
  environment.memory_write_override = &FixtureWrite;
  environment.virtual_alloc_override = &FixtureAlloc;
  environment.virtual_free_override = &FixtureFree;
  environment.virtual_protect_override = &FixtureProtect;
  environment.flush_instruction_cache_override = &FixtureFlush;
  environment.capture_admission_context = &admission;
  environment.capture_admission_probe = &ReadAdmission;
  environment.identity_resolver_context = &resolver;
  environment.identity_resolver_override = &ResolveFactionIdentity;
  environment.character_identity_resolver_context = &resolver;
  environment.character_identity_resolver_override =
      &ResolveCharacterIdentity;
  return environment;
}

template <std::size_t Size>
bool ContainsU64(const std::array<std::uint8_t, Size> &bytes,
                 std::uint64_t value) {
  std::array<std::uint8_t, sizeof(value)> encoded{};
  std::memcpy(encoded.data(), &value, sizeof(value));
  return std::search(bytes.begin(), bytes.end(), encoded.begin(),
                     encoded.end()) != bytes.end();
}

struct FactionRowFixture {
  std::uint32_t faction_id = 0;
  std::array<std::uint8_t, 20> opaque{};
};

static_assert(sizeof(FactionRowFixture) == 0x18);

struct TargetingContainerFixture {
  std::uintptr_t row_data = 0;
  std::uint32_t unresolved_word_at_0x08 = 0;
  std::int32_t count = 0;
};

static_assert(sizeof(TargetingContainerFixture) == 16);

void TestDefaultOffAndExactHashGuard() {
  static_assert(!xar::bridge::kFactionTargetingRowObserverInstalledByDefaultV1);
  FactionTargetingRowObserverStateV1 state{};
  FactionTargetingRowObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      "0000000000000000000000000000000000000000000000000000000000000000";
  assert(!xar::bridge::InstallFactionTargetingRowObserverV1(state,
                                                            environment));
  const auto diagnostics =
      xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert((diagnostics.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_exact_build) !=
         0);
}

std::string TestAdmissionBeforeReadAndStableIdentityCapture() {
  FixtureMemory memory{};
  AdmissionFixture admission{};
  admission.value = {77, true, 42, 412, 777, 29829, 2};
  ResolverFixture resolver{};
  std::array<CharacterMemberRowFixture, 2> faction_42_members{};
  faction_42_members[0].character_id = 4001;
  faction_42_members[0].owner_faction_id = 42;
  faction_42_members[1].character_id = 4002;
  faction_42_members[1].owner_faction_id = 42;
  resolver.factions[0].faction_id = 42;
  resolver.factions[0].target_character_id = 29829;
  resolver.factions[0].leader_character_id = 4001;
  resolver.factions[0].character_member_data =
      reinterpret_cast<std::uintptr_t>(faction_42_members.data());
  resolver.factions[0].character_member_count = 2;
  resolver.factions[1].faction_id = 7;
  resolver.factions[1].target_character_id = 29829;
  resolver.characters[0].character_id = 29829;
  resolver.characters[1].character_id = 4001;
  resolver.characters[2].character_id = 4002;
  FactionTargetingRowObserverStateV1 state{};
  const auto environment = Environment(memory, admission, resolver);
  assert(xar::bridge::InstallFactionTargetingRowObserverV1(state,
                                                           environment));
  assert(memory.target[0] == 0xFF && memory.target[1] == 0x25);
  assert(ContainsU64(memory.stub,
                     environment.original_getter_target_override));
  assert(ContainsU64(memory.stub, environment.continue_target_override));
  assert(state.character_identity_resolver_target ==
         environment.character_identity_resolver_target_override);

  const auto reads_after_install = memory.read_count;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(state, 1, 76, 1000));
  assert(memory.read_count == reads_after_install);
  admission.value.paused = false;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(state, 1, 77, 1001));
  assert(memory.read_count == reads_after_install);
  admission.value.paused = true;

  std::array<FactionRowFixture, 2> rows{{{42, {}}, {7, {}}}};
  TargetingContainerFixture container{
      reinterpret_cast<std::uintptr_t>(rows.data()), 0xA5A5A5A5U, 2};
  assert(xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 77, 1002));

  const auto diagnostics =
      xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  const auto &capture = diagnostics.observation;
  assert(capture.callback_count == 3);
  assert(capture.rejected_application_main_count == 1);
  assert(capture.rejected_paused_count == 1);
  assert(capture.accepted_capture_count == 1);
  assert(capture.published_generation == 2);
  assert(capture.last_proof_epoch == 42);
  assert(capture.last_snapshot_revision == 412);
  assert(capture.last_date_raw == 777);
  assert(capture.last_player_character_id == 29829);
  assert(capture.last_campaign_root_targeting_faction_count == 2);
  assert(capture.last_faction_count == 2);
  assert(capture.last_faction_ids[0] == 7);
  assert(capture.last_faction_ids[1] == 42);
  assert(capture.last_target_character_ids[0] == 29829);
  assert(capture.last_target_character_ids[1] == 29829);
  assert(capture.last_leader_present[0] == 0);
  assert(capture.last_leader_present[1] == 1);
  assert(capture.last_leader_character_ids[0] == 0);
  assert(capture.last_leader_character_ids[1] == 4001);
  assert(capture.last_leader_present_in_character_members[0] == 0);
  assert(capture.last_leader_present_in_character_members[1] == 1);
  assert(capture.last_character_member_counts[0] == 0);
  assert(capture.last_character_member_counts[1] == 2);
  const auto member_base =
      xar::bridge::kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1;
  assert(capture.last_character_member_ids[member_base] == 4001);
  assert(capture.last_character_member_ids[member_base + 1] == 4002);

  const std::string serialized =
      xar::bridge::SerializeFactionTargetingRowObserverV1(diagnostics);
  assert(serialized.find("\"faction_ids\":[7,42]") != std::string::npos);
  assert(serialized.find("\"target_character_ids\":[29829,29829]") !=
         std::string::npos);
  assert(serialized.find(
             "\"faction_id\":7,\"target_character_id\":29829,"
             "\"leader_character_id\":null,"
             "\"leader_present_in_character_members\":false,"
             "\"character_member_ids\":[]") != std::string::npos);
  assert(serialized.find(
             "\"faction_id\":42,\"target_character_id\":29829,"
             "\"leader_character_id\":4001,"
             "\"leader_present_in_character_members\":true,"
             "\"character_member_ids\":[4001,4002]") !=
         std::string::npos);
  assert(serialized.find("\"canonical_nullable_leader\":true") !=
         std::string::npos);
  assert(serialized.find("\"same_admission_leader_member\":true") !=
         std::string::npos);
  assert(serialized.find(
             "\"campaign_root_targeting_faction_count\":2") !=
         std::string::npos);
  assert(serialized.find(
             "\"campaign_root_count_equivalence\":true") !=
         std::string::npos);
  assert(serialized.find("\"raw_pointer_fields_persisted\":false") !=
         std::string::npos);
  assert(serialized.find("\"raw_row_bytes_persisted\":false") !=
         std::string::npos);
  assert(serialized.find("\"raw_member_row_bytes_persisted\":false") !=
         std::string::npos);
  assert(serialized.find(std::to_string(
             reinterpret_cast<std::uintptr_t>(&rows[0]))) ==
         std::string::npos);
  assert(serialized.find(std::to_string(container.row_data)) ==
         std::string::npos);
  assert(serialized.find(std::to_string(
             resolver.factions[0].character_member_data)) ==
         std::string::npos);

  assert(xar::bridge::UninstallFactionTargetingRowObserverV1(state));
  assert(std::equal(kAnchor.begin(), kAnchor.end(), memory.target.begin()));
  assert(memory.free_count == 1);
  return serialized;
}

void TestTransactionalRejectionKeepsPreviousGeneration() {
  FixtureMemory memory{};
  AdmissionFixture admission{};
  admission.value = {12, true, 9, 99, 1234, 29829, 1};
  ResolverFixture resolver{};
  resolver.factions[0].faction_id = 11;
  resolver.factions[0].target_character_id = 29829;
  resolver.characters[0].character_id = 29829;
  FactionTargetingRowObserverStateV1 state{};
  assert(xar::bridge::InstallFactionTargetingRowObserverV1(
      state, Environment(memory, admission, resolver)));

  FactionRowFixture row{11, {}};
  TargetingContainerFixture container{
      reinterpret_cast<std::uintptr_t>(&row), 0xFFFFFFFFU, 1};
  assert(xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2000));
  auto before =
      xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(before.observation.published_generation == 2);

  resolver.fail_faction = true;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2001));
  auto after =
      xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.last_faction_ids[0] == 11);

  resolver.fail_faction = false;
  admission.calls = 0;
  admission.drift_on_second = true;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2002));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.rejected_state_change_count == 1);

  admission.calls = 0;
  admission.drift_on_second = false;
  admission.value.player_targeting_faction_count = 2;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2003));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.count_equivalence_failure_count == 1);
  assert((after.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_count_equivalence) !=
         0);

  admission.value.player_targeting_faction_count = 1;
  resolver.factions[0].target_character_id = 29999;
  resolver.characters[1].character_id = 29999;
  admission.calls = 0;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2004));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.target_character_failure_count == 1);
  assert((after.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_target_character) !=
         0);

  resolver.factions[0].target_character_id = 29829;
  resolver.factions[0].leader_character_id = 4200;
  resolver.round_trip_mismatch_character_id = 4200;
  admission.calls = 0;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2005));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.leader_character_failure_count == 1);
  assert((after.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_leader_character) !=
         0);

  resolver.factions[0].leader_character_id = 0;
  resolver.round_trip_mismatch_character_id = 0;
  CharacterMemberRowFixture member{};
  member.character_id = 4101;
  member.owner_faction_id = 99;
  resolver.characters[2].character_id = 4101;
  resolver.factions[0].character_member_data =
      reinterpret_cast<std::uintptr_t>(&member);
  resolver.factions[0].character_member_count = 1;
  admission.calls = 0;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2006));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.member_ownership_failure_count == 1);
  assert((after.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_member_ownership) !=
         0);

  member.owner_faction_id = 11;
  resolver.failed_character_id = 4101;
  admission.calls = 0;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2007));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.member_identity_failure_count == 1);
  assert((after.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_member_identity) !=
         0);

  resolver.failed_character_id = 0;
  resolver.factions[0].character_member_count = 65;
  admission.calls = 0;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2008));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.member_span_failure_count == 1);
  assert((after.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_member_span) != 0);

  resolver.factions[0].character_member_count = 1;
  resolver.characters[3].character_id = 4100;
  memory.drift_read_address =
      reinterpret_cast<std::uintptr_t>(&member.character_id);
  memory.drift_read_match = 2;
  memory.drift_read_matches = 0;
  admission.calls = 0;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2009));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.member_stability_failure_count == 1);
  assert((after.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_member_stability) !=
         0);

  memory.drift_read_address = reinterpret_cast<std::uintptr_t>(
      &resolver.factions[0].leader_character_id);
  memory.drift_read_match = 2;
  memory.drift_read_matches = 0;
  resolver.factions[0].leader_character_id = 4101;
  admission.calls = 0;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2010));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.leader_stability_failure_count == 1);
  assert((after.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_leader_stability) !=
         0);

  memory.drift_read_address = 0;
  memory.drift_read_match = 0;
  memory.drift_read_matches = 0;
  resolver.factions[0].leader_character_id = 0;
  resolver.factions[0].character_member_count = 0;
  resolver.factions[0].character_member_data = 0;

  TargetingContainerFixture oversized{0, 0, 65};
  admission.calls = 0;
  admission.drift_on_second = false;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&oversized), 12, 2011));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.span_read_failure_count == 1);
  assert(xar::bridge::UninstallFactionTargetingRowObserverV1(state));
}

void CheckFixture(const std::string &actual, const char *path) {
  if (path == nullptr) return;
  std::ifstream input(path, std::ios::binary);
  assert(input.good());
  const std::string expected{std::istreambuf_iterator<char>(input),
                             std::istreambuf_iterator<char>()};
  assert(actual == expected);
}

} // namespace

int main(int argc, char **argv) {
  TestDefaultOffAndExactHashGuard();
  const auto serialized = TestAdmissionBeforeReadAndStableIdentityCapture();
  TestTransactionalRejectionKeepsPreviousGeneration();
  CheckFixture(serialized, argc > 1 ? argv[1] : nullptr);
  if (argc == 1) std::cout << serialized;
  return 0;
}
