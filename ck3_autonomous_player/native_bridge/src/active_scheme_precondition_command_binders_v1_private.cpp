#include "active_scheme_precondition_command_binders_v1_private.hpp"

#include <algorithm>
#include <bit>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::bridge {
namespace {

using BinderFailure =
    ActiveSchemePreconditionCommandBindersV1PrivateFailure;
using BinderState = ActiveSchemePreconditionCommandBindersV1PrivateState;
using CharacterLease =
    ActiveSchemeSemanticActionV1PrivateNativeCharacterLease;
using CommandLease = ActiveSchemeSemanticActionV1PrivateNativeCommandLease;
using ContextLease = ActiveSchemeSemanticActionV1PrivateNativeContextLease;
using DefinitionLease =
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease;
using Frame = ActiveSchemeStateV1PrivateSourceFrame;
using RouteLease =
    ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease;
using ValidationProof =
    ActiveSchemeSemanticActionV1PrivateNativeValidationProof;

constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::int32_t kMaximumCharacters = 1 << 20;
constexpr std::uint32_t kIdentitySlotMask = 0x00FFFFFFU;
constexpr unsigned kIdentityGenerationShift = 24U;
constexpr std::uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr std::uint64_t kFnvPrime = 1099511628211ULL;
constexpr std::array<std::string_view, 4> kMurderStarters{
    "agent_focus_balance", "agent_focus_success", "agent_focus_speed",
    "agent_focus_secrecy"};

struct NativeStringView {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::uint8_t owned = 0;
  std::array<std::byte, 3> padding{};
};
static_assert(sizeof(NativeStringView) == 0x10);
static_assert(sizeof(void *) == 8);

bool CheckedAddress(std::uintptr_t base, std::size_t offset,
                    std::uintptr_t &output) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = 0;
    return false;
  }
  output = base + offset;
  return true;
}

std::uint64_t Hash(std::uint64_t hash, std::uint64_t value) noexcept {
  for (unsigned shift = 0; shift != 64; shift += 8) {
    hash ^= (value >> shift) & 0xFFU;
    hash *= kFnvPrime;
  }
  return hash;
}

std::uint64_t Generation(std::uint64_t proof_epoch,
                         std::uintptr_t address, std::uint64_t first,
                         std::uint64_t second) noexcept {
  auto value = Hash(kFnvOffset, proof_epoch);
  value = Hash(value, address);
  value = Hash(value, first);
  value = Hash(value, second);
  return value == 0 ? 1 : value;
}

