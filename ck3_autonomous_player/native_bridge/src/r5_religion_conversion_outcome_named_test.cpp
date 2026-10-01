// Reuse the frozen fixture's objects and owner pump; run one named queue case.
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/conversion_outcome12002_mailbox.hpp"
#define permitted_executor permitted_executor_religion_conversion_outcome12002
#define main FrozenConversionOutcomeFixtureMain12002
#include "conversion_outcome12002_mailbox_test.cpp"
#undef main
#undef permitted_executor

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory");
    const std::filesystem::path directory(argv[1]);
    Fixture fixture;
    FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id;
    adapter.frame.date_raw = 53175816;
    api::MainThreadQueryMailboxV1 mailbox{};
    Pump pump(fixture, mailbox);
    Check(mailbox.permitted_executor == nullptr, "primary permit stays null");
    Check(mailbox.permitted_executor_religion_conversion_outcome12002 ==
          &c::ExecutePlayerReligionConversionOutcomeMailbox12002, "exact named callback installed");
    c::PlayerReligionConversionOutcomeMailboxContext12002 query{};
    query.envelope.game = &adapter;
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 901;
    query.target_rite_id = 0x84000001u;
    BindQuery(fixture, query);
    adapter.reads = 0;
    std::atomic<bool> done{false};
    bool result = false, drained = false;
    std::string serialized, failure;
    std::thread worker([&] {
      result = c::RunPlayerReligionConversionOutcomeMailbox12002(
          query, "religion-outcome-named-fixture", serialized, failure);
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
    Check(drained, "actual owner drained named callback");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual ticket reclaimed");
    Check(mailbox.permitted_executor == nullptr, "primary permit remained null through execution");
    Check(mailbox.permitted_executor_religion_conversion_outcome12002 ==
          &c::ExecutePlayerReligionConversionOutcomeMailbox12002, "named callback remained exact");
    Check(result && query.completed && query.envelope.frame_stable && failure.empty() &&
          !serialized.empty(), "actual complete command_result");
    const auto &observed = query.observation;
    Check(observed.available && observed.actor.available && observed.state.available &&
          observed.target_rite_id == 0x84000001u && observed.target_reached == false,
          "actual current actor and target state");
    Check(observed.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
          observed.capture_epoch != 901, "actual owner epoch independent of public revision");
    Check(fixture.native_invocations_ok && fixture.knowledge_calls > 0 && fixture.lookup_calls > 0,
          "actual actor/state native-shaped callbacks reached");
    std::ofstream(directory / "named-current.json") << serialized << '\n';
    std::cout << "PASS checks=" << checks
              << " cases=1 primary_null=true exact_named_callback=true actual_submit_drain_wait_reclaim=true actual_wrapper=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
