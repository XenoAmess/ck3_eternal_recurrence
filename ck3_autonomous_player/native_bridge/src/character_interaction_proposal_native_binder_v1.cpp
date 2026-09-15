#include "xar_bridge/character_interaction_proposal_native_binder_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#define NOMINMAX
#include <windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

using AckStatus = game::CharacterInteractionProposalActionAckStatusV1;
using BinderFailure = CharacterInteractionProposalNativeBinderFailureV1;
using BinderResult = CharacterInteractionProposalNativeBindResultV1;
using Capture = CharacterInteractionProposalNativeCaptureV1;
using PayloadSource = game::CharacterInteractionProposalPayloadSourceV1;

constexpr std::size_t kContextDefinitionOffset = 0x00;
constexpr std::size_t kContextActorOffset = 0x2D8;
constexpr std::size_t kContextRecipientOffset = 0x2DC;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::uint32_t kStorageSlotMask = 0x00FFFFFFU;
constexpr std::int32_t kInvalidCharacterId = -1;

struct alignas(8) ContextStorage {
  std::array<std::byte, kCharacterInteractionProposalNativeContextSizeV1>
      bytes{};
};

struct alignas(8) CommandStorage {
  std::array<std::byte, kCharacterInteractionProposalNativeCommandSizeV1>
      bytes{};
};

static_assert(sizeof(ContextStorage) == 0x338);
static_assert(sizeof(CommandStorage) == 0x368);

bool AddRva(std::uintptr_t module, std::uintptr_t rva,
            std::uintptr_t &output) noexcept {
  if (module == 0 || module >
                         (std::numeric_limits<std::uintptr_t>::max)() - rva) {
    return false;
  }
  output = module + rva;
  return true;
}

template <typename Function>
bool Matches(Function function, std::uintptr_t module,
             std::uintptr_t rva) noexcept {
  std::uintptr_t expected = 0;
  return AddRva(module, rva, expected) &&
         reinterpret_cast<std::uintptr_t>(function) == expected;
}

bool DirectRead(void *, const void *address, void *output,
                std::size_t size) noexcept {
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

template <typename Value>
bool ReadAt(const CharacterInteractionProposalNativeBinderEnvironmentV1 &env,
            const void *base, std::size_t offset, Value &output) noexcept {
  if (base == nullptr || env.read_memory == nullptr ||
      reinterpret_cast<std::uintptr_t>(base) >
          (std::numeric_limits<std::uintptr_t>::max)() - offset) {
    return false;
  }
  const auto *address = static_cast<const std::byte *>(base) + offset;
  return env.read_memory(env.memory_context, address, &output,
                         sizeof(output));
}

bool IsTypedSpecial(std::string_view key) noexcept {
  return key == "educate_child_interaction" ||
         key == "offer_ward_interaction" ||
         key == "offer_guardianship_interaction" ||
         key == "grant_titles_interaction" ||
         key == "grant_vassal_interaction" || key == "ransom_interaction";
}

bool SamePayloadSource(const PayloadSource &left,
                       const PayloadSource &right) noexcept {
  return left.available == right.available && left.failure == right.failure &&
         left.reason == right.reason && left.snapshot_id == right.snapshot_id &&
         left.public_revision == right.public_revision &&
         left.native_revision == right.native_revision &&
         left.proof_epoch == right.proof_epoch &&
         left.date_raw == right.date_raw &&
         left.interaction_key == right.interaction_key &&
         left.actor_character_id == right.actor_character_id &&
         left.recipient_character_id == right.recipient_character_id &&
         left.secondary_actor_character_id ==
             right.secondary_actor_character_id &&
         left.secondary_recipient_character_id ==
             right.secondary_recipient_character_id &&
         left.intermediary_character_id == right.intermediary_character_id &&
         left.selected_option_mask == right.selected_option_mask &&
         left.selected_title_ids == right.selected_title_ids &&
         left.payload == right.payload;
}

bool SourceMatchesEnvelope(
    const PayloadSource &source,
    const game::CharacterInteractionProposalPreviewEnvelopeV1 &envelope)
    noexcept {
  const auto &preview = envelope.preview;
  return source.available &&
         source.failure ==
             game::CharacterInteractionProposalPayloadSourceFailureV1::none &&
         source.snapshot_id == preview.snapshot_id &&
         source.public_revision == preview.public_revision &&
         source.native_revision == preview.native_revision &&
         source.proof_epoch == preview.proof_epoch &&
         source.date_raw == preview.date_raw &&
         source.interaction_key == preview.definition.canonical_key &&
         source.actor_character_id == preview.roles.actor_character_id &&
         source.recipient_character_id ==
             preview.roles.recipient_character_id &&
         source.payload == envelope.payload;
}

void SetFailure(CharacterInteractionProposalNativeBinderStateV1 &binder,
                BinderFailure failure) noexcept {
  binder.last_failure.store(static_cast<std::uint32_t>(failure),
                            std::memory_order_release);
}

void *ResolveCharacter(
    const CharacterInteractionProposalNativeBinderEnvironmentV1 &env,
    std::int32_t full_id) noexcept {
  if (env.character_storage_slot == nullptr ||
      full_id == kInvalidCharacterId) {
    return nullptr;
  }
  void *storage = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!env.read_memory(env.memory_context, env.character_storage_slot,
                       &storage, sizeof(storage)) ||
      storage == nullptr ||
      !ReadAt(env, storage, kStorageSlotsOffset, slots) || slots == nullptr ||
      !ReadAt(env, storage, kStorageCapacityOffset, capacity) ||
      capacity <= 0) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & kStorageSlotMask;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      index > ((std::numeric_limits<std::uintptr_t>::max)() -
                   reinterpret_cast<std::uintptr_t>(slots) -
                   kStorageSlotObjectOffset) /
                  kStorageSlotStride) {
    return nullptr;
  }
  const auto *slot = static_cast<const std::byte *>(slots) +
                     static_cast<std::size_t>(index) * kStorageSlotStride;
  void *character = nullptr;
  std::int32_t observed_id = kInvalidCharacterId;
  if (!ReadAt(env, slot, kStorageSlotObjectOffset, character) ||
      character == nullptr ||
      !ReadAt(env, character, kCharacterIdentityOffset, observed_id) ||
      observed_id != full_id) {
    return nullptr;
  }
  return character;
}

