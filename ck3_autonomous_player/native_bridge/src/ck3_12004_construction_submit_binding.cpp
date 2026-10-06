#include "ck3_12004_construction_submit_binding.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

#include <windows.h>

namespace xar::ck3_12004 {
namespace {

struct alignas(void*) NativeCommand final {
  std::array<std::byte, kConstructionNativeCommandBytes> bytes{};
};
static_assert(sizeof(NativeCommand) == 0x30U);

bool AddRva(const std::uintptr_t base, const std::uintptr_t rva,
            std::uintptr_t& address) noexcept {
  if (base == 0U ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    address = 0U;
    return false;
  }
  address = base + rva;
  return true;
}

bool ReadCurrent(const std::uintptr_t address, void* destination,
                 const std::size_t bytes) noexcept {
  SIZE_T read = 0;
  return address != 0U && destination != nullptr && bytes != 0U &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void*>(address),
                           destination, bytes, &read) != FALSE && read == bytes;
}

template <typename T>
void Store(NativeCommand& command, const std::size_t offset,
           const T value) noexcept {
  std::memcpy(command.bytes.data() + offset, &value, sizeof(value));
}

bool CurrentValidateBuilding(void* context, const void* command,
                             bool& allowed) noexcept {
  allowed = false;
  std::uintptr_t target = 0;
  if (command == nullptr ||
      !AddRva(reinterpret_cast<std::uintptr_t>(context),
              kConstructionBuildingValidatorRva, target)) return false;
  using Function = bool(__fastcall*)(const void*, void*);
  allowed = reinterpret_cast<Function>(target)(command, nullptr);
  return true;
}

bool CurrentMaterialize(void* context, void* command,
                        std::uintptr_t& owned_command) noexcept {
  owned_command = 0;
  std::uintptr_t target = 0;
  if (command == nullptr ||
      !AddRva(reinterpret_cast<std::uintptr_t>(context),
              kConstructionBuildingMaterializeRva, target)) return false;
  using Function = std::uintptr_t*(__fastcall*)(void*, std::uintptr_t*);
  std::uintptr_t wrapper = 0;
  auto* returned = reinterpret_cast<Function>(target)(command, &wrapper);
  if (returned != &wrapper || wrapper == 0) return false;
  owned_command = wrapper;
  return true;
}

bool CurrentReceive(void* context, std::uintptr_t& owned_command,
                    const std::uint32_t flags, bool& accepted,
                    std::uint64_t& command_sequence) noexcept {
  accepted = false;
  command_sequence = 0;
  const auto module_base = reinterpret_cast<std::uintptr_t>(context);
  const auto commands = BindCommandImage12004(module_base, kExecutableSha256);
  std::uintptr_t phase_flags_address = 0;
  std::uint8_t phase_flags = 0;
  std::uint32_t sequence = 0;
  if (owned_command == 0 || !commands.enabled ||
      commands.command_manager == nullptr || commands.queue_owned_command == nullptr ||
      !AddRva(module_base, kConstructionCommandPhaseFlagsRva,
              phase_flags_address) ||
      !ReadCurrent(phase_flags_address, &phase_flags, sizeof(phase_flags)) ||
      !ReadCurrent(reinterpret_cast<std::uintptr_t>(commands.command_manager) + 0x3ECU,
                   &sequence, sizeof(sequence))) return false;
  // Preserve the actual .4 0x37EBC20 wrapper's queue-or-destroy branch. The
  // direct receiver is used only to retain its bool ACK and sequence.
  if ((phase_flags & 0xFDU) != 0U) return true;
  void* native_owned = reinterpret_cast<void*>(owned_command);
  accepted = commands.queue_owned_command(commands.command_manager,
                                          &native_owned, flags);
  owned_command = reinterpret_cast<std::uintptr_t>(native_owned);
  if (accepted) command_sequence = sequence;
  return true;
}

bool CurrentRelease(void*, std::uintptr_t& owned_command) noexcept {
  if (owned_command == 0) return true;
  std::uintptr_t vtable = 0;
  std::uintptr_t destroy = 0;
  if (!ReadCurrent(owned_command, &vtable, sizeof(vtable)) || vtable == 0 ||
      !ReadCurrent(vtable, &destroy, sizeof(destroy)) || destroy == 0) {
    return false;
  }
  using Function = void(__fastcall*)(void*, std::uint32_t);
  reinterpret_cast<Function>(destroy)(reinterpret_cast<void*>(owned_command),
                                      1U);
  owned_command = 0;
  return true;
}

bool BuildingCallsComplete(const ConstructionNativeCallsV1& calls) noexcept {
  return calls.validate_building != nullptr && calls.materialize != nullptr &&
         calls.receive != nullptr && calls.release != nullptr;
}

}  // namespace

