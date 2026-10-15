// Reuse the admitted .4 fixture memory/callbacks without running its broader
// Doctrine-knowledge cases. Only the two current-state production mailboxes run.
#define XAR_CURRENT_RELIGION_ACCEPTANCE_FIXTURE_ONLY
#include "ck3_12004_religion_bindings_mailbox_test.cpp"

int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "one output directory argument");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    BinderCases();
    Fixture memory;
    fixture_state = &memory;
    game::Ck3_12004AdapterBindings adapter_bindings{};
    adapter_bindings.core = Core(memory);
    auto adapter = game::CreateCk3_12004AdapterFromBindings(std::move(adapter_bindings));
    game::Snapshot frame{};
    Assert(adapter && game::ReadCk3_12002TimelineCoreSnapshot(*adapter, frame) &&
        frame.paused && frame.map_ready && frame.played_character_id == Fixture::actor_id,
        "actual .4 adapter/core admits the synthetic paused player frame");

    old::PlayerReligionDoctrinesMailboxContext12002 current{};
    current.bindings = Current(memory);
    WholeWire(memory, *adapter, frame, current, &old::RunPlayerReligionDoctrinesMailbox12002,
        directory, "current-doctrines.json", "ck3_12004_current_doctrines_v1");
    OwnerFields(current.observation, current);
    Assert(current.observation.current_rite.rows.size() == std::size_t{2} &&
        current.observation.faith_main_rite.rows.size() == std::size_t{1},
        "effective current and faith-main Doctrine rows remain separate");

    old::PlayerReligionTenetsMailboxContext12002 tenets{};
    const auto bindings = Tenets(memory);
    tenets.bindings = bindings.context;
    tenets.tenet_bindings = bindings.rows;
    tenets.comparison_bindings = bindings.comparison;
    tenets.knowledge_bindings = bindings.knowledge;
    const auto wire = WholeWire(memory, *adapter, frame, tenets,
        &old::RunPlayerReligionTenetsMailbox12002, directory,
        "tenets-current-only.json", "ck3_12004_tenet_rows_v1");
    OwnerFields(tenets.observation, tenets);
    TenetRows(tenets.observation);
    Assert(tenets.observation.current_rite->core_tenets.size() == std::size_t{1} &&
        tenets.observation.current_rite->core_tenets[0].key == "tenet_a" &&
        tenets.observation.effective_tenet_states[1].key == "tenet_b" &&
        tenets.observation.effective_tenet_states[1].current_rite_status == std::uint8_t{1},
        "a known tenet is preserved outside the current rite core collection");
    Assert(memory.extra_calls == 0U && memory.perks_calls == 0U &&
        memory.contains_calls == 0U && memory.target_status_calls == 0U &&
        wire.find("target_rite_tenet_comparison") == std::string::npos &&
        wire.find("player_tenet_knowledge_catalogue") == std::string::npos,
        "current-only acceptance does not invoke optional catalogue/target callbacks");
    std::cout << "PASS current_queries=2 checks=" << checks
        << " actual_adapter=true actual_core_reader=true actual_named_mailbox=true"
        << " actual_serializer=true actual_renderer=true actual_full_wire=true"
        << " synthetic_memory=true synthetic_callbacks=true broader_main_executed=false live=false\n";
    fixture_state = nullptr;
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
