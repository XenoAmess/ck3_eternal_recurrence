#include "xar_bridge/player_lifestyle_window_candidates_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <string_view>

namespace {

namespace game = xar::game;
namespace ck3 = xar::ck3_11906;

constexpr std::uintptr_t kModule = 0x140000000ULL;
constexpr std::uint32_t kPlayer = 0x8100002AU;

template <std::size_t Size>
void Fixed(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < Size);
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

game::PlayerLifestyleWindowStableKeyV1 Key(std::string_view value) {
  game::PlayerLifestyleWindowStableKeyV1 output{};
  assert(ck3::AssignPlayerLifestyleWindowStableKeyV1(value, output));
  return output;
}

struct Fixture {
  ck3::PlayerLifestyleWindowFrameV1 before{};
  ck3::PlayerLifestyleWindowFrameV1 after{};
  ck3::PlayerLifestyleWindowSourceSampleV1 first{};
  ck3::PlayerLifestyleWindowSourceSampleV1 second{};
  ck3::PlayerLifestyleWindowSourceReadResultV1 first_result =
      ck3::PlayerLifestyleWindowSourceReadResultV1::success;
  ck3::PlayerLifestyleWindowSourceReadResultV1 second_result =
      ck3::PlayerLifestyleWindowSourceReadResultV1::success;
  bool main_thread = true;
  bool fail_frame = false;
  std::uint32_t frame_calls = 0;
  std::uint32_t source_calls = 0;
  std::uintptr_t observed_module = 0;
  std::uint32_t observed_player = 0xFFFFFFFFU;
};

bool Capture(void *context,
             ck3::PlayerLifestyleWindowFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_calls;
  if (fixture.fail_frame) return false;
  output = fixture.frame_calls == 1 ? fixture.before : fixture.after;
  return true;
}

bool IsMain(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

ck3::PlayerLifestyleWindowSourceReadResultV1 ReadSource(
    void *context, std::uintptr_t module_base,
    std::uint32_t played_character_id,
    ck3::PlayerLifestyleWindowSourceSampleV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  fixture.observed_module = module_base;
  fixture.observed_player = played_character_id;
  ++fixture.source_calls;
  if (fixture.source_calls == 1) {
    output = fixture.first;
    return fixture.first_result;
  }
  output = fixture.second;
  return fixture.second_result;
}

ck3::PlayerLifestyleWindowCandidatesEnvironmentV1 Environment() {
  return {true, ck3::kPlayerLifestyleWindowCandidatesExecutableSha256V1,
          kModule, true};
}

ck3::PlayerLifestyleWindowCandidatesAccessV1 Access(Fixture &fixture) {
  return {&fixture, &Capture, &IsMain, &ReadSource};
}

ck3::PlayerLifestyleWindowCandidatesRequestV1 Request() {
  return {"life4-window-fixture-001", 709, 9017, 54'333'000, kPlayer};
}

ck3::PlayerLifestyleWindowFocusSourceRowV1 Focus(
    std::uintptr_t pointer, std::string_view key,
    std::string_view lifestyle, bool can_select) {
  ck3::PlayerLifestyleWindowFocusSourceRowV1 output{};
  output.definition = pointer;
  output.key = Key(key);
  output.lifestyle_key = Key(lifestyle);
  output.pointer_in_captured_focus_span = true;
  output.stable_key_round_trip = true;
  output.final_evaluator_invoked = true;
  output.can_select = can_select;
  return output;
}

ck3::PlayerLifestyleWindowPerkSourceRowV1 Perk(
    std::uintptr_t pointer, std::string_view key,
    std::string_view lifestyle, bool can_select,
    bool can_select_ignore_cost) {
  ck3::PlayerLifestyleWindowPerkSourceRowV1 output{};
  output.definition = pointer;
  output.key = Key(key);
  output.lifestyle_key = Key(lifestyle);
  output.pointer_in_exact_perk_database = true;
  output.stable_key_round_trip = true;
  output.final_evaluator_invoked = true;
  output.ignore_cost_evaluator_invoked = true;
  output.can_select = can_select;
  output.can_select_ignore_cost = can_select_ignore_cost;
  return output;
}

void FillOwner(ck3::PlayerLifestyleWindowSourceSampleV1 &sample,
               std::uint64_t serial) {
  sample.root_acquisition_serial = serial;
  sample.root = 0x50000000;
  sample.idler_base = 0x50001000;
  sample.idler_gfx = 0x50001100;
  sample.idler_exact_rtti_cast = true;
  sample.handler = 0x50002000;
  sample.handler_vtable = kModule + ck3::kLifestyleWindowHandlerVtableRvaV1;
  sample.window = 0x50003000;
  sample.window_primary_vtable =
      kModule + ck3::kLifestyleWindowPrimaryVtableRvaV1;
  sample.window_secondary_vtable =
      kModule + ck3::kLifestyleWindowSecondaryVtableRvaV1;
  sample.window_owner_round_trip = sample.handler;
  sample.bound_character_id = kPlayer;
  sample.character_storage_round_trip = true;

  sample.lifestyles = {0x50004000, 8, 5,
                       ck3::kLifestyleWindowPointerSpanElementBytesV1, true};
  sample.perk_trees = {0x50005000, 4, 3,
                       ck3::kLifestyleWindowPerkTreeRowBytesV1, true};
  sample.focuses = {0x50006000, 4, 2,
                    ck3::kLifestyleWindowPointerSpanElementBytesV1, true};
  sample.perk_database_fully_materialized = true;
  sample.focus_count = 2;
  sample.focus_rows[0] = Focus(
      0x50006100, "stewardship_wealth_focus", "stewardship_lifestyle",
      true);
  sample.focus_rows[1] = Focus(
      0x50006108, "stewardship_domain_focus", "stewardship_lifestyle",
      false);
  sample.perk_count = 2;
  sample.perk_rows[0] = Perk(
      0x60000100, "tax_man_perk", "stewardship_lifestyle", false, true);
  sample.perk_rows[1] = Perk(
      0x60000200, "heregeld_perk", "stewardship_lifestyle", true, true);
}

std::unique_ptr<Fixture> Base() {
  auto fixture = std::make_unique<Fixture>();
  Fixed(fixture->before.snapshot_id, "life4-window-fixture-001");
  fixture->before.public_revision = 709;
  fixture->before.native_revision = 9017;
  fixture->before.proof_epoch = 29;
  fixture->before.date_raw = 54'333'000;
  fixture->before.paused = true;
  fixture->before.map_ready = true;
  fixture->before.has_played_character = true;
  fixture->before.played_character_alive = true;
  fixture->before.played_character_id = kPlayer;
  fixture->before.played_character = 0x70000000;
  fixture->before.played_character_identity_round_trip = true;
  fixture->after = fixture->before;
  FillOwner(fixture->first, 101);
  fixture->second = fixture->first;
  fixture->second.root_acquisition_serial = 102;
  return fixture;
}

void RequireUnavailable(
    Fixture &fixture, game::PlayerLifestyleWindowCandidatesFailureV1 reason) {
  game::PlayerLifestyleWindowCandidatesV1 output{};
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             Environment(), Access(fixture), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::unavailable);
  assert(output.status ==
         game::PlayerLifestyleWindowCandidatesStatusV1::unavailable);
  assert(output.unavailable_reason == reason);
  assert(output.player_character_id == 0xFFFFFFFFU);
  assert(output.focus_status ==
         game::PlayerLifestyleWindowCollectionStatusV1::unavailable);
  assert(output.perk_status ==
         game::PlayerLifestyleWindowCollectionStatusV1::unavailable);
  assert(output.focus_count == 0 && output.perk_count == 0);
  assert(!output.readiness.owner_path_ready &&
         !output.readiness.same_frame_ready);
}

void TestAvailableStableCandidates() {
  auto fixture = Base();
  game::PlayerLifestyleWindowCandidatesV1 output{};
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             Environment(), Access(*fixture), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::available);
  assert(output.status ==
         game::PlayerLifestyleWindowCandidatesStatusV1::available);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleWindowCandidatesFailureV1::none);
  assert(output.player_character_id == kPlayer);
  assert(output.focus_status ==
         game::PlayerLifestyleWindowCollectionStatusV1::available);
  assert(output.perk_status ==
         game::PlayerLifestyleWindowCollectionStatusV1::available);
  assert(output.focus_count == 2 && output.perk_count == 2);
  assert(ck3::PlayerLifestyleWindowStableKeyViewV1(
             output.focuses[0].key) == "stewardship_domain_focus");
  assert(!output.focuses[0].can_select);
  assert(ck3::PlayerLifestyleWindowStableKeyViewV1(
             output.perks[0].key) == "heregeld_perk");
  assert(output.perks[0].can_select &&
         output.perks[0].can_select_ignore_cost);
  assert(!output.perks[1].can_select &&
         output.perks[1].can_select_ignore_cost);
  assert(output.readiness.owner_path_ready &&
         output.readiness.bound_player_ready &&
         output.readiness.containers_ready &&
         output.readiness.focus_candidates_ready &&
         output.readiness.perk_candidates_ready &&
         output.readiness.final_legality_ready &&
         output.readiness.same_frame_ready);
  assert(fixture->frame_calls == 2 && fixture->source_calls == 2);
  assert(fixture->observed_module == kModule &&
         fixture->observed_player == kPlayer);
}