bool DirectRead(void *, const void *address, void *output,
                std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
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

bool DirectWrite(void *, void *address, const void *input,
                 std::size_t size) noexcept {
  if (address == nullptr || input == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(address, input, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(address, input, size);
  return true;
#endif
}

bool DirectGetter(void *, std::uintptr_t address,
                  std::uintptr_t &output) noexcept {
  using Function = void *(*)();
  output = reinterpret_cast<std::uintptr_t>(
      reinterpret_cast<Function>(address)());
  return output != 0;
}

bool DirectHash(void *, std::uintptr_t address, std::uintptr_t database,
                std::string_view key, std::int32_t &output) noexcept {
  using Function = std::int32_t (*)(void *, const char *, std::uint32_t);
  if (database == 0 || key.empty() ||
      key.size() > (std::numeric_limits<std::uint32_t>::max)()) {
    output = 0;
    return false;
  }
  output = reinterpret_cast<Function>(address)(
      reinterpret_cast<void *>(database), key.data(),
      static_cast<std::uint32_t>(key.size()));
  return output != 0;
}

bool DirectLookup(void *, std::uintptr_t address, std::uintptr_t database,
                  std::int32_t hash, std::uintptr_t &output) noexcept {
  using Function = void *(*)(void *, std::int32_t);
  output = reinterpret_cast<std::uintptr_t>(
      reinterpret_cast<Function>(address)(reinterpret_cast<void *>(database),
                                          hash));
  return output != 0;
}

bool DirectResolveIdentifier(void *, std::uintptr_t table_address,
                             std::uintptr_t lookup_address,
                             std::string_view key,
                             std::int32_t &output) noexcept {
  using GetTable = void *(*)();
  using Lookup = std::int32_t *(*)(void *, std::int32_t *, const void *);
  output = -1;
  if (key.empty() ||
      key.size() >
          static_cast<std::size_t>((std::numeric_limits<std::int32_t>::max)())) {
    return false;
  }
  void *const table = reinterpret_cast<GetTable>(table_address)();
  const NativeStringView view{key.data(), static_cast<std::int32_t>(key.size())};
  return table != nullptr &&
         reinterpret_cast<Lookup>(lookup_address)(table, &output, &view) !=
             nullptr &&
         output >= 0;
}

bool DirectConstructContext(void *, std::uintptr_t address, void *storage,
                            std::uintptr_t interaction, std::int32_t actor,
                            std::int32_t target) noexcept {
  using Function = void *(*)(void *, void *, std::int32_t, std::int32_t,
                             void *, bool);
  return reinterpret_cast<Function>(address)(
             storage, reinterpret_cast<void *>(interaction), actor, target,
             nullptr, false) == storage;
}

bool DirectRefresh(void *, std::uintptr_t address, void *context) noexcept {
  using Function = void (*)(void *, bool);
  reinterpret_cast<Function>(address)(context, true);
  return true;
}

bool DirectFinalize(void *, std::uintptr_t address, void *context) noexcept {
  using Function = void (*)(void *);
  reinterpret_cast<Function>(address)(context);
  return true;
}

bool DirectValidate(void *, std::uintptr_t address, void *context,
                    bool &output) noexcept {
  using Function = bool (*)(void *, void *);
  output = reinterpret_cast<Function>(address)(context, nullptr);
  return true;
}

bool DirectConstructCommand(void *, std::uintptr_t address, void *storage,
                            const void *context) noexcept {
  using Function = void *(*)(void *, const void *);
  return reinterpret_cast<Function>(address)(storage, context) == storage;
}

bool DirectSubmit(void *, std::uintptr_t address, std::uintptr_t manager,
                  void *command, std::uint32_t channel,
                  bool &accepted) noexcept {
  using Function = bool (*)(void *, void *, std::uint32_t);
  accepted = reinterpret_cast<Function>(address)(
      reinterpret_cast<void *>(manager), command, channel);
  return true;
}

bool DirectDestroy(void *, std::uintptr_t address, void *context) noexcept {
  using Function = void (*)(void *);
  reinterpret_cast<Function>(address)(context);
  return true;
}

bool OperationsEmpty(
    const ActiveSchemePreconditionCommandBindersV1PrivateOperations
        &operations) noexcept {
  return operations.read_memory == nullptr &&
         operations.write_memory == nullptr &&
         operations.invoke_database_getter == nullptr &&
         operations.invoke_stable_key_hash == nullptr &&
         operations.invoke_loaded_lookup == nullptr &&
         operations.resolve_script_identifier == nullptr &&
         operations.construct_context == nullptr &&
         operations.refresh_context == nullptr &&
         operations.finalize_context == nullptr &&
         operations.validate_context == nullptr &&
         operations.construct_command == nullptr &&
         operations.submit == nullptr && operations.destroy_context == nullptr;
}

bool OperationsComplete(
    const ActiveSchemePreconditionCommandBindersV1PrivateOperations
        &operations) noexcept {
  return operations.read_memory != nullptr &&
         operations.write_memory != nullptr &&
         operations.invoke_database_getter != nullptr &&
         operations.invoke_stable_key_hash != nullptr &&
         operations.invoke_loaded_lookup != nullptr &&
         operations.resolve_script_identifier != nullptr &&
         operations.construct_context != nullptr &&
         operations.refresh_context != nullptr &&
         operations.finalize_context != nullptr &&
         operations.validate_context != nullptr &&
         operations.construct_command != nullptr &&
         operations.submit != nullptr && operations.destroy_context != nullptr;
}

ActiveSchemePreconditionCommandBindersV1PrivateOperations
DirectOperations() noexcept {
  return {&DirectRead,          &DirectWrite,
          &DirectGetter,        &DirectHash,
          &DirectLookup,        &DirectResolveIdentifier,
          &DirectConstructContext, &DirectRefresh,
          &DirectFinalize,      &DirectValidate,
          &DirectConstructCommand, &DirectSubmit,
          &DirectDestroy};
}

template <typename T>
bool Read(const BinderState &state, std::uintptr_t base, std::size_t offset,
          T &output) noexcept {
  std::uintptr_t address = 0;
  return CheckedAddress(base, offset, address) &&
         state.operations.read_memory(
             state.operation_context, reinterpret_cast<const void *>(address),
             &output, sizeof(output));
}

bool WriteByte(const BinderState &state, std::uintptr_t base,
               std::size_t offset, std::uint8_t value) noexcept {
  std::uintptr_t address = 0;
  return CheckedAddress(base, offset, address) &&
         state.operations.write_memory(
             state.operation_context, reinterpret_cast<void *>(address),
             &value, sizeof(value));
}

bool CurrentFrame(BinderState &state, Frame &output) noexcept {
  output = {};
  return state.attached && state.operation_active &&
         state.active_current_thread_id != 0 &&
         state.active_current_thread_id ==
             state.active_application_main_thread_id &&
         state.source_access.capture_frame != nullptr &&
         state.source_access.capture_frame(state.source_access.context,
                                           output) &&
         output.paused && output.capture_epoch != 0;
}

bool SameFrame(const Frame &left, const Frame &right) noexcept {
  return left.capture_epoch == right.capture_epoch &&
         left.date_raw == right.date_raw &&
         left.played_character_id == right.played_character_id &&
         left.paused == right.paused;
}

bool ResolveCharacterAddress(BinderState &state, std::uint32_t full_id,
                             std::uintptr_t &output) noexcept {
  output = 0;
  std::uintptr_t storage_slot = 0;
  std::uintptr_t fallback_slot = 0;
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (!CheckedAddress(state.module_base, kActiveSchemeCharacterStorageSlotRva,
                      storage_slot) ||
      !CheckedAddress(state.module_base,
                      kActiveSchemeCharacterFallbackSlotRva, fallback_slot) ||
      !Read(state, storage_slot, 0, storage) ||
      !Read(state, fallback_slot, 0, fallback) || storage == 0 ||
      !Read(state, storage, kStorageSlotsOffset, slots) || slots == 0 ||
      !Read(state, storage, kStorageCapacityOffset, capacity) || capacity <= 0 ||
      capacity > kMaximumCharacters) {
    return false;
  }
  const auto slot = full_id & kIdentitySlotMask;
  if (slot >= static_cast<std::uint32_t>(capacity) ||
      !Read(state, slots,
            static_cast<std::size_t>(slot) * kStorageSlotStride +
                kStorageObjectOffset,
            output) ||
      output == 0 || output == fallback) {
    output = 0;
    return false;
  }
  std::uint32_t observed = 0;
  if (!Read(state, output, kCharacterIdentityOffset, observed) ||
      observed != full_id) {
    output = 0;
    return false;
  }
  return true;
}

bool VerifyExactImage(BinderState &state) noexcept {
  std::array<std::uint8_t, 24> observed{};
  for (const auto &signature :
       kActiveSchemePreconditionCommandBindersV1PrivateSignatures) {
    std::uintptr_t address = 0;
    observed.fill(0);
    if (!CheckedAddress(state.module_base, signature.rva, address) ||
        !state.operations.read_memory(
            state.operation_context, reinterpret_cast<const void *>(address),
            observed.data(), signature.size) ||
        !std::equal(observed.begin(), observed.begin() + signature.size,
                    signature.bytes.begin())) {
      return false;
    }
  }
  return true;
}

bool Begin(BinderState &state,
           const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
           BinderFailure &failure) noexcept {
  failure = BinderFailure::not_bound;
  if (!state.attached || !state.readiness.callback_core_ready) return false;
  if (state.operation_active) {
    failure = BinderFailure::reentrant_execution;
    return false;
  }
  if (execution.current_thread_id == 0 ||
      execution.current_thread_id != execution.application_main_thread_id) {
    failure = BinderFailure::not_application_main_thread;
    return false;
  }
  state.operation_active = true;
  state.native_release_failed = false;
  state.active_current_thread_id = execution.current_thread_id;
  state.active_application_main_thread_id =
      execution.application_main_thread_id;
  failure = BinderFailure::none;
  return true;
}

void End(BinderState &state) noexcept {
  state.active_current_thread_id = 0;
  state.active_application_main_thread_id = 0;
  state.operation_active = false;
}

bool ValidRequest(const ActiveSchemeSemanticActionV1PrivateRequest &request,
                  std::string_view &scheme_type) noexcept {
  if (request.request_id.empty() || request.actor_character_id <= 0 ||
      request.target_kind != ActiveSchemeStateV1PrivateTargetKind::character ||
      request.target_id <= 0 ||
      request.actor_character_id == request.target_id) {
    return false;
  }
  if (request.interaction_key == "sway_interaction") {
    scheme_type = "sway";
    return request.selected_starter_package.empty();
  }
  if (request.interaction_key == "start_murder_interaction") {
    scheme_type = "murder";
    return std::find(kMurderStarters.begin(), kMurderStarters.end(),
                     request.selected_starter_package) !=
           kMurderStarters.end();
  }
  return false;
}

bool ResolveCharacterThunk(void *context, std::uint32_t full_id,
                           CharacterLease &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  output = {};
  Frame before{};
  Frame after{};
  std::uintptr_t first = 0;
  std::uintptr_t second = 0;
  const auto generation = full_id >> kIdentityGenerationShift;
  if (generation == 0 || !CurrentFrame(state, before) ||
      !ResolveCharacterAddress(state, full_id, first) ||
      !ResolveCharacterAddress(state, full_id, second) || first != second ||
      !CurrentFrame(state, after) || !SameFrame(before, after)) {
    return false;
  }
  output = {true, first, full_id, full_id & kIdentitySlotMask, generation,
            before.capture_epoch};
  return true;
}

bool ReadMemoryThunk(void *context, const void *address, void *output,
                     std::size_t size) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  return state.attached && state.operations.read_memory(
                               state.operation_context, address, output, size);
}

bool ResolveRouteThunk(void *context, RouteLease &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  output = {};
  Frame before{};
  Frame after{};
  std::uintptr_t manager = 0;
  std::uintptr_t submitter = 0;
  if (!CurrentFrame(state, before) ||
      !CheckedAddress(state.module_base, kActiveSchemeCommandManagerRva,
                      manager) ||
      !CheckedAddress(
          state.module_base,
          kActiveSchemeSemanticActionV1PrivateSubmitCommandRva, submitter) ||
      !CurrentFrame(state, after) || !SameFrame(before, after)) {
    return false;
  }
  output.identity_round_trip = true;
  output.command_manager_address = manager;
  output.command_manager_generation =
      Generation(before.capture_epoch, manager, submitter, 0x0E);
  output.submitter_address = submitter;
  output.proof_epoch = before.capture_epoch;
  return true;
}

bool ReadOptions(BinderState &state, std::uintptr_t definition,
                 std::uintptr_t context, bool murder,
                 std::string_view selected) noexcept {
  std::uintptr_t rows = 0;
  std::int32_t definition_count = 0;
  bool exclusive = false;
  std::uintptr_t selected_bytes = 0;
  std::int32_t selected_count = 0;
  if (!Read(state, definition, kActiveSchemeDefinitionOptionsOffset, rows) ||
      !Read(state, definition, kActiveSchemeDefinitionOptionsCountOffset,
            definition_count) ||
      !Read(state, definition, kActiveSchemeDefinitionOptionsExclusiveOffset,
            exclusive) ||
      !Read(state, context, kActiveSchemeContextSelectedOptionsOffset,
            selected_bytes) ||
      !Read(state, context, kActiveSchemeContextSelectedOptionsCountOffset,
            selected_count)) {
    return false;
  }
  if (!murder) {
    return rows == 0 && definition_count == 0 && !exclusive &&
           selected_count == 0 && selected.empty();
  }
  if (rows == 0 || definition_count != 4 || !exclusive ||
      selected_bytes == 0 || selected_count != 4) {
    return false;
  }
  std::uintptr_t table_function = 0;
  std::uintptr_t lookup_function = 0;
  if (!CheckedAddress(state.module_base,
                      kActiveSchemePreconditionGetScriptIdentifierTableRva,
                      table_function) ||
      !CheckedAddress(state.module_base,
                      kActiveSchemePreconditionLookupScriptIdentifierRva,
                      lookup_function)) {
    return false;
  }
  bool found = false;
  for (std::size_t index = 0; index < kMurderStarters.size(); ++index) {
    std::int32_t expected_flag = -1;
    std::int32_t observed_flag = -1;
    if (!state.operations.resolve_script_identifier(
            state.operation_context, table_function, lookup_function,
            kMurderStarters[index], expected_flag) ||
        !Read(state, rows, index * kActiveSchemeDefinitionOptionStride +
                              kActiveSchemeDefinitionOptionFlagOffset,
              observed_flag) ||
        observed_flag != expected_flag) {
      return false;
    }
    const bool chosen = selected == kMurderStarters[index];
    found = found || chosen;
    if (!WriteByte(state, selected_bytes, index, chosen ? 1U : 0U)) {
      return false;
    }
  }
  return found;
}

bool VerifySelectedOptions(BinderState &state, std::uintptr_t context,
                           bool murder, std::string_view selected) noexcept {
  std::uintptr_t bytes = 0;
  std::int32_t count = 0;
  if (!Read(state, context, kActiveSchemeContextSelectedOptionsOffset, bytes) ||
      !Read(state, context, kActiveSchemeContextSelectedOptionsCountOffset,
            count)) {
    return false;
  }
  if (!murder) return count == 0 && selected.empty();
  if (bytes == 0 || count != 4) return false;
  std::uint32_t selected_count = 0;
  for (std::size_t index = 0; index < kMurderStarters.size(); ++index) {
    std::uint8_t value = 0;
    if (!Read(state, bytes, index, value) || value > 1U ||
        (value == 1U) != (selected == kMurderStarters[index])) {
      return false;
    }
    selected_count += value;
  }
  return selected_count == 1;
}

bool ConstructContextThunk(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateCommand &semantic_command,
    const CharacterLease &actor, const CharacterLease &target,
    const DefinitionLease &interaction, ContextLease &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  output = {};
  if (!state.attached || !state.operation_active ||
      state.native_context_active || state.native_command_active ||
      actor.proof_epoch == 0 || actor.proof_epoch != target.proof_epoch ||
      actor.proof_epoch != interaction.proof_epoch) {
    return false;
  }
  std::uintptr_t constructor = 0;
  std::uintptr_t refresh = 0;
  std::uintptr_t finalize = 0;
  if (!CheckedAddress(
          state.module_base,
          kActiveSchemeSemanticActionV1PrivateConstructContextRva,
          constructor) ||
      !CheckedAddress(state.module_base,
                      kActiveSchemePreconditionRefreshContextRva, refresh) ||
      !CheckedAddress(state.module_base,
                      kActiveSchemePreconditionFinalizeContextRva, finalize)) {
    return false;
  }
  state.context_storage.fill(std::byte{});
  void *const storage = state.context_storage.data();
  const auto address = reinterpret_cast<std::uintptr_t>(storage);
  if (!state.operations.construct_context(
          state.operation_context, constructor, storage,
          interaction.native_address,
          std::bit_cast<std::int32_t>(actor.observed_full_id),
          std::bit_cast<std::int32_t>(target.observed_full_id))) {
    return false;
  }
  state.native_context_active = true;
  output.native_address = address;
  output.generation = Generation(actor.proof_epoch, address,
                                 actor.observed_full_id,
                                 interaction.definition_generation);
  output.proof_epoch = actor.proof_epoch;

  std::uint32_t observed_actor = 0;
  std::uint32_t observed_target = 0;
  const bool murder =
      semantic_command.interaction_key == "start_murder_interaction";
  if (!Read(state, address, kActiveSchemeContextActorOffset, observed_actor) ||
      !Read(state, address, kActiveSchemeContextRecipientOffset,
            observed_target) ||
      observed_actor != actor.observed_full_id ||
      observed_target != target.observed_full_id ||
      !ReadOptions(state, interaction.native_address, address, murder,
                   semantic_command.selected_starter_package) ||
      !state.operations.refresh_context(state.operation_context, refresh,
                                        storage) ||
      !state.operations.finalize_context(state.operation_context, finalize,
                                         storage) ||
      !VerifySelectedOptions(state, address, murder,
                             semantic_command.selected_starter_package)) {
    return false;
  }
  output.identity_round_trip = true;
  output.actor_full_id = observed_actor;
  output.target_full_id = observed_target;
  output.interaction_stable_key_hash = interaction.stable_key_hash;
  output.interaction_generation = interaction.definition_generation;
  output.starter_options_exclusive = murder;
  output.starter_option_count = murder ? 4U : 0U;
  output.selected_starter_package = semantic_command.selected_starter_package;
  return true;
}

bool ValidateContextThunk(void *context, const ContextLease &native_context,
                          ValidationProof &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  output = {};
  Frame before{};
  Frame after{};
  std::uintptr_t validator = 0;
  bool valid = false;
  if (!state.native_context_active ||
      native_context.native_address !=
          reinterpret_cast<std::uintptr_t>(state.context_storage.data()) ||
      !CurrentFrame(state, before) ||
      before.capture_epoch != native_context.proof_epoch ||
      !CheckedAddress(
          state.module_base,
          kActiveSchemeSemanticActionV1PrivateValidateContextRva, validator) ||
      !state.operations.validate_context(
          state.operation_context, validator,
          reinterpret_cast<void *>(native_context.native_address), valid) ||
      !CurrentFrame(state, after) || !SameFrame(before, after)) {
    return false;
  }
  output = {true, valid, validator, native_context.native_address,
            native_context.generation, before.capture_epoch};
  return true;
}

bool ConstructCommandThunk(void *context, const ContextLease &native_context,
                           CommandLease &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  output = {};
  if (!state.native_context_active || state.native_command_active ||
      native_context.native_address !=
          reinterpret_cast<std::uintptr_t>(state.context_storage.data())) {
    return false;
  }
  std::uintptr_t constructor = 0;
  if (!CheckedAddress(
          state.module_base,
          kActiveSchemeSemanticActionV1PrivateConstructCommandRva,
          constructor)) {
    return false;
  }
  state.command_storage.fill(std::byte{});
  void *const storage = state.command_storage.data();
  const auto address = reinterpret_cast<std::uintptr_t>(storage);
  if (!state.operations.construct_command(
          state.operation_context, constructor, storage,
          reinterpret_cast<const void *>(native_context.native_address))) {
    std::uintptr_t copied_context_tag = 0;
    if (Read(state, address, kActiveSchemeCopiedCommandContextOffset,
             copied_context_tag) &&
        copied_context_tag != 0) {
      // Match the exact generic command path: a partially constructed inline
      // context still needs the command release callback.
      state.native_command_active = true;
      output.native_address = address;
    }
    return false;
  }
  state.native_command_active = true;
  output.native_address = address;
  output.generation = Generation(native_context.proof_epoch, address,
                                 native_context.generation,
                                 native_context.interaction_stable_key_hash);
  output.proof_epoch = native_context.proof_epoch;
  output.constructor_address = constructor;
  output.copied_context_address = address + kActiveSchemeCopiedCommandContextOffset;
  output.copied_context_generation = native_context.generation;

  std::uint32_t copied_actor = 0;
  std::uint32_t copied_target = 0;
  if (!Read(state, address, 0, output.primary_vtable) ||
      !Read(state, address, 0x18, output.secondary_vtable) ||
      !Read(state, output.copied_context_address,
            kActiveSchemeContextActorOffset, copied_actor) ||
      !Read(state, output.copied_context_address,
            kActiveSchemeContextRecipientOffset, copied_target) ||
      copied_actor != native_context.actor_full_id ||
      copied_target != native_context.target_full_id) {
    return false;
  }
  output.identity_round_trip = true;
  output.actor_full_id = copied_actor;
  output.target_full_id = copied_target;
  output.interaction_stable_key_hash =
      native_context.interaction_stable_key_hash;
  return true;
}

bool SubmitThunk(void *context, const RouteLease &route,
                 const CommandLease &command,
                 std::uint32_t channel_flags) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  if (!state.native_command_active || state.submit_attempted ||
      command.native_address !=
          reinterpret_cast<std::uintptr_t>(state.command_storage.data()) ||
      route.proof_epoch != command.proof_epoch ||
      channel_flags !=
          kActiveSchemeSemanticActionV1PrivateNativeCommandChannel) {
    return false;
  }
  state.submit_attempted = true;
  bool accepted = false;
  return state.operations.submit(
             state.operation_context, route.submitter_address,
             route.command_manager_address,
             reinterpret_cast<void *>(command.native_address), channel_flags,
             accepted) &&
         accepted;
}

void ReleaseCommandThunk(void *context,
                         const CommandLease &native_command) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  if (!state.native_command_active ||
      native_command.native_address !=
          reinterpret_cast<std::uintptr_t>(state.command_storage.data())) {
    state.native_release_failed = true;
    return;
  }
  std::uintptr_t destroy = 0;
  if (CheckedAddress(
          state.module_base,
          kActiveSchemeSemanticActionV1PrivateDestroyContextRva, destroy)) {
    if (!state.operations.destroy_context(
            state.operation_context, destroy,
            reinterpret_cast<void *>(native_command.native_address +
                                     kActiveSchemeCopiedCommandContextOffset))) {
      state.native_release_failed = true;
    }
  } else {
    state.native_release_failed = true;
  }
  state.native_command_active = false;
  state.command_storage.fill(std::byte{});
}

