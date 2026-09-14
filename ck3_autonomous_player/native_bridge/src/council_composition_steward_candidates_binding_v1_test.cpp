#include "xar_bridge/council_composition_steward_candidates_binding_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string_view>
#include <vector>

namespace {

using namespace xar::ck3_11906;
using Failure = xar::game::CouncilCompositionStewardCandidatesFailureV1;
using Result = xar::game::ReadCouncilCompositionStewardCandidatesResultV1;

constexpr std::uintptr_t kModuleBase = 0x0000000140000000ULL;
constexpr std::int32_t kOwnerId = 29829;
constexpr std::int32_t kTaskId = 7159;
constexpr std::uintptr_t kActiveTaskStorageSlotRva = 0x570C778;
constexpr std::uintptr_t kActiveTaskFallbackSlotRva = 0x570C6D8;

template <typename Value, std::size_t Size>
void Put(std::array<std::byte, Size> &storage, std::size_t offset,
         const Value &value) {
  assert(offset + sizeof(value) <= storage.size());
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

struct TestContext {
  xar::ck3_11906::CouncilCompositionStewardCandidatesFrameV1 frame{};
  bool main_thread = true;
  bool wrong_position = false;
  bool producer_failure = false;
  bool release_failure = false;
  bool corrupt_task_identity = false;
  int capture_count = 0;
  int initialize_count = 0;
  int producer_count = 0;
  int release_count = 0;

  std::array<std::byte, 0x300> owner{};
  std::array<std::byte, 0x280> land_state{};
  std::array<std::byte, 0x80> task{};
  std::array<std::byte, 0x80> task_type{};
  std::array<std::byte, 0x80> position_type{};
  std::array<std::byte, 0x40> task_storage{};
  std::array<std::byte, 0x20> fallback_task{};
  std::vector<std::byte> task_slots;
  std::array<std::int32_t, 1> active_task_ids{kTaskId};

  std::array<std::array<std::byte, 0x30>, 3> candidates{};
  std::array<std::int32_t, 3> candidate_ids{33888, 30784, 33437};
  std::array<std::uintptr_t, 3> candidate_pointers{};

  TestContext() : task_slots((static_cast<std::size_t>(kTaskId) + 1U) * 0x10) {
    const std::string_view snapshot = "fixture:7";
    std::memcpy(frame.snapshot_id.data(), snapshot.data(), snapshot.size());
    frame.public_revision = 7;
    frame.native_revision = 11;
    frame.date_raw = 53178264;
    frame.paused = true;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_alive = true;
    frame.played_character_id = kOwnerId;
    frame.played_character = reinterpret_cast<std::uintptr_t>(owner.data());

    Put(owner, 0x18, kOwnerId);
    void *land = land_state.data();
    Put(owner, 0x1B8, land);
    void *ids = active_task_ids.data();
    Put(land_state, 0x230, ids);
    const std::int32_t active_count = 1;
    Put(land_state, 0x23C, active_count);

    Put(task, 0x10, kTaskId);
    void *type = task_type.data();
    Put(task, 0x18, type);
    Put(task, 0x3C, kOwnerId);
    void *position = position_type.data();
    Put(task_type, 0x38, position);

    void *slot_data = task_slots.data();
    Put(task_storage, 0x20, slot_data);
    const std::int32_t capacity = kTaskId + 1;
    Put(task_storage, 0x2C, capacity);
    void *task_pointer = task.data();
    std::memcpy(task_slots.data() + static_cast<std::size_t>(kTaskId) * 0x10 +
                    0x08,
                &task_pointer, sizeof(task_pointer));

    for (std::size_t index = 0; index < candidates.size(); ++index) {
      Put(candidates[index], 0x18, candidate_ids[index]);
      candidate_pointers[index] =
          reinterpret_cast<std::uintptr_t>(candidates[index].data());
    }
  }
};

bool CaptureFrame(void *context,
                  CouncilCompositionStewardCandidatesFrameV1 &output) noexcept {
  auto &test = *static_cast<TestContext *>(context);
  ++test.capture_count;
  output = test.frame;
  return true;
}

bool IsMainThread(void *context) noexcept {
  return static_cast<TestContext *>(context)->main_thread;
}

bool ReadMemory(void *context, const void *address, void *output,
                std::size_t size) noexcept {
  auto &test = *static_cast<TestContext *>(context);
  const auto numeric = reinterpret_cast<std::uintptr_t>(address);
  if (numeric == kModuleBase + kActiveTaskStorageSlotRva) {
    void *storage = test.task_storage.data();
    std::memcpy(output, &storage, size);
    return size == sizeof(storage);
  }
  if (numeric == kModuleBase + kActiveTaskFallbackSlotRva) {
    void *fallback = test.fallback_task.data();
    std::memcpy(output, &fallback, size);
    return size == sizeof(fallback);
  }
  if (address == nullptr || output == nullptr || size == 0)
    return false;
  std::memcpy(output, address, size);
  return true;
}

bool ReadStableKey(void *context, const void *native_string, char *output,
                   std::size_t output_capacity) noexcept {
  auto &test = *static_cast<TestContext *>(context);
  if (native_string != test.position_type.data() + 0x18 || output == nullptr) {
    return false;
  }
  const std::string_view key =
      test.wrong_position
          ? std::string_view{"councillor_marshal"}
          : kCouncilCompositionStewardCandidatesReaderPositionKeyV1;
  if (key.size() >= output_capacity)
    return false;
  std::memcpy(output, key.data(), key.size());
  output[key.size()] = '\0';
  return true;
}

bool ResolveCharacter(void *context, std::uintptr_t module_base,
                      std::int32_t full_id,
                      std::uintptr_t &character) noexcept {
  auto &test = *static_cast<TestContext *>(context);
  character = 0;
  if (module_base != kModuleBase)
    return false;
  if (full_id == kOwnerId) {
    character = reinterpret_cast<std::uintptr_t>(test.owner.data());
    return true;
  }
  for (std::size_t index = 0; index < test.candidate_ids.size(); ++index) {
    if (test.candidate_ids[index] == full_id) {
      character = test.candidate_pointers[index];
      return true;
    }
  }
  return false;
}

bool InitializeVector(
    void *context, std::uintptr_t module_base, void *allocator_storage,
    std::size_t allocator_storage_size,
    CouncilCompositionStewardCandidatesBindingNativeVectorV1 &vector) noexcept {
  auto &test = *static_cast<TestContext *>(context);
  ++test.initialize_count;
  if (module_base != kModuleBase || allocator_storage == nullptr ||
      allocator_storage_size !=
          kCouncilCompositionStewardInlineAllocatorSizeV1) {
    return false;
  }
  vector = {};
  vector.data_address =
      reinterpret_cast<std::uintptr_t>(allocator_storage) + 8U;
  vector.capacity = kCouncilCompositionStewardInlineCandidateCapacityV1;
  vector.allocator = allocator_storage;
  return true;
}

bool InvokeProducer(
    void *context, std::uintptr_t module_base, std::uintptr_t owner_character,
    std::uintptr_t active_task, bool gui_eligibility_mode,
    CouncilCompositionStewardCandidatesBindingNativeVectorV1 &vector) noexcept {
  auto &test = *static_cast<TestContext *>(context);
  ++test.producer_count;
  if (module_base != kModuleBase ||
      owner_character != reinterpret_cast<std::uintptr_t>(test.owner.data()) ||
      active_task != reinterpret_cast<std::uintptr_t>(test.task.data()) ||
      !gui_eligibility_mode || vector.allocator == nullptr) {
    return false;
  }
  if (test.producer_failure)
    return false;
  vector.data_address =
      reinterpret_cast<std::uintptr_t>(test.candidate_pointers.data());
  vector.capacity = kCouncilCompositionStewardInlineCandidateCapacityV1;
  vector.count = static_cast<std::int32_t>(test.candidate_pointers.size());
  return true;
}

bool ReleaseAllocation(void *context, std::uintptr_t module_base,
                       void *allocator, std::uintptr_t data_address,
                       std::size_t element_size) noexcept {
  auto &test = *static_cast<TestContext *>(context);
  ++test.release_count;
  return module_base == kModuleBase && allocator != nullptr &&
         data_address != 0 && element_size == sizeof(std::uintptr_t) &&
         !test.release_failure;
}

CouncilCompositionStewardCandidatesBindingEnvironmentV1
Binding(TestContext &test) {
  CouncilCompositionStewardCandidatesBindingEnvironmentV1 result{};
  result.binding_enabled = true;
  result.exact_build_admitted = true;
  result.admitted_executable_sha256 =
      kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  result.offline_fixture = true;
  result.module_base = kModuleBase;
  result.operation_context = &test;
  result.operations = {&ReadMemory,       &ReadStableKey,  &ResolveCharacter,
                       &InitializeVector, &InvokeProducer, &ReleaseAllocation};
  return result;
}

struct BoundFixture {
  CouncilCompositionStewardCandidatesEnvironmentV1 environment{};
  CouncilCompositionStewardCandidatesAccessV1 access{};
  CouncilCompositionStewardCandidatesBindingStateV1 state{};

  explicit BoundFixture(TestContext &test) {
    access.context = &test;
    access.capture_frame = &CaptureFrame;
    access.is_main_thread = &IsMainThread;
    assert(BindCouncilCompositionStewardCandidatesV1(Binding(test), state,
                                                     environment, access));
  }
};

CouncilCompositionStewardCandidatesRequestV1 Request() {
  CouncilCompositionStewardCandidatesRequestV1 request{};
  request.expected_snapshot_id = "fixture:7";
  request.expected_public_revision = 7;
  request.expected_native_revision = 11;
  request.expected_date_raw = 53178264;
  request.expected_owner_character_id = kOwnerId;
  return request;
}

void ExpectUnavailable(
    const xar::game::CouncilCompositionStewardCandidatesV1 &output,
    Failure reason, bool released) {
  assert(output.status ==
         xar::game::CouncilCompositionStewardCandidatesStatusV1::unavailable);
  assert(output.unavailable_reason == reason);
  assert(output.candidate_count == 0);
  assert(output.temporary_vector_released == released);
}

} // namespace

int main() {
  {
    TestContext test;
    BoundFixture bound(test);
    xar::game::CouncilCompositionStewardCandidatesV1 output{};
    assert(ReadCouncilCompositionStewardCandidatesV1(
               bound.environment, bound.access, Request(), output) ==
           Result::available);
    assert(output.candidate_count == 3);
    assert(output.candidates[0].character_id == 30784);
    assert(output.candidates[0].native_collection_ordinal == 1);
    assert(output.candidates[1].character_id == 33437);
    assert(output.candidates[1].native_collection_ordinal == 2);
    assert(output.candidates[2].character_id == 33888);
    assert(output.candidates[2].native_collection_ordinal == 0);
    assert(output.temporary_vector_released);
    assert(test.capture_count == 2);
    assert(test.initialize_count == 1);
    assert(test.producer_count == 1);
    assert(test.release_count == 1);
    assert(!bound.state.transaction_active);
  }

  {
    TestContext test;
    test.wrong_position = true;
    BoundFixture bound(test);
    xar::game::CouncilCompositionStewardCandidatesV1 output{};
    assert(ReadCouncilCompositionStewardCandidatesV1(
               bound.environment, bound.access, Request(), output) ==
           Result::unavailable);
    ExpectUnavailable(output, Failure::active_steward_task_unavailable, false);
    assert(test.producer_count == 0);
    assert(test.release_count == 0);
  }

  {
    TestContext test;
    test.corrupt_task_identity = true;
    const std::int32_t corrupt = kTaskId + 1;
    Put(test.task, 0x10, corrupt);
    BoundFixture bound(test);
    xar::game::CouncilCompositionStewardCandidatesV1 output{};
    assert(ReadCouncilCompositionStewardCandidatesV1(
               bound.environment, bound.access, Request(), output) ==
           Result::unavailable);
    ExpectUnavailable(output, Failure::active_steward_task_unavailable, false);
  }

  {
    TestContext test;
    test.producer_failure = true;
    BoundFixture bound(test);
    xar::game::CouncilCompositionStewardCandidatesV1 output{};
    assert(ReadCouncilCompositionStewardCandidatesV1(
               bound.environment, bound.access, Request(), output) ==
           Result::unavailable);
    ExpectUnavailable(output, Failure::candidate_collection_unavailable, true);
    assert(test.producer_count == 1);
    assert(test.release_count == 1);
  }

  {
    TestContext test;
    test.release_failure = true;
    BoundFixture bound(test);
    xar::game::CouncilCompositionStewardCandidatesV1 output{};
    assert(ReadCouncilCompositionStewardCandidatesV1(
               bound.environment, bound.access, Request(), output) ==
           Result::unavailable);
    ExpectUnavailable(output, Failure::temporary_vector_release_failed, false);
    assert(test.release_count == 1);
  }

  {
    TestContext test;
    test.main_thread = false;
    BoundFixture bound(test);
    xar::game::CouncilCompositionStewardCandidatesV1 output{};
    assert(ReadCouncilCompositionStewardCandidatesV1(
               bound.environment, bound.access, Request(), output) ==
           Result::unavailable);
    ExpectUnavailable(output, Failure::application_main_thread_required, false);
    assert(test.capture_count == 0);
  }

  {
    TestContext test;
    test.frame.paused = false;
    BoundFixture bound(test);
    xar::game::CouncilCompositionStewardCandidatesV1 output{};
    assert(ReadCouncilCompositionStewardCandidatesV1(
               bound.environment, bound.access, Request(), output) ==
           Result::unavailable);
    ExpectUnavailable(output, Failure::not_paused, false);
    assert(test.producer_count == 0);
  }

  {
    TestContext test;
    auto binding = Binding(test);
    binding.admitted_executable_sha256 = "wrong";
    CouncilCompositionStewardCandidatesEnvironmentV1 environment{};
    CouncilCompositionStewardCandidatesAccessV1 access{};
    access.context = &test;
    access.capture_frame = &CaptureFrame;
    access.is_main_thread = &IsMainThread;
    CouncilCompositionStewardCandidatesBindingStateV1 state{};
    assert(!BindCouncilCompositionStewardCandidatesV1(binding, state,
                                                      environment, access));
    assert(!state.attached);
    assert(access.context == &test);
  }

  return 0;
}
