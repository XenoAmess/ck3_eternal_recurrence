#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::uint16_t kPrewarNodeNoIndex12004 = 0xFFFF;
inline constexpr std::size_t kPrewarNodeLimit12004 = 128;
inline constexpr std::size_t kPrewarNodeEdgeLimit12004 = 128;
inline constexpr std::size_t kPrewarNodeDepthLimit12004 = 16;
inline constexpr std::size_t kPrewarNodeReadByteLimit12004 = 32768;
inline constexpr std::size_t kPrewarNodeReadAttemptLimit12004 = 2048;

// Stable wire enums. A zero value is unobserved, never an observed null.
enum class PrewarNodeReadStatus12004 : std::uint8_t {
  unobserved, observed, observed_null, unreadable, address_overflow,
  byte_cap, attempt_cap
};
enum class PrewarNodeLayout12004 : std::uint8_t {
  unknown_compiled, sequence_list, on_action_definition, opaque_payload
};
enum class PrewarNodeStatus12004 : std::uint8_t {
  unobserved, captured, known_empty, unsupported_layout, unreadable,
  address_overflow, negative_count, null_nonzero_data, null_child,
  node_cap, edge_cap, depth_cap, byte_cap, attempt_cap, cycle,
  invalid_binding, invalid_selection, invalid_frame, role_identity,
  clock_changed, allocation_failure, unqualified_roles
};
enum class PrewarNodeReferenceStatus12004 : std::uint8_t {
  unobserved, captured, observed_null, unreadable, address_overflow,
  byte_cap, attempt_cap, node_cap, depth_cap, cycle, shared_node, edge_cap
};

struct PrewarNodeRva12004 {
  bool observed = false;
  bool in_module = false;
  std::uint32_t value = 0;
  bool operator==(const PrewarNodeRva12004 &) const = default;
};

// Public, pointer-free projection. Index is first-seen row position. For a
// sequence list, edge ordinals preserve native array order and duplicates.
// For a definition, the three edge ordinals are primary/alternate/recursive.
struct PrewarDeclarationNodeRow12004 {
  PrewarNodeLayout12004 layout = PrewarNodeLayout12004::unknown_compiled;
  PrewarNodeStatus12004 status = PrewarNodeStatus12004::unobserved;
  std::array<PrewarNodeReadStatus12004, 4> identity_read_status{};
  PrewarNodeRva12004 vptr;
  PrewarNodeRva12004 scope_kind_callee;
  PrewarNodeRva12004 scope_mask_callee;
  PrewarNodeRva12004 invoke_callee;
  bool child_count_observed = false;
  std::int32_t child_count_raw = -1;
  std::uint16_t edge_begin = 0;
  std::uint16_t edge_count = 0;
  bool operator==(const PrewarDeclarationNodeRow12004 &) const = default;
};
struct PrewarDeclarationNodeEdge12004 {
  std::uint16_t target_index = kPrewarNodeNoIndex12004;
  PrewarNodeReferenceStatus12004 status =
      PrewarNodeReferenceStatus12004::unobserved;
  bool operator==(const PrewarDeclarationNodeEdge12004 &) const = default;
};

struct PrewarDeclarationNodeSelection12004 {
  std::int32_t actor_character_id = -1;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::int32_t claimant_character_id = -1;
  std::int32_t target_character_id = -1;
  std::int32_t casus_belli_index = -1;
  std::int32_t cb_config_index = -1;
  std::string cb_key;
  std::vector<std::int32_t> selected_title_ids;
  bool operator==(const PrewarDeclarationNodeSelection12004 &) const = default;
};
struct PrewarDeclarationNodeFrame12004 {
  std::int32_t date_raw = 0;
  std::int32_t speed = 0;
  bool paused = false;
  std::int32_t local_player_id = -1;
  bool map_ready = false;
  bool has_played_character = false;
  std::int32_t played_character_id = -1;
  bool played_character_alive = false;
  bool operator==(const PrewarDeclarationNodeFrame12004 &) const = default;
};

