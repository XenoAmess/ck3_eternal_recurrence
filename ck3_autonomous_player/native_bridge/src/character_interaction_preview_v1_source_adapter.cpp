#include "xar_bridge/character_interaction_preview_v1_source_adapter.hpp"

#include <array>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#define NOMINMAX
#include <windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kContextDefinitionOffset = 0x00;
constexpr std::size_t kContextEventTargetScopeOffset = 0x08;
constexpr std::size_t kContextRecipientIdOffset = 0x2DC;
constexpr std::size_t kContextIntermediaryIdOffset = 0x2E8;
constexpr std::size_t kDefinitionCostBlockOffset = 0x38;
constexpr std::size_t kDefinitionAutoAcceptTriggerOffset = 0x2580;
constexpr std::size_t kDefinitionAutoAcceptScalarOffset = 0x2A48;
constexpr std::int32_t kInvalidCharacterId = -1;

using GetDatabase = void *(*)();
using HashStableKey = std::int32_t (*)(void *, const char *, std::uint32_t);
using LookupDefinition = void *(*)(void *, std::int32_t);
using ConstructContext = void *(*)(void *, void *, std::int32_t,
                                   std::int32_t, void *, bool);
using RefreshContext = void (*)(void *, bool);
using ContextStep = void (*)(void *);
using CanSend = bool (*)(void *, void *);
using EvaluateCosts = void (*)(const void *, const void *, std::int64_t *);
using EvaluateTrigger = bool (*)(void *, const void *);
using ReadRawAcceptance = std::int64_t *(*)(void *, std::int64_t *);
using ReadOuterAcceptance = std::uint8_t (*)(void *, std::uint8_t,
                                             std::uint8_t, void *, void *);
using IsHumanPlayer = bool (*)(std::int32_t);

bool AddAddress(std::uintptr_t base, std::uintptr_t rva,
                std::uintptr_t &output) noexcept {
  if (base == 0 || base > std::numeric_limits<std::uintptr_t>::max() - rva) {
    return false;
  }
  output = base + rva;
  return true;
}

bool Matches(std::uintptr_t function, std::uintptr_t module,
             std::uintptr_t rva) noexcept {
  std::uintptr_t expected = 0;
  return AddAddress(module, rva, expected) && function == expected;
}

bool DirectRead(const void *address, void *output, std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
#if defined(_MSC_VER) && defined(_WIN32)
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

bool DefaultGetDatabase(void *, std::uintptr_t module, void *&output) noexcept {
  output = nullptr;
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewDatabaseGetterRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = reinterpret_cast<GetDatabase>(function)();
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = reinterpret_cast<GetDatabase>(function)();
#endif
  return output != nullptr;
}

bool DefaultHashStableKey(void *, std::uintptr_t module, void *database,
                          std::string_view key,
                          std::int32_t &output) noexcept {
  if (database == nullptr || key.empty() ||
      key.size() > std::numeric_limits<std::uint32_t>::max()) {
    return false;
  }
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewStableKeyHashRvaV1,
                  function)) {
    return false;
  }
  const char *const data = key.data();
  const auto size = static_cast<std::uint32_t>(key.size());
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = reinterpret_cast<HashStableKey>(function)(database, data, size);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = reinterpret_cast<HashStableKey>(function)(database, data, size);
#endif
  return true;
}

bool DefaultLookupDefinition(void *, std::uintptr_t module, void *database,
                             std::int32_t key_hash, void *&output) noexcept {
  output = nullptr;
  if (database == nullptr) return false;
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewDefinitionLookupRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output =
        reinterpret_cast<LookupDefinition>(function)(database, key_hash);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = reinterpret_cast<LookupDefinition>(function)(database, key_hash);
#endif
  return output != nullptr;
}

bool DefaultConstructContext(void *, std::uintptr_t module,
                             void *context_storage, void *definition,
                             std::int32_t actor_character_id,
                             std::int32_t recipient_character_id,
                             void *&output) noexcept {
  output = nullptr;
  if (context_storage == nullptr || definition == nullptr) return false;
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewConstructContextRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = reinterpret_cast<ConstructContext>(function)(
        context_storage, definition, actor_character_id,
        recipient_character_id, nullptr, true);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = reinterpret_cast<ConstructContext>(function)(
      context_storage, definition, actor_character_id,
      recipient_character_id, nullptr, true);
#endif
  return output == context_storage;
}

