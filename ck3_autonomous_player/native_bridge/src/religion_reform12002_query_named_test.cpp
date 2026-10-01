// Reuse the frozen memory backing and helpers without invoking its matrix.
#define main FrozenReform12CaseMainNotExecuted
#include "religion_reform12002_query_mailbox_test.cpp"
#undef main

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    auto fixture = std::make_unique<Fixture>();
    FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = Fixture::date;
    api::MainThreadQueryMailboxV1 mailbox{};
    Pump pump(*fixture, mailbox);
    mailbox.permitted_executor = nullptr;
    mailbox.permitted_executor_religion_reform12002 = &c::ExecutePlayerReligionReformMailbox12002;
    Check(mailbox.permitted_executor == nullptr &&
          mailbox.permitted_executor_religion12002 == nullptr &&
          mailbox.permitted_executor_religion_reform12002 == &c::ExecutePlayerReligionReformMailbox12002,
          "generic and earlier religion slots absent; exact new named callback configured");
    c::PlayerReligionReformMailboxContext12002 query{};
    query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 701;
    query.bindings = Bind(*fixture);
    std::atomic<bool> done{false};
    bool result = false, drained = false;
    std::string serialized, failure;
    std::thread worker([&] {
      result = c::RunPlayerReligionReformMailbox12002(
          query, "reform\"mailbox-fixture", serialized, failure);
      done.store(true, std::memory_order_release);
    });
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
    while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
      if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
        drained = api::ObserveMainThreadPumpAndDrainV1(
            mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    worker.join();
    Check(drained, "actual new named callback submitted and drained on owner");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
          "actual wait and reclaim return mailbox to idle");
    Check(result && failure.empty() && !serialized.empty() && query.completed && query.envelope.frame_stable,
          "actual provider and Finish return complete result");
    const auto &out = query.observation;
    Check(out.available && out.current_window.visible && out.draft_eligibility.can_create_rite == true &&
          out.draft_eligibility.can_edit_rite == false && out.draft_costs.piety_cost_raw == 9000000 &&
          out.current_doctrine_selection.selectable_doctrine_keys == std::vector<std::string>{"doctrine_a"} &&
          fixture->arguments_correct, "single frozen visible-create actual provider outcome");
    Check(out.capture_epoch == query.envelope.execution_stamp.pump_epoch && out.capture_epoch != 701 &&
          query.envelope.executor == &c::ExecutePlayerReligionReformMailbox12002,
          "actual owner stamp and typed executed callback");
    std::ofstream(directory / "visible-create.json") << serialized << '\n';
    std::cout << "PASS checks=" << checks << " cases=1 named_only=true actual_submit_owner_drain_finish_wait_reclaim=true "
                 "actual_command_result=true frozen_12_case_main_invoked=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