void ReleaseContextThunk(void *context,
                         const ContextLease &native_context) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  if (!state.native_context_active ||
      native_context.native_address !=
          reinterpret_cast<std::uintptr_t>(state.context_storage.data())) {
    state.native_release_failed = true;
    return;
  }
  std::uintptr_t destroy = 0;
  if (CheckedAddress(
          state.module_base,
          kActiveSchemeSemanticActionV1PrivateDestroyContextRva, destroy)) {
    if (!state.operations.destroy_context(
            state.operation_context, destroy,
            reinterpret_cast<void *>(native_context.native_address))) {
      state.native_release_failed = true;
    }
  } else {
    state.native_release_failed = true;
  }
  state.native_context_active = false;
  state.context_storage.fill(std::byte{});
}

bool CaptureDefinitionFrameThunk(
    void *context,
    ActiveSchemeInteractionDefinitionResolverV1PrivateFrame &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  output = {};
  Frame frame{};
  if (!CurrentFrame(state, frame)) return false;
  output = {true, true, frame.capture_epoch, frame.date_raw};
  return true;
}

bool InvokeGetterThunk(void *context, std::uintptr_t address,
                       std::uintptr_t &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  return state.operation_active && state.operations.invoke_database_getter(
                                       state.operation_context, address, output);
}

