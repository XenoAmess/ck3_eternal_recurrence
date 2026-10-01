// The runner creates an exact frozen helper copy with its outer main renamed.
// Neither the original 12-case nor the prior generic resource case is invoked.
#include "religion_reform12002_resource_costs_named_frozen_helpers.hpp"

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
    mailbox.permitted_executor_religion_draft_resource_costs12002 =
        &c::ExecutePlayerReligionDraftResourceCostsMailbox12002;
    Check(mailbox.permitted_executor == nullptr &&
          mailbox.permitted_executor_religion12002 == nullptr &&
          mailbox.permitted_executor_religion_reform12002 == nullptr &&
          mailbox.permitted_executor_religion_draft_groups12002 == nullptr &&
          mailbox.permitted_executor_religion_draft_doctrine_choices12002 == nullptr &&
          mailbox.permitted_executor_religion_draft_tenet_choices12002 == nullptr &&
          mailbox.permitted_executor_religion_draft_resource_costs12002 ==
              &c::ExecutePlayerReligionDraftResourceCostsMailbox12002,
          "only the actual dedicated resource-cost executor configured");
    c::PlayerReligionDraftResourceCostsMailboxContext12002 query{};
    query.envelope.game = &adapter;
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 701;
    const auto bindings = Bind(*fixture);
    query.window_bindings = bindings.window;
    query.cost_bindings = bindings.costs;
    std::atomic<bool> done{false};
    bool result = false, drained = false;
    std::string serialized, failure;
    std::thread worker([&] {
      result = c::RunPlayerReligionDraftResourceCostsMailbox12002(
          query, "draft-resource-costs\"mailbox-fixture", serialized, failure);
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
    Check(drained, "actual resource-cost callback drained on fixture owning thread");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
          "actual resource-cost ticket terminal and reclaimed");
    Check(result && query.completed && query.envelope.frame_stable && failure.empty() && !serialized.empty(),
          "actual window/cost provider, Finish and complete caller wire");
    const auto &out = query.observation;
    const auto &quote = out.base_resource_cost_quote;
    Check(out.available && out.draft_observed && out.current_window.present &&
          out.current_window.window == fixture->window.data() &&
          out.played_character_id == Fixture::actor_id && out.date_raw == Fixture::date &&
          out.capture_epoch == query.envelope.execution_stamp.pump_epoch && out.capture_epoch != 701,
          "actual visible window and owner-pump identity");
    Check(quote.base_resource_cost_vector_observed && quote.native_base_fee_slots_raw &&
          quote.draft_quote.available && quote.draft_quote.piety_cost_raw == fixture->price &&
          quote.draft_quote.piety_missing_signed_raw == fixture->missing &&
          quote.draft_quote.has_enough_piety == true &&
          quote.draft_quote.source_rite_id == Fixture::rite_id,
          "actual signed budget and quote pass through the new provider");
    std::array<std::int64_t, f::kRiteCreationBaseCostSlotCount> expected{};
    expected[f::kRiteCreationBasePietySlot] = fixture->price;
    Check(*quote.native_base_fee_slots_raw == expected &&
          !quote.actual_debit_observed && !quote.post_action_net_resource_change_observed &&
          fixture->arguments_correct && fixture->draft_calls == 6,
          "exact native base-fee slot initialization and only existing cost callbacks");
    std::ofstream(directory / "visible-base-fee.json") << serialized << '\n';
    std::cout << "PASS checks=" << checks << " cases=1 named_only=true actual_resource_cost_provider=true "
                 "actual_submit_owner_drain_finish_wait_reclaim=true actual_command_result=true "
                 "frozen_12_case_main_invoked=false frozen_generic_case_main_invoked=false live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