bool InvokeGetDatabase(CharacterInteractionProposalGetDatabaseV1 function,
                       void *&output) noexcept {
  output = nullptr;
  if (function == nullptr) return false;
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = function();
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = function();
#endif
  return output != nullptr;
}

bool InvokeHash(CharacterInteractionProposalHashStableKeyV1 function,
                void *database, std::string_view key,
                std::int32_t &output) noexcept {
  if (function == nullptr || database == nullptr || key.empty() ||
      key.size() > (std::numeric_limits<std::uint32_t>::max)()) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = function(database, key.data(),
                      static_cast<std::uint32_t>(key.size()));
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output =
      function(database, key.data(), static_cast<std::uint32_t>(key.size()));
#endif
  return true;
}

bool InvokeLookup(CharacterInteractionProposalLookupDefinitionV1 function,
                  void *database, std::int32_t stable_hash,
                  void *&output) noexcept {
  output = nullptr;
  if (function == nullptr || database == nullptr) return false;
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = function(database, stable_hash);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = function(database, stable_hash);
#endif
  return output != nullptr;
}

bool LookupDefinition(
    const CharacterInteractionProposalNativeBinderEnvironmentV1 &env,
    std::string_view key, void *&output) noexcept {
  void *database = nullptr;
  std::int32_t hash = 0;
  return InvokeGetDatabase(env.get_database, database) &&
         InvokeHash(env.hash_stable_key, database, key, hash) &&
         InvokeLookup(env.lookup_definition, database, hash, output);
}

bool InvokeConstructTwoRole(
    CharacterInteractionProposalConstructTwoRoleContextV1 function,
    void *storage, void *definition, std::int32_t actor_id,
    std::int32_t recipient_id, void *&output) noexcept {
  output = nullptr;
  if (function == nullptr || storage == nullptr || definition == nullptr) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = function(storage, definition, actor_id, recipient_id, nullptr,
                      true);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output =
      function(storage, definition, actor_id, recipient_id, nullptr, true);
#endif
  return output == storage;
}

bool InvokeMaterializer(
    MaterializeCharacterInteractionProposalSpecialContextV1 function,
    void *callback_context, const PayloadSource &source, void *storage,
    std::size_t size, void *definition, void *&output) noexcept {
  output = nullptr;
  if (function == nullptr || storage == nullptr || definition == nullptr) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    return function(callback_context, source, storage, size, definition,
                    output) &&
           output == storage;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  return function(callback_context, source, storage, size, definition,
                  output) &&
         output == storage;
#endif
}

