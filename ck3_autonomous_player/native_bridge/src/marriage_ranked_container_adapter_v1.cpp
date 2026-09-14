#include "xar_bridge/marriage_ranked_container_adapter_v1.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <new>
#include <type_traits>

namespace xar::bridge {
namespace {

template <typename Value>
bool AddRva(std::uintptr_t base, std::uintptr_t rva, Value &output) noexcept {
  if (base == 0 || rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = {};
    return false;
  }
  if constexpr (std::is_pointer_v<Value>) {
    output = reinterpret_cast<Value>(base + rva);
  } else {
    output = static_cast<Value>(base + rva);
  }
  return true;
}

void SetFailure(MarriageRankedContainerAdapterStateV1 &state,
                MarriageRankedContainerAdapterFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool ReadMemory(const MarriageRankedContainerAdapterEnvironmentV1 &env,
                std::uintptr_t address, void *output, std::size_t size) {
  return env.read_memory != nullptr && address != 0 && output != nullptr &&
      size != 0 && env.read_memory(env.memory_context, address, output, size);
}

template <typename Value>
bool ReadAt(const MarriageRankedContainerAdapterEnvironmentV1 &env,
            std::uintptr_t base, std::size_t offset, Value &output) {
  return base != 0 &&
      offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
      ReadMemory(env, base + offset, &output, sizeof(output));
}

struct RankedHeaderV1 {
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *owner = nullptr;
};
static_assert(sizeof(RankedHeaderV1) == kMarriageRankedHeaderSizeV1);

struct alignas(8) CandidateStorageV1 {
  RankedHeaderV1 header{};
  std::array<std::byte, kMarriageCandidateOwnerSizeV1> owner{};
};
struct alignas(8) ScoredStorageV1 {
  RankedHeaderV1 header{};
  std::array<std::byte, kMarriageScoredOwnerSizeV1> owner{};
};
static_assert(sizeof(CandidateStorageV1) == kMarriageCandidateStorageSizeV1);
static_assert(sizeof(ScoredStorageV1) == kMarriageScoredStorageSizeV1);

struct RankedTokenV1 {
  static constexpr std::uint64_t kMagic = 0x31564B4E41524D58ULL;
  CandidateStorageV1 *candidate = nullptr;
  ScoredStorageV1 *scored = nullptr;
  std::uint64_t magic = kMagic;
  MarriageRankedContainerAdapterStateV1 *state = nullptr;
  bool candidate_initialized = false;
  bool scored_initialized = false;
};

template <typename Storage>
Storage *AllocateNativeStorage() noexcept {
  void *memory = ::operator new(sizeof(Storage), std::align_val_t{16},
                                std::nothrow);
  return memory == nullptr ? nullptr : new (memory) Storage{};
}

template <typename Storage>
void DeleteNativeStorage(Storage *storage) noexcept {
  if (storage == nullptr) return;
  storage->~Storage();
  ::operator delete(storage, std::align_val_t{16});
}

void WritePointer(void *base, std::size_t offset,
                  std::uintptr_t value) noexcept {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

MarriageRankedContainerAdapterFailureV1 Validate(
    const MarriageRankedContainerAdapterEnvironmentV1 &env) {
  if (!env.exact_build_admitted ||
      env.admitted_executable_sha256 !=
          kMarriageProposalNativeBinderExecutableSha256V1 ||
      (!env.offline_fixture && env.module_base == 0))
    return MarriageRankedContainerAdapterFailureV1::exact_build_not_admitted;
  if (env.read_memory == nullptr)
    return MarriageRankedContainerAdapterFailureV1::memory_reader_unavailable;
  if (env.read_native_tier == nullptr || env.native_cap_table_slot == 0 ||
      env.enumerate_candidates == nullptr || env.score_candidates == nullptr ||
      env.initialize_scored_container == nullptr ||
      env.release_native_buffer == nullptr ||
      env.initialize_candidate_buffer == nullptr ||
      env.candidate_owner_vtable == 0 || env.scored_owner_vtable == 0 ||
      env.scored_row_vtable == 0 ||
      env.candidate_backing_allocator == 0 ||
      env.scored_backing_allocator == 0)
    return MarriageRankedContainerAdapterFailureV1::binding_mismatch;
  if (env.offline_fixture) return MarriageRankedContainerAdapterFailureV1::none;

  const auto expected = BindMarriageRankedContainerAdapterEnvironmentV1(
      env.module_base, env.exact_build_admitted,
      env.admitted_executable_sha256);
  if (env.read_native_tier != expected.read_native_tier ||
      env.native_cap_table_slot != expected.native_cap_table_slot ||
      env.enumerate_candidates != expected.enumerate_candidates ||
      env.score_candidates != expected.score_candidates ||
      env.initialize_scored_container !=
          expected.initialize_scored_container ||
      env.release_native_buffer != expected.release_native_buffer ||
      env.initialize_candidate_buffer !=
          expected.initialize_candidate_buffer ||
      env.candidate_owner_vtable != expected.candidate_owner_vtable ||
      env.scored_owner_vtable != expected.scored_owner_vtable ||
      env.scored_row_vtable != expected.scored_row_vtable ||
      env.candidate_backing_allocator !=
          expected.candidate_backing_allocator ||
      env.scored_backing_allocator != expected.scored_backing_allocator)
    return MarriageRankedContainerAdapterFailureV1::binding_mismatch;

  struct Prefix {
    std::uintptr_t rva;
    std::array<std::uint8_t, 16> bytes;
  };
  constexpr std::array<Prefix, 7> prefixes{{
      {kMarriageNativeTierRvaV1,
       {0x48, 0x8B, 0x81, 0xB8, 0x01, 0x00, 0x00, 0x48, 0x85, 0xC0, 0x75,
        0x61, 0x48, 0x8B, 0x81, 0xC8}},
      {kMarriageCandidateEnumeratorRvaV1,
       {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x08, 0x44, 0x89, 0x48, 0x20,
        0x55, 0x56, 0x57, 0x41, 0x54}},
      {kMarriageCandidateScoreFilterRvaV1,
       {0x40, 0x53, 0x55, 0x56, 0x57, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x20,
        0x48, 0x8B, 0x42, 0x10, 0x49}},
      {kMarriageInitializeScoredContainerRvaV1,
       {0x48, 0x89, 0x6C, 0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57,
        0x41, 0x56, 0x41, 0x57, 0x48}},
      {kMarriageReleaseNativeBufferRvaV1,
       {0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x48,
        0x8D, 0x41, 0x08, 0x49, 0x8B}},
      {kMarriageInitializeCandidateBufferRvaV1,
       {0x48, 0x8D, 0x41, 0x08, 0x48, 0x89, 0x02, 0x41, 0xC7, 0x00, 0x80,
        0x00, 0x00, 0x00, 0xC3, 0xCC}},
      {kMarriageDestroyScoredRowRvaV1,
       {0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x48, 0x8B, 0xD9, 0xF6, 0xC2,
        0x01, 0x74, 0x0A, 0xBA, 0x10}},
  }};
  for (const auto &prefix : prefixes) {
    std::array<std::uint8_t, 16> actual{};
    if (!ReadMemory(env, env.module_base + prefix.rva, actual.data(),
                    actual.size()) ||
        actual != prefix.bytes)
      return MarriageRankedContainerAdapterFailureV1::signature_mismatch;
  }
  const std::array<std::uintptr_t, 8> candidate_vtable{
      env.module_base + 0x8042F0, env.module_base + 0x7E8FF0,
      env.module_base + 0x7E8FB0, env.module_base + 0x7E8F90,
      env.module_base + 0x947C00, env.module_base + 0x947C00,
      env.module_base + 0x804260, env.module_base + 0x804260};
  const std::array<std::uintptr_t, 8> scored_vtable{
      env.module_base + 0x82D790, env.module_base + 0x7E8FF0,
      env.module_base + 0x7E8FB0, env.module_base + 0x7E8F90,
      env.module_base + 0x804270, env.module_base + 0x804270,
      env.module_base + 0x82A9A0, env.module_base + 0x82A9A0};
  std::array<std::uintptr_t, 8> actual_candidate{};
  std::array<std::uintptr_t, 8> actual_scored{};
  std::uintptr_t actual_row_destructor = 0;
  if (!ReadMemory(env, env.candidate_owner_vtable, actual_candidate.data(),
                  sizeof(actual_candidate)) ||
      !ReadMemory(env, env.scored_owner_vtable, actual_scored.data(),
                  sizeof(actual_scored)) ||
      !ReadMemory(env, env.scored_row_vtable, &actual_row_destructor,
                  sizeof(actual_row_destructor)) ||
      actual_candidate != candidate_vtable || actual_scored != scored_vtable ||
      actual_row_destructor != env.module_base + kMarriageDestroyScoredRowRvaV1)
    return MarriageRankedContainerAdapterFailureV1::signature_mismatch;
  return MarriageRankedContainerAdapterFailureV1::none;
}

bool ValidHeader(const RankedHeaderV1 &header, std::int32_t maximum_count) {
  return header.capacity >= 0 && header.count >= 0 &&
      header.count <= header.capacity && header.count <= maximum_count &&
      (header.count == 0 || header.data != nullptr) && header.owner != nullptr;
}

bool InitializeCandidate(RankedTokenV1 &token) {
  auto &env = token.state->environment;
  auto &storage = *token.candidate;
  storage = {};
  storage.header.owner = storage.owner.data();
  WritePointer(storage.owner.data(), 0, env.candidate_owner_vtable);
  WritePointer(storage.owner.data(), 0x408,
               env.candidate_backing_allocator);
  env.release_native_buffer(storage.owner.data(), nullptr, 8);
  env.initialize_candidate_buffer(storage.owner.data(), &storage.header.data,
                                  &storage.header.capacity);
  token.candidate_initialized = true;
  return storage.header.data == storage.owner.data() + 8 &&
      storage.header.capacity ==
          static_cast<std::int32_t>(kMarriageCandidateInlineCapacityV1) &&
      storage.header.count == 0;
}

bool InitializeScored(RankedTokenV1 &token) {
  auto &env = token.state->environment;
  *token.scored = {};
  if (env.initialize_scored_container(&token.scored->header) !=
      &token.scored->header)
    return false;
  token.scored_initialized = true;
  std::uintptr_t owner_vtable = 0;
  std::uintptr_t backing = 0;
  std::memcpy(&owner_vtable, token.scored->owner.data(), sizeof(owner_vtable));
  std::memcpy(&backing, token.scored->owner.data() + 0x208,
              sizeof(backing));
  return token.scored->header.owner == token.scored->owner.data() &&
      token.scored->header.data == token.scored->owner.data() + 8 &&
      token.scored->header.capacity ==
          static_cast<std::int32_t>(kMarriageScoredInlineCapacityV1) &&
      token.scored->header.count == 0 &&
      owner_vtable == env.scored_owner_vtable &&
      backing == env.scored_backing_allocator;
}

void DestroyToken(RankedTokenV1 *token) {
  if (token == nullptr || token->magic != RankedTokenV1::kMagic ||
      token->state == nullptr)
    return;
  auto &env = token->state->environment;
  if (token->scored_initialized) {
    env.initialize_scored_container(&token->scored->header);
    token->scored_initialized = false;
  }
  if (token->candidate_initialized) {
    token->candidate->header.count = 0;
    env.release_native_buffer(token->candidate->owner.data(),
                              token->candidate->header.data, 8);
    token->candidate->header.data = nullptr;
    token->candidate->header.capacity = 0;
    token->candidate_initialized = false;
  }
  DeleteNativeStorage(token->scored);
  DeleteNativeStorage(token->candidate);
  token->magic = 0;
  delete token;
}

bool ReadNativeCap(const MarriageRankedContainerAdapterEnvironmentV1 &env,
                   void *subject, std::int32_t &output) {
  const auto tier = env.read_native_tier(subject);
  std::uintptr_t table = 0;
  if (!ReadMemory(env, env.native_cap_table_slot, &table, sizeof(table)) ||
      table == 0)
    return false;
  const auto signed_offset = static_cast<std::int64_t>(tier) *
      static_cast<std::int64_t>(sizeof(std::int32_t));
  std::uintptr_t address = 0;
  if (signed_offset >= 0) {
    const auto offset = static_cast<std::uintptr_t>(signed_offset);
    if (offset > (std::numeric_limits<std::uintptr_t>::max)() - table)
      return false;
    address = table + offset;
  } else {
    const auto offset = static_cast<std::uintptr_t>(-signed_offset);
    if (offset > table) return false;
    address = table - offset;
  }
  std::int32_t native_value = 0;
  if (!ReadMemory(env, address, &native_value, sizeof(native_value)))
    return false;
  output = native_value > 0 ? native_value : 0;
  return true;
}

bool BuildParameters(const MarriageRankedContainerAdapterEnvironmentV1 &env,
                     const MarriageNativeRankedInvocationV1 &request,
                     std::array<std::byte, 0x20> &output) {
  output = {};
  const auto interaction = request.arrange_marriage_interaction;
  const auto subject = request.subject_character;
  std::memcpy(output.data(), &interaction, sizeof(interaction));
  std::memcpy(output.data() + 8, &subject, sizeof(subject));
  std::memcpy(output.data() + 0x10, &subject, sizeof(subject));
  std::uintptr_t living = 0;
  if (!ReadAt(env, subject, kMarriageCharacterLivingDataOffsetV1, living))
    return false;
  bool younger_than_thirty = false;
  if (living != 0) {
    std::uintptr_t age_data = 0;
    std::int8_t age = 0;
    if (!ReadAt(env, living, 0x308, age_data) || age_data == 0 ||
        !ReadAt(env, age_data, 2, age))
      return false;
    younger_than_thirty = age < 30;
  }
  std::memcpy(output.data() + 0x18, &younger_than_thirty,
              sizeof(younger_than_thirty));
  const std::int32_t minimum_score = 1;
  std::memcpy(output.data() + 0x1C, &minimum_score, sizeof(minimum_score));
  return true;
}

} // namespace

MarriageRankedContainerAdapterEnvironmentV1
BindMarriageRankedContainerAdapterEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  MarriageRankedContainerAdapterEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  const bool complete =
      AddRva(module_base, kMarriageNativeTierRvaV1,
             output.read_native_tier) &&
      AddRva(module_base, kMarriageNativeCapTableSlotRvaV1,
             output.native_cap_table_slot) &&
      AddRva(module_base, kMarriageCandidateEnumeratorRvaV1,
             output.enumerate_candidates) &&
      AddRva(module_base, kMarriageCandidateScoreFilterRvaV1,
             output.score_candidates) &&
      AddRva(module_base, kMarriageInitializeScoredContainerRvaV1,
             output.initialize_scored_container) &&
      AddRva(module_base, kMarriageReleaseNativeBufferRvaV1,
             output.release_native_buffer) &&
      AddRva(module_base, kMarriageInitializeCandidateBufferRvaV1,
             output.initialize_candidate_buffer) &&
      AddRva(module_base, kMarriageCandidateOwnerVtableRvaV1,
             output.candidate_owner_vtable) &&
      AddRva(module_base, kMarriageScoredOwnerVtableRvaV1,
             output.scored_owner_vtable) &&
      AddRva(module_base, kMarriageScoredRowVtableRvaV1,
             output.scored_row_vtable) &&
      AddRva(module_base, kMarriageCandidateBackingAllocatorRvaV1,
             output.candidate_backing_allocator) &&
      AddRva(module_base, kMarriageScoredBackingAllocatorRvaV1,
             output.scored_backing_allocator);
  if (!complete) {
    const auto admitted = output.exact_build_admitted;
    const auto sha = output.admitted_executable_sha256;
    output = {};
    output.exact_build_admitted = admitted;
    output.admitted_executable_sha256 = sha;
  }
  return output;
}

bool ConfigureMarriageRankedContainerAdapterV1(
    MarriageRankedContainerAdapterStateV1 &adapter,
    MarriageProposalNativeBinderStateV1 &binder) noexcept {
  const auto failure = Validate(adapter.environment);
  if (failure != MarriageRankedContainerAdapterFailureV1::none) {
    SetFailure(adapter, failure);
    return false;
  }
  binder.environment.source_adapter.ranked_context = &adapter;
  binder.environment.source_adapter.invoke_ranked_source =
      &InvokeMarriageRankedContainerExactV1;
  binder.environment.source_adapter.read_ranked_container_view =
      &ReadMarriageRankedContainerViewExactV1;
  binder.environment.source_adapter.release_ranked_container =
      &ReleaseMarriageRankedContainerExactV1;
  binder.environment.ranked_container_lifecycle_certified = true;
  SetFailure(adapter, MarriageRankedContainerAdapterFailureV1::none);
  return true;
}

bool InvokeMarriageRankedContainerExactV1(
    void *context, const MarriageNativeRankedInvocationV1 &request,
    std::uintptr_t &container_token) noexcept {
  container_token = 0;
  if (context == nullptr) return false;
  auto &state = *static_cast<MarriageRankedContainerAdapterStateV1 *>(context);
  auto failure = Validate(state.environment);
  if (failure != MarriageRankedContainerAdapterFailureV1::none) {
    SetFailure(state, failure);
    return false;
  }
  auto &env = state.environment;
  if (request.subject_character == 0 || request.strategy == 0 ||
      request.arrange_marriage_interaction == 0 || request.limit == 0 ||
      request.limit > kMarriageMatchmakingMaximumCandidatesV1 ||
      request.entry_points.enumerate_candidates !=
          reinterpret_cast<std::uintptr_t>(env.enumerate_candidates) ||
      request.entry_points.score_filter_candidates !=
          reinterpret_cast<std::uintptr_t>(env.score_candidates)) {
    SetFailure(state,
               MarriageRankedContainerAdapterFailureV1::invalid_invocation);
    return false;
  }
  auto *token = new (std::nothrow) RankedTokenV1{};
  if (token == nullptr) {
    SetFailure(state,
               MarriageRankedContainerAdapterFailureV1::candidate_container_invalid);
    return false;
  }
  token->state = &state;
  token->candidate = AllocateNativeStorage<CandidateStorageV1>();
  token->scored = AllocateNativeStorage<ScoredStorageV1>();
  if (token->candidate == nullptr || token->scored == nullptr) {
    SetFailure(state,
               MarriageRankedContainerAdapterFailureV1::candidate_container_invalid);
    DestroyToken(token);
    return false;
  }
  if (!InitializeCandidate(*token)) {
    failure = MarriageRankedContainerAdapterFailureV1::
        candidate_container_invalid;
  }
  std::int32_t native_cap = 0;
  if (failure == MarriageRankedContainerAdapterFailureV1::none &&
      !ReadNativeCap(env, reinterpret_cast<void *>(request.subject_character),
                     native_cap))
    failure = MarriageRankedContainerAdapterFailureV1::native_cap_unavailable;
  std::array<std::byte, 0x20> parameters{};
  if (failure == MarriageRankedContainerAdapterFailureV1::none &&
      !BuildParameters(env, request, parameters))
    failure =
        MarriageRankedContainerAdapterFailureV1::parameter_source_unavailable;
  if (failure == MarriageRankedContainerAdapterFailureV1::none) {
    env.enumerate_candidates(
        reinterpret_cast<void *>(request.strategy), 0, true, native_cap,
        &token->candidate->header);
    if (!ValidHeader(token->candidate->header,
                     kMarriageMaximumNativeRankedRowsV1))
      failure = MarriageRankedContainerAdapterFailureV1::
          candidate_container_invalid;
  }
  if (failure == MarriageRankedContainerAdapterFailureV1::none &&
      !InitializeScored(*token))
    failure =
        MarriageRankedContainerAdapterFailureV1::scored_container_invalid;
  if (failure == MarriageRankedContainerAdapterFailureV1::none) {
    env.score_candidates(reinterpret_cast<void *>(request.strategy),
                         parameters.data(), &token->candidate->header,
                         &token->scored->header);
    if (!ValidHeader(token->scored->header,
                     kMarriageMaximumNativeRankedRowsV1)) {
      failure =
          MarriageRankedContainerAdapterFailureV1::scored_container_invalid;
    } else {
      for (std::int32_t index = 0; index < token->scored->header.count; ++index) {
        std::uintptr_t vtable = 0;
        const auto row = reinterpret_cast<std::uintptr_t>(
                             token->scored->header.data) +
            static_cast<std::uintptr_t>(index) *
                kMarriageNativeRankedRowStrideV1;
        if (!ReadMemory(env, row, &vtable, sizeof(vtable)) ||
            vtable != env.scored_row_vtable) {
          failure = MarriageRankedContainerAdapterFailureV1::
              scored_row_identity_mismatch;
          break;
        }
      }
    }
  }
  if (failure != MarriageRankedContainerAdapterFailureV1::none) {
    SetFailure(state, failure);
    DestroyToken(token);
    return false;
  }
  container_token = reinterpret_cast<std::uintptr_t>(token);
  SetFailure(state, MarriageRankedContainerAdapterFailureV1::none);
  return true;
}

bool ReadMarriageRankedContainerViewExactV1(
    void *context, std::uintptr_t container_token,
    MarriageNativeRankedContainerViewV1 &output) noexcept {
  output = {};
  if (context == nullptr || container_token == 0) return false;
  auto &state = *static_cast<MarriageRankedContainerAdapterStateV1 *>(context);
  auto *token = reinterpret_cast<RankedTokenV1 *>(container_token);
  if (token->magic != RankedTokenV1::kMagic || token->state != &state ||
      !token->scored_initialized ||
      !ValidHeader(token->scored->header,
                   kMarriageMaximumNativeRankedRowsV1)) {
    SetFailure(state,
               MarriageRankedContainerAdapterFailureV1::scored_container_invalid);
    return false;
  }
  output.row_data =
      reinterpret_cast<std::uintptr_t>(token->scored->header.data);
  output.capacity = token->scored->header.capacity;
  output.count = token->scored->header.count;
  SetFailure(state, MarriageRankedContainerAdapterFailureV1::none);
  return true;
}

void ReleaseMarriageRankedContainerExactV1(
    void *context, std::uintptr_t container_token) noexcept {
  if (context == nullptr || container_token == 0) return;
  auto &state = *static_cast<MarriageRankedContainerAdapterStateV1 *>(context);
  auto *token = reinterpret_cast<RankedTokenV1 *>(container_token);
  if (token->magic != RankedTokenV1::kMagic || token->state != &state) {
    SetFailure(state,
               MarriageRankedContainerAdapterFailureV1::invalid_invocation);
    return;
  }
  DestroyToken(token);
}

MarriageRankedContainerAdapterFailureV1
ReadMarriageRankedContainerAdapterFailureV1(
    const MarriageRankedContainerAdapterStateV1 &adapter) noexcept {
  return static_cast<MarriageRankedContainerAdapterFailureV1>(
      adapter.last_failure.load(std::memory_order_acquire));
}

} // namespace xar::bridge
