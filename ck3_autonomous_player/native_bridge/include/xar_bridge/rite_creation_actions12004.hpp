#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::religion::rite_creation_actions {
inline constexpr std::string_view schema = "ck3_12004_rite_creation_action_v1";
inline constexpr std::string_view step = "player-rite-creation-action-v1";
inline constexpr std::string_view domain_key = "player_rite_creation_action_v1";
inline constexpr std::string_view result_key = "rite_creation_action";
inline constexpr std::uint32_t absent = 0xFFFFFFFFU;

enum class Operation { open_create_draft, open_edit_current_rite_draft,
 select_core_tenet, select_doctrine, set_name_field, preview,
 prepare_confirmation, confirm_once };
enum class NameField { name, adjective, adherent, adherent_plural, description };
enum class Outcome { create_faith, create_rite, edit_rite };
enum class ModalStage { unknown, none, confirmation };
enum class ModalKind { create, edit };

struct Frame {
 std::uint64_t connection_generation=0,native_revision=0,capture_epoch=0;
 std::int32_t date_raw=0,played_character_id=-1;
 bool operator==(const Frame&)const=default;
};
struct Request {
 Operation operation=Operation::preview;
 std::uint32_t expected_source_rite_id=absent;
 std::optional<std::uint32_t> core_slot_index;
 std::string tenet_key,group_key,doctrine_key;
 std::optional<NameField> name_field;
 std::string text;
 std::optional<Outcome> expected_outcome_kind;
 std::string expected_preview_identity,action_id;
};
struct TenetSelection {std::uint32_t slot_index=0;std::string tenet_key;
 bool operator==(const TenetSelection&)const=default;};
struct DoctrineSelection {std::string group_key,doctrine_key;
 bool operator==(const DoctrineSelection&)const=default;};
struct Draft {
 bool observed=false,names_observed=false,selected_core_tenets_observed=false,selected_doctrines_observed=false;
 std::optional<std::uint32_t> source_rite_id,source_faith_id,actor_faith_id;
 std::optional<Outcome> actual_outcome_kind;
 std::optional<bool> editing_owned_current_rite,native_create_faith_or_reform;
 std::array<std::optional<std::string>,5>names;
 std::vector<TenetSelection>selected_core_tenets;
 std::vector<DoctrineSelection>selected_doctrines;
 bool operator==(const Draft&)const=default;
};
struct Modal {
 bool observed=false;ModalStage stage=ModalStage::unknown;
 std::optional<ModalKind>kind;
 std::optional<bool>active,same_draft_window_bound,native_can_accept;
 bool operator==(const Modal&)const=default;
};
struct FullCan {
 bool observed=false;std::optional<bool>can_create,can_edit;
 std::optional<std::string>create_reason,edit_reason;
 bool operator==(const FullCan&)const=default;
};
struct Quote {
 bool observed=false;std::optional<std::int64_t>piety_cost_raw,piety_missing_signed_raw;
 std::optional<bool>has_enough_piety;
 static constexpr std::int64_t raw_scale=100000;
 bool operator==(const Quote&)const=default;
};
struct Result {
 Operation operation=Operation::preview;bool available=false;
 std::string status="unavailable",unavailable_reason="not_read";
 Frame frame{};Draft draft{};Modal modal{};FullCan full_can{};Quote quote{};
 bool preview_identity_available=false;
 std::optional<std::string>preview_identity;
 bool complete_command_payload_observed=false;
 bool original_writer_inputs_observed=false;
 std::optional<std::uint64_t>native_command_text_bytes;
 std::optional<std::string>native_command_text_sha256;
 bool native_dispatch_attempted=false,dispatch_invoked=false,verification_pending=false;
 bool original_writer_may_have_been_queued=false,business_outcome_observed=false;
 bool already_in_requested_state=false,selection_or_name_postcondition_observed=false;
 bool draft_open_postcondition_observed=false,native_once_claimed=false;
 std::optional<std::string>action_id;
};

using ReadMemory=bool(*)(void*,const void*,void*,std::size_t);
// Adapter to existing named-GUI runtime reader. No caller pointer/name/callback
// enters the transport. The wrapper must reject truncated/ambiguous roots.
using GuiRootState=bool(*)(void*,const void*,std::string_view,bool&,bool&);
using NamedButtonState=bool(*)(void*,const void*,std::string_view,bool&,bool&);
using ModalScopeState=bool(*)(void*,const void*);
struct Admission {
 bool owner_tls_paused_verified=false,exact_build_admitted=false;
 bool draft_action_opt_in=false,gameplay_commit_opt_in=false;
 void*jomini_owner=nullptr;void*handler=nullptr;
 GuiRootState gui_root_state=nullptr;void*gui_context=nullptr;
 NamedButtonState named_button_state=nullptr;
 ModalScopeState modal_scope_state=nullptr;
};
struct Bindings {
 bool enabled=false,source_bound=false;std::uintptr_t image_base=0;
 ReadMemory read_memory=nullptr;void*read_context=nullptr;
};

// This source candidate installs concrete exact-.4 controller calls. It does
// not register a transport, advertise capability, grant thread ownership or
// manufacture tokens from a partial DTO. It uses the original command factory,
// private finalization and original command text serializer; actual repeated
// byte stability and cleanup are required before minting.
Bindings BindRiteCreationActionsImage12004(std::uintptr_t,std::string_view) noexcept;
bool ValidateRequest(const Request&) noexcept;
bool ReadRiteCreationController12004(const Bindings&,const Admission&,const Frame&,
 const Request&,Result&) noexcept;
bool ExecuteRiteCreationAction12004(const Bindings&,const Admission&,const Frame&,
 const Request&,Result&) noexcept;
} // namespace xar::ck3_12004::religion::rite_creation_actions
