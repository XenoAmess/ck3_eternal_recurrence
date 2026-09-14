#include "xar_bridge/major_decision_found_kingdom_native_submit_v1.hpp"

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

namespace xar::bridge {
namespace {

using State = MajorDecisionFoundKingdomNativeSubmitStateV1;
using Operations = MajorDecisionFoundKingdomNativeSubmitOperationsV1;
using Binding = MajorDecisionFoundKingdomActionBindingV1;

constexpr std::size_t kComponentSlotsOffset = 0x20;
constexpr std::size_t kComponentCapacityOffset = 0x2C;
constexpr std::size_t kComponentSlotStride = 0x10;
constexpr std::size_t kComponentSlotObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;
constexpr std::uint64_t kFnvOffset = 14695981039346656037ULL;
constexpr std::uint64_t kFnvPrime = 1099511628211ULL;
constexpr char kExecuteDecisionCommandRttiName[] =
    ".?AVCExecuteDecisionCommand@@";

bool DirectReadMemory(void *, const void *address, void *output,
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

template <typename T>
bool DirectRead(const void *address, T &output) noexcept {
  return DirectReadMemory(nullptr, address, &output, sizeof(output));
}

std::uintptr_t DirectResolvePlayer(void *, std::uintptr_t module_base,
                                   std::int32_t character_id) noexcept {
  if (module_base == 0 || character_id <= 0) return 0;
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!DirectRead(reinterpret_cast<const void *>(
                      module_base +
                      kMajorDecisionFoundKingdomCharacterStorageSlotRvaV1),
                  storage) ||
      !DirectRead(reinterpret_cast<const void *>(
                      module_base +
                      kMajorDecisionFoundKingdomCharacterFallbackSlotRvaV1),
                  fallback) ||
      storage == nullptr) {
    return 0;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!DirectRead(static_cast<std::byte *>(storage) + kComponentSlotsOffset,
                  slots) ||
      !DirectRead(static_cast<std::byte *>(storage) +
                      kComponentCapacityOffset,
                  capacity) ||
      slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentSlots) {
    return 0;
  }
  const auto index = static_cast<std::uint32_t>(character_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return 0;
  void *player = nullptr;
  std::int32_t observed_id = 0;
  if (!DirectRead(static_cast<std::byte *>(slots) +
                      static_cast<std::size_t>(index) * kComponentSlotStride +
                      kComponentSlotObjectOffset,
                  player) ||
      player == nullptr || player == fallback ||
      !DirectRead(static_cast<std::byte *>(player) + kCharacterIdentityOffset,
                  observed_id) ||
      observed_id != character_id) {
    return 0;
  }
  return reinterpret_cast<std::uintptr_t>(player);
}

using NameHash = std::uint32_t (*)(void *, const char *, std::uint32_t);
using LookupDefinition = const void *(*)(void *, std::uint32_t);
using ConstructCommand = void *(*)(void *, std::int32_t, void *, void **);
using ValidateCommand = bool (*)(void *, void *);
using CloneCommand = void **(*)(void *, void **);
using DestroyCommand = void *(*)(void *, std::uint32_t);
using QueueCommand = bool (*)(void *, void **, std::uint32_t);

bool DirectHashName(void *, std::uintptr_t module_base, std::string_view name,
                    std::uint32_t &output) noexcept {
  output = 0;
  if (module_base == 0 || name.empty() ||
      name.size() > (std::numeric_limits<std::uint32_t>::max)()) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    output = reinterpret_cast<NameHash>(
        module_base + kMajorDecisionFoundKingdomNameHashRvaV1)(
        nullptr, name.data(), static_cast<std::uint32_t>(name.size()));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = 0;
    return false;
  }
#endif
}

std::uintptr_t DirectLookupDefinition(void *, std::uintptr_t module_base,
                                      std::uintptr_t database,
                                      std::uint32_t name_hash) noexcept {
  if (module_base == 0 || database == 0) return 0;
#if defined(_MSC_VER)
  __try {
#endif
    return reinterpret_cast<std::uintptr_t>(
        reinterpret_cast<LookupDefinition>(
            module_base + kMajorDecisionFoundKingdomDatabaseLookupRvaV1)(
            reinterpret_cast<void *>(database), name_hash));
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return 0;
  }
#endif
}

bool DirectConstruct(void *, std::uintptr_t module_base, void *command,
                     std::int32_t character_id, std::uintptr_t definition,
                     void **owned_decision_context) noexcept {
  if (module_base == 0 || command == nullptr || character_id <= 0 ||
      definition == 0 || owned_decision_context == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    return reinterpret_cast<ConstructCommand>(
               module_base +
               kMajorDecisionFoundKingdomExecuteCommandConstructorRvaV1)(
               command, character_id, reinterpret_cast<void *>(definition),
               owned_decision_context) == command;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool DirectValidate(void *, std::uintptr_t module_base,
                    void *command) noexcept {
  if (module_base == 0 || command == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return reinterpret_cast<ValidateCommand>(
        module_base +
        kMajorDecisionFoundKingdomExecuteCommandValidatorRvaV1)(command,
                                                                 nullptr);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool DirectClone(void *, std::uintptr_t module_base, void *command,
                 void **owned_clone) noexcept {
  if (module_base == 0 || command == nullptr || owned_clone == nullptr ||
      *owned_clone != nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    return reinterpret_cast<CloneCommand>(
               module_base +
               kMajorDecisionFoundKingdomExecuteCommandCloneRvaV1)(
               command, owned_clone) == owned_clone &&
           *owned_clone != nullptr;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool DirectDestroy(void *, std::uintptr_t module_base, void *command,
                   std::uint32_t flags) noexcept {
  if (module_base == 0 || command == nullptr || (flags != 0 && flags != 1)) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    return reinterpret_cast<DestroyCommand>(
               module_base +
               kMajorDecisionFoundKingdomExecuteCommandDestructorRvaV1)(
               command, flags) == command;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool DirectQueue(void *, std::uintptr_t module_base, void **owned_command,
                 std::uint32_t flags) noexcept {
  if (module_base == 0 || owned_command == nullptr ||
      *owned_command == nullptr ||
      flags != kMajorDecisionFoundKingdomCommandQueueFlagsV1) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    return reinterpret_cast<QueueCommand>(
        module_base + kMajorDecisionFoundKingdomCommandQueueReceiverRvaV1)(
        reinterpret_cast<void *>(
            module_base + kMajorDecisionFoundKingdomCommandQueueContextRvaV1),
        owned_command, flags);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

Operations DefaultOperations() noexcept {
  return {&DirectReadMemory,      &DirectResolvePlayer, &DirectHashName,
          &DirectLookupDefinition, &DirectConstruct,      &DirectValidate,
          &DirectClone,          &DirectDestroy,       &DirectQueue};
}

bool AnyOverride(const Operations &operations) noexcept {
  return operations.read_memory != nullptr ||
         operations.resolve_player != nullptr || operations.hash_name != nullptr ||
         operations.lookup_definition != nullptr ||
         operations.construct != nullptr || operations.validate != nullptr ||
         operations.clone != nullptr || operations.destroy != nullptr ||
         operations.queue != nullptr;
}

bool Complete(const Operations &operations) noexcept {
  return operations.read_memory != nullptr &&
         operations.resolve_player != nullptr && operations.hash_name != nullptr &&
         operations.lookup_definition != nullptr &&
         operations.construct != nullptr && operations.validate != nullptr &&
         operations.clone != nullptr && operations.destroy != nullptr &&
         operations.queue != nullptr;
}

bool ReadBytes(const State &state, std::uintptr_t address, void *output,
               std::size_t size) noexcept {
  return state.operations.read_memory(state.operation_context,
                                      reinterpret_cast<const void *>(address),
                                      output, size);
}

template <typename T>
bool Read(const State &state, std::uintptr_t address, T &output) noexcept {
  return ReadBytes(state, address, &output, sizeof(output));
}

bool ExpectedVtable(const State &state, std::uintptr_t object,
                    std::uintptr_t expected_rva) noexcept {
  std::uintptr_t vtable = 0;
  return object != 0 && Read(state, object, vtable) &&
         vtable == state.module_base + expected_rva;
}

bool VerifyExactImage(const State &state) noexcept {
  // The submit path reuses DECISION4's exact player/database/name lookup, so
  // inherit every read-side signature and virtual identity gate as well as
  // checking the command-specific surface below.
  for (const auto &signature : kMajorDecisionFoundKingdomNativeSignaturesV1) {
    std::array<std::uint8_t, 16> observed{};
    if (signature.size == 0 || signature.size > observed.size() ||
        !ReadBytes(state, state.module_base + signature.rva, observed.data(),
                   signature.size) ||
        !std::equal(observed.begin(), observed.begin() + signature.size,
                    signature.bytes.begin())) {
      return false;
    }
  }
  for (const auto &slot : kMajorDecisionFoundKingdomNativeSlotsV1) {
    std::uintptr_t observed = 0;
    if (!Read(state, state.module_base + slot.slot_rva, observed) ||
        observed != state.module_base + slot.function_rva) {
      return false;
    }
  }
  for (const auto &signature :
       kMajorDecisionFoundKingdomNativeSubmitSignaturesV1) {
    std::array<std::uint8_t, 16> observed{};
    if (signature.size == 0 || signature.size > observed.size() ||
        !ReadBytes(state, state.module_base + signature.rva, observed.data(),
                   signature.size) ||
        !std::equal(observed.begin(), observed.begin() + signature.size,
                    signature.bytes.begin())) {
      return false;
    }
  }
  for (const auto &slot : kMajorDecisionFoundKingdomNativeSubmitSlotsV1) {
    std::uintptr_t observed = 0;
    if (!Read(state, state.module_base + slot.slot_rva, observed) ||
        observed != state.module_base + slot.function_rva) {
      return false;
    }
  }
  std::array<char, sizeof(kExecuteDecisionCommandRttiName)> observed_name{};
  return ReadBytes(
             state,
             state.module_base +
                 kMajorDecisionFoundKingdomExecuteCommandTypeDescriptorRvaV1 +
                 0x10,
             observed_name.data(), observed_name.size()) &&
         std::equal(observed_name.begin(), observed_name.end(),
                    std::begin(kExecuteDecisionCommandRttiName));
}

std::uint64_t HashValue(std::uint64_t hash, std::uint64_t value) noexcept {
  for (int byte = 0; byte != 8; ++byte) {
    hash ^= value & 0xFFU;
    hash *= kFnvPrime;
    value >>= 8;
  }
  return hash;
}

bool ResolveBoundObjects(const State &state, const Binding &binding,
                         std::uintptr_t &player,
                         std::uintptr_t &definition) noexcept {
  player = state.operations.resolve_player(
      state.operation_context, state.module_base, binding.played_character_id);
  std::int32_t observed_character_id = 0;
  if (player == 0 ||
      !Read(state, player + kCharacterIdentityOffset, observed_character_id) ||
      observed_character_id != binding.played_character_id) {
    return false;
  }

  std::uintptr_t database = 0;
  if (!Read(state,
            state.module_base +
                kMajorDecisionFoundKingdomDecisionDatabaseSlotRvaV1,
            database) ||
      !ExpectedVtable(
          state, database,
          kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1) ||
      database != binding.decision_database_identity) {
    return false;
  }
  auto database_generation = HashValue(kFnvOffset, database);
  database_generation = HashValue(
      database_generation,
      kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1);
  if (database_generation == 0) database_generation = 1;
  if (database_generation != binding.decision_database_generation) {
    return false;
  }

  std::uint32_t name_hash = 0;
  if (!state.operations.hash_name(
          state.operation_context, state.module_base,
          kMajorDecisionFoundKingdomDecisionIdV1, name_hash)) {
    return false;
  }
  definition = state.operations.lookup_definition(
      state.operation_context, state.module_base, database, name_hash);
  if (!ExpectedVtable(
          state, definition,
          kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1) ||
      definition != binding.decision_definition_identity) {
    return false;
  }
  auto definition_generation = HashValue(kFnvOffset, database_generation);
  definition_generation = HashValue(definition_generation, definition);
  definition_generation = HashValue(
      definition_generation,
      kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1);
  if (definition_generation == 0) definition_generation = 1;
  return definition_generation == binding.decision_definition_generation;
}

bool VerifyCommandLayout(const State &state, std::uintptr_t command,
                         const Binding &binding,
                         std::uintptr_t definition) noexcept {
  std::uintptr_t primary_vtable = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t character_id = 0;
  std::uintptr_t observed_definition = 0;
  std::uintptr_t owned_context = 1;
  return command != 0 && Read(state, command, primary_vtable) &&
         primary_vtable ==
             state.module_base +
                 kMajorDecisionFoundKingdomExecuteCommandPrimaryVtableRvaV1 &&
         Read(state,
              command +
                  kMajorDecisionFoundKingdomExecuteCommandSecondaryOffsetV1,
              secondary_vtable) &&
         secondary_vtable ==
             state.module_base +
                 kMajorDecisionFoundKingdomExecuteCommandSecondaryVtableRvaV1 &&
         Read(state,
              command +
                  kMajorDecisionFoundKingdomExecuteCommandCharacterIdOffsetV1,
              character_id) &&
         character_id == binding.played_character_id &&
         Read(state,
              command +
                  kMajorDecisionFoundKingdomExecuteCommandDefinitionOffsetV1,
              observed_definition) &&
         observed_definition == definition &&
         Read(state,
              command +
                  kMajorDecisionFoundKingdomExecuteCommandContextOffsetV1,
              owned_context) &&
         owned_context == 0;
}

bool ForwardCapture(
    void *context,
    MajorDecisionFoundKingdomActionPreconditionV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  return state.attached && state.upstream_capture_precondition != nullptr &&
         state.upstream_capture_precondition(state.upstream_context, output);
}

bool Submit(void *context, const Binding &binding,
            std::string_view decision_id) noexcept {
  auto &state = *static_cast<State *>(context);
  if (!state.attached || decision_id != kMajorDecisionFoundKingdomDecisionIdV1 ||
      binding.played_character_id <= 0) {
    return false;
  }

  std::uintptr_t player = 0;
  std::uintptr_t definition = 0;
  if (!ResolveBoundObjects(state, binding, player, definition)) return false;
  (void)player;

  alignas(16) std::array<std::byte,
                         kMajorDecisionFoundKingdomExecuteCommandSizeV1>
      command{};
  void *owned_decision_context = nullptr;
  if (!state.operations.construct(
          state.operation_context, state.module_base, command.data(),
          binding.played_character_id, definition, &owned_decision_context) ||
      owned_decision_context != nullptr) {
    return false;
  }
  if (!VerifyCommandLayout(
          state, reinterpret_cast<std::uintptr_t>(command.data()), binding,
          definition)) {
    state.operations.destroy(state.operation_context, state.module_base,
                             command.data(), 0);
    return false;
  }
  if (!state.operations.validate(state.operation_context, state.module_base,
                                 command.data())) {
    state.operations.destroy(state.operation_context, state.module_base,
                             command.data(), 0);
    return false;
  }

  void *owned_clone = nullptr;
  if (!state.operations.clone(state.operation_context, state.module_base,
                              command.data(), &owned_clone) ||
      owned_clone == nullptr) {
    if (owned_clone != nullptr) {
      state.operations.destroy(state.operation_context, state.module_base,
                               owned_clone, 1);
    }
    state.operations.destroy(state.operation_context, state.module_base,
                             command.data(), 0);
    return false;
  }
  if (!VerifyCommandLayout(state,
                           reinterpret_cast<std::uintptr_t>(owned_clone),
                           binding, definition)) {
    state.operations.destroy(state.operation_context, state.module_base,
                             owned_clone, 1);
    state.operations.destroy(state.operation_context, state.module_base,
                             command.data(), 0);
    return false;
  }

  // The stack command is no longer needed once the heap clone is complete.
  // Destroy it before queue ownership crosses the receiver boundary.
  if (!state.operations.destroy(state.operation_context, state.module_base,
                                command.data(), 0)) {
    state.operations.destroy(state.operation_context, state.module_base,
                             owned_clone, 1);
    return false;
  }

  const bool accepted = state.operations.queue(
      state.operation_context, state.module_base, &owned_clone,
      kMajorDecisionFoundKingdomCommandQueueFlagsV1);
  const bool consumed = owned_clone == nullptr;
  if (!consumed) {
    state.operations.destroy(state.operation_context, state.module_base,
                             owned_clone, 1);
    owned_clone = nullptr;
  }
  return accepted && consumed;
}

} // namespace

bool BindMajorDecisionFoundKingdomNativeSubmitV1(
    const MajorDecisionFoundKingdomNativeSubmitEnvironmentV1 &environment,
    MajorDecisionFoundKingdomNativeSubmitStateV1 &state,
    MajorDecisionFoundKingdomActionEnvironmentV1 &action_environment,
    MajorDecisionFoundKingdomActionAccessV1 &action_access) noexcept {
  if (!environment.binding_enabled || !environment.exact_build_admitted ||
      environment.admitted_game_version !=
          kMajorDecisionFoundKingdomNativeSubmitGameVersionV1 ||
      environment.admitted_executable_sha256 !=
          kMajorDecisionFoundKingdomExecutableSha256V1 ||
      action_access.capture_precondition == nullptr ||
      action_access.submit != nullptr || action_access.context == &state ||
      state.attached) {
    return false;
  }

  Operations operations{};
  if (environment.offline_fixture) {
    if (environment.module_base != 0) return false;
    operations = environment.operations;
  } else {
    if (environment.module_base == 0 || AnyOverride(environment.operations) ||
        environment.operation_context != nullptr) {
      return false;
    }
    operations = DefaultOperations();
  }
  if (!Complete(operations)) return false;

  State candidate{};
  candidate.module_base = environment.module_base;
  candidate.operation_context = environment.operation_context;
  candidate.operations = operations;
  candidate.upstream_context = action_access.context;
  candidate.upstream_capture_precondition =
      action_access.capture_precondition;
  candidate.offline_fixture = environment.offline_fixture;
  if (!VerifyExactImage(candidate)) return false;
  candidate.attached = true;
  state = candidate;

  action_environment.exact_build_admitted = true;
  action_environment.admitted_game_version =
      kMajorDecisionFoundKingdomNativeSubmitGameVersionV1;
  action_environment.admitted_executable_sha256 =
      kMajorDecisionFoundKingdomExecutableSha256V1;
  action_environment.module_base = environment.module_base;
  action_environment.submit_abi_certified = !environment.offline_fixture;
  action_environment.offline_fixture_submit = environment.offline_fixture;
  action_access.context = &state;
  action_access.capture_precondition = &ForwardCapture;
  action_access.submit = &Submit;
  return true;
}

} // namespace xar::bridge
