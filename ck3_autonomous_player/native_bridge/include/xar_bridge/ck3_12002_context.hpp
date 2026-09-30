#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"
#include "xar_bridge/game_contract.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::game {

// Native evaluated sendable choices. Scores are engine fixed-point operands,
// not probabilities; the successful marriage is observed in relationships.
struct MarriageCandidateEvaluation12002 {
  ArrangeMarriageChoice choice;
  ArrangeMarriageValidationSample roles;
  bool native_legal = false;
  bool native_auto_accept = false;
  std::int64_t recipient_acceptance_score_raw = 0;
  std::int64_t intermediary_acceptance_score_raw = 0;
  std::int64_t raw_scale = 100'000;
  // gold, prestige, piety, renown, influence, herd, treasury,
  // treasury_or_gold, merit, barter_goods, in native evaluator order.
  std::array<std::int64_t, 10> send_costs_raw{};
};

struct PlayedCharacterRelationships12002 {
  std::int32_t betrothed_character_id = -1;
  std::int32_t primary_spouse_character_id = -1;
  std::vector<std::int32_t> spouse_character_ids;
};

} // namespace xar::game

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kMarriageInteractionDatabaseSlotRva = 0x5C67538;
inline constexpr std::size_t kMarriageArrangeMarriageInteractionOffset = 0xF30;
inline constexpr std::size_t kMarriageCharacterFamilyDataOffset = 0x1A8;
inline constexpr std::uintptr_t kMarriageRedirectInteractionRolesRva = 0x3148DE0;
inline constexpr std::uintptr_t kMarriageConstructInteractionAllRolesRva = 0x3076E50;
inline constexpr std::uintptr_t kMarriageRefreshInteractionContextRva = 0x3078A60;
inline constexpr std::uintptr_t kMarriageFinalizeInteractionContextRva = 0x3078C90;
inline constexpr std::uintptr_t kMarriageValidateInteractionContextRva = 0x307C040;
inline constexpr std::uintptr_t kMarriageDestroyInteractionContextRva = 0x30773A0;
inline constexpr std::uintptr_t kMarriageRecipientInteractionAnswerScoreRva = 0x307C460;
inline constexpr std::uintptr_t kMarriageIntermediaryInteractionAnswerScoreRva = 0x307C360;
inline constexpr std::uintptr_t kMarriageInteractionCostEvaluatorRva = 0x310CEE0;
inline constexpr std::uintptr_t kMarriageInteractionTriggerEvaluatorRva = 0x372DF30;
inline constexpr std::uintptr_t kMarriageConstructSendInteractionCommandRva = 0x2968170;
inline constexpr std::uintptr_t kMarriageSendInteractionPrimaryVtableRva = 0x448BCE0;
inline constexpr std::uintptr_t kMarriageSendInteractionSecondaryVtableRva = 0x448BCB0;

// 1.20 adds the sixth role pointer. The former 1.19 six-argument function type
// cannot call this seven-argument entry. The native marriage caller supplies
// -1 for the added role and constructs the ordinary all-role context.
using MarriageRedirectInteractionRoles = void (*)(void *, std::int32_t *,
    std::int32_t *, std::int32_t *, std::int32_t *, std::int32_t *,
    std::int32_t *);
using MarriageConstructInteractionAllRoles = void *(*)(void *, void *, std::int32_t,
    std::int32_t, std::int32_t, std::int32_t, std::int32_t, void *);
using MarriageRefreshInteractionContext = void (*)(void *, bool);
using MarriageFinalizeInteractionContext = void (*)(void *);
using MarriageValidateInteractionContext = bool (*)(void *, void *);
using MarriageDestroyInteractionContext = void (*)(void *);
using MarriageReadInteractionAnswerScore = std::int64_t *(*)(void *, std::int64_t *);
using MarriageEvaluateInteractionCost = void (*)(const void *, const void *, std::int64_t *);
using MarriageEvaluateInteractionTrigger = bool (*)(void *, const void *);
using MarriageConstructSendInteractionCommand = void *(*)(void *, const void *);

struct ContextBindings {
  bool enabled = false;
  CoreBindings core;
  CommandBindings commands;
  void **interaction_database_slot = nullptr;
  MarriageRedirectInteractionRoles redirect_roles = nullptr;
  MarriageConstructInteractionAllRoles construct_all_roles = nullptr;
  MarriageRefreshInteractionContext refresh = nullptr;
  MarriageFinalizeInteractionContext finalize = nullptr;
  MarriageValidateInteractionContext validate = nullptr;
  MarriageDestroyInteractionContext destroy = nullptr;
  MarriageReadInteractionAnswerScore recipient_answer_score = nullptr;
  MarriageReadInteractionAnswerScore intermediary_answer_score = nullptr;
  MarriageEvaluateInteractionCost evaluate_cost = nullptr;
  MarriageEvaluateInteractionTrigger evaluate_trigger = nullptr;
  MarriageConstructSendInteractionCommand construct_send_command = nullptr;
  std::uintptr_t send_primary_vtable = 0;
  std::uintptr_t send_secondary_vtable = 0;
};

ContextBindings BindContextImage(std::uintptr_t module_base,
                                std::string_view executable_sha256) noexcept;

// In-process, owning-thread readers. Offline tests supply only fixture-owned
// objects/functions. No API here discovers, attaches to or reads a process.
bool ReadPlayedCharacterRelationships(
    const CoreBindings &core, std::int32_t played_character_id,
    game::PlayedCharacterRelationships12002 &output) noexcept;

game::ReadArrangeMarriageChoicesResult ReadArrangeMarriageChoices(
    const ContextBindings &bindings,
    std::vector<game::ArrangeMarriageChoice> &output,
    game::ArrangeMarriageQueryDiagnostics &diagnostics,
    std::vector<game::MarriageCandidateEvaluation12002> *evaluations = nullptr)
    noexcept;

game::ArrangeMarriageResult SubmitArrangeMarriage(
    const ContextBindings &bindings,
    const game::ArrangeMarriageChoice &choice) noexcept;

} // namespace xar::ck3_12002