bool DefaultRefreshContext(void *, std::uintptr_t module,
                           void *interaction_context, bool refresh) noexcept {
  if (interaction_context == nullptr || !refresh) return false;
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewRefreshContextRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    reinterpret_cast<RefreshContext>(function)(interaction_context, true);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  reinterpret_cast<RefreshContext>(function)(interaction_context, true);
#endif
  return true;
}

bool DefaultFinalizeContext(void *, std::uintptr_t module,
                            void *interaction_context) noexcept {
  if (interaction_context == nullptr) return false;
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewFinalizeContextRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    reinterpret_cast<ContextStep>(function)(interaction_context);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  reinterpret_cast<ContextStep>(function)(interaction_context);
#endif
  return true;
}

bool DefaultCanSend(void *, std::uintptr_t module, void *interaction_context,
                    bool &output) noexcept {
  if (interaction_context == nullptr) return false;
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewCanSendRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = reinterpret_cast<CanSend>(function)(interaction_context, nullptr);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = reinterpret_cast<CanSend>(function)(interaction_context, nullptr);
#endif
  return true;
}

bool DefaultEvaluateCosts(
    void *, std::uintptr_t module, void *interaction_context,
    std::array<std::int64_t, game::kCharacterInteractionPreviewCostCountV1>
        &output) noexcept {
  output.fill(0);
  if (interaction_context == nullptr) return false;
  void *definition = nullptr;
  if (!DirectRead(static_cast<const std::byte *>(interaction_context) +
                      kContextDefinitionOffset,
                  &definition, sizeof(definition)) ||
      definition == nullptr) {
    return false;
  }
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewCostEvaluatorRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    reinterpret_cast<EvaluateCosts>(function)(
        static_cast<const std::byte *>(definition) + kDefinitionCostBlockOffset,
        static_cast<const std::byte *>(interaction_context) +
            kContextEventTargetScopeOffset,
        output.data());
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output.fill(0);
    return false;
  }
#else
  reinterpret_cast<EvaluateCosts>(function)(
      static_cast<const std::byte *>(definition) + kDefinitionCostBlockOffset,
      static_cast<const std::byte *>(interaction_context) +
          kContextEventTargetScopeOffset,
      output.data());
#endif
  return true;
}

bool DefaultEvaluateTrigger(void *, std::uintptr_t module, void *trigger,
                            const void *event_target_scope,
                            bool &output) noexcept {
  if (trigger == nullptr || event_target_scope == nullptr) return false;
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewAutoAcceptEvaluatorRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = reinterpret_cast<EvaluateTrigger>(function)(
        trigger, event_target_scope);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = reinterpret_cast<EvaluateTrigger>(function)(trigger,
                                                        event_target_scope);
#endif
  return true;
}

bool DefaultReadRaw(std::uintptr_t rva, std::uintptr_t module,
                    void *interaction_context, std::int64_t &output) noexcept {
  if (interaction_context == nullptr) return false;
  std::uintptr_t function = 0;
  if (!AddAddress(module, rva, function)) return false;
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    auto *const returned = reinterpret_cast<ReadRawAcceptance>(function)(
        interaction_context, &output);
    return returned == &output;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  auto *const returned = reinterpret_cast<ReadRawAcceptance>(function)(
      interaction_context, &output);
  return returned == &output;
#endif
}

bool DefaultIntermediaryRaw(void *, std::uintptr_t module,
                            void *interaction_context,
                            std::int64_t &output) noexcept {
  return DefaultReadRaw(kCharacterInteractionPreviewIntermediaryRawRvaV1,
                        module, interaction_context, output);
}

bool DefaultRecipientRaw(void *, std::uintptr_t module,
                         void *interaction_context,
                         std::int64_t &output) noexcept {
  return DefaultReadRaw(kCharacterInteractionPreviewRecipientRawRvaV1, module,
                        interaction_context, output);
}

