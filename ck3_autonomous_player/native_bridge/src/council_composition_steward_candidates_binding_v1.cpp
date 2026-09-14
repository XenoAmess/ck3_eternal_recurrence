#include "xar_bridge/council_composition_steward_candidates_binding_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kCharacterStorageSlotRva = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackSlotRva = 0x570C138;
constexpr std::uintptr_t kActiveTaskStorageSlotRva = 0x570C778;
constexpr std::uintptr_t kActiveTaskFallbackSlotRva = 0x570C6D8;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterLandStateOffset = 0x1B8;
constexpr std::size_t kLandStateActiveTaskIdsOffset = 0x230;
constexpr std::size_t kLandStateActiveTaskCountOffset = 0x23C;
constexpr std::size_t kActiveTaskIdentityOffset = 0x10;
constexpr std::size_t kActiveTaskTypeOffset = 0x18;
constexpr std::size_t kActiveTaskScopesOffset = 0x38;
constexpr std::size_t kActiveTaskOwnerIdOffset = kActiveTaskScopesOffset + 0x04;
constexpr std::size_t kTaskTypePositionTypeOffset = 0x38;
constexpr std::size_t kPositionTypeKeyOffset = 0x18;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 0x0F;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;
constexpr std::int32_t kMaximumActiveTasks = 4'096;
constexpr std::size_t kMaximumCandidateSpanBytes =
    game::kCouncilCompositionStewardCandidatesMaximumRowsV1 *
    sizeof(std::uintptr_t);

static_assert(sizeof(void *) == 8, "council composition binding is x64-only");
static_assert(offsetof(CouncilCompositionStewardCandidatesBindingNativeVectorV1,
                       data_address) == 0x00);
static_assert(offsetof(CouncilCompositionStewardCandidatesBindingNativeVectorV1,
                       capacity) == 0x08);
static_assert(offsetof(CouncilCompositionStewardCandidatesBindingNativeVectorV1,
                       count) == 0x0C);
static_assert(offsetof(CouncilCompositionStewardCandidatesBindingNativeVectorV1,
                       allocator) == 0x10);
static_assert(
    sizeof(CouncilCompositionStewardCandidatesBindingNativeVectorV1) == 0x18);

void *AlignedAllocator(
    CouncilCompositionStewardCandidatesBindingStateV1 &state) noexcept {
  const auto address =
      reinterpret_cast<std::uintptr_t>(state.allocator_storage.data());
  return reinterpret_cast<void *>((address + 15U) & ~std::uintptr_t{15U});
}

bool CheckedAddress(const void *base, std::size_t offset,
                    const void *&output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - address) {
    output = nullptr;
    return false;
  }
  output = reinterpret_cast<const void *>(address + offset);
  return true;
}

bool DirectReadMemory(void *, const void *address, void *output,
                      std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0)
    return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

template <typename Value>
bool Read(const CouncilCompositionStewardCandidatesBindingStateV1 &state,
          const void *base, std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         state.operations.read_memory(state.operation_context, address, &output,
                                      sizeof(output));
}

bool DefaultReadStableKey(void *, const void *native_string, char *output,
                          std::size_t output_capacity) noexcept {
  if (native_string == nullptr || output == nullptr || output_capacity < 2) {
    return false;
  }
  output[0] = '\0';
  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!DirectReadMemory(nullptr,
                        static_cast<const std::byte *>(native_string) +
                            kMsvcStringSizeOffset,
                        &size, sizeof(size)) ||
      !DirectReadMemory(nullptr,
                        static_cast<const std::byte *>(native_string) +
                            kMsvcStringCapacityOffset,
                        &capacity, sizeof(capacity)) ||
      size == 0 || size > capacity || size >= output_capacity) {
    return false;
  }
  const void *bytes = native_string;
  if (capacity > kMsvcStringInlineCapacity &&
      (!DirectReadMemory(nullptr, native_string, &bytes, sizeof(bytes)) ||
       bytes == nullptr)) {
    return false;
  }
  if (!DirectReadMemory(nullptr, bytes, output, size))
    return false;
  output[size] = '\0';
  return std::none_of(output, output + size, [](unsigned char value) {
    return value == 0 || value < 0x20U;
  });
}

