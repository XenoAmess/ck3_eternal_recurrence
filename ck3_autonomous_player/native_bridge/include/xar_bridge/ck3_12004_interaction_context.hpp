#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_faction_gift.hpp"
#include "xar_bridge/ck3_11906.hpp"

namespace xar::ck3_12004 {

// Actual .4 entry mapping, not an inferred image-wide address shift.
// Frozen spans: prisoner/current4-context-release/FAMILY-MAP.json.
// Admission and consumed-layout receipts: current4-context-release/ROOT-DELIVERY.json.
inline constexpr std::uintptr_t kInteractionDatabaseGetterRva12004 = 0x89DA60;
inline constexpr std::uintptr_t kInteractionDefinitionLookupRva12004 = 0xA055E0;
inline constexpr std::uintptr_t kInteractionConstructTwoRoleRva12004 = 0x3076C70;
inline constexpr std::uintptr_t kInteractionConstructAllRolesRva12004 = 0x3076E30;
inline constexpr std::uintptr_t kInteractionDestroyRva12004 = 0x3077380;
inline constexpr std::uintptr_t kInteractionClearOptionsRva12004 = 0x30786E0;
inline constexpr std::uintptr_t kInteractionSelectOptionRva12004 = 0x30787C0;
inline constexpr std::uintptr_t kInteractionRefreshRva12004 = 0x3078A40;
inline constexpr std::uintptr_t kInteractionFinalizeRva12004 = 0x3078C70;
inline constexpr std::uintptr_t kInteractionEvaluateAnswerRva12004 = 0x307BC60;
inline constexpr std::uintptr_t kInteractionValidatorRva12004 = 0x307C020;
inline constexpr std::uintptr_t kInteractionRecipientAnswerScoreRva12004 = 0x307C440;
inline constexpr std::uintptr_t kInteractionCostEvaluatorRva12004 = 0x310CEC0;
inline constexpr std::uintptr_t kInteractionRedirectRolesRva12004 = 0x3148DC0;
inline constexpr std::uintptr_t kInteractionTriggerEvaluatorRva12004 = 0x372DF10;
inline constexpr std::uintptr_t kInteractionStableHashRva12004 = 0x3F7E220;
inline constexpr std::uintptr_t kInteractionLookupScriptIdRva12004 = 0x3F8A660;
inline constexpr std::uintptr_t kInteractionScriptIdTableRva12004 = 0x3F8A7E0;

// The old provider's function types and pointer container are software-only.
// The binder below supplies actual .4 core and native addresses directly.
struct InteractionContextBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ck3_12002::ContextBindings context{};
  ck3_12002::FactionGiftGetDatabaseV1 get_database = nullptr;
  ck3_12002::FactionGiftStableHashV1 stable_hash = nullptr;
  ck3_12002::FactionGiftLookupDefinitionV1 lookup_definition = nullptr;
  ck3_12002::FactionGiftConstructTwoRoleContextV1 construct_two_role = nullptr;
  ck3_11906::GetScriptIdentifierTable get_script_identifier_table = nullptr;
  ck3_11906::LookupScriptIdentifierId lookup_script_identifier_id = nullptr;
  void (*clear_local_options)(void *) = nullptr;
  void (*select_local_option)(void *, std::int32_t) = nullptr;
  ck3_11906::EvaluateCharacterInteractionAnswer evaluate_answer = nullptr;
  ck3_12002::MarriageReadInteractionAnswerScore
      read_character_interaction_answer_score = nullptr;
};

// Query bindings only. Command construction/queue/vtables belong to the
// separate actual-build command provider and are not populated here.
InteractionContextBindings12004 BindInteractionContext12004(
    std::uintptr_t module_base,
    std::string_view actual_executable_sha256) noexcept;

} // namespace xar::ck3_12004
