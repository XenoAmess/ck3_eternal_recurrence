// Reuse frozen memory/owner helpers; the original matrix is never invoked.
#define main FrozenReform12CaseMainNotExecuted
#include "religion_reform12002_query_mailbox_test.cpp"
#undef main
#include "xar_bridge/religion_reform12002_group_mailbox.hpp"

namespace {
struct GroupBacking {
  Fixture base{};
  Bytes<0xB20> definition_b{}, definition_c{}, definition_d{};
  Bytes<0x160> group_a{}, group_c{};
  Bytes<0x48 * 2> slots{};
  std::array<void *, 2> a_sources{base.doctrine.data(), definition_b.data()};
  std::array<void *, 2> c_sources{definition_c.data(), definition_d.data()};
  GroupBacking() {
    Key(definition_b, "doctrine_b"); Key(definition_c, "doctrine_c"); Key(definition_d, "doctrine_d");
    Key(group_a, "group_a"); Key(group_c, "group_c");
    Put(base.doctrine, 0xB08, group_a.data()); Put(definition_b, 0xB08, group_a.data());
    Put(definition_c, 0xB08, group_c.data()); Put(definition_d, 0xB08, group_c.data());
    Array(group_a, f::kGroupDefinitionSourcesOffset, a_sources.data(), 2);
    Array(group_c, f::kGroupDefinitionSourcesOffset, c_sources.data(), 2);
    Put(slots, f::kChoiceDefinitionOffset, base.doctrine.data());
    Put(slots, f::kActualDraftSlotStride + f::kChoiceDefinitionOffset, definition_c.data());
    Array(base.window, f::kDraftSelectedSlotsOffset, slots.data(), 2);
    Put(base.window, 0x888, base.window.data()); Put(base.window, 0x890, group_a.data());
    Put(base.window, 0x898, base.doctrine.data()); Put(base.window, 0x8D8, std::int32_t{0});
    Array(base.window, 0x8C0, base.tenet_item.data(), 1);
    base.native_tenet = true;
  }
  void KnownEmpty() {
    Array(base.window, f::kDraftSelectedSlotsOffset, slots.data(), 0);
    Array(base.window, 0x8A8, base.doctrine_item.data(), 0);
    Array(base.window, 0x8C0, base.tenet_item.data(), 0);
    Array(base.window, f::kDraftTenetGroupArrayOffset, base.tenet_group.data(), 0);
    Put(base.window, 0x8D8, std::int32_t{-1});
    Put(base.window, 0x890, static_cast<void *>(nullptr));
    Put(base.window, 0x898, static_cast<void *>(nullptr));
  }
};

f::DraftGroupModel GroupQuery(GroupBacking &backing, FrameAdapter &adapter,
                             const std::filesystem::path &directory, const char *filename) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(backing.base, mailbox);
  mailbox.permitted_executor = &c::ExecutePlayerReligionDraftGroupsMailbox12002;
  c::PlayerReligionDraftGroupsMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(backing.base).choices;
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
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
  Check(drained, "actual group callback drained on fixture owning thread");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual group ticket terminal/reclaimed");
  Check(result && query.completed && query.envelope.frame_stable && failure.empty() && !serialized.empty(),
        "actual group reader / Finish / complete caller wire");
  Check(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
        query.observation.capture_epoch != 701, "group capture epoch is actual pump epoch");
  std::ofstream(directory / filename) << serialized << '\n';
  return query.observation;
}
} // namespace

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
    auto out = GroupQuery(*backing, adapter, directory, "visible-multi-slots.json");
    Check(out.available && out.draft_observed && out.category_materialized &&
          out.selected_slots.size() == 2 && out.selected_slots[0].selected_definition_key == "doctrine_a" &&
          out.selected_slots[1].selected_definition_key == "doctrine_c" &&
          out.selected_slots[0].group_source_definition_keys == std::vector<std::string>{"doctrine_a", "doctrine_b"} &&
          out.selected_slots[1].group_source_definition_keys == std::vector<std::string>{"doctrine_c", "doctrine_d"} &&
          out.current_group_key == "group_a" && out.current_category_slot == 0 &&
          out.current_doctrine_cache_count == 1 && out.current_tenet_source_count == 1 &&
          out.current_tenet_group_count == 1 && out.current_tenet_choices.size() == 1 &&
          out.current_tenet_choices[0].final_can_pick && out.current_tenet_gate_complete &&
          backing->base.arguments_correct, "actual distinct group sources / current materialized caches / native Tenet gate");
    Put(backing->base.handler, f::kDraftWindowFromHandlerOffset, static_cast<void *>(nullptr));
    out = GroupQuery(*backing, adapter, directory, "absent-window.json");
    Check(out.available && !out.draft_observed && out.selected_slots.empty() && !out.source_rite_id &&
          out.current_tenet_choices.empty() && !out.current_tenet_gate_complete,
          "known absent window stays observed without draft model");
    Put(backing->base.handler, f::kDraftWindowFromHandlerOffset, backing->base.window.data());
    backing->base.visible = false;
    const auto calls = backing->base.draft_calls;
    out = GroupQuery(*backing, adapter, directory, "hidden-window.json");
    Check(out.available && !out.draft_observed && out.selected_slots.empty() && !out.source_rite_id &&
          backing->base.draft_calls == calls, "hidden current window calls no Tenet / category helpers");
    backing->base.visible = true; backing->KnownEmpty();
    out = GroupQuery(*backing, adapter, directory, "known-empty.json");
    Check(out.available && out.draft_observed && out.selected_slots.empty() && out.current_tenet_choices.empty() &&
          out.current_doctrine_cache_count == 0 && out.current_tenet_source_count == 0 &&
          out.current_tenet_group_count == 0 && !out.category_materialized && out.current_category_slot == -1,
          "visible known empty selected slots/cache model stays distinct from absence");
    std::cout << "PASS checks=" << checks << " cases=4 actual_group_provider=true "
                 "actual_submit_owner_drain_finish_wait_reclaim=true actual_command_result=true "
                 "frozen_12_case_main_invoked=false dedicated_production_registration_tested=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
