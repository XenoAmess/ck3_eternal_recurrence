#include "domain_construction_application_main_runtime_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <string>
#include <utility>
#include <vector>

#include <windows.h>

namespace xar::ck3::shared {
namespace {

using CandidateKind = research::DomainConstructionCandidateKindV1;
using Binding = research::DomainConstructionCandidateSnapshotBindingV1;
using ExactSample = research::DomainConstructionExactCollectorMemorySampleV1;
using Publication = research::DomainConstructionCostLegalityPublicationV1;

struct alignas(void*) NativeCommandStorageV1 final {
  std::array<std::byte, kDomainConstructionNativeCommandBytesV1> bytes{};
};

static_assert(sizeof(NativeCommandStorageV1) == 0x30U);

struct ExactBackendContextV1 final {
  std::uintptr_t module_base = 0U;
  DomainConstructionExactNativeCallsV1 calls;
  NativeCommandStorageV1 command;
  bool command_ready = false;
};

bool AddRva(const std::uintptr_t base, const std::uintptr_t rva,
            std::uintptr_t& output) noexcept {
  if (base == 0U ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = 0U;
    return false;
  }
  output = base + rva;
  return true;
}

bool ReadCurrent(const std::uintptr_t address, void* destination,
                 const std::size_t bytes) noexcept {
  SIZE_T read = 0U;
  return address != 0U && destination != nullptr && bytes != 0U &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void*>(address),
                           destination, bytes, &read) != FALSE &&
         read == bytes;
}

template <typename T>
void Store(NativeCommandStorageV1& storage, const std::size_t offset,
           const T& value) noexcept {
  std::memcpy(storage.bytes.data() + offset, &value, sizeof(value));
}

bool CallsComplete(const DomainConstructionExactNativeCallsV1& calls) {
  return calls.validate_building != nullptr &&
         calls.validate_holding != nullptr && calls.materialize != nullptr &&
         calls.receive != nullptr && calls.release != nullptr;
}

ExactSample MakeSample(
    const DomainConstructionConcreteCandidateCaptureV1& candidate,
    const DomainConstructionBorrowedCollectorFrameV1& frame,
    const ck3_11906::MainThreadExecutionStampV1& stamp,
    const bool exact_build_admitted, const bool session_live) noexcept {
  ExactSample sample{};
  sample.admission.exact_build_admitted = exact_build_admitted;
  sample.admission.application_main_thread_id = stamp.thread_id;
  sample.admission.current_thread_id = GetCurrentThreadId();
  sample.admission.session_live = session_live;
  sample.admission.expected_binding = candidate.expected_binding;
  sample.admission.observed_binding = frame.observed_binding;
  sample.candidate_row_address = frame.candidate_row_address;
  sample.cost_vector_address = frame.cost_vector_address;
  sample.resource_balance_vector_address =
      frame.resource_balance_vector_address;
  sample.final_legality = frame.final_legality;
  return sample;
}

bool CapturePublication(
    const DomainConstructionConcreteCandidateCaptureV1& candidate,
    const std::array<DomainConstructionBorrowedCollectorFrameV1, 2>& frames,
    const ck3_11906::MainThreadExecutionStampV1& stamp,
    const DomainConstructionApplicationMainRequestV1& request,
    Publication& publication) {
  research::DomainConstructionCostLegalityLiveObserverStateV1 observer{};
  const auto first = MakeSample(candidate, frames[0], stamp,
                                request.exact_build_admitted,
                                request.session_live);
  const auto second = MakeSample(candidate, frames[1], stamp,
                                 request.exact_build_admitted,
                                 request.session_live);
  if (!research::CaptureDomainConstructionCostLegalityDoubleSampleV1(
          observer, first, second, request.read_memory,
          request.read_context)) {
    return false;
  }
  publication =
      research::ReadDomainConstructionCostLegalityPublicationV1(observer);
  return publication.available;
}

bool PrepareNativeCommand(
    ExactBackendContextV1& backend,
    const research::DomainConstructionNativeCommandContextV1& command,
    const research::DomainConstructionTransientNativeSubmitContextV1&
        transient) noexcept {
  backend.command = {};
  backend.command_ready = false;
  std::uintptr_t primary = 0U;
  std::uintptr_t secondary = 0U;
  if (command.candidate_kind == CandidateKind::building_in_holding) {
    if (!AddRva(backend.module_base,
                kDomainConstructionBuildingPrimaryVtableRvaV1, primary) ||
        !AddRva(backend.module_base,
                kDomainConstructionBuildingSecondaryVtableRvaV1,
                secondary)) {
      return false;
    }
    Store(backend.command, 0x00U, primary);
    Store(backend.command, 0x18U, secondary);
    Store(backend.command, 0x20U, command.actor_or_holder_id);
    Store(backend.command, 0x24U, command.holding_province_id);
    Store(backend.command, 0x28U, command.candidate_selector);
    Store(backend.command, 0x2CU, command.building_type_id);
  } else if (command.candidate_kind == CandidateKind::new_holding) {
    if (transient.new_holding_candidate_object == 0U ||
        !AddRva(backend.module_base,
                kDomainConstructionHoldingPrimaryVtableRvaV1, primary) ||
        !AddRva(backend.module_base,
                kDomainConstructionHoldingSecondaryVtableRvaV1,
                secondary)) {
      return false;
    }
    Store(backend.command, 0x00U, primary);
    Store(backend.command, 0x18U, secondary);
    Store(backend.command, 0x20U, command.actor_or_holder_id);
    Store(backend.command, 0x24U, command.candidate_selector);
    Store(backend.command, 0x28U,
          transient.new_holding_candidate_object);
  } else {
    return false;
  }
  backend.command_ready = true;
  return true;
}

bool ValidateBackend(
    void* context,
    const research::DomainConstructionNativeCommandContextV1& command,
    const research::DomainConstructionTransientNativeSubmitContextV1&
        transient,
    bool& allowed) noexcept {
  auto& backend = *static_cast<ExactBackendContextV1*>(context);
  allowed = false;
  if (!PrepareNativeCommand(backend, command, transient)) return false;
  if (command.candidate_kind == CandidateKind::building_in_holding) {
    return backend.calls.validate_building(
        backend.calls.context, backend.command.bytes.data(), allowed);
  }
  return backend.calls.validate_holding(
      backend.calls.context, backend.command.bytes.data(),
      command.candidate_province_id, command.candidate_selector,
      transient.new_holding_candidate_object, allowed);
}

bool MaterializeBackend(
    void* context,
    const research::DomainConstructionNativeCommandContextV1&,
    const research::DomainConstructionTransientNativeSubmitContextV1&,
    std::uintptr_t& owned_command) noexcept {
  auto& backend = *static_cast<ExactBackendContextV1*>(context);
  owned_command = 0U;
  return backend.command_ready &&
         backend.calls.materialize(backend.calls.context,
                                   backend.command.bytes.data(),
                                   owned_command);
}

bool ReceiveBackend(void* context, std::uintptr_t& owned_command,
                    const std::uint32_t flags, bool& accepted,
                    std::uint64_t& sequence) noexcept {
  auto& backend = *static_cast<ExactBackendContextV1*>(context);
  return backend.calls.receive(backend.calls.context, owned_command, flags,
                               accepted, sequence);
}

bool ReleaseBackend(void* context,
                    std::uintptr_t& owned_command) noexcept {
  auto& backend = *static_cast<ExactBackendContextV1*>(context);
  return backend.calls.release(backend.calls.context, owned_command);
}

DomainConstructionNativeBackendAccessV1 BackendAccess(
    ExactBackendContextV1& backend) noexcept {
  return {&backend, ValidateBackend, MaterializeBackend, ReceiveBackend,
          ReleaseBackend};
}

bool ResolveCurrentProvince(const std::uintptr_t module_base,
                            const std::int32_t province_id,
                            std::uintptr_t& province) noexcept {
  province = 0U;
  if (province_id < 0) return false;
  std::uintptr_t storage_slot = 0U;
  std::uintptr_t fallback_slot = 0U;
  if (!AddRva(module_base, 0x570CC98U, storage_slot) ||
      !AddRva(module_base, 0x570CC58U, fallback_slot)) {
    return false;
  }
  std::uintptr_t storage = 0U;
  if (!ReadCurrent(storage_slot, &storage, sizeof(storage)) || storage == 0U) {
    return ReadCurrent(fallback_slot, &province, sizeof(province)) &&
           province != 0U;
  }
  const auto index = static_cast<std::uint32_t>(province_id) & 0x00FFFFFFU;
  std::uint32_t capacity = 0U;
  std::uintptr_t rows = 0U;
  if (!ReadCurrent(storage + 0x2CU, &capacity, sizeof(capacity)) ||
      !ReadCurrent(storage + 0x20U, &rows, sizeof(rows)) ||
      rows == 0U || index >= capacity) {
    return ReadCurrent(fallback_slot, &province, sizeof(province)) &&
           province != 0U;
  }
  const auto offset = static_cast<std::uintptr_t>(index) * 16U + 8U;
  if (offset < 8U ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - rows ||
      !ReadCurrent(rows + offset, &province, sizeof(province)) ||
      province == 0U) {
    return ReadCurrent(fallback_slot, &province, sizeof(province)) &&
           province != 0U;
  }
  std::int32_t observed_id = -1;
  if (!ReadCurrent(province + 0x08U, &observed_id, sizeof(observed_id)) ||
      observed_id != province_id) {
    return ReadCurrent(fallback_slot, &province, sizeof(province)) &&
           province != 0U;
  }
  return true;
}

bool CurrentValidateBuilding(void* context, const void* native_command,
                             bool& allowed) noexcept {
  const auto module_base = reinterpret_cast<std::uintptr_t>(context);
  std::uintptr_t target = 0U;
  if (native_command == nullptr ||
      !AddRva(module_base,
              research::kDomainConstructionBuildingValidatorRvaV1,
              target)) {
    return false;
  }
  using Function = bool(__fastcall*)(const void*, bool);
  allowed = reinterpret_cast<Function>(target)(native_command, false);
  return true;
}

bool CurrentValidateHolding(void* context, const void*,
                            const std::int32_t candidate_province_id,
                            const std::int32_t candidate_selector,
                            const std::uintptr_t candidate_object,
                            bool& allowed) noexcept {
  const auto module_base = reinterpret_cast<std::uintptr_t>(context);
  std::uintptr_t target = 0U;
  std::uintptr_t province = 0U;
  if (candidate_object == 0U ||
      !AddRva(module_base,
              research::kDomainConstructionHoldingValidatorRvaV1,
              target) ||
      !ResolveCurrentProvince(module_base, candidate_province_id, province)) {
    return false;
  }
  using Function = bool(__fastcall*)(void*, std::int32_t, void*, void*,
                                      std::uintptr_t, std::uint32_t);
  allowed = reinterpret_cast<Function>(target)(
      reinterpret_cast<void*>(province), candidate_selector,
      reinterpret_cast<void*>(candidate_object), nullptr, 0U, 2U);
  return true;
}

bool CurrentMaterialize(void*, void* native_command,
                        std::uintptr_t& owned_command) noexcept {
  owned_command = 0U;
  if (native_command == nullptr) return false;
  std::uintptr_t vtable = 0U;
  std::memcpy(&vtable, native_command, sizeof(vtable));
  if (vtable == 0U) return false;
  std::uintptr_t target = 0U;
  if (!ReadCurrent(vtable + 0x40U, &target, sizeof(target)) || target == 0U) {
    return false;
  }
  using Function = std::uintptr_t*(__fastcall*)(void*, std::uintptr_t*);
  std::uintptr_t wrapper = 0U;
  auto* returned = reinterpret_cast<Function>(target)(native_command,
                                                       &wrapper);
  if (returned != &wrapper || wrapper == 0U) return false;
  owned_command = wrapper;
  wrapper = 0U;
  return true;
}

bool CurrentReceive(void* context, std::uintptr_t& owned_command,
                    const std::uint32_t flags, bool& accepted,
                    std::uint64_t& command_sequence) noexcept {
  const auto module_base = reinterpret_cast<std::uintptr_t>(context);
  accepted = false;
  command_sequence = 0U;
  std::uintptr_t target = 0U;
  std::uintptr_t receiver = 0U;
  std::uint32_t sequence = 0U;
  if (owned_command == 0U ||
      !AddRva(module_base, research::kDomainConstructionReceiverRvaV1,
              target) ||
      !AddRva(module_base, kDomainConstructionReceiverSingletonRvaV1,
              receiver) ||
      !ReadCurrent(receiver + 0x3ECU, &sequence, sizeof(sequence))) {
    return false;
  }
  using Function = bool(__fastcall*)(void*, std::uintptr_t*, std::uint32_t);
  accepted = reinterpret_cast<Function>(target)(
      reinterpret_cast<void*>(receiver), &owned_command, flags);
  if (accepted) command_sequence = sequence;
  return true;
}

bool CurrentRelease(void*, std::uintptr_t& owned_command) noexcept {
  if (owned_command == 0U) return true;
  std::uintptr_t vtable = 0U;
  std::uintptr_t destroy = 0U;
  if (!ReadCurrent(owned_command, &vtable, sizeof(vtable)) || vtable == 0U ||
      !ReadCurrent(vtable, &destroy, sizeof(destroy)) || destroy == 0U) {
    return false;
  }
  using Function = void(__fastcall*)(void*, std::uint32_t);
  reinterpret_cast<Function>(destroy)(reinterpret_cast<void*>(owned_command),
                                      1U);
  owned_command = 0U;
  return true;
}

void AddRed(DomainConstructionApplicationMainResultV1& result,
            const DomainConstructionApplicationMainRedV1 red) noexcept {
  result.red_flags |= static_cast<std::uint32_t>(red);
}

}  // namespace

