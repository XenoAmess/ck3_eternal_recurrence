#include "xar_bridge/religion_doctrine12002_numeric_mailbox.hpp"

// The runner emits an exact byte copy of the frozen combined fixture with only
// the final main renamed. Its nested cache-main macro stays intact.
// Only the Pump's existing primary assignment maps to the production named slot.
#define permitted_executor permitted_executor_religion_numeric_special_parameters12002
#include "religion_doctrine12002_numeric_named_permit_fixture.inc"
#undef permitted_executor

int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "named packet output directory argument");
    const std::filesystem::path directory(argv[1]);
    Fixture fixture;
    FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id;
    adapter.frame.date_raw = Get<std::int32_t>(fixture.state.data(), 8);
    {
      api::MainThreadQueryMailboxV1 mailbox{};
      Pump pump(fixture, mailbox);
      Assert(mailbox.permitted_executor == nullptr, "primary permit remains unset");
      Assert(mailbox.permitted_executor_religion_numeric_special_parameters12002 ==
             &c::ExecutePlayerReligionNumericSpecialParametersMailbox12002,
             "actual named permit identifies exact numeric executor");
    }
    d::NumericSpecialContext observation{};
    d::FaithNumericFinalContext final{};
    Assert(Query(fixture, adapter, directory, "named-current-versus-main.json", observation, final) &&
           observation.available && final.available && threshold_calls == 2 &&
           observation.current_rite.has_value() && observation.faith_main_rite.has_value() &&
           observation.current_rite->rite_id == 0U && observation.faith_id == Fixture::faith_id &&
           observation.faith_main_rite->rite_id == Fixture::main_id &&
           final.current_rite_id == observation.current_rite->rite_id &&
           final.faith_id == observation.faith_id && final.main_rite_id == observation.faith_main_rite->rite_id &&
           final.capture_epoch == observation.capture_epoch && final.date_raw == observation.date_raw &&
           final.played_character_id == observation.played_character_id &&
           final.main_rite_adjustment_raw == 500000 && final.native_define_raw == 2500000 &&
           final.final_heresy_threshold_raw == 3000000,
           "single actual named query reports same-scope current/main cache and native final30");
    std::cout << "PASS checks=" << mailbox_checks
              << " named_permit_only=true old_numeric15_executed=false old_final10_executed=false"
              << " old_mailbox39_executed=false old_combined31_executed=false"
              << " actual_submit_drain_wait_reclaim=true actual_faith_numeric_final=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
