#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>

namespace c = xar::ck3_12002;
namespace county = xar::ck3_12003::religion::county_conversion;
namespace {
int checks = 0;
int unused_adapter_calls = 0;
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}

county::Observation ReplayFrozenLeaf() {
  // These values come from the frozen actual reader/serializer GREEN output
  // real-current-conversion.json (SHA 5c6b9b5bd10df6a3dd85845045e05e1bf09ec15f56d3748b67b695615fd84a0f).
  // No native reader or seven-case fixture is rerun in this full-wire fixture.
  county::Observation v{};
  v.available = true;
  v.failure = county::Failure::none;
  v.capture_epoch = 102;
  v.date_raw = 53230008;
  v.owner_character_id = 50331652;
  v.owner_rite_id = 152;
  v.position_present = true;
  v.incumbent_character_id = 100663301;
  v.incumbent_rite_id = 152;
  v.active_task_id = 33554438;
  v.current_task_key = "task_conversion";
  v.current_task_type = 1;
  v.current_progress_kind = 1;
  v.current_task_frozen = true;
  v.current_percentage_progress_raw = 8750000;
  v.current_conversion_monthly_rate_raw = 777000;
  v.current_target_province_id = 1;
  v.current_target_county_title_id = 67108866;
  v.current_target_county_rite_id = 0;
  v.native_task_shown = true;
  v.native_task_valid = true;
  v.candidate_collection_evaluated = true;
  v.candidate_collection_complete = true;
  v.candidates = {
      {2, 2, 16777219, 33554439, std::uint32_t{2197815299U}, false, true, 350000},
      {1, 1, 67108866, 50331652, std::uint32_t{0}, true, true, 125000},
      {0, 3, 100663297, 33554439, std::uint32_t{153}, false, true, 500000},
  };
  return v;
}
} // namespace

// Standalone link seams for adapter construction/unwrap paths outside this
// serializer fixture. The actual production serializers/renderers stay linked;
// the focused case verifies none of these seams is called.
namespace xar::game {
Ck3_12002AdapterBindings BindCk3_12002AdapterImage(std::uintptr_t, std::string_view) noexcept {
  ++unused_adapter_calls;
  return {};
}
const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept {
  ++unused_adapter_calls;
  static const AdapterDescriptor descriptor{};
  return descriptor;
}
std::unique_ptr<GameAdapter> CreateCk3_12003AdapterFromBindings(Ck3_12003AdapterBindings) noexcept {
  ++unused_adapter_calls;
  return {};
}
} // namespace xar::game
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept {
  ++unused_adapter_calls;
  return adapter;
}
} // namespace xar::ck3_12002

int main(int argc, char **argv) {
  try {
    Check(argc == 3, "frozen leaf and output directory arguments");
    std::ifstream input(argv[1], std::ios::binary);
    std::string frozen((std::istreambuf_iterator<char>(input)), {});
    while (!frozen.empty() && (frozen.back() == '\n' || frozen.back() == '\r')) frozen.pop_back();
    const auto replayed = ReplayFrozenLeaf();
    Check(county::SerializeCountyConversion12003(replayed) == frozen,
          "production leaf serializer exactly reproduces prior actual GREEN wire");

    c::PlayerClergyAppointmentMailboxContext12002 query{};
    query.completed = true;
    query.envelope.frame_stable = true;
    query.envelope.expected_snapshot_revision = 701;
    auto &frame = query.envelope.expected_snapshot;
    frame.date_raw = replayed.date_raw;
    frame.played_character_id = replayed.owner_character_id;
    frame.paused = frame.map_ready = true;
    frame.has_played_character = frame.played_character_alive = true;
    query.request.candidate_character_id = *replayed.incumbent_character_id;
    auto &clergy = query.observation;
    clergy.available = true;
    clergy.failure = c::religion::clergy::Failure::none;
    clergy.capture_epoch = replayed.capture_epoch;
    clergy.date_raw = replayed.date_raw;
    clergy.owner_character_id = replayed.owner_character_id;
    clergy.candidate_character_id = query.request.candidate_character_id;
    clergy.position_present = true;
    clergy.active_task_id = replayed.active_task_id;
    clergy.incumbent_character_id = replayed.incumbent_character_id;
    clergy.candidate_court_owner_id = replayed.owner_character_id;
    clergy.owner_rite_id = replayed.owner_rite_id;
    clergy.candidate_rite_id = replayed.incumbent_rite_id;
    clergy.candidate_is_incumbent = true;
    clergy.candidate_matches_owner_context = true;
    clergy.native_valid_position = true;
    clergy.native_valid_character = true;
    clergy.native_can_reassign = false;
    clergy.native_can_fire = false;
    query.county_conversion_environment = county::BindCountyConversionImage12003(
        0x140000000, xar::ck3_12003::kExecutableSha256);
    query.county_conversion_observation = replayed;

    constexpr std::string_view request_id = "g2-read-00000000000000000000000000003203";
    auto serialized = c::SerializePlayerClergyAppointmentResult12002(query, request_id);
    Check(!serialized.empty() && serialized.find("\"county_conversion\":" + frozen) != std::string::npos,
          "actual production full command-result contains exact prior leaf");
    const xar::game::AdapterDescriptor actual_descriptor{
        xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
        xar::ck3_12003::kExecutableSha256, "county-conversion-full-wire-fixture", {}};
    serialized = xar::game::RenderCrozierBuildIdentity(std::move(serialized), actual_descriptor);
    Check(serialized.find("\"game_version\":\"1.20.0.2\"") == std::string::npos &&
          serialized.find(c::kExecutableSha256) == std::string::npos &&
          serialized.find("ck3-1.20.0.3-native-player-clergy-appointment-v1") != std::string::npos,
          "actual production .3 renderer translates outer and legacy clergy identities");
    Check(serialized.find("\"county_conversion\":" + frozen) != std::string::npos &&
          query.observation.capture_epoch != query.envelope.expected_snapshot_revision,
          "renderer preserves county exact bytes and independent public revision");

    const auto directory = std::filesystem::path(argv[2]);
    std::ofstream(directory / "county-conversion-clergy-full-command-result.json", std::ios::binary)
        << serialized << '\n';
    query.county_conversion_environment.reset();
    const auto legacy = c::SerializePlayerClergyAppointmentResult12002(query, request_id);
    Check(legacy.find("\"county_conversion\"") == std::string::npos &&
          legacy.find("\"game_version\":\"1.20.0.2\"") != std::string::npos,
          "legacy .2 context omits new leaf and retains original build");
    Check(unused_adapter_calls == 0, "fixture link-only adapter seams are never invoked");
    std::cout << "PASS focused_cases=1 checks=" << checks
              << " actual_full_serializer=true actual_crozier_renderer=true leaf_reader_rerun=false live=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
