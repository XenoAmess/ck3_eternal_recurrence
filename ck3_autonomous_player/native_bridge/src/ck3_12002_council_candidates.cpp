#include "xar_bridge/ck3_12002_council_candidates.hpp"

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

namespace xar::ck3_12002 {
namespace {

using Source = game::CouncilCompositionStewardCandidatesV1;
using SourceFailure = game::CouncilCompositionStewardCandidatesFailureV1;
using Public = game::CouncilCompositionCandidatesPublicV1;
using PublicFailure = game::CouncilCompositionCandidatesPublicFailureV1;
using Result = ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1;
using Enrichment = ck3_11906::CouncilCompositionCandidatesPublicEnrichmentV1;

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  return end == value.end() ? std::string_view{} :
      std::string_view{value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool Address(const void *base, std::size_t offset, const void *&output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  output = nullptr;
  if (base == nullptr || offset > (std::numeric_limits<std::uintptr_t>::max)() - address)
    return false;
  output = reinterpret_cast<const void *>(address + offset);
  return true;
}

template <typename T>
bool Read(const CouncilCandidatesAccessV1 &access, const void *base,
          std::size_t offset, T &output) noexcept {
  const void *address = nullptr;
  return Address(base, offset, address) &&
         ReadCouncilMemory12002(access, address, &output, sizeof(output));
}

bool EnvironmentExact(const CouncilCandidatesEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 != kExecutableSha256 ||
      environment.module_base == 0 ||
      environment.character_storage_slot == nullptr ||
      environment.character_fallback_slot == nullptr ||
      environment.active_task_storage_slot == nullptr ||
      environment.active_task_fallback_slot == nullptr ||
      environment.allocator_vtable == 0 || environment.fallback_allocator == 0 ||
      environment.initialize_vector == nullptr ||
      environment.produce_candidates == nullptr ||
      environment.release_allocation == nullptr) return false;
  if (environment.offline_fixture_function_overrides) return true;
  const auto base = environment.module_base;
  return reinterpret_cast<std::uintptr_t>(environment.character_storage_slot) ==
             base + kCharacterStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.character_fallback_slot) ==
             base + kCouncilCandidatesCharacterFallbackSlotRva12002 &&
         reinterpret_cast<std::uintptr_t>(environment.active_task_storage_slot) ==
             base + kCouncilCandidatesTaskStorageSlotRva12002 &&
         reinterpret_cast<std::uintptr_t>(environment.active_task_fallback_slot) ==
             base + kCouncilCandidatesTaskFallbackSlotRva12002 &&
         environment.allocator_vtable == base + kCouncilCandidatesAllocatorVtableRva12002 &&
         environment.fallback_allocator == base + kCouncilCandidatesFallbackAllocatorRva12002 &&
         reinterpret_cast<std::uintptr_t>(environment.initialize_vector) ==
             base + kCouncilCandidatesInitializeRva12002 &&
         reinterpret_cast<std::uintptr_t>(environment.produce_candidates) ==
             base + kCouncilCandidatesProducerRva12002 &&
         reinterpret_cast<std::uintptr_t>(environment.release_allocation) ==
             base + kCouncilCandidatesReleaseRva12002;
}

bool Resolve(const CouncilCandidatesAccessV1 &access, void **storage_slot,
             void **fallback_slot, std::int32_t id,
             std::size_t identity_offset, const void *&output) noexcept {
  output = nullptr;
  if (id <= 0) return false;
  void *storage = nullptr, *fallback = nullptr, *slots = nullptr, *object = nullptr;
  std::int32_t capacity = 0, observed = -1;
  if (!Read(access, storage_slot, 0, storage) ||
      !Read(access, fallback_slot, 0, fallback) || storage == nullptr ||
      !Read(access, storage, 0x20, slots) || slots == nullptr ||
      !Read(access, storage, 0x2C, capacity) || capacity <= 0 ||
      capacity > 4'194'304) return false;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      !Read(access, slots, static_cast<std::size_t>(index) * 0x10 + 0x08, object) ||
      object == nullptr || object == fallback ||
      !Read(access, object, identity_offset, observed) || observed != id)
    return false;
  output = object;
  return true;
}

