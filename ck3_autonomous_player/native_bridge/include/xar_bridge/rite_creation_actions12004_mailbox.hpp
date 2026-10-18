#pragma once
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/rite_creation_actions12004_wire.hpp"

namespace xar::ck3_12004::religion::rite_creation_actions {
struct MailboxContext {
 ck3_12002::QueryMailboxEnvelope envelope{};
 ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 environment{};
 WireRequest wire{};Frame actual_frame{};Result result{};
 bool completed=false;std::string failure;
};
std::string_view PrepareMailbox12004(const game::GameAdapter&,
 const game::Snapshot*previous_snapshot,std::string_view payload,
 std::uint64_t actual_revision,std::uint64_t actual_connection_generation,
 std::uintptr_t module_base,ck3_11906::MainThreadQueryMailboxV1&,
 MailboxContext&) noexcept;
bool ExecuteMailbox12004(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool RunMailbox12004(MailboxContext&,std::string_view request_id,
 std::string&serialized,std::string&failure) noexcept;
}
