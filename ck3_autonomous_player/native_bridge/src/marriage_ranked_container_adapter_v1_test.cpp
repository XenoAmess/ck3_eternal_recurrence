#include "xar_bridge/marriage_ranked_container_adapter_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace bridge = xar::bridge;

namespace {

constexpr std::uintptr_t kCandidateOwnerVtable = 0x11110000;
constexpr std::uintptr_t kScoredOwnerVtable = 0x22220000;
constexpr std::uintptr_t kScoredRowVtable = 0x33330000;
constexpr std::uintptr_t kCandidateBacking = 0x44440000;
constexpr std::uintptr_t kScoredBacking = 0x55550000;

struct Header {
  void *data;
  std::int32_t capacity;
  std::int32_t count;
  void *owner;
};
static_assert(sizeof(Header) == bridge::kMarriageRankedHeaderSizeV1);

template <typename Value, std::size_t Size>
void Write(std::array<std::byte, Size> &bytes, std::size_t offset,
           Value value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

void WritePointer(void *base, std::size_t offset, std::uintptr_t value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0x200> subject{};
  std::array<std::byte, 0x320> living{};
  std::array<std::byte, 0x10> age_data{};
  std::array<std::int32_t, 3> native_caps{11, 77, 99};
  std::uintptr_t native_cap_table =
      reinterpret_cast<std::uintptr_t>(native_caps.data());
  std::array<std::byte, 0x10> strategy{};
  std::array<std::byte, 0x10> interaction{};
  std::array<std::byte, 0x40> candidate_a{};
  std::array<std::byte, 0x40> candidate_b{};
  int enumerate_calls = 0;
  int score_calls = 0;
  int release_calls = 0;
  int scored_reset_calls = 0;
  int destroyed_rows = 0;
  std::int32_t observed_cap = -1;
  bool observed_young = false;

  Fixture() {
    Write(subject, bridge::kMarriageCharacterLivingDataOffsetV1,
          reinterpret_cast<std::uintptr_t>(living.data()));
    Write(living, 0x308, reinterpret_cast<std::uintptr_t>(age_data.data()));
    Write(age_data, 2, std::int8_t{25});
  }
};

Fixture *g_fixture = nullptr;

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

std::int32_t ReadTier(void *character) {
  assert(character == g_fixture->subject.data());
  return 1;
}

void InitializeCandidate(void *owner, void **data, std::int32_t *capacity) {
  *data = static_cast<std::byte *>(owner) + 8;
  *capacity = static_cast<std::int32_t>(
      bridge::kMarriageCandidateInlineCapacityV1);
}

void ReleaseBuffer(void *, void *, std::size_t alignment) {
  assert(alignment == 8);
  ++g_fixture->release_calls;
}

void *InitializeScored(void *scored_header) {
  assert(reinterpret_cast<std::uintptr_t>(scored_header) % 16 == 0);
  auto &header = *static_cast<Header *>(scored_header);
  if (header.count > 0) g_fixture->destroyed_rows += header.count;
  if (header.owner != nullptr) ++g_fixture->release_calls;
  auto *owner = static_cast<std::byte *>(scored_header) +
      bridge::kMarriageRankedHeaderSizeV1;
  header = {};
  header.owner = owner;
  WritePointer(owner, 0, kScoredOwnerVtable);
  WritePointer(owner, 0x208, kScoredBacking);
  header.data = owner + 8;
  header.capacity =
      static_cast<std::int32_t>(bridge::kMarriageScoredInlineCapacityV1);
  ++g_fixture->scored_reset_calls;
  return scored_header;
}

void Enumerate(void *strategy, std::int32_t selector, bool mode,
               std::int32_t cap, void *candidate_header) {
  assert(strategy == g_fixture->strategy.data() && selector == 0 && mode);
  assert(reinterpret_cast<std::uintptr_t>(candidate_header) % 16 == 0);
  ++g_fixture->enumerate_calls;
  g_fixture->observed_cap = cap;
  auto &header = *static_cast<Header *>(candidate_header);
  auto **rows = static_cast<void **>(header.data);
  rows[0] = g_fixture->candidate_a.data();
  rows[1] = g_fixture->candidate_b.data();
  header.count = 2;
}

void Score(void *strategy, const void *parameters, void *candidate_header,
           void *scored_header) {
  assert(strategy == g_fixture->strategy.data());
  ++g_fixture->score_calls;
  const auto *bytes = static_cast<const std::byte *>(parameters);
  std::uintptr_t interaction = 0;
  std::uintptr_t subject_a = 0;
  std::uintptr_t subject_b = 0;
  std::memcpy(&interaction, bytes, sizeof(interaction));
  std::memcpy(&subject_a, bytes + 8, sizeof(subject_a));
  std::memcpy(&subject_b, bytes + 0x10, sizeof(subject_b));
  std::memcpy(&g_fixture->observed_young, bytes + 0x18,
              sizeof(g_fixture->observed_young));
  assert(interaction ==
             reinterpret_cast<std::uintptr_t>(g_fixture->interaction.data()) &&
         subject_a ==
             reinterpret_cast<std::uintptr_t>(g_fixture->subject.data()) &&
         subject_b == subject_a);
  std::int32_t minimum_score = 0;
  std::memcpy(&minimum_score, bytes + 0x1C, sizeof(minimum_score));
  assert(minimum_score == 1);
  assert(static_cast<Header *>(candidate_header)->count == 2);
  auto &header = *static_cast<Header *>(scored_header);
  auto *rows = static_cast<std::byte *>(header.data);
  WritePointer(rows, 0, kScoredRowVtable);
  WritePointer(rows + 0x10, 0, kScoredRowVtable);
  const std::int32_t id_a = 0x01000001;
  const std::int32_t id_b = 0x02000002;
  const std::int32_t score_a = 500;
  const std::int32_t score_b = 400;
  std::memcpy(rows + 8, &id_a, sizeof(id_a));
  std::memcpy(rows + 0xC, &score_a, sizeof(score_a));
  std::memcpy(rows + 0x18, &id_b, sizeof(id_b));
  std::memcpy(rows + 0x1C, &score_b, sizeof(score_b));
  header.count = 2;
}

void InitializeState(Fixture &fixture,
                     bridge::MarriageRankedContainerAdapterStateV1 &state) {
  g_fixture = &fixture;
  auto &env = state.environment;
  env.module_base = 1;
  env.exact_build_admitted = true;
  env.admitted_executable_sha256 =
      bridge::kMarriageProposalNativeBinderExecutableSha256V1;
  env.offline_fixture = true;
  env.read_memory = &ReadMemory;
  env.read_native_tier = &ReadTier;
  env.native_cap_table_slot =
      reinterpret_cast<std::uintptr_t>(&fixture.native_cap_table);
  env.enumerate_candidates = &Enumerate;
  env.score_candidates = &Score;
  env.initialize_scored_container = &InitializeScored;
  env.release_native_buffer = &ReleaseBuffer;
  env.initialize_candidate_buffer = &InitializeCandidate;
  env.candidate_owner_vtable = kCandidateOwnerVtable;
  env.scored_owner_vtable = kScoredOwnerVtable;
  env.scored_row_vtable = kScoredRowVtable;
  env.candidate_backing_allocator = kCandidateBacking;
  env.scored_backing_allocator = kScoredBacking;
}

bridge::MarriageNativeRankedInvocationV1 Request(Fixture &fixture) {
  bridge::MarriageNativeRankedInvocationV1 output{};
  output.subject_character =
      reinterpret_cast<std::uintptr_t>(fixture.subject.data());
  output.strategy = reinterpret_cast<std::uintptr_t>(fixture.strategy.data());
  output.arrange_marriage_interaction =
      reinterpret_cast<std::uintptr_t>(fixture.interaction.data());
  output.limit = 1;
  output.entry_points.enumerate_candidates =
      reinterpret_cast<std::uintptr_t>(&Enumerate);
  output.entry_points.score_filter_candidates =
      reinterpret_cast<std::uintptr_t>(&Score);
  return output;
}

void TestBindingAndCompleteLifecycle() {
  const auto bound = bridge::BindMarriageRankedContainerAdapterEnvironmentV1(
      0x10000000U, true,
      bridge::kMarriageProposalNativeBinderExecutableSha256V1);
  assert(reinterpret_cast<std::uintptr_t>(bound.enumerate_candidates) ==
         0x10000000U + bridge::kMarriageCandidateEnumeratorRvaV1);
  assert(bound.candidate_owner_vtable ==
         0x10000000U + bridge::kMarriageCandidateOwnerVtableRvaV1);

  Fixture fixture{};
  bridge::MarriageRankedContainerAdapterStateV1 state{};
  InitializeState(fixture, state);
  bridge::MarriageProposalNativeBinderStateV1 binder{};
  assert(bridge::ConfigureMarriageRankedContainerAdapterV1(state, binder));
  assert(binder.environment.ranked_container_lifecycle_certified &&
         binder.environment.source_adapter.invoke_ranked_source ==
             &bridge::InvokeMarriageRankedContainerExactV1);

  std::uintptr_t token = 0;
  assert(bridge::InvokeMarriageRankedContainerExactV1(
      &state, Request(fixture), token));
  assert(token != 0 && fixture.enumerate_calls == 1 &&
         fixture.score_calls == 1 && fixture.observed_cap == 77 &&
         fixture.observed_young);
  bridge::MarriageNativeRankedContainerViewV1 view{};
  assert(bridge::ReadMarriageRankedContainerViewExactV1(&state, token, view));
  assert(view.count == 2 && view.capacity == 32 && view.row_data != 0);
  std::int32_t first_id = 0;
  std::int32_t first_score = 0;
  std::memcpy(&first_id,
              reinterpret_cast<const void *>(
                  view.row_data +
                  bridge::kMarriageNativeRankedRowCharacterIdOffsetV1),
              sizeof(first_id));
  std::memcpy(&first_score,
              reinterpret_cast<const void *>(
                  view.row_data + bridge::kMarriageNativeRankedRowScoreOffsetV1),
              sizeof(first_score));
  assert(first_id == 0x01000001 && first_score == 500);
  bridge::ReleaseMarriageRankedContainerExactV1(&state, token);
  assert(fixture.scored_reset_calls == 2 && fixture.destroyed_rows == 2 &&
         fixture.release_calls == 3);
}

void TestInvocationAndShaFailClosed() {
  Fixture fixture{};
  bridge::MarriageRankedContainerAdapterStateV1 state{};
  InitializeState(fixture, state);
  auto request = Request(fixture);
  request.entry_points.enumerate_candidates ^= 1;
  std::uintptr_t token = 9;
  assert(!bridge::InvokeMarriageRankedContainerExactV1(&state, request,
                                                       token));
  assert(token == 0 && fixture.enumerate_calls == 0);
  state.environment.admitted_executable_sha256 = "wrong";
  request = Request(fixture);
  assert(!bridge::InvokeMarriageRankedContainerExactV1(&state, request,
                                                       token));
  assert(bridge::ReadMarriageRankedContainerAdapterFailureV1(state) ==
         bridge::MarriageRankedContainerAdapterFailureV1::
             exact_build_not_admitted);
}

} // namespace

int main() {
  TestBindingAndCompleteLifecycle();
  TestInvocationAndShaFailClosed();
  std::cout << "marriage ranked container adapter v1 tests passed\n";
  return 0;
}