bool ReadKey(const CouncilCandidatesAccessV1 &access, const void *object,
             std::array<char, game::kCouncilCompositionStewardPositionKeyCapacityV1>
                 &output) noexcept {
  output.fill('\0');
  const void *key = nullptr;
  std::size_t size = 0, capacity = 0;
  if (!Address(object, 0x18, key) ||
      !Read(access, key, 0x10, size) || !Read(access, key, 0x18, capacity) ||
      size == 0 || size > capacity || size >= output.size()) return false;
  const void *bytes = key;
  if (capacity > 0x0F && (!Read(access, key, 0, bytes) || bytes == nullptr))
    return false;
  return ReadCouncilMemory12002(access, bytes, output.data(), size) &&
         std::none_of(output.begin(), output.begin() + size,
             [](unsigned char c) { return c == 0 || c < 0x20U; });
}

bool ResolvePositionTask(const CouncilCandidatesEnvironmentV1 &environment,
                         const CouncilCandidatesAccessV1 &access,
                         CouncilCandidatesFrameV1 &frame,
                         std::string_view position_key) noexcept {
  frame.active_task_id = -1;
  frame.active_task = 0;
  frame.active_task_identity_round_trip = false;
  frame.position_key.fill('\0');
  frame.played_character_identity_round_trip = false;
  const void *owner = nullptr;
  if (!frame.has_played_character || frame.played_character == 0 ||
      !ResolveCouncilCharacter12002(environment, access, frame.played_character_id, owner) ||
      reinterpret_cast<std::uintptr_t>(owner) != frame.played_character)
    return true;
  frame.played_character_identity_round_trip = true;
  const void *extension = nullptr, *ids = nullptr;
  std::int32_t count = 0;
  if (!Read(access, owner, 0x1C0, extension) || extension == nullptr ||
      !Read(access, extension, 0x230, ids) ||
      !Read(access, extension, 0x23C, count) || count < 0 || count > 4'096 ||
      (count > 0 && ids == nullptr)) return true;
  const void *matched = nullptr;
  std::int32_t matched_id = -1;
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t id = -1, task_owner = -1;
    const void *task = nullptr, *type = nullptr, *position = nullptr;
    std::array<char, game::kCouncilCompositionStewardPositionKeyCapacityV1> key{};
    if (!Read(access, ids, static_cast<std::size_t>(index) * 4, id) ||
        !Resolve(access, environment.active_task_storage_slot,
            environment.active_task_fallback_slot, id, 0x10, task) ||
        !Read(access, task, 0x18, type) || type == nullptr ||
        !Read(access, type, 0x40, position) || position == nullptr ||
        !ReadKey(access, position, key) ||
        !Read(access, task, 0x44, task_owner)) return true;
    if (FixedString(key) != position_key) continue;
    if (task_owner != frame.played_character_id || matched != nullptr)
      return true;
    matched = task;
    matched_id = id;
  }
  if (matched == nullptr) return true;
  frame.active_task_id = matched_id;
  frame.active_task = reinterpret_cast<std::uintptr_t>(matched);
  frame.active_task_identity_round_trip = true;
  std::copy(position_key.begin(), position_key.end(), frame.position_key.begin());
  return true;
}

SourceFailure ValidateFrame(const CouncilCandidatesFrameV1 &frame,
                           const CouncilCandidatesRequestV1 &request) noexcept {
  if (FixedString(frame.snapshot_id) != request.expected_snapshot_id)
    return SourceFailure::snapshot_identity_mismatch;
  if (frame.public_revision != request.expected_public_revision ||
      frame.native_revision != request.expected_native_revision)
    return SourceFailure::revision_drift;
  if (frame.date_raw != request.expected_date_raw) return SourceFailure::date_drift;
  if (!frame.paused) return SourceFailure::not_paused;
  if (!frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive || frame.played_character == 0 ||
      !frame.played_character_identity_round_trip ||
      frame.played_character_id != request.expected_owner_character_id)
    return SourceFailure::player_unavailable;
  if (frame.active_task_id <= 0 || frame.active_task == 0 ||
      !frame.active_task_identity_round_trip)
    return SourceFailure::active_steward_task_unavailable;
  if (FixedString(frame.position_key) != request.position_key)
    return SourceFailure::position_outside_coverage;
  return SourceFailure::none;
}

