#include "xar_bridge/religion_doctrine12002_catalogue_mailbox.hpp"

// Preserve the published fixture source and declarations. Only its Pump's
// existing primary assignment is redirected to the new production named slot.
#define permitted_executor permitted_executor_religion_doctrine_catalogue12002
#define main UnusedDoctrineCatalogueMatrixMain12002
#include "religion_doctrine12002_catalogue_mailbox_test.cpp"
#undef main
#undef permitted_executor

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "named packet output directory argument");
    const std::filesystem::path directory(argv[1]);
    Fixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = 53175816;
    {
      api::MainThreadQueryMailboxV1 mailbox{};
      Pump pump(fixture, mailbox);
      Check(mailbox.permitted_executor == nullptr, "primary permit remains unset");
      Check(mailbox.permitted_executor_religion_doctrine_catalogue12002 ==
            &c::ExecutePlayerReligionDoctrineCatalogueMailbox12002,
            "actual named permit identifies exact catalogue executor");
    }
    d::DoctrineCatalogue observed{};
    Check(Query(fixture, adapter, directory, "named-loaded-catalogue.json", observed) &&
          observed.available && observed.catalogue_complete && observed.rows.size() == 3 &&
          observed.rows[2].doctrine_key == Fixture::mod_key,
          "single actual named-slot loaded catalogue query");
    std::cout << "PASS checks=" << checks
              << " named_permit_only=true old_matrix_main_executed=false"
              << " actual_submit_drain_wait_reclaim=true actual_wrapper=true live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
