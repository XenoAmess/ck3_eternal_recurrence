// Reuse two existing bounded RAM/adapter fixtures without executing their mains.
// This owner fixture never maps or launches Game; source_kind stays offline_fixture.
#define wmain RosterUnusedCoreFixture041
#include "ck3_1210_core_frame_test.cpp"
#undef wmain
#undef CHECK
#define main RosterUnusedManagerFixture041
#include "ck3_1210_character_manager_v1_focused_test.cpp"
#undef main
#include "xar_bridge/ck3_1210_character_roster_frame_v1.hpp"
namespace {
using namespace xar::ck3_11906;
constexpr std::array<std::string_view, 1> kRosterCaps{kCharacterRosterCapabilityV1};
constexpr std::array<std::string_view, 6> kRosterCases{
  "reader_observed", "reader_lifecycle_changed", "owner_missing", "revision_changed", "connection_changed", "wrong_tuple"};
struct RosterMembershipChange {
  Fixture *fixture;
  std::int32_t second_count = 4;
  MainThreadQueryMailboxV1 *owner = nullptr;
  int owner_change = -1;
  static bool Copy(void *opaque, const void *source, void *destination, std::size_t bytes) noexcept {
    auto &change = *static_cast<RosterMembershipChange *>(opaque);
    auto &f = *change.fixture;
    if (source == &f.storage_pointer && f.root_reads == 2)
      Put(f.data, kCharacterManagerOffsetV1 + 0x2C, change.second_count);
    const bool copied = Fixture::Copy(&f, source, destination, bytes);
    if (change.owner && source == &f.storage_pointer && f.root_reads == 2) {
      if (change.owner_change == 0) change.owner->proof_reset_requested.store(true);
      if (change.owner_change == 1) change.owner->pump_epochs.fetch_add(1);
      if (change.owner_change == 2) change.owner->active_hook_calls.store(0);
    }
    return copied;
  }
};
std::string RosterCase(std::string_view name) {
  Fixture f; const auto expected = f.Expected();
  xar::game::AdapterDescriptor descriptor{kAdapterId, kGameVersion, kExecutableSha256, "xar_checkpoint", kRosterCaps};
  if (name == "wrong_tuple") descriptor.game_version = "1.20.0.4";
  FixtureAdapter adapter(descriptor);
  std::uint64_t revision = 17, generation = 23;
  CharacterRosterMailboxContextV1 q{}; q.bindings = f.bindings; q.expected = expected;
  q.expected_native_revision = revision; q.expected_connection_generation = generation;
  q.current_native_revision = &revision; q.current_connection_generation = &generation;
  q.fixture_access = {&f, Fixture::Copy};
  RosterMembershipChange membership{&f, name == "reader_member_removed" ? 3 : 4};
  if (name == "reader_member_added" || name == "reader_member_removed") {
    if (name == "reader_member_added") Put(f.data, kCharacterManagerOffsetV1 + 0x2C, std::int32_t{3});
    q.fixture_access = {&membership, RosterMembershipChange::Copy};
  }
  MainThreadQueryMailboxV1 mailbox{}; mailbox.offline_fixture = true;
  PersonalGoldMailboxContextV1 parent{}; parent.kind = ActorObservationKindV1::character_roster;
  parent.roster = &q; parent.game = &adapter; parent.mailbox = &mailbox;
  parent.bindings = {true, f.bindings.core}; parent.ticket.sequence = 71;
  MainThreadExecutionStampV1 stamp{}; stamp.thread_id = GetCurrentThreadId(); stamp.pump_epoch = 89;
  stamp.tls_initialized = stamp.tls_main_thread_marker = 1; stamp.tls_context = 1;
  stamp.paused = true; stamp.date_raw = expected.clock.date_raw;
  stamp.game_state = reinterpret_cast<std::uintptr_t>(f.state_pointer);
  stamp.jomini_state = reinterpret_cast<std::uintptr_t>(f.jomini_pointer);
  mailbox.iat_hook_installed.store(true); mailbox.owner_thread_id.store(stamp.thread_id);
  mailbox.pump_epochs.store(stamp.pump_epoch); mailbox.active_hook_calls.store(1);
  mailbox.paused_owner_verified_pump_epochs.store(2);
  mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(71); mailbox.executor_started_sequence.store(71);
  mailbox.executor_started_pump_epoch.store(89); mailbox.executor_context = &parent;
  mailbox.executor.store(&ExecutePersonalGoldMailboxV1);
  const auto late = name.find("owner_late_") == 0;
  if (late) {
    membership.owner = &mailbox; membership.owner_change = name.back() - char(48);
    q.fixture_access = {&membership, RosterMembershipChange::Copy};
  }
  if (name == "owner_reset") mailbox.proof_reset_requested.store(true);
  if (name == "owner_epoch") mailbox.pump_epochs.fetch_add(1);
  if (name == "owner_drained") mailbox.active_hook_calls.store(0);
  if (name == "owner_missing") mailbox.state.store(MainThreadQueryMailboxStateV1::idle);
  if (name == "revision_changed") ++revision;
  if (name == "connection_changed") ++generation;
  if (name == "reader_lifecycle_changed") f.mutation = Mutation::death;
  Check(ExecuteCharacterRosterOnActorOwnerV1(parent, stamp), "query infrastructure completes");
  Check(!q.application_main_observed && !q.source.custody_available && !parent.application_main_observed,
    "offline fixture never acquires actual application-main/sourceproof");
  if (name == "reader_observed") {
    Check(q.observation.available && q.observation.members.size() == 4 && q.source.offline_fixture,
      "actual Core->manager->copied rows in RAM");
    Check(q.observation.members[0].character_id == kPeer && q.observation.members[1].character_id == 0 &&
      !q.observation.members[2].alive, "raw native order/negative/zero/dead retained");
  } else Check(!q.observation.available && q.observation.members.empty(), "failure clears all roster DATA");
  const auto wire = SerializeCharacterRosterCommandResultV1(std::string("roster-fixture-") + std::string(name), q);
  Check(wire.find("actor_readonly_manager_roster") != std::string::npos &&
    wire.find("same_owner_family_join_available") != std::string::npos,
    "owner envelope has actual roster identity and explicit missing Family scope");
  return wire;
}
} // namespace
int main(int argc, char **argv) {
  const bool emit = argc == 2 && std::string_view(argv[1]) == "--emit-character-roster-owner-ram";
  if (argc != 1 && !emit) return 2;
  for (const auto name : kRosterCases) {
    const auto wire = RosterCase(name);
    if (emit) std::cout << R"({"case":")" << name << R"(","command_result":)" << wire << '}' << char(10);
  }
  if (!emit) {
    (void)RosterCase("reader_member_added"); (void)RosterCase("reader_member_removed");
    for (const auto name : {"owner_reset", "owner_epoch", "owner_drained",
        "owner_late_0", "owner_late_1", "owner_late_2"}) (void)RosterCase(name);
    std::cout << "PASS actual RAM reader to roster wire; no actual owner-main or Family proof" << char(10);
  }
}
