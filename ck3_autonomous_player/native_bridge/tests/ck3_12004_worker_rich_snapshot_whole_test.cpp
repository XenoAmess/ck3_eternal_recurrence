// Source-only offline reproduction. Root owns compilation and execution.
// Synthetic current native DTOs; no CK3, hooks, target-process access, or future simulation.
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/state_snapshot_frame_v1.hpp"

#include <atomic>
#include <cstdio>
#include <exception>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

namespace {
namespace api = xar::ck3_11906;
namespace build = xar::ck3_12002;
namespace game = xar::game;

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}

game::ArmySnapshot MakeArmy(std::int32_t id, std::int32_t owner,
                            std::int32_t province, bool controllable) {
  game::ArmySnapshot army{};
  army.army_id = id;
  army.owner_character_id = owner;
  army.has_current_province = true;
  army.current_province_id = province;
  army.route_province_ids = {province + 1, province + 2, province + 3};
  army.route_read_status = game::ArmyRouteReadStatus::complete_nonempty;
  army.route_source_count = 3;
  army.move_target_observable = true;
  army.move_target_province_id = province + 3;
  army.army_state_code = 1;
  army.army_state = "synthetic-paused-current";
  army.controllable = controllable;
  return army;
}

game::Snapshot MakeRichSnapshot() {
  game::Snapshot frame{};
  frame.date_raw = 123456;
  frame.speed = 3;
  frame.paused = true;
  frame.player_id = 7;
  frame.map_ready = true;
  frame.has_played_character = true;
  frame.played_character_id = 29829;
  frame.played_character_alive = true;
  frame.played_character_stress_points = 21;
  frame.played_character_gold = {7654321, 100000};
  frame.played_character_prestige = {345678, 100000};
  frame.played_character_piety = {234567, 100000};
  frame.played_character_primary_spouse_id = 29830;
  frame.played_character_spouse_ids = {29830, 29831};
  frame.player_armies = {MakeArmy(1201, 29829, 900, true),
                         MakeArmy(1202, 29829, 901, true)};
  for (std::int32_t wi = 0; wi != 2; ++wi) {
    game::ActiveWarSnapshot war{};
    war.war_id = 4001 + wi;
    war.player_side = wi == 0 ? game::PlayerWarSide::attacker
                             : game::PlayerWarSide::defender;
    war.primary_opponent_character_id = 30800 + wi;
    war.player_is_primary_war_leader = true;
    war.targeted_title_ids = {5001 + wi * 10, 5002 + wi * 10};
    war.enemy_primary_default_raise_province_id = 950 + wi * 10;
    war.player_relative_war_score = 15 + wi;
    war.allied_armies = {MakeArmy(1301 + wi * 10, 29829, 920 + wi * 10, true),
                         MakeArmy(1302 + wi * 10, 29832, 921 + wi * 10, false)};
    war.enemy_armies = {MakeArmy(1401 + wi * 10, 30800 + wi, 950 + wi * 10, false),
                        MakeArmy(1402 + wi * 10, 30810 + wi, 951 + wi * 10, false)};
    for (std::int32_t pi = 0; pi != 2; ++pi) {
      game::WarObjectiveProvinceState province{};
      province.province_id = 900 + wi * 10 + pi;
      const auto unit = wi == 0 ? 1201 + pi : 1401 + wi * 10 + pi;
      const auto native_army = 6001 + wi * 10 + pi;
      auto &selection = province.current_besieging_army_selection;
      selection.observable = true;
      selection.native_carmy_id = native_army;
      selection.public_unit_id = unit;
      selection.controllable_observable = true;
      selection.controllable = wi == 0;
      province.occupation_observable = true;
      province.is_occupied = wi == 0;
      province.occupying_character_id = wi == 0 ? 29829 : -1;
      province.fort_level_observable = true;
      province.fort_level = 3 + pi;
      province.garrison_size_observable = true;
      province.garrison_size = 240 + wi * 10 + pi;
      province.besieging_strength_observable = true;
      province.besieging_strength = 720 + wi * 10 + pi;
      province.siege_observable = true;
      province.has_active_siege = true;
      province.siege_id = 8001 + wi * 10 + pi;
      province.besieging_army_id = unit;
      province.player_army_besieging = wi == 0;
      province.siege_progress_fraction = {25000 + pi * 1000, 100000};
      province.siege_current_work = {300000 + wi * 1000 + pi, 100000};
      province.siege_total_work = {1200000 + wi * 1000 + pi, 100000};
      province.siege_days_left_observable = true;
      province.siege_days_left = 30 + pi;
      province.siege_province_unit_occurrences_observable = true;
      for (std::int32_t oi = 0; oi != 2; ++oi) {
        game::SiegeProvinceUnitOccurrenceV1 occurrence{};
        occurrence.occurrence_index = oi;
        occurrence.public_unit_id = unit;
        occurrence.native_carmy_id = native_army;
        occurrence.eligible_observable = true;
        occurrence.eligible = true;
        occurrence.qualified_regiment_ids_observable = true;
        occurrence.qualified_regiment_ids = {7001 + wi * 100 + pi * 10 + oi,
                                            7101 + wi * 100 + pi * 10 + oi};
        province.siege_province_unit_occurrences.push_back(occurrence);
      }
      war.war_objective_province_ids.push_back(province.province_id);
      war.objective_province_states.push_back(province);
    }
    frame.active_wars.push_back(war);
  }
  return frame;
}

