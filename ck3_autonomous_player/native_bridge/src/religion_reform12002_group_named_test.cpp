// The runner supplies an exact frozen helper copy with both old mains renamed.
// Neither the original 12-case nor 4-case matrix is invoked.
#include "religion_reform12002_group_named_frozen_helpers.hpp"

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    auto backing = std::make_unique<GroupBacking>();
    FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = Fixture::date;
    api::MainThreadQueryMailboxV1 mailbox{};
    Pump pump(backing->base, mailbox);
    mailbox.permitted_executor = nullptr;
    mailbox.permitted_executor_religion_draft_groups12002 = &c::ExecutePlayerReligionDraftGroupsMailbox12002;
    Check(mailbox.permitted_executor == nullptr && mailbox.permitted_executor_religion12002 == nullptr &&
          mailbox.permitted_executor_religion_reform12002 == nullptr &&
          mailbox.permitted_executor_religion_draft_groups12002 == &c::ExecutePlayerReligionDraftGroupsMailbox12002,
          "only actual dedicated draft-groups executor configured");
    c::PlayerReligionDraftGroupsMailboxContext12002 query{};
    query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 701;
    query.bindings = Bind(backing->base).choices;
    std::atomic<bool> done{false}; bool result = false, drained = false;
    std::string serialized, failure;
    std::thread worker([&] {
      result = c::RunPlayerReligionDraftGroupsMailbox12002(
          query, "draft-groups\"mailbox-fixture", serialized, failure);
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
    Check(drained, "actual dedicated group query admitted and drained on owner");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual terminal wait / reclaim completed");
    Check(result && query.completed && query.envelope.frame_stable && !serialized.empty() && failure.empty(),
          "actual group read / Finish / complete native command_result");
    const auto &out = query.observation;
    Check(out.available && out.draft_observed && out.selected_slots.size() == 2 &&
          out.selected_slots[0].group_source_definition_keys == std::vector<std::string>{"doctrine_a", "doctrine_b"} &&
          out.selected_slots[1].group_source_definition_keys == std::vector<std::string>{"doctrine_c", "doctrine_d"} &&
          out.current_tenet_choices.size() == 1 && out.current_tenet_choices[0].final_can_pick &&
          out.current_category_slot == 0 && backing->base.arguments_correct,
          "single actual visible-two-slots group model outcome");
    Check(out.capture_epoch == query.envelope.execution_stamp.pump_epoch && out.capture_epoch != 701 &&
          query.envelope.executor == &c::ExecutePlayerReligionDraftGroupsMailbox12002,
          "owning pump stamp and exact typed group callback");
    std::ofstream(directory / "visible-multi-slots.json") << serialized << '\n';
    std::cout << "PASS checks=" << checks << " cases=1 named_only=true actual_group_provider=true "
                 "actual_submit_owner_drain_finish_wait_reclaim=true actual_command_result=true "
                 "frozen_12_case_main_invoked=false frozen_4_case_main_invoked=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
