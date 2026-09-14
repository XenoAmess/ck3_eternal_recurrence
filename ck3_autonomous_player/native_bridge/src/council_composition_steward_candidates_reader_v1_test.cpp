#include "xar_bridge/council_composition_steward_candidates_reader_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string_view>
#include <vector>

namespace {

using namespace xar;
using Failure = game::CouncilCompositionStewardCandidatesFailureV1;
using Result = game::ReadCouncilCompositionStewardCandidatesResultV1;

constexpr std::array<std::int32_t, 11> kR684CharacterIds{
    30'784, 33'437, 33'888, 35'637, 57'582, 33'435,
    34'333, 34'867, 32'440, 43'706, 33'433};
constexpr std::array<std::int32_t, 11> kSortedCharacterIds{
    30'784, 32'440, 33'433, 33'435, 33'437, 33'888,
    34'333, 34'867, 35'637, 43'706, 57'582};
constexpr std::array<std::uint32_t, 11> kSortedOrdinals{
    0, 8, 10, 5, 1, 2, 6, 7, 3, 9, 4};

template <std::size_t Size>
void SetFixed(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < output.size());
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

struct Fixture {
  ck3_11906::CouncilCompositionStewardCandidatesFrameV1 frame{};
  std::array<std::uintptr_t, kR684CharacterIds.size()> pointers{};
  std::array<std::int32_t, kR684CharacterIds.size()> ids{kR684CharacterIds};
  std::uintptr_t vector_address = 0x000001E438000000ULL;
  bool main_thread = true;
  bool capture_ok = true;
  bool produce_ok = true;
  bool release_ok = true;
  bool readable_span = true;
  int unreadable_row = -1;
  int generation_mismatch_row = -1;
  std::int32_t capacity_override = 64;
  std::int32_t count_override = 11;
  bool drift_date_after_release = false;
  std::uint32_t capture_calls = 0;
  std::uint32_t produce_calls = 0;
  std::uint32_t release_calls = 0;
  bool observed_gui_mode = false;
  std::vector<int> events;

  Fixture() {
    SetFixed(frame.snapshot_id, "native:3");
    frame.public_revision = 4;
    frame.native_revision = 3;
    frame.date_raw = 53'178'264;
    frame.paused = true;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_alive = true;
    frame.played_character_id = 29'829;
    frame.played_character = 0x000001E430001000ULL;
    frame.played_character_identity_round_trip = true;
    frame.active_task_id = 7'159;
    frame.active_task = 0x000001E430002000ULL;
    frame.active_task_identity_round_trip = true;
    SetFixed(frame.position_key, "councillor_steward");
    for (std::size_t index = 0; index < pointers.size(); ++index) {
      pointers[index] = 0x000001E438100000ULL + index * 0x100;
    }
  }
};

bool CaptureFrame(
    void *opaque,
    ck3_11906::CouncilCompositionStewardCandidatesFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.capture_calls;
  fixture.events.push_back(1);
  if (!fixture.capture_ok) return false;
  output = fixture.frame;
  if (fixture.capture_calls == 2 && fixture.drift_date_after_release) {
    ++output.date_raw;
  }
  return true;
}

bool IsMainThread(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->main_thread;
}

bool Produce(
    void *opaque, std::uintptr_t owner_character,
    std::uintptr_t active_task, bool gui_eligibility_mode,
    ck3_11906::CouncilCompositionStewardNativeCandidateVectorV1
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.produce_calls;
  fixture.events.push_back(2);
  fixture.observed_gui_mode = gui_eligibility_mode;
  if (owner_character != fixture.frame.played_character ||
      active_task != fixture.frame.active_task) {
    return false;
  }
  output.data_address = fixture.count_override == 0 ? 0 : fixture.vector_address;
  output.capacity = fixture.capacity_override;
  output.count = fixture.count_override;
  return fixture.produce_ok;
}

bool Release(
    void *opaque,
    ck3_11906::CouncilCompositionStewardNativeCandidateVectorV1
        &vector) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.release_calls;
  fixture.events.push_back(3);
  if (!fixture.release_ok) return false;
  vector = {};
  return true;
}

bool IsReadableSpan(void *opaque, std::uintptr_t address,
                    std::size_t size) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  return fixture.readable_span && address == fixture.vector_address &&
      size == static_cast<std::size_t>(fixture.count_override) *
          sizeof(std::uintptr_t);
}

bool ReadCandidatePointer(void *opaque, std::uintptr_t address,
                          std::uintptr_t &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  if (address < fixture.vector_address) return false;
  const auto offset = address - fixture.vector_address;
  if (offset % sizeof(std::uintptr_t) != 0) return false;
  const auto index = offset / sizeof(std::uintptr_t);
  if (index >= fixture.pointers.size() ||
      static_cast<int>(index) == fixture.unreadable_row) {
    return false;
  }
  output = fixture.pointers[index];
  return true;
}

bool ReadCandidateId(void *opaque, std::uintptr_t candidate,
                     std::int32_t &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  const auto found = std::find(fixture.pointers.begin(), fixture.pointers.end(),
                               candidate);
  if (found == fixture.pointers.end()) return false;
  const auto index = static_cast<std::size_t>(found - fixture.pointers.begin());
  output = fixture.ids[index];
  return true;
}

bool ResolveCandidate(void *opaque, std::int32_t character_id,
                      std::uintptr_t &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  const auto found = std::find(fixture.ids.begin(), fixture.ids.end(),
                               character_id);
  if (found == fixture.ids.end()) return false;
  const auto index = static_cast<std::size_t>(found - fixture.ids.begin());
  output = fixture.pointers[index];
  if (static_cast<int>(index) == fixture.generation_mismatch_row) {
    output += 8;
  }
  return true;
}

ck3_11906::CouncilCompositionStewardCandidatesEnvironmentV1 Environment() {
  constexpr std::uintptr_t base = 0x140000000ULL;
  return {
      true,
      ck3_11906::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1,
      base,
      base + ck3_11906::kCouncilCompositionStewardCandidatesProducerRvaV1,
  };
}

ck3_11906::CouncilCompositionStewardCandidatesAccessV1 Access(Fixture &fixture) {
  return {
      &fixture,
      CaptureFrame,
      IsMainThread,
      Produce,
      Release,
      IsReadableSpan,
      ReadCandidatePointer,
      ReadCandidateId,
      ResolveCandidate,
  };
}

ck3_11906::CouncilCompositionStewardCandidatesRequestV1 Request() {
  return {"native:3", 4, 3, 53'178'264, 29'829};
}

Result Read(
    Fixture &fixture, game::CouncilCompositionStewardCandidatesV1 &output,
    ck3_11906::CouncilCompositionStewardCandidatesEnvironmentV1 environment =
        Environment(),
    ck3_11906::CouncilCompositionStewardCandidatesRequestV1 request =
        Request()) {
  return ck3_11906::ReadCouncilCompositionStewardCandidatesV1(
      environment, Access(fixture), request, output);
}

void ExpectUnavailable(
    const game::CouncilCompositionStewardCandidatesV1 &output,
    Failure reason, bool released) {
  assert(output.status ==
         game::CouncilCompositionStewardCandidatesStatusV1::unavailable);
  assert(output.unavailable_reason == reason);
  assert(output.candidate_count == 0);
  assert(!output.candidate_collection_complete);
  assert(!output.readiness.identity_ready);
  assert(!output.readiness.candidate_collection_ready);
  assert(output.temporary_vector_released == released);
}

void TestR684ElevenRowsSuccess() {
  Fixture fixture;
  game::CouncilCompositionStewardCandidatesV1 output{};
  assert(Read(fixture, output) == Result::available);
  assert(output.status ==
         game::CouncilCompositionStewardCandidatesStatusV1::available);
  assert(output.unavailable_reason == Failure::none);
  assert(output.owner_character_id == 29'829);
  assert(output.public_revision == 4);
  assert(output.native_revision == 3);
  assert(output.date_raw == 53'178'264);
  assert(output.paused);
  assert(output.candidate_collection_complete);
  assert(output.candidate_count == 11);
  assert(output.temporary_vector_released);
  assert(output.readiness.identity_ready);
  assert(output.readiness.candidate_collection_ready);
  for (std::size_t index = 0; index < kSortedCharacterIds.size(); ++index) {
    assert(output.candidates[index].character_id == kSortedCharacterIds[index]);
    assert(output.candidates[index].native_collection_ordinal ==
           kSortedOrdinals[index]);
  }
  assert(fixture.produce_calls == 1);
  assert(fixture.release_calls == 1);
  assert(fixture.capture_calls == 2);
  assert(fixture.observed_gui_mode);
  assert((fixture.events == std::vector<int>{1, 2, 3, 1}));
}

void TestEmptyVectorFixtureSuccess() {
  Fixture fixture;
  fixture.capacity_override = 0;
  fixture.count_override = 0;
  game::CouncilCompositionStewardCandidatesV1 output{};
  assert(Read(fixture, output) == Result::available);
  assert(output.candidate_count == 0);
  assert(output.candidate_collection_complete);
  assert(output.temporary_vector_released);
  assert(fixture.release_calls == 1);
}

void TestPreProducerGates() {
  {
    Fixture fixture;
    auto environment = Environment();
    environment.exact_build_admitted = false;
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output, environment) == Result::unavailable);
    ExpectUnavailable(output, Failure::exact_build_not_admitted, false);
    assert(fixture.produce_calls == 0 && fixture.release_calls == 0);
  }
  {
    Fixture fixture;
    fixture.main_thread = false;
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::application_main_thread_required, false);
    assert(fixture.produce_calls == 0 && fixture.release_calls == 0);
  }
  {
    Fixture fixture;
    fixture.frame.paused = false;
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::not_paused, false);
    assert(fixture.produce_calls == 0 && fixture.release_calls == 0);
  }
  {
    Fixture fixture;
    SetFixed(fixture.frame.position_key, "councillor_marshal");
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::position_outside_coverage, false);
    assert(fixture.produce_calls == 0 && fixture.release_calls == 0);
  }
}

