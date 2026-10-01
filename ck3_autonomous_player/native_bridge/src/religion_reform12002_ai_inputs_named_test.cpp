// Exact frozen generic helper copy, with both old mains renamed and uncalled.
#include "religion_reform12002_ai_inputs_named_frozen_helpers.hpp"
#include "religion_reform12002_ai_inputs_named_other_permits.hpp"

namespace {
c::PlayerReligionAIReformInputsObservation12002 NamedAIInputsQuery(
    AIInputsBacking &backing, FrameAdapter &adapter, const std::filesystem::path &directory, const char *filename) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(backing.base, mailbox);
  ClearOtherAIInputsPermits(mailbox);
  mailbox.permitted_executor_religion_ai_reform_inputs12002 = &c::ExecutePlayerReligionAIReformInputsMailbox12002;
  Check(AllOtherAIInputsPermitsNull(mailbox) && mailbox.permitted_executor_religion_ai_reform_inputs12002 ==
            &c::ExecutePlayerReligionAIReformInputsMailbox12002, "only actual dedicated AI inputs executor configured");
  c::PlayerReligionAIReformInputsMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings.core = Bind(backing.base).core;
  query.bindings.context = {true, &backing.context_state_slot};
  query.bindings.schedule = {true, &AIInputsTier, &AIInputsIndependent, &backing.period_data, &backing.toggle};
  ai_inputs_backing = &backing;
  adapter.reads = 0;
  std::atomic<bool> done{false}; bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionAIReformInputsMailbox12002(
        query, "ai-inputs\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained && mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
        "actual dedicated AI inputs admission / owner drain / terminal wait reclaim");
  Check(result && query.completed && query.envelope.frame_stable && !serialized.empty() && failure.empty(),
        "actual AI holder/schedule collector / Finish / complete native command_result");
  Check(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
        query.observation.capture_epoch != 701 && query.envelope.executor == &c::ExecutePlayerReligionAIReformInputsMailbox12002,
        "exact owning pump stamp and typed AI inputs callback");
  std::ofstream(directory / filename) << serialized << '\n';
  return query.observation;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    auto backing = std::make_unique<AIInputsBacking>();
    FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = Fixture::date;
    auto out = NamedAIInputsQuery(*backing, adapter, directory, "multiple-controllers.json");
    Check(out.available && out.gate_inputs_observation_complete &&
          out.context.status == f::AIContextStatus::observed_controllers && out.context.actual_holder_count == 5 &&
          out.context.controllers.size() == 3 && out.controller_inputs.size() == 3 &&
          out.context.controllers[0].actual_ai == backing->ordinary_a.data() &&
          out.context.controllers[1].actual_ai == backing->special.data() &&
          out.context.controllers[2].actual_ai == backing->ordinary_b.data() &&
          out.controller_inputs[0].schedule.rare_countdown_prepare_ticks == -4 &&
          out.controller_inputs[1].schedule.ai_status == f::ScheduleAIStatus::gates_only &&
          out.controller_inputs[2].schedule.rare_countdown_prepare_ticks == 12 &&
          backing->tier_reads == 4 && backing->independent_reads == 4 && backing->base.arguments_correct,
          "same actual multiple-controller holder and per-member schedule outcome");
    backing->NoMatchingController();
    out = NamedAIInputsQuery(*backing, adapter, directory, "observed-no-ai.json");
    Check(out.available && out.gate_inputs_observation_complete &&
          out.context.status == f::AIContextStatus::observed_no_ai && out.context.actual_holder_count == 2 &&
          out.context.controllers.empty() && out.controller_inputs.empty() &&
          out.schedule_base.status == f::ScheduleStatus::observed &&
          out.schedule_base.ai_status == f::ScheduleAIStatus::not_supplied &&
          out.schedule_base.actor_id == Fixture::actor_id && out.schedule_base.rare_period == 360 &&
          backing->tier_reads == 5 && backing->independent_reads == 5,
          "same actual known controller absence with observed no-AI base inputs");
    std::cout << "PASS checks=" << checks << " cases=1 queued_commands=2 named_only=true actual_ai_holder=true actual_schedule=true "
                 "actual_submit_owner_drain_finish_wait_reclaim=true actual_command_result=true "
                 "frozen_12_case_main_invoked=false frozen_generic_main_invoked=false "
                 "ai_provider_matrix_repeated=false schedule_provider_matrix_repeated=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