bool InvokeRefresh(CharacterInteractionProposalRefreshContextV1 function,
                   void *context) noexcept {
  if (function == nullptr || context == nullptr) return false;
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    function(context, true);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  function(context, true);
#endif
  return true;
}

bool InvokeStep(CharacterInteractionProposalContextStepV1 function,
                void *context) noexcept {
  if (function == nullptr || context == nullptr) return false;
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    function(context);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  function(context);
#endif
  return true;
}

bool InvokeCanSend(CharacterInteractionProposalCanSendV1 function,
                   void *context, bool &output) noexcept {
  output = false;
  if (function == nullptr || context == nullptr) return false;
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = function(context, nullptr);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = function(context, nullptr);
#endif
  return true;
}

bool InvokeConstructCommand(
    ConstructCharacterInteractionProposalCommandV1 function, void *storage,
    const void *context, void *&output) noexcept {
  output = nullptr;
  if (function == nullptr || storage == nullptr || context == nullptr) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    output = function(storage, context);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = function(storage, context);
#endif
  return output == storage;
}

bool InvokeSubmit(SubmitCharacterInteractionProposalCommandV1 function,
                  void *manager, void *command,
                  std::uint32_t flags) noexcept {
  if (function == nullptr || manager == nullptr || command == nullptr) {
    return false;
  }
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    return function(manager, command, flags);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return function(manager, command, flags);
#endif
}

struct ReReadContext {
  CharacterInteractionProposalNativeBinderStateV1 *binder = nullptr;
  void *interaction_context = nullptr;
  void *definition = nullptr;
};

bool ReReadCollector(
    void *context, std::string_view interaction_key,
    std::int32_t actor_character_id, std::int32_t recipient_character_id,
    CharacterInteractionProposalPayloadCollectorMemoryV1 &output) noexcept {
  auto *const value = static_cast<ReReadContext *>(context);
  if (value == nullptr || value->binder == nullptr ||
      value->interaction_context == nullptr ||
      interaction_key !=
          value->binder->bound_capture.envelope.preview.definition.canonical_key ||
      actor_character_id !=
          value->binder->bound_capture.envelope.preview.roles.actor_character_id ||
      recipient_character_id != value->binder->bound_capture.envelope.preview
                                    .roles.recipient_character_id) {
    return false;
  }
  output = {};
  output.interaction_context = value->interaction_context;
  const auto &preview = value->binder->bound_capture.envelope.preview;
  output.frame.snapshot_id = preview.snapshot_id;
  output.frame.public_revision = preview.public_revision;
  output.frame.native_revision = preview.native_revision;
  output.frame.proof_epoch = preview.proof_epoch;
  output.frame.date_raw = preview.date_raw;
  output.frame.paused = true;
  output.frame.map_ready = true;
  output.frame.has_played_character = true;
  output.frame.played_character_alive = true;
  output.frame.played_character_id = preview.roles.actor_character_id;
  return true;
}

bool ReReadMemory(void *context, const void *address, void *output,
                  std::size_t size) noexcept {
  auto *const value = static_cast<ReReadContext *>(context);
  return value != nullptr && value->binder != nullptr &&
         value->binder->environment.read_memory != nullptr &&
         value->binder->environment.read_memory(
             value->binder->environment.memory_context, address, output,
             size);
}

bool ReLookupDefinition(void *context, std::string_view key,
                        void *&output) noexcept {
  auto *const value = static_cast<ReReadContext *>(context);
  output = nullptr;
  return value != nullptr && value->binder != nullptr &&
         LookupDefinition(value->binder->environment, key, output) &&
         output == value->definition;
}