bool ResolveComponent(
    const CouncilCompositionStewardCandidatesBindingStateV1 &state,
    std::uintptr_t storage_slot_rva, std::uintptr_t fallback_slot_rva,
    std::int32_t full_id, std::size_t identity_offset,
    std::uintptr_t &object) noexcept {
  object = 0;
  if (state.module_base == 0 || full_id <= 0)
    return false;
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!state.operations.read_memory(
          state.operation_context,
          reinterpret_cast<const void *>(state.module_base + storage_slot_rva),
          &storage, sizeof(storage)) ||
      !state.operations.read_memory(
          state.operation_context,
          reinterpret_cast<const void *>(state.module_base + fallback_slot_rva),
          &fallback, sizeof(fallback)) ||
      storage == nullptr) {
    return false;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!Read(state, storage, kStorageSlotsOffset, slots) ||
      !Read(state, storage, kStorageCapacityOffset, capacity) ||
      slots == nullptr || capacity <= 0 || capacity > kMaximumComponentSlots) {
    return false;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity))
    return false;
  void *candidate = nullptr;
  std::int32_t observed_id = -1;
  if (!Read(state, slots,
            static_cast<std::size_t>(index) * kStorageSlotStride +
                kStorageObjectOffset,
            candidate) ||
      candidate == nullptr || candidate == fallback ||
      !Read(state, candidate, identity_offset, observed_id) ||
      observed_id != full_id) {
    return false;
  }
  object = reinterpret_cast<std::uintptr_t>(candidate);
  return true;
}

bool DefaultResolveCharacter(void *, std::uintptr_t module_base,
                             std::int32_t full_id,
                             std::uintptr_t &character) noexcept {
  character = 0;
  if (module_base == 0 || full_id <= 0)
    return false;
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!DirectReadMemory(nullptr,
                        reinterpret_cast<const void *>(
                            module_base + kCharacterStorageSlotRva),
                        &storage, sizeof(storage)) ||
      !DirectReadMemory(nullptr,
                        reinterpret_cast<const void *>(
                            module_base + kCharacterFallbackSlotRva),
                        &fallback, sizeof(fallback)) ||
      storage == nullptr) {
    return false;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!DirectReadMemory(nullptr,
                        static_cast<const std::byte *>(storage) +
                            kStorageSlotsOffset,
                        &slots, sizeof(slots)) ||
      !DirectReadMemory(nullptr,
                        static_cast<const std::byte *>(storage) +
                            kStorageCapacityOffset,
                        &capacity, sizeof(capacity)) ||
      slots == nullptr || capacity <= 0 || capacity > kMaximumComponentSlots) {
    return false;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity))
    return false;
  void *candidate = nullptr;
  std::int32_t observed_id = -1;
  if (!DirectReadMemory(nullptr,
                        static_cast<const std::byte *>(slots) +
                            static_cast<std::size_t>(index) *
                                kStorageSlotStride +
                            kStorageObjectOffset,
                        &candidate, sizeof(candidate)) ||
      candidate == nullptr || candidate == fallback ||
      !DirectReadMemory(nullptr,
                        static_cast<const std::byte *>(candidate) +
                            kCharacterIdentityOffset,
                        &observed_id, sizeof(observed_id)) ||
      observed_id != full_id) {
    return false;
  }
  character = reinterpret_cast<std::uintptr_t>(candidate);
  return true;
}

#if defined(_MSC_VER)
#define XAR_COUNCIL_BINDING_FASTCALL __fastcall
#else
#define XAR_COUNCIL_BINDING_FASTCALL
#endif

using NativeInitializeVector = void(XAR_COUNCIL_BINDING_FASTCALL *)(
    void *allocator, std::uintptr_t *data_address, std::int32_t *capacity);
using NativeProduceCandidates = void(XAR_COUNCIL_BINDING_FASTCALL *)(
    void *owner_character, void *active_task, bool gui_eligibility_mode,
    CouncilCompositionStewardCandidatesBindingNativeVectorV1 *vector);
