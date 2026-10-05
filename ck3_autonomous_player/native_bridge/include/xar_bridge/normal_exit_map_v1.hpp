#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"

#include <array>
#include <atomic>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12003 {
inline constexpr std::string_view kNormalExitMapV1Step = "normal-exit-map-v1";
inline constexpr std::string_view kNormalExitMapV1Capability = "normal-exit-map-v1";
#if defined(XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1)
inline constexpr bool kNormalExitMapV1CompiledEnabled = true;
#else
inline constexpr bool kNormalExitMapV1CompiledEnabled = false;
#endif

enum class NormalExitMapActionV1 : std::uint32_t {
  query_context = 0, prepare_confirmation = 1, confirm_desktop = 2,
};
enum class NormalExitMapStatusV1 : std::uint32_t {
  unavailable = 0, context_observed = 1, confirmation_observed = 2,
  dispatch_pending = 3, dispatch_unknown_claimed = 4,
};

// This is the complete, closed production wire request; native addresses,
// widget names, paths, save settings and caller-created claim tokens are absent.
struct NormalExitMapRequestV1 {
  std::string request_id;
  NormalExitMapActionV1 action = NormalExitMapActionV1::query_context;
  std::uint64_t expected_revision = 0;
  std::uint32_t expected_player_character_id = 0;
  std::uint32_t expected_game_pid = 0;
  std::uint64_t expected_connection_generation = 0;
  std::uint64_t expected_process_creation_filetime_100ns = 0;
  std::string request_nonce;
  std::string source_inventory_sha256;
  std::string expected_exit_context_signature;
};
bool ParseNormalExitMapRequestV1(std::string_view json,
    NormalExitMapRequestV1 &request, std::string &reason) noexcept;
std::string_view NormalExitMapActionNameV1(NormalExitMapActionV1 action) noexcept;

struct NormalExitMapTargetV1 {
  bool read_complete = false;
  bool root_exists = false, root_visible = false;
  bool target_exists = false, target_visible = false, target_enabled = false;
  bool unique_target = false, dispatch_admitted = false;
  std::uint64_t target_vtable_rva = 0;
  friend bool operator==(const NormalExitMapTargetV1 &, const NormalExitMapTargetV1 &) = default;
};
struct NormalExitMapDispatchV1 {
  bool claim_latched = false, dispatch_invoked = false, native_handled = false;
  bool post_read_complete = false, postcondition_observed = false;
};
struct NormalExitMapObservationV1 {
  NormalExitMapActionV1 action = NormalExitMapActionV1::query_context;
  NormalExitMapStatusV1 status = NormalExitMapStatusV1::unavailable;
  std::uint64_t native_revision = 0, connection_generation = 0;
  std::uint32_t game_pid = 0, played_character_id = 0;
  std::uint64_t process_creation_filetime_100ns = 0;
  std::uint64_t pump_epoch = 0;
  bool exact_build_verified = false, owner_verified = false;
  bool process_identity_verified = false, source_abi_pins_verified = false;
  bool stock_files_verified = false, loaded_source_binding_verified = false;
  bool frame_verified = false, context_signature_verified = false;
  bool confirmation_visible = false;
  bool orderly_exit_verified = false, autosave_verified = false;
  std::array<NormalExitMapTargetV1, 3> targets{};
  // Fixed stages: menu opener, confirmation opener, desktop confirmation.
  std::array<NormalExitMapDispatchV1, 3> dispatches{};
  std::string exit_context_signature, reason;
};
std::string SerializeNormalExitMapObservationV1(
    const NormalExitMapObservationV1 &observation);

// Bridge-owned, retained for the entire loaded bridge/process lifetime.
// Query/reconnect/revision changes never clear a stage's consumed claim.
struct NormalExitMapSessionV1 {
  std::uint32_t process_pid = 0;
  std::uint64_t process_creation_filetime_100ns = 0, query_epoch = 0;
  std::array<std::atomic<bool>, 3> claimed{};
  std::string signature;
  std::string queried_inventory_sha256;
  game::Snapshot queried_snapshot{};
  std::uint64_t queried_revision = 0, queried_generation = 0;
  void *queried_gui_context = nullptr, *queried_gui_owner = nullptr;
  std::array<void *, 3> queried_roots{}, queried_targets{}, queried_vtables{};
  std::array<NormalExitMapTargetV1, 3> queried_observations{};
};

struct NormalExitMapContextV1 {
  const game::GameAdapter *game = nullptr;
  NormalExitMapRequestV1 request{};
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision = 0, connection_generation = 0;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  void *owner_executor_context = nullptr;
  NormalExitMapSessionV1 *session = nullptr;
  NormalExitMapObservationV1 observation{};
};
bool ExecuteNormalExitMapV1(NormalExitMapContextV1 &context,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment,
    ck3_11906::ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept;
} // namespace xar::ck3_12003
