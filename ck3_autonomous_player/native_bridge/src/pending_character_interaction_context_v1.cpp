#include "xar_bridge/pending_character_interaction_context_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kComponentIdentityOffset = 0x10;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kPendingDefinitionOffset = 0x18;
constexpr std::size_t kPendingPrimaryScopeOffset = 0x20;
constexpr std::size_t kPendingActorOffset = 0x2F0;
constexpr std::size_t kPendingRecipientOffset = 0x2F4;
constexpr std::size_t kPendingSecondaryActorOffset = 0x2F8;
constexpr std::size_t kPendingSecondaryRecipientOffset = 0x2FC;
constexpr std::size_t kPendingIntermediaryOffset = 0x300;
constexpr std::size_t kPendingTargetEnvelopeOffset = 0x308;
constexpr std::size_t kPendingSelectedOptionsDataOffset = 0x318;
constexpr std::size_t kPendingSelectedOptionsCapacityOffset = 0x320;
constexpr std::size_t kPendingSelectedOptionsCountOffset = 0x324;
constexpr std::size_t kPendingSpecialDataOffset = 0x348;
constexpr std::size_t kPendingAgeDaysOffset = 0x5B8;
constexpr std::size_t kPendingRoutingKindOffset = 0x5C0;
constexpr std::size_t kPendingAutoAcceptNotificationOffset = 0x5C6;
constexpr std::size_t kDefinitionRuntimeOrdinalOffset = 0x10;
constexpr std::size_t kDefinitionKeyHashOffset = 0x14;
constexpr std::size_t kDefinitionCanonicalKeyOffset = 0x18;
constexpr std::size_t kDefinitionSendOptionRowsOffset = 0x2548;
constexpr std::size_t kDefinitionSendOptionCountOffset = 0x2554;
constexpr std::size_t kDefinitionAutoAcceptTriggerOffset = 0x2580;
constexpr std::size_t kDefinitionAutoAcceptScalarOffset = 0x2A48;
constexpr std::size_t kDefinitionSendOptionsExclusiveOffset = 0x2A4E;
constexpr std::size_t kSendOptionRowStride = 0x7D0;
constexpr std::size_t kSendOptionShownTriggerOffset = 0x00;
constexpr std::size_t kSendOptionValidTriggerOffset = 0xE0;
constexpr std::size_t kSendOptionNumericFlagIdentifierOffset = 0x3A8;
constexpr std::size_t kTargetTypeRegistryDataOffset = 0x00;
constexpr std::size_t kTargetTypeRegistryCountOffset = 0x0C;
constexpr std::size_t kTargetTypeRegistryEntryStride = 0x50;
constexpr std::size_t kTargetTypeRegistryEntryIdentifierOffset = 0x00;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 0x0F;
constexpr std::size_t kMaximumStableKeyBytes = 1'024;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;
constexpr std::int32_t kMaximumTargetTypeEntries = 65'536;
constexpr std::int32_t kMaximumExpirationDays = 100'000;

struct ReplyCharacterInteractionCommandV1 {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t pending_interaction_id = -1;
  std::int32_t reply = 0;
};

static_assert(sizeof(ReplyCharacterInteractionCommandV1) == 0x28);
static_assert(offsetof(ReplyCharacterInteractionCommandV1,
                       pending_interaction_id) == 0x20);
static_assert(offsetof(ReplyCharacterInteractionCommandV1, reply) == 0x24);

struct FailureV1 {
  game::PendingCharacterInteractionContextStatusV1 status =
      game::PendingCharacterInteractionContextStatusV1::unavailable;
  std::string_view reason = "internal_error";
};

struct ObservationV1 {
  void *pending = nullptr;
  void *played_character = nullptr;
  void *definition_pointer = nullptr;
  void *selected_option_data = nullptr;
  void *send_option_rows = nullptr;
  void *target_type_registry = nullptr;
  game::PendingCharacterInteractionDefinitionV1 definition;
  game::PendingCharacterInteractionRolesV1 roles;
  game::PendingCharacterInteractionTargetV1 target;
  game::PendingCharacterInteractionSendOptionsV1 send_options;
  game::PendingCharacterInteractionRoutingV1 routing;
  game::PendingCharacterInteractionDeadlineV1 deadline;
  game::PendingCharacterInteractionBooleanV1 auto_accept;
  game::PendingCharacterInteractionLegalitiesV1 legality;
  game::PendingCharacterInteractionTermsV1 terms;

  friend bool operator==(const ObservationV1 &,
                         const ObservationV1 &) = default;
};

bool GuardedDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) {
    return false;
  }
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

bool ReadBytes(const PendingCharacterInteractionAccessV1 &access,
               const void *address, void *output,
               std::size_t size) noexcept {
  if (access.read_memory != nullptr) {
    return access.read_memory(access.context, address, output, size);
  }
  return GuardedDirectRead(address, output, size);
}

bool CheckedAddress(const void *base, std::size_t offset,
                    const void *&output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() - value) {
    output = nullptr;
    return false;
  }
  output = reinterpret_cast<const void *>(value + offset);
  return true;
}