using NativeReleaseAllocation = void(XAR_COUNCIL_BINDING_FASTCALL *)(
    void *allocator, void *data, std::size_t element_size);

#undef XAR_COUNCIL_BINDING_FASTCALL

bool DefaultInitializeVector(
    void *, std::uintptr_t module_base, void *allocator_storage,
    std::size_t allocator_storage_size,
    CouncilCompositionStewardCandidatesBindingNativeVectorV1 &vector) noexcept {
  if (module_base == 0 || allocator_storage == nullptr ||
      allocator_storage_size <
          kCouncilCompositionStewardInlineAllocatorSizeV1) {
    return false;
  }
  std::memset(allocator_storage, 0,
              kCouncilCompositionStewardInlineAllocatorSizeV1);
  const auto vtable =
      module_base + kCouncilCompositionStewardInlineAllocatorVtableRvaV1;
  const auto fallback =
      module_base + kCouncilCompositionStewardInlineAllocatorFallbackRvaV1;
  std::memcpy(allocator_storage, &vtable, sizeof(vtable));
  std::memcpy(static_cast<std::byte *>(allocator_storage) +
                  kCouncilCompositionStewardInlineAllocatorFallbackOffsetV1,
              &fallback, sizeof(fallback));
  vector = {};
  vector.allocator = allocator_storage;
#if defined(_MSC_VER)
  __try {
    reinterpret_cast<NativeInitializeVector>(
        module_base + kCouncilCompositionStewardInlineAllocatorInitializeRvaV1)(
        allocator_storage, &vector.data_address, &vector.capacity);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    vector = {};
    return false;
  }
#else
  reinterpret_cast<NativeInitializeVector>(
      module_base + kCouncilCompositionStewardInlineAllocatorInitializeRvaV1)(
      allocator_storage, &vector.data_address, &vector.capacity);
#endif
  return vector.data_address ==
             reinterpret_cast<std::uintptr_t>(allocator_storage) + 8U &&
         vector.capacity ==
             kCouncilCompositionStewardInlineCandidateCapacityV1 &&
         vector.count == 0;
}

