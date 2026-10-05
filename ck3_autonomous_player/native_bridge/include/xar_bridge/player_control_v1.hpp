#pragma once

#include <array>
#include <atomic>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003 {
inline constexpr std::string_view kPlayerControlV1Step = "player-control-v1";
inline constexpr std::string_view kPlayerControlV1Capability = "player-control-v1";
#if defined(XAR_CK3_ENABLE_PLAYER_CONTROL_PRIVATE_V1)
inline constexpr bool kPlayerControlV1CompiledEnabled = true;
#else
inline constexpr bool kPlayerControlV1CompiledEnabled = false;
#endif

enum class PlayerControlActionV1 : std::uint32_t {
  query_context = 0, open_pause_menu = 1, open_switch = 2,
  choose_character = 3, confirm_control = 4,
};
enum class PlayerControlStatusV1 : std::uint32_t {
  unavailable = 0, context_observed = 1, dispatch_pending = 2,
  dispatch_unknown_claimed = 3, control_observed = 4,
};
enum class PlayerControlPhaseV1 : std::uint32_t {
  unavailable = 0, map = 1, pause_menu = 2, switch_chooser = 3,
  control_confirmed = 4,
};

// Full identities are retained. A future .3 adapter must reject an unsupported
// full ID before touching its 32-bit storage; it must never truncate it.
struct PlayerControlRequestV1 {
  std::string request_id, request_nonce, source_inventory_sha256;
  PlayerControlActionV1 action = PlayerControlActionV1::query_context;
  std::uint64_t expected_revision = 0, expected_player_character_id = 0;
  std::uint32_t expected_game_pid = 0;
  std::uint64_t expected_connection_generation = 0;
  std::uint64_t expected_process_creation_filetime_100ns = 0;
  std::string expected_control_context_signature;
  std::optional<std::uint64_t> candidate_character_id;
};
bool ParsePlayerControlRequestV1(std::string_view json,
    PlayerControlRequestV1 &request, std::string &reason) noexcept;
std::string_view PlayerControlActionNameV1(PlayerControlActionV1 action) noexcept;
bool IsCompletePlayerControlCharacterIdV1(std::uint64_t id) noexcept;

struct PlayerControlTargetV1 {
  bool read_complete = false, root_exists = false, root_visible = false;
  bool target_exists = false, target_visible = false, target_enabled = false;
  bool unique_target = false, dispatch_admitted = false;
  std::uint64_t target_vtable_rva = 0;
};
struct PlayerControlDispatchV1 {
  bool claim_latched = false, dispatch_invoked = false, native_handled = false;
  bool post_read_complete = false, postcondition_observed = false;
};
struct PlayerControlControllerRecordV1 {
  std::optional<std::uint32_t> player_id;
  std::optional<std::uint64_t> character_id;
  std::optional<bool> is_current_controller, is_ai;
};
struct PlayerControlCandidateV1 {
  std::optional<std::uint64_t> character_id, playable_id;
  std::optional<bool> is_ruler, can_control;
  std::optional<bool> selection_visible, selection_enabled, source_verified;
};
struct PlayerControlObservationV1 {
  PlayerControlActionV1 action = PlayerControlActionV1::query_context;
  PlayerControlStatusV1 status = PlayerControlStatusV1::unavailable;
  PlayerControlPhaseV1 phase = PlayerControlPhaseV1::unavailable;
  std::uint64_t native_revision = 0, connection_generation = 0;
  std::uint32_t game_pid = 0;
  std::uint64_t played_character_id = 0;
  std::uint64_t process_creation_filetime_100ns = 0, pump_epoch = 0;
  bool exact_build_verified = false, owner_verified = false;
  bool process_identity_verified = false, source_abi_pins_verified = false;
  bool stock_files_verified = false, loaded_source_binding_verified = false;
  bool frame_verified = false, context_signature_verified = false;
  std::string control_context_signature;
  std::optional<std::string> flow_id;
  std::optional<std::uint64_t> flow_source_character_id, flow_target_character_id;
  std::optional<std::uint32_t> flow_local_player_id, local_player_id;
  bool flow_complete = false;
  std::optional<std::uint64_t> controlled_character_id, selected_character_id;
  std::optional<bool> controlled_character_is_ai, ironman, multiple_players;
  bool controller_records_complete = false, candidates_complete = false;
  std::vector<PlayerControlControllerRecordV1> controller_records;
  std::vector<PlayerControlCandidateV1> candidates;
  // Fixed order: stock pause menu, SwitchCharacter, candidate selection,
  // stock Control/Ready. Queries never clear these durable stage facts.
  std::array<bool, 4> stage_consumed{};
  std::array<PlayerControlTargetV1, 4> targets{};
  std::array<PlayerControlDispatchV1, 4> dispatches{};
  std::string reason;
};
// Pure gates for the future owner-thread provider. No callback or memory writer
// is present in this contract; unknown source fields cannot admit an action.
bool PlayerControlSourceProofV1(const PlayerControlObservationV1 &v) noexcept;
bool PlayerControlStageAdmittedV1(const PlayerControlObservationV1 &v,
    PlayerControlActionV1 action, std::optional<std::uint64_t> candidate) noexcept;
bool PlayerControlActualControlObservedV1(const PlayerControlObservationV1 &v) noexcept;
std::string SerializePlayerControlObservationV1(const PlayerControlObservationV1 &v);
PlayerControlObservationV1 UnavailablePlayerControlObservationV1(
    const PlayerControlRequestV1 &request);
} // namespace xar::ck3_12003