template <typename Value>
bool ReadValue(const PendingCharacterInteractionAccessV1 &access,
               const void *base, std::size_t offset,
               Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

template <typename Value>
bool ReadSlot(const PendingCharacterInteractionAccessV1 &access,
              const Value *slot, Value &output) noexcept {
  return ReadBytes(access, slot, &output, sizeof(output));
}

bool ValidUtf8(std::string_view value) noexcept {
  const auto *bytes = reinterpret_cast<const unsigned char *>(value.data());
  std::size_t index = 0;
  while (index < value.size()) {
    const auto first = bytes[index];
    if (first <= 0x7F) {
      ++index;
      continue;
    }
    std::size_t trailing = 0;
    std::uint32_t codepoint = 0;
    if (first >= 0xC2 && first <= 0xDF) {
      trailing = 1;
      codepoint = first & 0x1FU;
    } else if (first >= 0xE0 && first <= 0xEF) {
      trailing = 2;
      codepoint = first & 0x0FU;
    } else if (first >= 0xF0 && first <= 0xF4) {
      trailing = 3;
      codepoint = first & 0x07U;
    } else {
      return false;
    }
    if (index + trailing >= value.size()) {
      return false;
    }
    for (std::size_t offset = 1; offset <= trailing; ++offset) {
      const auto continuation = bytes[index + offset];
      if ((continuation & 0xC0U) != 0x80U) {
        return false;
      }
      codepoint = (codepoint << 6U) | (continuation & 0x3FU);
    }
    if ((trailing == 2 && codepoint < 0x800U) ||
        (trailing == 3 && codepoint < 0x10000U) ||
        codepoint > 0x10FFFFU ||
        (codepoint >= 0xD800U && codepoint <= 0xDFFFU)) {
      return false;
    }
    index += trailing + 1;
  }
  return true;
}

bool ReadNativeString(const PendingCharacterInteractionAccessV1 &access,
                      const void *native_string,
                      std::string &output) noexcept {
  output.clear();
  if (native_string == nullptr) {
    return false;
  }
  if (access.read_string != nullptr) {
    if (!access.read_string(access.context, native_string, output)) {
      output.clear();
      return false;
    }
  } else {
    std::size_t size = 0;
    std::size_t capacity = 0;
    if (!ReadValue(access, native_string, kMsvcStringSizeOffset, size) ||
        !ReadValue(access, native_string, kMsvcStringCapacityOffset,
                   capacity) ||
        size == 0 || size > capacity || size > kMaximumStableKeyBytes) {
      return false;
    }
    const void *bytes = native_string;
    if (capacity > kMsvcStringInlineCapacity &&
        (!ReadValue(access, native_string, 0, bytes) || bytes == nullptr)) {
      return false;
    }
    try {
      output.resize(size);
    } catch (...) {
      output.clear();
      return false;
    }
    if (!ReadBytes(access, bytes, output.data(), size)) {
      output.clear();
      return false;
    }
  }
  if (output.empty() || output.size() > kMaximumStableKeyBytes ||
      !ValidUtf8(output) ||
      std::any_of(output.begin(), output.end(), [](unsigned char value) {
        return value == 0 || value < 0x20U;
      })) {
    output.clear();
    return false;
  }
  return true;
}

bool EnvironmentIsExact(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment)
    noexcept {
  if (!environment.exact_build_admitted ||
      environment.pending_storage_slot == nullptr ||
      environment.character_storage_slot == nullptr ||
      environment.expiration_days == nullptr ||
      environment.local_routing == nullptr ||
      environment.reply_validator == nullptr ||
      environment.trigger_evaluator == nullptr ||
      environment.target_type_registry == nullptr ||
      environment.script_identifier_name == nullptr ||
      environment.reply_primary_vtable == 0 ||
      environment.reply_secondary_vtable == 0) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    return true;
  }
  if (environment.module_base == 0) {
    return false;
  }
  const auto base = environment.module_base;
  return reinterpret_cast<std::uintptr_t>(environment.pending_storage_slot) ==
             base + kPendingInteractionStorageSlotV1Rva &&
         reinterpret_cast<std::uintptr_t>(
             environment.character_storage_slot) ==
             base + kPendingInteractionCharacterStorageSlotV1Rva &&
         reinterpret_cast<std::uintptr_t>(environment.expiration_days) ==
             base + kPendingInteractionExpirationDaysV1Rva &&
         reinterpret_cast<std::uintptr_t>(environment.local_routing) ==
             base + kPendingInteractionLocalRoutingV1Rva &&
         reinterpret_cast<std::uintptr_t>(environment.reply_validator) ==
             base + kPendingInteractionReplyValidatorV1Rva &&
         reinterpret_cast<std::uintptr_t>(environment.trigger_evaluator) ==
             base + kPendingInteractionTriggerEvaluatorV1Rva &&
         reinterpret_cast<std::uintptr_t>(environment.target_type_registry) ==
             base + kPendingInteractionTargetTypeRegistryGetterV1Rva &&
         reinterpret_cast<std::uintptr_t>(
             environment.script_identifier_name) ==
             base + kPendingInteractionScriptIdentifierNameV1Rva &&
         environment.reply_primary_vtable ==
             base + kPendingInteractionReplyPrimaryVtableV1Rva &&
         environment.reply_secondary_vtable ==
             base + kPendingInteractionReplySecondaryVtableV1Rva;
}