bool DefaultInvokeProducer(
    void *, std::uintptr_t module_base, std::uintptr_t owner_character,
    std::uintptr_t active_task, bool gui_eligibility_mode,
    CouncilCompositionStewardCandidatesBindingNativeVectorV1 &vector) noexcept {
  if (module_base == 0 || owner_character == 0 || active_task == 0 ||
      vector.allocator == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    reinterpret_cast<NativeProduceCandidates>(
        module_base + kCouncilCompositionStewardCandidatesProducerRvaV1)(
        reinterpret_cast<void *>(owner_character),
        reinterpret_cast<void *>(active_task), gui_eligibility_mode, &vector);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  reinterpret_cast<NativeProduceCandidates>(
      module_base + kCouncilCompositionStewardCandidatesProducerRvaV1)(
      reinterpret_cast<void *>(owner_character),
      reinterpret_cast<void *>(active_task), gui_eligibility_mode, &vector);
  return true;
#endif
}

bool DefaultReleaseAllocation(void *, std::uintptr_t module_base,
                              void *allocator, std::uintptr_t data_address,
                              std::size_t element_size) noexcept {
  if (module_base == 0 || allocator == nullptr || data_address == 0 ||
      element_size != sizeof(std::uintptr_t)) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    reinterpret_cast<NativeReleaseAllocation>(
        module_base + kCouncilCompositionStewardInlineAllocatorReleaseRvaV1)(
        allocator, reinterpret_cast<void *>(data_address), element_size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  reinterpret_cast<NativeReleaseAllocation>(
      module_base + kCouncilCompositionStewardInlineAllocatorReleaseRvaV1)(
      allocator, reinterpret_cast<void *>(data_address), element_size);
  return true;
#endif
}

CouncilCompositionStewardCandidatesBindingOperationsV1
DefaultOperations() noexcept {
  return {&DirectReadMemory,        &DefaultReadStableKey,
          &DefaultResolveCharacter, &DefaultInitializeVector,
          &DefaultInvokeProducer,   &DefaultReleaseAllocation};
}

bool OperationsComplete(
    const CouncilCompositionStewardCandidatesBindingOperationsV1 &ops) {
  return ops.read_memory != nullptr && ops.read_stable_key != nullptr &&
         ops.resolve_character != nullptr && ops.initialize_vector != nullptr &&
         ops.invoke_producer != nullptr && ops.release_allocation != nullptr;
}

bool AnyOperationOverride(
    const CouncilCompositionStewardCandidatesBindingOperationsV1 &ops) {
  return ops.read_memory != nullptr || ops.read_stable_key != nullptr ||
         ops.resolve_character != nullptr || ops.initialize_vector != nullptr ||
         ops.invoke_producer != nullptr || ops.release_allocation != nullptr;
}

bool ResolveActiveStewardTask(
    CouncilCompositionStewardCandidatesBindingStateV1 &state,
    CouncilCompositionStewardCandidatesFrameV1 &frame) noexcept {
  frame.active_task_id = -1;
  frame.active_task = 0;
  frame.active_task_identity_round_trip = false;
  frame.position_key.fill('\0');

  std::uintptr_t resolved_owner = 0;
  frame.played_character_identity_round_trip =
      frame.played_character_id > 0 && frame.played_character != 0 &&
      state.operations.resolve_character(
          state.operation_context, state.module_base, frame.played_character_id,
          resolved_owner) &&
      resolved_owner == frame.played_character;
  if (!frame.played_character_identity_round_trip || !frame.paused) {
    return true;
  }

  void *land_state = nullptr;
  void *active_task_ids = nullptr;
  std::int32_t active_task_count = 0;
  if (!Read(state, reinterpret_cast<const void *>(frame.played_character),
            kCharacterLandStateOffset, land_state) ||
      land_state == nullptr ||
      !Read(state, land_state, kLandStateActiveTaskIdsOffset,
            active_task_ids) ||
      !Read(state, land_state, kLandStateActiveTaskCountOffset,
            active_task_count) ||
      active_task_count < 0 || active_task_count > kMaximumActiveTasks ||
      (active_task_count > 0 && active_task_ids == nullptr)) {
    return true;
  }

  std::int32_t matched_id = -1;
  std::uintptr_t matched_task = 0;
  for (std::int32_t index = 0; index < active_task_count; ++index) {
    std::int32_t task_id = -1;
    if (!Read(state, active_task_ids,
              static_cast<std::size_t>(index) * sizeof(task_id), task_id)) {
      return true;
    }
    std::uintptr_t active_task = 0;
    if (!ResolveComponent(state, kActiveTaskStorageSlotRva,
                          kActiveTaskFallbackSlotRva, task_id,
                          kActiveTaskIdentityOffset, active_task)) {
      return true;
    }
    void *task_type = nullptr;
    void *position_type = nullptr;
    std::int32_t owner_id = -1;
    const void *position_key = nullptr;
    std::array<char, game::kCouncilCompositionStewardPositionKeyCapacityV1>
        key{};
    if (!Read(state, reinterpret_cast<const void *>(active_task),
              kActiveTaskTypeOffset, task_type) ||
        task_type == nullptr ||
        !Read(state, task_type, kTaskTypePositionTypeOffset, position_type) ||
        position_type == nullptr ||
        !CheckedAddress(position_type, kPositionTypeKeyOffset, position_key) ||
        !state.operations.read_stable_key(state.operation_context, position_key,
                                          key.data(), key.size()) ||
        !Read(state, reinterpret_cast<const void *>(active_task),
              kActiveTaskOwnerIdOffset, owner_id)) {
      return true;
    }
    if (std::string_view(key.data()) !=
            kCouncilCompositionStewardCandidatesReaderPositionKeyV1 ||
        owner_id != frame.played_character_id) {
      continue;
    }
    if (matched_task != 0) {
      return true;
    }
    matched_id = task_id;
    matched_task = active_task;
  }

  if (matched_task == 0)
    return true;
  frame.active_task_id = matched_id;
  frame.active_task = matched_task;
  frame.active_task_identity_round_trip = true;
  std::copy(kCouncilCompositionStewardCandidatesReaderPositionKeyV1.begin(),
            kCouncilCompositionStewardCandidatesReaderPositionKeyV1.end(),
            frame.position_key.begin());
  return true;
}

bool IsMainThreadThunk(void *context) noexcept {
  auto &state =
      *static_cast<CouncilCompositionStewardCandidatesBindingStateV1 *>(
          context);
  return state.attached && state.upstream_is_main_thread != nullptr &&
         state.upstream_is_main_thread(state.upstream_context);
}

bool CaptureFrameThunk(
    void *context,
    CouncilCompositionStewardCandidatesFrameV1 &output) noexcept {
  auto &state =
      *static_cast<CouncilCompositionStewardCandidatesBindingStateV1 *>(
          context);
  if (!state.attached || state.transaction_active ||
      state.upstream_capture_frame == nullptr ||
      !state.upstream_capture_frame(state.upstream_context, output) ||
      !ResolveActiveStewardTask(state, output)) {
    return false;
  }
  state.bound_frame = output;
  state.frame_bound = output.paused &&
                      output.played_character_identity_round_trip &&
                      output.active_task_identity_round_trip;
  return true;
}

bool ProduceThunk(
    void *context, std::uintptr_t owner_character, std::uintptr_t active_task,
    bool gui_eligibility_mode,
    CouncilCompositionStewardNativeCandidateVectorV1 &output) noexcept {
  auto &state =
      *static_cast<CouncilCompositionStewardCandidatesBindingStateV1 *>(
          context);
  output = {};
  if (!state.attached || !state.frame_bound || state.transaction_active ||
      !gui_eligibility_mode || owner_character == 0 || active_task == 0 ||
      owner_character != state.bound_frame.played_character ||
      active_task != state.bound_frame.active_task ||
      !IsMainThreadThunk(&state)) {
    return false;
  }
  state.allocator_storage.fill(std::byte{0});
  state.native_vector = {};
  state.transaction_active = true;
  state.vector_initialized = state.operations.initialize_vector(
      state.operation_context, state.module_base, AlignedAllocator(state),
      kCouncilCompositionStewardInlineAllocatorSizeV1, state.native_vector);
  if (!state.vector_initialized ||
      state.native_vector.allocator != AlignedAllocator(state)) {
    state.vector_initialized = false;
    return false;
  }
  state.producer_invoked = state.operations.invoke_producer(
      state.operation_context, state.module_base, owner_character, active_task,
      gui_eligibility_mode, state.native_vector);
  output.data_address = state.native_vector.data_address;
  output.capacity = state.native_vector.capacity;
  output.count = state.native_vector.count;
  return state.producer_invoked;
}

bool ReleaseThunk(
    void *context,
    CouncilCompositionStewardNativeCandidateVectorV1 &vector) noexcept {
  auto &state =
      *static_cast<CouncilCompositionStewardCandidatesBindingStateV1 *>(
          context);
  if (!state.attached || !state.transaction_active ||
      vector.data_address != state.native_vector.data_address ||
      vector.capacity != state.native_vector.capacity ||
      vector.count != state.native_vector.count) {
    return false;
  }
  const bool initialized = state.vector_initialized;
  const auto data_address = state.native_vector.data_address;
  void *const allocator = state.native_vector.allocator;
  state.transaction_active = false;
  state.frame_bound = false;
  state.vector_initialized = false;
  state.producer_invoked = false;
  state.native_vector = {};
  vector = {};
  if (!initialized || data_address == 0)
    return true;
  return state.operations.release_allocation(
      state.operation_context, state.module_base, allocator, data_address,
      sizeof(std::uintptr_t));
}

bool CandidateSpanReadableThunk(void *context, std::uintptr_t address,
                                std::size_t size) noexcept {
  auto &state =
      *static_cast<CouncilCompositionStewardCandidatesBindingStateV1 *>(
          context);
  std::array<std::byte, kMaximumCandidateSpanBytes> bytes{};
  return state.attached && state.transaction_active && address != 0 &&
         size > 0 && size <= bytes.size() &&
         state.operations.read_memory(state.operation_context,
                                      reinterpret_cast<const void *>(address),
                                      bytes.data(), size);
}

bool ReadCandidatePointerThunk(void *context, std::uintptr_t address,
                               std::uintptr_t &candidate) noexcept {
  auto &state =
      *static_cast<CouncilCompositionStewardCandidatesBindingStateV1 *>(
          context);
  candidate = 0;
  return state.attached && state.transaction_active && address != 0 &&
         state.operations.read_memory(state.operation_context,
                                      reinterpret_cast<const void *>(address),
                                      &candidate, sizeof(candidate));
}

bool ReadCandidateIdThunk(void *context, std::uintptr_t candidate,
                          std::int32_t &character_id) noexcept {
  auto &state =
      *static_cast<CouncilCompositionStewardCandidatesBindingStateV1 *>(
          context);
  character_id = -1;
  const void *address = nullptr;
  return state.attached && state.transaction_active && candidate != 0 &&
         CheckedAddress(reinterpret_cast<const void *>(candidate),
                        kCharacterIdentityOffset, address) &&
         state.operations.read_memory(state.operation_context, address,
                                      &character_id, sizeof(character_id));
}

bool ResolveCandidateThunk(void *context, std::int32_t character_id,
                           std::uintptr_t &candidate) noexcept {
  auto &state =
      *static_cast<CouncilCompositionStewardCandidatesBindingStateV1 *>(
          context);
  candidate = 0;
  return state.attached && state.transaction_active && character_id > 0 &&
         state.operations.resolve_character(state.operation_context,
                                            state.module_base, character_id,
                                            candidate);
}

} // namespace

bool BindCouncilCompositionStewardCandidatesV1(
    const CouncilCompositionStewardCandidatesBindingEnvironmentV1 &binding,
    CouncilCompositionStewardCandidatesBindingStateV1 &state,
    CouncilCompositionStewardCandidatesEnvironmentV1 &core_environment,
    CouncilCompositionStewardCandidatesAccessV1 &core_access) noexcept {
  if (!binding.binding_enabled || !binding.exact_build_admitted ||
      binding.admitted_executable_sha256 !=
          kCouncilCompositionStewardCandidatesReaderExecutableSha256V1 ||
      binding.module_base == 0 || state.attached ||
      core_access.context == &state || core_access.capture_frame == nullptr ||
      core_access.is_main_thread == nullptr) {
    return false;
  }

  CouncilCompositionStewardCandidatesBindingOperationsV1 operations{};
  if (binding.offline_fixture) {
    operations = binding.operations;
  } else {
    if (binding.operation_context != nullptr ||
        AnyOperationOverride(binding.operations)) {
      return false;
    }
    operations = DefaultOperations();
  }
  if (!OperationsComplete(operations))
    return false;

  CouncilCompositionStewardCandidatesBindingStateV1 next{};
  next.module_base = binding.module_base;
  next.operation_context = binding.operation_context;
  next.operations = operations;
  next.upstream_context = core_access.context;
  next.upstream_capture_frame = core_access.capture_frame;
  next.upstream_is_main_thread = core_access.is_main_thread;
  next.attached = true;
  state = next;

  core_environment.exact_build_admitted = true;
  core_environment.admitted_executable_sha256 =
      kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  core_environment.module_base = binding.module_base;
  core_environment.producer_address =
      binding.module_base + kCouncilCompositionStewardCandidatesProducerRvaV1;

  core_access.context = &state;
  core_access.capture_frame = &CaptureFrameThunk;
  core_access.is_main_thread = &IsMainThreadThunk;
  core_access.produce = &ProduceThunk;
  core_access.release = &ReleaseThunk;
  core_access.is_readable_span = &CandidateSpanReadableThunk;
  core_access.read_candidate_pointer = &ReadCandidatePointerThunk;
  core_access.read_candidate_id = &ReadCandidateIdThunk;
  core_access.resolve_candidate = &ResolveCandidateThunk;
  return true;
}

} // namespace xar::ck3_11906
