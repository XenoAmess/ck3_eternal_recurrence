#pragma once
// Closed internal RMTM spec. Never a caller family/actor/allow-change parameter.
#include "xar_bridge/ck3_121003_ted_date_proof26785313_v1.hpp"
namespace xar::ck3_1210 {
using RmtmFixedDayStage267V1=TedFixedDayStage267V1;
using RmtmFixedDayProof267V1=TedFixedDayProof267V1;
ck3_11906::TacticalDailySentinelArmStatusV1 ArmRmtmFixedDay267V1(DateSentinelStateV1&,const ck3_11906::TacticalDailySentinelArmRequestV1&,std::uint64_t,RmtmFixedDayStage267V1)noexcept;
bool ReadRmtmFixedDayProof267V1(const DateSentinelStateV1&,std::uint64_t,RmtmFixedDayProof267V1&,ck3_11906::TacticalDailySentinelStatusV1&)noexcept;
bool ReadRmtmDeferredActorOnOwner267V1(DateSentinelStateV1&,const RmtmFixedDayProof267V1&,const ck3_11906::MainThreadExecutionStampV1&,DateSentinelObservationV1&,bool*busy=nullptr)noexcept;
}

namespace xar::ck3_121003::build26785313 {
bool RmtmDatePredecessorResolved267V1(const ck3_1210::DateSentinelStateV1&)noexcept;
bool ClaimRmtmDateCustody267V1(const ck3_1210::DateSentinelStateV1&,bool continuation)noexcept;
void CompleteRmtmDateCustody267V1(const ck3_1210::DateSentinelStateV1&)noexcept;
void BlockRmtmDateCustodyUnknown267V1(const ck3_1210::DateSentinelStateV1&)noexcept;
}