void SetFailure(game::PendingCharacterInteractionContextV1 &output,
                game::PendingCharacterInteractionContextStatusV1 status,
                std::string_view reason) {
  const auto revision = output.snapshot_revision;
  const auto date_raw = output.date_raw;
  const auto pending_id = output.pending_interaction_id;
  output = {};
  output.snapshot_revision = revision;
  output.date_raw = date_raw;
  output.pending_interaction_id = pending_id;
  output.status = status;
  output.reason.assign(reason);
  auto set_legality = [reason](
                          game::PendingCharacterInteractionLegalityV1 &item) {
    item.status =
        game::PendingCharacterInteractionSemanticStatusV1::unavailable;
    item.allowed = false;
    item.reason.assign(reason);
  };
  set_legality(output.legality.accept);
  set_legality(output.legality.reject);
  set_legality(output.legality.block);
  set_legality(output.legality.acknowledge);
  output.readiness.not_ready_reasons.emplace_back(reason);
}

bool Fail(FailureV1 &failure,
          game::PendingCharacterInteractionContextStatusV1 status,
          std::string_view reason) noexcept {
  failure.status = status;
  failure.reason = reason;
  return false;
}

void *ResolveComponent(
    const PendingCharacterInteractionAccessV1 &access,
    void *const *storage_slot, std::int32_t full_id,
    std::size_t identity_offset, std::string_view storage_failure,
    std::string_view generation_failure, FailureV1 &failure) noexcept {
  void *storage = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadSlot(access, storage_slot, storage) || storage == nullptr ||
      !ReadValue(access, storage, kStorageSlotsOffset, slots) ||
      !ReadValue(access, storage, kStorageCapacityOffset, capacity) ||
      slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentSlots) {
    Fail(failure,
         game::PendingCharacterInteractionContextStatusV1::unavailable,
         storage_failure);
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) {
    Fail(failure,
         game::PendingCharacterInteractionContextStatusV1::unavailable,
         generation_failure);
    return nullptr;
  }
  const auto offset = static_cast<std::size_t>(index) * kStorageSlotStride +
                      kStorageSlotObjectOffset;
  void *object = nullptr;
  std::int32_t observed_id = -1;
  if (!ReadValue(access, slots, offset, object) || object == nullptr ||
      !ReadValue(access, object, identity_offset, observed_id) ||
      observed_id != full_id) {
    Fail(failure,
         game::PendingCharacterInteractionContextStatusV1::unavailable,
         generation_failure);
    return nullptr;
  }
  return object;
}

bool ValidOptionalCharacterId(std::int32_t value) noexcept {
  return value == -1 || value > 0;
}

bool ReadRoles(const PendingCharacterInteractionAccessV1 &access,
               void *pending,
               game::PendingCharacterInteractionRolesV1 &roles,
               FailureV1 &failure) noexcept {
  if (!ReadValue(access, pending, kPendingActorOffset,
                 roles.actor_character_id) ||
      !ReadValue(access, pending, kPendingRecipientOffset,
                 roles.recipient_character_id) ||
      !ReadValue(access, pending, kPendingSecondaryActorOffset,
                 roles.secondary_actor_character_id) ||
      !ReadValue(access, pending, kPendingSecondaryRecipientOffset,
                 roles.secondary_recipient_character_id) ||
      !ReadValue(access, pending, kPendingIntermediaryOffset,
                 roles.intermediary_character_id)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_roles_unavailable");
  }
  if (roles.actor_character_id <= 0 ||
      roles.recipient_character_id <= 0 ||
      !ValidOptionalCharacterId(roles.secondary_actor_character_id) ||
      !ValidOptionalCharacterId(
          roles.secondary_recipient_character_id) ||
      !ValidOptionalCharacterId(roles.intermediary_character_id)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "pending_roles_invalid");
  }
  return true;
}

bool ReadRouting(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access,
    const PendingCharacterInteractionContextRequestV1 &request,
    void *pending, void *played_character,
    const game::PendingCharacterInteractionRolesV1 &roles,
    game::PendingCharacterInteractionRoutingV1 &routing,
    FailureV1 &failure) noexcept {
  std::uint8_t notification = 0;
  if (!ReadValue(access, pending, kPendingRoutingKindOffset, routing.kind) ||
      !ReadValue(access, pending, kPendingAutoAcceptNotificationOffset,
                 notification)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_routing_unavailable");
  }
  if (notification > 1) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "pending_routing_invalid");
  }
  routing.played_character_id = request.played_character_id;
  routing.auto_accept_notification = notification != 0;
  std::int32_t responder_id = -1;
  if (routing.kind == 1) {
    if (roles.intermediary_character_id <= 0) {
      return Fail(failure,
                  game::PendingCharacterInteractionContextStatusV1::invalid,
                  "pending_routing_invalid");
    }
    responder_id = roles.intermediary_character_id;
    routing.current_responder_role = "intermediary";
    routing.reply_execution_channel = "intermediary";
  } else if (routing.kind == 0 || routing.kind == 2) {
    responder_id = roles.recipient_character_id;
    routing.current_responder_role = "recipient";
    routing.reply_execution_channel = "recipient";
  } else if (routing.kind == 3) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_not_routed_to_played_character");
  } else {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "pending_routing_invalid");
  }
  if (responder_id != request.played_character_id) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_not_routed_to_played_character");
  }
  bool local_route = false;
  if (!access.invoke_local_routing(
          access.context, environment.local_routing, pending,
          played_character, local_route)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_routing_unavailable");
  }
  if (!local_route) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_reply_state_unavailable");
  }
  routing.local_route = true;
  return true;
}

