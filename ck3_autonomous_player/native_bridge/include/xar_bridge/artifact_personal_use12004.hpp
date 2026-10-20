#pragma once
#include "xar_bridge/ck3_12004_holy_site_relic_permissions.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::artifact_personal_use {
inline constexpr std::uint32_t absent = 0xFFFFFFFFU;
// Proposed global owner-callback API; neither this domain nor its actions is registered.
struct Frame {
  std::uint64_t revision=0, capture_epoch=0, connection_generation=0;
  std::int64_t date_raw=0;
  std::uint32_t bridge_pid=0, actor_id=absent;
  std::uintptr_t owner=0;
  bool application_main_thread=false, native_tls_ready=false, paused=false,
       map_ready=false, actor_alive=false;
  bool operator==(const Frame&) const = default;
};
struct Env;
using ReadFrame = bool(*)(void*, Frame&) noexcept;
using Visible = bool(*)(const Env&,const void*,bool&) noexcept;
using Pick = bool(*)(const Env&,const void*,const void*,const void*&) noexcept;
using Predicate = bool(*)(const Env&,const void*,const void*,const void*,bool&) noexcept;
using Equipped = bool(*)(const Env&,const void*,const void*,bool&) noexcept;
using Text = bool(*)(const Env&,const void*,std::string&) noexcept;
using Dispatch = bool(*)(const Env&,const void*,const void*,bool) noexcept;
struct Request;
struct Observation;
struct Witness;
// Must atomically persist/consume the existing owner-bound central once ledger.
// False is a pre-dispatch refusal. No reset/retry API is provided here.
// An unresolved actor/artifact intent stays blocked across renamed request IDs;
// the callback may only touch the ledger, never advance the game or revise Frame.
using ClaimOnce = bool(*)(void*,const Frame&,const Request&,
                         const Observation&,const Witness&) noexcept;
struct Env {
  religion::relic_permissions::Bindings existing{};
  std::string_view admitted_executable_sha256{};
  bool enabled=false, actions_enabled=false;
  void* context=nullptr;
  ReadFrame frame=nullptr;
  Visible visible=nullptr;
  Pick pick=nullptr;
  Predicate can_equip_in_slot=nullptr;
  Equipped equipped=nullptr;
  Text modifier_text=nullptr;
  Dispatch dispatch=nullptr;
  ClaimOnce claim_once=nullptr;
};
struct Slot {
  std::uint32_t index=0, artifact_id=absent;
  std::string key;
  bool personal=false;
  bool operator==(const Slot&) const = default;
};
struct ModifierEntry {
  std::uint16_t key_raw_u16=0xFFFF;
  std::int64_t definition_value_raw_q64=0;
  bool operator==(const ModifierEntry&) const = default;
};
struct Observation {
  bool available=false, loaded_source_pins_verified=false;
  Frame frame{};
  std::uint32_t artifact_id=absent;
  std::vector<std::uint32_t> owned_ids;
  std::vector<Slot> slots;
  bool personally_owned=false, inventory_artifact=false, equipped=false;
  bool native_equipped_observed=false, inventory_view_available=false, inventory_view_visible=false;
  std::optional<std::uint32_t> equipped_slot_index, effective_slot_index;
  std::optional<std::uint32_t> replacing_artifact_id;
  std::optional<bool> can_equip_in_effective_slot, can_unequip;
  bool item_modifier_definition_available=false, modifier_description_available=false;
  std::vector<ModifierEntry> item_modifier_definition;
  std::string modifier_description;
  // Description/definition is item-scoped. It is not an actor total or net award.
  bool modifier_names_bound=false, actor_aggregate_observed=false,
       personal_net_effect_attributed=false, total_payment_observed=false;
  std::string unavailable_reason="not_read";
};
// Native-only witness. Never serialize its process pointers to public evidence.
struct Witness {
  std::uintptr_t actor=0, component=0, inventory=0, artifact=0, artifact_type=0,
      handler=0, view=0, view_root=0, selected_slot=0, effective_slot=0;
  std::uint32_t character_owner=absent, site_owner=absent;
  bool operator==(const Witness&) const = default;
};
struct Request {
  std::uint64_t request_sequence=0;
  std::uint32_t artifact_id=absent, expected_slot_index=absent,
      expected_replacing_artifact_id=absent;
  bool desired_equipped=false;
};
struct Result {
  bool invoked=false, once_intent_consumed=false, dispatch_call_returned=false,
      needs_recovery=false;
  Observation before{};
  std::string status="private_action_disabled";
};
bool ReadArtifactPersonalUse12004(const Env&,const Frame&,std::uint32_t,Observation&,
                                Witness* native_witness=nullptr) noexcept;
Result SubmitArtifactPersonalUse12004(const Env&,const Frame&,const Request&) noexcept;
// An independently read later frame may confirm the desired inventory state;
// absence alone, an ACK, or a new request ID never resolves an unknown action.
bool DesiredStateObserved12004(const Observation& before,const Request&,
                              const Observation& independently_read_after) noexcept;
// Attaches only statically recovered native callbacks. Remains disabled until
// the actual global owner/main-thread/TLS frame producer is supplied by transport.
Env BindArtifactPersonalUseCallbacks12004(
    const religion::relic_permissions::Bindings&,std::string_view executable_sha256) noexcept;
}
