#pragma once

#include "xar_bridge/game_contract.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class PendingCharacterInteractionContextStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
  invalid = 2,
};

enum class PendingCharacterInteractionSemanticStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
  absent = 2,
};

struct PendingCharacterInteractionDefinitionV1 {
  std::string canonical_key;
  std::uint32_t deterministic_key_hash = 0;
  std::int32_t runtime_ordinal = -1;

  friend bool
  operator==(const PendingCharacterInteractionDefinitionV1 &,
             const PendingCharacterInteractionDefinitionV1 &) = default;
};

struct PendingCharacterInteractionRolesV1 {
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t secondary_actor_character_id = -1;
  std::int32_t secondary_recipient_character_id = -1;
  std::int32_t intermediary_character_id = -1;

  friend bool operator==(const PendingCharacterInteractionRolesV1 &,
                         const PendingCharacterInteractionRolesV1 &) = default;
};

struct PendingCharacterInteractionTargetV1 {
  bool present = false;
  std::uint16_t raw_type_index = 0;
  std::array<std::uint8_t, 16> raw_envelope{};
  PendingCharacterInteractionSemanticStatusV1 type_key_status =
      PendingCharacterInteractionSemanticStatusV1::absent;
  std::optional<std::string> type_key;
  std::string type_key_reason;
  PendingCharacterInteractionSemanticStatusV1 typed_identity_status =
      PendingCharacterInteractionSemanticStatusV1::absent;
  std::optional<std::string> typed_identity;
  std::string typed_identity_reason;

  friend bool operator==(const PendingCharacterInteractionTargetV1 &,
                         const PendingCharacterInteractionTargetV1 &) = default;
};

struct PendingCharacterInteractionSendOptionRowV1 {
  std::int32_t native_index = -1;
  std::int32_t numeric_flag_identifier = -1;
  bool selected = false;
  bool is_shown = false;
  bool is_valid = false;
  PendingCharacterInteractionSemanticStatusV1 canonical_flag_status =
      PendingCharacterInteractionSemanticStatusV1::unavailable;
  std::optional<std::string> canonical_flag_key;
  std::string canonical_flag_reason;

  friend bool
  operator==(const PendingCharacterInteractionSendOptionRowV1 &,
             const PendingCharacterInteractionSendOptionRowV1 &) = default;
};

struct PendingCharacterInteractionSendOptionsV1 {
  bool exclusive = false;
  std::int32_t definition_count = 0;
  std::int32_t context_count = 0;
  std::vector<PendingCharacterInteractionSendOptionRowV1> rows;

  friend bool
  operator==(const PendingCharacterInteractionSendOptionsV1 &,
             const PendingCharacterInteractionSendOptionsV1 &) = default;
};

struct PendingCharacterInteractionRoutingV1 {
  std::int32_t kind = -1;
  std::int32_t played_character_id = -1;
  std::string current_responder_role;
  std::string reply_execution_channel;
  bool local_route = false;
  bool auto_accept_notification = false;

  friend bool
  operator==(const PendingCharacterInteractionRoutingV1 &,
             const PendingCharacterInteractionRoutingV1 &) = default;
};

struct PendingCharacterInteractionDeadlineV1 {
  std::int32_t age_days = 0;
  std::int32_t expiration_days = 0;
  std::int32_t remaining_days = 0;
  std::string expiry_boundary_status;

  friend bool
  operator==(const PendingCharacterInteractionDeadlineV1 &,
             const PendingCharacterInteractionDeadlineV1 &) = default;
};

struct PendingCharacterInteractionBooleanV1 {
  PendingCharacterInteractionSemanticStatusV1 status =
      PendingCharacterInteractionSemanticStatusV1::unavailable;
  bool value = false;
  std::string reason;

  friend bool
  operator==(const PendingCharacterInteractionBooleanV1 &,
             const PendingCharacterInteractionBooleanV1 &) = default;
};

struct PendingCharacterInteractionLegalityV1 {
  PendingCharacterInteractionSemanticStatusV1 status =
      PendingCharacterInteractionSemanticStatusV1::unavailable;
  bool allowed = false;
  std::string reason;

  friend bool
  operator==(const PendingCharacterInteractionLegalityV1 &,
             const PendingCharacterInteractionLegalityV1 &) = default;
};

struct PendingCharacterInteractionLegalitiesV1 {
  PendingCharacterInteractionLegalityV1 accept;
  PendingCharacterInteractionLegalityV1 reject;
  PendingCharacterInteractionLegalityV1 block;
  PendingCharacterInteractionLegalityV1 acknowledge;