void TestKnownEmptyIsAvailable() {
  auto fixture = Base();
  for (auto *sample : {&fixture->first, &fixture->second}) {
    sample->focuses.data = 0;
    sample->focuses.count = 0;
    sample->focuses.complete_range_readable = false;
    sample->focus_count = 0;
    sample->perk_count = 0;
  }
  game::PlayerLifestyleWindowCandidatesV1 output{};
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             Environment(), Access(*fixture), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::available);
  assert(output.focus_status ==
         game::PlayerLifestyleWindowCollectionStatusV1::known_empty);
  assert(output.perk_status ==
         game::PlayerLifestyleWindowCollectionStatusV1::known_empty);
  assert(output.focus_count == 0 && output.perk_count == 0);
  assert(output.readiness.same_frame_ready);
}

void TestTypedUnboundAndOwnerFailures() {
  auto unbound = Base();
  unbound->first.bound_character_id ^= 1U;
  RequireUnavailable(
      *unbound,
      game::PlayerLifestyleWindowCandidatesFailureV1::
          lifestyle_window_unbound_or_stale);

  auto stale_round_trip = Base();
  stale_round_trip->first.character_storage_round_trip = false;
  RequireUnavailable(
      *stale_round_trip,
      game::PlayerLifestyleWindowCandidatesFailureV1::
          lifestyle_window_unbound_or_stale);

  auto wrong_owner = Base();
  ++wrong_owner->first.window_primary_vtable;
  RequireUnavailable(
      *wrong_owner,
      game::PlayerLifestyleWindowCandidatesFailureV1::owner_path_invalid);

  auto missing_owner = Base();
  missing_owner->first_result =
      ck3::PlayerLifestyleWindowSourceReadResultV1::owner_path_unavailable;
  RequireUnavailable(
      *missing_owner,
      game::PlayerLifestyleWindowCandidatesFailureV1::owner_path_unavailable);
}

