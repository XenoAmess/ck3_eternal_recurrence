// Frozen owner/memory helpers only; the original twelve-case main is never run.
#define main FrozenReform12CaseMainNotExecuted
#include "religion_reform12002_query_mailbox_test.cpp"
#undef main
#include "xar_bridge/religion_reform12002_fullchoices_mailbox.hpp"
#include "xar_bridge/religion_reform12002_group_model.hpp"

namespace {
struct FullChoiceBacking {
  Fixture base{};
  std::array<Bytes<0xB20>, 10> definitions{};
  std::array<Bytes<0x160>, 3> groups{};
  Bytes<0x48 * 4> selected_slots{};
  std::array<void *, 6> a_sources{};
  std::array<void *, 3> g_sources{};
  unsigned trigger_reads = 0, knowledge_reads = 0, perk_reads = 0;
  FullChoiceBacking() {
    constexpr std::array<const char *, 10> keys{
        "doctrine_a", "doctrine_b", "doctrine_c", "doctrine_d", "doctrine_e",
        "doctrine_f", "doctrine_g", "doctrine_h", "doctrine_i", "doctrine_j"};
    Key(groups[0], "group_a"); Key(groups[1], "group_g"); Key(groups[2], "group_zero");
    for (std::size_t index = 0; index < definitions.size(); ++index) {
      auto &definition = definitions[index];
      Key(definition, keys[index]);
      Put(definition, 0xB08, groups[index < 6 ? 0 : index < 9 ? 1 : 2].data());
      Put(definition, 0x1B8, index != 2);
      Put(definition, 0xE8, index != 3);
      Put(definition, 0xB10, index != 4 && index != 7 && index != 8);
    }
    for (std::size_t index = 0; index < a_sources.size(); ++index) a_sources[index] = definitions[index].data();
    for (std::size_t index = 0; index < g_sources.size(); ++index) g_sources[index] = definitions[index + 6].data();
    Array(groups[0], f::kGroupDefinitionSourcesOffset, a_sources.data(), 6);
    Array(groups[1], f::kGroupDefinitionSourcesOffset, g_sources.data(), 3);
    Array(groups[2], f::kGroupDefinitionSourcesOffset, static_cast<void *>(nullptr), 0);
    constexpr std::array<std::size_t, 4> selected{0, 1, 6, 9};
    for (std::size_t index = 0; index < selected.size(); ++index)
      Put(selected_slots, index * f::kActualDraftSlotStride + f::kChoiceDefinitionOffset,
          definitions[selected[index]].data());
    Array(base.window, f::kDraftSelectedSlotsOffset, selected_slots.data(), 4);
    // Full source choices require no constructed or materialized popup rows.
    Put(base.window, 0x8D8, std::int32_t{-1});
    Array(base.window, 0x8A8, static_cast<void *>(nullptr), 0);
    Array(base.window, f::kDraftTenetGroupArrayOffset, static_cast<void *>(nullptr), 0);
  }
};
FullChoiceBacking *full_choice_backing = nullptr;
bool FullSourceTrigger(const void *trigger, const void *scope) {
  auto &backing = *full_choice_backing;
  ++backing.trigger_reads;
  backing.base.arguments_correct &= scope == backing.base.window.data() + 0xD0;
  for (const auto &definition : backing.definitions) {
    if (trigger == definition.data() + 0x1B8) return Get<bool>(definition.data(), 0x1B8);
    if (trigger == definition.data() + 0xE8) return Get<bool>(definition.data(), 0xE8);
  }
  backing.base.arguments_correct = false;
  return false;
}
bool FullSourceKnowledge(void *actor, const void *definition) {
  auto &backing = *full_choice_backing;
  ++backing.knowledge_reads;
  backing.base.arguments_correct &= actor == backing.base.actor.data();
  for (const auto &candidate : backing.definitions)
    if (definition == candidate.data()) return Get<bool>(definition, 0xB10);
  backing.base.arguments_correct = false;
  return false;
}
bool FullSourceProphet(void *actor, const void *perk) {
  ++full_choice_backing->perk_reads;
  return HasPerk(actor, perk);
}

f::DraftFullDoctrineChoices FullChoicesQuery(FullChoiceBacking &backing, FrameAdapter &adapter,
                                            const std::filesystem::path &directory) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(backing.base, mailbox);
  mailbox.permitted_executor = &c::ExecutePlayerReligionDraftDoctrineChoicesMailbox12002;
  c::PlayerReligionDraftDoctrineChoicesMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(backing.base).choices;
  query.bindings.evaluate_trigger = &FullSourceTrigger;
  query.bindings.knows_doctrine = &FullSourceKnowledge;
  query.bindings.has_perk = &FullSourceProphet;
  full_choice_backing = &backing;
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
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
  Check(drained, "actual full Doctrine callback drained on fixture owning thread");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual full Doctrine ticket terminal/reclaimed");
  Check(result && query.completed && query.envelope.frame_stable && failure.empty() && !serialized.empty(),
        "actual reader / Finish / complete caller wire");
  Check(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
        query.observation.capture_epoch != 701, "full choices capture epoch is actual owner pump epoch");
  std::ofstream(directory / "visible-four-slots.json") << serialized << '\n';
  return query.observation;
}
} // namespace

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
    const auto out = FullChoicesQuery(*backing, adapter, directory);
    Check(out.available && out.draft_observed && out.doctrine_gates_complete &&
          out.played_character_id == Fixture::actor_id && out.date_raw == Fixture::date &&
          out.source_rite_id == Fixture::rite_id && out.slots.size() == 4 &&
          out.slots[0].sources.size() == 6 && out.slots[1].sources.size() == 6 &&
          out.slots[2].sources.size() == 3 && out.slots[3].sources.empty() &&
          out.slots[3].group_key == "group_zero", "actual four 48-byte slots / fifteen group-local sources / zero-source group");
    const auto &first = out.slots[0].sources;
    Check(first[0].currently_selected && first[0].final_selectable &&
          first[1].duplicate_excluded && !first[1].passed_shown.has_value() && !first[1].final_selectable &&
          first[2].passed_shown == false && first[2].native_can_pick == false && !first[2].native_knows_doctrine.has_value() &&
          first[3].passed_shown == true && first[3].native_can_pick == false &&
          first[4].native_knows_doctrine == false && first[4].native_has_prophet == false && !first[4].final_selectable &&
          first[5].final_selectable && out.slots[1].sources[0].duplicate_excluded &&
          out.slots[1].sources[1].currently_selected && out.slots[1].sources[1].final_selectable,
          "actual duplicate / ShouldDisplay false / native CanPick false / knowledge and Prophet false");
    unsigned selectable = 0;
    for (const auto &slot : out.slots) for (const auto &row : slot.sources) if (row.final_selectable) ++selectable;
    Check(selectable == 5 && backing->trigger_reads == 24 && backing->knowledge_reads == 9 &&
          backing->perk_reads == 4 && backing->base.draft_calls == 4 && backing->base.arguments_correct,
          "actual gate short-circuits / argument identities / five final selectable rows / no popup or Tenet helper");
    std::cout << "PASS checks=" << checks << " cases=1 actual_fullchoices_provider=true "
                 "actual_submit_owner_drain_finish_wait_reclaim=true actual_command_result=true "
                 "frozen_12_case_main_invoked=false provider_matrix_repeated=false dedicated_production_registration_tested=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