bool ReReadSpecialSource(
    CharacterInteractionProposalNativeBinderStateV1 &binder, void *context,
    void *definition) noexcept {
  ReReadContext reread{&binder, context, definition};
  CharacterInteractionProposalPayloadSourceEnvironmentV1 environment{};
  environment.enabled = true;
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      binder.environment.admitted_executable_sha256;
  environment.offline_fixture = binder.environment.offline_fixture;
  environment.module_base = binder.environment.module_base;
  environment.character_storage_slot =
      binder.environment.character_storage_slot;
  environment.landed_title_storage_slot =
      binder.environment.landed_title_storage_slot;
  CharacterInteractionProposalPayloadSourceAccessV1 access{};
  access.context = &reread;
  access.capture_collector = &ReReadCollector;
  access.read_memory = &ReReadMemory;
  access.lookup_definition = &ReLookupDefinition;
  PayloadSource observed{};
  const auto result = ReadCharacterInteractionProposalPayloadSourceV1(
      environment, access, binder.bound_capture.envelope.preview, observed);
  const bool same = SamePayloadSource(
      observed, binder.bound_capture.typed_payload_source);
  return result ==
             game::ReadCharacterInteractionProposalPayloadSourceResultV1::
                 available &&
         same;
}

bool ReadContextIdentity(
    const CharacterInteractionProposalNativeBinderEnvironmentV1 &environment,
    const void *context, void *definition, std::int32_t actor_id,
    std::int32_t recipient_id) noexcept {
  void *observed_definition = nullptr;
  std::int32_t observed_actor = kInvalidCharacterId;
  std::int32_t observed_recipient = kInvalidCharacterId;
  return ReadAt(environment, context, kContextDefinitionOffset,
                observed_definition) &&
         observed_definition == definition &&
         ReadAt(environment, context, kContextActorOffset, observed_actor) &&
         observed_actor == actor_id &&
         ReadAt(environment, context, kContextRecipientOffset,
                observed_recipient) &&
         observed_recipient == recipient_id;
}

void DestroyIfOwned(
    const CharacterInteractionProposalNativeBinderEnvironmentV1 &environment,
    void *context) noexcept {
  if (context != nullptr) {
    (void)InvokeStep(environment.destroy_context, context);
  }
}

bool CapturePreview(
    void *context,
    game::CharacterInteractionProposalPreviewEnvelopeV1 &output) noexcept {
  auto *const binder =
      static_cast<CharacterInteractionProposalNativeBinderStateV1 *>(context);
  if (binder == nullptr || !binder->configured ||
      binder->active_request == nullptr || binder->capture_count >= 2 ||
      binder->environment.capture == nullptr) {
    if (binder != nullptr) SetFailure(*binder, BinderFailure::capture_unavailable);
    return false;
  }
  try {
    Capture captured{};
    if (!binder->environment.capture(binder->environment.capture_context,
                                     *binder->active_request, captured)) {
      SetFailure(*binder, BinderFailure::capture_unavailable);
      return false;
    }
    const bool special = IsTypedSpecial(binder->active_request->interaction_key);
    if (special != captured.typed_payload_source_present) {
      SetFailure(*binder, special ? BinderFailure::typed_payload_source_required
                                  : BinderFailure::typed_payload_source_mismatch);
      return false;
    }
    if (special &&
        !SourceMatchesEnvelope(captured.typed_payload_source,
                               captured.envelope)) {
      SetFailure(*binder, BinderFailure::typed_payload_source_mismatch);
      return false;
    }
    if (binder->capture_count == 1 &&
        (!SamePayloadSource(binder->bound_capture.typed_payload_source,
                            captured.typed_payload_source) ||
         binder->bound_capture.typed_payload_source_present !=
             captured.typed_payload_source_present)) {
      SetFailure(*binder, BinderFailure::capture_drift);
      return false;
    }
    binder->bound_capture = captured;
    ++binder->capture_count;
    output = std::move(captured.envelope);
    return true;
  } catch (...) {
    SetFailure(*binder, BinderFailure::capture_unavailable);
    return false;
  }
}