void TestContainerMaterializationAndCandidateFailures() {
  auto container = Base();
  container->first.focuses.count = 5;
  RequireUnavailable(
      *container,
      game::PlayerLifestyleWindowCandidatesFailureV1::invalid_container);

  auto materialization = Base();
  materialization->first.perk_database_fully_materialized = false;
  RequireUnavailable(
      *materialization,
      game::PlayerLifestyleWindowCandidatesFailureV1::
          materialization_unavailable);

  auto provenance = Base();
  provenance->first.perk_rows[0].pointer_in_exact_perk_database = false;
  RequireUnavailable(
      *provenance,
      game::PlayerLifestyleWindowCandidatesFailureV1::
          candidate_provenance_invalid);

  auto evaluator = Base();
  evaluator->first.focus_rows[0].final_evaluator_invoked = false;
  RequireUnavailable(
      *evaluator,
      game::PlayerLifestyleWindowCandidatesFailureV1::
          final_legality_evaluator_unavailable);

  auto duplicate = Base();
  duplicate->first.perk_rows[1].key = duplicate->first.perk_rows[0].key;
  RequireUnavailable(
      *duplicate,
      game::PlayerLifestyleWindowCandidatesFailureV1::duplicate_stable_key);
}

void TestBothFreshAcquisitionsAndDrift() {
  auto reused = Base();
  reused->second.root_acquisition_serial =
      reused->first.root_acquisition_serial;
  RequireUnavailable(
      *reused,
      game::PlayerLifestyleWindowCandidatesFailureV1::
          root_reacquisition_not_proven);

  auto owner_drift = Base();
  owner_drift->second.window += 0x1000;
  RequireUnavailable(
      *owner_drift,
      game::PlayerLifestyleWindowCandidatesFailureV1::native_sample_drift);

  auto gate_drift = Base();
  gate_drift->second.perk_rows[0].can_select = true;
  RequireUnavailable(
      *gate_drift,
      game::PlayerLifestyleWindowCandidatesFailureV1::native_sample_drift);

  auto frame_drift = Base();
  ++frame_drift->after.proof_epoch;
  RequireUnavailable(
      *frame_drift,
      game::PlayerLifestyleWindowCandidatesFailureV1::revision_drift);
}