DomainConstructionExactNativeCallsV1
BindCurrentProcessDomainConstructionExactNativeCallsV1(
    const std::uintptr_t module_base) noexcept {
  if (module_base == 0U) return {};
  DomainConstructionExactNativeCallsV1 calls{};
  calls.context = reinterpret_cast<void*>(module_base);
  calls.production_exact_addresses = true;
  calls.validate_building = CurrentValidateBuilding;
  calls.validate_holding = CurrentValidateHolding;
  calls.materialize = CurrentMaterialize;
  calls.receive = CurrentReceive;
  calls.release = CurrentRelease;
  return calls;
}

bool SubmitPlayerWorldBuildingDirectActionV1(
    PlayerWorldBuildingDirectActionStateV1& state,
    const PlayerWorldBuildingDirectActionRequestV1& request,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept {
  using Phase = PlayerWorldBuildingDirectActionPhaseV1;
  using Failure = PlayerWorldBuildingDirectActionFailureV1;
  if (state.phase != Phase::idle) {
    state.failure = Failure::already_submitted;
    return false;
  }
  state = {};
  if (!request.exact_build_admitted || !request.session_live ||
      request.module_base == 0 || request.source == nullptr ||
      request.candidate == nullptr || stamp.thread_id == 0 ||
      stamp.thread_id != GetCurrentThreadId() || !stamp.paused ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.pump_epoch == 0) {
    state.phase = Phase::red;
    state.failure = Failure::frame_binding;
    return false;
  }
  const auto& source = *request.source;
  const auto& candidate = *request.candidate;
  if (!candidate.ready || !source.source_available ||
      source.failure != ck3_11906::PlayerWorldBuildingFailureV1::none ||
      !source.native_final_legality_evaluated ||
      !source.native_cost_evaluated || !source.player_gold_observed ||
      candidate.snapshot_revision != source.snapshot_revision ||
      candidate.proof_epoch != stamp.pump_epoch ||
      candidate.date_raw != stamp.date_raw ||
      candidate.date_raw != source.date_raw ||
      candidate.actor_character_id != source.player_character_id ||
      candidate.player_gold_before_raw != source.player_gold_raw ||
      candidate.stock_gold_cost_raw <= 0 ||
      candidate.stock_gold_cost_raw >= source.player_gold_raw ||
      candidate.gold_reserve_after_raw !=
          source.player_gold_raw - candidate.stock_gold_cost_raw ||
      !std::all_of(candidate.stock_cost_raw_native.begin() + 1,
                   candidate.stock_cost_raw_native.end(),
                   [](const std::int64_t raw) { return raw == 0; })) {
    state.phase = Phase::red;
    state.failure = Failure::candidate_drift;
    return false;
  }
  const auto sample = std::find_if(
      source.legal_samples.begin(), source.legal_samples.end(),
      [&candidate](const auto& row) {
        return row.native_cost_observed &&
               row.barony_title_id == candidate.barony_title_id &&
               row.province_id == candidate.province_id &&
               row.building_type_id == candidate.building_type_id &&
               row.slot_index == candidate.slot_index &&
               row.cost_raw_native == candidate.stock_cost_raw_native;
      });
  const auto active = std::find_if(
      source.active_constructions.begin(),
      source.active_constructions.end(),
      [&candidate](const auto& row) {
        return row.barony_title_id == candidate.barony_title_id &&
               row.province_id == candidate.province_id && !row.active;
      });
  if (sample == source.legal_samples.end() ||
      active == source.active_constructions.end()) {
    state.phase = Phase::red;
    state.failure = Failure::candidate_drift;
    return false;
  }
  auto calls = request.offline_fixture
                   ? request.native_calls
                   : BindCurrentProcessDomainConstructionExactNativeCallsV1(
                         request.module_base);
  if (!CallsComplete(calls) ||
      request.offline_fixture == calls.production_exact_addresses) {
    state.phase = Phase::red;
    state.failure = Failure::backend;
    return false;
  }
  ExactBackendContextV1 backend{request.module_base, calls, {}, false};
  research::DomainConstructionNativeCommandContextV1 command{};
  command.candidate_kind = CandidateKind::building_in_holding;
  command.actor_or_holder_id = candidate.actor_character_id;
  command.holding_province_id = candidate.province_id;
  command.candidate_selector = candidate.slot_index;
  command.building_type_id = candidate.building_type_id;
  research::DomainConstructionTransientNativeSubmitContextV1 transient{};
  bool allowed = false;
  ++state.validator_calls;
  if (!ValidateBackend(&backend, command, transient, allowed)) {
    state.phase = Phase::red;
    state.failure = Failure::validator;
    return false;
  }
  if (!allowed) {
    state.phase = Phase::rejected;
    state.failure = Failure::validator;
    return false;
  }
  std::uintptr_t owned_command = 0;
  ++state.materialize_calls;
  if (!MaterializeBackend(&backend, command, transient, owned_command) ||
      owned_command == 0) {
    if (owned_command != 0) (void)ReleaseBackend(&backend, owned_command);
    state.phase = Phase::red;
    state.failure = Failure::materialize;
    return false;
  }
  bool accepted = false;
  std::uint64_t sequence = 0;
  ++state.receiver_calls;
  const bool receiver_completed = ReceiveBackend(
      &backend, owned_command, research::kDomainConstructionReceiverFlagsV1,
      accepted, sequence);
  const bool leftover_closed =
      owned_command == 0 || ReleaseBackend(&backend, owned_command);
  if (!leftover_closed || owned_command != 0) {
    state.phase = Phase::red;
    state.failure = Failure::ownership;
    return false;
  }
  if (!receiver_completed || !accepted || sequence == 0) {
    state.phase = receiver_completed && !accepted ? Phase::rejected
                                                   : Phase::red;
    state.failure = Failure::receiver;
    return false;
  }
  state.phase = Phase::pending_receipt;
  state.failure = Failure::none;
  state.production_native_path = !request.offline_fixture;
  state.receiver_command_sequence = sequence;
  state.submitted = candidate;
  return true;
}

bool ObservePlayerWorldBuildingDirectActionReceiptV1(
    PlayerWorldBuildingDirectActionStateV1& state,
    const ck3_11906::PlayerWorldBuildingSourceResultV1& fresh,
    const std::uint64_t fresh_proof_epoch) noexcept {
  if (state.phase != PlayerWorldBuildingDirectActionPhaseV1::pending_receipt ||
      state.receiver_command_sequence == 0 ||
      !state.submitted.ready || !fresh.source_available ||
      fresh.failure != ck3_11906::PlayerWorldBuildingFailureV1::none ||
      fresh_proof_epoch <= state.submitted.proof_epoch ||
      fresh.snapshot_revision < state.submitted.snapshot_revision ||
      fresh.date_raw < state.submitted.date_raw ||
      fresh.player_character_id != state.submitted.actor_character_id) {
    return false;
  }
  const auto& submitted = state.submitted;
  const auto found = std::find_if(
      fresh.active_constructions.begin(),
      fresh.active_constructions.end(),
      [&submitted](const auto& row) {
        return row.active &&
               row.barony_title_id == submitted.barony_title_id &&
               row.province_id == submitted.province_id &&
               row.building_type_id == submitted.building_type_id &&
               row.slot_index == submitted.slot_index &&
               row.initiator_character_id == submitted.actor_character_id;
      });
  if (found == fresh.active_constructions.end()) return false;
  state.phase = PlayerWorldBuildingDirectActionPhaseV1::applied;
  return true;
}

bool ExecuteDomainConstructionApplicationMainRuntimeV1(
    void* context,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept {
  auto* execution =
      static_cast<DomainConstructionApplicationMainExecutionV1*>(context);
  if (execution == nullptr || execution->request == nullptr ||
      execution->result == nullptr) {
    return false;
  }
  const auto& request = *execution->request;
  auto& result = *execution->result;
  result = {};
  result.executor_completed = true;
  try {
    if (!request.exact_build_admitted || request.module_base == 0U) {
      AddRed(result, domain_construction_application_main_red_exact_build);
      return true;
    }
    if (stamp.thread_id == 0U || stamp.thread_id != GetCurrentThreadId() ||
        stamp.tls_main_thread_marker != 1U || stamp.tls_context == 0U) {
      AddRed(result, domain_construction_application_main_red_thread);
      return true;
    }
    if (!request.session_live) {
      AddRed(result, domain_construction_application_main_red_session);
      return true;
    }
    if (request.actor_or_holder_id < 0 || request.candidates.empty() ||
        request.read_memory == nullptr) {
      AddRed(result,
             domain_construction_application_main_red_collector_input);
      return true;
    }

    std::vector<Publication> first_publications;
    std::vector<Publication> second_publications;
    first_publications.reserve(request.candidates.size());
    second_publications.reserve(request.candidates.size());
    for (const auto& candidate : request.candidates) {
      if (candidate.expected_binding.generation == 0U ||
          (candidate.expected_binding.generation & 1U) != 0U ||
          candidate.expected_binding.proof_epoch != stamp.pump_epoch ||
          candidate.expected_binding.date_raw != stamp.date_raw) {
        AddRed(result,
               domain_construction_application_main_red_collector_input);
        return true;
      }
      Publication first{};
      Publication second{};
      if (!CapturePublication(candidate, candidate.first_publication, stamp,
                              request, first) ||
          !CapturePublication(candidate, candidate.second_publication, stamp,
                              request, second)) {
        AddRed(result, domain_construction_application_main_red_collector);
        return true;
      }
      first_publications.push_back(std::move(first));
      second_publications.push_back(std::move(second));
    }
    result.collected_candidate_count =
        static_cast<std::uint32_t>(first_publications.size());
    result.collector_ready = true;
    if (!PrepareDomainConstructionSharedCandidateV1(
            result.shared, first_publications, second_publications)) {
      AddRed(result, domain_construction_application_main_red_candidate);
      return true;
    }
    result.shared.candidate_live = !request.offline_fixture;

    std::uintptr_t new_holding_candidate_object = 0U;
    for (std::size_t index = 0; index < first_publications.size(); ++index) {
      const auto& publication = first_publications[index];
      if (publication.candidate.candidate_id !=
          result.shared.candidate.candidate_id) {
        continue;
      }
      if (publication.candidate.candidate_kind == CandidateKind::new_holding) {
        const auto& source = request.candidates[index];
        new_holding_candidate_object =
            source.first_publication[0].new_holding_candidate_object;
        for (const auto& frame : source.first_publication) {
          if (frame.new_holding_candidate_object !=
              new_holding_candidate_object) {
            AddRed(result,
                   domain_construction_application_main_red_collector);
            return true;
          }
        }
        for (const auto& frame : source.second_publication) {
          if (frame.new_holding_candidate_object !=
              new_holding_candidate_object) {
            AddRed(result,
                   domain_construction_application_main_red_collector);
            return true;
          }
        }
      }
      break;
    }

    auto calls = request.native_calls;
    if (!request.offline_fixture) {
      calls = BindCurrentProcessDomainConstructionExactNativeCallsV1(
          request.module_base);
    }
    const bool exactly_one_backend =
        request.offline_fixture != calls.production_exact_addresses;
    if (!exactly_one_backend || !CallsComplete(calls)) {
      AddRed(result, domain_construction_application_main_red_backend);
      return true;
    }
    ExactBackendContextV1 backend{request.module_base, calls, {}, false};
    DomainConstructionNativeBackendEnvironmentV1 environment{};
    environment.exact_build_admitted = request.exact_build_admitted;
    environment.application_main_thread = true;
    environment.concrete_native_backend_bound =
        calls.production_exact_addresses;
    environment.offline_fixture_backend = request.offline_fixture;
    if (!SubmitDomainConstructionSharedCandidateV1(
            result.shared, environment, BackendAccess(backend),
            result.shared.candidate.binding, request.actor_or_holder_id,
            new_holding_candidate_object)) {
      AddRed(result, domain_construction_application_main_red_backend);
      return true;
    }
    result.submit_accepted = true;
    return true;
  } catch (...) {
    AddRed(result, domain_construction_application_main_red_backend);
    return true;
  }
}

}  // namespace xar::ck3::shared
