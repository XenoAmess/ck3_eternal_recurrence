#pragma once

#include "xar_bridge/pending_character_interaction_context_v1.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view
    kPendingCharacterInteractionContextV1Capability =
        "game.command.query-pending-character-interaction-context-v1";
inline constexpr std::string_view kPendingCharacterInteractionContextV1Step =
    "query-pending-character-interaction-context-v1";
inline constexpr std::string_view
    kPendingCharacterInteractionContextV1GameVersion = "1.20.0.2";
inline constexpr std::string_view
    kPendingCharacterInteractionContextV1ExecutableSha256 =
        "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::string_view
    kPendingCharacterInteractionContextV1BackendId =
        "ck3-1.20.0.2-native-pending-character-interaction-context-v1";
inline constexpr std::string_view
    kPendingCharacterInteractionSpecialWarBindingV1Contract =
        "pending-character-interaction-special-war-binding-v1";

inline constexpr std::uintptr_t kPendingInteractionStorageSlotV1Rva = 0x5D1EC80;
inline constexpr std::uintptr_t kPendingInteractionCharacterStorageSlotV1Rva =
    0x5C67568;
inline constexpr std::uintptr_t kPendingInteractionExpirationDaysV1Rva =
    0x5C68CFC;
inline constexpr std::uintptr_t kPendingInteractionLocalRoutingV1Rva =
    0x136D1B0;
inline constexpr std::uintptr_t kPendingInteractionReplyValidatorV1Rva =
    0x2968490;
inline constexpr std::uintptr_t kPendingInteractionTriggerEvaluatorV1Rva =
    0x372DF30;
inline constexpr std::uintptr_t kPendingInteractionCostEvaluatorV1Rva =
    0x310CEE0;
inline constexpr std::uintptr_t kPendingInteractionCommonWarRelationV1Rva =
    0x28BC270;
inline constexpr std::uintptr_t
    kPendingInteractionTargetTypeRegistryGetterV1Rva = 0x3795A80;
inline constexpr std::uintptr_t kPendingInteractionTargetTypeRegistryV1Rva =
    0x54F2AF0;
inline constexpr std::uintptr_t kPendingInteractionScriptIdentifierNameV1Rva =
    0x3F4F900;
inline constexpr std::uintptr_t kPendingInteractionReplyPrimaryVtableV1Rva =
    0x448BC18;
inline constexpr std::uintptr_t kPendingInteractionReplySecondaryVtableV1Rva =
    0x448BBE8;
inline constexpr std::uintptr_t
    kPendingInteractionWarVictorySpecialVtableV1Rva = 0x46C3AA0;
inline constexpr std::uintptr_t
    kPendingInteractionWarWhitePeaceSpecialVtableV1Rva = 0x46C3B10;
inline constexpr std::uintptr_t kPendingInteractionWarDefeatSpecialVtableV1Rva =
    0x46C3B80;
inline constexpr std::int32_t kPendingInteractionMaximumSendOptionsV1 = 256;

#if defined(_MSC_VER)
#define XAR_PENDING_INTERACTION_FASTCALL __fastcall
#else
#define XAR_PENDING_INTERACTION_FASTCALL
#endif

using NativePendingInteractionLocalRoutingV1 =
    bool(XAR_PENDING_INTERACTION_FASTCALL *)(void *pending_interaction,
                                             void *played_character);
using NativePendingInteractionReplyValidatorV1 =
    bool(XAR_PENDING_INTERACTION_FASTCALL *)(void *reply_command);
using NativePendingInteractionTriggerEvaluatorV1 =
    bool(XAR_PENDING_INTERACTION_FASTCALL *)(void *trigger,
                                             const void *event_target_scope);
using NativePendingInteractionCostEvaluatorV1 =
    void(XAR_PENDING_INTERACTION_FASTCALL *)(const void *compiled_cost_block,
                                             const void *event_target_scope,
                                             std::int64_t *out10);
using NativePendingInteractionCommonWarRelationV1 =
    void *(XAR_PENDING_INTERACTION_FASTCALL *)(void *actor_character,
                                               void *recipient_character);
