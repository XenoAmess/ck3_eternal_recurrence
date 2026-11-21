// Offline-only TU: compile the actual production Bridge once for these two test entry points.
#include "bridge.cpp"
namespace xar::combined142_fixture {
std::string Serialize(const game::Snapshot &s,const game::GameAdapter *a){
 return StateSnapshotFrame(s,7,CheckpointSubmission{}, {},"own142",a?&a->descriptor():nullptr);
}
std::string ArmNonempty(const game::GameAdapter &a,const game::Snapshot &s,std::string_view step,std::string_view payload,bool &unchanged){
 WorkerState state{};state.state_revision=7;state.previous_snapshot=s;
 const auto sequence=g_main_thread_query_mailbox_v1.published_sequence.load();
 const auto generation=ck3_1210::ReadDateSentinelStatusV1(g_date_sentinel_1210_v1).generation;
 auto result=RunDateSentinelArm1210(a,state,"own142",step,payload);
 unchanged=sequence==g_main_thread_query_mailbox_v1.published_sequence.load()&&generation==ck3_1210::ReadDateSentinelStatusV1(g_date_sentinel_1210_v1).generation;
 return result;
}
}