bool InvokeHashThunk(void *context, std::uintptr_t address,
                     std::uintptr_t database, std::string_view key,
                     std::int32_t &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  return state.operation_active &&
         state.operations.invoke_stable_key_hash(
             state.operation_context, address, database, key, output);
}

bool InvokeLookupThunk(void *context, std::uintptr_t address,
                       std::uintptr_t database, std::int32_t hash,
                       std::uintptr_t &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  return state.operation_active && state.operations.invoke_loaded_lookup(
                                       state.operation_context, address,
                                       database, hash, output);
}

bool NativePreconditionThunk(
    void *context,
    ActiveSchemeSemanticActionV1PrivatePrecondition &output) noexcept {
  auto &state = *static_cast<BinderState *>(context);
  output = {};
  if (!state.attached || !state.operation_active || !state.request_armed) {
    return false;
  }
  std::string_view scheme_type;
  if (!ValidRequest(state.armed_request, scheme_type)) return false;
  const auto &request = state.armed_request;
  if (request.actor_character_id >
          static_cast<std::int64_t>(
              (std::numeric_limits<std::uint32_t>::max)()) ||
      request.target_id >
          static_cast<std::int64_t>(
              (std::numeric_limits<std::uint32_t>::max)())) {
    return false;
  }
  const auto actor_id = static_cast<std::uint32_t>(request.actor_character_id);
  const auto target_id = static_cast<std::uint32_t>(request.target_id);
  Frame before{};
  Frame after{};
  if (!CurrentFrame(state, before) ||
      before.played_character_id != request.actor_character_id) {
    return false;
  }
  const auto &operations = state.glue.command_state.operations;
  void *const operation_context = state.glue.command_state.operation_context;
  CharacterLease actor{};
  CharacterLease target{};
  DefinitionLease interaction{};
  if (!operations.resolve_character(operation_context, actor_id, actor) ||
      !operations.resolve_character(operation_context, target_id, target) ||
      !operations.resolve_interaction(operation_context,
                                      request.interaction_key, interaction) ||
      actor.proof_epoch != before.capture_epoch ||
      target.proof_epoch != before.capture_epoch ||
      interaction.proof_epoch != before.capture_epoch) {
    return false;
  }
  ActiveSchemeSemanticActionV1PrivateCommand command{
      request.request_id, request.interaction_key, std::string(scheme_type),
      request.actor_character_id, request.target_kind, request.target_id,
      request.selected_starter_package};
  ContextLease native_context{};
  if (!operations.construct_context(operation_context, command, actor, target,
                                    interaction, native_context)) {
    if (native_context.native_address != 0) {
      operations.release_context(operation_context, native_context);
    }
    return false;
  }
  ValidationProof proof{};
  const bool evaluated = operations.validate_context(
      operation_context, native_context, proof);
  operations.release_context(operation_context, native_context);
  if (state.native_release_failed || !evaluated || !proof.evaluated ||
      proof.proof_epoch != before.capture_epoch ||
      !CurrentFrame(state, after) || !SameFrame(before, after)) {
    return false;
  }

  output.available = true;
  output.paused = true;
  output.capture_epoch = before.capture_epoch;
  output.date_raw = before.date_raw;
  output.actor_character_id = request.actor_character_id;
  output.target_kind = request.target_kind;
  output.target_id = request.target_id;
  output.interaction_key = request.interaction_key;
  output.scheme_type_key.assign(scheme_type);
  output.shown_evaluated = true;
  output.shown = proof.valid;
  output.validity_evaluated = true;
  output.valid = proof.valid;
  output.can_start_scheme_evaluated = true;
  output.can_start_scheme = proof.valid;
  if (!proof.valid) {
    output.native_reason_key = "native_complete_validator_rejected";
  }
  const bool murder = scheme_type == "murder";
  output.starter_options_evaluated = true;
  output.starter_options_exclusive = murder;
  output.starter_option_count = murder ? 4U : 0U;
  output.selected_starter_package = request.selected_starter_package;
  output.success_chance.status =
      ActiveSchemeSemanticActionV1PrivatePreviewStatus::explicitly_unavailable;
  output.maximum_success_chance.status =
      ActiveSchemeSemanticActionV1PrivatePreviewStatus::explicitly_unavailable;
  output.secrecy.status =
      ActiveSchemeSemanticActionV1PrivatePreviewStatus::explicitly_unavailable;
  return true;
}

ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment
CommandBinding(BinderState &state) noexcept {
  ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment binding{};
  binding.binding_enabled = true;
  binding.exact_build_admitted = true;
  binding.admitted_executable_sha256 =
      kActiveSchemeSemanticActionV1PrivateExecutableSha256;
  binding.admitted_game_version =
      kActiveSchemeSemanticActionV1PrivateNativeCommandGameVersion;
  binding.offline_fixture = state.offline_fixture;
  binding.module_base = state.module_base;
  binding.operation_context = &state;
  binding.operations = {&ReadMemoryThunk,
                        &ResolveCharacterThunk,
                        nullptr,
                        &ResolveRouteThunk,
                        &ConstructContextThunk,
                        &ValidateContextThunk,
                        &ConstructCommandThunk,
                        &SubmitThunk,
                        &ReleaseContextThunk,
                        &ReleaseCommandThunk};
  binding.proof_gate.evidence_revision =
      kActiveSchemeSemanticActionV1PrivateNativeCommandEvidenceRevision;
  binding.proof_gate.full_character_identity_generation_proven = true;
  binding.proof_gate.starter_package_encoding_proven = true;
  binding.proof_gate.command_copy_lifetime_proven = true;
  return binding;
}