using NativePendingInteractionTargetTypeRegistryGetterV1 =
    void *(XAR_PENDING_INTERACTION_FASTCALL *)();
using NativePendingInteractionScriptIdentifierNameV1 = const std::string *(
    XAR_PENDING_INTERACTION_FASTCALL *)(std::int32_t identifier);

#undef XAR_PENDING_INTERACTION_FASTCALL

struct PendingCharacterInteractionNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  void **pending_storage_slot = nullptr;
  void **character_storage_slot = nullptr;
  const std::int32_t *expiration_days = nullptr;
  NativePendingInteractionLocalRoutingV1 local_routing = nullptr;
  NativePendingInteractionReplyValidatorV1 reply_validator = nullptr;
  NativePendingInteractionTriggerEvaluatorV1 trigger_evaluator = nullptr;
  NativePendingInteractionCostEvaluatorV1 cost_evaluator = nullptr;
  NativePendingInteractionCommonWarRelationV1 common_war_relation = nullptr;
  NativePendingInteractionTargetTypeRegistryGetterV1 target_type_registry =
      nullptr;
  NativePendingInteractionScriptIdentifierNameV1 script_identifier_name =
      nullptr;
  std::uintptr_t reply_primary_vtable = 0;
  std::uintptr_t reply_secondary_vtable = 0;
  std::uintptr_t war_victory_special_vtable = 0;
  std::uintptr_t war_white_peace_special_vtable = 0;
  std::uintptr_t war_defeat_special_vtable = 0;
};

using CapturePendingCharacterInteractionFrameV1 = bool (*)(
    void *context, game::PendingCharacterInteractionFrameV1 &output) noexcept;
using IsPendingCharacterInteractionMainThreadV1 =
    bool (*)(void *context) noexcept;
using ReadPendingCharacterInteractionMemoryV1 =
    bool (*)(void *context, const void *address, void *output,
             std::size_t size) noexcept;
using ReadPendingCharacterInteractionStringV1 = bool (*)(
    void *context, const void *native_string, std::string &output) noexcept;
using InvokePendingCharacterInteractionLocalRoutingV1 = bool (*)(
    void *context, NativePendingInteractionLocalRoutingV1 function,
    void *pending_interaction, void *played_character, bool &output) noexcept;
using InvokePendingCharacterInteractionReplyValidatorV1 =
    bool (*)(void *context, NativePendingInteractionReplyValidatorV1 function,
             void *reply_command, bool &output) noexcept;
using InvokePendingCharacterInteractionTriggerEvaluatorV1 = bool (*)(
    void *context, NativePendingInteractionTriggerEvaluatorV1 function,
    void *trigger, const void *event_target_scope, bool &output) noexcept;
using InvokePendingCharacterInteractionCostEvaluatorV1 =
    bool (*)(void *context, NativePendingInteractionCostEvaluatorV1 function,
             const void *compiled_cost_block, const void *event_target_scope,
             std::array<std::int64_t,
                        game::kPendingCharacterInteractionCostResourceCountV1>
                 &output) noexcept;
using InvokePendingCharacterInteractionCommonWarRelationV1 = bool (*)(
    void *context, NativePendingInteractionCommonWarRelationV1 function,
    void *actor_character, void *recipient_character, void *&output) noexcept;
using ResolvePendingCharacterInteractionActiveWarAccessV1 =
    bool (*)(void *context, std::int32_t war_id, void *&output) noexcept;
using InvokePendingCharacterInteractionTargetTypeRegistryV1 = bool (*)(
    void *context, NativePendingInteractionTargetTypeRegistryGetterV1 function,
    void *&output) noexcept;
using InvokePendingCharacterInteractionScriptIdentifierNameV1 = bool (*)(
    void *context, NativePendingInteractionScriptIdentifierNameV1 function,
    std::int32_t identifier, const std::string *&output) noexcept;

using ReadPendingRansomFlagIdentifierV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::string_view key,
    std::int32_t &identifier) noexcept;
using ReadPendingRansomNamedGoldV1 = bool (*)(
    void *context, std::uintptr_t module_base, const void *borrowed_scope,
    std::int32_t actor_id, std::int32_t jailer_id, std::int32_t prisoner_id,
    std::int64_t &gold_raw) noexcept;

