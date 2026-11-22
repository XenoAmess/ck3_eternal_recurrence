#pragma once
// Internal finite TED binding only. Not a caller flag or old DateV1 extension.
#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
namespace xar::ck3_1210 {
enum class TedFixedDayStage267V1 {song_transition,recipient_stable};
struct TedFixedDayProof267V1 {
 bool captured=false,actor_changed=false;
 TedFixedDayStage267V1 stage=TedFixedDayStage267V1::song_transition;
 DateSentinelObservationV1 before{},after{};
 DateSentinelWorkerEpochV1 worker{};
 std::uint64_t generation=0,original_deadline_unix_ms=0,monotonic_deadline_ms=0,
  captured_unix_ms=0,captured_monotonic_ms=0;
 ck3_11906::TacticalDailySentinelStatusV1 status{};
};
ck3_11906::TacticalDailySentinelArmStatusV1 ArmTedFixedDay267V1(
 DateSentinelStateV1&,const ck3_11906::TacticalDailySentinelArmRequestV1&,
 std::uint64_t original_deadline_unix_ms,TedFixedDayStage267V1)noexcept;
// Pipe thread only, same worker rundown lock as old status read. Never owner/Post.
bool ReadTedFixedDayProof267V1(const DateSentinelStateV1&,std::uint64_t,
 TedFixedDayProof267V1&,ck3_11906::TacticalDailySentinelStatusV1&)noexcept;
// Owner-only, readonly. Captured worker proof is never rewritten. A later
// current actor is separate evidence, under the original generation/deadlines.
bool ReadTedDeferredActorOnOwner267V1(DateSentinelStateV1&,
 const TedFixedDayProof267V1&,const ck3_11906::MainThreadExecutionStampV1&,
 DateSentinelObservationV1&,bool*busy=nullptr)noexcept;
}