bool SubmitOnce(
    void *context,
    const game::CharacterInteractionProposalActionRequestV1 &request,
    const game::CharacterInteractionProposalPreviewEnvelopeV1 &envelope)
    noexcept {
  auto *const binder =
      static_cast<CharacterInteractionProposalNativeBinderStateV1 *>(context);
  if (binder == nullptr || !binder->configured || binder->submit_called ||
      binder->active_request != &request || binder->capture_count != 2) {
    if (binder != nullptr) SetFailure(*binder, BinderFailure::capture_drift);
    return false;
  }
  binder->submit_called = true;
  auto &environment = binder->environment;
  const bool special = IsTypedSpecial(request.interaction_key);
  if (special && (!binder->bound_capture.typed_payload_source_present ||
                  !SourceMatchesEnvelope(
                      binder->bound_capture.typed_payload_source, envelope))) {
    SetFailure(*binder, BinderFailure::typed_payload_source_mismatch);
    return false;
  }

  void *definition = nullptr;
  if (!LookupDefinition(environment, request.interaction_key, definition)) {
    SetFailure(*binder, BinderFailure::definition_lookup_failed);
    return false;
  }
  if (ResolveCharacter(environment, request.actor_character_id) == nullptr ||
      ResolveCharacter(environment, request.recipient_character_id) ==
          nullptr) {
    SetFailure(*binder, BinderFailure::character_identity_unavailable);
    return false;
  }

  ContextStorage context_storage{};
  void *native_context = nullptr;
  const bool constructed =
      special
          ? InvokeMaterializer(
                environment.materialize_special_context,
                environment.special_materializer_context,
                binder->bound_capture.typed_payload_source,
                context_storage.bytes.data(), context_storage.bytes.size(),
                definition, native_context)
          : InvokeConstructTwoRole(
                environment.construct_two_role_context,
                context_storage.bytes.data(), definition,
                request.actor_character_id, request.recipient_character_id,
                native_context);
  if (!constructed || native_context != context_storage.bytes.data()) {
    void *partial_definition = nullptr;
    if (ReadAt(environment, context_storage.bytes.data(),
               kContextDefinitionOffset, partial_definition) &&
        partial_definition != nullptr) {
      DestroyIfOwned(environment, context_storage.bytes.data());
    }
    SetFailure(*binder,
               special ? BinderFailure::special_context_materialization_failed
                       : BinderFailure::context_construction_failed);
    return false;
  }

  const auto fail_context = [&](BinderFailure failure) noexcept {
    SetFailure(*binder, failure);
    DestroyIfOwned(environment, native_context);
    return false;
  };
  if (!InvokeRefresh(environment.refresh_context, native_context) ||
      !InvokeStep(environment.finalize_context, native_context)) {
    return fail_context(BinderFailure::context_construction_failed);
  }
  if (!ReadContextIdentity(environment, native_context, definition,
                           request.actor_character_id,
                           request.recipient_character_id)) {
    return fail_context(BinderFailure::context_identity_mismatch);
  }
  if (special && !ReReadSpecialSource(*binder, native_context, definition)) {
    return fail_context(BinderFailure::typed_payload_source_mismatch);
  }
  bool can_send = false;
  if (!InvokeCanSend(environment.complete_can_send, native_context,
                     can_send)) {
    return fail_context(BinderFailure::native_signature_mismatch);
  }
  if (!can_send) {
    return fail_context(BinderFailure::complete_can_send_rejected);
  }

  CommandStorage command_storage{};
  void *native_command = nullptr;
  if (!InvokeConstructCommand(environment.construct_command,
                              command_storage.bytes.data(), native_context,
                              native_command)) {
    void *partial_definition = nullptr;
    auto *const partial_context =
        command_storage.bytes.data() +
        kCharacterInteractionProposalCommandContextOffsetV1;
    if (ReadAt(environment, partial_context, kContextDefinitionOffset,
               partial_definition) &&
        partial_definition != nullptr) {
      DestroyIfOwned(environment, partial_context);
    }
    return fail_context(BinderFailure::command_construction_failed);
  }
  void *primary_vtable = nullptr;
  void *secondary_vtable = nullptr;
  void *embedded_definition = nullptr;
  const auto *embedded_context =
      command_storage.bytes.data() +
      kCharacterInteractionProposalCommandContextOffsetV1;
  const bool command_context_owned =
      ReadAt(environment, embedded_context, kContextDefinitionOffset,
             embedded_definition) &&
      embedded_definition != nullptr;
  const bool command_identity =
      ReadAt(environment, native_command, 0, primary_vtable) &&
      reinterpret_cast<std::uintptr_t>(primary_vtable) ==
          environment.command_primary_vtable &&
      ReadAt(environment, native_command,
             kCharacterInteractionProposalCommandSecondaryVtableOffsetV1,
             secondary_vtable) &&
      reinterpret_cast<std::uintptr_t>(secondary_vtable) ==
          environment.command_secondary_vtable &&
      command_context_owned &&
      ReadContextIdentity(environment, embedded_context, definition,
                          request.actor_character_id,
                          request.recipient_character_id) &&
      (!special ||
       ReReadSpecialSource(*binder,
                           const_cast<std::byte *>(embedded_context),
                           definition));
  if (!command_identity) {
    if (command_context_owned) {
      DestroyIfOwned(environment, const_cast<std::byte *>(embedded_context));
    }
    return fail_context(BinderFailure::command_identity_mismatch);
  }

  const bool submitted = InvokeSubmit(
      environment.submit_command, environment.command_manager, native_command,
      kCharacterInteractionProposalSubmitFlagsV1);
  DestroyIfOwned(environment, const_cast<std::byte *>(embedded_context));
  DestroyIfOwned(environment, native_context);
  if (!submitted) {
    SetFailure(*binder, BinderFailure::command_queue_rejected);
    return false;
  }
  SetFailure(*binder, BinderFailure::none);
  return true;
}