struct PendingCharacterInteractionAccessV1 {
  void *context = nullptr;
  CapturePendingCharacterInteractionFrameV1 capture_frame = nullptr;
  IsPendingCharacterInteractionMainThreadV1 is_main_thread = nullptr;
  ReadPendingCharacterInteractionMemoryV1 read_memory = nullptr;
  ReadPendingCharacterInteractionStringV1 read_string = nullptr;
  InvokePendingCharacterInteractionLocalRoutingV1 invoke_local_routing =
      nullptr;
  InvokePendingCharacterInteractionReplyValidatorV1 invoke_reply_validator =
      nullptr;
  InvokePendingCharacterInteractionTriggerEvaluatorV1 invoke_trigger_evaluator =
      nullptr;
  InvokePendingCharacterInteractionCostEvaluatorV1 invoke_cost_evaluator =
      nullptr;
  InvokePendingCharacterInteractionCommonWarRelationV1
      invoke_common_war_relation = nullptr;
  ResolvePendingCharacterInteractionActiveWarAccessV1 resolve_active_war =
      nullptr;
  InvokePendingCharacterInteractionTargetTypeRegistryV1
      invoke_target_type_registry = nullptr;
  InvokePendingCharacterInteractionScriptIdentifierNameV1
      invoke_script_identifier_name = nullptr;
  ReadPendingRansomFlagIdentifierV1 read_ransom_flag_identifier = nullptr;
  ReadPendingRansomNamedGoldV1 read_ransom_named_gold = nullptr;
  ReadPendingRansomNamedGoldV1 read_ransom_named_current_gold = nullptr;
};

struct PendingCharacterInteractionContextRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t pending_interaction_id = -1;
  std::int32_t played_character_id = -1;
};

// Production mailbox wrappers may delegate to these guarded, read-only native
// invokers after checking the executing slot and application-main identity.
bool InvokePendingCharacterInteractionLocalRoutingDirectV1(
    void *context, NativePendingInteractionLocalRoutingV1 function,
    void *pending_interaction, void *played_character, bool &output) noexcept;
bool InvokePendingCharacterInteractionReplyValidatorDirectV1(
    void *context, NativePendingInteractionReplyValidatorV1 function,
    void *reply_command, bool &output) noexcept;
bool InvokePendingCharacterInteractionTriggerEvaluatorDirectV1(
    void *context, NativePendingInteractionTriggerEvaluatorV1 function,
    void *trigger, const void *event_target_scope, bool &output) noexcept;
bool InvokePendingCharacterInteractionCostEvaluatorDirectV1(
    void *context, NativePendingInteractionCostEvaluatorV1 function,
    const void *compiled_cost_block, const void *event_target_scope,
    std::array<std::int64_t,
               game::kPendingCharacterInteractionCostResourceCountV1>
        &output) noexcept;
bool InvokePendingCharacterInteractionCommonWarRelationDirectV1(
    void *context, NativePendingInteractionCommonWarRelationV1 function,
    void *actor_character, void *recipient_character, void *&output) noexcept;
bool InvokePendingCharacterInteractionTargetTypeRegistryDirectV1(
    void *context, NativePendingInteractionTargetTypeRegistryGetterV1 function,
    void *&output) noexcept;
bool InvokePendingCharacterInteractionScriptIdentifierNameDirectV1(
    void *context, NativePendingInteractionScriptIdentifierNameV1 function,
    std::int32_t identifier, const std::string *&output) noexcept;

PendingCharacterInteractionNativeEnvironmentV1
BindPendingCharacterInteractionNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadPendingCharacterInteractionContextResultV1
ReadPendingCharacterInteractionContextV1(
    const PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const PendingCharacterInteractionAccessV1 &access,
    const PendingCharacterInteractionContextRequestV1 &request,
    game::PendingCharacterInteractionContextV1 &output) noexcept;

std::string SerializePendingCharacterInteractionContextV1(
    const game::PendingCharacterInteractionContextV1 &context);

} // namespace xar::ck3_12002
