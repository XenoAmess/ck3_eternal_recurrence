#include "xar_bridge/player_lifestyle_snapshot_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

namespace game = xar::game;
namespace ck3 = xar::ck3_11906;

game::PlayerLifestyleStableKeyV1 Key(std::string_view value) {
  game::PlayerLifestyleStableKeyV1 output{};
  assert(ck3::AssignPlayerLifestyleStableKeyV1(value, output));
  return output;
}

template <std::size_t Size>
void CopyFixed(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < output.size());
  std::memcpy(output.data(), value.data(), value.size());
  output[value.size()] = '\0';
}

std::string ReadFixture(const char *path) {
  std::ifstream input(path, std::ios::binary);
  std::string output{std::istreambuf_iterator<char>(input),
                     std::istreambuf_iterator<char>()};
  while (!output.empty() &&
         (output.back() == '\n' || output.back() == '\r')) {
    output.pop_back();
  }
  return output;
}

struct Fixture {
  ck3::PlayerLifestyleSnapshotFrameV1 before{};
  ck3::PlayerLifestyleSnapshotFrameV1 after{};
  ck3::PlayerLifestyleSourceSampleV1 first{};
  ck3::PlayerLifestyleSourceSampleV1 second{};
  bool main_thread = true;
  bool fail_source = false;
  std::uint32_t frame_calls = 0;
  std::uint32_t source_calls = 0;
};

bool Capture(void *context,
             ck3::PlayerLifestyleSnapshotFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.frame_calls++ == 0 ? fixture.before : fixture.after;
  return true;
}

