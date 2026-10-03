// Reuse fixture construction only; never run the old seven-case main.
#define main county_component_previous_main
#include "ck3_12003_county_conversion_test.cpp"
#undef main

namespace {
struct DispatchFixture : Fixture {
  std::int32_t rejected_province = province_ids[1];
  int final_calls = 0;
};
DispatchFixture *df = nullptr;

bool FinalTaskValidator(const void *packet, void *tooltip) {
  ++df->final_calls;
  const auto *scopes = static_cast<const std::byte *>(packet) + 0x30;
  const auto target = Load<std::int64_t>(scopes, 0x10);
  if (tooltip || Load<std::int32_t>(packet, 0x20) != Fixture::task_id ||
      Load<const void *>(packet, 0x28) != df->conversion_type.data() ||
      Load<std::int32_t>(scopes, 0) != Fixture::incumbent_id ||
      Load<std::int32_t>(scopes, 4) != Fixture::owner_id ||
      Load<std::uint32_t>(scopes, 8) != 8U ||
      Load<std::uint64_t>(scopes, 0x18) != 0 ||
      std::none_of(Fixture::province_ids.begin(), Fixture::province_ids.end(),
          [&](auto id) { return target == id; })) df->bad_arguments = true;
  return target != df->rejected_province;
}

q::Environment BindDispatch(DispatchFixture &fixture) {
  df = &fixture;
  auto e = Bind(fixture);
  e.task_dispatch_enabled = true;
  e.final_task_validator = &FinalTaskValidator;
  return e;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 100;
  const std::filesystem::path dir{argv[1]};
  DispatchFixture fixture;
  auto environment = BindDispatch(fixture);
  q::Observation out{};
  if (!Check(q::ReadCountyConversion12003(environment, 301, out) && out.task_dispatch &&
      out.task_dispatch->available, "native final dispatch input from production reader") ||
      !Check(out.task_dispatch->candidates.size() == 3 && fixture.final_calls == 3,
      "one final command validator call for each actual candidate") ||
      !Check(!out.task_dispatch->candidates[1].native_final_can_dispatch &&
      out.candidates[1].native_target_valid && out.native_task_valid == true,
      "native command denial remains distinct from target and task validity") ||
      !Check(out.task_dispatch->candidates[0].native_final_can_dispatch &&
      out.task_dispatch->candidates[2].native_final_can_dispatch,
      "native true and false are preserved in one complete eligibility query") ||
      !Check(std::all_of(out.task_dispatch->candidates.begin(), out.task_dispatch->candidates.end(),
      [](const auto &row) { return row.replacement_required && !row.already_active_at_target; }),
      "RR replacement prerequisite for all proposed conversion targets") ||
      !Check(!fixture.bad_arguments,
      "actual task ID and type plus owner/incumbent/province scopes; no appointment calls")) return 1;
  Wire(dir, "final-command-accepted-and-denied.json", out);

  fixture.rejected_province = -1;
  Put(fixture.task, 0x18, fixture.conversion_type.data());
  Put(fixture.task, 0x48, std::uint32_t{8});
  Put(fixture.task, 0x50, Fixture::province_ids[1]);
  fixture.task[0x39] = std::byte{1};
  if (!Check(q::ReadCountyConversion12003(environment, 302, out) && out.task_dispatch->available,
      "current conversion task eligibility input") ||
      !Check(out.task_dispatch->candidates[1].already_active_at_target &&
      !out.task_dispatch->candidates[1].replacement_required &&
      out.task_dispatch->candidates[1].native_final_can_dispatch,
      "native final true does not erase already-active no-op prerequisite") ||
      !Check(out.task_dispatch->candidates[0].replacement_required &&
      out.task_dispatch->candidates[2].replacement_required && fixture.final_calls == 6,
      "same task at another county requires replacing existing target") ||
      !Check(!fixture.bad_arguments, "current target keeps native fullID scopes")) return 2;
  Wire(dir, "already-active-current-county.json", out);

  environment.final_task_validator = nullptr;
  if (!Check(q::ReadCountyConversion12003(environment, 303, out) && out.available &&
      out.task_dispatch && !out.task_dispatch->available &&
      out.task_dispatch->failure == "bindings_unavailable",
      "missing final input leaves existing county observation available") ||
      !Check(out.task_dispatch->candidates.empty() && out.candidates.size() == 3 &&
      fixture.final_calls == 6, "unavailable final read does not invent native false rows")) return 3;
  Wire(dir, "final-validator-unavailable.json", out);

  environment.final_task_validator = &FinalTaskValidator;
  fixture.shown_value = false;
  if (!Check(q::ReadCountyConversion12003(environment, 304, out) && out.task_dispatch->available &&
      out.native_task_shown == false && out.candidates.empty(),
      "known task-wide hidden result completely blocks candidate dispatch inputs") ||
      !Check(fixture.final_calls == 6 && out.task_dispatch->candidates.empty() &&
      fixture.allocations == fixture.releases && !fixture.bad_arguments,
      "no native final calls for hidden task and unchanged target allocation ownership")) return 4;
  Wire(dir, "task-hidden-known-blocker.json", out);
  std::cout << "PASS checks=" << checks << " cases=4 actual_reader=true actual_serializer=true live=false\n";
  return 0;
}