void TestAdmissionAndFailureVocabulary() {
  auto fixture = Base();
  game::PlayerLifestyleWindowCandidatesV1 output{};
  auto environment = Environment();
  environment.admitted_executable_sha256 = "WRONG";
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             environment, Access(*fixture), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleWindowCandidatesFailureV1::
             exact_build_not_admitted);

  fixture = Base();
  fixture->main_thread = false;
  RequireUnavailable(
      *fixture,
      game::PlayerLifestyleWindowCandidatesFailureV1::
          application_main_thread_required);

  fixture = Base();
  fixture->second_result =
      ck3::PlayerLifestyleWindowSourceReadResultV1::source_read_failed;
  RequireUnavailable(
      *fixture,
      game::PlayerLifestyleWindowCandidatesFailureV1::
          native_source_read_failed);

  assert(ck3::PlayerLifestyleWindowCandidatesFailureKeyV1(
             game::PlayerLifestyleWindowCandidatesFailureV1::
                 lifestyle_window_unbound_or_stale) ==
         "lifestyle_window_unbound_or_stale");
  assert(ck3::kLifestyleWindowForbiddenBinderRvaV1 == 0xF48780);
  assert(ck3::kLifestyleWindowForbiddenRefreshRvaV1 == 0x132C970);
  assert(ck3::kPlayerLifestyleWindowCandidatesReadOnlyV1);
  assert(!ck3::kPlayerLifestyleWindowCandidatesAdvertisedByDefaultV1);
}

} // namespace

int main() {
  TestAvailableStableCandidates();
  TestKnownEmptyIsAvailable();
  TestTypedUnboundAndOwnerFailures();
  TestContainerMaterializationAndCandidateFailures();
  TestBothFreshAcquisitionsAndDrift();
  TestAdmissionAndFailureVocabulary();
  std::cout << "player_lifestyle_window_candidates_v1_test: 6/6 GREEN\n";
  return 0;
}
