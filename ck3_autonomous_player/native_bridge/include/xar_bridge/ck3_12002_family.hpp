#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_family_value.hpp"
#include "xar_bridge/ck3_12002_family_projection.hpp"
#include "xar_bridge/current_first_heir_relationship_v1.hpp"
#include "xar_bridge/observed_heir_marriage_private_v1.hpp"

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

// The old namespace's value types are retained for the private wire serializer.
// Every native function and object layout below belongs to 1.20.0.2.
using CurrentFirstHeirRelationshipReadV1 =
    ck3_11906::CurrentFirstHeirRelationshipReadV1;
using CurrentFirstHeirBetrothalActionabilityReadV1 =
    ck3_11906::CurrentFirstHeirBetrothalActionabilityReadV1;

using FamilyEvaluateAnswer = std::uint8_t (*)(
    void *, std::uint8_t, std::uint8_t, void *, void *);
using FamilyReadBooleanOption = bool (*)(const void *, std::uint32_t);
using FamilySetBooleanOption = void (*)(void *, std::uint32_t, bool);

struct FamilyBindings {
  bool enabled = false;
  ContextBindings context{};
  family_value::Bindings values{};
  FamilyEvaluateAnswer evaluate_answer = nullptr;
  FamilyReadBooleanOption read_boolean_option = nullptr;
  FamilySetBooleanOption set_boolean_option = nullptr;
  const std::int32_t *adult_threshold_zero = nullptr;
  const std::int32_t *adult_threshold_one = nullptr;
  const std::uint32_t *grand_wedding_option = nullptr;
  const std::uint32_t *matrilineal_option = nullptr;
};

struct alignas(8) FamilyPairContextV1 {
  std::array<std::byte, 0x338> bytes{};
  game::ArrangeMarriageValidationSample roles{};
  bool initialized = false;
};
struct FamilyPairTermsV1 {
  game::ArrangeMarriageValidationSample roles{};
  bool final_legality_sampled = false;
  bool complete_can_send = false;
  std::int64_t recipient_ai_accept_raw = 0;
  std::uint8_t recipient_answer_status_raw = 3;
  std::array<std::int64_t, 10> generic_cost_raw{};
  bridge::MarriageNativeOutcomeDetailsV1 adult{};
  bool effective_matrilineal_if_accepted = false;
};

bool PrepareFamilyPairContextV1(const FamilyBindings &, std::int32_t actor,
    std::int32_t subject, std::int32_t candidate, FamilyPairContextV1 &) noexcept;
void DestroyFamilyPairContextV1(const FamilyBindings &, FamilyPairContextV1 &) noexcept;
bool ReadFamilyPairTermsV1(const FamilyBindings &, std::int32_t subject,
    std::int32_t candidate, const FamilyPairContextV1 &, FamilyPairTermsV1 &) noexcept;

game::ReadArrangeMarriageFamilyCandidatesResultV1 ReadArrangeMarriageFamilyCandidatesV1(
    const FamilyBindings &, std::int32_t subject_character_id,
    std::vector<game::ArrangeMarriageFamilyCandidateV1> &output,
    game::ArrangeMarriageQueryDiagnostics &diagnostics) noexcept;

// The existing owning consumer prepares the typed subject / roles and pending
// mode. The native provider then re-evaluates that exact final context and
// copies the selected/default option into the queued command.
bridge::MarriageProposalNativeSubmitResultV1 SubmitFamilyMarriageProposalV1(
    const FamilyBindings &, const bridge::MarriageProposalSubmissionV1 &) noexcept;

ck3_11906::MarriageCandidateAlliancePrivateReadV1 ReadMarriageCandidateAlliancePrivateV1(
    const FamilyBindings &, const game::ArrangeMarriageFamilyCandidateV1 &,
    const FamilyProjectionBindings &, bool request_matrilineal_option = false,
    bool read_fertility = false) noexcept;

FamilyBindings BindFamilyImage(std::uintptr_t module_base,
                              std::string_view executable_sha256) noexcept;

// Called on the paused application thread with the independently observed
// public campaign-root first-heir ID. A failed reciprocal read is unavailable,
// never an empty relation; a minor / negative complete CanSend is observable.
CurrentFirstHeirRelationshipReadV1 ReadCurrentFirstHeirRelationshipV1(
    const FamilyBindings &, std::int32_t heir_character_id) noexcept;
CurrentFirstHeirBetrothalActionabilityReadV1
ReadCurrentFirstHeirBetrothalActionabilityV1(
    const FamilyBindings &, const CurrentFirstHeirRelationshipReadV1 &) noexcept;

bool ReadFamilyBilateralRelationshipV1(
    const FamilyBindings &, std::int32_t subject_character_id,
    std::int32_t candidate_character_id,
    bridge::MarriageProposalBilateralRelationshipV1 &) noexcept;
bool ReadFamilyAlliancePairV1(const FamilyBindings &, const FamilyProjectionBindings &,
    std::int32_t first_character_id, std::int32_t second_character_id,
    bool &first_has_second, bool &second_has_first) noexcept;

// Re-evaluates exactly the current pair, preserves native default lineality,
// and submits CSendCharacterInteractionCommand through the new owning queue.
// A submitted ACK remains pending until independent relationship readback.
bridge::MarriageProposalNativeSubmitResultV1
SubmitCurrentFirstHeirBetrothalFulfillmentV1(
    const FamilyBindings &, std::int32_t played_character_id,
    std::int32_t heir_character_id,
    const CurrentFirstHeirBetrothalActionabilityReadV1 &observed,
    std::uint64_t native_revision,
    bridge::ObservedHeirMarriagePendingV1 &pending) noexcept;

#endif
} // namespace xar::ck3_12002
