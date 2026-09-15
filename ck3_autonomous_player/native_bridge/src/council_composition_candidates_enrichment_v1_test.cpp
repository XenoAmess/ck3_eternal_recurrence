#include "xar_bridge/council_composition_candidates_enrichment_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string_view>

namespace {

using namespace xar;
using Failure = game::CouncilCompositionCandidatesEnrichmentFailureV1;
using Result = game::ReadCouncilCompositionCandidatesEnrichmentResultV1;

template <std::size_t Size>
void SetFixed(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < output.size());
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

template <std::size_t Size, typename Value>
void Store(std::array<std::byte, Size> &object, std::size_t offset,
           Value value) {
  assert(offset + sizeof(value) <= object.size());
  std::memcpy(object.data() + offset, &value, sizeof(value));
}

struct Fixture {
  struct Character {
    std::array<std::byte, 0x100> bytes{};
    std::int32_t id = -1;
  };

  std::array<std::byte, 0x80> active_task{};
  std::array<Character, 3> characters{};
  ck3_11906::CouncilCompositionStewardCandidatesFrameV1 frame{};
  bool main_thread = true;
  bool drift_after_first_capture = false;
  std::uint32_t capture_count = 0;
  const void *unreadable_address = nullptr;

  Fixture() {
    SetCharacter(0, 33'433, 12);
    SetCharacter(1, 30'784, 18);
    SetCharacter(2, 57'582, 27);
    Store(active_task,
          ck3_11906::kCouncilCompositionActiveTaskIncumbentIdOffsetV1,
          std::int32_t{33'433});
    SetFixed(frame.snapshot_id, "native:17");
    frame.public_revision = 19;
    frame.native_revision = 17;
    frame.date_raw = 53'178'264;
    frame.paused = true;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_alive = true;
    frame.played_character_id = 29'829;
    frame.played_character = 0x1234;
    frame.played_character_identity_round_trip = true;
    frame.active_task_id = 7'159;
    frame.active_task = reinterpret_cast<std::uintptr_t>(active_task.data());
    frame.active_task_identity_round_trip = true;
    SetFixed(frame.position_key, "councillor_steward");
  }

  void SetCharacter(std::size_t index, std::int32_t id,
                    std::int32_t stewardship) {
    characters[index].id = id;
    Store(characters[index].bytes,
          ck3_11906::kCouncilCompositionCharacterIdentityOffsetV1, id);
    Store(characters[index].bytes,
          ck3_11906::kCouncilCompositionCharacterStewardshipOffsetV1,
          stewardship);
  }
};

bool InObject(const void *address, std::size_t size, const std::byte *begin,
              std::size_t capacity, std::size_t &offset) {
  const auto target = reinterpret_cast<std::uintptr_t>(address);
  const auto first = reinterpret_cast<std::uintptr_t>(begin);
  if (target < first || target > first + capacity ||
      size > capacity - static_cast<std::size_t>(target - first)) {
    return false;
  }
  offset = static_cast<std::size_t>(target - first);
  return true;
}

bool Capture(void *context,
             ck3_11906::CouncilCompositionStewardCandidatesFrameV1 &output)
    noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.frame;
  if (fixture.drift_after_first_capture && fixture.capture_count != 0) {
    ++output.native_revision;
  }
  ++fixture.capture_count;
  return true;
}

bool IsMain(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

bool ReadMemory(void *context, const void *address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (address == fixture.unreadable_address || output == nullptr || size == 0) {
    return false;
  }
  std::size_t offset = 0;
  if (InObject(address, size, fixture.active_task.data(),
               fixture.active_task.size(), offset)) {
    std::memcpy(output, fixture.active_task.data() + offset, size);
    return true;
  }
  for (const auto &character : fixture.characters) {
    if (InObject(address, size, character.bytes.data(), character.bytes.size(),
                 offset)) {
      std::memcpy(output, character.bytes.data() + offset, size);
      return true;
    }
  }
  return false;
}

bool Resolve(void *context, std::int32_t id,
             std::uintptr_t &character) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  character = 0;
  for (auto &row : fixture.characters) {
    if (row.id == id) {
      character = reinterpret_cast<std::uintptr_t>(row.bytes.data());
      return true;
    }
  }
  return false;
}

game::CouncilCompositionStewardCandidatesV1 PrivateResult() {
  game::CouncilCompositionStewardCandidatesV1 output{};
  output.status =
      game::CouncilCompositionStewardCandidatesStatusV1::available;
  output.unavailable_reason =
      game::CouncilCompositionStewardCandidatesFailureV1::none;
  SetFixed(output.snapshot_id, "native:17");
  output.public_revision = 19;
  output.native_revision = 17;
  output.date_raw = 53'178'264;
  output.paused = true;
  output.owner_character_id = 29'829;
  SetFixed(output.position_key, "councillor_steward");
  output.candidate_collection_complete = true;
  output.candidate_count = 2;
  output.candidates[0] = {30'784, 4};
  output.candidates[1] = {57'582, 1};
  output.temporary_vector_released = true;
  output.readiness.identity_ready = true;
  output.readiness.candidate_collection_ready = true;
  return output;
}

ck3_11906::CouncilCompositionCandidatesEnrichmentEnvironmentV1 Environment() {
  return {true,
          ck3_11906::
              kCouncilCompositionCandidatesEnrichmentExecutableSha256V1};
}

ck3_11906::CouncilCompositionCandidatesEnrichmentAccessV1 Access(
    Fixture &fixture) {
  return {&fixture, &Capture, &IsMain, &ReadMemory, &Resolve};
}

ck3_11906::CouncilCompositionCandidatesPublicEnrichmentV1 Read(
    Fixture &fixture, const game::CouncilCompositionStewardCandidatesV1 &input,
    Result expected, Failure expected_failure) {
  ck3_11906::CouncilCompositionCandidatesPublicEnrichmentV1 output{};
  Failure failure = Failure::none;
  assert(ck3_11906::ReadCouncilCompositionCandidatesEnrichmentV1(
             Environment(), Access(fixture), input, output, failure) ==
         expected);
  assert(failure == expected_failure);
  return output;
}

void TestOccupiedSameFrameEnrichment() {
  Fixture fixture;
  const auto enrichment = Read(fixture, PrivateResult(), Result::available,
                               Failure::none);
  assert(enrichment.incumbent_ready);
  assert(enrichment.incumbent_character_id == 33'433);
  assert(enrichment.incumbent_main_skill_ready);
  assert(enrichment.incumbent_main_skill == 12);
  assert(enrichment.candidate_count == 2);
  assert(enrichment.candidates[0].character_id == 30'784);
  assert(enrichment.candidates[0].main_skill == 18);
  assert(enrichment.candidates[1].character_id == 57'582);
  assert(enrichment.candidates[1].main_skill == 27);
  assert(enrichment.same_frame_stable);

  game::CouncilCompositionCandidatesPublicV1 public_output{};
  assert(ck3_11906::ProjectCouncilCompositionCandidatesPublicV1(
             PrivateResult(), enrichment, public_output) ==
         ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1::
             available);
  assert(!public_output.vacant);
  assert(public_output.incumbent_main_skill.value == 12);
  assert(public_output.readiness.incumbent_main_skill_ready);
}

void TestVacancyHasNullSkillSentinel() {
  Fixture fixture;
  Store(fixture.active_task,
        ck3_11906::kCouncilCompositionActiveTaskIncumbentIdOffsetV1,
        std::int32_t{-1});
  const auto enrichment = Read(fixture, PrivateResult(), Result::available,
                               Failure::none);
  assert(enrichment.incumbent_character_id == -1);
  assert(enrichment.incumbent_main_skill == -1);
  assert(enrichment.incumbent_main_skill_ready);
}

void TestFailClosedInputsAndDrift() {
  {
    Fixture fixture;
    fixture.main_thread = false;
    Read(fixture, PrivateResult(), Result::unavailable,
         Failure::application_main_thread_required);
  }
  {
    Fixture fixture;
    auto input = PrivateResult();
    ++input.native_revision;
    Read(fixture, input, Result::unavailable,
         Failure::same_frame_binding_mismatch);
  }
  {
    Fixture fixture;
    fixture.SetCharacter(1, 30'784, -1);
    Read(fixture, PrivateResult(), Result::unavailable,
         Failure::candidate_main_skill_unreadable);
  }
  {
    Fixture fixture;
    fixture.unreadable_address =
        fixture.characters[0].bytes.data() +
        ck3_11906::kCouncilCompositionCharacterStewardshipOffsetV1;
    Read(fixture, PrivateResult(), Result::unavailable,
         Failure::incumbent_main_skill_unreadable);
  }
  {
    Fixture fixture;
    fixture.drift_after_first_capture = true;
    Read(fixture, PrivateResult(), Result::unavailable, Failure::frame_drift);
  }
}

} // namespace

int main() {
  TestOccupiedSameFrameEnrichment();
  TestVacancyHasNullSkillSentinel();
  TestFailClosedInputsAndDrift();
  return 0;
}
