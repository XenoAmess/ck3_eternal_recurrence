#pragma once
#include "xar_bridge/ck3_121003_living_inventory26785313_v1.hpp"
#include "xar_bridge/ck3_121003_living_event_scopes26785313_private_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Public wire SOURCE contract. No current descriptor/profile exposes it yet.
// A new exact owner/route is required; old LYD/12004 capability is insufficient.
inline constexpr char kLivingUiStep267V1[]="ck3_121003_living_ui.execute";
inline constexpr char kLivingUiCapability267V1[]="game.command.current-living-fixed-ui.v1";
inline constexpr char kLivingUiBackend267V1[]="current267-fixed-living-ui-v1";
inline constexpr char kLivingUiRequestSchema267V1[]="xar.living-ui.request/v1";
inline constexpr char kLivingUiResultSchema267V1[]="xar.living-ui.result/v1";
inline constexpr char kLivingUiSourceSchema267V1[]="xar.living-ui.source/v1";
enum class LivingUiAction267V1 {query_weapon,select_weapon,equip_target,unequip_target,
 query_events,open_tutorial,feed_common,feed_masterwork,feed_famed,feed_illustrious,
 cancel_review,confirm_review,query_detail,close_management};
enum class LivingUiKind267V1 {weapon,events,detail};
enum class LivingUiStatus267V1 {unavailable,available,dispatched,rejected,expired,stale_source,indeterminate};
struct LivingUiRequest267V1:LivingInventoryQueryRequest267V1 {
 LivingUiAction267V1 action=LivingUiAction267V1::query_events;
 std::uint64_t provider_generation=0,query_sequence=0;
 // No artifact/material/owner/slot/event/index/key/token/pointer selector.
};
struct LivingWeaponData267V1 {
 std::uint32_t target_full_id=0xFFFFFFFFU;
 std::optional<std::uint32_t>weapon_artifact_full_id;
 bool window_found=false,visible=false,enabled=false,target_equipped=false,weapon_selected=false;
 std::optional<bool>native_slot_available,native_can_hold;
 bool select_admissible=false,equip_admissible=false,unequip_admissible=false;
 friend bool operator==(const LivingWeaponData267V1&,const LivingWeaponData267V1&)=default;
};
struct LivingEventActionData267V1 {
 LivingUiAction267V1 action=LivingUiAction267V1::open_tutorial;
 std::int32_t instance_id=0,authored_option_index=-1;
 bool admissible=false;
 friend bool operator==(const LivingEventActionData267V1&,const LivingEventActionData267V1&)=default;
};
struct LivingEventData267V1 {
 LydEventSource267V1 census; // Common DATA fields only; all old LYD role/key null.
 std::vector<LivingEventScopeData267V1>bindings;
 std::vector<LivingEventActionData267V1>fixed_actions;
 bool complete_bindings=false;
 friend bool operator==(const LivingEventData267V1&,const LivingEventData267V1&)=default;
};
struct LivingDetailData267V1 {
 std::uint32_t target_full_id=0xFFFFFFFFU;
 bool window_found=false,visible=false,enabled=false,target_bound=false;
 std::optional<std::string>modifier_effects_text,custom_effects_text,description_text;
 // Null means that particular current getter was not observed/qualified.
 // It never becomes computed XP/static localization or empty observed text.
 friend bool operator==(const LivingDetailData267V1&,const LivingDetailData267V1&)=default;
};
struct LivingUiSource267V1 {
 LivingUiKind267V1 kind=LivingUiKind267V1::events;
 std::uint32_t actor_full_id=0xFFFFFFFFU;
 std::optional<LivingWeaponData267V1>weapon;
 std::optional<LivingEventData267V1>events;
 std::optional<LivingDetailData267V1>detail;
 bool sampled_twice=false;
 friend bool operator==(const LivingUiSource267V1&,const LivingUiSource267V1&)=default;
};
struct LivingUiResult267V1 {
 LivingUiAction267V1 action=LivingUiAction267V1::query_events;
 LivingUiStatus267V1 status=LivingUiStatus267V1::unavailable;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0;
 std::uint64_t connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;
 bool facts_available=false,source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<LivingUiSource267V1>source;std::string reason;
 // Effects return void: native_handled is false; no applied/closed claim is emitted.
};
const char*LivingUiActionName267V1(LivingUiAction267V1)noexcept;
LivingUiKind267V1 LivingUiKindFor267V1(LivingUiAction267V1)noexcept;
bool LivingUiQuery267V1(LivingUiAction267V1)noexcept;
bool LivingUiRequestShape267V1(const LivingUiRequest267V1&)noexcept;
bool LivingUiSourceShape267V1(const LivingUiSource267V1&,const ck3_1210::CoreSnapshotPrefix&)noexcept;
bool ParseLivingUiRequest267V1(std::string_view,LivingUiRequest267V1&)noexcept;
std::string SerializeLivingUiResult267V1(std::string_view,const LivingUiResult267V1&);
}