SourceFailure Drift(const CouncilCandidatesFrameV1 &before,
                    const CouncilCandidatesFrameV1 &after) noexcept {
  if (before.snapshot_id != after.snapshot_id)
    return SourceFailure::snapshot_identity_mismatch;
  if (before.public_revision != after.public_revision ||
      before.native_revision != after.native_revision)
    return SourceFailure::revision_drift;
  if (before.date_raw != after.date_raw) return SourceFailure::date_drift;
  if (!after.paused) return SourceFailure::not_paused;
  if (before != after) return SourceFailure::active_steward_task_unavailable;
  return SourceFailure::none;
}

bool Initialize(const CouncilCandidatesEnvironmentV1 &environment,
                const CouncilCandidatesAccessV1 &access, void *allocator,
                CouncilCandidatesNativeVectorV1 &vector) noexcept {
  std::memset(allocator, 0, kCouncilCandidatesAllocatorSize12002);
  std::memcpy(allocator, &environment.allocator_vtable, sizeof(std::uintptr_t));
  std::memcpy(static_cast<std::byte *>(allocator) +
      kCouncilCandidatesAllocatorFallbackOffset12002,
      &environment.fallback_allocator, sizeof(std::uintptr_t));
  vector = {};
  vector.allocator = allocator;
  if (access.initialize_vector != nullptr)
    return access.initialize_vector(access.context, environment, allocator,
        kCouncilCandidatesAllocatorSize12002, vector);
#if defined(_MSC_VER)
  __try {
    environment.initialize_vector(allocator, &vector.data_address, &vector.capacity);
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  environment.initialize_vector(allocator, &vector.data_address, &vector.capacity);
#endif
  return vector.data_address == reinterpret_cast<std::uintptr_t>(allocator) + 8 &&
         vector.capacity == 64 && vector.count == 0;
}

bool Produce(const CouncilCandidatesEnvironmentV1 &environment,
             const CouncilCandidatesAccessV1 &access,
             const CouncilCandidatesFrameV1 &frame,
             CouncilCandidatesNativeVectorV1 &vector) noexcept {
  const auto *owner = reinterpret_cast<const void *>(frame.played_character);
  const auto *task = reinterpret_cast<const void *>(frame.active_task);
  if (access.invoke_producer != nullptr)
    return access.invoke_producer(access.context, environment, owner, task, true, vector);
#if defined(_MSC_VER)
  __try { environment.produce_candidates(owner, task, true, &vector); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  environment.produce_candidates(owner, task, true, &vector);
#endif
  return true;
}

bool Release(const CouncilCandidatesEnvironmentV1 &environment,
             const CouncilCandidatesAccessV1 &access,
             CouncilCandidatesNativeVectorV1 &vector) noexcept {
  if (access.release_allocation != nullptr)
    return access.release_allocation(access.context, environment, vector);
  if (vector.data_address == 0) return true;
#if defined(_MSC_VER)
  __try {
    environment.release_allocation(vector.allocator,
        reinterpret_cast<void *>(vector.data_address), sizeof(std::uintptr_t));
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  environment.release_allocation(vector.allocator,
      reinterpret_cast<void *>(vector.data_address), sizeof(std::uintptr_t));
#endif
  return true;
}

Result Unavailable(Public &output, Source *private_source,
                   SourceFailure reason, bool released = false,
                   PublicFailure public_reason = PublicFailure::private_reader_unavailable) noexcept {
  output = {};
  output.unavailable_reason = public_reason;
  output.source_unavailable_reason = reason;
  if (private_source != nullptr) {
    *private_source = {};
    private_source->unavailable_reason = reason;
    private_source->temporary_vector_released = released;
  }
  return Result::unavailable;
}

} // namespace

CouncilCandidatesEnvironmentV1 BindCouncilCandidates12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  CouncilCandidatesEnvironmentV1 output{};
  if (module_base == 0 || executable_sha256 != kExecutableSha256) return output;
  output.exact_build_admitted = true;
  output.module_base = module_base;
  output.admitted_executable_sha256 = kExecutableSha256;
  output.character_storage_slot = reinterpret_cast<void **>(module_base + kCharacterStorageSlotRva);
  output.character_fallback_slot = reinterpret_cast<void **>(module_base + kCouncilCandidatesCharacterFallbackSlotRva12002);
  output.active_task_storage_slot = reinterpret_cast<void **>(module_base + kCouncilCandidatesTaskStorageSlotRva12002);
  output.active_task_fallback_slot = reinterpret_cast<void **>(module_base + kCouncilCandidatesTaskFallbackSlotRva12002);
  output.allocator_vtable = module_base + kCouncilCandidatesAllocatorVtableRva12002;
  output.fallback_allocator = module_base + kCouncilCandidatesFallbackAllocatorRva12002;
  output.initialize_vector = reinterpret_cast<NativeCouncilCandidatesInitialize12002>(module_base + kCouncilCandidatesInitializeRva12002);
  output.produce_candidates = reinterpret_cast<NativeCouncilCandidatesProducer12002>(module_base + kCouncilCandidatesProducerRva12002);
  output.release_allocation = reinterpret_cast<NativeCouncilCandidatesRelease12002>(module_base + kCouncilCandidatesReleaseRva12002);
  return output;
}

bool ReadCouncilMemory12002(const CouncilCandidatesAccessV1 &access,
    const void *address, void *output, std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
  if (access.read_memory != nullptr)
    return access.read_memory(access.context, address, output, size);
#if defined(_MSC_VER)
  __try { std::memcpy(output, address, size); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

bool ResolveCouncilCharacter12002(const CouncilCandidatesEnvironmentV1 &environment,
    const CouncilCandidatesAccessV1 &access, std::int32_t full_id,
    const void *&pointer) noexcept {
  pointer = nullptr;
  return EnvironmentExact(environment) &&
         Resolve(access, environment.character_storage_slot,
             environment.character_fallback_slot, full_id, 0x18, pointer);
}

bool CaptureCouncilCandidatesFrame12002(
    const CouncilCandidatesEnvironmentV1 &environment,
    const CouncilCandidatesAccessV1 &access,
    CouncilCandidatesFrameV1 &output, std::string_view position_key) noexcept {
  output = {};
  return !CouncilCandidatesProfile12002(position_key).position_key.empty() &&
          EnvironmentExact(environment) && access.capture_frame != nullptr &&
         access.is_main_thread != nullptr && access.is_main_thread(access.context) &&
         access.capture_frame(access.context, output) &&
          ResolvePositionTask(environment, access, output, position_key);
}

ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1
ReadCouncilCandidates12002(const CouncilCandidatesEnvironmentV1 &environment,
    const CouncilCandidatesAccessV1 &access, const CouncilCandidatesRequestV1 &request,
    game::CouncilCompositionCandidatesPublicV1 &output,
    game::CouncilCompositionStewardCandidatesV1 *private_source) noexcept {
  output = {};
  if (private_source != nullptr) *private_source = {};
  if (request.expected_snapshot_id.empty() ||
      request.expected_snapshot_id.size() >= game::kCouncilCompositionStewardSnapshotIdCapacityV1 ||
      request.expected_public_revision == 0 || request.expected_native_revision == 0 ||
      request.expected_owner_character_id <= 0)
    return Unavailable(output, private_source, SourceFailure::invalid_request);
  const auto profile = CouncilCandidatesProfile12002(request.position_key);
  if (profile.position_key.empty())
    return Unavailable(output, private_source, SourceFailure::position_outside_coverage);
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 != kExecutableSha256)
    return Unavailable(output, private_source, SourceFailure::exact_build_not_admitted);
  if (!EnvironmentExact(environment) || access.capture_frame == nullptr ||
      access.is_main_thread == nullptr ||
      (!environment.offline_fixture_function_overrides &&
       (access.initialize_vector != nullptr || access.invoke_producer != nullptr ||
        access.release_allocation != nullptr)))
    return Unavailable(output, private_source, SourceFailure::native_bindings_unavailable);
  if (!access.is_main_thread(access.context))
    return Unavailable(output, private_source, SourceFailure::application_main_thread_required);
  CouncilCandidatesFrameV1 before{};
  if (!CaptureCouncilCandidatesFrame12002(environment, access, before, request.position_key))
    return Unavailable(output, private_source, SourceFailure::frame_capture_failed);
  const auto initial = ValidateFrame(before, request);
  if (initial != SourceFailure::none) return Unavailable(output, private_source, initial);

  Enrichment enrichment{};
  std::int32_t incumbent_id = -1, incumbent_skill = -1;
  if (!Read(access, reinterpret_cast<const void *>(before.active_task),
      kCouncilCandidatesTaskIncumbentOffset12002, incumbent_id) || incumbent_id == 0)
    return Unavailable(output, private_source, SourceFailure::none, false,
        PublicFailure::incumbent_invalid);
  if (incumbent_id != -1) {
    const void *incumbent = nullptr;
    if (!ResolveCouncilCharacter12002(environment, access, incumbent_id, incumbent))
      return Unavailable(output, private_source, SourceFailure::none, false,
          PublicFailure::incumbent_invalid);
    if (!Read(access, incumbent, profile.main_skill_offset,
        incumbent_skill) || incumbent_skill < 0)
      return Unavailable(output, private_source, SourceFailure::none, false,
          PublicFailure::incumbent_main_skill_unready);
  }

  alignas(16) std::array<std::byte, kCouncilCandidatesAllocatorSize12002> allocator{};
  CouncilCandidatesNativeVectorV1 vector{};
  SourceFailure failure = SourceFailure::none;
  PublicFailure public_failure = PublicFailure::private_reader_unavailable;
  const bool initialized = Initialize(environment, access, allocator.data(), vector);
  if (!initialized || vector.allocator != allocator.data()) {
    const bool released = vector.allocator == allocator.data() && Release(environment, access, vector);
    return Unavailable(output, private_source, released ?
        SourceFailure::candidate_collection_unavailable :
        SourceFailure::temporary_vector_release_failed, released);
  }
  const bool produced = Produce(environment, access, before, vector);
  if (!produced) failure = SourceFailure::candidate_collection_unavailable;
  if (failure == SourceFailure::none &&
      (vector.count < 0 || vector.capacity < 0 || vector.capacity > 65'536 ||
       vector.count > vector.capacity ||
       vector.count > static_cast<std::int32_t>(game::kCouncilCompositionStewardCandidatesMaximumRowsV1) ||
       (vector.count > 0 && (vector.data_address == 0 ||
        vector.data_address % alignof(std::uintptr_t) != 0 ||
        vector.data_address > (std::numeric_limits<std::uintptr_t>::max)() -
            static_cast<std::size_t>(vector.count) * sizeof(std::uintptr_t)))))
    failure = SourceFailure::candidate_span_invalid;

  Source pending{};
  if (failure == SourceFailure::none) {
    pending.candidate_count = static_cast<std::uint32_t>(vector.count);
    for (std::uint32_t ordinal = 0; ordinal < pending.candidate_count; ++ordinal) {
      const void *candidate = nullptr, *resolved = nullptr;
      std::int32_t id = -1, skill = -1;
      if (!Read(access, reinterpret_cast<const void *>(vector.data_address),
          static_cast<std::size_t>(ordinal) * sizeof(std::uintptr_t), candidate) ||
          candidate == nullptr || !Read(access, candidate, 0x18, id)) {
        failure = SourceFailure::candidate_row_unreadable; break;
      }
      if (!ResolveCouncilCharacter12002(environment, access, id, resolved) ||
          candidate != resolved) {
        failure = SourceFailure::candidate_generation_mismatch; break;
      }
      if (std::any_of(pending.candidates.begin(), pending.candidates.begin() + ordinal,
          [id](const auto &row) { return row.character_id == id; })) {
        failure = SourceFailure::duplicate_candidate_id; break;
      }
      if (!Read(access, candidate, profile.main_skill_offset, skill) || skill < 0) {
        public_failure = PublicFailure::candidate_main_skill_unready;
        failure = SourceFailure::candidate_row_unreadable; break;
      }
      pending.candidates[ordinal] = {id, ordinal};
      enrichment.candidates[ordinal] = {id, ordinal, true,
          game::CouncilCompositionCandidateEligibilityReasonV1::native_candidate_provider_accepted,
          skill};
    }
  }
  const bool released = Release(environment, access, vector);
  if (!released)
    return Unavailable(output, private_source, SourceFailure::temporary_vector_release_failed);
  if (!access.is_main_thread(access.context))
    return Unavailable(output, private_source, SourceFailure::application_main_thread_required, true);
  CouncilCandidatesFrameV1 after{};
  if (!CaptureCouncilCandidatesFrame12002(environment, access, after, request.position_key))
    return Unavailable(output, private_source, SourceFailure::frame_capture_failed, true);
  const auto drift = Drift(before, after);
  if (drift != SourceFailure::none) return Unavailable(output, private_source, drift, true);
  std::int32_t after_incumbent = -1;
  if (!Read(access, reinterpret_cast<const void *>(after.active_task),
      kCouncilCandidatesTaskIncumbentOffset12002, after_incumbent) ||
      after_incumbent != incumbent_id)
    return Unavailable(output, private_source, SourceFailure::none, true,
        PublicFailure::same_frame_binding_mismatch);
  if (failure != SourceFailure::none)
    return Unavailable(output, private_source, failure, true, public_failure);

  // Keep native ordinals while publishing the canonical unsigned-ID order.
  std::sort(enrichment.candidates.begin(), enrichment.candidates.begin() + pending.candidate_count,
      [](const auto &a, const auto &b) {
        return static_cast<std::uint32_t>(a.character_id) < static_cast<std::uint32_t>(b.character_id);
      });
  for (std::uint32_t i = 0; i < pending.candidate_count; ++i)
    pending.candidates[i] = {enrichment.candidates[i].character_id,
        enrichment.candidates[i].native_collection_ordinal};
  pending.status = game::CouncilCompositionStewardCandidatesStatusV1::available;
  pending.snapshot_id = before.snapshot_id;
  pending.public_revision = before.public_revision;
  pending.native_revision = before.native_revision;
  pending.date_raw = before.date_raw;
  pending.paused = true;
  pending.owner_character_id = before.played_character_id;
  pending.position_key = before.position_key;
  pending.candidate_collection_complete = true;
  pending.temporary_vector_released = true;
  pending.readiness = {true, true};
  enrichment.snapshot_id = pending.snapshot_id;
  enrichment.public_revision = pending.public_revision;
  enrichment.native_revision = pending.native_revision;
  enrichment.date_raw = pending.date_raw;
  enrichment.owner_character_id = pending.owner_character_id;
  enrichment.position_key = pending.position_key;
  enrichment.incumbent_character_id = incumbent_id;
  enrichment.incumbent_ready = true;
  enrichment.incumbent_main_skill = incumbent_skill;
  enrichment.incumbent_main_skill_ready = true;
  enrichment.candidate_count = pending.candidate_count;
  enrichment.same_frame_stable = true;
  const auto result = ck3_11906::ProjectCouncilCompositionCandidatesPublicV1(
      pending, enrichment, output, profile.position_key, profile.main_skill_key);
  if (result == Result::available && private_source != nullptr) *private_source = pending;
  return result;
}

std::string SerializeCouncilCandidates12002(const game::CouncilCompositionCandidatesPublicV1 &value) {
  // The v1 codec validates and escapes the unchanged public DTO. Its result
  // supplies only the version-neutral status/payload suffix; this adapter owns
  // the complete schema/capability/build prefix. No old build is admitted.
  const auto profile = CouncilCandidatesProfile12002(FixedString(value.position_key));
  const std::string payload = ck3_11906::SerializeCouncilCompositionCandidatesPublicV1(
      value, profile.position_key, profile.main_skill_key);
  const auto at = payload.find(",\"status\":");
  if (payload.empty() || at == std::string::npos) return {};
  std::string output = "{\"schema\":\"";
  output += ck3_11906::kCouncilCompositionCandidatesPublicSchemaV1;
  output += "\",\"schema_version\":1,\"capability\":\"";
  output += ck3_11906::kCouncilCompositionCandidatesPublicCapabilityV1;
  output += "\",\"exact_build\":{\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"";
  output += kExecutableSha256;
  output += "\"}";
  output.append(payload, at, std::string::npos);
  return output;
}

} // namespace xar::ck3_12002