  friend bool
  operator==(const PendingCharacterInteractionLegalitiesV1 &,
             const PendingCharacterInteractionLegalitiesV1 &) = default;
};

struct PendingCharacterInteractionUnavailableTermV1 {
  PendingCharacterInteractionSemanticStatusV1 status =
      PendingCharacterInteractionSemanticStatusV1::unavailable;
  std::string reason;

  friend bool
  operator==(const PendingCharacterInteractionUnavailableTermV1 &,
             const PendingCharacterInteractionUnavailableTermV1 &) = default;
};

inline constexpr std::size_t kPendingCharacterInteractionCostResourceCountV1 =
    10;
inline constexpr std::int64_t kPendingCharacterInteractionCostRawScaleV1 =
    100'000;

struct PendingCharacterInteractionCostEntryV1 {
  std::string resource_key;
  std::int64_t raw = 0;

  friend bool
  operator==(const PendingCharacterInteractionCostEntryV1 &,
             const PendingCharacterInteractionCostEntryV1 &) = default;
};

struct PendingCharacterInteractionStructuredCostsV1 {
  PendingCharacterInteractionSemanticStatusV1 status =
      PendingCharacterInteractionSemanticStatusV1::unavailable;
  std::int64_t raw_scale = kPendingCharacterInteractionCostRawScaleV1;
  std::string payer_role;
  std::string application_timing;
  std::string pending_payment_state;
  std::array<PendingCharacterInteractionCostEntryV1,
             kPendingCharacterInteractionCostResourceCountV1>
      entries{};
  std::string reason;

  friend bool
  operator==(const PendingCharacterInteractionStructuredCostsV1 &,
             const PendingCharacterInteractionStructuredCostsV1 &) = default;
};

struct PendingCharacterInteractionSpecialWarBindingV1 {
  PendingCharacterInteractionSemanticStatusV1 status =
      PendingCharacterInteractionSemanticStatusV1::unavailable;
  std::string special_interaction_kind;
  std::string absolute_outcome;
  std::int32_t war_id = -1;
  std::string actor_war_role;
  std::string recipient_war_role;
  std::string binding_source;
  std::string reason;

  friend bool
  operator==(const PendingCharacterInteractionSpecialWarBindingV1 &,
             const PendingCharacterInteractionSpecialWarBindingV1 &) = default;
};

struct PendingCharacterInteractionTermsV1 {
  bool special_data_present = false;
  PendingCharacterInteractionSpecialWarBindingV1 special_war_binding;
  PendingCharacterInteractionStructuredCostsV1 structured_costs;
  PendingCharacterInteractionUnavailableTermV1 structured_exchanges;
  PendingCharacterInteractionUnavailableTermV1 structured_effect_preview;
  PendingCharacterInteractionUnavailableTermV1 recipient_ai_acceptance_score;
  PendingCharacterInteractionUnavailableTermV1 recipient_ai_final_decision;

  friend bool operator==(const PendingCharacterInteractionTermsV1 &,
                         const PendingCharacterInteractionTermsV1 &) = default;
};

struct PendingCharacterInteractionReadinessV1 {
  bool stable_definition_ready = false;
  bool roles_ready = false;
  bool target_type_key_ready = false;
  bool target_typed_identity_ready = false;
  bool send_options_ready = false;
  bool routing_ready = false;
  bool deadline_ready = false;
  bool auto_accept_ready = false;
  bool reply_legality_ready = false;
  bool generic_costs_ready = false;
  bool special_war_binding_ready = false;
  bool special_outcome_terms_ready = false;
  bool structured_terms_ready = false;
  bool same_frame_ready = false;
  bool interaction_semantic_decision_ready = false;
  std::vector<std::string> not_ready_reasons;

  friend bool
  operator==(const PendingCharacterInteractionReadinessV1 &,
             const PendingCharacterInteractionReadinessV1 &) = default;
};

struct PendingCharacterInteractionContextV1 {
  PendingCharacterInteractionContextStatusV1 status =
      PendingCharacterInteractionContextStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t pending_interaction_id = -1;
  std::string reason;
  std::optional<PendingCharacterInteractionDefinitionV1> definition;
  std::optional<PendingCharacterInteractionRolesV1> roles;
  std::optional<PendingCharacterInteractionTargetV1> target;
  std::optional<PendingCharacterInteractionSendOptionsV1> send_options;
  std::optional<PendingCharacterInteractionRoutingV1> routing;
  std::optional<PendingCharacterInteractionDeadlineV1> deadline;
  std::optional<PendingCharacterInteractionBooleanV1> auto_accept;
  PendingCharacterInteractionLegalitiesV1 legality;
  std::optional<PendingCharacterInteractionTermsV1> terms;
  PendingCharacterInteractionReadinessV1 readiness;