bool ReadDefinition(
    const PendingCharacterInteractionAccessV1 &access, void *pending,
    void *&definition_pointer,
    game::PendingCharacterInteractionDefinitionV1 &definition,
    FailureV1 &failure) noexcept {
  const void *key_address = nullptr;
  if (!ReadValue(access, pending, kPendingDefinitionOffset,
                 definition_pointer) ||
      definition_pointer == nullptr ||
      !ReadValue(access, definition_pointer,
                 kDefinitionRuntimeOrdinalOffset,
                 definition.runtime_ordinal) ||
      !ReadValue(access, definition_pointer, kDefinitionKeyHashOffset,
                 definition.deterministic_key_hash) ||
      !CheckedAddress(definition_pointer, kDefinitionCanonicalKeyOffset,
                      key_address) ||
      !ReadNativeString(access, key_address, definition.canonical_key)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_definition_unavailable");
  }
  if (definition.runtime_ordinal < 0) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "pending_definition_invalid");
  }
  return true;
}

bool ReadTargetTypeKey(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access,
    std::uint16_t type_index, void *&registry_pointer,
    std::string &type_key, FailureV1 &failure) noexcept {
  if (!access.invoke_target_type_registry(
          access.context, environment.target_type_registry,
          registry_pointer) ||
      registry_pointer == nullptr) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "target_type_registry_unavailable");
  }
  if (!environment.offline_fixture_function_overrides &&
      reinterpret_cast<std::uintptr_t>(registry_pointer) !=
          environment.module_base + kPendingInteractionTargetTypeRegistryV1Rva) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "target_type_registry_drift");
  }
  void *entries = nullptr;
  std::int32_t count = 0;
  if (!ReadValue(access, registry_pointer,
                 kTargetTypeRegistryDataOffset, entries) ||
      !ReadValue(access, registry_pointer,
                 kTargetTypeRegistryCountOffset, count) ||
      entries == nullptr || count <= 0 ||
      count > kMaximumTargetTypeEntries) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "target_type_registry_unavailable");
  }
  if (type_index >= static_cast<std::uint32_t>(count)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "target_type_index_out_of_bounds");
  }
  const auto entry_offset =
      static_cast<std::size_t>(type_index) * kTargetTypeRegistryEntryStride;
  std::int32_t identifier = -1;
  if (!ReadValue(access, entries,
                 entry_offset + kTargetTypeRegistryEntryIdentifierOffset,
                 identifier) ||
      identifier < 0) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "target_type_registry_drift");
  }
  const std::string *native_name = nullptr;
  if (!access.invoke_script_identifier_name(
          access.context, environment.script_identifier_name, identifier,
          native_name) ||
      native_name == nullptr ||
      !ReadNativeString(access, native_name, type_key)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "target_type_key_unavailable");
  }
  return true;
}

bool ReadTarget(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access, void *pending,
    game::PendingCharacterInteractionTargetV1 &target,
    void *&target_type_registry, FailureV1 &failure) noexcept {
  if (!ReadValue(access, pending, kPendingTargetEnvelopeOffset,
                 target.raw_envelope)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_target_unavailable");
  }
  std::memcpy(&target.raw_type_index, target.raw_envelope.data(),
              sizeof(target.raw_type_index));
  target.present = target.raw_type_index != 0;
  if (!target.present) {
    target.type_key_status =
        game::PendingCharacterInteractionSemanticStatusV1::absent;
    target.typed_identity_status =
        game::PendingCharacterInteractionSemanticStatusV1::absent;
    return true;
  }
  std::string type_key;
  if (!ReadTargetTypeKey(environment, access, target.raw_type_index,
                         target_type_registry, type_key, failure)) {
    return false;
  }
  target.type_key_status =
      game::PendingCharacterInteractionSemanticStatusV1::available;
  target.type_key = std::move(type_key);
  target.typed_identity_status =
      game::PendingCharacterInteractionSemanticStatusV1::unavailable;
  target.typed_identity_reason =
      "generic_scope_payload_identity_not_closed";
  return true;
}

bool InvokeTrigger(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access, void *trigger,
    const void *scope, bool &output, FailureV1 &failure,
    std::string_view reason) noexcept {
  if (!access.invoke_trigger_evaluator(
          access.context, environment.trigger_evaluator, trigger, scope,
          output)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                reason);
  }
  return true;
}