bool DefaultOuterFinal(void *, std::uintptr_t module,
                       void *interaction_context,
                       std::int32_t &status) noexcept {
  if (interaction_context == nullptr) return false;
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewOuterFinalRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    status = static_cast<std::int32_t>(
        reinterpret_cast<ReadOuterAcceptance>(function)(
            interaction_context, 1, 0, nullptr, nullptr));
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  status = static_cast<std::int32_t>(
      reinterpret_cast<ReadOuterAcceptance>(function)(
          interaction_context, 1, 0, nullptr, nullptr));
#endif
  return true;
}

bool DefaultIsHumanPlayer(void *, std::uintptr_t module,
                          std::int32_t character_id, bool &output) noexcept {
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewHumanPlayerPredicateRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = reinterpret_cast<IsHumanPlayer>(function)(character_id);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = reinterpret_cast<IsHumanPlayer>(function)(character_id);
#endif
  return true;
}

bool DefaultDestroyContext(void *, std::uintptr_t module,
                           void *interaction_context) noexcept {
  if (interaction_context == nullptr) return false;
  std::uintptr_t function = 0;
  if (!AddAddress(module, kCharacterInteractionPreviewDestroyContextRvaV1,
                  function)) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    reinterpret_cast<ContextStep>(function)(interaction_context);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  reinterpret_cast<ContextStep>(function)(interaction_context);
#endif
  return true;
}

bool DefaultReadMemory(void *, const void *address, void *output,
                       std::size_t size) noexcept {
  return DirectRead(address, output, size);
}

CharacterInteractionPreviewSourceOperationsV1 DefaultOperations() noexcept {
  return {&DefaultGetDatabase,   &DefaultHashStableKey,
          &DefaultLookupDefinition,
          &DefaultConstructContext,
          &DefaultRefreshContext,
          &DefaultFinalizeContext,
          &DefaultCanSend,
          &DefaultEvaluateCosts,
          &DefaultEvaluateTrigger,
          &DefaultIntermediaryRaw,
          &DefaultRecipientRaw,
          &DefaultOuterFinal,
          &DefaultIsHumanPlayer,
          &DefaultDestroyContext,
          &DefaultReadMemory};
}

bool Complete(
    const CharacterInteractionPreviewSourceOperationsV1 &operations) noexcept {
  return operations.get_database != nullptr &&
         operations.hash_stable_key != nullptr &&
         operations.lookup_definition != nullptr &&
         operations.construct_context != nullptr &&
         operations.refresh_context != nullptr &&
         operations.finalize_context != nullptr &&
         operations.can_send != nullptr &&
         operations.evaluate_costs != nullptr &&
         operations.evaluate_trigger != nullptr &&
         operations.intermediary_raw != nullptr &&
         operations.recipient_raw != nullptr &&
         operations.outer_final != nullptr &&
         operations.is_human_player != nullptr &&
         operations.destroy_context != nullptr &&
         operations.read_memory != nullptr;
}

bool Any(
    const CharacterInteractionPreviewSourceOperationsV1 &operations) noexcept {
  return operations.get_database != nullptr ||
         operations.hash_stable_key != nullptr ||
         operations.lookup_definition != nullptr ||
         operations.construct_context != nullptr ||
         operations.refresh_context != nullptr ||
         operations.finalize_context != nullptr || operations.can_send != nullptr ||
         operations.evaluate_costs != nullptr ||
         operations.evaluate_trigger != nullptr ||
         operations.intermediary_raw != nullptr ||
         operations.recipient_raw != nullptr ||
         operations.outer_final != nullptr ||
         operations.is_human_player != nullptr ||
         operations.destroy_context != nullptr ||
         operations.read_memory != nullptr;
}

CharacterInteractionPreviewSourceStateV1 *State(void *context) noexcept {
  return static_cast<CharacterInteractionPreviewSourceStateV1 *>(context);
}

bool CaptureFrame(void *context,
                  CharacterInteractionPreviewFrameV1 &output) noexcept {
  auto *const state = State(context);
  return state != nullptr && state->attached &&
         state->upstream_capture_frame != nullptr &&
         state->upstream_capture_frame(state->upstream_context, output);
}