  friend bool
  operator==(const PendingCharacterInteractionContextV1 &,
             const PendingCharacterInteractionContextV1 &) = default;
};

struct PendingCharacterInteractionFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;

  friend bool operator==(const PendingCharacterInteractionFrameV1 &,
                         const PendingCharacterInteractionFrameV1 &) = default;
};

enum class ReadPendingCharacterInteractionContextResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
  invalid = 2,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kPendingCharacterInteractionContextV1Capability =
        "game.command.query-pending-character-interaction-context-v1";
inline constexpr std::string_view kPendingCharacterInteractionContextV1Step =
    "query-pending-character-interaction-context-v1";
inline constexpr std::string_view
    kPendingCharacterInteractionContextV1GameVersion = "1.19.0.6";
inline constexpr std::string_view
    kPendingCharacterInteractionContextV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kPendingCharacterInteractionContextV1BackendId =
        "ck3-1.19.0.6-native-pending-character-interaction-context-v1";
inline constexpr std::string_view
    kPendingCharacterInteractionSpecialWarBindingV1Contract =
        "pending-character-interaction-special-war-binding-v1";

inline constexpr std::uintptr_t kPendingInteractionStorageSlotV1Rva = 0x57BF1C8;
inline constexpr std::uintptr_t kPendingInteractionCharacterStorageSlotV1Rva =
    0x570C130;
inline constexpr std::uintptr_t kPendingInteractionExpirationDaysV1Rva =
    0x570F528;
inline constexpr std::uintptr_t kPendingInteractionLocalRoutingV1Rva =
    0x1266BA0;
inline constexpr std::uintptr_t kPendingInteractionReplyValidatorV1Rva =
    0x26B3540;
inline constexpr std::uintptr_t kPendingInteractionTriggerEvaluatorV1Rva =
    0x334C510;
inline constexpr std::uintptr_t kPendingInteractionCostEvaluatorV1Rva =
    0x2CDB7B0;
inline constexpr std::uintptr_t kPendingInteractionCommonWarRelationV1Rva =
    0x2610840;
inline constexpr std::uintptr_t
    kPendingInteractionTargetTypeRegistryGetterV1Rva = 0x33C52B0;
inline constexpr std::uintptr_t kPendingInteractionTargetTypeRegistryV1Rva =
    0x4FFE290;
inline constexpr std::uintptr_t
    kPendingInteractionTargetTypeFallbackEntryV1Rva = 0x5000AB0;
inline constexpr std::uintptr_t kPendingInteractionScriptIdentifierNameV1Rva =
    0x3B58970;
// Exact-build generic target decoder for the stock call_ally war target.
// The first uint16 in the 16-byte envelope is the registry index; for the
// `war` type (index 16), the complete signed int32 WarID starts at +0x08.
// `typed_identity` serializes this as `war:<canonical positive signed-decimal-id>` only after the
// generation-safe active-CWar resolver and a second full-ID read succeed.
inline constexpr std::uint16_t kPendingInteractionWarTargetTypeIndexV1 = 16;
inline constexpr std::size_t kPendingInteractionWarTargetWarIdOffsetV1 = 0x08;
inline constexpr std::string_view kPendingInteractionWarTargetIdentityPrefixV1 =
    "war:";
// The typed decoder is intentionally bound to the canonical stock definition
// we researched.  Other interaction definitions can reuse the same generic
// target registry type, but are not allowed to cross this semantic seam.
inline constexpr std::string_view kPendingInteractionCallAllyDefinitionKeyV1 =
    "call_ally_interaction";
inline constexpr std::uintptr_t kPendingInteractionReplyPrimaryVtableV1Rva =
    0x4082930;
inline constexpr std::uintptr_t kPendingInteractionReplySecondaryVtableV1Rva =
    0x4082900;
inline constexpr std::uintptr_t
    kPendingInteractionWarVictorySpecialVtableV1Rva = 0x428EEA8;
inline constexpr std::uintptr_t
    kPendingInteractionWarWhitePeaceSpecialVtableV1Rva = 0x428EF88;
inline constexpr std::uintptr_t kPendingInteractionWarDefeatSpecialVtableV1Rva =
    0x428EF18;
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

} // namespace xar::ck3_11906
