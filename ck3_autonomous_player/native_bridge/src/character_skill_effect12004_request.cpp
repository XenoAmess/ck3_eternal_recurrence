#include "xar_bridge/character_skill_effect12004_mailbox.hpp"
#include "xar_bridge/protocol.hpp"
#include <windows.h>
#include <array>
#include <limits>
namespace xar::ck3_12004::character_skill_effects {
namespace {
constexpr std::array<std::string_view,6> skills{
    "diplomacy","martial","stewardship","intrigue","learning","prowess"};
}
bool ParseRequest(std::string_view payload,const game::Snapshot &current,
    std::uint64_t revision,std::uint64_t generation,std::uint32_t &target,std::int32_t &skill) noexcept {
  std::uint64_t a=0,b=0,date=0,played=0,pid=0,gen=0,id=0,index=0;std::string key;
  if(!bridge::JsonUnsignedField(payload,"expected_revision",a)||a==0||a!=revision||
      !bridge::JsonUnsignedField(payload,"expected_snapshot_revision",b)||b!=revision||
      !bridge::JsonUnsignedField(payload,"expected_date_raw",date)||
      date>static_cast<std::uint64_t>((std::numeric_limits<std::int32_t>::max)())||
      date!=static_cast<std::uint64_t>(current.date_raw)||
      !bridge::JsonUnsignedField(payload,"expected_actor_character_id",played)||
      played!=static_cast<std::uint64_t>(current.played_character_id)||
      !bridge::JsonUnsignedField(payload,"expected_game_pid",pid)||pid!=GetCurrentProcessId()||
      !bridge::JsonUnsignedField(payload,"expected_connection_generation",gen)||gen==0||gen!=generation||
      !bridge::JsonUnsignedField(payload,"character_id",id)||id>=0xFFFFFFFFULL||
      !bridge::JsonUnsignedField(payload,"skill_enum",index)||index>=skills.size()||
      !bridge::JsonStringField(payload,"skill_key",key,32)||key!=skills[static_cast<std::size_t>(index)])return false;
  target=static_cast<std::uint32_t>(id);skill=static_cast<std::int32_t>(index);return true;
}
}