// Interface stub base copied only from ck3_12002_semantic_adapter_test.cpp:64-279.
// Its original constructor/descriptor are replaced; no original test is replayed.
class FixtureAdapter final : public game::GameAdapter {
public:
  const DWORD owner = GetCurrentThreadId();
  game::Snapshot frame{};
  mutable std::atomic<std::uint32_t> raw_reads{0};
  mutable std::atomic<std::uint32_t> semantic_calls{0};
  mutable std::atomic<std::uint32_t> wrong_owner{0};
  mutable std::atomic<DWORD> queue_thread{0};
  mutable std::atomic<std::int32_t> last_event_option{-1};
  mutable std::atomic<std::int32_t> last_army{-1};
  mutable std::atomic<std::int32_t> last_province{-1};
  mutable std::atomic<std::int32_t> last_family_subject{-1};
  bool reader_available = true;
  bool declarations_available = true;
  bool family_available = true;
  bool patch3 = false;

  FixtureAdapter() : frame(MakeRichSnapshot()) {}

  const game::AdapterDescriptor &descriptor() const noexcept override {
    return game::Ck3_12004AdapterDescriptor();
  }
  bool enabled() const noexcept override { return true; }
  void RecordSemantic() const noexcept {
    ++semantic_calls;
    if (GetCurrentThreadId() != owner) ++wrong_owner;
  }
  bool read_snapshot(game::Snapshot &output) const noexcept override {
    ++raw_reads;
    if (GetCurrentThreadId() != owner) {
      ++wrong_owner;
      output = {};
      return false;
    }
    output = reader_available ? frame : game::Snapshot{};
    return reader_available;
  }
  game::PauseSubmitResult submit_pause_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::PauseSubmitResult::submitted;
  }
  game::ResumeSubmitResult submit_resume_map(
      game::Snapshot *observed_snapshot = nullptr) const noexcept override {
    if (observed_snapshot != nullptr) *observed_snapshot = frame;
    queue_thread = GetCurrentThreadId();
    return game::ResumeSubmitResult::submitted;
  }
  bool submit_set_speed(std::int32_t speed) const noexcept override {
    queue_thread = GetCurrentThreadId();
    return speed == 4;
  }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override {
    queue_thread = GetCurrentThreadId();
    return {game::SaveCheckpointStatus::submitted, 123456};
  }
  game::SelectEventOptionResult submit_select_event_option(
      std::int32_t option) const noexcept override {
    RecordSemantic();
    last_event_option = option;
    return option < 0 || option >= frame.active_event_option_count
      ? game::SelectEventOptionResult::option_out_of_range
      : game::SelectEventOptionResult::submitted;
  }
  bool read_declarable_wars(
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return false;
    output.push_back({0x14000042, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return true;
  }
  game::ReadDeclarableWarsResult read_declarable_wars_for_target(
      std::int32_t target_id,
      std::vector<game::DeclarableWarSnapshot> &output) const noexcept override {
    RecordSemantic();
    output.clear();
    if (!declarations_available) return game::ReadDeclarableWarsResult::unavailable;
    if (target_id != 0x14000042) return game::ReadDeclarableWarsResult::target_not_found;
    output.push_back({target_id, 8, "fixture_claim", 3,
                      frame.played_character_id, {0x11000018, 0x12000019}});
    return game::ReadDeclarableWarsResult::available;
  }
  game::MoveArmyResult submit_move_army(
      std::int32_t army, std::int32_t province) const noexcept override {
    RecordSemantic();
    last_army = army;
    last_province = province;
    return army == frame.player_armies.front().army_id && province == 901
      ? game::MoveArmyResult::submitted : game::MoveArmyResult::validation_failed;
  }
  game::ReadArmyStrengthsResult read_army_strengths(
      std::vector<game::ArmyStrengthSnapshot> &output) const noexcept override {
    RecordSemantic();
    game::ArmyStrengthSnapshot row{};
    row.available = true;
    row.army_id = frame.player_armies.front().army_id;
    row.regiment_count = 2;
    row.current_soldiers = 734;
    row.maximum_soldiers = 1000;
    row.ai_base_power_raw = 123456789;
    output = {row};
    return game::ReadArmyStrengthsResult::available;
  }
  game::ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(
      std::vector<game::ArrangeMarriageChoice> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    output = {{frame.played_character_id, 0x15000011}};
    diagnostics = {};
    diagnostics.storage_capacity = 17;
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageChoicesResult::available;
  }
  game::ReadWarTerminationOptionsResult read_war_termination_options(
      std::int32_t war_id, game::WarTerminationOptionsSnapshot &output) const noexcept override {
    RecordSemantic();
    output = {};
    if (frame.active_wars.empty() || frame.active_wars.front().war_id != war_id)
      return game::ReadWarTerminationOptionsResult::war_not_found;
    output.war_id = war_id;
    output.player_relative_war_score = frame.active_wars.front().player_relative_war_score;
    return game::ReadWarTerminationOptionsResult::available;
  }
  game::ReadArrangeMarriageFamilyCandidatesResultV1
  read_arrange_marriage_family_candidates_v1(
      std::int32_t subject_id,
      std::vector<game::ArrangeMarriageFamilyCandidateV1> &output,
      game::ArrangeMarriageQueryDiagnostics &diagnostics) const noexcept override {
    RecordSemantic();
    last_family_subject = subject_id;
    output.clear();
    diagnostics = {};
    if (subject_id != 0x13000016)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::subject_not_found;
    diagnostics.storage_capacity = 17;
    diagnostics.slots_scanned = 2;
    if (!family_available)
      return game::ReadArrangeMarriageFamilyCandidatesResultV1::unavailable;
    game::ArrangeMarriageFamilyCandidateV1 row{};
    row.played_character_id = frame.played_character_id;
    row.subject_character_id = subject_id;
    row.candidate_character_id = 0x15000011;
    row.recipient_matchmaker_character_id = 0x14000042;
    row.recipient_ai_accept_raw = 2'500'000;
    row.recipient_answer_status_raw = 1;
    row.complete_can_send = true;
    row.recipient_answer_allows_send = true;
    row.heir_adult_measure_raw = std::int16_t{17};
    row.candidate_adult_measure_raw = std::int16_t{19};
    row.played_dynasty_id = 71;
    row.heir_dynasty_id = 71;
    row.candidate_dynasty_id = 72;
    row.realm_backed_actor_recipient = true;
    output.push_back(row);
    diagnostics.native_validate_true = 1;
    return game::ReadArrangeMarriageFamilyCandidatesResultV1::available;
  }

#define UNAVAILABLE_RESULT(Result, Name, Parameters) \
  game::Result Name Parameters const noexcept override { \
    RecordSemantic(); return game::Result::unavailable; }
  UNAVAILABLE_RESULT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction,
                     (game::PendingInteractionReply))
  UNAVAILABLE_RESULT(AcknowledgePendingInteractionResult, submit_acknowledge_pending_interaction,
                     (std::int32_t))
  UNAVAILABLE_RESULT(RaiseTroopsResult, submit_raise_troops_default, ())
  UNAVAILABLE_RESULT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  UNAVAILABLE_RESULT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  UNAVAILABLE_RESULT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  UNAVAILABLE_RESULT(StartAssaultResult, submit_start_assault, (std::int32_t))
  UNAVAILABLE_RESULT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  UNAVAILABLE_RESULT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  UNAVAILABLE_RESULT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  UNAVAILABLE_RESULT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  UNAVAILABLE_RESULT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  UNAVAILABLE_RESULT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  UNAVAILABLE_RESULT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
                     (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationTermsResult, read_war_termination_terms,
                     (std::int32_t, game::WarTerminationTermsSnapshot &))
  UNAVAILABLE_RESULT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms,
                     (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef UNAVAILABLE_RESULT
  game::PreviewMoveArmyResult preview_move_army(
      std::int32_t, std::int32_t) const noexcept override {
    RecordSemantic();
    return {};
  }
};

void MirrorStamp(api::MainThreadQueryMailboxV1 &mailbox,
                 const api::MainThreadExecutionStampV1 &stamp) {
  mailbox.observed_date_raw.store(stamp.date_raw);
  mailbox.observed_tls_initialized.store(stamp.tls_initialized);
  mailbox.observed_tls_main_thread_marker.store(stamp.tls_main_thread_marker);
  mailbox.observed_paused.store(stamp.paused);
  mailbox.observed_stamp_read_success.store(true);
}

void CheckExactRows(const game::Snapshot &actual, const game::Snapshot &expected) {
  Require(actual == expected, "full Snapshot equality mismatch");
  Require(actual.played_character_id == 29829 && actual.paused,
          "synthetic paused Robert scope mismatch");
  Require(actual.played_character_spouse_ids == expected.played_character_spouse_ids,
          "spouse vector mismatch");
  Require(actual.player_armies == expected.player_armies, "player Army rows mismatch");
  Require(actual.active_wars.size() == 2 && expected.active_wars.size() == 2,
          "two rich wars missing");
  for (std::size_t wi = 0; wi != 2; ++wi) {
    const auto &war = actual.active_wars[wi];
    const auto &wanted = expected.active_wars[wi];
    Require(war.war_id == wanted.war_id &&
            war.targeted_title_ids == wanted.targeted_title_ids &&
            war.war_objective_province_ids == wanted.war_objective_province_ids &&
            war.allied_armies == wanted.allied_armies &&
            war.enemy_armies == wanted.enemy_armies, "nested war vectors mismatch");
    Require(war.objective_province_states.size() == 2 &&
            wanted.objective_province_states.size() == 2, "two objectives missing");
    for (std::size_t pi = 0; pi != 2; ++pi) {
      const auto &province = war.objective_province_states[pi];
      const auto &want = wanted.objective_province_states[pi];
      const auto &selection = province.current_besieging_army_selection;
      const auto &want_selection = want.current_besieging_army_selection;
      Require(province == want, "exact objective row mismatch");
      Require(province.province_id == want.province_id &&
              province.garrison_size == want.garrison_size &&
              selection.observable == want_selection.observable &&
              selection.native_carmy_id == want_selection.native_carmy_id &&
              selection.public_unit_id == want_selection.public_unit_id &&
              selection.controllable_observable == want_selection.controllable_observable &&
              selection.controllable == want_selection.controllable,
              "objective scalar or current selection mismatch");
      Require(province.siege_province_unit_occurrences_observable &&
              province.siege_province_unit_occurrences.size() == 2,
              "existing nested siege occurrences missing");
      for (std::size_t oi = 0; oi != 2; ++oi) {
        const auto &occurrence = province.siege_province_unit_occurrences[oi];
        const auto &want_occurrence = want.siege_province_unit_occurrences[oi];
        Require(occurrence == want_occurrence &&
                occurrence.qualified_regiment_ids.size() == 2 &&
                occurrence.qualified_regiment_ids == want_occurrence.qualified_regiment_ids,
                "exact nested siege occurrence mismatch");
      }
    }
  }
}

struct Sample {
  game::Snapshot copied;
  std::string wire;
  DWORD worker_thread_id = 0;
};

Sample ReadWorkerSample(build::WorkerAdapter &proxy,
                        const game::Snapshot &expected, std::uint64_t revision,
                        DWORD owner_thread_id) {
  Sample result{};
  std::exception_ptr failure;
  std::thread worker([&] {
    try {
      result.worker_thread_id = GetCurrentThreadId();
      Require(result.worker_thread_id != owner_thread_id,
              "sample must read from a distinct std::thread");
      game::Snapshot observed{};
      Require(proxy.read_snapshot(observed), "production worker snapshot read failed");
      CheckExactRows(observed, expected); // Check actual production cache-to-output copy.
      result.copied = observed;
      CheckExactRows(result.copied, expected); // Check a second explicit owning copy.
      result.wire = xar::bridge::SerializeStateSnapshotFrameV1(result.copied, revision);
      Require(!result.wire.empty(), "production state_snapshot serializer returned empty");
    } catch (...) {
      failure = std::current_exception();
    }
  });
  worker.join();
  if (failure) std::rethrow_exception(failure);
  CheckExactRows(result.copied, expected);
  return result;
}

void WriteFile(const std::filesystem::path &path, const std::string &text) {
  std::ofstream stream(path, std::ios::binary | std::ios::trunc);
  Require(static_cast<bool>(stream), "wire output file could not open");
  stream << text << '\n';
  Require(static_cast<bool>(stream), "wire output file could not write");
}

void WriteContext(const std::filesystem::path &directory, const FixtureAdapter &native,
                  const char *status, std::uint32_t samples) {
  // Metadata only. Business Snapshot rows come exclusively from the production serializer.
  const std::string context =
      "{\"producer\":\"fixture-native-gameadapter-rich-snapshot-v1\","
      "\"frame_population\":\"synthetic-current-native-DTO-constructed-in-CPP\","
      "\"native_reader\":\"FixtureAdapter::read_snapshot\","
      "\"production_worker\":\"xar::ck3_12002::WorkerAdapter\","
      "\"production_observer\":\"xar::ck3_12002::ObserveAdapterSnapshot12002\","
      "\"production_serializer\":\"xar::bridge::SerializeStateSnapshotFrameV1\","
      "\"Game_executed\":false,\"worker_preparation_FIRST\":0,\"future_simulation\":false,"
      "\"execution_status\":\"" + std::string(status) +
      "\",\"samples\":" + std::to_string(samples) +
      ",\"raw_reads\":" + std::to_string(native.raw_reads.load()) +
      ",\"semantic_calls\":" + std::to_string(native.semantic_calls.load()) +
      ",\"wrong_owner\":" + std::to_string(native.wrong_owner.load()) + "}";
  WriteFile(directory / "NATIVE-CONTEXT.json", context);
}

int Reproduce(const std::filesystem::path &wire_directory) {
  Require(!std::filesystem::exists(wire_directory), "--wire-dir must be a fresh path");
  Require(std::filesystem::create_directories(wire_directory),
          "fresh wire directory could not be created");
  FixtureAdapter native;
  WriteContext(wire_directory, native, "started", 0);
  api::MainThreadQueryMailboxV1 mailbox{};
  build::WorkerAdapter proxy(native, mailbox); // Actual production constructor.
  api::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 1;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized = 1;
  stamp.tls_main_thread_marker = 1;
  stamp.date_raw = native.frame.date_raw;
  stamp.paused = native.frame.paused;
  MirrorStamp(mailbox, stamp);
  const game::Snapshot initial_expected = native.frame;
  Require(build::ObserveAdapterSnapshot12002(&proxy, stamp),
          "initial production Observe failed");
  const auto initial = ReadWorkerSample(proxy, initial_expected, 1, native.owner);
  Require(native.raw_reads.load() == 1 && native.semantic_calls.load() == 0 &&
          native.wrong_owner.load() == 0, "initial native counters mismatch");
  WriteFile(wire_directory / "initial.native-frame.json", initial.wire);
  WriteContext(wire_directory, native, "initial_sample_complete", 1);

  // A date change bypasses the production 250 ms cadence without sleeping.
  ++native.frame.date_raw;
  auto &changed = native.frame.active_wars[1].objective_province_states[1];
  changed.garrison_size += 13; // Existing scalar after the inserted DTO.
  changed.current_besieging_army_selection.controllable =
      !changed.current_besieging_army_selection.controllable;
  changed.siege_province_unit_occurrences[1].qualified_regiment_ids[1] += 17;
  ++stamp.pump_epoch;
  stamp.date_raw = native.frame.date_raw;
  MirrorStamp(mailbox, stamp);
  Require(native.frame != initial_expected, "updated frame equality must differ");
  Require(build::ObserveAdapterSnapshot12002(&proxy, stamp),
          "updated production Observe failed");
  const auto updated = ReadWorkerSample(proxy, native.frame, 2, native.owner);
  Require(updated.copied.date_raw == initial.copied.date_raw + 1,
          "second frame date increment missing");
  Require(initial.copied != updated.copied, "worker copies must retain two distinct samples");
  CheckExactRows(initial.copied, initial_expected); // Original owned copy survives replacement.
  Require(native.raw_reads.load() == 2 && native.semantic_calls.load() == 0 &&
          native.wrong_owner.load() == 0, "final native counters must be raw_reads=2/semantic_calls=0");
  WriteFile(wire_directory / "updated.native-frame.json", updated.wire);
  WriteContext(wire_directory, native, "passed", 2);
  std::printf("synthetic-current-native-DTO WorkerAdapter reproduction passed: raw_reads=2 semantic_calls=0 Game=0 worker_preparation_FIRST=0\n");
  return 0;
}
} // namespace

int main(int argc, char **argv) {
  try {
    if (argc != 3 || std::string_view(argv[1]) != "--wire-dir") {
      std::fprintf(stderr, "usage: worker-rich-snapshot-repro --wire-dir FRESH_DIRECTORY\n");
      return 2;
    }
    return Reproduce(std::filesystem::path(argv[2]));
  } catch (const std::exception &error) {
    std::fprintf(stderr, "worker rich Snapshot reproduction failed: %s\n", error.what());
    return 1;
  }
}