void TestPostProducerFailuresAlwaysRelease() {
  {
    Fixture fixture;
    fixture.produce_ok = false;
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::candidate_collection_unavailable, true);
    assert(fixture.release_calls == 1);
  }
  {
    Fixture fixture;
    fixture.capacity_override = 10;
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::candidate_span_invalid, true);
    assert(fixture.release_calls == 1);
  }
  {
    Fixture fixture;
    fixture.unreadable_row = 4;
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::candidate_row_unreadable, true);
    assert(fixture.release_calls == 1);
  }
  {
    Fixture fixture;
    fixture.generation_mismatch_row = 5;
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::candidate_generation_mismatch, true);
    assert(fixture.release_calls == 1);
  }
  {
    Fixture fixture;
    fixture.ids[6] = fixture.ids[2];
    fixture.pointers[6] = fixture.pointers[2];
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::duplicate_candidate_id, true);
    assert(fixture.release_calls == 1);
  }
}

void TestReleaseAndFrameFailuresStayClosed() {
  {
    Fixture fixture;
    fixture.release_ok = false;
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::temporary_vector_release_failed, false);
    assert(fixture.release_calls == 1);
    assert(fixture.capture_calls == 1);
  }
  {
    Fixture fixture;
    fixture.drift_date_after_release = true;
    game::CouncilCompositionStewardCandidatesV1 output{};
    assert(Read(fixture, output) == Result::unavailable);
    ExpectUnavailable(output, Failure::date_drift, true);
    assert(fixture.release_calls == 1);
    assert((fixture.events == std::vector<int>{1, 2, 3, 1}));
  }
}

void TestFailureVocabulary() {
  assert(ck3_11906::CouncilCompositionStewardCandidatesFailureKeyV1(
             Failure::snapshot_identity_mismatch) ==
         "snapshot_identity_mismatch");
  assert(ck3_11906::CouncilCompositionStewardCandidatesFailureKeyV1(
             Failure::temporary_vector_release_failed) ==
         "temporary_vector_release_failed");
  assert(ck3_11906::kCouncilCompositionStewardCandidatesReaderPrivateKeyV1 ==
         "g2_council_composition_steward_candidates_reader_v1");
}

} // namespace

int main() {
  TestR684ElevenRowsSuccess();
  TestEmptyVectorFixtureSuccess();
  TestPreProducerGates();
  TestPostProducerFailuresAlwaysRelease();
  TestReleaseAndFrameFailuresStayClosed();
  TestFailureVocabulary();
  return 0;
}