// Caller-supplied fresh selected observation from the same owning callback.
// Readiness and the complete tuple must be independently qualified there.
// This reader does not finalize a CB, call a getter, or substitute role IDs.
struct PrewarDeclarationNodeSelectionObservation12004 {
  CoreSnapshotPrefix frame{};
  std::uint64_t query_ticket = 0;
  std::uint64_t epoch = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t public_revision = 0;
  bool finalized_selection_ready = false;
  bool named_roles_ready = false;
  PrewarDeclarationNodeSelection12004 selection;
};
struct PrewarDeclarationNodeIdentityNativeScope12004 {
  const void *actual_cb = nullptr;
  const void *actual_actor = nullptr;
  const void *actual_target = nullptr;
  const void *primary_attacker = nullptr;
  const void *primary_defender = nullptr;
};
struct PrewarDeclarationNodeIdentityBindings12004 {
  bool enabled = false;
  CoreBindings core{};
  std::uintptr_t image_base = 0;
  std::size_t runtime_image_size = 0;
};

// PRIVATE equality witnesses. These integer identities are never public wire
// values, never exported as heap RVAs, and never dereferenced after Read.
struct PrewarNodeRawField12004 {
  std::uintptr_t value = 0;
  PrewarNodeReadStatus12004 status = PrewarNodeReadStatus12004::unobserved;
  bool operator==(const PrewarNodeRawField12004 &) const = default;
};
struct PrewarDeclarationNodeRawRow12004 {
  std::uintptr_t address = 0;
  std::array<PrewarNodeRawField12004, 4> identity;
  PrewarNodeRawField12004 child_data;
  PrewarNodeReadStatus12004 child_count_status =
      PrewarNodeReadStatus12004::unobserved;
  std::int32_t child_count_raw = -1;
  std::array<PrewarNodeRawField12004, 3> definition_fields;
  bool operator==(const PrewarDeclarationNodeRawRow12004 &) const = default;
};
struct PrewarDeclarationNodeRawEdge12004 {
  std::uint16_t parent_index = kPrewarNodeNoIndex12004;
  std::uint32_t ordinal = 0;
  PrewarNodeRawField12004 target;
  bool operator==(const PrewarDeclarationNodeRawEdge12004 &) const = default;
};
struct PrewarDeclarationNodeRoleWitness12004 {
  std::uintptr_t supplied_address = 0;
  PrewarNodeRawField12004 storage;
  PrewarNodeRawField12004 slots;
  PrewarNodeRawField12004 resolved_address;
  PrewarNodeReadStatus12004 capacity_status =
      PrewarNodeReadStatus12004::unobserved;
  std::int32_t capacity_raw = -1;
  PrewarNodeReadStatus12004 id_status = PrewarNodeReadStatus12004::unobserved;
  std::uint32_t full_id_raw = 0xFFFFFFFF;
  PrewarNodeRawField12004 death_data;
  bool verified_alive = false;
  bool operator==(const PrewarDeclarationNodeRoleWitness12004 &) const = default;
};
struct PrewarDeclarationNodeIdentityPrivateWitness12004 {
  std::uintptr_t source_module_base = 0;
  std::size_t source_module_size = 0;
  std::array<std::uintptr_t, 3> source_core_slot_addresses{};
  std::uintptr_t actual_cb_address = 0;
  // actor/attacker/defender/target/played. Optional unqualified named roles
  // remain unobserved; input IDs do not certify native scope semantics.
  std::array<PrewarDeclarationNodeRoleWitness12004, 5> roles;
  PrewarNodeRawField12004 game_state;
  PrewarNodeRawField12004 jomini_state;
  std::array<PrewarNodeReadStatus12004, 3> clock_read_status{};
  std::int32_t date_raw = 0;
  std::int32_t native_speed_raw = -1;
  std::uint8_t paused_raw = 0;
  std::array<PrewarNodeRawField12004, 2> clock_after_roots;
  std::array<PrewarNodeReadStatus12004, 3> clock_after_read_status{};
  std::int32_t date_after_raw = 0;
  std::int32_t native_speed_after_raw = -1;
  std::uint8_t paused_after_raw = 0;
  PrewarNodeRawField12004 on_action_manager;
  PrewarNodeRawField12004 on_action_table;
  PrewarNodeRawField12004 on_action_definition;
  std::vector<PrewarDeclarationNodeRawRow12004> nodes;
  std::vector<PrewarDeclarationNodeRawEdge12004> edges;
  std::uint32_t read_bytes = 0;
  std::uint32_t read_attempts = 0;
  std::uint16_t failure_node = kPrewarNodeNoIndex12004;
  std::uint32_t failure_ordinal = 0;
  bool operator==(const PrewarDeclarationNodeIdentityPrivateWitness12004 &) const = default;
};