bool IsMainThread(void *context) noexcept {
  auto *const state = State(context);
  return state != nullptr && state->attached &&
         state->upstream_is_main_thread != nullptr &&
         state->upstream_is_main_thread(state->upstream_context);
}

bool ReadMemory(void *context, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  auto *const state = State(context);
  return state != nullptr && state->attached &&
         state->operations.read_memory(state->operation_context,
                                       reinterpret_cast<const void *>(address),
                                       output, size);
}

bool InvokeDatabaseGetter(void *context, std::uintptr_t function,
                          void *&output) noexcept {
  auto *const state = State(context);
  output = nullptr;
  return state != nullptr && state->attached &&
         Matches(function, state->module_base,
                 kCharacterInteractionPreviewDatabaseGetterRvaV1) &&
         state->operations.get_database(state->operation_context,
                                        state->module_base, output) &&
         output != nullptr;
}

bool InvokeStableHash(void *context, std::uintptr_t function, void *database,
                      std::string_view key, std::int32_t &output) noexcept {
  auto *const state = State(context);
  return state != nullptr && state->attached && database != nullptr &&
         Matches(function, state->module_base,
                 kCharacterInteractionPreviewStableKeyHashRvaV1) &&
         state->operations.hash_stable_key(
             state->operation_context, state->module_base, database, key,
             output);
}

bool InvokeDefinitionLookup(void *context, std::uintptr_t function,
                            void *database, std::int32_t key_hash,
                            void *&output) noexcept {
  auto *const state = State(context);
  output = nullptr;
  return state != nullptr && state->attached && database != nullptr &&
         Matches(function, state->module_base,
                 kCharacterInteractionPreviewDefinitionLookupRvaV1) &&
         state->operations.lookup_definition(
             state->operation_context, state->module_base, database, key_hash,
             output) &&
         output != nullptr;
}

bool InvokeConstruct(void *context, std::uintptr_t function,
                     void *context_storage, void *definition,
                     std::int32_t actor_character_id,
                     std::int32_t recipient_character_id,
                     void *&output) noexcept {
  auto *const state = State(context);
  output = nullptr;
  if (state == nullptr || !state->attached || state->context_active ||
      state->terminal_cleanup_failure || context_storage == nullptr ||
      definition == nullptr ||
      !Matches(function, state->module_base,
               kCharacterInteractionPreviewConstructContextRvaV1) ||
      !state->operations.construct_context(
          state->operation_context, state->module_base, context_storage,
          definition, actor_character_id, recipient_character_id, output) ||
      output != context_storage) {
    return false;
  }
  state->active_owned_context = output;
  state->context_active = true;
  return true;
}

bool ActiveContext(CharacterInteractionPreviewSourceStateV1 *state,
                   std::uintptr_t function, std::uintptr_t expected_rva,
                   void *interaction_context) noexcept {
  return state != nullptr && state->attached && state->context_active &&
         !state->terminal_cleanup_failure && interaction_context != nullptr &&
         interaction_context == state->active_owned_context &&
         Matches(function, state->module_base, expected_rva);
}

bool InvokeRefresh(void *context, std::uintptr_t function,
                   void *interaction_context) noexcept {
  auto *const state = State(context);
  return ActiveContext(state, function,
                       kCharacterInteractionPreviewRefreshContextRvaV1,
                       interaction_context) &&
         state->operations.refresh_context(state->operation_context,
                                           state->module_base,
                                           interaction_context, true);
}

bool InvokeFinalize(void *context, std::uintptr_t function,
                    void *interaction_context) noexcept {
  auto *const state = State(context);
  return ActiveContext(state, function,
                       kCharacterInteractionPreviewFinalizeContextRvaV1,
                       interaction_context) &&
         state->operations.finalize_context(state->operation_context,
                                            state->module_base,
                                            interaction_context);
}

bool InvokeCanSend(void *context, std::uintptr_t function,
                   void *interaction_context, bool &output) noexcept {
  auto *const state = State(context);
  return ActiveContext(state, function,
                       kCharacterInteractionPreviewCanSendRvaV1,
                       interaction_context) &&
         state->operations.can_send(state->operation_context,
                                    state->module_base, interaction_context,
                                    output);
}

