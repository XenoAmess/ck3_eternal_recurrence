#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kRiteCreateRequestSchema267V1[]="ck3.rite_create.current267_request.v1";
inline constexpr char kRiteCreateSourceSchema267V1[]="ck3.rite_create.current267_source.v1";
inline constexpr char kRiteCreateResultSchema267V1[]="ck3.rite_create.current267_result.v1";
inline constexpr char kRiteCreateBackend267V1[]="ck3-1.21.0.3-native-application-main-rite-create";
inline constexpr char kRiteCreateStep267V1[]="current-rite-create-v1";
inline constexpr char kRiteCreateCapability267V1[]="game.command.current-rite-create.v1";
enum class RiteCreateAction267V1{query,create,query_confirmation,accept_confirmation};
enum class RiteCreatePhase267V1{draft,confirmation};
enum class RiteCreateStatus267V1{unavailable,available,expired,stale_source,claim_consumed,prerequisite_rejected,confirmation_pending,create_dispatched,confirmation_dispatched,indeterminate};
struct RiteCreateRequest267V1{RiteCreateAction267V1 action=RiteCreateAction267V1::query;ck3_1210::CoreSnapshotPrefix expected{};std::uint32_t expected_source_rite_id=0xFFFFFFFFU;std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return{request_id.data(),request_id_size};}};
struct RiteCreateDraft267V1{bool is_creating=false,native_can_create=false;std::int64_t piety_cost_raw=0,piety_missing_raw=0;bool known_dynastic=false,selected_dynastic=false,create_button_found=false,create_button_visible=false,create_button_enabled=false,blocked_by_unrelated_modal=false,create_admissible=false;friend bool operator==(const RiteCreateDraft267V1&,const RiteCreateDraft267V1&)=default;};
struct RiteCreateConfirmation267V1{bool modal_found=false,native_can_accept=false,accept_button_visible=false,accept_button_enabled=false,original_create_bound=false,accept_admissible=false;friend bool operator==(const RiteCreateConfirmation267V1&,const RiteCreateConfirmation267V1&)=default;};
struct RiteCreateSource267V1{RiteCreatePhase267V1 phase=RiteCreatePhase267V1::draft;std::uint32_t source_rite_id=0xFFFFFFFFU;std::int32_t actor_id=-1;std::optional<RiteCreateDraft267V1>draft;std::optional<RiteCreateConfirmation267V1>confirmation;friend bool operator==(const RiteCreateSource267V1&,const RiteCreateSource267V1&)=default;};
struct RiteCreateResult267V1{RiteCreateAction267V1 action=RiteCreateAction267V1::query;RiteCreateStatus267V1 status=RiteCreateStatus267V1::unavailable;bool source_available=false,cleanup_known=true,facts_available=false;std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;bool effect_attempted=false,native_returned=false,native_handled=false;ck3_1210::CoreSnapshotPrefix facts{};std::optional<RiteCreateSource267V1>source;std::string reason;};
bool RiteCreateRequestShape267V1(const RiteCreateRequest267V1&)noexcept;
bool ParseRiteCreateRequest267V1(std::string_view,RiteCreateRequest267V1&)noexcept;
std::string SerializeRiteCreateResult267V1(std::string_view,const RiteCreateResult267V1&);
}