struct PrewarDeclarationNodeIdentity12004 {
  bool sampled = false;
  bool structural_capture_complete = false;
  bool participant_coverage_complete = false;
  bool war_permission = false;
  bool finalized_selection_ready = false;
  bool named_roles_ready = false;
  std::uint64_t query_ticket = 0;
  std::uint64_t epoch = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t public_revision = 0;
  PrewarDeclarationNodeFrame12004 frame;
  PrewarDeclarationNodeSelection12004 selection;
  std::uint16_t cb_root_index = kPrewarNodeNoIndex12004;
  std::uint16_t on_action_root_index = kPrewarNodeNoIndex12004;
  bool on_action_definition_observed = false;
  bool on_action_definition_known_null = false;
  // Callsite-qualified static provenance, not observed runtime callback args.
  std::array<std::uint32_t, 2> callback_source_rvas{0x25B1B70, 0x25B1E70};
  std::array<std::uint32_t, 3> unresolved_helper_source_rvas{
      0x37CDA20, 0x37CD150, 0x37CB450};
  bool callbacks_runtime_observed = false;
  bool real_war_context_observed = false;
  std::vector<PrewarDeclarationNodeRow12004> rows;
  std::vector<PrewarDeclarationNodeEdge12004> ordered_edges;
  PrewarNodeStatus12004 status = PrewarNodeStatus12004::unobserved;
  PrewarDeclarationNodeIdentityPrivateWitness12004 private_identity;
  bool operator==(const PrewarDeclarationNodeIdentity12004 &) const = default;
};

// Pure binding: actual .4 core and caller-attested runtime PE module bounds.
// No module discovery, whole-image read, or native call occurs here.
PrewarDeclarationNodeIdentityBindings12004
BindPrewarDeclarationNodeIdentityImage12004(
    const CoreBindings &actual_core, std::uintptr_t image_base,
    std::size_t runtime_image_size, std::string_view executable_sha256) noexcept;

// One bounded synchronous round on the owning paused query thread. True means
// sampled, including partial; false rejects base selection/frame/identity.
// Caller must freshly read twice in the same ticket, compare the WHOLE DTO
// (including private_identity), then seal its full frame. Drift revokes readiness.
// The serializer must omit private_identity, retain the entire selection tuple,
// and check its complete envelope's UTF-8 size <=8192; caps here do not prove it.
// Neither structural capture nor equality grants participant/war permission.
bool ReadPrewarDeclarationNodeIdentity12004(
    const PrewarDeclarationNodeIdentityBindings12004 &bindings,
    const PrewarDeclarationNodeIdentityNativeScope12004 &selected_scope,
    const PrewarDeclarationNodeSelectionObservation12004 &observation,
    PrewarDeclarationNodeIdentity12004 &output,
    std::string_view *reason = nullptr) noexcept;

} // namespace xar::ck3_12004