bool ReadSendOptions(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access, void *pending,
    void *definition, void *&selected_data, void *&rows_pointer,
    game::PendingCharacterInteractionSendOptionsV1 &send_options,
    FailureV1 &failure) noexcept {
  std::int32_t selected_capacity = 0;
  std::uint8_t exclusive = 0;
  if (!ReadValue(access, definition, kDefinitionSendOptionRowsOffset,
                 rows_pointer) ||
      !ReadValue(access, definition, kDefinitionSendOptionCountOffset,
                 send_options.definition_count) ||
      !ReadValue(access, definition, kDefinitionSendOptionsExclusiveOffset,
                 exclusive) ||
      !ReadValue(access, pending, kPendingSelectedOptionsDataOffset,
                 selected_data) ||
      !ReadValue(access, pending, kPendingSelectedOptionsCapacityOffset,
                 selected_capacity) ||
      !ReadValue(access, pending, kPendingSelectedOptionsCountOffset,
                 send_options.context_count)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "send_options_unavailable");
  }
  if (exclusive > 1 || send_options.definition_count < 0 ||
      send_options.context_count < 0 || selected_capacity < 0 ||
      send_options.definition_count > kPendingInteractionMaximumSendOptionsV1 ||
      send_options.context_count > kPendingInteractionMaximumSendOptionsV1 ||
      selected_capacity > kPendingInteractionMaximumSendOptionsV1) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "send_option_count_invalid");
  }
  if (send_options.definition_count != send_options.context_count) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "send_option_count_mismatch");
  }
  if (selected_capacity < send_options.context_count ||
      (send_options.definition_count > 0 &&
       (rows_pointer == nullptr || selected_data == nullptr))) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "send_option_storage_invalid");
  }
  send_options.exclusive = exclusive != 0;
  try {
    send_options.rows.reserve(
        static_cast<std::size_t>(send_options.definition_count));
  } catch (...) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "internal_error");
  }
  std::int32_t selected_count = 0;
  const void *scope = nullptr;
  if (!CheckedAddress(pending, kPendingPrimaryScopeOffset, scope)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "send_options_unavailable");
  }
  for (std::int32_t index = 0; index < send_options.definition_count;
       ++index) {
    const auto row_offset =
        static_cast<std::size_t>(index) * kSendOptionRowStride;
    const void *row = nullptr;
    std::uint8_t selected = 0;
    game::PendingCharacterInteractionSendOptionRowV1 item{};
    item.native_index = index;
    if (!CheckedAddress(rows_pointer, row_offset, row) ||
        !ReadValue(access, selected_data,
                   static_cast<std::size_t>(index), selected) ||
        !ReadValue(access, row, kSendOptionNumericFlagIdentifierOffset,
                   item.numeric_flag_identifier)) {
      return Fail(failure,
                  game::PendingCharacterInteractionContextStatusV1::unavailable,
                  "send_options_unavailable");
    }
    if (selected > 1 || item.numeric_flag_identifier < 0) {
      return Fail(failure,
                  game::PendingCharacterInteractionContextStatusV1::invalid,
                  "send_option_row_invalid");
    }
    item.selected = selected == 1;
    selected_count += item.selected ? 1 : 0;
    const void *valid_trigger = nullptr;
    const void *shown_trigger = nullptr;
    if (!CheckedAddress(row, kSendOptionValidTriggerOffset,
                        valid_trigger) ||
        !CheckedAddress(row, kSendOptionShownTriggerOffset,
                        shown_trigger) ||
        !InvokeTrigger(environment, access,
                       const_cast<void *>(valid_trigger), scope,
                       item.is_valid, failure,
                       "send_option_evaluation_unavailable")) {
      return false;
    }
    // Exact RVA 0x2C408B0 short-circuits is_shown when is_valid is false.
    // Publish the effective shown result, rather than evaluating a trigger
    // the engine deliberately did not reach.
    if (item.is_valid &&
        !InvokeTrigger(environment, access,
                       const_cast<void *>(shown_trigger), scope,
                       item.is_shown, failure,
                       "send_option_evaluation_unavailable")) {
      return false;
    }
    item.canonical_flag_status =
        game::PendingCharacterInteractionSemanticStatusV1::unavailable;
    item.canonical_flag_reason =
        "numeric_flag_identifier_string_mapping_not_closed";
    send_options.rows.push_back(std::move(item));
  }
  if (send_options.exclusive && selected_count > 1) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "exclusive_send_option_selection_invalid");
  }
  return true;
}

bool ReadDeadline(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access, void *pending,
    game::PendingCharacterInteractionDeadlineV1 &deadline,
    FailureV1 &failure) noexcept {
  if (!ReadValue(access, pending, kPendingAgeDaysOffset,
                 deadline.age_days) ||
      !ReadSlot(access, environment.expiration_days,
                deadline.expiration_days)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_deadline_unavailable");
  }
  if (deadline.age_days < 0 || deadline.expiration_days <= 0 ||
      deadline.expiration_days > kMaximumExpirationDays) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "pending_deadline_invalid");
  }
  deadline.remaining_days = std::max(
      0, deadline.expiration_days - deadline.age_days);
  deadline.expiry_boundary_status =
      deadline.age_days >= deadline.expiration_days
          ? "at_or_past_daily_expiry_queue_threshold"
          : "not_reached";
  return true;
}

