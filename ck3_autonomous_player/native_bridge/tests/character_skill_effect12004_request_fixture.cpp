// Actual production finite request parser + real protocol helpers, no stub.
#include "xar_bridge/character_skill_effect12004_mailbox.hpp"
#include <windows.h>
#include <cstdlib>
#include <iostream>
using namespace xar::ck3_12004::character_skill_effects;
void Check(bool b){if(!b)std::abort();}
std::string Packet(){
 return "{\"expected_revision\":7,\"expected_snapshot_revision\":7,\"expected_date_raw\":51394920,"
     "\"expected_actor_character_id\":15893,\"expected_game_pid\":"+std::to_string(GetCurrentProcessId())+
     ",\"expected_connection_generation\":2,\"character_id\":16777219,\"skill_key\":\"diplomacy\",\"skill_enum\":0}";
}
int main(){
 xar::game::Snapshot s{};s.date_raw=51394920;s.played_character_id=15893;
 std::uint32_t actor=0;std::int32_t skill=-1;
 auto parse=[&](std::string_view p,std::uint64_t rev=7,std::uint64_t gen=2){return ParseRequest(p,s,rev,gen,actor,skill);};
 const auto good=Packet();Check(parse(good)&&actor==16777219&&skill==0);
 auto changed=[&](std::string_view from,std::string_view to){auto p=good;const auto pos=p.find(from);Check(pos!=std::string::npos);p.replace(pos,from.size(),to);return p;};
 Check(!parse(changed("\"expected_revision\":7","\"expected_revision\":0")));
 Check(!parse(changed("\"expected_snapshot_revision\":7","\"expected_snapshot_revision\":8")));
 Check(!parse(changed("\"expected_date_raw\":51394920","\"expected_date_raw\":2147483648")));
 Check(!parse(changed("\"expected_actor_character_id\":15893","\"expected_actor_character_id\":3")));
 Check(!parse(changed("\"expected_game_pid\":"+std::to_string(GetCurrentProcessId()),"\"expected_game_pid\":0")));
 Check(!parse(changed("\"expected_connection_generation\":2","\"expected_connection_generation\":3")));
 Check(!parse(good,8,2));Check(!parse(good,7,3));
 Check(!parse(changed("\"character_id\":16777219","\"character_id\":4294967295")));
 Check(!parse(changed("\"character_id\":16777219","\"character_id\":-1")));
 Check(!parse(changed("\"skill_enum\":0","\"skill_enum\":6")));
 Check(!parse(changed("\"skill_enum\":0","\"skill_enum\":true")));
 Check(!parse(changed("\"skill_key\":\"diplomacy\"","\"skill_key\":\"prowess\"")));
 Check(!parse(changed("\"skill_key\":\"diplomacy\"","\"wrong_key\":\"diplomacy\"")));
 std::cout<<"15 actual production finite parser source assertions; no game action\n";return 0;
}
