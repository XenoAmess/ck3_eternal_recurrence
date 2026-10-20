#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/player_inventory_window_native12004.hpp"
#include <string>
#include <string_view>
namespace xar::ck3_12004::player_inventory_window {
inline constexpr std::string_view kQuery="query-player-inventory-window-v1-private";
inline constexpr std::string_view kOpen="open-player-inventory-window-v1-private";
inline constexpr std::string_view kPost="query-player-inventory-window-open-post-v1-private";
inline constexpr std::string_view kClose="close-player-inventory-window-v1-private";
inline constexpr std::string_view kCloseQuery="query-player-inventory-window-close-v1-private";
inline constexpr std::string_view kClosePost="query-player-inventory-window-close-post-v1-private";
struct Observation {
  bool available=false,read_only=true,code_pins_verified=false,gui_sources_verified=false;
  bool intent_found=false,once_consumed=false,invoked=false,call_returned=false,needs_recovery=false,
       desired_window_observed=false,has_before=false,has_after=false;
  std::uint64_t intent_sequence=0;
  std::string operation="query",status="inventory_window_unavailable",unavailable_reason="not_read";
  PlayerInventoryOpenPost12004 current{},before{},after{};
};
std::string Serialize(const Observation&);
// Independent domain/schema; existing open wire remains unchanged.
std::string SerializeClose(const Observation&);
bool IsStep(std::string_view) noexcept;
bool ExecuteRead(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool ExecuteOpen(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
// ExecuteOpen is the existing fixed inventory action slot; it also owns Close.
bool Handle(const game::GameAdapter&,ck3_11906::MainThreadQueryMailboxV1&,
    const game::Snapshot* published,std::uint64_t actual_revision,std::uint64_t actual_generation,
    std::string_view step,std::string_view payload,std::string_view request_id,
    std::string& serialized,std::string& failure) noexcept;
}