bool ReadAutoAccept(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access, void *pending,
    void *definition,
    game::PendingCharacterInteractionBooleanV1 &auto_accept,
    FailureV1 &failure) noexcept {
  void *trigger = nullptr;
  if (!ReadValue(access, definition, kDefinitionAutoAcceptTriggerOffset,
                 trigger)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "auto_accept_unavailable");
  }
  bool value = false;
  if (trigger != nullptr) {
    const void *scope = nullptr;
    if (!CheckedAddress(pending, kPendingPrimaryScopeOffset, scope) ||
        !InvokeTrigger(environment, access, trigger, scope, value, failure,
                       "auto_accept_unavailable")) {
      return false;
    }
  } else {
    std::uint8_t scalar = 0;
    if (!ReadValue(access, definition,
                   kDefinitionAutoAcceptScalarOffset, scalar)) {
      return Fail(
          failure,
          game::PendingCharacterInteractionContextStatusV1::unavailable,
          "auto_accept_unavailable");
    }
    if (scalar > 1) {
      return Fail(failure,
                  game::PendingCharacterInteractionContextStatusV1::invalid,
                  "auto_accept_invalid");
    }
    value = scalar != 0;
  }
  auto_accept.status =
      game::PendingCharacterInteractionSemanticStatusV1::available;
  auto_accept.value = value;
  auto_accept.reason.clear();
  return true;
}

void SetAvailableLegality(
    game::PendingCharacterInteractionLegalityV1 &legality, bool allowed,
    std::string_view false_reason) {
  legality.status =
      game::PendingCharacterInteractionSemanticStatusV1::available;
  legality.allowed = allowed;
  legality.reason.assign(allowed ? std::string_view{} : false_reason);
}

bool ValidateReply(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access,
    std::int32_t pending_id, std::int32_t reply, bool &output,
    FailureV1 &failure) noexcept {
  ReplyCharacterInteractionCommandV1 command{};
  command.primary_vtable = environment.reply_primary_vtable;
  command.secondary_vtable = environment.reply_secondary_vtable;
  command.pending_interaction_id = pending_id;
  command.reply = reply;
  if (!access.invoke_reply_validator(
          access.context, environment.reply_validator, &command, output)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "reply_legality_unavailable");
  }
  return true;
}

bool ReadLegalities(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access,
    const PendingCharacterInteractionContextRequestV1 &request,
    const game::PendingCharacterInteractionRolesV1 &roles,
    const game::PendingCharacterInteractionRoutingV1 &routing,
    const game::PendingCharacterInteractionBooleanV1 &auto_accept,
    game::PendingCharacterInteractionLegalitiesV1 &legalities,
    FailureV1 &failure) noexcept {
  if (routing.auto_accept_notification) {
    SetAvailableLegality(legalities.accept, false,
                         "auto_accept_notification_channel");
    SetAvailableLegality(legalities.reject, false,
                         "auto_accept_notification_channel");
    SetAvailableLegality(legalities.block, false,
                         "auto_accept_notification_channel");
    SetAvailableLegality(legalities.acknowledge, true, {});
    return true;
  }
  bool accept = false;
  bool reject = false;
  bool block = false;
  if (!ValidateReply(environment, access, request.pending_interaction_id,
                     0, accept, failure) ||
      !ValidateReply(environment, access, request.pending_interaction_id,
                     1, reject, failure) ||
      !ValidateReply(environment, access, request.pending_interaction_id,
                     2, block, failure)) {
    return false;
  }
  if ((auto_accept.value ||
       roles.actor_character_id == roles.recipient_character_id) &&
      (reject || block)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::invalid,
                "reply_validator_semantic_mismatch");
  }
  SetAvailableLegality(legalities.accept, accept,
                       "native_reply_validator_rejected");
  SetAvailableLegality(legalities.reject, reject,
                       "native_reply_validator_rejected");
  SetAvailableLegality(legalities.block, block,
                       "native_reply_validator_rejected");
  SetAvailableLegality(legalities.acknowledge, false,
                       "normal_reply_channel");
  return true;
}

void InitializeUnavailableTerms(
    game::PendingCharacterInteractionTermsV1 &terms) {
  terms.structured_costs.reason = "structured_costs_unavailable";
  terms.structured_exchanges.reason = "structured_exchanges_unavailable";
  terms.structured_effect_preview.reason =
      "structured_effect_preview_unavailable";
  terms.recipient_ai_acceptance_score.reason =
      "recipient_ai_acceptance_score_unavailable";
  terms.recipient_ai_final_decision.reason =
      "recipient_ai_final_decision_unavailable";
}