bool ExactBindings(
    const CharacterInteractionProposalNativeBinderEnvironmentV1 &environment)
    noexcept {
  if (environment.offline_fixture) return true;
  std::uintptr_t expected = 0;
  return AddRva(
             environment.module_base,
             kCharacterInteractionProposalPayloadCharacterStorageSlotRvaV1,
             expected) &&
         reinterpret_cast<std::uintptr_t>(
             environment.character_storage_slot) == expected &&
         AddRva(environment.module_base,
                kCharacterInteractionProposalPayloadTitleStorageSlotRvaV1,
                expected) &&
         reinterpret_cast<std::uintptr_t>(
             environment.landed_title_storage_slot) == expected &&
         Matches(environment.get_database, environment.module_base,
                 kCharacterInteractionProposalDatabaseGetterRvaV1) &&
         Matches(environment.hash_stable_key, environment.module_base,
                 kCharacterInteractionProposalStableKeyHashRvaV1) &&
         Matches(environment.lookup_definition, environment.module_base,
                 kCharacterInteractionProposalDefinitionLookupRvaV1) &&
         Matches(environment.construct_two_role_context,
                 environment.module_base,
                 kCharacterInteractionProposalConstructTwoRoleContextRvaV1) &&
         Matches(environment.refresh_context, environment.module_base,
                 kCharacterInteractionProposalRefreshContextRvaV1) &&
         Matches(environment.finalize_context, environment.module_base,
                 kCharacterInteractionProposalFinalizeContextRvaV1) &&
         Matches(environment.complete_can_send, environment.module_base,
                 kCharacterInteractionProposalCompleteCanSendRvaV1) &&
         Matches(environment.destroy_context, environment.module_base,
                 kCharacterInteractionProposalDestroyContextRvaV1) &&
         AddRva(environment.module_base,
                kCharacterInteractionProposalCommandManagerRvaV1, expected) &&
         reinterpret_cast<std::uintptr_t>(environment.command_manager) ==
             expected &&
         Matches(environment.construct_command, environment.module_base,
                 kCharacterInteractionProposalConstructCommandRvaV1) &&
         Matches(environment.submit_command, environment.module_base,
                 kCharacterInteractionProposalSubmitCommandRvaV1) &&
         AddRva(environment.module_base,
                kCharacterInteractionProposalCommandPrimaryVtableRvaV1,
                expected) &&
         environment.command_primary_vtable == expected &&
         AddRva(environment.module_base,
                kCharacterInteractionProposalCommandSecondaryVtableRvaV1,
                expected) &&
         environment.command_secondary_vtable == expected;
}

bool CompleteLifecycle(
    const CharacterInteractionProposalNativeBinderEnvironmentV1 &environment)
    noexcept {
  return environment.read_memory != nullptr &&
         environment.character_storage_slot != nullptr &&
         environment.landed_title_storage_slot != nullptr &&
         environment.get_database != nullptr &&
         environment.hash_stable_key != nullptr &&
         environment.lookup_definition != nullptr &&
         environment.construct_two_role_context != nullptr &&
         environment.refresh_context != nullptr &&
         environment.finalize_context != nullptr &&
         environment.complete_can_send != nullptr &&
         environment.destroy_context != nullptr &&
         environment.command_manager != nullptr &&
         environment.construct_command != nullptr &&
         environment.submit_command != nullptr &&
         environment.command_primary_vtable != 0 &&
         environment.command_secondary_vtable != 0;
}

