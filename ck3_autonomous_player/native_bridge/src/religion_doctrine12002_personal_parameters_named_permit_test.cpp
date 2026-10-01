#include "xar_bridge/religion_doctrine12002_personal_parameters_mailbox.hpp"

// The runner copies the frozen fixture bytes and renames only its final main.
// Its nested provider-main alias and all original Query helpers stay intact.
#define permitted_executor permitted_executor_religion_personal_parameters12002
#include "religion_doctrine12002_personal_parameters_named_permit_fixture.inc"
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
      Assert(mailbox.permitted_executor_religion_personal_parameters12002 ==
             &c::ExecutePlayerReligionPersonalParametersMailbox12002,
             "actual named permit identifies exact personal parameter executor");
    }
    d::PersonalParameterContext observation{};
    Assert(Query(fixture, adapter, directory, "named-current-personal-flags.json", observation) &&
           observation.available && observation.has_character_extension &&
           observation.capture_epoch > 0U && observation.date_raw == adapter.frame.date_raw &&
           observation.played_character_id == static_cast<std::uint32_t>(Fixture::character_id) &&
           observation.personal_tenet_keys == std::vector<std::string>{"tenet_guest", "tenet_adaptive"} &&
           observation.parameters.size() == 4 &&
           d::LookupPersonalParameter12002(observation, fixture.names[1]).value == true &&
           d::LookupPersonalParameter12002(observation, fixture.names[2]).value == true &&
           d::LookupPersonalParameter12002(observation, fixture.names[0]).state == d::PersonalParameterLookupState::Value &&
           d::LookupPersonalParameter12002(observation, fixture.names[0]).value == false &&
           d::LookupPersonalParameter12002(observation, fixture.names[3]).value == false,
           "single actual named query preserves full personal registry and known true/false in played scope");
    std::cout << "PASS checks=" << mailbox_checks
              << " named_permit_only=true old_provider17_executed=false old_mailbox30_executed=false"
              << " actual_submit_drain_wait_reclaim=true actual_personal_parameters=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
