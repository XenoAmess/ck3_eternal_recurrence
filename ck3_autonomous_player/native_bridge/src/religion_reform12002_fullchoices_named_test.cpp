// The runner copies the exact frozen generic helper and renames only its main.
// Neither the generic caller main nor the original twelve-case main is invoked.
#include "religion_reform12002_fullchoices_named_frozen_helpers.hpp"
#include "religion_reform12002_fullchoices_named_other_permits.hpp"

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    auto backing = std::make_unique<FullChoiceBacking>();
    FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = Fixture::date;
    api::MainThreadQueryMailboxV1 mailbox{};
    Pump pump(backing->base, mailbox);
    ClearOtherFullChoicePermits(mailbox);
    mailbox.permitted_executor_religion_draft_doctrine_choices12002 =
        &c::ExecutePlayerReligionDraftDoctrineChoicesMailbox12002;
    Check(AllOtherFullChoicePermitsNull(mailbox) &&
          mailbox.permitted_executor_religion_draft_doctrine_choices12002 ==
              &c::ExecutePlayerReligionDraftDoctrineChoicesMailbox12002,
          "only actual dedicated full Doctrine choices executor configured");
    c::PlayerReligionDraftDoctrineChoicesMailboxContext12002 query{};
    query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 701;
    query.bindings = Bind(backing->base).choices;
    query.bindings.evaluate_trigger = &FullSourceTrigger;
    query.bindings.knows_doctrine = &FullSourceKnowledge;
    query.bindings.has_perk = &FullSourceProphet;
    full_choice_backing = backing.get();
    std::atomic<bool> done{false}; bool result = false, drained = false;
    std::string serialized, failure;
    std::thread worker([&] {
      result = c::RunPlayerReligionDraftDoctrineChoicesMailbox12002(
          query, "draft-doctrines\"mailbox-fixture", serialized, failure);
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
    Check(drained, "actual dedicated full Doctrine query admitted and drained on owner");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual terminal wait / reclaim completed");
    Check(result && query.completed && query.envelope.frame_stable && !serialized.empty() && failure.empty(),
          "actual full Doctrine reader / Finish / complete native command_result");
    const auto &out = query.observation;
    unsigned selectable = 0;
    for (const auto &slot : out.slots) for (const auto &row : slot.sources) if (row.final_selectable) ++selectable;
    Check(out.available && out.draft_observed && out.doctrine_gates_complete && out.slots.size() == 4 &&
          out.slots[0].sources.size() == 6 && out.slots[1].sources.size() == 6 &&
          out.slots[2].sources.size() == 3 && out.slots[3].sources.empty() && selectable == 5 &&
          backing->trigger_reads == 24 && backing->knowledge_reads == 9 && backing->perk_reads == 4 &&
          backing->base.arguments_correct, "single actual visible four-slot full Doctrine outcome");
    Check(out.capture_epoch == query.envelope.execution_stamp.pump_epoch && out.capture_epoch != 701 &&
          query.envelope.executor == &c::ExecutePlayerReligionDraftDoctrineChoicesMailbox12002,
          "owning pump stamp and exact typed full Doctrine callback");
    std::ofstream(directory / "visible-four-slots.json") << serialized << '\n';
    std::cout << "PASS checks=" << checks << " cases=1 named_only=true actual_fullchoices_provider=true "
                 "actual_submit_owner_drain_finish_wait_reclaim=true actual_command_result=true "
                 "frozen_12_case_main_invoked=false frozen_generic_main_invoked=false provider_matrix_repeated=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