bool IsMain(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

bool ReadSource(void *context, std::uintptr_t character,
                ck3::PlayerLifestyleSourceSampleV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (fixture.fail_source || character != fixture.before.played_character) {
    return false;
  }
  output = fixture.source_calls++ == 0 ? fixture.first : fixture.second;
  return true;
}

Fixture Base() {
  Fixture fixture{};
  CopyFixed(fixture.before.snapshot_id, "life2-fixture-001");
  fixture.before.public_revision = 701;
  fixture.before.native_revision = 9001;
  fixture.before.proof_epoch = 17;
  fixture.before.date_raw = 54'321'000;
  fixture.before.paused = true;
  fixture.before.map_ready = true;
  fixture.before.has_played_character = true;
  fixture.before.played_character_alive = true;
  fixture.before.played_character_id = 32904;
  fixture.before.played_character = 0x123456780ULL;
  fixture.before.played_character_identity_round_trip = true;
  fixture.after = fixture.before;
  fixture.first.player_character_id = 32904;
  fixture.first.player_identity_round_trip = true;
  fixture.second = fixture.first;
  return fixture;
}

ck3::PlayerLifestyleSnapshotEnvironmentV1 OfflineEnvironment() {
  ck3::PlayerLifestyleSnapshotEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      ck3::kPlayerLifestyleSnapshotExecutableSha256V1;
  output.offline_fixture = true;
  return output;
}

ck3::PlayerLifestyleSnapshotAccessV1 OfflineAccess(Fixture &fixture) {
  ck3::PlayerLifestyleSnapshotAccessV1 output{};
  output.context = &fixture;
  output.capture_frame = &Capture;
  output.is_main_thread = &IsMain;
  output.read_offline_fixture_source = &ReadSource;
  return output;
}

ck3::PlayerLifestyleSnapshotRequestV1 Request() {
  return {"life2-fixture-001", 701, 9001, 54'321'000, 32904};
}

game::PlayerLifestyleLegalCandidateV1 Candidate(std::string_view key,
                                                 std::string_view lifestyle) {
  return {Key(key), Key(lifestyle)};
}

void FillNormal(ck3::PlayerLifestyleSourceSampleV1 &sample) {
  auto &state = sample.state;
  state.current_focus_presence =
      game::PlayerLifestyleFocusPresenceV1::present;
  state.current_focus_key = Key("stewardship_wealth_focus");
  state.current_lifestyle_key = Key("stewardship_lifestyle");
  state.current_lifestyle_progress_present = true;
  state.current_lifestyle_progress.lifestyle_key =
      state.current_lifestyle_key;
  state.current_lifestyle_progress.xp_total_raw = 250'100'000;
  state.current_lifestyle_progress.xp_within_level_raw = 50'100'000;
  state.current_lifestyle_progress.xp_per_level = 1000;
  state.current_lifestyle_progress.unspent_perk_points = 1;
  state.current_lifestyle_progress.used_perk_points = 1;

  state.owned_perk_count = 3;
  state.owned_perk_keys[0] = Key("tax_man_perk");
  state.owned_perk_keys[1] = Key("golden_obligations_perk");
  state.owned_perk_keys[2] = Key("thoughtful_perk");

  state.legal_focus_candidate_status =
      game::PlayerLifestyleCandidateCollectionStatusV1::available;
  state.legal_focus_candidate_unavailable_reason =
      game::PlayerLifestyleCandidateCollectionFailureV1::none;
  state.legal_focus_candidate_count = 2;
  state.legal_focus_candidates[0] =
      Candidate("stewardship_wealth_focus", "stewardship_lifestyle");
  state.legal_focus_candidates[1] =
      Candidate("stewardship_domain_focus", "stewardship_lifestyle");

  state.legal_perk_candidate_status =
      game::PlayerLifestyleCandidateCollectionStatusV1::available;
  state.legal_perk_candidate_unavailable_reason =
      game::PlayerLifestyleCandidateCollectionFailureV1::none;
  state.legal_perk_candidate_count = 2;
  state.legal_perk_candidates[0] =
      Candidate("war_profiteer_perk", "stewardship_lifestyle");
  state.legal_perk_candidates[1] =
      Candidate("heregeld_perk", "stewardship_lifestyle");
}

void FillNoFocus(ck3::PlayerLifestyleSourceSampleV1 &sample) {
  auto &state = sample.state;
  state.current_focus_presence =
      game::PlayerLifestyleFocusPresenceV1::absent;
  state.owned_perk_count = 0;
  state.legal_focus_candidate_status =
      game::PlayerLifestyleCandidateCollectionStatusV1::available;
  state.legal_focus_candidate_unavailable_reason =
      game::PlayerLifestyleCandidateCollectionFailureV1::none;
  state.legal_focus_candidate_count = 2;
  state.legal_focus_candidates[0] =
      Candidate("stewardship_wealth_focus", "stewardship_lifestyle");
  state.legal_focus_candidates[1] =
      Candidate("learning_medicine_focus", "learning_lifestyle");
  state.legal_perk_candidate_status =
      game::PlayerLifestyleCandidateCollectionStatusV1::available;
  state.legal_perk_candidate_unavailable_reason =
      game::PlayerLifestyleCandidateCollectionFailureV1::none;
  state.legal_perk_candidate_count = 0;
}

std::string ReadOffline(Fixture &fixture,
                        game::PlayerLifestyleSnapshotV1 &output) {
  const auto result = ck3::ReadPlayerLifestyleSnapshotV1(
      OfflineEnvironment(), OfflineAccess(fixture), Request(), output);
  assert(result == game::ReadPlayerLifestyleSnapshotResultV1::available);
  assert(output.status == game::PlayerLifestyleSnapshotStatusV1::available);
  assert(output.readiness.current_focus_ready);
  assert(output.readiness.lifestyle_progress_ready);
  assert(output.readiness.owned_perks_ready);
  assert(output.readiness.legal_focus_candidates_ready);
  assert(output.readiness.legal_perk_candidates_ready);
  assert(output.readiness.same_frame_ready);
  assert(fixture.frame_calls == 2 && fixture.source_calls == 2);
  return ck3::SerializePlayerLifestyleSnapshotV1(output);
}

void ExpectFixture(const std::string &actual, const char *path) {
  const auto expected = ReadFixture(path);
  if (actual != expected) {
    std::cerr << "fixture mismatch: " << path << "\nactual: " << actual
              << "\nexpected: " << expected << '\n';
    std::abort();
  }
}

void TestNormalAndNoFocusFixtures(const char *normal_path,
                                  const char *no_focus_path) {
  auto normal = Base();
  FillNormal(normal.first);
  normal.second = normal.first;
  game::PlayerLifestyleSnapshotV1 normal_output{};
  const auto normal_json = ReadOffline(normal, normal_output);
  assert(normal_output.state.owned_perk_count == 3);
  assert(ck3::PlayerLifestyleStableKeyViewV1(
             normal_output.state.owned_perk_keys[0]) ==
         "golden_obligations_perk");
  assert(ck3::PlayerLifestyleStableKeyViewV1(
             normal_output.state.legal_perk_candidates[0].key) ==
         "heregeld_perk");
  ExpectFixture(normal_json, normal_path);

  auto no_focus = Base();
  FillNoFocus(no_focus.first);
  no_focus.second = no_focus.first;
  game::PlayerLifestyleSnapshotV1 no_focus_output{};
  const auto no_focus_json = ReadOffline(no_focus, no_focus_output);
  assert(no_focus_output.state.current_focus_presence ==
         game::PlayerLifestyleFocusPresenceV1::absent);
  assert(!no_focus_output.state.current_lifestyle_progress_present);
  assert(no_focus_output.state.owned_perk_count == 0);
  assert(no_focus_output.state.legal_perk_candidate_count == 0);
  ExpectFixture(no_focus_json, no_focus_path);
}

void TestFailureDoesNotPublishEmptyState() {
  auto fixture = Base();
  FillNormal(fixture.first);
  fixture.second = fixture.first;
  fixture.fail_source = true;
  game::PlayerLifestyleSnapshotV1 output{};
  const auto result = ck3::ReadPlayerLifestyleSnapshotV1(
      OfflineEnvironment(), OfflineAccess(fixture), Request(), output);
  assert(result == game::ReadPlayerLifestyleSnapshotResultV1::unavailable);
  assert(output.status == game::PlayerLifestyleSnapshotStatusV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleSnapshotFailureV1::native_source_read_failed);
  assert(output.state.current_focus_presence ==
         game::PlayerLifestyleFocusPresenceV1::unknown);
  assert(output.state.owned_perk_count == 0);
  assert(!output.readiness.current_focus_ready &&
         !output.readiness.owned_perks_ready &&
         !output.readiness.same_frame_ready);
  assert(ck3::SerializePlayerLifestyleSnapshotV1(output) ==
         "{\"private_build\":true,\"advertised\":false,"
         "\"status\":\"unavailable\","
         "\"unavailable_reason\":\"native_source_read_failed\"}");
}

void TestSampleAndFrameDrift() {
  auto sample_drift = Base();
  FillNormal(sample_drift.first);
  sample_drift.second = sample_drift.first;
  sample_drift.second.state.current_lifestyle_progress.xp_total_raw += 1;
  game::PlayerLifestyleSnapshotV1 output{};
  assert(ck3::ReadPlayerLifestyleSnapshotV1(
             OfflineEnvironment(), OfflineAccess(sample_drift), Request(),
             output) ==
         game::ReadPlayerLifestyleSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleSnapshotFailureV1::native_sample_drift);

  auto frame_drift = Base();
  FillNormal(frame_drift.first);
  frame_drift.second = frame_drift.first;
  ++frame_drift.after.proof_epoch;
  assert(ck3::ReadPlayerLifestyleSnapshotV1(
             OfflineEnvironment(), OfflineAccess(frame_drift), Request(),
             output) ==
         game::ReadPlayerLifestyleSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleSnapshotFailureV1::revision_drift);
}

void TestInvalidAndDuplicateStableKeys() {
  auto invalid = Base();
  FillNormal(invalid.first);
  invalid.first.state.current_focus_key.bytes[0] = 'X';
  invalid.second = invalid.first;
  game::PlayerLifestyleSnapshotV1 output{};
  assert(ck3::ReadPlayerLifestyleSnapshotV1(
             OfflineEnvironment(), OfflineAccess(invalid), Request(),
             output) ==
         game::ReadPlayerLifestyleSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleSnapshotFailureV1::current_focus_invariant_failed);

  auto duplicate = Base();
  FillNormal(duplicate.first);
  duplicate.first.state.owned_perk_keys[1] =
      duplicate.first.state.owned_perk_keys[0];
  duplicate.second = duplicate.first;
  assert(ck3::ReadPlayerLifestyleSnapshotV1(
             OfflineEnvironment(), OfflineAccess(duplicate), Request(),
             output) ==
         game::ReadPlayerLifestyleSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleSnapshotFailureV1::duplicate_stable_key);
}

struct NativeStringFixture {
  std::array<std::uint8_t, 32> inline_string{};
  std::array<std::uint8_t, 32> heap_string{};
  std::array<char, 64> heap_bytes{};
};

template <typename Value, std::size_t Size>
void Put(std::array<std::uint8_t, Size> &bytes, std::size_t offset,
         Value value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

bool DirectMemory(void *, std::uintptr_t address, void *output,
                  std::size_t size) noexcept {
  if (address == 0 || output == nullptr) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

void TestMsvcStableKeyReader() {
  NativeStringFixture fixture{};
  constexpr std::string_view inline_key = "tax_man_perk";
  std::memcpy(fixture.inline_string.data(), inline_key.data(),
              inline_key.size());
  Put(fixture.inline_string, 0x10,
      static_cast<std::uint64_t>(inline_key.size()));
  Put(fixture.inline_string, 0x18, std::uint64_t{15});

  constexpr std::string_view heap_key = "stewardship_wealth_focus";
  std::memcpy(fixture.heap_bytes.data(), heap_key.data(), heap_key.size());
  Put(fixture.heap_string, 0,
      reinterpret_cast<std::uintptr_t>(fixture.heap_bytes.data()));
  Put(fixture.heap_string, 0x10,
      static_cast<std::uint64_t>(heap_key.size()));
  Put(fixture.heap_string, 0x18, std::uint64_t{63});

  game::PlayerLifestyleStableKeyV1 output{};
  assert(ck3::ReadPlayerLifestyleMsvcStableKeyV1(
      nullptr, &DirectMemory,
      reinterpret_cast<std::uintptr_t>(fixture.inline_string.data()),
      output));
  assert(ck3::PlayerLifestyleStableKeyViewV1(output) == inline_key);
  assert(ck3::ReadPlayerLifestyleMsvcStableKeyV1(
      nullptr, &DirectMemory,
      reinterpret_cast<std::uintptr_t>(fixture.heap_string.data()), output));
  assert(ck3::PlayerLifestyleStableKeyViewV1(output) == heap_key);

  fixture.inline_string[0] = 'B';
  assert(!ck3::ReadPlayerLifestyleMsvcStableKeyV1(
      nullptr, &DirectMemory,
      reinterpret_cast<std::uintptr_t>(fixture.inline_string.data()),
      output));
}

struct NativeFixture {
  std::array<std::uint8_t, 0x900> focus{};
  std::array<std::uint8_t, 0x180> lifestyle{};
  std::array<std::uint8_t, 0x40> perk_a{};
  std::array<std::uint8_t, 0x40> perk_b{};
  std::array<std::uintptr_t, 2> perk_rows{};
  struct Span {
    std::uintptr_t data = 0;
    std::uint32_t unknown = 0;
    std::int32_t count = 0;
  } span{};
  std::uintptr_t fallback_focus = 0x11110000ULL;
};

NativeFixture *g_native = nullptr;

void WriteInlineKey(std::uint8_t *object, std::size_t offset,
                    std::string_view key) {
  assert(key.size() < 16);
  std::memcpy(object + offset, key.data(), key.size());
  const auto size = static_cast<std::uint64_t>(key.size());
  const std::uint64_t capacity = 15;
  std::memcpy(object + offset + 0x10, &size, sizeof(size));
  std::memcpy(object + offset + 0x18, &capacity, sizeof(capacity));
}

void WriteHeapKey(std::uint8_t *object, std::size_t offset,
                  const char *key, std::size_t size) {
  const auto pointer = reinterpret_cast<std::uintptr_t>(key);
  const std::uint64_t key_size = size;
  const std::uint64_t capacity = 63;
  std::memcpy(object + offset, &pointer, sizeof(pointer));
  std::memcpy(object + offset + 0x10, &key_size, sizeof(key_size));
  std::memcpy(object + offset + 0x18, &capacity, sizeof(capacity));
}

void *NativeFocus(void *) {
  return g_native == nullptr ? nullptr : g_native->focus.data();
}

void *NativeLifestyle(void *) {
  return g_native == nullptr ? nullptr : g_native->lifestyle.data();
}

std::int32_t NativeUnspent(void *, void *) { return 1; }
std::int32_t NativeUsed(void *, void *) { return 1; }

std::int64_t *NativeXp(void *, std::int64_t *output, void *,
                       bool within) {
  if (output != nullptr) *output = within ? 50'100'000 : 250'100'000;
  return output;
}

const void *NativePerks(void *) {
  return g_native == nullptr ? nullptr : &g_native->span;
}

void TestNativeCurrentStateAndCandidateBoundary() {
  NativeFixture native{};
  g_native = &native;
  static constexpr char focus_key[] = "stewardship_wealth_focus";
  static constexpr char lifestyle_key[] = "stewardship_lifestyle";
  WriteHeapKey(native.focus.data(),
               ck3::kPlayerLifestyleDatabaseStableKeyOffsetV1,
               focus_key, std::char_traits<char>::length(focus_key));
  WriteHeapKey(native.lifestyle.data(),
               ck3::kPlayerLifestyleDatabaseStableKeyOffsetV1,
               lifestyle_key,
               std::char_traits<char>::length(lifestyle_key));
  const auto lifestyle_pointer =
      reinterpret_cast<std::uintptr_t>(native.lifestyle.data());
  std::memcpy(native.focus.data() +
                  ck3::kPlayerLifestyleFocusLifestyleOffsetV1,
              &lifestyle_pointer, sizeof(lifestyle_pointer));
  const std::int32_t xp_per_level = 1000;
  std::memcpy(native.lifestyle.data() +
                  ck3::kPlayerLifestyleXpPerLevelOffsetV1,
              &xp_per_level, sizeof(xp_per_level));
  WriteInlineKey(native.perk_a.data(),
                 ck3::kPlayerLifestyleCharacterPerkStableKeyOffsetV1,
                 "tax_man_perk");
  WriteInlineKey(native.perk_b.data(),
                 ck3::kPlayerLifestyleCharacterPerkStableKeyOffsetV1,
                 "heregeld_perk");
  native.perk_rows = {
      reinterpret_cast<std::uintptr_t>(native.perk_a.data()),
      reinterpret_cast<std::uintptr_t>(native.perk_b.data())};
  native.span.data =
      reinterpret_cast<std::uintptr_t>(native.perk_rows.data());
  native.span.count = 2;

  auto fixture = Base();
  fixture.before.played_character = 0x22220000ULL;
  fixture.after = fixture.before;
  ck3::PlayerLifestyleSnapshotAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.read_memory = &DirectMemory;

  ck3::PlayerLifestyleSnapshotEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      ck3::kPlayerLifestyleSnapshotExecutableSha256V1;
  environment.module_base = 1;
  environment.current_focus = &NativeFocus;
  environment.current_lifestyle = &NativeLifestyle;
  environment.unspent_perk_points = &NativeUnspent;
  environment.used_perk_points = &NativeUsed;
  environment.lifestyle_xp = &NativeXp;
  environment.unlocked_perks = &NativePerks;
  environment.focus_fallback_slot_address =
      reinterpret_cast<std::uintptr_t>(&native.fallback_focus);

  game::PlayerLifestyleSnapshotV1 output{};
  assert(ck3::ReadPlayerLifestyleSnapshotV1(
             environment, access, Request(), output) ==
         game::ReadPlayerLifestyleSnapshotResultV1::available);
  assert(output.readiness.current_focus_ready &&
         output.readiness.lifestyle_progress_ready &&
         output.readiness.owned_perks_ready &&
         !output.readiness.legal_focus_candidates_ready &&
         !output.readiness.legal_perk_candidates_ready &&
         output.readiness.same_frame_ready);
  assert(output.state.legal_focus_candidate_status ==
         game::PlayerLifestyleCandidateCollectionStatusV1::unavailable);
  assert(output.state.legal_focus_candidate_count == 0 &&
         output.state.legal_perk_candidate_count == 0);
  const auto json = ck3::SerializePlayerLifestyleSnapshotV1(output);
  assert(json.find("\"reason\":\"lifestyle_window_unavailable\"") !=
         std::string::npos);
  assert(json.find("\"owned_perk_keys\":[\"heregeld_perk\","
                   "\"tax_man_perk\"]") != std::string::npos);

  auto no_focus_fixture = Base();
  access.context = &no_focus_fixture;
  native.fallback_focus =
      reinterpret_cast<std::uintptr_t>(native.focus.data());
  output = {};
  assert(ck3::ReadPlayerLifestyleSnapshotV1(
             environment, access, Request(), output) ==
         game::ReadPlayerLifestyleSnapshotResultV1::available);
  assert(output.state.current_focus_presence ==
         game::PlayerLifestyleFocusPresenceV1::absent);
  assert(!output.state.current_lifestyle_progress_present);
  assert(output.state.owned_perk_count == 2);
  g_native = nullptr;
}

void TestBoundEnvironment() {
  constexpr std::uintptr_t module = 0x140000000ULL;
  const auto environment = ck3::BindPlayerLifestyleSnapshotEnvironmentV1(
      module, true, ck3::kPlayerLifestyleSnapshotExecutableSha256V1);
  assert(reinterpret_cast<std::uintptr_t>(environment.current_focus) ==
         module + ck3::kPlayerLifestyleCurrentFocusGetterRvaV1);
  assert(reinterpret_cast<std::uintptr_t>(environment.current_lifestyle) ==
         module + ck3::kPlayerLifestyleCurrentLifestyleGetterRvaV1);
  assert(environment.focus_fallback_slot_address ==
         module + ck3::kPlayerLifestyleFocusFallbackSlotRvaV1);
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 3);
  TestNormalAndNoFocusFixtures(argv[1], argv[2]);
  TestFailureDoesNotPublishEmptyState();
  TestSampleAndFrameDrift();
  TestInvalidAndDuplicateStableKeys();
  TestMsvcStableKeyReader();
  TestNativeCurrentStateAndCandidateBoundary();
  TestBoundEnvironment();
  std::cout << "player-lifestyle-snapshot-v1 fixture passed\n";
  return 0;
}