AckStatus RejectBinder(
    const game::CharacterInteractionProposalActionRequestV1 &request,
    BinderFailure failure,
    game::CharacterInteractionProposalActionAckV1 &ack) noexcept {
  ack = {};
  ack.status = AckStatus::rejected_before_submit;
  ack.verification_pending = false;
  ack.request_id = request.request_id;
  ack.interaction_key = request.interaction_key;
  ack.actor_character_id = request.actor_character_id;
  ack.recipient_character_id = request.recipient_character_id;
  ack.failure = failure == BinderFailure::exact_build_not_admitted
                    ? game::CharacterInteractionProposalActionFailureV1::
                          exact_build_not_admitted
                    : game::CharacterInteractionProposalActionFailureV1::
                          submit_seam_unavailable;
  ack.reason = CharacterInteractionProposalNativeBinderFailureKeyV1(failure);
  return ack.status;
}

} // namespace

CharacterInteractionProposalNativeBinderEnvironmentV1
BindCharacterInteractionProposalNativeBinderEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  CharacterInteractionProposalNativeBinderEnvironmentV1 result{};
  result.module_base = module_base;
  result.exact_build_admitted = exact_build_admitted;
  result.admitted_executable_sha256 = admitted_executable_sha256;
  if (!exact_build_admitted ||
      admitted_executable_sha256 !=
          kCharacterInteractionProposalNativeBinderExecutableSha256V1 ||
      module_base == 0 ||
      module_base > (std::numeric_limits<std::uintptr_t>::max)() -
                        kCharacterInteractionProposalCommandManagerRvaV1) {
    return result;
  }
  result.read_memory = &DirectRead;
  result.character_storage_slot = reinterpret_cast<void **>(
      module_base +
      kCharacterInteractionProposalPayloadCharacterStorageSlotRvaV1);
  result.landed_title_storage_slot = reinterpret_cast<void **>(
      module_base + kCharacterInteractionProposalPayloadTitleStorageSlotRvaV1);
  result.get_database =
      reinterpret_cast<CharacterInteractionProposalGetDatabaseV1>(
          module_base + kCharacterInteractionProposalDatabaseGetterRvaV1);
  result.hash_stable_key =
      reinterpret_cast<CharacterInteractionProposalHashStableKeyV1>(
          module_base + kCharacterInteractionProposalStableKeyHashRvaV1);
  result.lookup_definition =
      reinterpret_cast<CharacterInteractionProposalLookupDefinitionV1>(
          module_base + kCharacterInteractionProposalDefinitionLookupRvaV1);
  result.construct_two_role_context =
      reinterpret_cast<CharacterInteractionProposalConstructTwoRoleContextV1>(
          module_base +
          kCharacterInteractionProposalConstructTwoRoleContextRvaV1);
  result.refresh_context =
      reinterpret_cast<CharacterInteractionProposalRefreshContextV1>(
          module_base + kCharacterInteractionProposalRefreshContextRvaV1);
  result.finalize_context =
      reinterpret_cast<CharacterInteractionProposalContextStepV1>(
          module_base + kCharacterInteractionProposalFinalizeContextRvaV1);
  result.complete_can_send =
      reinterpret_cast<CharacterInteractionProposalCanSendV1>(
          module_base + kCharacterInteractionProposalCompleteCanSendRvaV1);
  result.destroy_context =
      reinterpret_cast<CharacterInteractionProposalContextStepV1>(
          module_base + kCharacterInteractionProposalDestroyContextRvaV1);
  result.command_manager = reinterpret_cast<void *>(
      module_base + kCharacterInteractionProposalCommandManagerRvaV1);
  result.construct_command =
      reinterpret_cast<ConstructCharacterInteractionProposalCommandV1>(
          module_base + kCharacterInteractionProposalConstructCommandRvaV1);
  result.submit_command =
      reinterpret_cast<SubmitCharacterInteractionProposalCommandV1>(
          module_base + kCharacterInteractionProposalSubmitCommandRvaV1);
  result.command_primary_vtable =
      module_base + kCharacterInteractionProposalCommandPrimaryVtableRvaV1;
  result.command_secondary_vtable =
      module_base + kCharacterInteractionProposalCommandSecondaryVtableRvaV1;
  return result;
}