ActiveSchemeInteractionDefinitionResolverV1PrivateEnvironment
DefinitionBinding(BinderState &state) noexcept {
  return {true,
          true,
          kActiveSchemeInteractionDefinitionResolverV1PrivateExecutableSha256,
          kActiveSchemeInteractionDefinitionResolverV1PrivateGameVersion,
          kActiveSchemeInteractionDefinitionResolverV1PrivateEvidenceRevision,
          state.module_base,
          &state,
          &CaptureDefinitionFrameThunk,
          &InvokeGetterThunk,
          &InvokeHashThunk,
          &InvokeLookupThunk};
}

} // namespace

bool BindActiveSchemePreconditionCommandBindersV1Private(
    const ActiveSchemePreconditionCommandBindersV1PrivateEnvironment
        &environment,
    BinderState &state,
    ActiveSchemePreconditionCommandBindersV1PrivateReadiness
        &readiness) noexcept {
  readiness = {};
  readiness.failure = BinderFailure::binding_contract;
  if (!environment.binding_enabled || !environment.exact_build_admitted ||
      environment.module_base == 0 || state.attached) {
    return false;
  }
  if (environment.admitted_executable_sha256 !=
          kActiveSchemeSemanticActionV1PrivateExecutableSha256 ||
      environment.admitted_game_version !=
          kActiveSchemeSemanticActionV1PrivateNativeCommandGameVersion ||
      environment.source_access.admitted_executable_sha256 !=
          environment.admitted_executable_sha256) {
    readiness.failure = BinderFailure::exact_build_mismatch;
    return false;
  }
  readiness.exact_build_bound = true;
  auto operations = environment.operations;
  if (environment.offline_fixture) {
    if (!OperationsComplete(operations)) {
      readiness.failure = BinderFailure::primitive_callbacks_unavailable;
      return false;
    }
  } else {
    if (!OperationsEmpty(operations) || environment.operation_context != nullptr) {
      readiness.failure = BinderFailure::binding_contract;
      return false;
    }
    operations = DirectOperations();
  }

  state = {};
  state.offline_fixture = environment.offline_fixture;
  state.module_base = environment.module_base;
  state.operation_context = environment.operation_context;
  state.operations = operations;
  state.source_access = environment.source_access;
  // Exact verification needs the state callbacks before attached is published.
  state.attached = true;
  if (!VerifyExactImage(state)) {
    state = {};
    readiness.failure = BinderFailure::exact_image_mismatch;
    return false;
  }
  readiness.stable_identity_route_bound = true;
  readiness.native_context_validator_bound = true;
  readiness.native_single_submit_release_bound = true;
  readiness.native_precondition_bound = true;

  ActiveSchemePausedLiveNativeGlueV1PrivateEnvironment glue_environment{};
  glue_environment.binding_enabled = true;
  glue_environment.source_access = state.source_access;
  glue_environment.precondition_context = &state;
  glue_environment.capture_precondition = &NativePreconditionThunk;
  glue_environment.command_binding = CommandBinding(state);
  glue_environment.definition_binding = DefinitionBinding(state);
  ActiveSchemePausedLiveNativeGlueV1PrivateReadiness glue_readiness{};
  if (!BindActiveSchemePausedLiveNativeGlueV1Private(
          glue_environment, state.glue, glue_readiness)) {
    state = {};
    readiness.failure = BinderFailure::glue_binding_rejected;
    return false;
  }
  readiness.callback_core_ready = glue_readiness.candidate_core_ready;
  readiness.failure = BinderFailure::none;
  state.readiness = readiness;
  return true;
}

