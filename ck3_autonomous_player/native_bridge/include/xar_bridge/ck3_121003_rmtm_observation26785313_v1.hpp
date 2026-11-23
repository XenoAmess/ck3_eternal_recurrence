#pragma once
#include "xar_bridge/ck3_121003_rmtm_title_query26785313_v1.hpp"
#include <array>
#include <optional>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kRmtmObservationRequestSchema267V1[]="ck3.rmtm_observation.current267_request.v1";
inline constexpr char kRmtmObservationSourceSchema267V1[]="ck3.rmtm_observation.current267_source.v1";
inline constexpr char kRmtmObservationResultSchema267V1[]="ck3.rmtm_observation.current267_result.v1";
inline constexpr char kRmtmObservationBackend267V1[]="ck3-1.21.0.3-native-application-main-rmtm-observation";
inline constexpr std::array<std::string_view,8>kRmtmObservationActions267V1{"query_title_phase","query_council","query_budget","open_budget","cancel_budget","query_offer","open_offer","cancel_offer"};
inline constexpr std::array<std::string_view,8>kRmtmObservationSteps267V1{"query-rmtm-title-phase-current-v1","query-rmtm-council-current-v1","query-rmtm-budget-current-v1","open-rmtm-budget-current-v1","cancel-rmtm-budget-current-v1","query-rmtm-offer-current-v1","open-rmtm-offer-current-v1","cancel-rmtm-offer-current-v1"};
inline constexpr std::array<std::string_view,8>kRmtmObservationCaps267V1{"game.query.current-rmtm-title-phase.v1","game.query.current-rmtm-council.v1","game.query.current-rmtm-budget.v1","game.command.open-current-rmtm-budget.v1","game.command.cancel-current-rmtm-budget.v1","game.query.current-rmtm-offer.v1","game.command.open-current-rmtm-offer.v1","game.command.cancel-current-rmtm-offer.v1"};
inline constexpr std::array<std::string_view,3>kRmtmPhysicalPhases267V1{"d3","predeath","postdeath"};
inline constexpr std::array<std::string_view,9>kRmtmCouncilKeys267V1{"councillor_chancellor","councillor_spymaster","minister_grand_marshal","minister_personnel","councillor_marshal","councillor_steward","minister_justice","councillor_court_chaplain","minister_works"};
enum class RmtmObservationAction267V1:std::uint8_t {query_title_phase,query_council,query_budget,open_budget,cancel_budget,query_offer,open_offer,cancel_offer};
enum class RmtmPhysicalPhase267V1:std::uint8_t {d3,predeath,postdeath};
enum class RmtmOfferTarget267V1:std::uint8_t {released_a,released_b};
enum class RmtmObservationKind267V1:std::uint8_t {title_phase,council,budget,offer};
enum class RmtmObservationStatus267V1:std::uint8_t {unavailable,expired,stale_source,claim_consumed,available,navigation_dispatched,indeterminate};
struct RmtmObservationRequest267V1 {
 RmtmObservationAction267V1 action=RmtmObservationAction267V1::query_council;
 ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::optional<RmtmPhysicalPhase267V1>phase;std::optional<RmtmOfferTarget267V1>offer_target;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
struct RmtmTitlePhaseData267V1 {
 RmtmPhysicalPhase267V1 phase=RmtmPhysicalPhase267V1::d3;RmtmTitleQuerySource267V1 physical{};
 bool script_own_single_heir=false,holder_realm_single_heir=false,witness_guard_bound=false,witness_sampled_twice=false;
 friend bool operator==(const RmtmTitlePhaseData267V1&,const RmtmTitlePhaseData267V1&)=default;
};
struct RmtmCouncilSeat267V1 {
 std::string position_key;std::uint32_t full_task_id=0xFFFFFFFFU;
 std::optional<std::uint32_t>incumbent_id;std::optional<bool>incumbent_alive;
 friend bool operator==(const RmtmCouncilSeat267V1&,const RmtmCouncilSeat267V1&)=default;
};
struct RmtmCouncilData267V1 {
 std::int32_t owner_id=-1,native_task_count=0;bool complete_model_census=false,sampled_twice=false;
 std::array<RmtmCouncilSeat267V1,9>seats{};
 friend bool operator==(const RmtmCouncilData267V1&,const RmtmCouncilData267V1&)=default;
};
struct RmtmBudgetData267V1 {
 bool found=false,visible=false,enabled=false,blocked_by_visible_modal=false,open_admissible=false,cancel_admissible=false,sampled_twice=false;
 std::optional<std::int32_t>owner_id;std::optional<std::uint32_t>full_title_id,holder_id;
 // Only fixed MyRealm GetPlayer.Self. HUD TopLiege is a separate unadvertised context.
 std::string route="my_realm_player";
 friend bool operator==(const RmtmBudgetData267V1&,const RmtmBudgetData267V1&)=default;
};
struct RmtmOfferData267V1 {
 RmtmOfferTarget267V1 target=RmtmOfferTarget267V1::released_a;
 bool found=false,visible=false,enabled=false,blocked_by_visible_modal=false,open_admissible=false,cancel_admissible=false,sampled_twice=false;
 std::int32_t actor_id=-1,recipient_id=-1;std::string interaction_key="offer_vassalization_interaction",description;
 friend bool operator==(const RmtmOfferData267V1&,const RmtmOfferData267V1&)=default;
};
struct RmtmObservationSource267V1 {
 RmtmObservationKind267V1 kind=RmtmObservationKind267V1::council;bool case_bound=false,sampled_twice=false;
 std::optional<RmtmTitlePhaseData267V1>title_phase;std::optional<RmtmCouncilData267V1>council;
 std::optional<RmtmBudgetData267V1>budget;std::optional<RmtmOfferData267V1>offer;
 friend bool operator==(const RmtmObservationSource267V1&,const RmtmObservationSource267V1&)=default;
};
struct RmtmObservationResult267V1 {
 RmtmObservationAction267V1 action=RmtmObservationAction267V1::query_council;RmtmObservationStatus267V1 status=RmtmObservationStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,native_handled=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<RmtmObservationSource267V1>source;std::string reason;
};
bool RmtmObservationQuery267V1(RmtmObservationAction267V1)noexcept;
RmtmObservationKind267V1 RmtmObservationKindFor267V1(RmtmObservationAction267V1)noexcept;
bool RmtmObservationRequestShape267V1(const RmtmObservationRequest267V1&)noexcept;
bool RmtmObservationSourceShape267V1(const RmtmObservationSource267V1&,const ck3_1210::CoreSnapshotPrefix&)noexcept;
bool ParseRmtmObservationRequest267V1(std::string_view,RmtmObservationRequest267V1&)noexcept;
std::string SerializeRmtmObservationResult267V1(std::string_view,const RmtmObservationResult267V1&);
}