BinderResult ConfigureCharacterInteractionProposalNativeBinderV1(
    CharacterInteractionProposalNativeBinderStateV1 &binder) noexcept {
  binder.configured = false;
  if (!binder.environment.exact_build_admitted ||
      binder.environment.admitted_executable_sha256 !=
          kCharacterInteractionProposalNativeBinderExecutableSha256V1) {
    SetFailure(binder, BinderFailure::exact_build_not_admitted);
    return BinderResult::blocked;
  }
  if (!CompleteLifecycle(binder.environment)) {
    SetFailure(binder, BinderFailure::native_lifecycle_unavailable);
    return BinderResult::blocked;
  }
  if (!ExactBindings(binder.environment)) {
    SetFailure(binder, BinderFailure::native_binding_mismatch);
    return BinderResult::failed;
  }
  if (binder.environment.capture == nullptr) {
    SetFailure(binder, BinderFailure::capture_unavailable);
    return BinderResult::blocked;
  }
  if (binder.environment.materialize_special_context == nullptr) {
    SetFailure(binder, BinderFailure::special_context_materializer_unavailable);
    return BinderResult::blocked;
  }
  binder.configured = true;
  SetFailure(binder, BinderFailure::none);
  return BinderResult::available;
}

AckStatus ExecuteCharacterInteractionProposalFromNativeBinderV1(
    CharacterInteractionProposalNativeBinderStateV1 &binder,
    const game::CharacterInteractionProposalActionRequestV1 &request,
    game::CharacterInteractionProposalActionAckV1 &ack) noexcept {
  const auto configured =
      ConfigureCharacterInteractionProposalNativeBinderV1(binder);
  if (configured != BinderResult::available) {
    return RejectBinder(request,
                        ReadCharacterInteractionProposalNativeBinderFailureV1(
                            binder),
                        ack);
  }
  binder.active_request = &request;
  binder.bound_capture = {};
  binder.capture_count = 0;
  binder.submit_called = false;
  CharacterInteractionProposalActionEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.submit_abi_certified = !binder.environment.offline_fixture;
  environment.offline_fixture_submit = binder.environment.offline_fixture;
  CharacterInteractionProposalActionAccessV1 access{};
  access.context = &binder;
  access.capture_preview = &CapturePreview;
  access.submit_once = &SubmitOnce;
  const auto status = ExecuteCharacterInteractionProposalActionCoreV1(
      environment, access, binder.action_state, request, ack);
  binder.active_request = nullptr;
  const auto native_failure =
      ReadCharacterInteractionProposalNativeBinderFailureV1(binder);
  if (status == AckStatus::rejected_before_submit &&
      native_failure != BinderFailure::none) {
    try {
      ack.reason.assign(
          CharacterInteractionProposalNativeBinderFailureKeyV1(
              native_failure));
    } catch (...) {
    }
  }
  return status;
}

BinderFailure ReadCharacterInteractionProposalNativeBinderFailureV1(
    const CharacterInteractionProposalNativeBinderStateV1 &binder) noexcept {
  return static_cast<BinderFailure>(
      binder.last_failure.load(std::memory_order_acquire));
}

std::string_view CharacterInteractionProposalNativeBinderFailureKeyV1(
    BinderFailure failure) noexcept {
  using enum CharacterInteractionProposalNativeBinderFailureV1;
  switch (failure) {
  case none: return "none";
  case exact_build_not_admitted: return "exact_build_not_admitted";
  case native_binding_mismatch: return "native_binding_mismatch";
  case native_signature_mismatch: return "native_signature_mismatch";
  case native_lifecycle_unavailable: return "native_lifecycle_unavailable";
  case capture_unavailable: return "capture_unavailable";
  case capture_drift: return "capture_drift";
  case typed_payload_source_required: return "typed_payload_source_required";
  case typed_payload_source_mismatch: return "typed_payload_source_mismatch";
  case special_context_materializer_unavailable:
    return "special_context_materializer_unavailable";
  case special_context_materialization_failed:
    return "special_context_materialization_failed";
  case definition_lookup_failed: return "definition_lookup_failed";
  case character_identity_unavailable:
    return "character_identity_unavailable";
  case context_construction_failed: return "context_construction_failed";
  case context_identity_mismatch: return "context_identity_mismatch";
  case complete_can_send_rejected: return "complete_can_send_rejected";
  case command_construction_failed: return "command_construction_failed";
  case command_identity_mismatch: return "command_identity_mismatch";
  case command_queue_rejected: return "command_queue_rejected";
  }
  return "native_signature_mismatch";
}

} // namespace xar::ck3_11906