bool InvokeCosts(
    void *context, std::uintptr_t function, void *interaction_context,
    std::array<std::int64_t, game::kCharacterInteractionPreviewCostCountV1>
        &output) noexcept {
  auto *const state = State(context);
  return ActiveContext(state, function,
                       kCharacterInteractionPreviewCostEvaluatorRvaV1,
                       interaction_context) &&
         state->operations.evaluate_costs(state->operation_context,
                                          state->module_base,
                                          interaction_context, output);
}

template <typename T>
bool ReadAt(CharacterInteractionPreviewSourceStateV1 &state,
            const void *base, std::size_t offset, T &output) noexcept {
  return base != nullptr &&
         state.operations.read_memory(
             state.operation_context,
             static_cast<const std::byte *>(base) + offset, &output,
             sizeof(output));
}

bool InvokeAcceptance(
    void *context, std::uintptr_t auto_accept_function,
    std::uintptr_t intermediary_raw_function,
    std::uintptr_t recipient_raw_function,
    std::uintptr_t outer_final_function, void *interaction_context,
    game::CharacterInteractionPreviewAcceptanceV1 &output) noexcept {
  auto *const state = State(context);
  output = {};
  if (!ActiveContext(state, auto_accept_function,
                     kCharacterInteractionPreviewAutoAcceptEvaluatorRvaV1,
                     interaction_context) ||
      !Matches(intermediary_raw_function, state->module_base,
               kCharacterInteractionPreviewIntermediaryRawRvaV1) ||
      !Matches(recipient_raw_function, state->module_base,
               kCharacterInteractionPreviewRecipientRawRvaV1) ||
      !Matches(outer_final_function, state->module_base,
               kCharacterInteractionPreviewOuterFinalRvaV1)) {
    return false;
  }

  void *definition = nullptr;
  std::int32_t recipient_id = kInvalidCharacterId;
  std::int32_t intermediary_id = kInvalidCharacterId;
  void *trigger = nullptr;
  if (!ReadAt(*state, interaction_context, kContextDefinitionOffset,
              definition) ||
      definition == nullptr ||
      !ReadAt(*state, interaction_context, kContextRecipientIdOffset,
              recipient_id) ||
      recipient_id == kInvalidCharacterId ||
      !ReadAt(*state, interaction_context, kContextIntermediaryIdOffset,
              intermediary_id) ||
      !ReadAt(*state, definition, kDefinitionAutoAcceptTriggerOffset,
              trigger)) {
    return false;
  }

  bool auto_accept = false;
  if (trigger != nullptr) {
    if (!state->operations.evaluate_trigger(
            state->operation_context, state->module_base, trigger,
            static_cast<const std::byte *>(interaction_context) +
                kContextEventTargetScopeOffset,
            auto_accept)) {
      return false;
    }
  } else {
    std::uint8_t scalar = 0;
    if (!ReadAt(*state, definition, kDefinitionAutoAcceptScalarOffset,
                scalar) ||
        scalar > 1) {
      return false;
    }
    auto_accept = scalar != 0;
  }

  bool human = false;
  if (!state->operations.is_human_player(
          state->operation_context, state->module_base, recipient_id, human)) {
    return false;
  }
  output.recipient_is_ai = !human;
  if (auto_accept) {
    output.kind = game::CharacterInteractionAcceptanceKindV1::auto_accept;
    output.auto_accept = true;
    output.would_accept_now_present = true;
    output.would_accept_now = true;
    return true;
  }
  if (human) {
    output.kind = game::CharacterInteractionAcceptanceKindV1::human_pending;
    return true;
  }

  output.kind = game::CharacterInteractionAcceptanceKindV1::ai_final;
  output.recipient_is_ai = true;
  output.intermediary_present = intermediary_id != kInvalidCharacterId;
  if (output.intermediary_present) {
    if (!state->operations.intermediary_raw(
            state->operation_context, state->module_base, interaction_context,
            output.intermediary_raw)) {
      return false;
    }
    output.intermediary_raw_present = true;
  }
  if (!state->operations.recipient_raw(
          state->operation_context, state->module_base, interaction_context,
          output.recipient_raw)) {
    return false;
  }
  output.recipient_raw_present = true;
  if (!state->operations.outer_final(
          state->operation_context, state->module_base, interaction_context,
          output.final_status_raw) ||
      output.final_status_raw < 0 || output.final_status_raw > 2) {
    return false;
  }
  output.final_status_present = true;
  output.would_accept_now_present = true;
  output.would_accept_now = output.final_status_raw != 2;
  return true;
}