bool ReadObservation(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access,
    const PendingCharacterInteractionContextRequestV1 &request,
    ObservationV1 &output, FailureV1 &failure) noexcept {
  output = {};
  output.pending = ResolveComponent(
      access, environment.pending_storage_slot,
      request.pending_interaction_id, kComponentIdentityOffset,
      "pending_storage_unavailable", "pending_generation_mismatch",
      failure);
  if (output.pending == nullptr) {
    return false;
  }
  output.played_character = ResolveComponent(
      access, environment.character_storage_slot,
      request.played_character_id, kCharacterIdentityOffset,
      "character_storage_unavailable",
      "played_character_generation_mismatch", failure);
  if (output.played_character == nullptr ||
      !ReadRoles(access, output.pending, output.roles, failure) ||
      !ReadRouting(environment, access, request, output.pending,
                   output.played_character, output.roles, output.routing,
                   failure) ||
      !ReadDefinition(access, output.pending, output.definition_pointer,
                      output.definition, failure) ||
      !ReadTarget(environment, access, output.pending, output.target,
                  output.target_type_registry, failure) ||
      !ReadSendOptions(environment, access, output.pending,
                       output.definition_pointer, output.selected_option_data,
                       output.send_option_rows, output.send_options,
                       failure) ||
      !ReadDeadline(environment, access, output.pending, output.deadline,
                    failure) ||
      !ReadAutoAccept(environment, access, output.pending,
                      output.definition_pointer, output.auto_accept,
                      failure) ||
      !ReadLegalities(environment, access, request, output.roles,
                      output.routing, output.auto_accept, output.legality,
                      failure)) {
    return false;
  }
  void *special_data = nullptr;
  if (!ReadValue(access, output.pending, kPendingSpecialDataOffset,
                 special_data)) {
    return Fail(failure,
                game::PendingCharacterInteractionContextStatusV1::unavailable,
                "pending_terms_unavailable");
  }
  output.terms.special_data_present = special_data != nullptr;
  InitializeUnavailableTerms(output.terms);
  return true;
}

game::ReadPendingCharacterInteractionContextResultV1 ResultForStatus(
    game::PendingCharacterInteractionContextStatusV1 status) noexcept {
  switch (status) {
  case game::PendingCharacterInteractionContextStatusV1::available:
    return game::ReadPendingCharacterInteractionContextResultV1::available;
  case game::PendingCharacterInteractionContextStatusV1::invalid:
    return game::ReadPendingCharacterInteractionContextResultV1::invalid;
  case game::PendingCharacterInteractionContextStatusV1::unavailable:
  default:
    return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
  }
}

} // namespace

bool InvokePendingCharacterInteractionLocalRoutingDirectV1(
    void *, NativePendingInteractionLocalRoutingV1 function,
    void *pending_interaction, void *played_character,
    bool &output) noexcept {
  output = false;
  if (function == nullptr || pending_interaction == nullptr ||
      played_character == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    output = function(pending_interaction, played_character);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = false;
    return false;
  }
#else
  output = function(pending_interaction, played_character);
  return true;
#endif
}

bool InvokePendingCharacterInteractionReplyValidatorDirectV1(
    void *, NativePendingInteractionReplyValidatorV1 function,
    void *reply_command, bool &output) noexcept {
  output = false;
  if (function == nullptr || reply_command == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    output = function(reply_command);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = false;
    return false;
  }
#else
  output = function(reply_command);
  return true;
#endif
}

bool InvokePendingCharacterInteractionTriggerEvaluatorDirectV1(
    void *, NativePendingInteractionTriggerEvaluatorV1 function,
    void *trigger, const void *event_target_scope,
    bool &output) noexcept {
  output = false;
  if (function == nullptr || trigger == nullptr ||
      event_target_scope == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    output = function(trigger, event_target_scope);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = false;
    return false;
  }
#else
  output = function(trigger, event_target_scope);
  return true;
#endif
}

