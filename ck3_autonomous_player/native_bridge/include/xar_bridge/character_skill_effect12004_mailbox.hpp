#pragma once
#include "xar_bridge/character_skill_effect12004.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <string>
#include <string_view>

namespace xar::ck3_12004::character_skill_effects {
inline constexpr std::string_view kStep="query-character-skill-effects-v1-private";
inline constexpr std::string_view kDomain="character_skill_effects_v1";
namespace core=bridge::character_skill_effect12004;
using ReadSnapshot=bool (*)(void *,game::Snapshot &) noexcept;
struct Query {
  ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  bool enabled=false,completed=false,frame_changed=false;
  std::uintptr_t module_base=0;
  std::string_view executable_sha256{};
  void *native_context=nullptr;
  ReadSnapshot read_snapshot=nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision=0,connection_generation=0;
  std::uint32_t game_pid=0,character_id=0xFFFFFFFFU,invocations=0;
  std::int32_t skill=-1;
  core::Result observation{};
  std::string failure{};
};
// Pure finite wire parser. Actual owner revision/generation come from worker.
bool ParseRequest(std::string_view,const game::Snapshot &,std::uint64_t actual_revision,
    std::uint64_t actual_generation,std::uint32_t &target,std::int32_t &skill) noexcept;
bool Execute(void *,const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string Serialize(const Query &);
bool Handle(const game::GameAdapter &,ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot *actual_published,std::uint64_t actual_revision,
    std::uint64_t actual_connection_generation,std::string_view payload,
    std::string_view request_id,std::string &wire,std::string &failure) noexcept;
} // namespace xar::ck3_12004::character_skill_effects