bool InvokeDestroy(void *context, std::uintptr_t function,
                   void *interaction_context) noexcept {
  auto *const state = State(context);
  if (state == nullptr || !state->attached || !state->context_active ||
      interaction_context == nullptr ||
      interaction_context != state->active_owned_context ||
      !Matches(function, state->module_base,
               kCharacterInteractionPreviewDestroyContextRvaV1)) {
    return false;
  }

  // Relinquish the owned address before native teardown so no error path can
  // try to destroy the same context twice.
  state->active_owned_context = nullptr;
  state->context_active = false;
  if (!state->operations.destroy_context(state->operation_context,
                                         state->module_base,
                                         interaction_context)) {
    state->terminal_cleanup_failure = true;
    return false;
  }
  ++state->completed_context_count;
  return true;
}

CharacterInteractionPreviewAccessV1 CoreAccess(
    CharacterInteractionPreviewSourceStateV1 &state) noexcept {
  return {&state,
          &CaptureFrame,
          &IsMainThread,
          &ReadMemory,
          &InvokeStableHash,
          &InvokeDatabaseGetter,
          &InvokeDefinitionLookup,
          &InvokeConstruct,
          &InvokeRefresh,
          &InvokeFinalize,
          &InvokeCanSend,
          &InvokeCosts,
          &InvokeAcceptance,
          &InvokeDestroy};
}

} // namespace

bool BindCharacterInteractionPreviewSourceAdapterV1(
    const CharacterInteractionPreviewSourceEnvironmentV1 &environment,
    CharacterInteractionPreviewSourceStateV1 &state) noexcept {
  if (state.context_active || environment.adapter_enabled == false ||
      environment.exact_build_admitted == false ||
      environment.admitted_executable_sha256 !=
          kCharacterInteractionPreviewExecutableSha256V1 ||
      environment.module_base == 0 || environment.capture_frame == nullptr ||
      environment.is_main_thread == nullptr) {
    return false;
  }

  const bool has_overrides = Any(environment.operations);
  if (has_overrides && !Complete(environment.operations)) return false;

  CharacterInteractionPreviewSourceStateV1 candidate{};
  candidate.module_base = environment.module_base;
  candidate.operation_context = environment.operation_context;
  candidate.operations =
      has_overrides ? environment.operations : DefaultOperations();
  candidate.upstream_context = environment.upstream_context;
  candidate.upstream_capture_frame = environment.capture_frame;
  candidate.upstream_is_main_thread = environment.is_main_thread;
  candidate.core_environment = BindCharacterInteractionPreviewEnvironmentV1(
      environment.module_base, environment.exact_build_admitted,
      environment.admitted_executable_sha256);
  candidate.core_environment.offline_fixture = environment.offline_fixture;
  candidate.attached = true;
  candidate.core_access = CoreAccess(candidate);
  state = candidate;
  // CoreAccess embeds the state address, so rebuild it after the value copy.
  state.core_access = CoreAccess(state);
  return true;
}

game::ReadCharacterInteractionPreviewResultV1
ReadCharacterInteractionPreviewFromSourceAdapterV1(
    CharacterInteractionPreviewSourceStateV1 &state,
    const CharacterInteractionPreviewRequestV1 &request,
    game::CharacterInteractionPreviewV1 &output) noexcept {
  if (!state.attached || state.context_active ||
      state.terminal_cleanup_failure) {
    output = {};
    output.status = game::CharacterInteractionPreviewStatusV1::unavailable;
    output.unavailable_reason =
        game::CharacterInteractionPreviewFailureV1::native_bindings_unavailable;
    return game::ReadCharacterInteractionPreviewResultV1::unavailable;
  }
  return ReadCharacterInteractionPreviewV1(state.core_environment,
                                           state.core_access, request, output);
}

} // namespace xar::ck3_11906