bool CaptureActiveSchemePreconditionCommandSnapshotV1Private(
    BinderState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    ActiveSchemeStateV1PrivateObservation &output,
    BinderFailure &failure) noexcept {
  output = {};
  if (!Begin(state, execution, failure)) return false;
  ActiveSchemePausedLiveNativeGlueV1PrivateFailure glue_failure{};
  const bool ok = CaptureActiveSchemePausedLiveSnapshotV1Private(
      state.glue, execution, output, glue_failure);
  End(state);
  failure = ok ? BinderFailure::none : BinderFailure::glue_red;
  return ok;
}

bool ResolveActiveSchemePreconditionCommandDefinitionV1Private(
    BinderState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    std::string_view interaction_key, DefinitionLease &output,
    BinderFailure &failure) noexcept {
  output = {};
  if (!Begin(state, execution, failure)) return false;
  ActiveSchemePausedLiveNativeGlueV1PrivateFailure glue_failure{};
  const bool ok = ResolveActiveSchemePausedLiveDefinitionV1Private(
      state.glue, execution, interaction_key, output, glue_failure);
  End(state);
  failure = ok ? BinderFailure::none : BinderFailure::glue_red;
  return ok;
}

bool CaptureActiveSchemePreconditionCommandPreconditionV1Private(
    BinderState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    const ActiveSchemeSemanticActionV1PrivateRequest &request,
    ActiveSchemeSemanticActionV1PrivatePrecondition &output,
    BinderFailure &failure) noexcept {
  output = {};
  std::string_view scheme_type;
  if (!ValidRequest(request, scheme_type)) {
    failure = BinderFailure::request_contract;
    return false;
  }
  if (!Begin(state, execution, failure)) return false;
  state.armed_request = request;
  state.request_armed = true;
  ActiveSchemePausedLiveNativeGlueV1PrivateFailure glue_failure{};
  const bool ok = CaptureActiveSchemePausedLivePreconditionV1Private(
      state.glue, execution, output, glue_failure);
  state.request_armed = false;
  state.armed_request = {};
  End(state);
  failure = ok ? BinderFailure::none : BinderFailure::native_precondition_red;
  return ok;
}

