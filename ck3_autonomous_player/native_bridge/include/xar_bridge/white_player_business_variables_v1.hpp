#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
inline constexpr std::string_view kWhitePlayerBusinessVariablesV1Step = "query-white-player-business-variables-v1";
inline constexpr std::string_view kWhitePlayerBusinessVariablesV1Capability = "game.command.query-white-player-business-variables-v1";
inline constexpr std::array<std::string_view,8> kWhitePlayerBusinessVariableKeysV1{{
  "ervc_cc_female", "ervc_cc_age", "ervc_cc_diplomacy", "ervc_cc_martial",
  "ervc_cc_stewardship", "ervc_cc_intrigue", "ervc_cc_learning", "ervc_cc_prowess",
}};
struct WhitePlayerBusinessScalarV1 {
  bool present = false;
  std::uint16_t actual_kind = 0;
  std::int64_t actual_payload = 0;
  std::optional<std::int64_t> fixed_raw;
  std::optional<std::int64_t> integer_value;
  friend bool operator==(const WhitePlayerBusinessScalarV1 &,const WhitePlayerBusinessScalarV1 &) = default;
};
struct WhitePlayerBusinessVariablesResultV1 {
  bool available = false, all_eight_numeric_integers = false;
  bool owner_thread_verified = false, source_abi_pins_verified = false;
  bool player_scope_verified = false, stable_two_pass_values = false, frame_verified = false;
  std::uint64_t native_revision = 0, connection_generation = 0;
  std::uint32_t game_pid = 0, application_thread_id = 0;
  std::uint64_t application_pump_epoch = 0;
  std::uintptr_t application_tls_context = 0, variable_context = 0, character_address = 0;
  std::int32_t played_character_id = -1, date_raw = 0;
  std::array<WhitePlayerBusinessScalarV1,8> fields{};
  std::string status = "unavailable", unavailable_reason;
};
struct WhitePlayerBusinessVariablesContextV1 {
  const game::GameAdapter *game = nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision = 0, connection_generation = 0;
  WhitePlayerBusinessVariablesResultV1 result{};
};
// Fixed current-player query only, executed by the owning application-main
// mailbox. No arbitrary variable names, actors, pointers or input effects.
bool ExecuteWhitePlayerBusinessVariablesV1(WhitePlayerBusinessVariablesContextV1 &,
    MainThreadQueryMailboxV1 &,const MainThreadExecutionStampV1 &) noexcept;
std::string SerializeWhitePlayerBusinessVariablesV1(const WhitePlayerBusinessVariablesResultV1 &);
} // namespace xar::ck3_11906