bool InvokePendingCharacterInteractionTargetTypeRegistryDirectV1(
    void *, NativePendingInteractionTargetTypeRegistryGetterV1 function,
    void *&output) noexcept {
  output = nullptr;
  if (function == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    output = function();
    return output != nullptr;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = function();
  return output != nullptr;
#endif
}

bool InvokePendingCharacterInteractionScriptIdentifierNameDirectV1(
    void *, NativePendingInteractionScriptIdentifierNameV1 function,
    std::int32_t identifier, const std::string *&output) noexcept {
  output = nullptr;
  if (function == nullptr || identifier < 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    output = function(identifier);
    return output != nullptr;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = function(identifier);
  return output != nullptr;
#endif
}

PendingCharacterInteractionNativeEnvironmentV1
BindPendingCharacterInteractionNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  PendingCharacterInteractionNativeEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  if (module_base == 0 || !exact_build_admitted) {
    return output;
  }
  output.pending_storage_slot = reinterpret_cast<void **>(
      module_base + kPendingInteractionStorageSlotV1Rva);
  output.character_storage_slot = reinterpret_cast<void **>(
      module_base + kPendingInteractionCharacterStorageSlotV1Rva);
  output.expiration_days = reinterpret_cast<const std::int32_t *>(
      module_base + kPendingInteractionExpirationDaysV1Rva);
  output.local_routing = reinterpret_cast<
      NativePendingInteractionLocalRoutingV1>(
      module_base + kPendingInteractionLocalRoutingV1Rva);
  output.reply_validator = reinterpret_cast<
      NativePendingInteractionReplyValidatorV1>(
      module_base + kPendingInteractionReplyValidatorV1Rva);
  output.trigger_evaluator = reinterpret_cast<
      NativePendingInteractionTriggerEvaluatorV1>(
      module_base + kPendingInteractionTriggerEvaluatorV1Rva);
  output.target_type_registry = reinterpret_cast<
      NativePendingInteractionTargetTypeRegistryGetterV1>(
      module_base + kPendingInteractionTargetTypeRegistryGetterV1Rva);
  output.script_identifier_name = reinterpret_cast<
      NativePendingInteractionScriptIdentifierNameV1>(
      module_base + kPendingInteractionScriptIdentifierNameV1Rva);
  output.reply_primary_vtable =
      module_base + kPendingInteractionReplyPrimaryVtableV1Rva;
  output.reply_secondary_vtable =
      module_base + kPendingInteractionReplySecondaryVtableV1Rva;
  return output;
}

game::ReadPendingCharacterInteractionContextResultV1
ReadPendingCharacterInteractionContextV1(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access,
    const PendingCharacterInteractionContextRequestV1 &request,
    game::PendingCharacterInteractionContextV1 &output) noexcept {
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  output.pending_interaction_id = request.pending_interaction_id;
  try {
    if (request.expected_snapshot_revision == 0 ||
        access.capture_frame == nullptr ||
        access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context) ||
        access.invoke_local_routing == nullptr ||
        access.invoke_reply_validator == nullptr ||
        access.invoke_trigger_evaluator == nullptr ||
        access.invoke_target_type_registry == nullptr ||
        access.invoke_script_identifier_name == nullptr) {
      SetFailure(
          output,
          game::PendingCharacterInteractionContextStatusV1::unavailable,
          "requires_application_main");
      return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
    }
    game::PendingCharacterInteractionFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetFailure(
          output,
          game::PendingCharacterInteractionContextStatusV1::unavailable,
          "state_changed");
      return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
    }
    output.snapshot_revision = before.snapshot_revision;
    output.date_raw = before.date_raw;
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetFailure(
          output,
          game::PendingCharacterInteractionContextStatusV1::unavailable,
          "state_changed");
      return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
    }
    if (!before.paused) {
      SetFailure(
          output,
          game::PendingCharacterInteractionContextStatusV1::unavailable,
          "requires_paused");
      return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
    }
    if (!before.map_ready) {
      SetFailure(
          output,
          game::PendingCharacterInteractionContextStatusV1::unavailable,
          "map_not_ready");
      return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
    }
    if (!EnvironmentIsExact(environment)) {
      SetFailure(
          output,
          game::PendingCharacterInteractionContextStatusV1::unavailable,
          "unsupported_build");
      return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
    }
    if (request.pending_interaction_id <= 0) {
      SetFailure(output,
                 game::PendingCharacterInteractionContextStatusV1::invalid,
                 "invalid_pending_interaction_id");
      return game::ReadPendingCharacterInteractionContextResultV1::invalid;
    }
    if (request.played_character_id <= 0) {
      SetFailure(output,
                 game::PendingCharacterInteractionContextStatusV1::invalid,
                 "invalid_played_character_id");
      return game::ReadPendingCharacterInteractionContextResultV1::invalid;
    }

    ObservationV1 first{};
    ObservationV1 second{};
    FailureV1 failure{};
    if (!ReadObservation(environment, access, request, first, failure)) {
      SetFailure(output, failure.status, failure.reason);
      return ResultForStatus(failure.status);
    }
    failure = {};
    if (!ReadObservation(environment, access, request, second, failure)) {
      SetFailure(output, failure.status, failure.reason);
      return ResultForStatus(failure.status);
    }
    game::PendingCharacterInteractionFrameV1 after{};
    if (!access.capture_frame(access.context, after) || after != before ||
        second != first) {
      SetFailure(
          output,
          game::PendingCharacterInteractionContextStatusV1::unavailable,
          "state_changed");
      return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
    }

    output.status =
        game::PendingCharacterInteractionContextStatusV1::available;
    output.reason.clear();
    output.definition = std::move(first.definition);
    output.roles = std::move(first.roles);
    output.target = std::move(first.target);
    output.send_options = std::move(first.send_options);
    output.routing = std::move(first.routing);
    output.deadline = std::move(first.deadline);
    output.auto_accept = std::move(first.auto_accept);
    output.legality = std::move(first.legality);
    output.terms = std::move(first.terms);
    output.readiness.stable_definition_ready = true;
    output.readiness.roles_ready = true;
    output.readiness.target_type_key_ready = true;
    output.readiness.target_typed_identity_ready =
        !output.target->present;
    output.readiness.send_options_ready = true;
    output.readiness.routing_ready = true;
    output.readiness.deadline_ready = true;
    output.readiness.auto_accept_ready = true;
    output.readiness.reply_legality_ready = true;
    output.readiness.structured_terms_ready = false;
    output.readiness.same_frame_ready = true;
    output.readiness.interaction_semantic_decision_ready = false;
    if (output.target->present) {
      output.readiness.not_ready_reasons.push_back(
          "target_generic_scope_payload_identity_not_closed");
    }
    output.readiness.not_ready_reasons.push_back(
        "structured_costs_unavailable");
    output.readiness.not_ready_reasons.push_back(
        "structured_exchanges_unavailable");
    output.readiness.not_ready_reasons.push_back(
        "structured_effect_preview_unavailable");
    return game::ReadPendingCharacterInteractionContextResultV1::available;
  } catch (...) {
    SetFailure(
        output,
        game::PendingCharacterInteractionContextStatusV1::unavailable,
        "internal_error");
    return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
