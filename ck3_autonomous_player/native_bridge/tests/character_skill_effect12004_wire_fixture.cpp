// Serializer DTO qualification only. These are explicit synthetic values,
// not native leaf execution, a game character, or actual business evidence.
#include "xar_bridge/character_skill_effect12004_mailbox.hpp"
#include <cstdlib>
#include <iostream>
using namespace xar::ck3_12004::character_skill_effects;
void Check(bool value){if(!value)std::abort();}
Query Sample(){
 Query q{};q.completed=true;q.invocations=1;q.expected_revision=7;q.executable_sha256=core::kExeSha;
 q.game_pid=123;q.connection_generation=2;q.character_id=0x01000003U;q.skill=0;
 q.expected_snapshot.date_raw=51394920;q.expected_snapshot.played_character_id=15893;
 q.expected_snapshot.has_played_character=true;q.expected_snapshot.played_character_alive=true;
 q.expected_snapshot.paused=true;q.expected_snapshot.map_ready=true;
 auto &v=q.observation;v.available=true;v.two_pass_stable=true;v.unavailable_reason.clear();
 v.frame={7,51394920,15893,true,true,true};v.character_id=q.character_id;v.requested_skill=0;
 v.rite_id=2;v.faith_id=1;v.current_skill_points=std::array<std::int32_t,6>{-2,11,12,13,14,15};
 v.effective_devotion_level=-1;v.devotion_total_raw=40000000;v.actual_skill_breakdown="Original actor text: \"quoted\"\nNo selected site source";
 v.callback_provenance=core::CallbackProvenance::exact4_native;return q;
}
int main(){
 auto q=Sample();const auto positive=Serialize(q);Check(!positive.empty());
 Check(positive.find("\"diplomacy\":-2")!=std::string::npos&&positive.find("\"effective_devotion_level\":-1")!=std::string::npos);
 Check(positive.find("\\\"quoted\\\"\\n")!=std::string::npos);
 auto bad=q;bad.character_id++;Check(Serialize(bad).empty());
 bad=q;bad.observation.callback_provenance=core::CallbackProvenance::owned_fixture;Check(Serialize(bad).empty());
 bad=q;bad.observation.two_pass_stable=false;Check(Serialize(bad).empty());
 bad=q;bad.observation.site_attribution_observed=true;Check(Serialize(bad).empty());
 bad=q;bad.observation.selected_site_contribution_raw=0;Check(Serialize(bad).empty());
 bad=q;bad.observation.actual_skill_breakdown->assign(core::kMaxBreakdownBytes+1,'x');Check(Serialize(bad).empty());
 bad=q;bad.observation.frame.revision++;Check(Serialize(bad).empty());
 bad=q;bad.frame_changed=true;Check(Serialize(bad).empty());
 auto unavailable=q;unavailable.observation={};auto &v=unavailable.observation;
 v.frame=q.observation.frame;v.character_id=q.character_id;v.requested_skill=0;v.unavailable_reason="fixture_source_unavailable";
 const auto negative=Serialize(unavailable);Check(!negative.empty()&&negative.find("\"callback_provenance\":\"unavailable\"")!=std::string::npos);
 unavailable.observation.current_skill_points=std::array<std::int32_t,6>{};Check(Serialize(unavailable).empty());
 std::cout<<positive<<'\n'<<negative<<'\n';return 0;
}