ConstructionNativeCallsV1
BindCurrentProcessDomainConstructionExactNativeCallsV1(
    const std::uintptr_t module_base) noexcept {
  if (!BindCoreImage(module_base, kExecutableSha256).enabled ||
      !BindCommandImage12004(module_base, kExecutableSha256).enabled) return {};
  ConstructionNativeCallsV1 calls{};
  calls.context = reinterpret_cast<void*>(module_base);
  calls.production_exact_addresses = true;
  calls.validate_building = CurrentValidateBuilding;
  calls.materialize = CurrentMaterialize;
  calls.receive = CurrentReceive;
  calls.release = CurrentRelease;
  return calls;
}

bool SubmitPlayerWorldBuildingDirectActionV1(
    ConstructionActionStateV1& state,
    const ConstructionActionRequestV1& request,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept {
  using Phase = ck3::shared::PlayerWorldBuildingDirectActionPhaseV1;
  using Failure = ck3::shared::PlayerWorldBuildingDirectActionFailureV1;
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
  const auto idle = std::find_if(
      source.active_constructions.begin(), source.active_constructions.end(),
      [&candidate](const auto& row) {
        return row.barony_title_id == candidate.barony_title_id &&
               row.province_id == candidate.province_id && !row.active;
      });
  if (sample == source.legal_samples.end() ||
      idle == source.active_constructions.end()) {
    state.phase = Phase::red;
    state.failure = Failure::candidate_drift;
    return false;
  }
  const auto calls = request.offline_fixture
                         ? request.native_calls
                         : BindCurrentProcessDomainConstructionExactNativeCallsV1(
                               request.module_base);
  if (!BuildingCallsComplete(calls) ||
      request.offline_fixture == calls.production_exact_addresses) {
    state.phase = Phase::red;
    state.failure = Failure::backend;
    return false;
  }
  NativeCommand command{};
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  if (!AddRva(request.module_base, kConstructionBuildingPrimaryVtableRva,
              primary) ||
      !AddRva(request.module_base, kConstructionBuildingSecondaryVtableRva,
              secondary)) {
    state.phase = Phase::red;
    state.failure = Failure::backend;
    return false;
  }
  Store(command, 0x00U, primary);
  Store(command, 0x18U, secondary);
  Store(command, 0x20U, candidate.actor_character_id);
  Store(command, 0x24U, candidate.province_id);
  Store(command, 0x28U, candidate.slot_index);
  Store(command, 0x2CU, candidate.building_type_id);
  bool allowed = false;
  ++state.validator_calls;
  if (!calls.validate_building(calls.context, command.bytes.data(), allowed)) {
    state.phase = Phase::red;
    state.failure = Failure::validator;
    return false;
  }
  if (!allowed) {
    state.phase = Phase::rejected;
    state.failure = Failure::validator;
    return false;
  }
  std::uintptr_t owned = 0;
  ++state.materialize_calls;
  if (!calls.materialize(calls.context, command.bytes.data(), owned) ||
      owned == 0) {
    if (owned != 0) (void)calls.release(calls.context, owned);
    state.phase = Phase::red;
    state.failure = Failure::materialize;
    return false;
  }
  bool accepted = false;
  std::uint64_t sequence = 0;
  ++state.receiver_calls;
  const auto completed = calls.receive(calls.context, owned,
                                       kConstructionReceiverFlags,
                                       accepted, sequence);
  const auto closed = owned == 0 || calls.release(calls.context, owned);
  if (!closed || owned != 0) {
    state.phase = Phase::red;
    state.failure = Failure::ownership;
    return false;
  }
  if (!completed || !accepted || sequence == 0) {
    state.phase = completed && !accepted ? Phase::rejected : Phase::red;
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
    ConstructionActionStateV1& state,
    const ck3_11906::PlayerWorldBuildingSourceResultV1& fresh,
    const std::uint64_t fresh_proof_epoch) noexcept {
  using Phase = ck3::shared::PlayerWorldBuildingDirectActionPhaseV1;
  if (state.phase != Phase::pending_receipt ||
      state.receiver_command_sequence == 0 ||
      !ck3_11906::ObservePlayerWorldBuildingMaterialResultV1(
          state.submitted, fresh, fresh_proof_epoch)) return false;
  state.phase = Phase::applied;
  return true;
}

}  // namespace xar::ck3_12004
