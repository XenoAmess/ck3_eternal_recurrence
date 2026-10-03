// Reuse memory/registry fixture construction; do not rerun its old cases.
#define main county_conversion_previous_fixture_main
#include "ck3_12003_county_conversion_test.cpp"
#undef main
#include "xar_bridge/ck3_12003_county_conversion_task_action_v1.hpp"

namespace action = q::action;
namespace {
struct ActionFixture : Fixture {
  bool final_value = true;
  bool queue_value = true;
  int final_calls = 0;
  int clone_calls = 0;
  int queue_calls = 0;
  int destroy_calls = 0;
  std::array<std::uintptr_t, 9> primary{};
  std::array<std::uintptr_t, 2> secondary{};
  action::ChangeCouncilTaskCommand queued;
};
ActionFixture *af = nullptr;
void *Destroy(void *command, std::uint32_t flags) {
  ++af->destroy_calls;
  if (flags != 1) af->bad_arguments = true;
  delete static_cast<action::ChangeCouncilTaskCommand *>(command);
  return nullptr;
}
void **Clone(const void *command, void **storage) {
  ++af->clone_calls;
  if (!storage || *storage) af->bad_arguments = true;
  *storage = new action::ChangeCouncilTaskCommand(
      *static_cast<const action::ChangeCouncilTaskCommand *>(command));
  return storage;
}
bool Queue(void *manager, void **command, std::uint32_t channel) {
  ++af->queue_calls;
  if (manager != af || !command || !*command || channel != action::kCommandChannel)
    af->bad_arguments = true;
  af->queued = *static_cast<const action::ChangeCouncilTaskCommand *>(*command);
  // Retained owning pointer exercises SubmitCommandCopy's residual native
  // deleting destructor on both queue acceptance and rejection.
  return af->queue_value;
}
bool Final(const void *packet, void *tooltip) {
  ++af->final_calls;
  const auto &command = *static_cast<const action::ChangeCouncilTaskCommand *>(packet);
  if (tooltip || command.flags != 0 || command.padding != 0 ||
      std::any_of(command.metadata.begin(), command.metadata.end(),
          [](std::byte b) { return b != std::byte{0}; }) ||
      command.primary_vtable != reinterpret_cast<std::uintptr_t>(af->primary.data()) ||
      command.secondary_vtable != reinterpret_cast<std::uintptr_t>(af->secondary.data()) ||
      command.active_task_id != Fixture::task_id || command.task_type != af->conversion_type.data() ||
      command.scopes.owner_character_id != Fixture::owner_id ||
      command.scopes.incumbent_character_id != Fixture::incumbent_id ||
      command.scopes.target_tag != 8 ||
      std::any_of(command.scopes.reserved.begin(), command.scopes.reserved.end(),
          [](std::byte b) { return b != std::byte{0}; }) ||
      std::any_of(command.scopes.trailing.begin(), command.scopes.trailing.end(),
          [](std::byte b) { return b != std::byte{0}; }) ||
      command.scopes.province_id != Fixture::province_ids[1]) af->bad_arguments = true;
  return af->final_value;
}
action::Access BindAction(ActionFixture &fixture) {
  af = &fixture;
  action::Access access;
  access.county = Bind(fixture);
  access.county.task_dispatch_enabled = true;
  access.county.final_task_validator = &Final;
  fixture.primary[0] = reinterpret_cast<std::uintptr_t>(&Destroy);
  fixture.primary[8] = reinterpret_cast<std::uintptr_t>(&Clone);
  access.primary_vtable = reinterpret_cast<std::uintptr_t>(fixture.primary.data());
  access.secondary_vtable = reinterpret_cast<std::uintptr_t>(fixture.secondary.data());
  access.commands.enabled = true;
  access.commands.command_manager = &fixture;
  access.commands.queue_owned_command = &Queue;
  return access;
}
xar::game::Snapshot Frame() {
  xar::game::Snapshot frame;
  frame.paused = true; frame.map_ready = true;
  frame.has_played_character = true; frame.played_character_alive = true;
  frame.played_character_id = Fixture::owner_id;
  frame.date_raw = 53230008;
  return frame;
}
action::Request Request() {
  action::Request request;
  request.expected_revision = 7;
  request.expected_active_task_id = Fixture::task_id;
  request.expected_incumbent_character_id = Fixture::incumbent_id;
  request.province_id = Fixture::province_ids[1];
  request.action_id = "county-assignment-focused-fixture";
  return request;
}
void DeliverFixtureCommand(ActionFixture &fixture) {
  // Explicit fixture delivery only. Queue acceptance above never changes the
  // task. The real production queue's later Execute is not emulated or claimed.
  Put(fixture.task, 0x18, fixture.queued.task_type);
  Put(fixture.task, 0x40, fixture.queued.scopes);
  Put(fixture.task, 0x20, std::int64_t{0});
  fixture.task[0x39] = std::byte{1};
}
void Save(const std::filesystem::path &directory, const char *name, const std::string &payload) {
  std::ofstream(directory / name) << payload << '\n';
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 100;
  const std::filesystem::path directory{argv[1]};
  ActionFixture fixture;
  auto access = BindAction(fixture);
  auto request = Request();
  const auto frame = Frame();

  fixture.final_value = false;
  auto rejected = action::SubmitCountyConversionTask12003(access, frame, 7, 12, 501,
      "county-task-11111111111111111111111111111111", request);
  if (!Check(rejected.status == action::SubmitStatus::not_submitted &&
      rejected.native_final_can_dispatch == false && !rejected.native_submit_copy_called &&
      fixture.final_calls == 1 && fixture.clone_calls == 0 && fixture.queue_calls == 0,
      "actual final native denial does not clone or queue") ||
      !Check(!fixture.bad_arguments, "exact 80-byte command fields and single final evaluation")) return 1;
  Save(directory, "native-final-denied-submission.json",
      action::SerializeCountyConversionTaskSubmission12003(rejected));

  fixture.final_value = true;
  request.expected_active_task_id ^= 0x01000000;
  auto stale = action::SubmitCountyConversionTask12003(access, frame, 7, 12, 502, "stale", request);
  if (!Check(stale.failure == "county_task_current_identity_changed" &&
      fixture.final_calls == 1 && fixture.clone_calls == 0,
      "full generation task identity mismatch remains an observed rejection")) return 2;
  request = Request();
  Put(fixture.rr_type, 0x54, std::int32_t{2});
  auto replacement = action::SubmitCountyConversionTask12003(access, frame, 7, 12, 503,
      "finite", request);
  if (!Check(replacement.failure == "county_task_replacement_required" &&
      fixture.final_calls == 1 && fixture.queue_calls == 0,
      "native finite-progress confirmation is expressed by explicit request field")) return 3;
  Put(fixture.rr_type, 0x54, std::int32_t{0});

  auto submitted = action::SubmitCountyConversionTask12003(access, frame, 7, 12, 504,
      "county-task-11111111111111111111111111111111", request);
  if (!Check(submitted.status == action::SubmitStatus::queued_verification_pending &&
      submitted.native_final_can_dispatch == true && submitted.native_submit_copy_called &&
      fixture.final_calls == 2 && fixture.clone_calls == 1 && fixture.queue_calls == 1 &&
      fixture.destroy_calls == 1, "production final + owning clone queue + native residual cleanup") ||
      !Check(submitted.before.task_key == "task_religious_relations" &&
      submitted.before.progress_kind == 0 && !request.replace_existing_task &&
      fixture.queued.scopes.province_id == request.province_id,
      "infinite incumbent task takes actual native direct branch")) return 4;
  Save(directory, "queued-submission.json",
      action::SerializeCountyConversionTaskSubmission12003(submitted));

  auto pending = action::ReadCountyConversionTaskResult12003(access, submitted, 505);
  if (!Check(pending.verification_pending && !pending.task_assignment_material_observed &&
      pending.actual_task_assignment_matches == false && pending.actual_task_id_unchanged == true,
      "queue ACK and unchanged task alone do not fabricate assignment")) return 5;
  Save(directory, "undelivered-independent-result.json",
      action::SerializeCountyConversionTaskIndependentResult12003(pending));

  DeliverFixtureCommand(fixture);
  auto delivered = action::ReadCountyConversionTaskResult12003(access, submitted, 506);
  if (!Check(delivered.task_assignment_material_observed && !delivered.verification_pending &&
      delivered.actual_task_assignment_matches == true && delivered.actual_task_id_unchanged == true,
      "fresh real task scopes observe assignment with identical FullTaskID") ||
      !Check(delivered.after.task_key == q::kTaskKey && delivered.after.target_scope_tag == 8 &&
      delivered.after.owner_character_id == Fixture::owner_id &&
      delivered.after.incumbent_character_id == Fixture::incumbent_id &&
      delivered.after.target_county_title_id == Fixture::title_ids[1] &&
      delivered.after.percentage_progress_raw == 0 && !delivered.county_conversion_completed,
      "independent registry type/owner/incumbent/Province/County/progress, no conversion benefit")) return 6;
  Save(directory, "delivered-independent-result.json",
      action::SerializeCountyConversionTaskIndependentResult12003(delivered));

  auto noop = action::SubmitCountyConversionTask12003(access, frame, 7, 12, 507, "noop", request);
  if (!Check(noop.status == action::SubmitStatus::already_active_noop &&
      !noop.native_submit_copy_called && fixture.clone_calls == 1 && fixture.final_calls == 2,
      "same native type and Province produce no duplicate assignment")) return 7;
  Save(directory, "already-active-noop-submission.json",
      action::SerializeCountyConversionTaskSubmission12003(noop));

  Put(fixture.task, 0x18, fixture.rr_type.data());
  Put(fixture.task, 0x48, std::uint32_t{0});
  Put(fixture.task, 0x50, std::int32_t{-1});
  fixture.queue_value = false;
  auto queue_rejected = action::SubmitCountyConversionTask12003(access, frame, 7, 12, 508,
      "rejected", request);
  if (!Check(queue_rejected.failure == "county_task_native_queue_rejected" &&
      queue_rejected.status == action::SubmitStatus::not_submitted &&
      fixture.clone_calls == 2 && fixture.queue_calls == 2 && fixture.destroy_calls == 2,
      "native queue rejection preserved with owning cleanup") ||
      !Check(!fixture.bad_arguments && fixture.allocations == fixture.releases,
      "actual reader callback arguments and existing candidate ownership preserved")) return 8;
  std::cout << "PASS checks=" << checks << " new_cases=8 actual_action=true actual_reader=true "
      "actual_serializer=true owning_clone_queue=true live=false\n";
  return 0;
}
