#pragma once

#include "xar_bridge/current_first_heir_conception_trait_inputs_v1.hpp"
#include "xar_bridge/conception_extended_gate_12004.hpp"
#include "xar_bridge/conception_candidate_pending_12004.hpp"
#include "xar_bridge/conception_first_value_12004.hpp"
#include "xar_bridge/conception_second_value_12004.hpp"
#include "xar_bridge/conception_secondary_context_12004.hpp"
#include "xar_bridge/conception_pair_value_inputs_12004.hpp"
#include "xar_bridge/conception_pair_list_bonus_12004.hpp"
#include "xar_bridge/conception_related_pair_12004.hpp"
#include "xar_bridge/ck3_12004_conception_pair_max_input.hpp"
#include "xar_bridge/conception_child_limit_12004.hpp"
#include "xar_bridge/conception_offspring_count_12004.hpp"
#include "xar_bridge/conception_pair_shortcircuit_observer_12004.hpp"
#include "xar_bridge/conception_last_child_date_12004.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace xar::ck3_11906 {

// Application-query-local companions. The published Snapshot/relationship and
// reproductive row layouts and every existing serializer signature stay intact.
struct CurrentCharacterConceptionCandidateRowV1 {
  std::int32_t character_id = -1;
  ck3_12004::ConceptionExtendedGate12004Read extended_gate{};
  ck3_12004::conception_candidate_pending::Observation pending_candidate{};
  ck3_12004::ConceptionFirstValue12004Read first_value{};
  ck3_12004::ConceptionSecondValue12004 second_value{};
  ck3_12004::ConceptionSecondaryContext12004Read secondary_context{};
};

struct CurrentHouseholdConceptionPairInputsV1 {
  std::int32_t first_character_id = -1;
  std::int32_t second_character_id = -1;
  ck3_12004::conception_pair_value_inputs::LoadedReadResult loaded_numeric{};
  ck3_12004::conception_pair_value_inputs::BaseResult base_stage{};
  ck3_12004::ConceptionPairListBonus12004Read list_bonus{};
  ck3_12004::ConceptionRelatedPair12004Read related_pair{};
  std::optional<bool> alternate_relation_path{};
  ck3_12004::ConceptionPairMaxInput lineage_tiers{};
  std::optional<bool> first_title_state_present{};
  std::optional<std::int32_t> first_highest_tier_raw{};
  std::optional<std::int32_t> second_highest_tier_raw{};
  std::optional<std::int32_t> selected_character_id{};
  ck3_12004::ConceptionChildLimit12004Read child_limit{};
  ck3_12004::ConceptionOffspringCount12004Read offspring_count{};
  ck3_12004::ConceptionPairShortCircuit12004Read short_circuit{};
  ck3_12004::conception_last_child_date::Observation last_child_date{};
};

struct CurrentFirstHeirConceptionCandidateInputsReadV1 {
  std::string_view status = "unavailable";
  std::string_view unavailable_reason = "current_household_conception_binding_unavailable";
  std::vector<CurrentCharacterConceptionCandidateRowV1> rows{};
  // Existing heir first, each current spouse second. Betrothal is not converted
  // into a current married pair. No arbitrary selected pair enters this query.
  std::vector<CurrentHouseholdConceptionPairInputsV1> pairs{};
};

std::string CurrentFirstHeirRelationshipResultJsonV1(
    std::string_view request_id, std::uint64_t native_revision,
    std::int32_t heir_character_id,
    const CurrentFirstHeirRelationshipReadV1 &read,
    std::string_view override_unavailable_reason,
    const CurrentFirstHeirChildInputsReadV1 *child_inputs,
    const CurrentFirstHeirConceptionTraitInputsReadV1 *conception_trait_inputs,
    const CurrentFirstHeirConceptionCandidateInputsReadV1 *conception_candidate_inputs);

} // namespace xar::ck3_11906
#endif
