#pragma once
#include "xar_bridge/holy_site_relic_action_v1.hpp"
#include <cstddef>
#include <string>
#include <vector>

namespace xar::ck3_12004::religion::relic_actions {
using ReadMemory=bool(*)(void*,const void*,void*,std::size_t) noexcept;
struct Frame {
 std::uint64_t connection_generation=0,native_revision=0,capture_epoch=0;
 std::int32_t date_raw=0,played_character_id=-1;
 bool operator==(const Frame&)const=default;
};
// Provider-private ephemeral identities, acquired inside the existing paused
// owner/TLS callback. None of these pointers/flags is accepted from public JSON.
struct Admission {
 const void* jomini_owner=nullptr,*handler=nullptr,*actual_root=nullptr;
 bool owner_tls_paused_verified=false,modal_admitted=false;
 bool actual_root_visible=false,actual_root_enabled=false;
};
// Must be produced afresh by the separate source-qualified action preview.
// The production binder deliberately installs no reader in this candidate.
struct PreviewProof {
 // These qualify this source-bound production observation in the admitted
 // owner frame. They never mean past action/business qualification passed.
 bool available=false,source_qualified=false,live_qualified=false;
 Frame frame{};
 std::uint32_t holy_site_id=absent,artifact_id=absent;
 std::optional<std::uint32_t> selected_slot_index,effective_slot_index,replacing_artifact_id;
 bool artifact_character_owner_matches_player=false,player_owned_ids_contains_artifact=false;
 bool site_equipped_slot_member=false;
 bool preview_observed=false;
 std::string preview_identity_sha256;
 bool operator==(const PreviewProof&)const=default;
};
struct ButtonPresentation {
 bool available=false,visible=false,enabled=false;
 std::string child_path;
 // Internal observations only; never public input or serialized as addresses.
 const void*widget=nullptr,*vtable=nullptr;
 bool operator==(const ButtonPresentation&)const=default;
};
struct Bindings;
using SelectionCall=bool(*)(const Bindings&,const void*,const void*,bool&) noexcept;
using ButtonPredicate=bool(*)(const Bindings&,const void*,bool&) noexcept;
using ClickCall=bool(*)(const Bindings&,const void*,bool&) noexcept;
using PreviewReader=bool(*)(void*,const Admission&,const Frame&,const Request&,PreviewProof&) noexcept;
using PresentationReader=bool(*)(void*,const Admission&,const Request&,ButtonPresentation&) noexcept;
struct Bindings {
 bool enabled=false,source_bound=false;
 std::uintptr_t image_base=0;
 ReadMemory read_memory=nullptr;void*read_context=nullptr;
 void**holy_site_storage=nullptr,**artifact_storage=nullptr,**character_storage=nullptr;
 const std::uint32_t*current_actor_reference=nullptr;
 SelectionCall select_artifact=nullptr,toggle_slot=nullptr;
 ButtonPredicate enshrine_button=nullptr,remove_button=nullptr;
 ClickCall enshrine_click=nullptr,remove_click=nullptr;
 PreviewReader preview_reader=nullptr;void*preview_context=nullptr;
 PresentationReader presentation_reader=nullptr;void*presentation_context=nullptr;
 // Explicit private lane opt-in, never evidence of prior business success.
 // The production binder leaves it false. The navigation adapter may enable
 // it only with the separately opted-in production preview reader installed.
 bool gameplay_action_lane_enabled=false;
 std::string_view backend="unavailable";
};
struct Selection {
 bool available=false;
 std::optional<std::uint32_t> artifact_id,slot_index;
 std::vector<std::optional<std::uint32_t>> slot_artifact_ids;
 std::string unavailable_reason="relic_ui_selection_not_read";
};
struct Result {
 bool available=false,loaded_source_pins_verified=false;
 bool native_dispatch_attempted=false,dispatch_invoked=false,verification_pending=false;
 bool already_in_requested_state=false,selection_postcondition_observed=false;
 bool original_button_enabled_observed=false;
 std::optional<bool> original_button_enabled;
 bool frozen_preview_verified=false,gameplay_command_may_have_been_queued=false;
 bool actual_button_presentation_observed=false;
 std::string button_child_path;
 // Callback return never grants business success. Post-owner/inventory/slot
 // query must be a separate request after a completed gameplay mailbox cycle.
 bool business_outcome_observed=false,action_ready=false;
 Selection before{},after{};
 std::string status="unavailable",unavailable_reason="relic_ui_action_not_run";
};
Bindings BindHolySiteRelicActionsImage12004(std::uintptr_t,std::string_view) noexcept;
// Existing IngameUi owner/TLS/paused/modal gates must precede this call.
// It resolves full references/current slot rows itself, never accepts pointers.
bool ExecuteHolySiteRelicAction12004(const Bindings&,const Admission&,const Frame&,
 const Request&,Result&) noexcept;
// Separate raw observation entry, usable by later owner callback readback.
bool ReadHolySiteRelicSelection12004(const Bindings&,const Admission&,const Frame&,
 std::uint32_t holy_site_id,Selection&) noexcept;
std::string SerializeHolySiteRelicAction12004(const Result&);
}
