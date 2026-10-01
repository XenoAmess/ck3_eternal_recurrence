// The artifact helper copy renames only the frozen outer generic-case main.
// The provider main was already renamed; neither old main is executed.
#include "religion_reform12002_tenet_sources_named_frozen_helpers.hpp"
#include "religion_reform12002_tenet_sources_named_permit_check.hpp"

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    auto backing = std::make_unique<Fixture>();
    TenetFrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = static_cast<std::int32_t>(Fixture::actor_id);
    adapter.frame.date_raw = 53175816;
    api::MainThreadQueryMailboxV1 mailbox{};
    TenetPump pump(*backing, mailbox);
    mailbox.permitted_executor = nullptr;
    mailbox.permitted_executor_religion_draft_tenet_choices12002 =
        &c::ExecutePlayerReligionDraftTenetChoicesMailbox12002;
    Require(OnlyTenetNamedPermit12002(mailbox),
        "actual dedicated Tenet permit enabled and every other permit null");
    c::PlayerReligionDraftTenetChoicesMailboxContext12002 query{};
    query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 701;
    query.bindings = Bind(*backing);
    std::atomic<bool> done{false};
    bool result = false, drained = false;
    std::string serialized, failure;
    std::thread worker([&] {
      result = c::RunPlayerReligionDraftTenetChoicesMailbox12002(
          query, "draft-tenets\"mailbox-fixture", serialized, failure);
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
    Require(drained, "actual dedicated Tenet callback admitted and drained on owner");
    Require(mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
        "actual dedicated Tenet terminal ticket reclaimed");
    Require(result && query.completed && query.envelope.frame_stable && failure.empty() &&
        !serialized.empty() && adapter.reads == 2,
        "actual provider / Finish / complete named caller wire");
    const auto &out = query.observation;
    Require(out.capture_epoch == query.envelope.execution_stamp.pump_epoch && out.capture_epoch != 701 &&
        query.envelope.execution_stamp.thread_id == adapter.owner &&
        query.envelope.executor == &c::ExecutePlayerReligionDraftTenetChoicesMailbox12002,
        "actual owner epoch, thread and exact typed named callback");
    Require(out.available && out.draft_observed && out.tenet_gates_complete &&
        out.sources.size() == 8 && out.slots.size() == 2 && out.slots[0].slot_index == 7 &&
        out.slots[1].slot_index == 11 && out.source_faith_id == Fixture::source_faith_id &&
        out.source_main_rite_id == Fixture::main_id && backing->correct_native_inputs &&
        backing->filter_calls == 8,
        "same actual source/category/main-Rite/actor-Faith/TopScope inputs");
    Require(out.sources[0].duplicate_excluded && !out.sources[0].final_selectable &&
        out.sources[0].native_can_pick && out.sources[3].native_status_raw == 0 &&
        out.sources[3].knowledge && out.sources[3].final_selectable &&
        out.sources[4].source_can_materialize && !out.sources[4].native_can_pick &&
        !out.sources[2].final_selectable && !out.sources[6].passed_shown && out.sources[7].final_selectable,
        "actual eight-source filter and final gates preserved through dedicated slot");
    std::ofstream(directory / "actual-multiple-sources.json") << serialized << '\n';
    std::cout << "PASS checks=" << mailbox_checks << " cases=1 named_only=true actual_tenet_sources_provider=true "
        "actual_submit_owner_drain_finish_wait_reclaim=true actual_command_result=true "
        "frozen_provider_main_invoked=false frozen_generic_main_invoked=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