ActiveSchemeSemanticActionV1PrivateAckStatus
ExecuteActiveSchemePreconditionCommandV1Private(
    BinderState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    const ActiveSchemeSemanticActionV1PrivateRequest &request,
    ActiveSchemeSemanticActionV1PrivateAck &ack,
    BinderFailure &failure) noexcept {
  ack = {};
  std::string_view scheme_type;
  if (!ValidRequest(request, scheme_type)) {
    failure = BinderFailure::request_contract;
    return ack.status;
  }
  if (!Begin(state, execution, failure)) return ack.status;
  state.armed_request = request;
  state.request_armed = true;
  state.submit_attempted = false;
  ActiveSchemePausedLiveNativeGlueV1PrivateFailure glue_failure{};
  const auto status = ExecuteActiveSchemePausedLiveNativeGlueV1Private(
      state.glue, execution, request, ack, glue_failure);
  state.request_armed = false;
  state.armed_request = {};
  End(state);
  const bool ok =
      status == ActiveSchemeSemanticActionV1PrivateAckStatus::
                    submitted_verification_pending &&
      ack.verification_pending && ack.submit_call_count == 1 &&
      !state.native_release_failed;
  failure = ok ? BinderFailure::none : BinderFailure::glue_red;
  return status;
}

ActiveSchemeSemanticActionV1PrivateReceiptStatus
VerifyActiveSchemePreconditionCommandReceiptV1Private(
    BinderState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    const ActiveSchemeSemanticActionV1PrivateAck &ack,
    ActiveSchemeSemanticActionV1PrivateReceipt &receipt,
    BinderFailure &failure) noexcept {
  receipt = {};
  if (!Begin(state, execution, failure)) return receipt.status;
  ActiveSchemePausedLiveNativeGlueV1PrivateFailure glue_failure{};
  const auto status = VerifyActiveSchemePausedLiveNativeGlueReceiptV1Private(
      state.glue, execution, ack, receipt, glue_failure);
  End(state);
  const bool ok =
      status == ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied &&
      receipt.postcondition_verified;
  failure = ok ? BinderFailure::none : BinderFailure::glue_red;
  return status;
}

std::string_view ActiveSchemePreconditionCommandBindersV1PrivateFailureName(
    BinderFailure failure) noexcept {
  switch (failure) {
  case BinderFailure::none: return "none";
  case BinderFailure::binding_contract: return "binding_contract";
  case BinderFailure::exact_build_mismatch: return "exact_build_mismatch";
  case BinderFailure::primitive_callbacks_unavailable:
    return "primitive_callbacks_unavailable";
  case BinderFailure::exact_image_mismatch: return "exact_image_mismatch";
  case BinderFailure::glue_binding_rejected: return "glue_binding_rejected";
  case BinderFailure::not_bound: return "not_bound";
  case BinderFailure::reentrant_execution: return "reentrant_execution";
  case BinderFailure::not_application_main_thread:
    return "not_application_main_thread";
  case BinderFailure::request_contract: return "request_contract";
  case BinderFailure::native_precondition_red:
    return "native_precondition_red";
  case BinderFailure::glue_red: return "glue_red";
  }
  return "unknown";
}

} // namespace xar::bridge
